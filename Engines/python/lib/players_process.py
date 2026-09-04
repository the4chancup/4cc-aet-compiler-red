import os
import re
import shutil
import logging
import filecmp

from .portraits_move import portraits_move
from .referee_tools import move_textures_to_common, update_folder_paths
from .team_id_get import teams_list_range_get
from .utils.FILE_INFO import FOX_BOOTS_FMDL_NAMES, FOX_GLOVES_FMDL_NAMES
from .utils.file_management import get_files_list, remove_readonly
from .utils.name_editing import strip_fmdl_prefix
from .utils.pausing import pause


PLAYERS_SLOTS_MIN = 1
FOLDER_NUMBER_REGEX = re.compile(r"^(\d{2})(?:\s*-\s*|\s+)(.+)$")
# Optional leading ID/number token of a shared folder or roster entry
# ("k0101 - Crocs", "g0567 Crocs", "XXX12 - Longhair", "04 - Messi")
NAME_TOKEN_REGEX = re.compile(r"^[A-Za-z]{0,3}\d{2,4}(?:\s*-\s*|\s+)(.+)$")

STAGING_FOLDER_NAME = "Staging"

# Kit slots and their kit-config suffixes (the old XXX_DEF_<kit>_realUni.bin names)
KIT_SLOT_SUFFIXES = {
    "p1": "1st", "p2": "2nd", "p3": "3rd", "p4": "4th", "p5": "5th",
    "p6": "6th", "p7": "7th", "p8": "8th", "p9": "9th", "g1": "GK1st",
}
KIT_SUFFIX_SLOTS = {suffix: slot for slot, suffix in KIT_SLOT_SUFFIXES.items()}


def folder_name_part(folder_name):
    """Strip a folder's optional leading ID/number token (the match key for link
    targets and roster entries)."""
    match = NAME_TOKEN_REGEX.match(folder_name)
    if match:
        return match.group(1)
    return folder_name


def players_txt_read(players_txt_path):
    """Process a players file and return a mapping of slot numbers to folder entries.

    Same grammar as the refs list: "NN <folder name>", blank lines ignored.
    Returns (mappings, error) where error describes a duplicate slot, else None.
    """
    slot_mappings = {}
    with open(players_txt_path, 'r', encoding='utf8') as f:
        for line in f:
            if not line.strip():
                continue
            match = re.match(r'(\d+)\s+(.+)', line.strip())
            if match:
                slot, folder_entry = match.groups()
                if slot in slot_mappings:
                    return None, slot
                slot_mappings[slot] = folder_entry
    return slot_mappings, None


def roster_build(export_path, slots_max):
    """Build the folder → slots mapping for a Players/ export folder.

    A root players.txt is authoritative: every folder must be listed and the slot
    comes solely from the roster line. Without one, the "NN - Name" folder names
    assign the slots. Returns (folders, error) where folders maps each distinct
    folder name to {"slots": [...], "name_part": str} and error is an
    export-discarding message or None.
    """
    players_path = os.path.join(export_path, "Players")
    folders = {}

    all_folders = [folder for folder in os.listdir(players_path)
                   if os.path.isdir(os.path.join(players_path, folder))]

    if os.path.isfile(os.path.join(export_path, "players.txt")):

        slot_mappings, duplicate_slot = players_txt_read(os.path.join(export_path, "players.txt"))
        if duplicate_slot is not None:
            return None, f"duplicate slot {duplicate_slot} in players.txt"

        matched_folders = set()
        for slot, folder_entry in slot_mappings.items():
            if not (slot.isdigit() and PLAYERS_SLOTS_MIN <= int(slot) <= slots_max):
                logging.error( "-")
                logging.error( f"- ERROR - Slot {slot} outside the {PLAYERS_SLOTS_MIN:02d}-{slots_max:02d} range")
                logging.error( "- This slot will be skipped")
                continue

            # Match the entry against the folders' name parts (prefix stripped)
            targets = [folder for folder in all_folders
                       if folder_name_part(folder).lower() == folder_entry.lower()]
            if not targets:
                logging.error( "-")
                logging.error( "- ERROR - players.txt lists a folder that does not exist")
                logging.error(f"- Folder name:    {folder_entry}")
                logging.error( "- This slot will be skipped")
                continue
            if len(targets) > 1:
                return None, f"the players.txt entry \"{folder_entry}\" matches more than one folder"

            matched_folders.add(targets[0])
            folder_info = folders.setdefault(targets[0], {"slots": [], "name_part": folder_name_part(targets[0])})
            folder_info["slots"].append(slot)

        # Folders not listed in the roster are discarded
        for folder in all_folders:
            if folder not in matched_folders:
                logging.error( "-")
                logging.error( "- ERROR - Unlisted folder in the Players folder")
                logging.error(f"- Folder name:    {folder}")
                logging.error( "- This folder will be discarded")

    else:

        for folder in all_folders:

            number = FOLDER_NUMBER_REGEX.match(folder)
            if not number:
                logging.error( "-")
                logging.error( "- ERROR - Unnumbered folder in the Players folder")
                logging.error(f"- Folder name:    {folder}")
                logging.error( "- This folder will be discarded")
                continue

            slot = number.group(1)
            if not (PLAYERS_SLOTS_MIN <= int(slot) <= slots_max):
                logging.error( "-")
                logging.error( f"- ERROR - Slot {slot} outside the {PLAYERS_SLOTS_MIN:02d}-{slots_max:02d} range")
                logging.error(f"- Folder name:    {folder}")
                logging.error( "- This folder will be discarded")
                continue

            if any(slot in info["slots"] for info in folders.values()):
                return None, f"duplicate slot {slot} in the Players folder"

            folders[folder] = {"slots": [slot], "name_part": number.group(2)}

    # Two folders with the same name part collide in the per-player Common folder
    seen_name_parts = {}
    for folder, info in folders.items():
        name_key = info["name_part"].lower()
        if name_key in seen_name_parts:
            return None, f"two folders share the name part \"{info['name_part']}\""
        seen_name_parts[name_key] = folder

    return folders, None


def links_resolve(folder_path, staging_path, ingame_face, consumed=None):
    """Resolve a player folder's link files against the staged shared folders.

    Link files are empty "<name>.face", "<name>.boots" or "<name>.gloves" files (a
    stray ".txt" suffix is accepted). The shared folder's files are copied into the
    player folder; on a file name collision with different bytes the whole shared
    folder is set aside instead (emitted as the player's own separate folder at
    instantiation). Under ingame_face, boots/gloves links are always set aside and a
    face link is an error.

    Returns (set_asides, error): the list of (category, shared_folder_name) set
    asides and whether the player folder must be discarded. Shared folders that
    were consumed (merged in or set aside) are added to the "consumed" set.
    """
    set_asides = []
    consumed = consumed if consumed is not None else set()

    for category in ("face", "boots", "gloves"):

        for file_name in get_files_list(folder_path):
            lower_name = file_name.lower()
            suffix = f".{category}"
            if lower_name.endswith(suffix + ".txt"):
                link_name = file_name[:-len(suffix) - 4]
            elif lower_name.endswith(suffix):
                link_name = file_name[:-len(suffix)]
            else:
                continue

            link_path = os.path.join(folder_path, file_name)

            category_folder = category.capitalize()
            category_path = os.path.join(staging_path, category_folder)
            targets = []
            if os.path.isdir(category_path):
                for shared_name in os.listdir(category_path):
                    if (shared_name.lower() == link_name.lower() or
                            folder_name_part(shared_name).lower() == link_name.lower()):
                        targets.append(shared_name)

            if len(targets) != 1:
                logging.error( "-")
                if not targets:
                    logging.error( "- ERROR - A link file points to a shared folder that does not exist")
                else:
                    logging.error( "- ERROR - A link file matches more than one shared folder")
                logging.error(f"- Link file:     {file_name}")
                logging.error(f"- Shared folder: {category_folder}/{link_name}")
                logging.error( "- This player folder will be discarded")
                pause()
                return [], True

            if category == "face" and ingame_face:
                logging.error( "-")
                logging.error( "- ERROR - A face link is present in an ingame_face player folder")
                logging.error(f"- Link file:     {file_name}")
                logging.error( "- This player folder will be discarded")
                pause()
                return [], True

            shared_path = os.path.join(category_path, targets[0])

            # Under ingame_face, boots/gloves links are always set aside instead of
            # copied in (one uniform rule on both engines, matching the upgrader)
            set_aside = ingame_face

            if not set_aside:
                # File name collisions (against local files and earlier link copies
                # alike): identical bytes are skipped, different bytes set the whole
                # shared folder aside
                collision = False
                for item_rel in get_files_list(shared_path, recursive=True):
                    item_path = os.path.join(shared_path, item_rel)
                    dest_path = os.path.join(folder_path, item_rel)
                    if os.path.isfile(dest_path) and not filecmp.cmp(item_path, dest_path, shallow=False):
                        collision = True
                        break

                if collision:
                    logging.error( "-")
                    logging.error( "- ERROR - Conflicting file names between a shared folder and a player folder")
                    logging.error(f"- Shared folder: {category_folder}/{targets[0]}")
                    logging.error(f"- Player folder: {os.path.basename(folder_path)}")
                    if category == "face":
                        logging.error( "- A colliding face link has no separate folder to fall back to")
                        logging.error( "- This player folder will be discarded")
                        pause()
                        return [], True
                    logging.error( "- The shared folder will be emitted as this player's own")
                    logging.error( "- separate boots/gloves folder instead of being merged in")
                    pause()
                    set_aside = True

            if set_aside:
                set_asides.append((category, targets[0]))
            else:
                # Copy the shared folder's files in, skipping identical ones
                for item_rel in get_files_list(shared_path, recursive=True):
                    src_path = os.path.join(shared_path, item_rel)
                    dest_path = os.path.join(folder_path, item_rel)
                    if os.path.isfile(dest_path):
                        continue
                    os.makedirs(os.path.dirname(dest_path) or folder_path, exist_ok=True)
                    shutil.copy2(src_path, dest_path)

            consumed.add(os.path.join(category_folder, targets[0]))
            os.remove(link_path)

    return set_asides, False


def player_folder_split(folder_path, fox_mode):
    """Categorize a player folder's files into face/, boots/ and gloves/ subfolders.

    Textures and the ingame_face marker stay in the folder's root for the
    relocation pass. On pre-Fox everything becomes face content, except local
    boots/gloves models under ingame_face, which are routed to boots/ and gloves/
    (the face folder will not be emitted). Returns an error message when the
    player folder must be discarded, else None.
    """
    marker = os.path.exists(os.path.join(folder_path, "ingame_face")) or \
             os.path.exists(os.path.join(folder_path, "ingame_face.txt"))

    model_categories = {}   # file stem (lowercase) → category, for .skl/.mtl pairing
    moves = []

    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        if not os.path.isfile(file_path):
            continue

        lower_name = file_name.lower()
        stem = os.path.splitext(file_name)[0].lower()

        if lower_name.endswith(('.dds', '.ftex')):
            continue  # textures stay for the relocation pass

        if lower_name == "ingame_face" or lower_name == "ingame_face.txt":
            continue  # marker stays for the instantiation pass

        if fox_mode:
            if lower_name.endswith(".fmdl"):
                if strip_fmdl_prefix(file_name, FOX_BOOTS_FMDL_NAMES) is not None:
                    category = "boots"
                elif strip_fmdl_prefix(file_name, FOX_GLOVES_FMDL_NAMES) is not None:
                    category = "gloves"
                else:
                    category = "face"
            elif lower_name.endswith(".skl"):
                continue  # paired below
            else:
                category = "face"
        else:
            if lower_name.endswith(".model"):
                if marker and stem.startswith("boots"):
                    category = "boots"
                elif marker and (stem.startswith("glove_l") or stem.startswith("glove_r")):
                    category = "gloves"
                else:
                    category = "face"
            elif lower_name.endswith((".mtl", ".skl")):
                continue  # paired below
            else:
                category = "face"

        model_categories[stem] = category
        moves.append((file_name, category))

    # .skl files (and pre-Fox .mtl files) travel with their model
    pair_suffixes = (".skl",) if fox_mode else (".mtl", ".skl")
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        if not os.path.isfile(file_path):
            continue
        lower_name = file_name.lower()
        if not lower_name.endswith(pair_suffixes):
            continue
        stem = os.path.splitext(file_name)[0].lower()
        moves.append((file_name, model_categories.get(stem, "face")))

    # The ingame_face marker must not sit alongside face content
    if marker and any(category == "face" for _file_name, category in moves):
        logging.error( "-")
        logging.error( "- ERROR - An ingame_face marker is present alongside face content")
        logging.error(f"- Player folder: {os.path.basename(folder_path)}")
        logging.error( "- This player folder will be discarded")
        pause()
        return "ingame_face with face content"

    # Move the categorized files into their subfolders
    for file_name, category in moves:
        src_path = os.path.join(folder_path, file_name)
        dest_folder = os.path.join(folder_path, category)
        os.makedirs(dest_folder, exist_ok=True)
        shutil.move(src_path, os.path.join(dest_folder, file_name))

    return None


def player_folder_preprocess(folder_path, fox_mode, common_name, export_path):
    """Relocate a player folder's textures to its per-player common subfolder."""
    move_textures_to_common(folder_path, "")

    common_files = get_files_list(os.path.join(folder_path, "common"), recursive=True)
    if not common_files:
        return

    export_common_files = get_files_list(os.path.join(export_path, "Common"), recursive=True)
    update_folder_paths(folder_path, common_name, common_files, export_common_files)


def copy_folder_contents(src_folder, dest_folder):
    """Copy every file and subdirectory of a folder into a destination folder.

    A missing source folder just creates the destination (an empty face category
    still gets its face folder emitted)."""
    os.makedirs(dest_folder, exist_ok=True)
    if not os.path.isdir(src_folder):
        return
    for item in os.listdir(src_folder):
        src_path = os.path.join(src_folder, item)
        dst_path = os.path.join(dest_folder, item)
        if os.path.isfile(src_path):
            shutil.copy2(src_path, dst_path)
        elif os.path.isdir(src_path):
            shutil.copytree(src_path, dst_path)


def folder_has_content(folder_path, subfolders):
    """Whether any of the folder's subfolders holds at least one file."""
    for subfolder in subfolders:
        subfolder_path = os.path.join(folder_path, subfolder)
        if os.path.isdir(subfolder_path) and get_files_list(subfolder_path):
            return True
    return False


def kits_process(export_path):
    """Convert a Kits/ folder into the item-folder kit layout.

    Each Kits/<slot>/ folder holds the kit config as a binary config.bin and
    textures with the generic kit prefix; they are mapped back to Kit Configs/
    XXX_DEF_<kit>_realUni.bin and Kit Textures/u0XXX<slot><suffix> names. A slot
    defined both in Kits/ and in the root kit folders discards the export.

    Returns True when the export must be discarded, else False.
    """
    kits_path = os.path.join(export_path, "Kits")
    kit_configs_path = os.path.join(export_path, "Kit Configs")
    kit_textures_path = os.path.join(export_path, "Kit Textures")

    # Slots already defined in the root kit folders
    root_slots = set()
    if os.path.isdir(kit_configs_path):
        for file_name in os.listdir(kit_configs_path):
            match = re.match(r"^[A-Za-z0-9]{3}_DEF_(.+)_realUni\.bin$", file_name, re.IGNORECASE)
            if match and match.group(1) in KIT_SUFFIX_SLOTS:
                root_slots.add(KIT_SUFFIX_SLOTS[match.group(1)])
    if os.path.isdir(kit_textures_path):
        for file_name in os.listdir(kit_textures_path):
            match = re.match(r"^u0[A-Za-z0-9]{3}(p[1-9]|g1)", file_name, re.IGNORECASE)
            if match:
                root_slots.add(match.group(1).lower())

    kit_slots = {}
    invalid_slots = []
    for slot_name in os.listdir(kits_path):
        slot = slot_name.lower()
        if slot not in KIT_SLOT_SUFFIXES:
            invalid_slots.append(slot_name)
            continue
        kit_slots[slot] = os.path.join(kits_path, slot_name)

    for slot_name in invalid_slots:
        logging.error( "-")
        logging.error( "- ERROR - Invalid kit slot folder name")
        logging.error(f"- Folder:   Kits/{slot_name}")
        logging.error( "- Allowed slots: p1-p9, g1")
        logging.error( "- This kit will be discarded")
        pause()

    if root_slots & set(kit_slots):
        for slot in sorted(root_slots & set(kit_slots)):
            logging.error( "-")
            logging.error( "- ERROR - Kit slot defined both in the Kits folder and in the root kit folders")
            logging.error(f"- Slot:    {slot}")
            logging.error( "- This export will be discarded")
        pause()
        shutil.rmtree(export_path, onerror=remove_readonly)
        return True

    for slot, kit_folder_path in kit_slots.items():
        kit_suffix = KIT_SLOT_SUFFIXES[slot]

        for file_name in os.listdir(kit_folder_path):
            src_path = os.path.join(kit_folder_path, file_name)
            lower_name = file_name.lower()

            if lower_name == "config.bin":
                dst_path = os.path.join(kit_configs_path, f"XXX_DEF_{kit_suffix}_realUni.bin")
                os.makedirs(kit_configs_path, exist_ok=True)
                shutil.move(src_path, dst_path)
            elif lower_name.startswith("kit"):
                # kit<suffix>.<ext> -> u0XXX<slot><suffix>.<ext>
                dst_path = os.path.join(kit_textures_path, f"u0XXX{slot}{file_name[3:]}")
                os.makedirs(kit_textures_path, exist_ok=True)
                shutil.move(src_path, dst_path)
            else:
                logging.warning( "-")
                logging.warning( "- Warning - Unexpected file in a kit folder")
                logging.warning(f"- File:    Kits/{slot}/{file_name}")
                logging.warning( "- It will be dropped")

    shutil.rmtree(kits_path, onerror=remove_readonly)
    return False


def players_process(export_path, team_id, team_name, fox_mode):
    """Convert a Players/ export into the item-folder layout.

    Returns True when the export must be discarded, else False.
    """
    players_path = os.path.join(export_path, "Players")
    staging_path = os.path.join(export_path, STAGING_FOLDER_NAME)

    folders, roster_error = roster_build(export_path, slots_max=23)
    if roster_error:
        logging.error( "-")
        logging.error( "- ERROR - Bad players roster")
        logging.error(f"- Team name:      {team_name}")
        logging.error(f"- {roster_error}")
        logging.error( "- This export will be discarded")
        pause()
        shutil.rmtree(export_path, onerror=remove_readonly)
        return True

    # Move the portraits out of the player folders, one per slot (nothing is deleted)
    folder_slots = [(os.path.join(players_path, folder_name), info["slots"])
                    for folder_name, info in folders.items()]
    if portraits_move(export_path, team_id, folder_slots=folder_slots, delete_on_ingame_face=False):
        return True

    # Stage the root shared-folder sources away from the instantiation destinations
    for itemfolder_name in ("Faces", "Boots", "Gloves"):
        itemfolder_path = os.path.join(export_path, itemfolder_name)
        if os.path.isdir(itemfolder_path):
            os.makedirs(staging_path, exist_ok=True)
            shutil.move(itemfolder_path, os.path.join(staging_path, itemfolder_name))

    # Per distinct folder: links → split → preprocess
    folder_set_asides = {}
    discarded_folders = set()
    consumed_staging = set()
    for folder_name, info in folders.items():
        folder_path = os.path.join(players_path, folder_name)
        marker = os.path.exists(os.path.join(folder_path, "ingame_face")) or \
                 os.path.exists(os.path.join(folder_path, "ingame_face.txt"))

        set_asides, link_error = links_resolve(folder_path, staging_path, marker, consumed_staging)
        if link_error:
            discarded_folders.add(folder_name)
            continue

        split_error = player_folder_split(folder_path, fox_mode)
        if split_error:
            discarded_folders.add(folder_name)
            continue

        folder_set_asides[folder_name] = set_asides
        player_folder_preprocess(folder_path, fox_mode, info["name_part"], export_path)

    # Boots/gloves IDs from the team's range; without a usable range the
    # boots/gloves folders of the whole export are discarded, faces still compile
    id_range = None
    if any(info["slots"] and folder_name not in discarded_folders and
           (folder_has_content(os.path.join(players_path, folder_name), ("boots", "gloves")) or
            folder_set_asides.get(folder_name))
           for folder_name, info in folders.items()):
        id_range = teams_list_range_get(team_id)
        if id_range is None:
            logging.error( "-")
            logging.error( "- ERROR - No boots/gloves ID range found for this team")
            logging.error(f"- Team name:      {team_name}")
            logging.error( "- Add the team's MinBootsID/MaxBootsID range to the teams list file")
            logging.error( "- The boots/gloves folders of this export will be discarded")
            pause()
            id_range = None
            boots_gloves_discarded = True
        else:
            boots_gloves_discarded = False
    else:
        boots_gloves_discarded = False

    # Per roster slot: instantiate into Faces/ Boots/ Gloves/ Common/
    for folder_name, info in folders.items():
        if folder_name in discarded_folders:
            continue

        folder_path = os.path.join(players_path, folder_name)
        name_part = info["name_part"]
        marker = os.path.exists(os.path.join(folder_path, "ingame_face")) or \
                 os.path.exists(os.path.join(folder_path, "ingame_face.txt"))

        folder_needs_ids = folder_has_content(folder_path, ("boots", "gloves")) or \
                           bool(folder_set_asides.get(folder_name))

        common_instantiated = False
        for slot in info["slots"]:
            face_id = f"XXX{slot}"

            boots_id = gloves_id = None
            if folder_needs_ids and not boots_gloves_discarded:
                id_number = id_range[0] + int(slot) - 1
                if id_number > id_range[1]:
                    logging.error( "-")
                    logging.error( "- ERROR - Boots/gloves ID outside the team's range")
                    logging.error(f"- Team name:      {team_name}")
                    logging.error(f"- Player folder:  {folder_name}")
                    logging.error(f"- ID:             {id_number} (max {id_range[1]})")
                    logging.error( "- This player's boots/gloves folders will be discarded")
                    pause()
                else:
                    boots_id = f"k{id_number:04d}"
                    gloves_id = f"g{id_number:04d}"

            # Face folder (always emitted, except under ingame_face)
            if not marker:
                copy_folder_contents(os.path.join(folder_path, "face"),
                                     os.path.join(export_path, "Faces", f"{face_id} - {name_part}"))

            # Boots/gloves folders from the split (Fox, or the pre-Fox ingame_face routing)
            if boots_id is not None:
                for subfolder, parent, id_value in (("boots", "Boots", boots_id), ("gloves", "Gloves", gloves_id)):
                    subfolder_path = os.path.join(folder_path, subfolder)
                    if os.path.isdir(subfolder_path) and os.listdir(subfolder_path):
                        copy_folder_contents(subfolder_path,
                                             os.path.join(export_path, parent, f"{id_value} - {name_part}"))

            # Set-aside shared folders become the player's own separate folders
            if boots_id is not None:
                for category, shared_name in folder_set_asides.get(folder_name, []):
                    category_folder = category.capitalize()
                    folder_id = boots_id if category == "boots" else gloves_id
                    copy_folder_contents(os.path.join(staging_path, category_folder, shared_name),
                                         os.path.join(export_path, category_folder, f"{folder_id} - {name_part}"))

            # Per-player common folder, emitted once per distinct folder
            if not common_instantiated:
                copy_folder_contents(os.path.join(folder_path, "common"),
                                     os.path.join(export_path, "Common", name_part))
                common_instantiated = True

    # Delete the Players folder and the staging folder (consumed or unreferenced)
    shutil.rmtree(players_path, onerror=remove_readonly)
    if os.path.isdir(staging_path):
        for category_folder in ("Faces", "Boots", "Gloves"):
            category_path = os.path.join(staging_path, category_folder)
            if os.path.isdir(category_path):
                for shared_name in os.listdir(category_path):
                    if os.path.join(category_folder, shared_name) in consumed_staging:
                        continue
                    logging.warning( "-")
                    logging.warning( "- Warning - Unreferenced shared folder")
                    logging.warning(f"- Folder:   {category_folder}/{shared_name}")
                    logging.warning( "- It will be dropped")
        shutil.rmtree(staging_path, onerror=remove_readonly)

    return False
