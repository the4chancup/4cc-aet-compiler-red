## Reads team and kit color entries from Note files and adds them to bin files
import os


def bytes_from_color(color_entry_parts, index, colors_type_hex=False):

    if colors_type_hex:
        # Split the RRGGBB string into its three components, by removing the # at the start and copying two characters into each component
        color = [color_entry_parts[index][i:i+2] for i in range(1, len(color_entry_parts[index]), 2)]

        # Check that each component is a valid hexadecimal number in the range 00-FF
        for component in color:
            try:
                if len(component) != 2 or int(component, 16) < 0 or int(component, 16) > 255:
                    raise ValueError
            except ValueError:
                # If a part is not a valid hexadecimal number or is out of range, reject the whole entry
                print(f"- Color entry {color_entry_parts} has invalid RGB component {component}.")
                return []
    else:
        # Convert the three decimal RGB components to hex, removing the resulting "0x" prefix and filling with a leading zero if necessary
        color = []
        for i in range(index, index + 3):
            try:
                value = int(color_entry_parts[i])
                if value < 0 or value > 255:
                    raise ValueError
                color.append(hex(value).replace("0x", "").zfill(2).upper())
            except ValueError:
                # If a part is not a valid decimal number or is out of range, reject the whole entry
                print(f"- Color entry {color_entry_parts} has invalid RGB component {color_entry_parts[i]}.")
                return []

    return color

def bytes_from_color_entry(color_entry,type_kits = False):

    # Split the color entry into its components
    color_entry_parts = color_entry.split()

    # If the color entry is for kits
    if type_kits:
        # Remove the first part from the color entry to keep the indices consistent
        color_entry_parts = color_entry_parts[1:]

    # Check if the colors are hex or decimal
    colors_type_hex = color_entry_parts[2].startswith("#")

    # Assign the colors
    color1_index = 2
    color1 = bytes_from_color(color_entry_parts, color1_index, colors_type_hex)

    # Kit color entries have two colors and might have an icon number
    if type_kits:
        if colors_type_hex:
            color2_index = 4
            icon_index = 6
        else:
            color2_index = 6
            icon_index = 10
        color2 = bytes_from_color(color_entry_parts, color2_index, colors_type_hex)

        # Check if there is an icon number between 0 and 23
        if icon_index < len(color_entry_parts) and 0 <= int(color_entry_parts[icon_index]) <= 23:
            # Convert the icon number to hex
            icon = hex(int(color_entry_parts[icon_index])).replace("0x", "").zfill(2).upper()
        else:
            icon = None

        return color1, color2, icon
    else:
        return color1


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

    return


def kitcolor_bin_update(team_id, kitcols, kitcolor_bin):

    # Initialize the number of player and GK kits to 0
    player_kits = 0
    gk_kits = 0

    # Compute the starting hexadecimal position in the UniColor.bin file to write to
    position = "0x0" + ((int(team_id) - 100) * 85).to_bytes(2, byteorder='big').hex().upper()

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

        # Check the kit type
        if kit[0].lower() == "gk:":
            # If it is a GK kit, prepare a number with the GK kit number increased by 16
            kit_number = gk_kits + 16

            # Increment the GK kit number
            gk_kits += 1
        else:
            # If it is a player kit, prepare a number with the player kit number
            kit_number = player_kits

            # Increment the player kit number
            player_kits += 1

        # Convert the kit number to hexadecimal
        kit_number_hex = hex(kit_number).replace("0x", "").zfill(2).upper()

        # Check if the kit has an icon
        if kit[3]:
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

    return


def bins_update(teamcolor_bin_path, kitcolor_bin_path):

    # Read the necessary parameters
    all_in_one = int(os.environ.get('ALL_IN_ONE', '0'))
    pause_on_error = int(os.environ.get('PAUSE_ON_ERROR', '0'))

    print("-")
    print("- Adding the color entries to the bin files")
    print("- Working on team:")

    extracted_exports_dir = "./extracted_exports/"
    teams_list_file = "./teams_list.txt"

    # Open the TeamColor.bin file in binary mode for writing
    teamcolor_bin = open(teamcolor_bin_path, 'rb+')

    # Open the UniColor.bin file in binary mode for writing
    kitcolor_bin = open(kitcolor_bin_path, 'rb+')

    # For every Note txt file
    for file_name in [f for f in os.listdir(extracted_exports_dir) if f.endswith(".txt")]:

        file_path = os.path.join(extracted_exports_dir, file_name)
        with open(file_path, 'r', encoding="utf8") as file:

            # Initialize variables
            stop = None
            team_id_found = False

            teamcols_search = False
            teamcols = []
            teamcols_cnt = 0

            kitcols_search = False
            kitcols = []
            kitcols_cnt = 0

            for line in file:

                # Break when stop is true
                if stop:
                    break

                # Skip empty lines
                if not line.strip():
                    continue

                data = line.split()

                # If we just started output the team name to screen
                if not team_id_found:

                    # Set the team name to the last word on the line
                    team_name = data[-1]

                    # Search for the team name in the list of team IDs
                    with open(teams_list_file, 'r') as teams_list:

                        for teams_list_line in teams_list:
                             if teams_list_line.split()[1] == team_name.lower():
                                team_id = teams_list_line.split()[0]
                                team_id_found = True
                                break

                    # Print team name and ID if found
                    if team_id_found:
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

                    # If we've reached the Player section or the Other section
                    if data[0].lower() == "player" or data[0].lower() == "other":

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

                            # Store the kit type
                            kitcol[0] = data[2]

                            # Add the entry to the kit color list
                            kitcols.append(kitcol)

        # When the file is done, update the bin files

        # If there are team colors
        if teamcols:
            # Update the team bin
            teamcolor_bin_update(team_id, teamcols, teamcolor_bin)

            # Store the number of team colors
            teamcols_cnt = len(teamcols)

        # If there are kit colors
        if kitcols:
            # Update the kits bin
            kitcolor_bin_update(team_id, kitcols, kitcolor_bin)

            # Store the number of kit colors
            kitcols_cnt = len(kitcols)

            # Set the kit configs folder path
            kit_configs_folder_path = os.path.join('extracted_exports', 'Kit Configs', team_id)

            # If there's a kit configs folder and we haven't checked the amount of kits before
            if os.path.exists(kit_configs_folder_path) and not all_in_one:

                # Check that the amount of kits found is equal to the amount of kit config files
                kit_configs_cnt = len(os.listdir(kit_configs_folder_path))

                if kit_configs_cnt != kitcols_cnt:
                    # Print a warning
                    print('- Warning -')
                    if team_name:
                        print(f"- The amount of {team_name}'s kit color entries is not")
                    else:
                        print(f"- The amount of {team_id}'s kit color entries is not")
                    print('- equal to the amount of kit config files')
                    print('- Stopping the script and fixing it is recommended')
                    print('-')

                    if not pause_on_error:
                        input('Press Enter to continue...')

        # Print the number of team and kit colors
        print(f"- Team colors: {teamcols_cnt} - Kits: {kitcols_cnt}")


    # Close the TeamColor.bin file
    teamcolor_bin.close()

    # Close the UniColor.bin file
    kitcolor_bin.close()

    print("- Done")
    print("- ")
