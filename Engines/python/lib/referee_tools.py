import os
import re
import shutil
import logging

from .cpk_tools import cpk_file_write
from .fmdl_editing import fmdl_texture_paths_change
from .utils import COLORS
from .utils.ftex import ddsToFtex
from .utils.pausing import pause
from .utils.zlib_plus import unzlib_file
from .utils.name_editing import (
    resolve_link_to_common,
    normalize_kit_dependent_file,
)
from .utils.FILE_INFO import (
    DT00_WRITE_ALLOWED_PATH,
    REFS_TEMPLATE_PREFOX_PATH,
    REFS_TEMPLATE_FOX_PATH,
    UNIFORM_COMMON_PREFOX_PATH,
)
from .utils.file_management import get_files_list


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
    ref_num_padded = ref_num.zfill(2)     # e.g. 01
    face_id = f'referee0{ref_num_padded}' # e.g. referee001
    boots_id = f'k99{ref_num_padded}'     # e.g. k9901
    gloves_id = f'g99{ref_num_padded}'    # e.g. g9901
    return face_id, boots_id, gloves_id


def update_file_paths(file_path, ref_name, ref_common_files, common_files):
    """
    Update paths in XML or MTL file to reference referee-specific Common subfolder.

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

        # New directory for player-specific common textures
        common_player_dir = f"{UNIFORM_COMMON_PREFOX_PATH}XXX/{ref_name}/"
        common_dir = f"{UNIFORM_COMMON_PREFOX_PATH}XXX/"

        # Match path="..." or material="..."
        pattern = re.compile(r'((?:path|material)=")([^"]+)(")')

        def replace_path(match: re.Match):
            prefix = match.group(1)
            path_value = match.group(2)
            suffix = match.group(3)

            # Normalize to forward slashes
            path_value_normalized = path_value.replace('\\', '/')

            file_path_rel = None

            # Check if path is a relative path starting with ./
            relative_match = re.match(r'./(.+)', path_value_normalized)

            # Check if path points to Common folder (with XXX subfolder pattern)
            # Pattern: model/character/uniform/common/XXX/ where XXX is 3 alphanumeric chars
            common_match = re.match(
                rf'{re.escape(UNIFORM_COMMON_PREFOX_PATH)}[a-zA-Z0-9]{{3}}/(.*)', path_value_normalized
            )

            if relative_match:
                file_path_rel = relative_match.group(1)
            elif common_match:
                file_path_rel = common_match.group(1)
            else:
                return match.group(0)

            file_path_rel_denormalized = normalize_kit_dependent_file(file_path_rel, reverse=True)

            # Check if this file is in the referee's common folder
            # or in the export's shared common folder
            new_dir = None
            use_denormalized_name = False
            if file_path_rel in ref_common_files:
                new_dir = common_player_dir
            elif file_path_rel in common_files:
                new_dir = common_dir
            # (with p1 instead of p0)
            elif file_path_rel_denormalized in ref_common_files:
                new_dir = common_player_dir
                use_denormalized_name = True
            elif file_path_rel_denormalized in common_files:
                new_dir = common_dir
                use_denormalized_name = True
            else:
                return match.group(0)

            if use_denormalized_name:
                new_path = f'{new_dir}{file_path_rel_denormalized}'
            else:
                new_path = f'{new_dir}{file_path_rel}'

            logging.debug(f"Updated path: {path_value} -> {new_path}")
            return prefix + new_path + suffix

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
    """
    Update paths in all XML, MTL and FMDL files in a folder.

    Args:
        folder_path: Path to the folder containing XML, MTL or FMDL files
        ref_name: Name of the referee (for subfolder)
        ref_common_files: List of files that are in the referee's Common folder
        common_files: List of files that are in the export's Common folder
    """
    files = get_files_list(folder_path, recursive=True)
    for file_path_rel in files:
        file_path = os.path.join(folder_path, file_path_rel)

        if file_path_rel.endswith('.xml') or file_path_rel.endswith('.mtl'):
            update_file_paths(file_path, ref_name, ref_common_files, common_files)

        if file_path_rel.endswith('.fmdl'):
            fmdl_texture_paths_change(file_path, ref_name, ref_common_files, common_files)


def move_textures_to_common(ref_folder_path, model_folder_name):
    """
    Move texture files from face/boots/gloves folder to common subfolder.

    Args:
        ref_folder_path: Path to the referee's source folder
        model_folder_name: Name of the model folder ('face', 'boots', or 'gloves')

    Returns:
        List of moved texture filenames
    """
    TEXTURE_EXTENSIONS = ['.dds', '.ftex']

    src_folder = os.path.join(ref_folder_path, model_folder_name)
    if not os.path.exists(src_folder):
        return []

    # Find texture files in the source folder (recursive)
    texture_files = []
    src_files = get_files_list(src_folder, recursive=True)
    for item_path_rel in src_files:
        if any(item_path_rel.lower().endswith(ext) for ext in TEXTURE_EXTENSIONS):
            texture_files.append(item_path_rel)

    if not texture_files:
        return []

    # Create common subfolder
    common_subfolder = os.path.join(ref_folder_path, 'common')
    os.makedirs(common_subfolder, exist_ok=True)

    # Move textures
    for texture_path_rel in texture_files:
        src_path = os.path.join(src_folder, os.path.normpath(texture_path_rel))

        # Create destination folder including any subdirectories
        dst_folder_path = os.path.join(common_subfolder, os.path.dirname(texture_path_rel))
        os.makedirs(dst_folder_path, exist_ok=True)

        dst_path = os.path.join(dst_folder_path, os.path.basename(texture_path_rel))
        shutil.move(src_path, dst_path)
        logging.debug(f"Moved texture {texture_path_rel} to common/")

    return texture_files

def move_links_to_subfolder(ref_folder_path, model_folder_name, common_files):
    """
    Move common file links to a subfolder with the referee name if they correspond to a file in
    the referee's common folder.

    Args:
        ref_folder_path: Path to the referee's source folder
        model_folder_name: Name of the model folder ('face', 'boots', or 'gloves')

    Returns:
        List of moved link filenames
    """
    src_folder_path = os.path.join(ref_folder_path, model_folder_name)
    if not os.path.exists(src_folder_path):
        return []

    ref_folder_name = os.path.basename(ref_folder_path)
    src_files = get_files_list(src_folder_path, recursive=True)
    for item_path_rel in src_files:
        item_resolved = resolve_link_to_common(item_path_rel)
        if not item_resolved:
            continue

        item_normalized = normalize_kit_dependent_file(item_resolved, reverse=True)
        if item_normalized is not None and item_normalized not in common_files:
            continue

        link_file_path = os.path.join(src_folder_path, os.path.normpath(item_path_rel))

        # Create destination folder including any subdirectories from item_path_rel
        dst_folder_path = os.path.join(
            ref_folder_path, model_folder_name, ref_folder_name, os.path.dirname(item_path_rel)
        )
        os.makedirs(dst_folder_path, exist_ok=True)

        dst_path = os.path.join(dst_folder_path, os.path.basename(item_path_rel))
        shutil.move(link_file_path, dst_path)
        logging.debug(f"Moved common file link {item_path_rel} to {ref_folder_name}/{os.path.dirname(item_path_rel)}/")

    return common_files


def move_models_to_common(ref_folder_path, model_folder_name):
    """
    Move model and mtl files from face/boots/gloves folder to common subfolder and create links.

    Args:
        ref_folder_path: Path to the referee's source folder
        model_folder_name: Name of the model folder ('face', 'boots', or 'gloves')

    Returns:
        List of moved model filenames
    """
    MODEL_EXTENSIONS = ['.model', '.mtl']

    src_folder = os.path.join(ref_folder_path, model_folder_name)
    if not os.path.exists(src_folder):
        return []

    # Find model files in the source folder (recursive)
    model_files = []
    src_files = get_files_list(src_folder, recursive=True)
    for item_path_rel in src_files:
        if any(item_path_rel.lower().endswith(ext) for ext in MODEL_EXTENSIONS):
            model_files.append(item_path_rel)

    if not model_files:
        return []

    # Create common subfolder
    common_subfolder = os.path.join(ref_folder_path, 'common')
    os.makedirs(common_subfolder, exist_ok=True)

    # Create [folder_name]/[ref_name] subfolder
    ref_folder_name = os.path.basename(ref_folder_path)
    folder_subfolder = os.path.join(src_folder, ref_folder_name)
    os.makedirs(folder_subfolder, exist_ok=True)

    # Move models
    for model_path_rel in model_files:
        src_path = os.path.join(src_folder, os.path.normpath(model_path_rel))

        # Create destination folder including any subdirectories
        dst_folder_path = os.path.join(common_subfolder, os.path.dirname(model_path_rel))
        os.makedirs(dst_folder_path, exist_ok=True)

        dst_path = os.path.join(dst_folder_path, os.path.basename(model_path_rel))
        shutil.move(src_path, dst_path)
        logging.debug(f"Moved model {model_path_rel} to common/")

        # Create empty .common link in the composite subfolder including subdirectories
        link_dir = os.path.join(folder_subfolder, os.path.dirname(model_path_rel))
        os.makedirs(link_dir, exist_ok=True)
        common_link_path = os.path.join(link_dir, f"{os.path.basename(model_path_rel)}.common")
        with open(common_link_path, 'w'):
            pass
        logging.debug(f"Created .common link for model {model_path_rel} in {link_dir}")

    return model_files


def ref_folder_preprocess(ref_folder_path, common_files, fox_mode):
    """Preprocess a referee folder by moving textures to common subfolders and updating paths.

    Args:
        ref_folder_path: Path to the referee's source folder
        common_files: List of files that are in the export's Common folder
        fox_mode: Whether fox mode is enabled
    """
    pes_version = int(os.environ.get('PES_VERSION', '19'))
    ref_name = os.path.basename(ref_folder_path)

    # Auto-move files to common subfolders
    logging.debug(f"Auto-moving files to common subfolders for {ref_name}")
    for model_folder_name in ['face', 'boots', 'gloves']:
        move_textures_to_common(ref_folder_path, model_folder_name)
        if not (fox_mode or pes_version == 16):
            move_links_to_subfolder(ref_folder_path, model_folder_name, common_files)
            move_models_to_common(ref_folder_path, model_folder_name)

    # Get list of files in the referee's common folder
    ref_common_files = get_files_list(os.path.join(ref_folder_path, 'common'), recursive=True)
    if not ref_common_files:
        return

    # Update paths in the folders
    for model_folder_name in ['face', 'boots', 'gloves', 'common']:
        folder_src = os.path.join(ref_folder_path, model_folder_name)
        if os.path.exists(folder_src):
            update_folder_paths(folder_src, ref_name, ref_common_files, common_files)


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

            # Copy all files and subdirectories
            for item in os.listdir(folder_src):
                src_path = os.path.join(folder_src, item)
                dst_path = os.path.join(folder_dst, item)
                if os.path.isfile(src_path):
                    shutil.copy2(src_path, dst_path)
                elif os.path.isdir(src_path):
                    shutil.copytree(src_path, dst_path)
        elif config['required']:
            logging.warning(f"- Warning - No {folder_name} folder found for referee {ref_name}")

    # Process common folder
    src_folder = os.path.join(ref_folder_path, 'common')
    dst_folder = os.path.join(export_destination_path, 'Common', ref_name)
    if not os.path.exists(src_folder):
        return

    os.makedirs(dst_folder, exist_ok=True)

    # Copy all files and subdirectories
    for item in os.listdir(src_folder):
        src_path = os.path.join(src_folder, item)
        dst_path = os.path.join(dst_folder, item)
        if os.path.exists(dst_path):
            continue
        if os.path.isfile(src_path):
            shutil.copy2(src_path, dst_path)
        elif os.path.isdir(src_path):
            shutil.copytree(src_path, dst_path)


def move_marker_to_data(marker_file_path, fox_mode):
    """Move the marker.dds file to the Data folder."""

    if not os.path.exists(marker_file_path):
        return

    if not fox_mode:

        # Move the texture to the refscpk_prefox template folder, overwriting the existing file
        dst_path = os.path.join(
            REFS_TEMPLATE_PREFOX_PATH,
            "common", "character1", "model", "character", "parts", "referee", "incom_bsm.dds"
        )
        shutil.move(marker_file_path, dst_path)

        return

    # Read the necessary parameters
    pes_folder_path = os.environ.get('PES_FOLDER_PATH', 'unknown')
    move_cpks = int(os.environ.get('MOVE_CPKS', '0'))

    if not move_cpks:
        print(f"- {COLORS.DARK_MAGENTA}Notice{COLORS.RESET} - A marker texture is present in the export folder but")
        print( "- Move Cpks mode is disabled.")
        print( "-")
        print( "- This file will be skipped.")
        pause()
        return

    # Check if a dt00_x64.cpk file exists in the Data folder in the PES path
    dt00_cpk_path = os.path.join(pes_folder_path, "Data", "dt00_x64.cpk")
    if not os.path.exists(dt00_cpk_path):
        return

    print( "-")
    print(f"- {COLORS.DARK_MAGENTA}Notice{COLORS.RESET} - A marker texture is present in the export folder but")
    print( "- a Fox version of PES has been set.")
    print( "-")
    print( "- The marker texture will be copied to the dt00_x64 cpk inside the Data folder.")
    print( "- Make sure to share this cpk together with the referees cpk.")
    print( "-")
    print( "- If you don't need to update the marker texture,")
    print( "- you should delete it from the export folder.")

    if not os.path.exists(DT00_WRITE_ALLOWED_PATH):
        print("-")
        print("- Do you want to allow the compiler to overwrite the dt00_x64 system cpk file?")
        print("- (This won't be asked again if confirmed.)")
        print("-")
        response = input("Type Y and press Enter to continue, or just press Enter to skip... ")

        if response.lower() != 'y':
            return

        with open(DT00_WRITE_ALLOWED_PATH, 'w') as f:
            f.write("This file tells the program that overwriting the dt00_x64 cpk has been allowed.")
    else:
        pause()

    # Convert the texture to ftex
    marker_file_ftex_path = marker_file_path.replace('.dds', '.ftex')
    ddsToFtex(marker_file_path, marker_file_ftex_path, None)

    # Write the ftex to the dt00 cpk
    dst_path = "Asset/model/character/common/sourceimages/#windx11/cup_logo.ftex"
    cpk_file_write(dt00_cpk_path, marker_file_ftex_path, dst_path)

    # Delete the marker file
    os.remove(marker_file_path)


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
    refs_txt_path = os.path.join(export_destination_path, "refs.txt")
    if not os.path.exists(refs_txt_path):
        logging.error("- ERROR - refs.txt not found in referee export")
        error_handle()
        return True

    # Process refs
    print("- Processing refs...")
    ref_mappings = refs_list_process(refs_txt_path)
    if not ref_mappings:
        logging.error("- ERROR - No valid entries found in refs.txt")
        error_handle()
        return True

    # Delete the refs.txt file
    os.remove(refs_txt_path)

    export_players_path = os.path.join(export_destination_path, "Players")

    # First pass: Move textures to common subfolders and update paths in source folders
    common_files = get_files_list(os.path.join(export_destination_path, 'Common'), recursive=True)
    for ref_name in set(ref_mappings.values()):
        ref_folder_path = os.path.join(export_players_path, ref_name)
        if not os.path.exists(ref_folder_path):
            continue

        ref_folder_preprocess(ref_folder_path, common_files, fox_mode)
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

    # Check for a marker.dds file in the export folder
    marker_file_path = os.path.join(export_destination_path,"ref_marker.dds")
    if os.path.exists(marker_file_path):
        # Move the marker file
        move_marker_to_data(marker_file_path, fox_mode)

    return False
