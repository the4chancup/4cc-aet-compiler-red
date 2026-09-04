"""Old-to-new export upgrader (Pre-Studio plan side project).

Converts old-format team exports from exports_to_upgrade/ into the Pre-Studio
unified player-folder format in exports_upgraded/, using an EDIT00000000
savefile to resolve each player's boots/gloves IDs. Fox savefiles only (PES 19
and 21, auto-detected); referee exports are not upgraded.
"""
import os
import re
import shutil
import sys

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(TOOLS_DIR))
sys.path.insert(0, os.path.join(ROOT, "Engines"))

from python.lib.players_process import KIT_SUFFIX_SLOTS, folder_name_part
from python.lib.savefile import ParseError, load_players, player_boots_gloves, player_name
from python.lib.team_id_get import id_search, teams_list_range_get

EXPORTS_SOURCE = "exports_to_upgrade"
EXPORTS_OUTPUT = "exports_upgraded"


def sanitize_name(name):
    """Strip medal colour codes (a \\x11c marker followed by 8 hex digits, e.g.
    '\\x11ce5de00ff' before the actual name), any remaining control characters,
    the characters Windows rejects in folder names, and trailing dots/spaces."""
    name = re.sub("\x11c[0-9a-fA-F]{8}", "", name)
    return re.sub(r'[\\/:*?"<>|\x00-\x1f]', "", name).rstrip(". ").strip()


def team_name_folder(export_name):
    """The /first-word/ team key, same rule as the compiler."""
    words = re.findall(r"[^.\s\-\+\_]+", export_name)
    if not words:
        return None
    return f"/{words[0].lower()}/"


def folder_conflicts(src_folder, dest_folder):
    """Relative paths present in both folders with different bytes."""
    conflicts = []
    for base, _dirs, files in os.walk(src_folder):
        for file_name in files:
            src_path = os.path.join(base, file_name)
            rel = os.path.relpath(src_path, src_folder)
            dest_path = os.path.join(dest_folder, rel)
            if os.path.isfile(dest_path):
                with open(src_path, "rb") as f1, open(dest_path, "rb") as f2:
                    if f1.read() != f2.read():
                        conflicts.append(rel)
    return conflicts


def move_folder_contents(src_folder, dest_folder, skip=()):
    """Move every file of a folder into another, skipping the given relative paths."""
    os.makedirs(dest_folder, exist_ok=True)
    for base, _dirs, files in os.walk(src_folder):
        for file_name in files:
            src_path = os.path.join(base, file_name)
            rel = os.path.relpath(src_path, src_folder)
            if rel in skip:
                continue
            dest_path = os.path.join(dest_folder, rel)
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            shutil.move(src_path, dest_path)


def upgrade_export(source_path, output_path, team_id, players, version):
    shutil.rmtree(output_path, ignore_errors=True)
    shutil.copytree(source_path, output_path)

    faces_path = os.path.join(output_path, "Faces")
    boots_path = os.path.join(output_path, "Boots")
    gloves_path = os.path.join(output_path, "Gloves")
    other_path = os.path.join(output_path, "Other")
    players_path = os.path.join(output_path, "Players")

    # Collect the old item folders
    face_folders = {}
    if os.path.isdir(faces_path):
        for name in os.listdir(faces_path):
            match = re.match(r"^.{3}(\d{2})", name)
            if match and 1 <= int(match.group(1)) <= 23:
                face_folders[match.group(1)] = name

    boots_folders = {}
    if os.path.isdir(boots_path):
        for name in os.listdir(boots_path):
            match = re.match(r"^k(\d{4})", name)
            if match:
                boots_folders[int(match.group(1))] = name

    gloves_folders = {}
    if os.path.isdir(gloves_path):
        for name in os.listdir(gloves_path):
            match = re.match(r"^g(\d{4})", name)
            if match:
                gloves_folders[int(match.group(1))] = name

    # Each player's worn IDs, from the savefile records
    team_players = {}
    for nn in range(1, 24):
        record = players.get(int(team_id) * 100 + nn)
        if record is None:
            continue
        boots_id, gloves_id = player_boots_gloves(record, version)
        team_players[f"{nn:02d}"] = {"record": record, "boots_id": boots_id, "gloves_id": gloves_id}

    def wearer_count(worn_key, folder_id):
        return sum(1 for player in team_players.values() if player[worn_key] == folder_id)

    # Per player: build the unified player folder
    for nn in sorted(set(face_folders) | set(team_players)):
        player_record = team_players.get(nn)
        face_name = face_folders.get(nn)

        # Folder name: the old face folder's suffix (the author's name), then
        # the savefile player name (medal colour codes stripped), then NN alone
        folder_name = None
        if face_name is not None:
            suffix = sanitize_name(face_name[5:].strip(" -_"))
            if suffix:
                folder_name = f"{nn} - {suffix}"
        if folder_name is None and player_record is not None:
            name = sanitize_name(player_name(player_record["record"], version).decode("utf8", "replace"))
            if name:
                folder_name = f"{nn} - {name}"
        if folder_name is None:
            folder_name = nn

        player_path = os.path.join(players_path, folder_name)

        boots_id = player_record["boots_id"] if player_record else None
        gloves_id = player_record["gloves_id"] if player_record else None
        boots_name = boots_folders.get(boots_id) if boots_id else None
        gloves_name = gloves_folders.get(gloves_id) if gloves_id else None

        # Resolve the boots/gloves disposition: merged in, or kept as a shared
        # folder + link file (multi-wearer, ingame_face players, or file name
        # collisions with the face content)
        dispositions = []
        for category, folder_name_worn, worn_key, worn_id in (
            ("boots", boots_name, "boots_id", boots_id),
            ("gloves", gloves_name, "gloves_id", gloves_id),
        ):
            if folder_name_worn is None:
                continue

            shared = (not has_face(face_folders, nn)) or wearer_count(worn_key, worn_id) > 1

            if not shared:
                conflicts = folder_conflicts(os.path.join(output_path, category.capitalize(), folder_name_worn),
                                             player_path)
                if conflicts:
                    print(f"- Warning - Conflicting file names between the face folder and the "
                          f"{category} folder {folder_name_worn} for player {folder_name}:")
                    for rel in conflicts:
                        print(f"    {rel}")
                    print("- The folder will be kept as a shared folder + link file instead of being merged in")
                    shared = True

            dispositions.append((category, folder_name_worn, shared))

        if has_face(face_folders, nn) or dispositions:
            os.makedirs(player_path, exist_ok=True)

        if face_name is not None:
            move_folder_contents(os.path.join(faces_path, face_name), player_path)
            shutil.rmtree(os.path.join(faces_path, face_name))

        for category, folder_name_worn, shared in dispositions:
            category_path = os.path.join(output_path, category.capitalize())
            if shared:
                # Keep the folder as a shared source (ID token stripped from its
                # name) and link it from the player folder
                shared_name = folder_name_part(folder_name_worn)
                shared_path = os.path.join(category_path, shared_name)
                source_path = os.path.join(category_path, folder_name_worn)
                if os.path.abspath(shared_path) != os.path.abspath(source_path) and os.path.isdir(source_path):
                    move_folder_contents(source_path, shared_path)
                    shutil.rmtree(source_path)
                with open(os.path.join(player_path, f"{shared_name}.{category}"), "w"):
                    pass
            else:
                # Worn by one player: merge the contents into the player folder
                move_folder_contents(os.path.join(category_path, folder_name_worn), player_path)
                shutil.rmtree(os.path.join(category_path, folder_name_worn))

    # Boots/gloves folders referenced by no player of the team end in Other/
    for category_name, category_path, folder_map, worn_key in (
        ("Boots", boots_path, boots_folders, "boots_id"),
        ("Gloves", gloves_path, gloves_folders, "gloves_id"),
    ):
        for folder_name_worn in list(folder_map.values()):
            folder_path = os.path.join(category_path, folder_name_worn)
            if not os.path.isdir(folder_path):
                continue  # consumed (renamed to a shared folder) or merged
            folder_id = next(i for i, n in folder_map.items() if n == folder_name_worn)
            if wearer_count(worn_key, folder_id) == 0:
                os.makedirs(other_path, exist_ok=True)
                shutil.move(folder_path, os.path.join(other_path, folder_name_worn))
                print(f"- Warning - {category_name}/{folder_name_worn} is worn by no player of the team "
                      f"- Moved to Other/")

    # Remove the consumed old item folders
    if os.path.isdir(faces_path) and not os.listdir(faces_path):
        os.rmdir(faces_path)

    # Kits: inverse of the compiler's slot map
    kit_configs_path = os.path.join(output_path, "Kit Configs")
    kit_textures_path = os.path.join(output_path, "Kit Textures")
    if os.path.isdir(kit_configs_path):
        for file_name in os.listdir(kit_configs_path):
            match = re.match(r"^[A-Za-z0-9]{3}_DEF_(.+)_realUni\.bin$", file_name, re.IGNORECASE)
            if not match or match.group(1) not in KIT_SUFFIX_SLOTS:
                continue
            slot = KIT_SUFFIX_SLOTS[match.group(1)]
            slot_path = os.path.join(output_path, "Kits", slot)
            os.makedirs(slot_path, exist_ok=True)
            shutil.move(os.path.join(kit_configs_path, file_name), os.path.join(slot_path, "config.bin"))
    if os.path.isdir(kit_textures_path):
        for file_name in os.listdir(kit_textures_path):
            match = re.match(r"^u0[A-Za-z0-9]{3}(p[1-9]|g1)(.+)$", file_name, re.IGNORECASE)
            if not match:
                continue
            slot, suffix = match.group(1).lower(), match.group(2)
            slot_path = os.path.join(output_path, "Kits", slot)
            os.makedirs(slot_path, exist_ok=True)
            shutil.move(os.path.join(kit_textures_path, file_name),
                        os.path.join(slot_path, f"kit{suffix}"))
    for folder in (kit_configs_path, kit_textures_path):
        if os.path.isdir(folder) and not os.listdir(folder):
            os.rmdir(folder)

    # Print the savefile IDs next to the new range so the admin can see what the
    # savefile must be changed to (the compiler assigns MinBootsID + NN - 1)
    id_range = teams_list_range_get(team_id)
    if id_range is None:
        print("- Warning - No ID range found for the team in teams_list.txt")
        return

    min_id, max_id = id_range
    print(f"- Team range: {min_id}-{max_id} (the compiler assigns MinBootsID + NN - 1)")
    for nn in sorted(team_players):
        boots_id = team_players[nn]["boots_id"]
        gloves_id = team_players[nn]["gloves_id"]
        new_id = min_id + int(nn) - 1
        print(f"- Player {nn}: savefile boots k{boots_id:04d} gloves g{gloves_id:04d}"
              f" -> new ID {new_id} (boots k{new_id:04d} / gloves g{new_id:04d})")


def has_face(face_folders, nn):
    return nn in face_folders


def extract_export(source_path, dest_path):
    if os.path.isdir(source_path):
        shutil.copytree(source_path, dest_path, ignore=shutil.ignore_patterns("*.db", "*.ini"))
        return
    ext = os.path.splitext(source_path)[1].lower()
    if ext == ".zip":
        shutil.unpack_archive(source_path, dest_path, "zip")
    elif ext == ".7z":
        import py7zr
        with py7zr.SevenZipFile(source_path, mode="r") as archive:
            archive.extractall(dest_path)
    else:
        raise ValueError(f"Unsupported archive type: {ext}")


def pause_exit():
    print("-")
    try:
        input("Press Enter to exit... ")
    except EOFError:
        pass
    sys.exit()


def main():
    # chdir to the compiler root: the teams list is read from there via
    # relative paths, while the upgrader's own folders live next to this script
    os.chdir(ROOT)

    exports_source_path = os.path.join(TOOLS_DIR, EXPORTS_SOURCE)
    exports_output_path = os.path.join(TOOLS_DIR, EXPORTS_OUTPUT)
    savefile_path = os.path.join(TOOLS_DIR, "EDIT00000000")

    if not os.path.isdir(exports_source_path):
        print(f"- FATAL ERROR - The {EXPORTS_SOURCE} folder was not found in the upgrader's folder")
        pause_exit()
    if not os.path.isfile(savefile_path):
        print("- FATAL ERROR - EDIT00000000 was not found in the upgrader's folder")
        print("- Place the cup's current savefile in the upgrader's folder and run again")
        pause_exit()

    try:
        version, players = load_players(savefile_path)
    except ParseError as e:
        print(f"- FATAL ERROR - Could not read the savefile: {e}")
        pause_exit()
    print(f"- Savefile loaded: PES {version} ({len(players)} players)")

    os.makedirs(exports_output_path, exist_ok=True)

    exports_list = [item for item in os.listdir(exports_source_path)
                    if os.path.isdir(os.path.join(exports_source_path, item))
                    or os.path.splitext(item)[1].lower() in (".zip", ".7z")]
    if not exports_list:
        print(f"- No exports found in {EXPORTS_SOURCE}/")
        pause_exit()

    for export_name in exports_list:
        print("-")
        print(f"- Upgrading {export_name}...")

        source_path = os.path.join(exports_source_path, export_name)
        export_name_clean = export_name if os.path.isdir(source_path) else os.path.splitext(export_name)[0]

        key = team_name_folder(export_name)
        if key == "/refs/":
            print("- Referee exports are not upgraded (the compiler keeps reading the old layout)")
            continue
        if key is None:
            print("- ERROR - Unusable export name - Skipped")
            continue

        team_id = id_search(key)
        if team_id is None:
            print(f"- ERROR - Team {key} not found in teams_list.txt - Skipped")
            continue

        output_path = os.path.join(exports_output_path, export_name_clean)
        temp_path = output_path + "_temp"

        try:
            shutil.rmtree(temp_path, ignore_errors=True)
            extract_export(source_path, temp_path)
            upgrade_export(temp_path, output_path, team_id, players, version)
            shutil.rmtree(temp_path, ignore_errors=True)
            print(f"- Upgraded export saved to {EXPORTS_OUTPUT}/{export_name_clean}")
        except Exception as e:
            shutil.rmtree(temp_path, ignore_errors=True)
            print(f"- ERROR - Failed to upgrade the export: {e}")

    print("-")
    print("- Done")
    pause_exit()


if __name__ == "__main__":
    main()
