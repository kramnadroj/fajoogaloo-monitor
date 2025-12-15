#!/usr/bin/env python3
"""
Deep Dip 2 Player Monitor
Monitors fajoogaloo's progress on Deep Dip 2 and alerts when reaching floor 15 (1500m)
"""

import requests
import sys
from datetime import datetime

# Configuration
PLAYER_NAME = "fajoogaloo"
FLOOR_15_HEIGHT = 1500.0  # meters
API_BASE_URL = "https://dips-plus-plus.xk.io"

def get_player_height(player_name):
    """
    Fetch player's CURRENT live height from the Deep Dip 2 API.

    Args:
        player_name: The name of the player to monitor

    Returns:
        tuple: (current_height, player_data) or (None, None) if player not found
    """
    try:
        # Step 1: Get player's wsid from leaderboard
        response = requests.get(f"{API_BASE_URL}/leaderboard/global", timeout=10)
        response.raise_for_status()
        leaderboard_data = response.json()

        wsid = None
        pb_height = None
        player_data = None

        # Search for player in leaderboard to get their wsid
        if isinstance(leaderboard_data, list):
            for entry in leaderboard_data:
                entry_name = entry.get('name', '').lower()
                if entry_name == player_name.lower():
                    wsid = entry.get('wsid')
                    pb_height = entry.get('height', 0)
                    player_data = entry
                    break

        if not wsid:
            # Player not found on leaderboard
            return None, None

        # Step 2: Get player's live height using their wsid
        response = requests.get(f"{API_BASE_URL}/live_heights/{wsid}", timeout=10)
        response.raise_for_status()
        live_data = response.json()

        # Extract current height from last_5_points
        if 'last_5_points' in live_data and len(live_data['last_5_points']) > 0:
            # Most recent point is first in array: [height, timestamp]
            current_height = live_data['last_5_points'][0][0]

            # Enrich player data with live info
            player_data['current_height'] = current_height
            player_data['pb_height'] = pb_height
            player_data['live_data'] = live_data

            return current_height, player_data
        else:
            # No live data available, player might not be currently playing
            # Return None to indicate no current session
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
        if player_data and 'height' in player_data:
            print(f"Personal Best: {player_data['height']}m")
        return

    # Display current live height and PB
    print(f"🔴 LIVE Height: {height:.2f}m")
    if 'pb_height' in player_data:
        print(f"🏆 Personal Best: {player_data['pb_height']}m")
    print(f"🎯 Floor 15 Target: {FLOOR_15_HEIGHT}m")

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
