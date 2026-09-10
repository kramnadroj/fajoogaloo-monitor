#!/usr/bin/env python3
"""
Regression test for monitor_player.get_player_height().

Reproduces the bug where a player who IS currently live (present in
/live_heights/global) but is NOT present in the capped, unsorted
/leaderboard/global snapshot was reported as "not found", causing the
monitor to silently stop recording data points.

Run with: python3 -m unittest tests.test_monitor_player -v
"""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import monitor_player  # noqa: E402


def _mock_response(json_data, status_code=200):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    resp.raise_for_status.return_value = None
    return resp


class GetPlayerHeightLiveButUnlistedTest(unittest.TestCase):
    """fajoogaloo-shaped scenario: live right now, absent from the leaderboard snapshot."""

    def setUp(self):
        # /leaderboard/global returns its usual capped ~100 entries, none of which
        # are our player (this is realistic: 18k+ registered players, ~100 shown).
        self.leaderboard_payload = [
            {"rank": 7843, "wsid": "aaa", "height": 122.0, "name": "SomeoneElse"},
        ]
        # /live_heights/global returns only currently-active players.
        self.live_global_payload = [
            {
                "display_name": "fajoogaloo",
                "user_id": "0c184d3a-29e9-4af5-9c5b-f927f349311c",
                "height": 39.5,
                "rank": 1,
            }
        ]

    def _fake_get(self, url, timeout=10):
        if url.endswith("/live_heights/global"):
            return _mock_response(self.live_global_payload)
        if url.endswith("/leaderboard/global"):
            return _mock_response(self.leaderboard_payload)
        raise AssertionError(f"Unexpected URL requested: {url}")

    def test_finds_live_player_missing_from_leaderboard_snapshot(self):
        with patch("monitor_player.requests.get", side_effect=self._fake_get):
            height, player_data = monitor_player.get_player_height("fajoogaloo")

        self.assertIsNotNone(
            player_data,
            "player should be found via /live_heights/global even though absent "
            "from the capped /leaderboard/global snapshot",
        )
        self.assertEqual(height, 39.5)

    def test_not_live_but_on_leaderboard_reports_pb_not_none_data(self):
        # Player has no live session but does appear on the leaderboard snapshot.
        self.live_global_payload = []
        self.leaderboard_payload = [
            {"rank": 42, "wsid": "bbb", "height": 300.0, "name": "fajoogaloo"},
        ]
        with patch("monitor_player.requests.get", side_effect=self._fake_get):
            height, player_data = monitor_player.get_player_height("fajoogaloo")

        self.assertIsNone(height)
        self.assertIsNotNone(player_data)
        self.assertEqual(player_data.get("pb_height"), 300.0)

    def test_truly_unknown_player_returns_none_none(self):
        self.live_global_payload = []
        self.leaderboard_payload = [
            {"rank": 1, "wsid": "ccc", "height": 900.0, "name": "SomeoneElse"},
        ]
        with patch("monitor_player.requests.get", side_effect=self._fake_get):
            height, player_data = monitor_player.get_player_height("fajoogaloo")

        self.assertIsNone(height)
        self.assertIsNone(player_data)


if __name__ == "__main__":
    unittest.main()
