## Reads team and kit color entries from Note files and adds them to bin files
import os
import re
import sys
import shutil
import logging

from . import pes_uniparam_edit as uniparamtool
from .cpk_tools import files_fetch_from_cpks
from .team_id_get import id_search
from .utils.file_management import file_critical_check, remove_readonly
from .utils.logging_tools import logger_stop
from .utils.pausing import pause
from .utils.FILE_INFO import (
    EXTRACTED_TEAMS_PATH,
    TEAMS_LIST_PATH,
    BIN_FOLDER_PATH,
    PATCHES_CONTENTS_PATH,
    TEAMCOLOR_BIN_NAME,
    UNICOLOR_BIN_NAME,
    UNIPARAM_NAME,
    UNIPARAM_18_NAME,
    UNIPARAM_19_NAME,
)


def bytes_from_color(color_entry, colors_type_hex=False):

    if colors_type_hex:
        # Remove the # at the start
        color_entry = color_entry.strip('#')
        # Check that each component is a valid hexadecimal number in the range 00-FF
        color = []
        # Split the RRGGBB string into its three components, by copying two characters into each component
        for component_start_index in [0, 2, 4]:
            part = color_entry[component_start_index:component_start_index+2]
            try:
                # Sanity check: ensure the part is a valid hexadecimal number
                int(part, 16)

                part_hex = part.upper()
                color.append(part_hex)

            except ValueError:
                # If a part is not a valid hexadecimal number or is out of range, reject the whole entry
                print(f"- Color entry {color_entry} has invalid RGB component {part}.")
                return []
    else:
        # Convert the three decimal RGB components to hex
        color = []
        for part in color_entry:
            try:
                # Sanity check: ensure the part is a valid decimal number
                part_int = int(part)
                if part_int < 0 or part_int > 255:
                    raise ValueError

                # Convert the decimal RGB component to hex, removing the resulting "0x" prefix
                # and filling with a leading zero if necessary
                part_hex = hex(part_int).replace("0x", "").zfill(2).upper()
                color.append(part_hex)

            except ValueError:
                # If a part is not a valid decimal number or is out of range, reject the whole entry
                print(f"- Color entry {color_entry} has invalid RGB component {part}.")
                return []

    return color

def bytes_from_color_entry(color_entry, type_kits = False):

    # Split the color entry into its components
    color_entry_parts = re.findall(r"#?[\dA-Fa-f]{1,6}", re.split(r":\s?", color_entry)[-1])

    # Check if the colors are hex or decimal
    colors_type_hex = color_entry_parts[0].startswith("#")

    # Assign the colors
    # Kit color entries have two colors and might have an icon number
    if type_kits:
        if colors_type_hex:
            icon_length_check_threshold = 2
            color1 = bytes_from_color(color_entry_parts[0], colors_type_hex)
            color2 = bytes_from_color(color_entry_parts[1], colors_type_hex)
        else:
            icon_length_check_threshold = 6
            color1 = bytes_from_color(color_entry_parts[0:3], colors_type_hex)
            color2 = bytes_from_color(color_entry_parts[3:6], colors_type_hex)

        # Check if there is an icon number between 0 and 23
        if len(color_entry_parts) > icon_length_check_threshold:
            try:
                icon_number = int(color_entry_parts[-1])
                if 0 <= icon_number <= 23:
                    # Convert the icon number to hex
                    icon = hex(icon_number).replace("0x", "").zfill(2).upper()
                else:
                    icon = None
            except ValueError:
                icon = None
        else:
            icon = None

        return color1, color2, icon
    else:
        if colors_type_hex:
            return bytes_from_color(color_entry_parts[0], colors_type_hex)
        else:
            return bytes_from_color(color_entry_parts[0:3], colors_type_hex)


def teamcolor_bin_update(team_id, teamcols, teamcolor_bin):

    # Compute the starting hexadecimal position in the TeamColor.bin file to write to
    position = "0x0" + (int(team_id) - 100).to_bytes(2, byteorder='big').hex().upper() + "0"

    # Increment the position by 4 to get to the first color entry of the team
    position = hex(int(position, 16) + 4).replace("0x", "").upper()

    # For each color
    for teamcol in teamcols:

        # Convert the color to bytes
        color_bytes = bytes.fromhex(f"{teamcol[0]+teamcol[1]+teamcol[2]}")

        # Write the color to the file
        teamcolor_bin.seek(int(position, 16))
        teamcolor_bin.write(color_bytes)

        # Increment the position by 3
        position = hex(int(position, 16) + 3).replace("0x", "").upper()

    return len(teamcols)


def kitcolor_bin_update(team_id, kitcols, kitcolor_bin):

    # Initialize the number of player and GK kits to 0
    player_kits = 0
    gk_kits = 0

    # Compute the starting hexadecimal position in the UniColor.bin file to write to
    position = "0x0" + ((int(team_id) - 100) * 85).to_bytes(4, byteorder='big').hex().upper()

    # Increment the position by 4 to get to the number of kits
    position = hex(int(position, 16) + 4).replace("0x", "").upper()

    # Check if there are more than 10 kits
    if len(kitcols) > 10:
        kits_number = 10
    else:
        kits_number = len(kitcols)

    # Convert the number of kits to bytes
    kits_number_bytes = int(kits_number).to_bytes(1, byteorder='big')

    # Write the number of kits
    kitcolor_bin.seek(int(position, 16))
    kitcolor_bin.write(kits_number_bytes)

    # Increment the position by 1 to get to the first kit entry of the team
    position = hex(int(position, 16) + 1).replace("0x", "").upper()

    # For each kit
    for kit in kitcols:

        # Check the kit type from the stored line
        type_gk = "gk:" in kit[0].lower()

        if type_gk:
            # Prepare a number with the GK kit number increased by 0x10
            kit_number = gk_kits + 16

            # Increment the GK kit counter
            gk_kits += 1
        else:
            # Prepare a number with the player kit number
            kit_number = player_kits

            # Increment the player kit counter
            player_kits += 1

        # Convert the kit number to hexadecimal
        kit_number_hex = hex(kit_number).replace("0x", "").zfill(2).upper()

        # Check if the kit has an icon
        if kit[3] is not None:
            # Store the icon number
            kit_icon_hex = kit[3]
        else:
            # If the kit doesn't have an icon, set the icon number to 3
            kit_icon_hex = "03"

        # Prepare the bytes for the kit
        kit_bytes = bytes.fromhex(f"{kit_number_hex}{kit_icon_hex}{kit[1][0]}{kit[1][1]}{kit[1][2]}{kit[2][0]}{kit[2][1]}{kit[2][2]}")

        # Write the kit to the file
        kitcolor_bin.seek(int(position, 16))
        kitcolor_bin.write(kit_bytes)

        # Increment the position by 8
        position = hex(int(position, 16) + 8).replace("0x", "").upper()

    # For every kit entry still needed to reach a total of 10
    for _ in range(10 - kits_number):

        # Prepare the bytes for the dummy kit
        kit_bytes = bytes.fromhex("FF00000000000000")

        # Write the kit to the file
        kitcolor_bin.seek(int(position, 16))
        kitcolor_bin.write(kit_bytes)

        # Increment the position by 8
        position = hex(int(position, 16) + 8).replace("0x", "").upper()

    return player_kits, gk_kits


def bins_update(teamcolor_bin_path, kitcolor_bin_path):

    # Check if the teams list file exists
    file_critical_check(TEAMS_LIST_PATH)

    # Read the necessary parameters
    all_in_one = int(os.environ.get('ALL_IN_ONE', '0'))

    print("-")
    print("- Adding the color entries to the bin files")
    print("- Working on team:")

    # Open the TeamColor.bin file in binary mode for writing
    teamcolor_bin = open(teamcolor_bin_path, 'rb+')

    # Open the UniColor.bin file in binary mode for writing
    kitcolor_bin = open(kitcolor_bin_path, 'rb+')

    # For every Note txt file
    for file_name in [f for f in os.listdir(EXTRACTED_TEAMS_PATH) if f.lower().endswith("note.txt")]:

        # Initialize variables
        stop = None
        team_id = None

        teamcols_search = False
        teamcols = []
        teamcols_cnt = 0

        kitcols_search = False
        kitcols = []
        kitcols_player_cnt = 0
        kitcols_gk_cnt = 0

        file_path = os.path.join(EXTRACTED_TEAMS_PATH, file_name)
        with open(file_path, 'r', encoding="utf8") as file:

            for line in file:

                # Break when stop is true
                if stop:
                    break

                # Skip empty lines
                if not line.strip():
                    continue

                data = line.split()

                # If we just started output the team name to screen
                if team_id is None:

                    # Set the team name to the last word on the line
                    team_name = data[-1]

                    # Search for the team name in the list of team IDs
                    team_id = id_search(team_name)

                    # Print team name and ID if found
                    if team_id is not None:
                        print(f"- {team_name} (ID: {team_id})")

                # If the team ID was found
                else:

                    # If we've reached the Team Color section
                    if data[0].lower() == "team" and data[1][0:2].lower() == "co":

                        # Start looking for the team colors
                        teamcols_search = True
                        kitcols_search = False

                    # If we've reached the Kit Color section
                    if data[0].lower() == "kit" and data[1][0:2].lower() == "co":

                        # Start looking for the kit colors
                        kitcols_search = True
                        teamcols_search = False

                    # If we've reached the Player, Other, or Notes section
                    if any(line.lower().startswith(word) for word in ["player", "other", "notes"]):

                        # Stop looking for data in this file
                        stop = True

                    # If we're looking for the team colors
                    if teamcols_search and data[0][0] == "-":

                        # Initialize a variable to store the team color entry
                        teamcol = None

                        # Convert the color entry to bytes
                        teamcol = bytes_from_color_entry(line, type_kits = False)

                        if teamcol:
                            # Add the entry to the team color list
                            teamcols.append(teamcol)

                    # If we're looking for the kit colors
                    if kitcols_search and data[0][0] == "-":

                        # Create a list to store the kit color entry
                        kitcol = [[], [], [], None]

                        # Convert the color entry to bytes
                        kitcol[1], kitcol[2], kitcol[3] = bytes_from_color_entry(line, type_kits = True)

                        if kitcol[1] and kitcol[2]:

                            # Store the full line to get the kit type later
                            kitcol[0] = line

                            # Add the entry to the kit color list
                            kitcols.append(kitcol)

        if team_id is None:

            # If no team ID was found, continue to the next file
            logging.error(f"- {team_name} skipped (no team ID found)")

            continue

        # When the file is done, update the bin files

        # If there are team colors
        if teamcols:
            # Update the team bin
            teamcols_cnt = teamcolor_bin_update(team_id, teamcols, teamcolor_bin)

        # If there are kit colors
        if kitcols:
            # Update the kits bin
            kitcols_player_cnt, kitcols_gk_cnt = kitcolor_bin_update(team_id, kitcols, kitcolor_bin)

            # Store the number of kit colors
            kitcols_cnt = kitcols_player_cnt + kitcols_gk_cnt

            # Set the kit configs folder path
            kit_configs_folder_path = os.path.join(EXTRACTED_TEAMS_PATH, 'Kit Configs', team_id)

            # If there's a kit configs folder and we haven't checked the amount of kits before
            if os.path.exists(kit_configs_folder_path) and not all_in_one:

                # Check that the amount of kits found is equal to the amount of kit config files
                kit_configs_cnt = len(os.listdir(kit_configs_folder_path))

                if kit_configs_cnt != kitcols_cnt:

                    logging.warning( "-")
                    logging.warning( "- Warning - Missing kit configs or txt kit color entries")
                    if team_name:
                        logging.warning(f"- Team name:      {team_name}")
                    else:
                        logging.warning(f"- Team ID:        {team_id}")
                    logging.warning(f"- The number of kit config files ({kit_configs_cnt}) is not equal to")
                    logging.warning(f"- the number of kit color entries ({kitcols_cnt}) in the Note txt file")

        # Print the number of team and kit colors
        print(f"- Team colors: {teamcols_cnt} - Kits: {kitcols_player_cnt}P + {kitcols_gk_cnt}GK")


    # Close the TeamColor.bin file
    teamcolor_bin.close()

    # Close the UniColor.bin file
    kitcolor_bin.close()

    print("- Done")
    print("-")


def bins_pack(bins_foldername):

    # Read the necessary parameters
    fox_mode = (int(os.environ.get('PES_VERSION', '19')) >= 18)
    pes_19_plus = (int(os.environ.get('PES_VERSION', '19')) >= 19)

    # Set the paths
    COMMON_ETC_PATH = "common/etc"
    UNIFORM_TEAM_PATH = "common/character0/model/character/uniform/team"

    bins_folder_path = os.path.join(PATCHES_CONTENTS_PATH, bins_foldername)

    patch_bins_common_etc_path = os.path.join(bins_folder_path, COMMON_ETC_PATH)
    patch_bins_uniform_team_path = os.path.join(bins_folder_path, UNIFORM_TEAM_PATH)

    # Prepare a list of sources and destination paths for the bin files
    BINS_TEMP_FOLDER_PATH = os.path.join(BIN_FOLDER_PATH, "temp")
    TEAMCOLOR_BIN_TEMP_PATH = os.path.join(BINS_TEMP_FOLDER_PATH, TEAMCOLOR_BIN_NAME)
    UNICOLOR_BIN_TEMP_PATH = os.path.join(BINS_TEMP_FOLDER_PATH, UNICOLOR_BIN_NAME)

    bin_info_list = [
        {
            'source_path': f"{COMMON_ETC_PATH}/{TEAMCOLOR_BIN_NAME}",
            'destination_path': TEAMCOLOR_BIN_TEMP_PATH,
            'fallback_path': f"{BIN_FOLDER_PATH}/{TEAMCOLOR_BIN_NAME}",
        },
        {
            'source_path': f"{UNIFORM_TEAM_PATH}/{UNICOLOR_BIN_NAME}",
            'destination_path': UNICOLOR_BIN_TEMP_PATH,
            'fallback_path': f"{BIN_FOLDER_PATH}/{UNICOLOR_BIN_NAME}",
        },
    ]

    if fox_mode:
        # Set the filename depending on pes version
        UNIPARAM_TEMP_NAME = UNIPARAM_19_NAME if pes_19_plus else UNIPARAM_18_NAME
        UNIPARAM_BIN_TEMP_PATH = os.path.join(BINS_TEMP_FOLDER_PATH, UNIPARAM_TEMP_NAME)

        bin_info_list.append(
            {
                'source_path': f"{UNIFORM_TEAM_PATH}/{UNIPARAM_NAME}",
                'destination_path': UNIPARAM_BIN_TEMP_PATH,
                'fallback_path': f"{BIN_FOLDER_PATH}/{UNIPARAM_TEMP_NAME}",
            }
        )

    # Create the folders
    os.makedirs(patch_bins_common_etc_path, exist_ok=True)
    os.makedirs(patch_bins_uniform_team_path, exist_ok=True)
    os.makedirs(BINS_TEMP_FOLDER_PATH, exist_ok=True)

    # Fetch the bin files from the cpks in the download folder and update their values
    BIN_CPK_NAMES_LIST = ['midcup', 'bins']
    files_fetch_from_cpks(bin_info_list, BIN_CPK_NAMES_LIST)

    bins_update(TEAMCOLOR_BIN_TEMP_PATH, UNICOLOR_BIN_TEMP_PATH)

    # And copy them to the Bins cpk folder
    shutil.copy(TEAMCOLOR_BIN_TEMP_PATH, patch_bins_common_etc_path)
    shutil.copy(UNICOLOR_BIN_TEMP_PATH, patch_bins_uniform_team_path)

    # If fox mode is enabled and there's a Kit Configs folder
    itemfolder_path = os.path.join(EXTRACTED_TEAMS_PATH, "Kit Configs")
    if fox_mode and os.path.exists(itemfolder_path):

        print("- \n- Compiling the kit config files into the UniformParameter bin")

        # Prepare an array with all the kit config files inside each team folder in the Kit Configs folder
        kit_config_path_list = []
        for itemfolder_team in [f for f in os.listdir(itemfolder_path)]:
            itemfolder_team_path = os.path.join(itemfolder_path, itemfolder_team)

            # Add the path of each kit config file to the array
            for kit_config in [f for f in os.listdir(itemfolder_team_path) if f.endswith(".bin")]:
                kit_config_path = os.path.join(itemfolder_team_path, kit_config)
                kit_config_path_list.append(kit_config_path)

        # Compile the UniformParameter file
        uniparam_error = uniparamtool.main(UNIPARAM_BIN_TEMP_PATH, kit_config_path_list, [], UNIPARAM_BIN_TEMP_PATH, True)

        if uniparam_error:
            logging.critical("-")
            logging.critical("- FATAL ERROR - Error compiling the UniformParameter file")
            logging.critical("- The compiler will stop here because the generated cpk would crash PES")
            logging.critical("- Disable Bins Updating on the settings file and try again")
            logging.critical("-")
            logging.critical("- Please report this issue to the developer")
            logger_stop()

            pause("Press any key to exit... ", force=True)

            sys.exit()

        # Copy the uniparam to the the Bins cpk folder with the proper filename
        shutil.copy(UNIPARAM_BIN_TEMP_PATH, f"{patch_bins_uniform_team_path}/{UNIPARAM_NAME}")

        print("-")

    # Delete the bins temp folder
    shutil.rmtree(BINS_TEMP_FOLDER_PATH, onerror=remove_readonly)
