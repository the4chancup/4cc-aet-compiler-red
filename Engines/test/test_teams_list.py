#!/usr/bin/env python3
"""Unit tests for the teams_list.txt TSV format helpers.

Run with: python -m pytest Engines/test/test_teams_list.py
"""
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "Engines"))

from python.lib import team_id_get  # noqa: E402 (path setup above)
from python.lib.team_id_get import id_search, teams_list_range_get, teams_list_validate  # noqa: E402


VALID_LIST = "ID\tName\tMinBootsID\tMaxBootsID\n701\t/3/\t101\t125\n702\t/a/\t126\t150\n"
OLD_LIST = "ID Name\n701 /3/\n"
MALFORMED_LIST = "ID\tName\tMinBootsID\tMaxBootsID\n701\t/3/\tabc\t140\n"
RANGELESS_LIST = "ID\tName\tMinBootsID\tMaxBootsID\n701\t/3/\n"


@pytest.fixture
def teams_list(tmp_path, monkeypatch):
    path = tmp_path / "teams_list.txt"
    monkeypatch.setattr(team_id_get, "TEAMS_LIST_PATH", str(path))
    # The fatal paths pause before exiting; keep the tests non-interactive
    monkeypatch.setattr(team_id_get, "pause", lambda *a, **k: None)
    return path


def write_list(path, content):
    with open(path, "w", encoding="utf8", newline="") as f:
        f.write(content)


def test_range_present(teams_list):
    write_list(teams_list, VALID_LIST)
    assert teams_list_range_get("701") == (101, 125)
    assert teams_list_range_get("702") == (126, 150)


def test_range_missing_team(teams_list):
    write_list(teams_list, VALID_LIST)
    assert teams_list_range_get("999") is None


def test_range_malformed_row(teams_list):
    write_list(teams_list, MALFORMED_LIST)
    assert teams_list_range_get("701") is None


def test_range_rangeless_row(teams_list):
    write_list(teams_list, RANGELESS_LIST)
    assert teams_list_range_get("701") is None


def test_validate_accepts_tsv(teams_list):
    write_list(teams_list, VALID_LIST)
    teams_list_validate()


def test_validate_accepts_rangeless_rows(teams_list):
    # Newly added teams are written rangeless on purpose
    write_list(teams_list, RANGELESS_LIST)
    teams_list_validate()


def test_validate_rejects_old_format(teams_list):
    write_list(teams_list, OLD_LIST)
    with pytest.raises(SystemExit):
        teams_list_validate()


def test_validate_rejects_malformed_row(teams_list):
    write_list(teams_list, "ID\tName\tMinBootsID\tMaxBootsID\n701 only spaces\n")
    with pytest.raises(SystemExit):
        teams_list_validate()


def test_id_search_resolves_shipped_list():
    """id_search must resolve every single-word team of the shipped list."""
    monkeypath = os.path.join(ROOT, "teams_list.txt")
    original = team_id_get.TEAMS_LIST_PATH
    team_id_get.TEAMS_LIST_PATH = monkeypath
    try:
        with open(monkeypath, "r", encoding="utf8") as f:
            lines = f.readlines()[1:]
    finally:
        team_id_get.TEAMS_LIST_PATH = original

    checked = 0
    for line in lines:
        parts = line.rstrip("\r\n").split('\t')
        if len(parts) < 2 or " " in parts[1]:
            # Multi-word names cannot be matched by design (first-word lookup)
            continue
        assert id_search(parts[1]) == parts[0], parts
        checked += 1
    # 220 teams shipped; the multi-word "Invitational N" placeholder rows are
    # skipped by design, leaving 125 checkable names
    assert checked == 125
