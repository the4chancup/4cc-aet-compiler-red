import os
import re
import sys
import struct
import fnmatch
import logging

from .utils.id_change import path_id_change


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
        if(texture_path_section_count == model_path_info["section_count"] and
            re.fullmatch(model_path_info["id_pattern"], texture_path_split[model_path_info["id_section"]])):

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
        logging.warning("- Warning: No texture paths with IDs found")
        logging.warning(f"- Folder:         {file_folder}")
        logging.warning(f"- File:           {file_name}")
        logging.warning(f"- Model ID:       {model_id}")
        if team_id:
            logging.warning(f"- Team ID:        {team_id}")
        for texture_path in texture_path_list:
            logging.warning(f"- Texture path:   {texture_path}")
        logging.warning("- This model might work fine, double-check its texture paths if it doesn't")

    # Re-open file for writing
    file_binary = open(file_path, "r+b")

    # Seek to string block
    file_binary.seek(section1_offset + string_end)

    # Re-write FMDL strings
    for string in string_list:
        file_binary.write(struct.pack("B", 0))
        file_binary.write(bytes(string, 'utf-8'))

    # Done, close file for good and exit
    file_binary.close()

    return


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