import os
import re
import shutil
import logging

from .utils.pausing import pause
from .utils.FILE_INFO import (
    PATCHES_CONTENTS_REFS_PATH,
)


def refs_list_process(refs_list_path):
    """Process the refs list file and return a mapping of ref numbers to ref names."""
    ref_mappings = {}
    with open(refs_list_path, 'r', encoding='utf8') as f:
        for line in f:
            # Skip empty lines
            if not line.strip():
                continue
            # Extract ref number and name
            match = re.match(r'(\d+)\s+(.+)', line.strip())
            if match:
                ref_num, ref_name = match.groups()
                ref_mappings[ref_num] = ref_name
    return ref_mappings


def get_ref_ids(ref_num):
    """Get the IDs for face, boots and gloves for a given ref number."""
    face_id = f'referee{ref_num.zfill(3)}'  # e.g. referee001
    boots_id = f'k99{ref_num.zfill(2)}'  # e.g. k9901
    gloves_id = f'g99{ref_num.zfill(2)}'  # e.g. g9901
    return face_id, boots_id, gloves_id


def ref_folder_process(ref_folder, ref_num, ref_name, extracted_path, fox_mode):
    """Process a referee folder, handling face, boots, gloves and common folders."""
    face_id, boots_id, gloves_id = get_ref_ids(ref_num)

    # Process face folder
    face_src = os.path.join(ref_folder, 'face')
    if os.path.exists(face_src):
        face_dst = os.path.join(extracted_path, 'Faces', f'{face_id} - {ref_name}')
        os.makedirs(face_dst, exist_ok=True)

        # Copy all files from face folder
        for item in os.listdir(face_src):
            src_path = os.path.join(face_src, item)
            if os.path.isfile(src_path):
                shutil.copy2(src_path, face_dst)
                logging.debug(f"Copied face file: {item}")
    else:
        logging.warning(f"No face folder found for referee {ref_name}")

    # Process boots folder if it exists
    boots_src = os.path.join(ref_folder, 'boots')
    if os.path.exists(boots_src):
        boots_dst = os.path.join(extracted_path, 'Boots', f'{boots_id} - {ref_name}')
        os.makedirs(boots_dst, exist_ok=True)

        # Copy all files from boots folder
        for item in os.listdir(boots_src):
            src_path = os.path.join(boots_src, item)
            if os.path.isfile(src_path):
                shutil.copy2(src_path, boots_dst)
                logging.debug(f"Copied boots file: {item}")
    else:
        logging.debug(f"No boots folder found for referee {ref_name}")

    # Process gloves folder if it exists
    gloves_src = os.path.join(ref_folder, 'gloves')
    if os.path.exists(gloves_src):
        gloves_dst = os.path.join(extracted_path, 'Gloves', f'{gloves_id} - {ref_name}')
        os.makedirs(gloves_dst, exist_ok=True)

        # Copy all files from gloves folder
        for item in os.listdir(gloves_src):
            src_path = os.path.join(gloves_src, item)
            if os.path.isfile(src_path):
                shutil.copy2(src_path, gloves_dst)
                logging.debug(f"Copied gloves file: {item}")
    else:
        logging.debug(f"No gloves folder found for referee {ref_name}")

    # Process common folder if it exists
    common_src = os.path.join(ref_folder, 'common')
    if os.path.exists(common_src):
        common_dst = os.path.join(extracted_path, 'Common')
        os.makedirs(common_dst, exist_ok=True)

        # Copy all files from common folder
        for item in os.listdir(common_src):
            src_path = os.path.join(common_src, item)
            if os.path.isfile(src_path):
                shutil.copy2(src_path, common_dst)
                logging.debug(f"Copied common file: {item}")
    else:
        logging.debug(f"No common folder found for referee {ref_name}")


def referee_export_process(export_destination_path: str, fox_mode: bool, pause_on_error: bool) -> bool:
    """Process a referee export folder.

    Args:
        export_destination_path: Path to the extracted referee export
        fox_mode: Whether to process in fox engine mode
        pause_on_error: Whether to pause on error

    Returns:
        bool: True if processing was successful, False otherwise
    """
    print("- Processing referee export")

    # Check for patches_contents_refs immediately
    if not os.path.exists(PATCHES_CONTENTS_REFS_PATH):
        logging.error("- ERROR - \"patches_contents_refs\" folder not found in compiler root folder")
        logging.error("- Referee compilation will be skipped")
        print("-")
        if pause_on_error:
            pause()
        return False

    # Check for refs list
    refs_list_path = os.path.join(export_destination_path, "Refs list.txt")
    if not os.path.exists(refs_list_path):
        logging.error("- ERROR - Refs list.txt not found in referee export")
        logging.error("- Referee compilation will be skipped")
        print("-")
        if pause_on_error:
            pause()
        return False

    # Process refs list
    ref_mappings = refs_list_process(refs_list_path)
    if not ref_mappings:
        logging.error("- ERROR - No valid entries found in Refs list.txt")
        logging.error("- Referee compilation will be skipped")
        print("-")
        if pause_on_error:
            pause()
        return False

    # Move the referee folders to a Referees folder
    referees_path = os.path.join(export_destination_path, "Referees")
    os.makedirs(referees_path, exist_ok=True)
    for ref_name in os.listdir(export_destination_path):
        ref_folder = os.path.join(export_destination_path, ref_name)
        if os.path.isdir(ref_folder):
            shutil.move(ref_folder, referees_path)

    # Process each referee folder according to the list
    for ref_num, ref_name in ref_mappings.items():
        ref_folder = os.path.join(referees_path, ref_name)
        if not os.path.exists(ref_folder):
            logging.error(f"- ERROR - Referee folder {ref_name} not found")
            logging.error("- This referee will be skipped")
            print("-")
            if pause_on_error:
                pause()
            continue

        print(f"- referee{ref_num.zfill(3)}: {ref_name}")
        ref_folder_process(ref_folder, ref_num, ref_name, export_destination_path, fox_mode)

    # Delete the referees folder
    shutil.rmtree(referees_path)

    return True
