#!/usr/bin/env python3
"""
Generate time-series chart showing player height progress over time.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Configuration
DATA_FILE = Path("data/heights.json")
OUTPUT_FILE = Path("charts/height_progress.png")

# Floor heights mapping (floor name -> height in meters)
FLOOR_HEIGHTS = {
    "Floor 00": 4.0,
    "Floor 01": 138.0,
    "Floor 02": 266.0,
    "Floor 03": 394.0,
    "Floor 04": 522.0,
    "Floor 05": 650.0,
    "Floor 06": 816.0,
    "Floor 07": 906.0,
    "Floor 08": 1026.0,
    "Floor 09": 1170.0,
    "Floor 10": 1296.0,
    "Floor 11": 1426.0,
    "Floor 12": 1554.0,
    "Floor 13": 1680.0,
    "Floor 14": 1824.0,
    "Floor 15": 1938.0,
    "The End": 2100.0,
}

def load_height_data():
    """
    Load height data from JSON file.

    Returns:
        dict: Height data or None if file doesn't exist
    """
    if not DATA_FILE.exists():
        print(f"No data file found at {DATA_FILE}")
        return None

    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}", file=sys.stderr)
        return None

def generate_chart(data):
    """
    Generate time-series chart from height data.

    Args:
        data: Height data dictionary with data_points list
    """
    if not data or 'data_points' not in data:
        print("No data points to chart")
        return

    data_points = data['data_points']
    if len(data_points) == 0:
        print("No data points to chart")
        return

    # Extract timestamps and heights (only when playing)
    timestamps = []
    heights = []

    for point in data_points:
        if point['is_playing'] and point['live_height'] is not None:
            timestamps.append(datetime.fromisoformat(point['timestamp']))
            heights.append(point['live_height'])

    if len(timestamps) == 0:
        print("No active playing sessions recorded yet")
        # Create empty chart with just the target line
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.axhline(y=data['floor_target'], color='red', linestyle='--',
                   linewidth=2, label=f"Floor 15 Target ({data['floor_target']}m)")
        ax.set_xlabel('Time', fontsize=12)
        ax.set_ylabel('Floor', fontsize=12)
        ax.set_title('No Active Sessions Recorded Yet', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        # Set y-axis ticks to floor numbers
        floor_heights = list(FLOOR_HEIGHTS.values())
        floor_labels = list(FLOOR_HEIGHTS.keys())
        ax.set_yticks(floor_heights)
        ax.set_yticklabels(floor_labels, fontsize=8)
        ax.set_ylim(0, FLOOR_HEIGHTS["The End"])
        plt.tight_layout()
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(OUTPUT_FILE, dpi=150, bbox_inches='tight')
        print(f"Empty chart saved to {OUTPUT_FILE}")
        return

    # Create figure and axis
    fig, ax = plt.subplots(figsize=(12, 6))

    # Plot height progression
    ax.plot(timestamps, heights, marker='o', linewidth=2, markersize=4,
            color='#2E86AB', label='Live Height')

    # Add Floor 15 target line
    ax.axhline(y=data['floor_target'], color='red', linestyle='--',
               linewidth=2, label=f"Floor 15 Target ({data['floor_target']}m)")

    # Calculate statistics
    current_height = heights[-1] if heights else 0
    peak_height = max(heights) if heights else 0
    total_checks = len(data_points)
    active_sessions = len([p for p in data_points if p['is_playing']])
    progress_pct = (current_height / data['floor_target']) * 100 if current_height else 0

    # Set title with current stats
    title = f"{data['player']}'s Deep Dip 2 Progress\n"
    title += f"Current: {current_height:.1f}m | Peak: {peak_height:.1f}m | "
    title += f"Progress: {progress_pct:.1f}% | Checks: {total_checks} | Sessions: {active_sessions}"
    ax.set_title(title, fontsize=14, fontweight='bold')

    # Labels and formatting
    ax.set_xlabel('Time', fontsize=12)
    ax.set_ylabel('Floor', fontsize=12)
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)

    # Format x-axis dates (date only, no time)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
    fig.autofmt_xdate()

    # Set y-axis ticks to floor numbers
    floor_heights = list(FLOOR_HEIGHTS.values())
    floor_labels = list(FLOOR_HEIGHTS.keys())
    ax.set_yticks(floor_heights)
    ax.set_yticklabels(floor_labels, fontsize=8)

    # Ensure y-axis includes Floor 15 target and some headroom
    ax.set_ylim(0, max(data['floor_target'] * 1.1, FLOOR_HEIGHTS["The End"]))

    # Save chart
    plt.tight_layout()
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUTPUT_FILE, dpi=150, bbox_inches='tight')
    print(f"✅ Chart generated: {OUTPUT_FILE}")
    print(f"   Current height: {current_height:.1f}m")
    print(f"   Peak height: {peak_height:.1f}m")
    print(f"   Progress: {progress_pct:.1f}%")

def main():
    """Main chart generation function."""
    print("Generating height progress chart...")

    # Load data
    data = load_height_data()
    if data is None:
        sys.exit(1)

    # Generate chart
    generate_chart(data)

if __name__ == "__main__":
    main()
