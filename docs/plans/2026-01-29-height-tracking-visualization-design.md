# Height Tracking & Visualization System Design

**Date**: 2026-01-29
**Project**: Deep Dip 2 Player Monitor
**Feature**: Historical height tracking with automated chart generation

## Overview

Track fajoogaloo's height over time across all monitoring runs and generate visual charts showing progress toward Floor 15 (1500m). The system records every check (every 10 minutes) and maintains a complete historical timeline.

## Requirements

- Record height data from every GitHub Actions run
- Store historical data in version-controlled JSON file
- Generate visual chart showing progress over time
- Automatically update chart and commit to repo
- Display chart in README for easy viewing

## Design

### 1. Data Storage & Collection

**File Structure**:
```
data/
  heights.json          # Historical height data
charts/
  height_progress.png   # Generated chart image
```

**Data Format** (`data/heights.json`):
```json
{
  "player": "fajoogaloo",
  "floor_target": 1500.0,
  "last_updated": "2026-01-29T12:00:00Z",
  "data_points": [
    {
      "timestamp": "2026-01-29T10:00:00Z",
      "live_height": 1245.5,
      "is_playing": true
    },
    {
      "timestamp": "2026-01-29T10:10:00Z",
      "live_height": null,
      "is_playing": false
    }
  ]
}
```

**Data Captured**:
- ISO 8601 timestamp of each check
- Current live height (null if not playing)
- Boolean flag for active session

**Recording Logic**:
- Modify `monitor_player.py` to add `record_height_data()` function
- After fetching player data, append to `data/heights.json`
- Create file with initial structure if doesn't exist
- Keep all historical data (no pruning)

### 2. Chart Generation

**Script**: `generate_chart.py`

**Chart Specifications**:
- **Type**: Time-series line chart (matplotlib)
- **X-axis**: Timeline (timestamps, auto-formatted)
- **Y-axis**: Height in meters
- **Data line**: Blue line connecting points where `is_playing: true`
- **Target line**: Red dashed horizontal line at 1500m
- **Gaps**: Don't connect points when player not active
- **Title**: Shows current height and progress percentage
- **Metadata**: Display total checks and active sessions

**Visual Style**:
- Clean design suitable for README embedding
- Grid lines for readability
- Auto-scaling Y-axis (always includes Floor 15 line)
- Date/time formatting adapts to data span (hours/days/weeks)

**Output**: `charts/height_progress.png`

### 3. GitHub Actions Integration

**Workflow Updates** (`.github/workflows/monitor.yml`):

**New workflow steps**:
1. **Record data** (after monitor check):
   - Run updated `monitor_player.py`
   - Appends data point to `data/heights.json`

2. **Generate chart**:
   - Install matplotlib: `pip install matplotlib`
   - Run `generate_chart.py`
   - Creates/updates `charts/height_progress.png`

3. **Commit changes**:
   - Configure git (bot identity)
   - Stage `data/heights.json` and `charts/height_progress.png`
   - Commit: "Update height data: [timestamp] - [height]m"
   - Push to repo

**Permissions**:
- Add `contents: write` to workflow permissions

**Execution Logic**:
- Always record data (even when not playing)
- Always generate chart (full history)
- Discord notification only on Floor 15 reached (unchanged)

### 4. README Integration

**Updates to README.md**:

Add progress section at top:
```markdown
## Current Progress

![Height Progress Chart](charts/height_progress.png)

*Chart updates every 10 minutes when monitoring runs*
```

**Statistics Section**:
- Latest height check result
- Total monitoring checks performed
- Peak height achieved
- Progress to Floor 15 target

### 5. Error Handling & Edge Cases

**Data Integrity**:
- **Missing file**: Create `data/heights.json` with initial structure
- **Corrupted JSON**: Backup corrupt file, reinitialize
- **API failures**: Record timestamp with null height, `is_playing: false`
- **Chart generation failure**: Log error, don't block workflow

**Edge Cases**:
- **First run**: Initialize empty data file with metadata
- **Player not found**: Record as null height, not playing
- **No live session**: Record as null height, `is_playing: false`
- **Git conflicts**: Use `git pull --rebase` before push
- **Large files**: Keep all data initially (can add pruning later)

**Chart Rendering**:
- **No data**: Show empty chart with axes and target line
- **Only nulls**: Display "No active sessions recorded yet"
- **Single point**: Render as dot, not line
- **Date range**: Auto-adjust X-axis formatting based on span

## Implementation Order

1. Create directory structure (`data/`, `charts/`)
2. Add `record_height_data()` function to `monitor_player.py`
3. Create `generate_chart.py` script
4. Update `requirements.txt` (add matplotlib)
5. Modify `.github/workflows/monitor.yml`
6. Update README.md with chart display
7. Test locally with sample data
8. Deploy and verify automated workflow

## Dependencies

- `matplotlib` - Chart generation
- `requests` - Already installed (API calls)
- Git write permissions in GitHub Actions

## Success Criteria

- ✅ Every monitoring run records height data
- ✅ Chart automatically updates every 10 minutes
- ✅ Chart displays correctly in GitHub README
- ✅ Historical data persists across runs
- ✅ Handles player offline gracefully
- ✅ No workflow failures from new features
