import os
import re
import shutil
import logging

from .utils.pausing import pause
from .utils.FILE_INFO import (
    REFS_TEMPLATE_PREFOX_PATH,
    REFS_TEMPLATE_FOX_PATH,
)


def refs_list_process(refs_txt_path):
    """Process the refs file and return a mapping of ref numbers to ref names."""
    ref_mappings = {}
    with open(refs_txt_path, 'r', encoding='utf8') as f:
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


def ref_folder_process(ref_folder, ref_num, ref_name, export_destination_path):
    """Process a referee folder, handling face, boots, gloves and common folders."""
    face_id, boots_id, gloves_id = get_ref_ids(ref_num)

    # Process face folder
    face_src = os.path.join(ref_folder, 'face')
    if os.path.exists(face_src):
        face_dst = os.path.join(export_destination_path, 'Faces', f'{face_id} - {ref_name}')
        os.makedirs(face_dst)

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
        boots_dst = os.path.join(export_destination_path, 'Boots', f'{boots_id} - {ref_name}')
        os.makedirs(boots_dst)

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
        gloves_dst = os.path.join(export_destination_path, 'Gloves', f'{gloves_id} - {ref_name}')
        os.makedirs(gloves_dst)

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
        common_dst = os.path.join(export_destination_path, 'Common')
        os.makedirs(common_dst, exist_ok=True)

        # Copy all files and folders from common folder
        for item in os.listdir(common_src):
            src_path = os.path.join(common_src, item)
            dst_path = os.path.join(common_dst, item)
            if os.path.exists(dst_path):
                continue
            if os.path.isfile(src_path):
                shutil.copy2(src_path, dst_path)
                logging.debug(f"Copied common file: {item}")
            elif os.path.isdir(src_path):
                shutil.copytree(src_path, dst_path)
                logging.debug(f"Copied common folder: {item}")
    else:
        logging.debug(f"No common folder found for referee {ref_name}")


def error_handle(pause_allow):
    logging.error("- Referee compilation will be skipped")
    print("-")
    if pause_allow:
        pause()

def referee_export_process(export_destination_path, pause_allow, fox_mode):
    """Process a referee export folder.

    Args:
        export_destination_path: Path to the extracted referee export
        pause_allow: Whether to pause on error

    Returns:
        bool: False if processing was successful, True otherwise
    """

    # Check for refs template immediately
    refs_template_path = REFS_TEMPLATE_FOX_PATH if fox_mode else REFS_TEMPLATE_PREFOX_PATH
    if not os.path.exists(refs_template_path):
        logging.error( "- ERROR - Refs template folder not found")
        logging.error(f"- Folder path: {refs_template_path}")
        error_handle(pause_allow)
        return True

    # Check for a refs txt
    refs_txt_path = os.path.join(export_destination_path, "Refs.txt")
    if not os.path.exists(refs_txt_path):
        logging.error("- ERROR - Refs.txt not found in referee export")
        error_handle(pause_allow)
        return True

    # Process refs
    ref_mappings = refs_list_process(refs_txt_path)
    if not ref_mappings:
        logging.error("- ERROR - No valid entries found in Refs.txt")
        error_handle(pause_allow)
        return True

    # Process each referee folder according to the list
    error_present = False
    players_folder_path = os.path.join(export_destination_path, "Players")
    for ref_num, ref_name in ref_mappings.items():
        ref_folder = os.path.join(players_folder_path, ref_name)
        if not os.path.exists(ref_folder):
            logging.error(f"- ERROR - Referee folder {ref_name} not found in the Players folder")
            logging.error("- This referee will be skipped")
            print("-")
            error_present = True
            continue

        ref_folder_process(ref_folder, ref_num, ref_name, export_destination_path)

    if error_present and pause_allow:
        pause()

    # Delete the Players folder
    shutil.rmtree(players_folder_path)

    # Delete the refs.txt file
    os.remove(refs_txt_path)

    return False
