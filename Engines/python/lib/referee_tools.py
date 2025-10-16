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


def get_common_files_list(folder_path):
    """Get a list of files in the Common folder of the folder indicated."""
    common_src = os.path.join(folder_path, 'common')
    if not os.path.exists(common_src):
        return []

    common_files = []
    for item in os.listdir(common_src):
        src_path = os.path.join(common_src, item)
        if os.path.isfile(src_path):
            common_files.append(item)
    return common_files


def update_file_paths(file_path, ref_name, ref_common_files, common_files):
    """Update paths in XML or MTL file to reference referee-specific Common subfolder.

    Args:
        file_path: Path to the file to update (XML or MTL)
        ref_name: Name of the referee (for subfolder)
        ref_common_files: List of files that are in the referee's Common folder
        common_files: List of files that are in the export's Common folder (for checking shared files)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        modified = False
        lines = content.split('\n')
        new_lines = []

        # Match path="..." or material="..."
        pattern = re.compile(r'((?:path|material)=")([^"]+)(")')

        def replace_path(match: re.Match):
            prefix = match.group(1)
            path_value = match.group(2)
            suffix = match.group(3)

            # Extract filename from path
            filename = os.path.basename(path_value)

            # Check if this file is in the referee's common folder
            # and it's not in the export's common folder
            if filename in ref_common_files and filename not in common_files:
                # Update to use referee-specific subfolder
                new_path = f"model/character/uniform/common/XXX/{ref_name}/{filename}"
                logging.debug(f"Updated path: {path_value} -> {new_path}")
                return prefix + new_path + suffix

            return match.group(0)

        for line in lines:
            # Check for lines containing path= or material=
            if not ('path=' in line or 'material=' in line):
                new_lines.append(line)
                continue

            new_line = re.sub(pattern, replace_path, line)
            new_lines.append(new_line)

            if new_line != line:
                modified = True

        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(new_lines))
            logging.debug(f"Updated paths in: {file_path}")

    except Exception as e:
        logging.error(f"- ERROR - Failed to update paths in {file_path}: {e}")
        pause()


def update_folder_paths(folder_path, ref_name, ref_common_files, common_files):
    """Update paths in all XML and MTL files in a folder.

    Args:
        folder_path: Path to the folder containing XML and MTL files
        ref_name: Name of the referee (for subfolder)
        ref_common_files: List of files that are in the referee's Common folder
        common_files: List of files that are in the export's Common folder
    """
    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        if os.path.isfile(item_path):
            if item.endswith('.xml') or item.endswith('.mtl'):
                update_file_paths(item_path, ref_name, ref_common_files, common_files)


def update_referee_source_paths(ref_folder_path, ref_name, common_files):
    """Update paths in the source referee folder's face, boots, and gloves folders.

    Args:
        ref_folder_path: Path to the referee's source folder
        ref_name: Name of the referee (for subfolder)
        common_files: List of files that are in the export's Common folder
    """
    # Get list of files in the Common folder of the referee's source folder
    ref_common_files = get_common_files_list(ref_folder_path)
    if not ref_common_files:
        return

    # Update paths in face folder
    face_src = os.path.join(ref_folder_path, 'face')
    if os.path.exists(face_src):
        update_folder_paths(face_src, ref_name, ref_common_files, common_files)

    # Update paths in boots folder
    boots_src = os.path.join(ref_folder_path, 'boots')
    if os.path.exists(boots_src):
        update_folder_paths(boots_src, ref_name, ref_common_files, common_files)

    # Update paths in gloves folder
    gloves_src = os.path.join(ref_folder_path, 'gloves')
    if os.path.exists(gloves_src):
        update_folder_paths(gloves_src, ref_name, ref_common_files, common_files)


def ref_folder_process(ref_folder_path, ref_num, ref_name, export_destination_path):
    """Process a referee folder, handling face, boots, gloves and common folders."""
    face_id, boots_id, gloves_id = get_ref_ids(ref_num)

    # Process face folder
    face_src = os.path.join(ref_folder_path, 'face')
    if os.path.exists(face_src):
        face_dst = os.path.join(export_destination_path, 'Faces', f'{face_id} - {ref_name}')
        os.makedirs(face_dst)

        # Copy all files from face folder
        for item in os.listdir(face_src):
            src_path = os.path.join(face_src, item)
            if os.path.isfile(src_path):
                shutil.copy2(src_path, face_dst)
    else:
        logging.warning(f"No face folder found for referee {ref_name}")

    # Process boots folder if it exists
    boots_src = os.path.join(ref_folder_path, 'boots')
    if os.path.exists(boots_src):
        boots_dst = os.path.join(export_destination_path, 'Boots', f'{boots_id} - {ref_name}')
        os.makedirs(boots_dst)

        # Copy all files from boots folder
        for item in os.listdir(boots_src):
            src_path = os.path.join(boots_src, item)
            if os.path.isfile(src_path):
                shutil.copy2(src_path, boots_dst)

    # Process gloves folder if it exists
    gloves_src = os.path.join(ref_folder_path, 'gloves')
    if os.path.exists(gloves_src):
        gloves_dst = os.path.join(export_destination_path, 'Gloves', f'{gloves_id} - {ref_name}')
        os.makedirs(gloves_dst)

        # Copy all files from gloves folder
        for item in os.listdir(gloves_src):
            src_path = os.path.join(gloves_src, item)
            if os.path.isfile(src_path):
                shutil.copy2(src_path, gloves_dst)

    # Process common folder if it exists - copy to referee-specific subfolder
    common_src = os.path.join(ref_folder_path, 'common')
    if os.path.exists(common_src):
        # Create referee-specific subfolder in Common
        common_dst = os.path.join(export_destination_path, 'Common', ref_name)
        os.makedirs(common_dst, exist_ok=True)

        # Copy all files and subdirectories from common folder to referee-specific subfolder
        for item in os.listdir(common_src):
            src_path = os.path.join(common_src, item)
            dst_path = os.path.join(common_dst, item)
            if os.path.isfile(src_path):
                shutil.copy2(src_path, dst_path)
            elif os.path.isdir(src_path):
                shutil.copytree(src_path, dst_path)


def error_handle():
    logging.error("- Referee compilation will be skipped")
    pause()

def referee_export_process(export_destination_path, fox_mode):
    """Process a referee export folder.

    Args:
        export_destination_path: Path to the extracted referee export

    Returns:
        bool: False if processing was successful, True otherwise
    """

    # Check for refs template immediately
    refs_template_path = REFS_TEMPLATE_FOX_PATH if fox_mode else REFS_TEMPLATE_PREFOX_PATH
    if not os.path.exists(refs_template_path):
        logging.error( "- ERROR - Refs template folder not found")
        logging.error(f"- Folder path: {refs_template_path}")
        error_handle()
        return True

    # Check for a refs txt
    refs_txt_path = os.path.join(export_destination_path, "Refs.txt")
    if not os.path.exists(refs_txt_path):
        logging.error("- ERROR - Refs.txt not found in referee export")
        error_handle()
        return True

    # Process refs
    print("- Processing refs...")
    ref_mappings = refs_list_process(refs_txt_path)
    if not ref_mappings:
        logging.error("- ERROR - No valid entries found in Refs.txt")
        error_handle()
        return True

    export_players_path = os.path.join(export_destination_path, "Players")

    # First pass: Update paths in source folders (once per unique referee)
    common_files = get_common_files_list(export_destination_path)
    for ref_name in set(ref_mappings.values()):
        ref_folder_path = os.path.join(export_players_path, ref_name)
        if os.path.exists(ref_folder_path):
            update_referee_source_paths(ref_folder_path, ref_name, common_files)
            logging.debug(f"Preprocessed referee folder: {ref_name}")

    # Second pass: Process each referee folder according to the list
    error_present = False
    for ref_num, ref_name in ref_mappings.items():
        ref_folder_path = os.path.join(export_players_path, ref_name)
        if not os.path.exists(ref_folder_path):
            logging.error(f"- ERROR - Referee folder {ref_name} not found in the Players folder")
            logging.error("- This referee will be skipped")
            error_present = True
            continue

        ref_folder_process(ref_folder_path, ref_num, ref_name, export_destination_path)

    if error_present:
        pause()

    # Delete the Players folder
    shutil.rmtree(export_players_path)

    # Delete the refs.txt file
    os.remove(refs_txt_path)

    return False
