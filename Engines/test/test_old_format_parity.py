#!/usr/bin/env python3
"""Old-format parity harness for the Pre-Studio work.

Builds old-format team and referee exports, runs the extraction stage in-process
(Fox mode, no PES folder needed), and hashes the resulting extracted_teams /
extracted_referees trees.

Usage:
    python Engines/test/test_old_format_parity.py record   -> write the baseline
    python Engines/test/test_old_format_parity.py          -> compare against it
    python Engines/test/test_old_format_parity.py newfmt   -> new-format smoke run
    python Engines/test/test_old_format_parity.py kits     -> Kits/ vs old kit layout
    python Engines/test/test_old_format_parity.py fox      -> Fox old-vs-new comparison
    python Engines/test/test_old_format_parity.py prefox   -> PES 16 old-vs-new comparison

Any diff in compare mode means a refactor changed old-format output and must be
justified against the parity gates in the plan.
"""
import hashlib
import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "Engines"))

EXPORTS_TO_ADD = os.path.join(ROOT, "exports_to_add")
EXTRACTED_TEAMS = os.path.join(ROOT, "extracted_teams")
EXTRACTED_REFEREES = os.path.join(ROOT, "extracted_referees")
BASELINE = os.path.join(TEST_DIR, "baseline_old_format.json")

TEAM_EXPORT = os.path.join(EXPORTS_TO_ADD, "parityteam")
REFS_EXPORT = os.path.join(EXPORTS_TO_ADD, "refs_paritytest")


def build_team_export():
    """Old-format team export: portraits, ingame_face, boots, gloves, kits, note."""
    shutil.rmtree(TEAM_EXPORT, ignore_errors=True)

    face1 = os.path.join(TEAM_EXPORT, "Faces", "XXX01 - Alpha")
    os.makedirs(face1)
    shutil.copy(os.path.join(TEST_DIR,"boots.fmdl"), os.path.join(face1, "hair_high.fmdl"))
    shutil.copy(os.path.join(TEST_DIR,"texture.dds"), os.path.join(face1, "portrait.dds"))

    face2 = os.path.join(TEAM_EXPORT, "Faces", "XXX02 - Beta")
    os.makedirs(face2)
    shutil.copy(os.path.join(TEST_DIR,"boots.fmdl"), os.path.join(face2, "hair_high.fmdl"))
    shutil.copy(os.path.join(TEST_DIR,"texture.dds"), os.path.join(face2, "portrait.dds"))
    with open(os.path.join(face2, "ingame_face"), "w"):
        pass

    boots = os.path.join(TEAM_EXPORT, "Boots", "k0101 - Boots")
    os.makedirs(boots)
    shutil.copy(os.path.join(TEST_DIR,"boots.fmdl"), os.path.join(boots, "boots.fmdl"))

    gloves = os.path.join(TEAM_EXPORT, "Gloves", "g0101 - Gloves")
    os.makedirs(gloves)
    shutil.copy(os.path.join(TEST_DIR,"boots.fmdl"), os.path.join(gloves, "glove_l.fmdl"))

    with open(os.path.join(TEAM_EXPORT, "Note.txt"), "w", encoding="utf8") as f:
        f.write("Team: /a/\nKit Colors:\n- 1st player: 255 255 255 - 255 255 255\n")

    kit_textures = os.path.join(TEAM_EXPORT, "Kit Textures")
    os.makedirs(kit_textures)
    shutil.copy(os.path.join(TEST_DIR,"texture.dds"), os.path.join(kit_textures, "u0XXXp1.dds"))

    kit_configs = os.path.join(TEAM_EXPORT, "Kit Configs")
    os.makedirs(kit_configs)
    shutil.copy(
        os.path.join(ROOT, "Engines", "templates", "XXX_DEF_xxx_realUni.bin"),
        os.path.join(kit_configs, "XXX_DEF_1st_realUni.bin"),
    )


def build_refs_export():
    """Old-format referee export: refs.txt + one referee with face/boots/gloves."""
    shutil.rmtree(REFS_EXPORT, ignore_errors=True)
    os.makedirs(REFS_EXPORT)

    with open(os.path.join(REFS_EXPORT, "refs.txt"), "w", encoding="utf8") as f:
        # Both slots map to the same folder (multi-mapped slot, per the plan)
        f.write("1 RefA\n2 RefA\n")

    ref = os.path.join(REFS_EXPORT, "Players", "RefA")
    for folder, file_name in (("face", "hair_high.fmdl"), ("boots", "boots.fmdl"), ("gloves", "glove_l.fmdl")):
        os.makedirs(os.path.join(ref, folder))
        shutil.copy(os.path.join(TEST_DIR,"boots.fmdl"), os.path.join(ref, folder, file_name))
    # One texture shared by the face and the boots folders (exercises the common relocation)
    shutil.copy(os.path.join(TEST_DIR,"texture.dds"), os.path.join(ref, "face", "shared.dds"))
    shutil.copy(os.path.join(TEST_DIR,"texture.dds"), os.path.join(ref, "boots", "shared.dds"))


def clean_fixtures():
    shutil.rmtree(TEAM_EXPORT, ignore_errors=True)
    shutil.rmtree(REFS_EXPORT, ignore_errors=True)


def run_extraction(pes_version=19):
    """Run extracted_from_exports in-process with preset env variables.

    Presetting the environment skips settings.ini entirely (settings_init and
    settings_missing_check only fill variables that are not already set).
    """
    os.environ.update({
        "PES_VERSION": str(pes_version),
        "CPK_NAME": "4cc_90_test",
        "PES_FOLDER_PATH": "unused",
        "MOVE_CPKS": "0",
        "BINS_UPDATING": "0",
        "RUN_PES": "0",
        "MULTICPK_MODE": "0",
        "DDS_COMPRESSION": "0",
        "PAUSE_ALLOW": "0",
        "STRICT_FILE_TYPE_CHECK": "1",
        "PASS_THROUGH": "0",
        "ADMIN_FORCING": "0",
        "UPDATES_CHECK": "0",
        "ALL_IN_ONE": "0",
        "CACHE_CLEAR": "0",
    })
    from python.extracted_from_exports import extracted_from_exports
    extracted_from_exports()


def tree_manifest(root):
    manifest = {}
    for base, _dirs, files in os.walk(root):
        for file_name in files:
            path = os.path.join(base, file_name)
            rel = os.path.relpath(path, root).replace(os.sep, "/")
            with open(path, "rb") as f:
                manifest[rel] = hashlib.sha256(f.read()).hexdigest()
    return manifest


def extracted_manifest():
    manifest = {}
    for label, root in (("teams", EXTRACTED_TEAMS), ("referees", EXTRACTED_REFEREES)):
        if os.path.exists(root):
            for rel, digest in tree_manifest(root).items():
                manifest[f"{label}/{rel}"] = digest
    return dict(sorted(manifest.items()))


def build_newfmt_team_export():
    """New-format team export: flat player folders, a shared boots folder, kits."""
    shutil.rmtree(TEAM_EXPORT, ignore_errors=True)

    players = os.path.join(TEAM_EXPORT, "Players")
    os.makedirs(os.path.join(players, "01 - Messi"))
    shutil.copy(os.path.join(TEST_DIR,"boots.fmdl"), os.path.join(players, "01 - Messi", "face_high.fmdl"))
    shutil.copy(os.path.join(TEST_DIR,"boots.fmdl"), os.path.join(players, "01 - Messi", "boots.fmdl"))
    shutil.copy(os.path.join(TEST_DIR,"texture.dds"), os.path.join(players, "01 - Messi", "tex.dds"))
    shutil.copy(os.path.join(TEST_DIR,"texture.dds"), os.path.join(players, "01 - Messi", "portrait.dds"))

    # A shared boots folder linked by two players
    shared = os.path.join(TEAM_EXPORT, "Boots", "k0101 - Crocs")
    os.makedirs(shared)
    shutil.copy(os.path.join(TEST_DIR,"boots.fmdl"), os.path.join(shared, "boots.fmdl"))
    os.makedirs(os.path.join(players, "02 - Suarez"))
    shutil.copy(os.path.join(TEST_DIR,"boots.fmdl"), os.path.join(players, "02 - Suarez", "face_high.fmdl"))
    with open(os.path.join(players, "02 - Suarez", "Crocs.boots"), "w"):
        pass

    with open(os.path.join(TEAM_EXPORT, "Note.txt"), "w", encoding="utf8") as f:
        f.write("Team: /a/\nKit Colors:\n- 1st player: 255 255 255 - 255 255 255\n")

    kit_textures = os.path.join(TEAM_EXPORT, "Kit Textures")
    os.makedirs(kit_textures)
    shutil.copy(os.path.join(TEST_DIR,"texture.dds"), os.path.join(kit_textures, "u0XXXp1.dds"))


def build_newfmt_refs_export():
    """New-format referee export: players.txt roster with a repeated slot."""
    shutil.rmtree(REFS_EXPORT, ignore_errors=True)
    os.makedirs(REFS_EXPORT)

    with open(os.path.join(REFS_EXPORT, "players.txt"), "w", encoding="utf8") as f:
        f.write("1 RefA\n2 RefA\n")

    ref = os.path.join(REFS_EXPORT, "Players", "RefA")
    os.makedirs(ref)
    shutil.copy(os.path.join(TEST_DIR,"boots.fmdl"), os.path.join(ref, "hair_high.fmdl"))
    shutil.copy(os.path.join(TEST_DIR,"boots.fmdl"), os.path.join(ref, "boots.fmdl"))


def main():
    os.chdir(ROOT)
    mode = sys.argv[1] if len(sys.argv) > 1 else "compare"

    if mode == "newfmt":
        build_newfmt_team_export()
        build_newfmt_refs_export()
        shutil.rmtree(EXTRACTED_TEAMS, ignore_errors=True)
        shutil.rmtree(EXTRACTED_REFEREES, ignore_errors=True)

        run_extraction()
        clean_fixtures()

        print("[NEWFMT] extracted teams tree:")
        for rel in sorted(tree_manifest(EXTRACTED_TEAMS)) if os.path.exists(EXTRACTED_TEAMS) else []:
            print(f"    {rel}")
        print("[NEWFMT] extracted referees tree:")
        for rel in sorted(tree_manifest(EXTRACTED_REFEREES)) if os.path.exists(EXTRACTED_REFEREES) else []:
            print(f"    {rel}")
        return

    if mode == "kits":
        # The same kits in the new Kits/ layout and in the old item-folder layout
        # must compile to identical trees
        results = {}
        for layout in ("new", "old"):
            shutil.rmtree(TEAM_EXPORT, ignore_errors=True)
            os.makedirs(TEAM_EXPORT)
            with open(os.path.join(TEAM_EXPORT, "Note.txt"), "w", encoding="utf8") as f:
                f.write("Team: /a/\nKit Colors:\n- 1st player: 255 255 255 - 255 255 255\n")

            if layout == "new":
                kit = os.path.join(TEAM_EXPORT, "Kits", "p1")
                os.makedirs(kit)
                shutil.copy(os.path.join(TEST_DIR,"texture.dds"), os.path.join(kit, "kit.dds"))
                shutil.copy(os.path.join(ROOT, "Engines", "templates", "XXX_DEF_xxx_realUni.bin"),
                            os.path.join(kit, "config.bin"))
            else:
                configs = os.path.join(TEAM_EXPORT, "Kit Configs")
                textures = os.path.join(TEAM_EXPORT, "Kit Textures")
                os.makedirs(configs)
                os.makedirs(textures)
                shutil.copy(os.path.join(ROOT, "Engines", "templates", "XXX_DEF_xxx_realUni.bin"),
                            os.path.join(configs, "XXX_DEF_1st_realUni.bin"))
                shutil.copy(os.path.join(TEST_DIR,"texture.dds"), os.path.join(textures, "u0XXXp1.dds"))

            shutil.rmtree(EXTRACTED_TEAMS, ignore_errors=True)
            run_extraction()
            clean_fixtures()
            results[layout] = tree_manifest(EXTRACTED_TEAMS) if os.path.exists(EXTRACTED_TEAMS) else {}

        ok = results["new"] == results["old"]
        for path in sorted(set(results["new"]) ^ set(results["old"])):
            print(f"[DIFF] {'new-only' if path in results['new'] else 'old-only'}: {path}")
        for path in sorted(set(results["new"]) & set(results["old"])):
            if results["new"][path] != results["old"][path]:
                print(f"[DIFF] CHANGED: {path}")
        print(f"[KITS] {'OK - Kits/ layout compiles identically' if ok else 'FAILED'} "
              f"({len(results['new'])} files)")
        sys.exit(0 if ok else 1)

    if mode == "prefox":
        # PES 16: the new-format output equals the old-format equivalent except
        # textures living under the per-player common folder and MTL paths
        # pointing there
        results = {}
        for layout in ("new", "old"):
            shutil.rmtree(TEAM_EXPORT, ignore_errors=True)
            os.makedirs(TEAM_EXPORT)
            with open(os.path.join(TEAM_EXPORT, "Note.txt"), "w", encoding="utf8") as f:
                f.write("Team: /a/\nKit Colors:\n- 1st player: 255 255 255 - 255 255 255\n")

            model_source = os.path.join(ROOT, "Engines", "templates", "dummy.model")
            mtl_source = os.path.join(ROOT, "Engines", "templates", "dummy.mtl")
            texture_source = os.path.join(TEST_DIR,"texture.dds")

            if layout == "new":
                player = os.path.join(TEAM_EXPORT, "Players", "01 - Messi")
                os.makedirs(player)
                shutil.copy(model_source, os.path.join(player, "face_high.model"))
                shutil.copy(mtl_source, os.path.join(player, "face_high.mtl"))
                shutil.copy(texture_source, os.path.join(player, "tex.dds"))
            else:
                face = os.path.join(TEAM_EXPORT, "Faces", "XXX01 - Messi")
                os.makedirs(face)
                shutil.copy(model_source, os.path.join(face, "face_high.model"))
                shutil.copy(mtl_source, os.path.join(face, "face_high.mtl"))
                shutil.copy(texture_source, os.path.join(face, "tex.dds"))

            shutil.rmtree(EXTRACTED_TEAMS, ignore_errors=True)
            run_extraction(pes_version=16)
            clean_fixtures()
            results[layout] = tree_manifest(EXTRACTED_TEAMS) if os.path.exists(EXTRACTED_TEAMS) else {}

        print("[PREFOX] new-format tree:")
        for rel in sorted(results["new"]):
            print(f"    {rel}")
        print("[PREFOX] old-format tree:")
        for rel in sorted(results["old"]):
            print(f"    {rel}")
        return

    if mode == "fox":
        # PES 19: the new-format output equals the old-format equivalent (built
        # with the same k/g IDs) except textures under common/<team_id>/<name>/
        # and FMDL paths pointing there
        import struct as _struct

        def read_fmdl_dirs(path):
            data = open(path, "rb").read()
            s0_count = _struct.unpack("<I", data[32:36])[0]
            s1_count = _struct.unpack("<I", data[36:40])[0]
            header_length = _struct.unpack("<I", data[40:44])[0]
            s1_offset = _struct.unpack("<I", data[48:52])[0]
            texture_offset = texture_count = string_offset = string_count = 0
            blockmap0 = data[64:64 + s0_count * 8]
            for i in range(s0_count):
                btype = _struct.unpack("<H", blockmap0[i * 8:i * 8 + 2])[0]
                bitems = _struct.unpack("<H", blockmap0[i * 8 + 2:i * 8 + 4])[0]
                boffset = _struct.unpack("<I", blockmap0[i * 8 + 4:i * 8 + 8])[0]
                if btype == 6:
                    texture_offset, texture_count = boffset, bitems
                elif btype == 12:
                    string_offset, string_count = boffset, bitems
            if not (texture_count and string_count):
                return []
            # Locate the string data via blockmap 1 (segment1 block 3)
            string_data_start = 0
            blockmap1 = data[64 + s0_count * 8:64 + s0_count * 8 + s1_count * 12]
            for i in range(s1_count):
                btype = _struct.unpack("<I", blockmap1[i * 12:i * 12 + 4])[0]
                boffset = _struct.unpack("<I", blockmap1[i * 12 + 4:i * 12 + 8])[0]
                if btype == 3:
                    string_data_start = s1_offset + boffset
            lengths = []
            for i in range(string_count):
                desc = header_length + string_offset + i * 8
                lengths.append(_struct.unpack("<H", data[desc + 2:desc + 4])[0])
            strings = []
            pos = string_data_start
            for length in lengths:
                strings.append(data[pos:pos + length].decode("utf-8"))
                pos += length + 1
            dirs = set()
            for i in range(texture_count):
                entry = header_length + texture_offset + i * 4
                dirs.add(strings[_struct.unpack("<H", data[entry + 2:entry + 4])[0]])
            return sorted(dirs)

        results = {}
        fmdl_dirs = {}
        for layout in ("new", "old"):
            shutil.rmtree(TEAM_EXPORT, ignore_errors=True)
            os.makedirs(TEAM_EXPORT)
            with open(os.path.join(TEAM_EXPORT, "Note.txt"), "w", encoding="utf8") as f:
                f.write("Team: /a/\nKit Colors:\n- 1st player: 255 255 255 - 255 255 255\n")

            boots_source = os.path.join(TEST_DIR,"boots.fmdl")
            texture_source = os.path.join(TEST_DIR,"texture.dds")

            if layout == "new":
                player = os.path.join(TEAM_EXPORT, "Players", "01 - Messi")
                os.makedirs(player)
                shutil.copy(boots_source, os.path.join(player, "face_high.fmdl"))
                shutil.copy(boots_source, os.path.join(player, "boots.fmdl"))
                # Named after a texture the test FMDL actually references, so the
                # path rewrite is exercised
                shutil.copy(texture_source, os.path.join(player, "body.dds"))
            else:
                face = os.path.join(TEAM_EXPORT, "Faces", "XXX01 - Messi")
                boots = os.path.join(TEAM_EXPORT, "Boots", "k0126 - Messi")
                os.makedirs(face)
                os.makedirs(boots)
                shutil.copy(boots_source, os.path.join(face, "face_high.fmdl"))
                shutil.copy(boots_source, os.path.join(boots, "boots.fmdl"))
                shutil.copy(texture_source, os.path.join(face, "body.dds"))

            shutil.rmtree(EXTRACTED_TEAMS, ignore_errors=True)
            run_extraction(pes_version=19)
            clean_fixtures()
            results[layout] = tree_manifest(EXTRACTED_TEAMS) if os.path.exists(EXTRACTED_TEAMS) else {}
            # Snapshot the FMDL texture dirs now: the second run overwrites the
            # extracted tree
            fmdl_dirs[layout] = {
                rel: read_fmdl_dirs(os.path.join(EXTRACTED_TEAMS, rel))
                for rel in results[layout] if rel.endswith(".fmdl")
            }

        print("[FOX] new-format tree:")
        for rel in sorted(results["new"]):
            print(f"    {rel}")
        print("[FOX] old-format tree:")
        for rel in sorted(results["old"]):
            print(f"    {rel}")

        # The non-texture file sets must match; textures move to the per-player
        # common folder
        def texture_entries(manifest):
            return {p for p in manifest if p.endswith((".dds", ".ftex"))}
        new_non_tex = set(results["new"]) - texture_entries(results["new"])
        old_non_tex = set(results["old"]) - texture_entries(results["old"])
        print("[FOX] non-texture sets equal:", new_non_tex == old_non_tex)
        if new_non_tex != old_non_tex:
            print("    new-only:", sorted(new_non_tex - old_non_tex))
            print("    old-only:", sorted(old_non_tex - new_non_tex))

        # The new FMDLs' texture directories must point at the per-player common
        for rel in sorted(new_non_tex):
            if rel.endswith(".fmdl"):
                dirs = fmdl_dirs["new"].get(rel, [])
                has_player_common = any("/character/common/702/Messi/" in d for d in dirs)
                print(f"[FOX] {rel} new-format dirs: {dirs}")
                print(f"[FOX]   points at per-player common: {has_player_common}")

        # The old FMDLs must NOT point at the per-player common folder
        for rel in sorted(old_non_tex):
            if rel.endswith(".fmdl"):
                dirs = fmdl_dirs["old"].get(rel, [])
                common_dirs = [d for d in dirs if "/character/common/702/" in d]
                print(f"[FOX] {rel} old-format common dirs (must be empty): {common_dirs}")
        return

    build_team_export()
    build_refs_export()
    shutil.rmtree(EXTRACTED_TEAMS, ignore_errors=True)
    shutil.rmtree(EXTRACTED_REFEREES, ignore_errors=True)

    run_extraction()

    clean_fixtures()
    manifest = extracted_manifest()
    print(f"[PARITY] extracted tree: {len(manifest)} files")

    if mode == "record":
        with open(BASELINE, "w", encoding="utf8") as f:
            json.dump(manifest, f, indent=1, sort_keys=True)
        print(f"[PARITY] Baseline recorded: {len(manifest)} entries")
        return

    with open(BASELINE, "r", encoding="utf8") as f:
        baseline = json.load(f)

    missing = sorted(set(baseline) - set(manifest))
    added = sorted(set(manifest) - set(baseline))
    changed = sorted(p for p in set(baseline) & set(manifest) if baseline[p] != manifest[p])

    for label, paths in (("MISSING", missing), ("ADDED", added), ("CHANGED", changed)):
        for path in paths:
            print(f"[DIFF] {label}: {path}")

    ok = not (missing or added or changed)
    print(f"[PARITY] {'OK - old-format output unchanged' if ok else 'FAILED'}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
