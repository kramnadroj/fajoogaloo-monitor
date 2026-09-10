#!/usr/bin/env python3
"""
Deep Dip 2 Player Monitor
Monitors fajoogaloo's progress on Deep Dip 2 and alerts when reaching floor 15 (1500m)
"""

import requests
import sys
from datetime import datetime
import json
import os
from pathlib import Path

# Configuration
PLAYER_NAME = "fajoogaloo"
FLOOR_15_HEIGHT = 1586.0  # meters
API_BASE_URL = "https://dips-plus-plus.xk.io"

def get_player_height(player_name):
    """
    Fetch player's CURRENT live height from the Deep Dip 2 API.

    Uses /live_heights/global as the source of truth for "is this player
    playing right now" (per the API's own docs, /live_heights/<wsid> is
    marked "prefer global"). /leaderboard/global is NOT a reliable way to
    find a live player: it's a capped, unsorted snapshot covering only a
    small slice of all registered players' all-time personal bests, so a
    currently-live player can easily be absent from it. It's used here only
    as a best-effort source for displaying a personal-best height, and its
    failure must never block live-height detection/recording.

    Args:
        player_name: The name of the player to monitor

    Returns:
        tuple: (current_height, player_data) or (None, None) if player not found
    """
    try:
        # Step 1: Check who's currently live - authoritative for live status.
        response = requests.get(f"{API_BASE_URL}/live_heights/global", timeout=10)
        response.raise_for_status()
        live_players = response.json()

        live_entry = None
        if isinstance(live_players, list):
            for entry in live_players:
                if entry.get('display_name', '').lower() == player_name.lower():
                    live_entry = entry
                    break

        # Step 2: Best-effort lookup of personal-best height for display.
        # Not finding the player here does NOT mean the player doesn't exist -
        # it just means they're outside the capped snapshot this call returns.
        pb_height = None
        wsid = live_entry.get('user_id') if live_entry else None
        try:
            lb_response = requests.get(f"{API_BASE_URL}/leaderboard/global", timeout=10)
            lb_response.raise_for_status()
            leaderboard_data = lb_response.json()
            if isinstance(leaderboard_data, list):
                for entry in leaderboard_data:
                    if entry.get('name', '').lower() == player_name.lower():
                        pb_height = entry.get('height', 0)
                        if not wsid:
                            wsid = entry.get('wsid')
                        break
        except requests.RequestException as e:
            print(f"Warning: leaderboard PB lookup failed (non-fatal): {e}", file=sys.stderr)

        if live_entry is not None:
            current_height = live_entry.get('height')
            player_data = dict(live_entry)
            player_data['name'] = live_entry.get('display_name', player_name)
            player_data['wsid'] = wsid
            player_data['pb_height'] = pb_height
            player_data['current_height'] = current_height
            player_data['live_data'] = live_entry
            return current_height, player_data

        if wsid is None and pb_height is None:
            # Not live, and not found on the leaderboard snapshot either.
            return None, None

        # Known player (found via leaderboard), but no live session right now.
        player_data = {'name': player_name, 'wsid': wsid, 'height': pb_height, 'pb_height': pb_height}
        print(f"No live session data for {player_name} (PB: {pb_height}m)")
        return None, player_data

    except requests.RequestException as e:
        print(f"Error fetching data from API: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

def check_floor_15_reached(height):
    """
    Check if the player has reached floor 15.

    Args:
        height: Player's current height in meters

    Returns:
        bool: True if floor 15 reached
    """
    return height is not None and height >= FLOOR_15_HEIGHT

def send_notification(player_name, height, player_data):
    """
    Send notification when floor 15 is reached.
    This is a placeholder - actual notification method to be implemented.

    Args:
        player_name: Name of the player
        height: Current height achieved
        player_data: Full player data from API
    """
    timestamp = datetime.now().isoformat()

    print("=" * 60)
    print("🎉 FLOOR 15 REACHED! 🎉")
    print("=" * 60)
    print(f"Player: {player_name}")
    print(f"Height: {height}m")
    print(f"Timestamp: {timestamp}")
    print(f"Floor 15 threshold: {FLOOR_15_HEIGHT}m")
    print("=" * 60)

    # TODO: Add actual notification logic here
    # Options: Discord webhook, Email, Slack, SMS, etc.
    # For now, just print to stdout

def record_height_data(height, is_playing, player_name):
    """
    Record height data to JSON file for historical tracking.

    Args:
        height: Current height in meters (or None if not playing)
        is_playing: Boolean indicating if player is currently active
        player_name: Name of the player
    """
    data_file = Path("data/heights.json")
    timestamp = datetime.now().isoformat()

    # Create data directory if it doesn't exist
    data_file.parent.mkdir(parents=True, exist_ok=True)

    # Initialize or load existing data
    if not data_file.exists():
        data = {
            "player": player_name,
            "floor_target": FLOOR_15_HEIGHT,
            "last_updated": timestamp,
            "data_points": []
        }
    else:
        try:
            with open(data_file, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            # Handle corrupted file by backing it up
            backup_file = data_file.with_suffix(f'.json.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}')
            print(f"⚠️  Corrupted data file detected. Backing up to {backup_file}")
            os.rename(data_file, backup_file)
            # Reinitialize data structure
            data = {
                "player": player_name,
                "floor_target": FLOOR_15_HEIGHT,
                "last_updated": timestamp,
                "data_points": []
            }

    # Append new data point
    data_point = {
        "timestamp": timestamp,
        "live_height": height,
        "is_playing": is_playing
    }
    data["data_points"].append(data_point)
    data["last_updated"] = timestamp

    # Write back to file
    with open(data_file, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"📝 Height data recorded: {height}m at {timestamp}")

def main():
    """Main monitoring function."""
    print(f"Checking {PLAYER_NAME}'s progress on Deep Dip 2...")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("-" * 60)

    # Get player's current height
    height, player_data = get_player_height(PLAYER_NAME)

    if player_data is None:
        print(f"Player '{PLAYER_NAME}' not found on leaderboard")
        return

    if height is None:
        print(f"Player '{PLAYER_NAME}' is not currently playing (no live session)")
        if player_data and player_data.get('height') is not None:
            print(f"Personal Best: {player_data['height']}m")
        record_height_data(None, False, PLAYER_NAME)
        return

    # Display current live height and PB
    print(f"🔴 LIVE Height: {height:.2f}m")
    if player_data.get('pb_height') is not None:
        print(f"🏆 Personal Best: {player_data['pb_height']}m")
    print(f"🎯 Floor 15 Target: {FLOOR_15_HEIGHT}m")
    record_height_data(height, True, PLAYER_NAME)

    # Check if floor 15 has been reached
    if check_floor_15_reached(height):
        send_notification(PLAYER_NAME, height, player_data)
    else:
        meters_remaining = FLOOR_15_HEIGHT - height
        print(f"📊 Distance to Floor 15: {meters_remaining:.2f}m remaining")
        progress_pct = (height / FLOOR_15_HEIGHT) * 100
        print(f"📈 Progress: {progress_pct:.1f}%")

if __name__ == "__main__":
    main()
