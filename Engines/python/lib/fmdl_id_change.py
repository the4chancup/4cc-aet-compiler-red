import os
import re
import sys
import struct
import fnmatch
import logging

from .utils.name_editing import path_id_change
from .utils.FmdlFile import FmdlContainer


def fmdl_id_change(file_path: str, model_id: str, team_id: str = ""):

    # Make sure the file exists
    if not os.path.exists(file_path):
        return

    # Check the team ID if provided
    if team_id and not re.match(r'[0-9]{3}', team_id):
        logging.debug(f"Incorrect Team ID {team_id}, please make sure the ID is exactly 3 digits long")
        return

    file_name = os.path.basename(file_path)
    file_folder = os.path.dirname(file_path)

    file_binary = open(file_path, 'rb')

    logging.debug("Working on file " + file_path)

    # Grab actually important values from header
    file_binary.seek(32)
    section0_item_count = struct.unpack("<I", file_binary.read(4))[0]
    section1_item_count = struct.unpack("<I", file_binary.read(4))[0]
    header_length = struct.unpack("<I", file_binary.read(4))[0]

    file_binary.seek(4, 1)
    section1_offset = struct.unpack("<I", file_binary.read(4))[0]

    # Then start working on the rest of the file
    file_binary.seek(64, 0)

    # Go through blockmap 0
    texture_offset = 0
    texture_count = 0
    string_offset = 0
    string_count = 0
    block_count = 0

    for i in range(section0_item_count):
        # Read block data in order to determine what type of block it is
        block_type = file_binary.read(2)
        block_items_count = file_binary.read(2)
        block_items_offset = file_binary.read(4)

        if(struct.unpack("<H", block_type)[0] == 6): # Texture block
            texture_offset = struct.unpack("<I", block_items_offset)[0]
            texture_count = struct.unpack("<H", block_items_count)[0]
            block_count = block_count + 1
        elif(struct.unpack("<H", block_type)[0] == 12): # String block
            string_offset = struct.unpack("<I", block_items_offset)[0]
            string_count = struct.unpack("<H", block_items_count)[0]
            block_count = block_count + 1

    # Check if all required blocks were found.
    ##NOTE: Change this when a new block is added
    if not (block_count == 2):
        logging.debug("1") # Error code 1 - Didn't find required blocks in file (texture definition, string block)
        file_binary.close()
        return

    # Go through blockmap 1
    string_end = 0
    _string_length = 0
    for i in range(section1_item_count):
        block_type = file_binary.read(4)
        block_items_offset = file_binary.read(4)
        block_end = file_binary.read(4)

        if(struct.unpack("<I", block_type)[0] == 3):
            string_end = struct.unpack("<I", block_items_offset)[0]
            _string_length = struct.unpack("<I", block_end)[0] # Not used

    # We have all the required offsets now, start building output
    file_binary.seek(header_length + string_offset)

    # Store string lengths
    string_length_list = []
    for i in range(string_count):
        file_binary.seek(2, 1)
        string_length_list.append(struct.unpack('<H', file_binary.read(2))[0])
        file_binary.seek(4, 1)

    # Then process MTL
    string_list = []
    file_binary.seek(section1_offset + string_end)
    for i in range(string_count):
        string = file_binary.read(string_length_list[i]+1).rstrip(b'\0').decode('utf-8')
        if string is not None:
            string_list.append(string)

    # Scan textures
    file_binary.seek(header_length + texture_offset)
    texture_index_list = []
    texture_path_list = []
    for i in range(texture_count*2): # 2 strings per texture: directory and filename
        texture_index = struct.unpack("<H", file_binary.read(2))[0]
        if texture_index not in texture_index_list:
            texture_index_list.append(texture_index)
            texture_path_list.append(string_list[texture_index])

    # Close file for now, we're done reading
    file_binary.close()

    # Prepare a list of dictionaries of path info
    path_info_list = [
        {"type": "face"   , "id_pattern": "[0-9]{5}"       , "section_count": 10, "id_section": 7},
        {"type": "referee", "id_pattern": "referee[0-9]{3}", "section_count": 10, "id_section": 7},
        {"type": "boots"  , "id_pattern": "k[0-9]{4}"      , "section_count": 8 , "id_section": 6},
        {"type": "glove"  , "id_pattern": "g[0-9]{4}"      , "section_count": 8 , "id_section": 6},
        {"type": "ball"   , "id_pattern": "ball[0-9]{3}"   , "section_count": 7 , "id_section": 5},
    ]

    # Check the type of ID that was provided
    for path_info in path_info_list:
        if(re.fullmatch(path_info["id_pattern"], model_id)):
            model_path_info = path_info
            break
    else:
        print(f"- Unrecognized ID \"{model_id}\"")
        return

    texture_path_found = False

    # Process the paths
    for texture_index in texture_index_list:
        # Split path to individual pieces
        texture_path_split = string_list[texture_index].split("/")
        texture_path_section_count = len(texture_path_split)

        # Model ID
        if(
            texture_path_section_count == model_path_info["section_count"] and
            re.fullmatch(model_path_info["id_pattern"], texture_path_split[model_path_info["id_section"]])
        ):
            # Change the ID
            texture_path_split[model_path_info["id_section"]] = model_id
            # Overwrite old path in the string list
            string_list[texture_index] = "/".join(texture_path_split)

            texture_path_found = True

    if team_id:

        # Replace the team ID on common paths and kit-dependent texture names
        for i, string in enumerate(string_list):
            string_new = path_id_change(string, team_id)
            if string_new != string:
                string_list[i] = string_new

                texture_path_found = True

    if not texture_path_found:
        logging.warning( "-")
        logging.warning( "- Warning: No texture paths with IDs found")
        logging.warning(f"- Folder:         {file_folder}")
        logging.warning(f"- File:           {file_name}")
        logging.warning(f"- Model ID:       {model_id}")
        if team_id:
            logging.warning(f"- Team ID:        {team_id}")
        for texture_path in texture_path_list:
            logging.warning(f"- Texture path:   {texture_path}")
        logging.warning( "- This model might work fine, double-check its texture paths if it doesn't")

    # Re-open file for writing
    file_binary = open(file_path, "r+b")

    # Seek to string block
    file_binary.seek(section1_offset + string_end)

    # Re-write FMDL strings
    for string in string_list:
        file_binary.write(bytes(string, 'utf-8'))
        file_binary.write(struct.pack("B", 0))

    # Done, close file for good and exit
    file_binary.close()

    return


def fmdl_texture_paths_change(file_path: str, common_base: str, player_name: str, model_folder_name: str):
    """
    Change all texture directory paths in an FMDL file to point to the
    player's common subfolders.

    Unlike fmdl_id_change which only modifies IDs within existing paths,
    this function can change the entire texture directory path, handling
    variable-length string changes by rewriting the file structure.

    Paths that match a model-type structure (face, boots, gloves, etc.)
    get model_folder_name appended, while paths that already point to
    common (shorter structure) only get player_name inserted.

    Args:
        file_path: Path to the .fmdl file
        common_base: Common folder base path
            (e.g. '/Assets/pes16/model/character/common/')
        player_name: Name of the player (e.g. 'marisa')
        model_folder_name: Name of the model folder (e.g. 'boots')
    """
    if not os.path.exists(file_path):
        return

    logging.debug("Changing texture paths in " + file_path)

    fmdl = FmdlContainer()
    fmdl.readFile(file_path)

    # Need block 12 (string descriptors) and segment1 block 3 (string data)
    if 12 not in fmdl.segment0Blocks or 3 not in fmdl.segment1Blocks:
        logging.debug("No string data found in file")
        return

    # Need block 6 (texture definitions)
    if 6 not in fmdl.segment0Blocks:
        logging.debug("No texture data found in file")
        return

    # Parse all strings
    string_block = fmdl.segment1Blocks[3]
    strings = []
    for definition in fmdl.segment0Blocks[12]:
        (block_id, length, offset) = struct.unpack('< H H I', definition)
        bytestring = string_block[offset : offset + length]
        strings.append(bytestring.decode('utf-8'))

    # Find texture directory string indices from block 6
    dir_string_indices = set()
    for definition in fmdl.segment0Blocks[6]:
        (filename_id, directory_id) = struct.unpack('< H H', definition)
        dir_string_indices.add(directory_id)

    if not dir_string_indices:
        logging.debug("No texture entries found in file")
        return

    # Model folder names that indicate a model-type path (face, boots, glove)
    model_folder_names = {'face', 'boots', 'glove'}
    # Team common path: has common/ followed by a 3-digit team ID
    team_common_pattern = re.compile(r'/common/[0-9]{3}/')

    # Replace directory strings with the appropriate new texture directory
    modified = False
    for idx in dir_string_indices:
        if idx >= len(strings):
            continue

        old_path = strings[idx]
        old_path_sections = [s for s in old_path.split("/") if s]

        # Check if the path contains a model folder name (face, boots, glove)
        is_model_type = any(section in model_folder_names for section in old_path_sections)

        if is_model_type:
            # Model-type paths -> replace with per-model per-player path
            new_path = f"{common_base}000/{player_name}/{model_folder_name}/sourceimages/"
        elif team_common_pattern.search(old_path):
            # Team common paths -> replace with per-player path
            new_path = f"{common_base}000/{player_name}/sourceimages/"
        else:
            # Game common paths -> leave unchanged
            continue

        if old_path != new_path:
            logging.debug(f"  {old_path} -> {new_path}")
            strings[idx] = new_path
            modified = True

    if not modified:
        return

    # Rebuild string data (segment1 block 3) and descriptors (segment0 block 12)
    new_string_data = bytearray()
    new_descriptors = []
    for string in strings:
        encoded = string.encode('utf-8')
        offset = len(new_string_data)
        new_string_data += encoded + b'\0'
        new_descriptors.append(bytearray(struct.pack('< H H I', 3, len(encoded), offset)))

    # Preserve any extension header data that may follow the last string
    if fmdl.segment0Blocks[12]:
        last_desc = fmdl.segment0Blocks[12][-1]
        (_, last_len, last_offset) = struct.unpack('< H H I', last_desc)
        original_strings_end = last_offset + last_len + 1  # +1 for null terminator
        if original_strings_end < len(string_block):
            new_string_data += string_block[original_strings_end:]

    fmdl.segment1Blocks[3] = new_string_data
    fmdl.segment0Blocks[12] = new_descriptors

    fmdl.writeFile(file_path)
    logging.debug(f"Updated texture directory paths in: {file_path}")


def main():
    if not((len(sys.argv) >= 3) and (len(sys.argv) <= 4)):
        logging.debug("Error: Invalid arguments.\nUsage: id.exe <.fmdl file> <new ID> [team ID]")
    elif not(os.path.isfile(sys.argv[1])):
        logging.debug("Error: Provided file " + sys.argv[1] + " doesn't exist or is not a valid file")
    elif not(fnmatch.fnmatch(sys.argv[1], '*.fmdl')):
        logging.debug("Error: Provided file " + sys.argv[1] + " doesn't appear to be a .fmdl file")
        logging.debug("Please make sure the file ends in \".fmdl\"")
    else:
        fmdl_id_change(sys.argv[1], sys.argv[2], sys.argv[3])

if __name__ == '__main__':
    main()