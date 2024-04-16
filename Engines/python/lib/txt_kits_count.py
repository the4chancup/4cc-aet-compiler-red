## Reads kit color entries from the provided Note file and returns the amount of them
from .bins_update import bytes_from_color_entry


def txt_kits_count(file_path):

    with open(file_path, 'r', encoding="utf8") as file:

        # Initialize variables
        stop = None

        kitcols_search = False
        kitcols_cnt = 0

        for line in file:

            # Break when stop is true
            if stop:
                break

            # Skip empty lines
            if not line.strip():
                continue

            data = line.split()

            # If we've reached the Kit Color section
            if data[0].lower() == "kit" and data[1][0:2].lower() == "co":

                # Start looking for the kit colors
                kitcols_search = True

            # If we've reached the Player section or the Other section
            if data[0].lower() == "player" or data[0].lower() == "other":

                # Stop looking for data in this file
                stop = True

            # If we're looking for the kit colors
            if kitcols_search and data[0][0] == "-":

                # Create a list to store the kit color entry
                kitcol = [[], [], [], None]

                # Convert the color entry to bytes
                kitcol[1], kitcol[2], kitcol[3] = bytes_from_color_entry(line, type_kits = True)

                if kitcol[1] and kitcol[2]:

                    # Increment the number of kit colors
                    kitcols_cnt += 1

    # Return the number of kit colors
    return kitcols_cnt
