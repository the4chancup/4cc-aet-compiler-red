#!/usr/bin/env python3
"""Unit tests for lib/players_process.py (roster, links, split, instantiation).

Run with: python -m pytest Engines/test/test_players_process.py
"""
import os
import sys
from pathlib import Path

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "Engines"))

from python.lib import players_process as pp  # noqa: E402 (path setup above)


@pytest.fixture(autouse=True)
def non_interactive(monkeypatch):
    monkeypatch.setattr(pp, "pause", lambda *a, **k: None)


def make_folder(export_path, name, files=None):
    folder = os.path.join(export_path, "Players", name)
    os.makedirs(folder, exist_ok=True)
    for file_name, content in (files or {}).items():
        with open(os.path.join(folder, file_name), "wb") as f:
            f.write(content)
    return folder


def write_players_txt(export_path, lines):
    with open(os.path.join(export_path, "players.txt"), "w", encoding="utf8") as f:
        f.write("\n".join(lines) + "\n")


# --- roster -----------------------------------------------------------------

def test_roster_folder_names(tmp_path):
    make_folder(tmp_path, "01 - Messi")
    make_folder(tmp_path, "11 - Suarez")
    folders, error = pp.roster_build(tmp_path, slots_max=23)
    assert error is None
    assert folders["01 - Messi"]["slots"] == ["01"]
    assert folders["11 - Suarez"]["name_part"] == "Suarez"


def test_roster_dash_optional(tmp_path):
    # The dash is optional: a plain space separator works too
    make_folder(tmp_path, "04 Messi")
    folders, error = pp.roster_build(tmp_path, slots_max=23)
    assert error is None
    assert folders["04 Messi"]["name_part"] == "Messi"


def test_roster_players_txt_authoritative(tmp_path):
    # The roster entry names the folder's name part (prefix stripped)
    make_folder(tmp_path, "07 - Whatever")
    write_players_txt(tmp_path, ["04 Whatever", "11 Whatever"])
    folders, error = pp.roster_build(tmp_path, slots_max=23)
    assert error is None
    assert folders["07 - Whatever"]["slots"] == ["04", "11"]


def test_roster_prefixless_folder_match(tmp_path):
    make_folder(tmp_path, "Messi")
    write_players_txt(tmp_path, ["04 Messi"])
    folders, error = pp.roster_build(tmp_path, slots_max=23)
    assert error is None
    assert folders["Messi"]["slots"] == ["04"]


def test_roster_ambiguous_match(tmp_path):
    make_folder(tmp_path, "Messi")
    make_folder(tmp_path, "11 - Messi")
    write_players_txt(tmp_path, ["04 Messi"])
    folders, error = pp.roster_build(tmp_path, slots_max=23)
    assert folders is None and "more than one folder" in error


def test_roster_same_name_part(tmp_path):
    make_folder(tmp_path, "01 - Messi")
    make_folder(tmp_path, "02 - MESSI")
    folders, error = pp.roster_build(tmp_path, slots_max=23)
    assert folders is None and "name part" in error


def test_roster_duplicate_slot_folder_names(tmp_path):
    make_folder(tmp_path, "01 - A")
    make_folder(tmp_path, "01 - B")
    folders, error = pp.roster_build(tmp_path, slots_max=23)
    assert folders is None and "duplicate slot" in error


def test_roster_unlisted_folder_discarded(tmp_path):
    make_folder(tmp_path, "01 - Messi")
    make_folder(tmp_path, "02 - Extra")
    write_players_txt(tmp_path, ["01 Messi"])
    folders, error = pp.roster_build(tmp_path, slots_max=23)
    assert error is None
    assert set(folders) == {"01 - Messi"}


def test_roster_slot_out_of_range_skipped(tmp_path):
    make_folder(tmp_path, "99 - Messi")
    folders, error = pp.roster_build(tmp_path, slots_max=23)
    assert error is None and folders == {}


def test_roster_duplicate_slot_players_txt(tmp_path):
    make_folder(tmp_path, "Messi")
    write_players_txt(tmp_path, ["04 Messi", "04 Messi"])
    folders, error = pp.roster_build(tmp_path, slots_max=23)
    assert folders is None and "duplicate slot" in error


# --- link resolution --------------------------------------------------------

def link_case(tmp_path, shared_name, files):
    """Stage a shared boots folder and a player folder with a link file."""
    export = tmp_path / "export"
    shared = export / "Staging" / "Boots" / shared_name
    shared.mkdir(parents=True)
    for file_name, content in files.items():
        (shared / file_name).write_bytes(content)
    folder = make_folder(export, "01 - Player", {"Crocs.boots": b""})
    return export, Path(folder), shared


def test_link_merge_copies_contents(tmp_path):
    export, folder, shared = link_case(tmp_path, "Crocs", {"boots.fmdl": b"A"})
    set_asides, error = pp.links_resolve(folder, os.path.join(export, "Staging"), False)
    assert error is False and set_asides == []
    assert os.path.isfile(os.path.join(folder, "boots.fmdl"))
    assert not os.path.exists(os.path.join(folder, "Crocs.boots"))


def test_link_id_token_match(tmp_path):
    export, folder, shared = link_case(tmp_path, "k0101 - Crocs", {"boots.fmdl": b"A"})
    set_asides, error = pp.links_resolve(folder, os.path.join(export, "Staging"), False)
    assert error is False
    assert os.path.isfile(os.path.join(folder, "boots.fmdl"))


def test_link_bare_id_name(tmp_path):
    export = tmp_path / "export"
    shared = export / "Staging" / "Boots" / "k0101"
    shared.mkdir(parents=True)
    (shared / "boots.fmdl").write_bytes(b"A")
    folder = make_folder(str(export), "01 - Player", {"k0101.boots": b""})
    set_asides, error = pp.links_resolve(folder, str(export / "Staging"), False)
    assert error is False
    assert os.path.isfile(os.path.join(folder, "boots.fmdl"))


def test_link_identical_bytes_dedupe(tmp_path):
    export, folder, shared = link_case(tmp_path, "Crocs", {"boots.fmdl": b"SAME", "keep.txt": b"local"})
    (folder / "boots.fmdl").write_bytes(b"SAME")
    set_asides, error = pp.links_resolve(folder, os.path.join(export, "Staging"), False)
    assert error is False
    assert (folder / "boots.fmdl").read_bytes() == b"SAME"
    assert (folder / "keep.txt").read_bytes() == b"local"


def test_link_collision_set_aside(tmp_path):
    export, folder, shared = link_case(tmp_path, "Crocs", {"boots.fmdl": b"SHARED"})
    (folder / "boots.fmdl").write_bytes(b"LOCAL")
    set_asides, error = pp.links_resolve(folder, os.path.join(export, "Staging"), False)
    assert error is False and set_asides == [("boots", "Crocs")]
    # The local file is untouched and the shared folder stays in staging
    assert (folder / "boots.fmdl").read_bytes() == b"LOCAL"
    assert (shared / "boots.fmdl").read_bytes() == b"SHARED"


def test_link_ingame_face_set_aside(tmp_path):
    export, folder, shared = link_case(tmp_path, "Crocs", {"boots.fmdl": b"A"})
    (folder / "ingame_face").write_bytes(b"")
    set_asides, error = pp.links_resolve(folder, os.path.join(export, "Staging"), True)
    assert error is False and set_asides == [("boots", "Crocs")]
    assert not os.path.exists(os.path.join(folder, "boots.fmdl"))


def test_link_face_ingame_face_error(tmp_path):
    export = tmp_path / "export"
    shared = export / "Staging" / "Faces" / "Longhair"
    shared.mkdir(parents=True)
    (shared / "hair.fmdl").write_bytes(b"A")
    folder = make_folder(str(export), "01 - Player", {"Longhair.face": b"", "ingame_face": b""})
    set_asides, error = pp.links_resolve(folder, str(export / "Staging"), True)
    assert error is True


def test_link_missing_target(tmp_path):
    folder = make_folder(tmp_path, "01 - Player", {"Ghost.boots": b""})
    set_asides, error = pp.links_resolve(folder, str(tmp_path / "Staging"), False)
    assert error is True


# --- categorization ---------------------------------------------------------

def test_split_fox_categories(tmp_path):
    folder = make_folder(tmp_path, "01 - P", {
        "face_high.fmdl": b"f", "boots.fmdl": b"b", "kit_boots.fmdl": b"kb",
        "glove_l.fmdl": b"gl", "boots.skl": b"s", "tex.dds": b"t",
        "face_diff.bin": b"d",
    })
    error = pp.player_folder_split(folder, fox_mode=True)
    assert error is None
    assert os.path.isfile(os.path.join(folder, "face", "face_high.fmdl"))
    assert os.path.isfile(os.path.join(folder, "face", "face_diff.bin"))
    assert os.path.isfile(os.path.join(folder, "boots", "boots.fmdl"))
    assert os.path.isfile(os.path.join(folder, "boots", "kit_boots.fmdl"))
    assert os.path.isfile(os.path.join(folder, "boots", "boots.skl"))
    assert os.path.isfile(os.path.join(folder, "gloves", "glove_l.fmdl"))
    # The texture stays in the folder root for the relocation pass
    assert os.path.isfile(os.path.join(folder, "tex.dds"))


def test_split_prefox_no_split(tmp_path):
    folder = make_folder(tmp_path, "01 - P", {
        "face_high_win32.model": b"m", "materials.mtl": b"m", "tex.dds": b"t",
    })
    error = pp.player_folder_split(folder, fox_mode=False)
    assert error is None
    assert os.path.isfile(os.path.join(folder, "face", "face_high_win32.model"))
    assert os.path.isfile(os.path.join(folder, "face", "materials.mtl"))
    assert os.path.isfile(os.path.join(folder, "tex.dds"))
    assert not os.path.exists(os.path.join(folder, "boots"))


def test_split_prefox_ingame_face_routing(tmp_path):
    folder = make_folder(tmp_path, "01 - P", {
        "ingame_face": b"", "boots.model": b"b", "boots.mtl": b"m",
        "glove_l.model": b"g", "glove_l.mtl": b"gm", "tex.dds": b"t",
    })
    error = pp.player_folder_split(folder, fox_mode=False)
    assert error is None
    assert os.path.isfile(os.path.join(folder, "boots", "boots.model"))
    assert os.path.isfile(os.path.join(folder, "boots", "boots.mtl"))
    assert os.path.isfile(os.path.join(folder, "gloves", "glove_l.model"))
    assert not os.path.exists(os.path.join(folder, "face"))


def test_split_marker_with_face_content_error(tmp_path):
    folder = make_folder(tmp_path, "01 - P", {"ingame_face": b"", "face_high.fmdl": b"f"})
    error = pp.player_folder_split(folder, fox_mode=True)
    assert error == "ingame_face with face content"


# --- end to end -------------------------------------------------------------

# A real FMDL: the Fox texture-path rewrite parses model files, so the e2e tests
# must feed valid ones (a boots model reused as a stand-in face model)
with open(os.path.join(TEST_DIR, "boots.fmdl"), "rb") as _f:
    REAL_FMDL = _f.read()


def run_players_process(export_path, monkeypatch, team_id="702", id_range=(101, 140), fox_mode=True):
    monkeypatch.setattr(pp, "teams_list_range_get", lambda team_id: id_range)
    return pp.players_process(str(export_path), team_id, "/test/", fox_mode=fox_mode)


def test_players_process_fox(tmp_path, monkeypatch):
    folder = make_folder(tmp_path, "01 - Messi", {
        "face_high.fmdl": REAL_FMDL, "boots.fmdl": REAL_FMDL, "tex.dds": b"t",
        "portrait.dds": b"p",
    })
    run_players_process(tmp_path, monkeypatch)
    assert os.path.isfile(os.path.join(tmp_path, "Faces", "XXX01 - Messi", "face_high.fmdl"))
    assert os.path.isfile(os.path.join(tmp_path, "Boots", "k0101 - Messi", "boots.fmdl"))
    # The texture was relocated to the per-player common folder
    assert os.path.isfile(os.path.join(tmp_path, "Common", "Messi", "tex.dds"))
    assert not os.path.exists(os.path.join(folder, "tex.dds"))
    assert os.path.isfile(os.path.join(tmp_path, "Portraits", "player_70201.dds"))
    assert not os.path.exists(os.path.join(tmp_path, "Players"))


def test_players_process_multi_map_portraits(tmp_path, monkeypatch):
    make_folder(tmp_path, "Messi", {"portrait.dds": b"p", "face_high.fmdl": REAL_FMDL})
    write_players_txt(tmp_path, ["01 Messi", "02 Messi"])
    run_players_process(tmp_path, monkeypatch)
    assert os.path.isfile(os.path.join(tmp_path, "Portraits", "player_70201.dds"))
    assert os.path.isfile(os.path.join(tmp_path, "Portraits", "player_70202.dds"))
    # The player folder itself is gone; both slots' face folders exist
    assert os.path.isdir(os.path.join(tmp_path, "Faces", "XXX01 - Messi"))
    assert os.path.isdir(os.path.join(tmp_path, "Faces", "XXX02 - Messi"))


def test_players_process_shared_folder_and_staging(tmp_path, monkeypatch):
    # One shared boots folder linked by two players; its instantiated name equals
    # the shared folder's name to prove the staging move prevents the clash
    shared = tmp_path / "Boots" / "k0101 - Same"
    shared.mkdir(parents=True)
    (shared / "boots.fmdl").write_bytes(b"B")
    make_folder(tmp_path, "01 - Same", {"Same.boots": b"", "face_high.fmdl": b"f"})
    make_folder(tmp_path, "02 - Other", {"Same.boots": b"", "face_high.fmdl": b"f"})
    write_players_txt(tmp_path, ["01 Same", "02 Other"])
    run_players_process(tmp_path, monkeypatch)
    assert os.path.isfile(os.path.join(tmp_path, "Boots", "k0101 - Same", "boots.fmdl"))
    assert os.path.isfile(os.path.join(tmp_path, "Boots", "k0102 - Other", "boots.fmdl"))
    assert os.path.isfile(os.path.join(tmp_path, "Faces", "XXX01 - Same", "face_high.fmdl"))
    assert os.path.isfile(os.path.join(tmp_path, "Faces", "XXX02 - Other", "face_high.fmdl"))
    assert not os.path.exists(os.path.join(tmp_path, "Staging"))
    assert not os.path.exists(os.path.join(tmp_path, "Players"))


def test_players_process_missing_range_keeps_face(tmp_path, monkeypatch):
    make_folder(tmp_path, "01 - Messi", {"face_high.fmdl": b"f", "boots.fmdl": b"b"})
    monkeypatch.setattr(pp, "teams_list_range_get", lambda team_id: None)
    result = pp.players_process(str(tmp_path), "702", "/test/", fox_mode=True)
    assert result is False
    assert os.path.isfile(os.path.join(tmp_path, "Faces", "XXX01 - Messi", "face_high.fmdl"))
    assert not os.path.exists(os.path.join(tmp_path, "Boots"))


def test_players_process_id_out_of_range(tmp_path, monkeypatch):
    make_folder(tmp_path, "Messi", {"face_high.fmdl": b"f", "boots.fmdl": b"b"})
    write_players_txt(tmp_path, ["01 Messi", "02 Messi", "03 Messi"])
    # Range 101-102: slots 01/02 fit, slot 03 (id 103) is out of bounds
    run_players_process(tmp_path, monkeypatch, id_range=(101, 102))
    assert os.path.isfile(os.path.join(tmp_path, "Boots", "k0101 - Messi", "boots.fmdl"))
    assert os.path.isfile(os.path.join(tmp_path, "Boots", "k0102 - Messi", "boots.fmdl"))
    assert not os.path.exists(os.path.join(tmp_path, "Boots", "k0103 - Messi"))
    assert os.path.isfile(os.path.join(tmp_path, "Faces", "XXX03 - Messi", "face_high.fmdl"))


def test_players_process_prefox_ingame_face(tmp_path, monkeypatch):
    folder = make_folder(tmp_path, "01 - Messi", {
        "ingame_face": b"", "boots.model": b"b", "boots.mtl": b'path="./tex.dds"',
        "tex.dds": b"t",
    })
    run_players_process(tmp_path, monkeypatch, fox_mode=False)
    # No face folder; the boots folder carries the models with MTLs pointing at
    # the per-player common folder, and the texture lives in Common/
    assert not os.path.exists(os.path.join(tmp_path, "Faces"))
    boots = os.path.join(tmp_path, "Boots", "k0101 - Messi")
    assert os.path.isfile(os.path.join(boots, "boots.model"))
    with open(os.path.join(boots, "boots.mtl"), encoding="utf8") as f:
        content = f.read()
    assert 'path="model/character/uniform/common/XXX/Messi/tex.dds"' in content
    assert os.path.isfile(os.path.join(tmp_path, "Common", "Messi", "tex.dds"))


# --- referee flat format -----------------------------------------------------

def test_referee_players_txt_flat_format(tmp_path, monkeypatch):
    from python.lib.referee_tools import referee_export_process

    export = tmp_path / "refs export"
    export.mkdir()
    folder = make_folder(export, "RefA", {"hair_high.fmdl": REAL_FMDL, "boots.fmdl": REAL_FMDL})
    write_players_txt(export, ["1 RefA", "2 RefA"])

    result = referee_export_process(str(export), fox_mode=True)
    assert result is False
    # Both slots instantiated from the one flat folder; fixed referee IDs
    assert os.path.isfile(os.path.join(export, "Faces", "referee001 - RefA", "hair_high.fmdl"))
    assert os.path.isfile(os.path.join(export, "Faces", "referee002 - RefA", "hair_high.fmdl"))
    assert os.path.isfile(os.path.join(export, "Boots", "k9901 - RefA", "boots.fmdl"))
    assert os.path.isfile(os.path.join(export, "Boots", "k9902 - RefA", "boots.fmdl"))
    assert not os.path.exists(os.path.join(export, "Players"))
    assert not os.path.exists(os.path.join(export, "Staging"))


def test_referee_refs_txt_and_players_txt_error(tmp_path, monkeypatch):
    from python.lib.referee_tools import referee_export_process

    export = tmp_path / "refs export"
    export.mkdir()
    make_folder(export, "RefA")
    (export / "refs.txt").write_text("1 RefA\n", encoding="utf8")
    write_players_txt(export, ["1 RefA"])
    assert referee_export_process(str(export), fox_mode=True) is True


def test_referee_refs_txt_and_players_txt_error(tmp_path, monkeypatch):
    from python.lib.referee_tools import referee_export_process

    export = tmp_path / "refs export"
    export.mkdir()
    make_folder(export, "RefA")
    (export / "refs.txt").write_text("1 RefA\n", encoding="utf8")
    write_players_txt(export, ["1 RefA"])
    assert referee_export_process(str(export), fox_mode=True) is True


# --- kits --------------------------------------------------------------------

def test_kits_process_slot_mapping(tmp_path):
    export = tmp_path
    os.makedirs(os.path.join(export, "Kits", "p1"))
    os.makedirs(os.path.join(export, "Kits", "p2"))
    os.makedirs(os.path.join(export, "Kits", "g1"))
    with open(os.path.join(export, "Kits", "p1", "config.bin"), "wb") as f:
        f.write(b"config1")
    with open(os.path.join(export, "Kits", "p1", "kit.dds"), "wb") as f:
        f.write(b"main")
    with open(os.path.join(export, "Kits", "p1", "kit_mask.dds"), "wb") as f:
        f.write(b"mask")
    with open(os.path.join(export, "Kits", "p2", "kit_chest.dds"), "wb") as f:
        f.write(b"chest")
    with open(os.path.join(export, "Kits", "g1", "config.bin"), "wb") as f:
        f.write(b"configgk")

    assert pp.kits_process(str(export)) is False
    assert not os.path.exists(os.path.join(export, "Kits"))
    assert os.path.isfile(os.path.join(export, "Kit Configs", "XXX_DEF_1st_realUni.bin"))
    assert os.path.isfile(os.path.join(export, "Kit Configs", "XXX_DEF_GK1st_realUni.bin"))
    assert os.path.isfile(os.path.join(export, "Kit Textures", "u0XXXp1.dds"))
    assert os.path.isfile(os.path.join(export, "Kit Textures", "u0XXXp1_mask.dds"))
    assert os.path.isfile(os.path.join(export, "Kit Textures", "u0XXXp2_chest.dds"))


def test_kits_process_invalid_slot(tmp_path):
    export = tmp_path
    os.makedirs(os.path.join(export, "Kits", "p10"))
    with open(os.path.join(export, "Kits", "p10", "kit.dds"), "wb") as f:
        f.write(b"x")
    assert pp.kits_process(str(export)) is False
    assert not os.path.exists(os.path.join(export, "Kits"))
    assert not os.path.exists(os.path.join(export, "Kit Textures"))


def test_kits_process_duplicate_slot(tmp_path):
    export = tmp_path
    os.makedirs(os.path.join(export, "Kits", "p2"))
    with open(os.path.join(export, "Kits", "p2", "kit.dds"), "wb") as f:
        f.write(b"x")
    os.makedirs(os.path.join(export, "Kit Textures"))
    with open(os.path.join(export, "Kit Textures", "u0XXXp2.dds"), "wb") as f:
        f.write(b"y")
    assert pp.kits_process(str(export)) is True
