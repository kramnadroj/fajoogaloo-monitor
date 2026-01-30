#!/usr/bin/env python3
"""
Backfill Historic Height Data from GitHub Actions Workflow Runs

This script fetches historic workflow run logs from GitHub Actions and extracts
height data to populate the heights.json file with historical data points.

Usage:
    GITHUB_TOKEN=your_token python backfill_historic_data.py

Environment Variables:
    GITHUB_TOKEN: GitHub personal access token with repo read access
"""

import requests
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path


# Configuration
REPO_OWNER = "kramnadroj"
REPO_NAME = "fajoogaloo-monitor"
WORKFLOW_NAME = "Monitor Deep Dip 2 Progress"
WORKFLOW_ID = "215175753"  # monitor.yml workflow ID
PLAYER_NAME = "fajoogaloo"
FLOOR_15_HEIGHT = 1500.0

# GitHub API base URL
GITHUB_API = "https://api.github.com"


def get_github_token():
    """Get GitHub token from environment variable."""
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("Error: GITHUB_TOKEN environment variable not set")
        print("Please set it with: export GITHUB_TOKEN=your_personal_access_token")
        sys.exit(1)
    return token


def get_headers(token):
    """Create headers for GitHub API requests."""
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }


def fetch_workflow_runs(token, per_page=100, created_filter=None):
    """
    Fetch all workflow runs for the monitor workflow.

    Args:
        token: GitHub API token
        per_page: Number of results per page
        created_filter: Optional date filter (e.g., "<2026-01-06" or ">2025-12-01")

    Returns:
        List of workflow run objects
    """
    headers = get_headers(token)
    all_runs = []
    page = 1
    total_count = None

    filter_desc = f" (filter: created{created_filter})" if created_filter else ""
    print(f"Fetching workflow runs for {REPO_OWNER}/{REPO_NAME} (workflow: {WORKFLOW_NAME}){filter_desc}...")

    while True:
        # Use workflow-specific endpoint to only get monitor workflow runs
        url = f"{GITHUB_API}/repos/{REPO_OWNER}/{REPO_NAME}/actions/workflows/{WORKFLOW_ID}/runs"
        params = {
            "per_page": per_page,
            "page": page,
            "status": "completed"
        }
        if created_filter:
            params["created"] = created_filter

        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        # Get total count from first page
        if total_count is None:
            total_count = data.get("total_count", 0)
            print(f"  Total monitor workflow runs: {total_count}")

        runs = data.get("workflow_runs", [])

        # All runs are already monitor workflow runs (endpoint is workflow-specific)
        if runs:
            all_runs.extend(runs)

        print(f"  Page {page}: Found {len(runs)} runs (cumulative: {len(all_runs)})")

        # Continue until we've fetched all pages
        # Calculate if there are more pages based on total count
        total_fetched = page * per_page
        if total_fetched >= total_count:
            print(f"  Reached end of pagination (fetched {total_fetched} >= {total_count} total)")
            break

        # If no runs returned and we haven't reached the total, something's wrong
        if not runs:
            print(f"  No runs returned on page {page}, stopping")
            break

        page += 1

        # Safety limit to prevent infinite loops
        if page > 100:
            print(f"  Warning: Reached page limit of 100")
            break

    print(f"Total workflow runs found: {len(all_runs)}")
    return all_runs


def fetch_run_logs(token, run_id, retries=3):
    """
    Fetch logs for a specific workflow run.

    Args:
        token: GitHub API token
        run_id: The workflow run ID
        retries: Number of retries for rate limiting

    Returns:
        Log content as string, or None if not available
    """
    import zipfile
    import io

    headers = get_headers(token)
    url = f"{GITHUB_API}/repos/{REPO_OWNER}/{REPO_NAME}/actions/runs/{run_id}/logs"

    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=60, allow_redirects=True)

            # Handle rate limiting
            if response.status_code == 403:
                reset_time = response.headers.get('X-RateLimit-Reset')
                if reset_time:
                    wait_time = int(reset_time) - int(time.time()) + 1
                    if wait_time > 0 and wait_time < 300:  # Max 5 min wait
                        print(f"\n  Rate limited. Waiting {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                # Exponential backoff for other 403s
                time.sleep(2 ** attempt)
                continue

            if response.status_code in (404, 410):
                return None  # Logs expired, deleted, or not available

            response.raise_for_status()

            zip_buffer = io.BytesIO(response.content)

            try:
                with zipfile.ZipFile(zip_buffer) as zf:
                    # Combine all log files
                    all_logs = []
                    for name in zf.namelist():
                        with zf.open(name) as f:
                            content = f.read().decode('utf-8', errors='ignore')
                            all_logs.append(content)
                    return "\n".join(all_logs)
            except zipfile.BadZipFile:
                # Sometimes logs come as plain text
                return response.text

        except requests.RequestException as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            print(f"  Warning: Could not fetch logs for run {run_id}: {e}")
            return None

    return None


def parse_height_from_logs(logs):
    """
    Parse height data from workflow run logs.

    Args:
        logs: Log content string

    Returns:
        tuple: (height, is_playing) or (None, False) if no height found
    """
    if not logs:
        return None, False

    # Look for LIVE Height pattern: "LIVE Height: XXX.XXm"
    live_match = re.search(r'LIVE Height:\s*([\d.]+)\s*m', logs)
    if live_match:
        try:
            height = float(live_match.group(1))
            return height, True
        except ValueError:
            pass

    # Check for "not currently playing" message
    if "not currently playing" in logs.lower() or "no live session" in logs.lower():
        return None, False

    # Check for PB height if no live height
    pb_match = re.search(r'Personal Best:\s*([\d.]+)\s*m', logs)
    if pb_match:
        # Player found but not playing
        return None, False

    return None, False


def load_existing_data():
    """Load existing heights data from JSON file."""
    data_file = Path("data/heights.json")

    if not data_file.exists():
        return {
            "player": PLAYER_NAME,
            "floor_target": FLOOR_15_HEIGHT,
            "last_updated": datetime.now().isoformat(),
            "data_points": []
        }

    with open(data_file, 'r') as f:
        return json.load(f)


def save_data(data):
    """Save heights data to JSON file."""
    data_file = Path("data/heights.json")
    data_file.parent.mkdir(parents=True, exist_ok=True)

    with open(data_file, 'w') as f:
        json.dump(data, f, indent=2)


def get_existing_timestamps(data):
    """Get set of existing timestamps to avoid duplicates."""
    timestamps = set()
    for point in data.get("data_points", []):
        # Normalize timestamp format for comparison
        ts = point.get("timestamp", "")
        # Remove microseconds for comparison
        ts_normalized = ts.split(".")[0].replace("Z", "")
        timestamps.add(ts_normalized)
    return timestamps


def main():
    """Main backfill function."""
    print("=" * 60)
    print("Historic Height Data Backfill")
    print("=" * 60)

    token = get_github_token()

    # Fetch workflow runs in two batches to work around GitHub's 1000-result pagination limit
    # Batch 1: Recent runs (newest 1000)
    runs_recent = fetch_workflow_runs(token)

    # Batch 2: Older runs (before Jan 6, 2026) to capture Dec 11 - Jan 5 data
    print(f"\n{'=' * 60}")
    print("Fetching older runs (before 2026-01-06) to get complete history...")
    print('=' * 60)
    runs_old = fetch_workflow_runs(token, created_filter="<2026-01-06")

    # Combine all runs
    runs = runs_recent + runs_old
    print(f"\nTotal runs fetched: {len(runs)} (recent: {len(runs_recent)}, old: {len(runs_old)})")

    if not runs:
        print("No workflow runs found.")
        return

    # Sort runs by creation time (oldest first)
    runs.sort(key=lambda r: r.get("created_at", ""))

    # Load existing data
    data = load_existing_data()
    existing_timestamps = get_existing_timestamps(data)

    print(f"\nExisting data points: {len(data.get('data_points', []))}")
    print(f"\nProcessing {len(runs)} workflow runs...")
    print("-" * 60)

    new_points = []
    skipped = 0
    failed = 0

    for i, run in enumerate(runs):
        run_id = run.get("id")
        created_at = run.get("created_at", "")
        conclusion = run.get("conclusion", "unknown")

        # Skip failed runs
        if conclusion != "success":
            failed += 1
            continue

        # Normalize timestamp for comparison
        ts_normalized = created_at.replace("Z", "").split(".")[0]

        # Skip if we already have this timestamp
        if ts_normalized in existing_timestamps:
            skipped += 1
            continue

        print(f"  [{i+1}/{len(runs)}] Run {run_id} at {created_at}...", end=" ", flush=True)

        # Fetch and parse logs (with small delay to avoid rate limits)
        logs = fetch_run_logs(token, run_id)
        time.sleep(0.5)  # Be nice to the API
        height, is_playing = parse_height_from_logs(logs)

        if height is not None or is_playing is False:
            data_point = {
                "timestamp": created_at,
                "live_height": height,
                "is_playing": is_playing
            }
            new_points.append(data_point)
            print(f"Height: {height}m" if height else "Not playing")
        else:
            print("No data found")

    print("-" * 60)
    print(f"New data points extracted: {len(new_points)}")
    print(f"Skipped (already exists): {skipped}")
    print(f"Failed runs: {failed}")

    if new_points:
        # Merge new points with existing data
        all_points = data.get("data_points", []) + new_points

        # Sort all points by timestamp
        all_points.sort(key=lambda p: p.get("timestamp", ""))

        # Remove duplicates based on timestamp (keep first occurrence)
        seen = set()
        unique_points = []
        for point in all_points:
            ts = point.get("timestamp", "").split(".")[0].replace("Z", "")
            if ts not in seen:
                seen.add(ts)
                unique_points.append(point)

        data["data_points"] = unique_points
        data["last_updated"] = datetime.now().isoformat()

        # Save updated data
        save_data(data)

        print(f"\nData saved! Total data points: {len(unique_points)}")
    else:
        print("\nNo new data to add.")

    print("=" * 60)


if __name__ == "__main__":
    main()
