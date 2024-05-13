import os
import re
import sys
import struct
import fnmatch
import logging


def fmdl_id_change(file_path: str, id: str, team_id: str = "000"):

    # Make sure the file exists
    if not os.path.exists(file_path):
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
        if(string):
            string_list.append(string)

    # Scan textures
    file_binary.seek(header_length + texture_offset)
    texture_path_list = []
    for i in range(texture_count):
        texture_path = struct.unpack("<H", file_binary.read(2))[0]
        if texture_path not in texture_path_list:
            texture_path_list.append(texture_path)

    # Close file for now, we're done reading
    file_binary.close()

    # Texture Path Count, for error reporting
    texture_path_count = 0

    # Process the paths
    for texture_path in texture_path_list:
        texture_path_split = string_list[texture_path-1].split("/") # Split path to individual pieces

        # Make sure our magic piece is the player ID and the path is the correct path
        # Faces path
        if(len(texture_path_split) == 10 and re.fullmatch("[0-9]{5}", texture_path_split[7])):
            if(id.isdigit() and len(id) == 5):
                texture_path_split[7] = str(id) # Change the ID
                texture_path_new = "/".join(texture_path_split) # Combine the path
                string_list[texture_path-1] = texture_path_new # Overwrite old path in string list
                texture_path_count = texture_path_count + 1
            else:
                logging.debug("Incorrect player ID " + id + ", please make sure the ID is exactly 5 digits long")

        # Refs path
        if(len(texture_path_split) == 10 and re.fullmatch("referee[0-9]{3}", texture_path_split[7])):
            if(re.fullmatch("referee[0-9]{3}", id)):
                texture_path_split[7] = str(id) # Change the ID
                texture_path_new = "/".join(texture_path_split) # Combine the path
                string_list[texture_path-1] = texture_path_new # Overwrite old path in string list
                texture_path_count = texture_path_count + 1
            else:
                logging.debug("Incorrect referee name " + id)

        # Boots path
        elif(len(texture_path_split) == 8 and re.fullmatch("k[0-9]{4}", texture_path_split[6])):
            if(re.fullmatch("k[0-9]{4}", id)):
                texture_path_split[6] = id # Change the ID
                texture_path_new = "/".join(texture_path_split) # Combine the path
                string_list[texture_path-1] = texture_path_new # Overwrite old path in string list
                texture_path_count = texture_path_count + 1
            else:
                logging.debug("Incorrect boots ID " + id + ", please make sure the ID is exactly 5 characters long and follows the 'kXXXX' format")

        # Gloves path
        elif(len(texture_path_split) == 8 and re.fullmatch("g[0-9]{4}", texture_path_split[6])):
            if(re.fullmatch("g[0-9]{4}", id)):
                texture_path_split[6] = id # Change the ID
                texture_path_new = "/".join(texture_path_split) # Combine the path
                string_list[texture_path-1] = texture_path_new # Overwrite old path in string list
                texture_path_count = texture_path_count + 1
            else:
                logging.debug("Incorrect gloves ID " + id + ", please make sure the ID is exactly 5 characters long and follows the 'gXXXX' format")

        # Balls path
        elif(len(texture_path_split) == 7 and re.fullmatch("ball[0-9]{3}", texture_path_split[5])):
            if(re.fullmatch("ball[0-9]{3}", id)):
                texture_path_split[5] = id # Change the ID
                texture_path_new = "/".join(texture_path_split) # Combine the path
                string_list[texture_path-1] = texture_path_new # Overwrite old path in string list
                texture_path_count = texture_path_count + 1
            else:
                logging.debug("Incorrect ball ID " + id + ", please make sure the ID is exactly 7 characters long and follows the 'ballXXX' format")

        # Common path
        elif(len(texture_path_split) == 9 and re.fullmatch("[0-9]{3}", texture_path_split[6])):
            if(re.fullmatch("[0-9]{3}", team_id)):
                texture_path_split[6] = team_id # Change the ID
                texture_path_new = "/".join(texture_path_split) # Combine the path
                string_list[texture_path-1] = texture_path_new # Overwrite old path in string list
                texture_path_count = texture_path_count + 1
            else:
                logging.debug("Incorrect Team ID " + team_id + ", please make sure the ID is exactly 3 characters long and follows the 'XXX' format")

        else:
            logging.debug("No ID found in path " + string_list[texture_path-1])

    # Yell if there were no paths with IDs at all
    if(texture_path_count == 0):
        logging.debug("No paths with IDs found in file " + file_path)

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