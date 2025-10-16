import os
import re
import shutil
import logging

from .utils.pausing import pause
from .utils.zlib_plus import unzlib_file
from .utils.FILE_INFO import (
    REFS_TEMPLATE_PREFOX_PATH,
    REFS_TEMPLATE_FOX_PATH,
)


UNIFORM_COMMON_PATH = 'model/character/uniform/common/'


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


def get_files_list(folder_path, recursive=False):
    """Get a list of files in the folder indicated.

    Args:
        folder_path: Path to the folder
        recursive: If True, include files in subdirectories with relative paths

    Returns:
        List of filenames (or relative paths if recursive=True)
    """
    if not os.path.exists(folder_path):
        return []

    files_list = []
    if recursive:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                # Get relative path from folder_path
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, folder_path)
                # Use forward slashes for consistency
                rel_path = rel_path.replace('\\', '/')
                files_list.append(rel_path)
    else:
        for item in os.listdir(folder_path):
            src_path = os.path.join(folder_path, item)
            if os.path.isfile(src_path):
                files_list.append(item)

    return files_list


def update_file_paths(file_path, ref_name, ref_common_files, common_files):
    """Update paths in XML or MTL file to reference referee-specific Common subfolder.

    Args:
        file_path: Path to the file to update (XML or MTL)
        ref_name: Name of the referee (for subfolder)
        ref_common_files: List of files that are in the referee's Common folder
        common_files: List of files that are in the export's Common folder (for checking shared files)
    """
    try:
        # Unzlib file if needed
        unzlib_file(file_path)

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

            # Normalize to forward slashes
            path_value_normalized = path_value.replace('\\', '/')

            # Check if path points to Common folder (with XXX subfolder pattern)
            # Pattern: model/character/uniform/common/XXX/ where XXX is 3 alphanumeric chars
            common_pattern = re.match(
                rf'{re.escape(UNIFORM_COMMON_PATH)}[a-zA-Z0-9]{{3}}/(.*)', path_value_normalized
            )
            if common_pattern:
                # Extract the part after common/XXX/
                common_part = common_pattern.group(1)

                # Check if this file is in the referee's common folder
                if common_part in ref_common_files and common_part not in common_files:
                    # Update to use referee-specific subfolder
                    new_path = f"{UNIFORM_COMMON_PATH}XXX/{ref_name}/{common_part}"
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


def update_mtl_for_moved_textures(mtl_path, texture_files, subfolder_name):
    """Update MTL file paths after textures have been moved to common subfolder.

    Args:
        mtl_path: Path to the MTL file
        texture_files: List of texture filenames that were moved
        subfolder_name: Name of the subfolder in common (e.g., 'face')
    """
    try:
        # Unzlib file if needed
        unzlib_file(mtl_path)

        with open(mtl_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        modified = False
        new_lines = []

        for line in lines:
            new_line = line
            # Check for texture references
            for texture in texture_files:
                if not ('path=' in line and f'./{texture}' in line):
                    continue
                # Replace texture path to point to common/XXX/[subfolder]/
                new_path = f"{UNIFORM_COMMON_PATH}XXX/{subfolder_name}/{texture}"
                new_line = re.sub(
                    rf'(path=")\./{re.escape(texture)}(")',
                    rf'\1{new_path}\2',
                    new_line
                )
                if new_line != line:
                    modified = True
                    logging.debug(f"Updated MTL texture reference: ./{texture} -> {new_path}")
                    break
            new_lines.append(new_line)

        if modified:
            with open(mtl_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            logging.debug(f"Updated MTL paths in: {mtl_path}")

    except Exception as e:
        logging.error(f"- ERROR - Failed to update MTL paths in {mtl_path}: {e}")
        pause()

def move_textures_to_common(ref_folder_path, folder_name):
    """Move texture files from face/boots/gloves folder to common subfolder and update MTL paths.

    Args:
        ref_folder_path: Path to the referee's source folder
        folder_name: Name of the folder ('face', 'boots', or 'gloves')

    Returns:
        List of moved texture filenames
    """
    TEXTURE_EXTENSIONS = ['.dds', '.ftex']

    src_folder = os.path.join(ref_folder_path, folder_name)
    if not os.path.exists(src_folder):
        return []

    # Find texture files in the source folder
    texture_files = []
    for item in os.listdir(src_folder):
        if any(item.lower().endswith(ext) for ext in TEXTURE_EXTENSIONS):
            texture_files.append(item)

    if not texture_files:
        return []

    # Create common/[folder_name] subfolder
    common_subfolder = os.path.join(ref_folder_path, 'common', folder_name)
    os.makedirs(common_subfolder, exist_ok=True)

    # Move textures
    for texture in texture_files:
        src_path = os.path.join(src_folder, texture)
        dst_path = os.path.join(common_subfolder, texture)
        shutil.move(src_path, dst_path)
        logging.debug(f"Moved texture {texture} to common/{folder_name}/")

    # Update MTL file paths in the source folder
    for item in os.listdir(src_folder):
        if item.endswith('.mtl'):
            mtl_path = os.path.join(src_folder, item)
            update_mtl_for_moved_textures(mtl_path, texture_files, folder_name)

    return texture_files


def ref_folder_preprocess(ref_folder_path, ref_name, common_files, fox_mode):
    """Preprocess a referee folder by moving textures to common subfolders and updating paths.

    Args:
        ref_folder_path: Path to the referee's source folder
        ref_name: Name of the referee (for subfolder)
        common_files: List of files that are in the export's Common folder
        fox_mode: Whether fox mode is enabled
    """
    if not fox_mode:
        # Auto-move textures to common subfolders
        logging.debug(f"Auto-moving textures to common subfolders for {ref_name}")
        for folder_name in ['face', 'boots', 'gloves']:
            move_textures_to_common(ref_folder_path, folder_name)

    # Get list of files in the referee's common folder
    ref_common_files = get_files_list(os.path.join(ref_folder_path, 'common'), recursive=True)
    if not ref_common_files:
        return

    # Get list of files in the referee's common_shared folder
    ref_common_shared_files = get_files_list(os.path.join(ref_folder_path, 'common_shared'), recursive=True)

    # Combine the list of files from common_shared and the list of files in the export's Common folder
    common_files_withshared = common_files + ref_common_shared_files

    # Update paths in the model folders
    for folder_name in ['face', 'boots', 'gloves']:
        folder_src = os.path.join(ref_folder_path, folder_name)
        if os.path.exists(folder_src):
            update_folder_paths(folder_src, ref_name, ref_common_files, common_files_withshared)


def ref_folder_process(ref_folder_path, ref_num, ref_name, export_destination_path):
    """Process a referee folder, handling face, boots, gloves and common folders."""
    face_id, boots_id, gloves_id = get_ref_ids(ref_num)

    # Configuration for each model folder type
    model_folder_configs = {
        'face': {
            'id': face_id,
            'destination_parent': 'Faces',
            'required': True
        },
        'boots': {
            'id': boots_id,
            'destination_parent': 'Boots',
            'required': False
        },
        'gloves': {
            'id': gloves_id,
            'destination_parent': 'Gloves',
            'required': False
        }
    }

    # Process model folders
    for folder_name, config in model_folder_configs.items():
        folder_src = os.path.join(ref_folder_path, folder_name)
        if os.path.exists(folder_src):
            folder_dst = os.path.join(
                export_destination_path,
                config['destination_parent'],
                f"{config['id']} - {ref_name}"
            )
            os.makedirs(folder_dst)

            # Copy all files from folder
            for item in os.listdir(folder_src):
                src_path = os.path.join(folder_src, item)
                if os.path.isfile(src_path):
                    shutil.copy2(src_path, folder_dst)
        elif config['required']:
            logging.warning(f"- Warning - No {folder_name} folder found for referee {ref_name}")

    # Configuration for each common folder type
    common_folder_configs = {
        # Files from "common" are copied to a referee-specific subfolder in Common
        'common': os.path.join(export_destination_path, 'Common', ref_name),
        # Files from "common_shared" are copied directly to the Common folder
        'common_shared': os.path.join(export_destination_path, 'Common')
    }

    # Process common folders
    for folder_name, destination in common_folder_configs.items():
        src_folder = os.path.join(ref_folder_path, folder_name)
        if not os.path.exists(src_folder):
            continue

        os.makedirs(destination, exist_ok=True)

        # Copy all files and subdirectories
        for item in os.listdir(src_folder):
            src_path = os.path.join(src_folder, item)
            dst_path = os.path.join(destination, item)
            if os.path.exists(dst_path):
                continue
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

    # First pass: Move textures to common subfolders and update paths in source folders
    common_files = get_files_list(os.path.join(export_destination_path, 'Common'), recursive=True)
    for ref_name in set(ref_mappings.values()):
        ref_folder_path = os.path.join(export_players_path, ref_name)
        if not os.path.exists(ref_folder_path):
            continue

        ref_folder_preprocess(ref_folder_path, ref_name, common_files, fox_mode)
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
