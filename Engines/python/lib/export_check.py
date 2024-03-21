## Checks the export for all kinds of errors
import os
import shutil
from .utils.zlib_plus import unzlib_file
from .texture_check import texture_check
from .txt_kits_count import txt_kits_count


# Check for nested folders with repeating names
def nested_folders_fix(exportfolder_path, team_name):

    # Variable to store whether nested folders were found
    nested_error = None
    
    # Loop through each directory in the folder
    for folder_name in os.listdir(exportfolder_path):
        
        # Get the path of the directory
        folder_path = os.path.join(exportfolder_path, folder_name)
        
        # Check if it's a directory
        if os.path.isdir(folder_path):
            
            # Loop through each subdirectory
            for subfolder_name in os.listdir(folder_path):
                
                # Get the path of the subdirectory
                subfolder_path = os.path.join(folder_path, subfolder_name)
                
                # If the subdirectory has the same name as its parent folder
                if os.path.isdir(subfolder_path) and subfolder_name == folder_name:
                    
                    # Unless it's the 'Other' or 'Common' folders
                    if subfolder_name not in ('Other', 'Common'):
                        
                        nested_error = True
                        
                        # Create a temporary folder path in the main export folder
                        temp_path = os.path.join(exportfolder_path, 'Temp')
                        os.makedirs(temp_path, exist_ok=True)
                        
                        # Loop through each item in the subdirectory and move it to the temporary folder
                        for item_name in os.listdir(subfolder_path):
                            shutil.move(os.path.join(subfolder_path, item_name), temp_path)
                        
                        # Delete the now empty subdirectory
                        shutil.rmtree(subfolder_path)
                        
                        # Loop through each file in the temporary folder and move it to the proper folder
                        for item_name in os.listdir(temp_path):
                            shutil.move(os.path.join(temp_path, item_name), folder_path)
                        
                        # Delete the temporary folder
                        shutil.rmtree(temp_path)
    
    # If some folders were nested, warn about it
    if nested_error:

        with open("memelist.txt", "a") as log:
            log.write("- \n")
            log.write(f"- {team_name}'s manager needs to get memed on (nested folders) - Fix Attempted.\n")
        
        os.environ["LOG"] = "1"

        print("- ")
        print(f"- {team_name}'s manager needs to get memed on (nested folders).")
        print("- An attempt to automatically fix those folders has just been done.")
        print("- Nothing has been discarded, though problems may still arise.")

        if pause_when_wrong:
            print("- ")
            input("Press any key to continue...")


def faces_check(exportfolder_path, team_name):
    itemfolder_path = os.path.join(exportfolder_path, "Faces")
    
    # Check if the folder exists
    if os.path.isdir(itemfolder_path):
        
        # Check if the folder is empty
        if os.listdir(itemfolder_path):
            
            folder_error_any = None

            # For every subfolder
            for subfolder_name in os.listdir(itemfolder_path):
                
                subfolder_path = os.path.join(itemfolder_path, subfolder_name)
                
                # Initialize error subflags
                folder_error_num = False
                folder_error_edithairxml = False
                folder_error_noxml = False
                folder_error_nofpkxml = False
                folder_error_tex_format = False
                
                # Check that the player number is within the 01-23 range
                folder_error_num = not (subfolder_name[3:5].isdigit() and '01' <= subfolder_name[3:5] <= '23')

                if not fox_mode:
                    # Check that the folder has the essential face.xml and not the unsupported face_edithair.xml file
                    face_xml_path = os.path.join(subfolder_path, "face.xml")
                    face_edithair_xml_path = os.path.join(subfolder_path, "face_edithair.xml")
                    if os.path.isfile(face_edithair_xml_path):
                        folder_error_edithairxml = True
                    elif not os.path.isfile(face_xml_path):
                        folder_error_noxml = True

                else:
                    # Check that the folder has the essential face.fpk.xml file
                    face_fpk_xml_path = os.path.join(subfolder_path, "face.fpk.xml")
                    if not os.path.isfile(face_fpk_xml_path):
                        folder_error_nofpkxml = True

                # Check every texture
                for file_name in os.listdir(subfolder_path):
                    file_path = os.path.join(subfolder_path, file_name)

                    folder_error_tex_format = texture_check(file_path)
                    
                    if folder_error_tex_format:
                        break
                
                # Set the main flag if any of the checks failed
                folder_error = (folder_error_num or
                                folder_error_edithairxml or
                                folder_error_noxml or
                                folder_error_nofpkxml or
                                folder_error_tex_format)
            
                # If the face folder has something wrong
                if folder_error:
                    
                    # Open memelist.txt for appending
                    with open("memelist.txt", "a") as log:

                        # Warn about the team having bad folders
                        if not folder_error_any:
                            log.write("- \n")
                            log.write(f'- {team_name}\'s manager needs to get memed on (bad face folders).\n')
                            print("- ")
                            print(f'- {team_name}\'s manager needs to get memed on (bad face folders).')
                            folder_error_any = True

                        log.write(f'- The face folder {subfolder_name} is bad.\n')
                        print(f'- The face folder {subfolder_name} is bad.')

                        # Give an error depending on the particular problem
                        if folder_error_num:
                            log.write(f'- (player number {subfolder_name[3:5]} out of the 01-23 range) - Folder discarded\n')
                            print(f'- (player number {subfolder_name[3:5]} out of the 01-23 range) - Folder discarded')
                        if folder_error_nofpkxml:
                            log.write(f'- (no face.fpk.xml file inside) - Folder discarded)\n')
                            print(f'- (no face.fpk.xml file inside) - Folder discarded')
                        if folder_error_noxml:
                            log.write(f'- (no face.xml file inside) - Folder discarded)\n')
                            print(f'- (no face.xml file inside) - Folder discarded')
                        if folder_error_edithairxml:
                            log.write(f'- (unsupported edithair face folder, needs updating) - Folder discarded)\n')
                            print(f'- (unsupported edithair face folder, needs updating) - Folder discarded')
                        if folder_error_tex_format:
                            log.write(f'- ({file_name} is a bad texture) - Folder discarded)\n')
                            print(f'- ({file_name} is a bad texture) - Folder discarded')

                    # And skip it
                    shutil.rmtree(subfolder_path)

            # If there were any bad folders
            if folder_error_any:
                
                print("- These face folders will be discarded to avoid problems.")
                print("- Closing the script's window and fixing them is recommended.")
                
                os.environ["LOG"] = "1"

                if pause_when_wrong:
                    input('Press Enter to continue...')

        # If the folder exists but is empty, delete it
        else:
            shutil.rmtree(itemfolder_path)


# If a Kit Configs folder exists and is not empty, check that the amount of kit config files is correct
def kitconfigs_check(exportfolder_path, team_name):
    itemfolder_path = os.path.join(exportfolder_path, "Kit Configs")
    
    # Check if the folder exists
    if os.path.isdir(itemfolder_path):
        
        # Initialize the main error flag
        folder_error = False
            
        # Check if the folder is empty
        if os.listdir(itemfolder_path):
            
            # Initialize the error flag
            file_error = False
            
            # Check if the files are in an inner folder
            for subitem_name in os.listdir(itemfolder_path):
                subitem_path = os.path.join(itemfolder_path, subitem_name)
                if os.path.isdir(subitem_path):
                    
                    # If a folder was found move its contents to the root folder
                    for file in os.listdir(subitem_path):
                        shutil.move(os.path.join(subitem_path, file), itemfolder_path)
                    
                    # And delete the now empty folder
                    shutil.rmtree(subitem_path)

            config_count = len(os.listdir(itemfolder_path))

            # For every file
            for file_name in os.listdir(itemfolder_path):
                
                #TODO: Check if these checks are really case-insensitive
                # Check the DEF part of the name
                if not file_name[3:8].lower() == "_def_":#DEF?
                    file_error = True
                # Check the realUni part
                if not file_name[-12:].lower() == "_realuni.bin":#realUni?
                    file_error = True
                
                # Unzlib it if needed
                file_path = os.path.join(itemfolder_path, file_name)
                unzlib_file(file_path)
  
            # If any file was wrong
            if file_error:
                
                # Skip the whole folder
                shutil.rmtree(os.path.join(exportfolder_path, "Kit Configs"))

                # Log the issue
                with open("memelist.txt", "a") as log:
                    log.write("- \n")
                    log.write(f"- {team_name}'s manager needs to get memed on (wrong kit config names). - Kit Configs discarded\n")

                # Print the issue
                print("- ")
                print(f"- {team_name}'s manager needs to get memed on (wrong kit config names).")
                print("- The Kit Configs folder will be discarded since it's unusable.")
                print("- Closing the script's window and fixing it is recommended.")

                # Pause if needed
                if pause_when_wrong:
                    input("Press Enter to continue...")
            
            else:
                # Store the team name without the slashes at the ends
                team_name_raw = team_name[1:-1].upper()
                
                # Path to the txt file with the team's name
                note_path = os.path.join(exportfolder_path, f"{team_name_raw} Note.txt")
                
                # Check if the txt file exists
                if os.path.exists(note_path):

                    # Check that the amount of kit configs and kit color entries in the Note txt are the same
                    if txt_kits_count(note_path) != config_count:
                        
                        with open("memelist.txt", "a") as log:
                            log.write("- \n")
                            log.write(f"- {team_name}'s manager needs to get memed on (missing kit configs or txt kit color entries). - Warning\n")
                        
                        os.environ["LOG"] = "1"
                        
                        print("- ")
                        print(f"- {team_name}'s manager needs to get memed on (missing kit configs or txt kit color entries).")
                        print("- The amount of ", team_name, "'s kit color entries is not equal to")
                        print("- the amount of kit config files in the Note txt file.")
                        print("- Closing the script's window and fixing this is recommended.")
                        
                        if pause_when_wrong:
                            input("Press Enter to continue...")
                            
        # If the folder exists but is empty
        else:
            
            # Warn about it later
            folder_error = True
            
            # Delete the folder
            shutil.rmtree(itemfolder_path)
    
    # If the folder doesn't exist   
    else:
            
        # Warn about it later
        folder_error = True
        
    # If we need to warn about the folder
    if folder_error:
        
        # Warn about it
        with open("memelist.txt", "a") as log:
            log.write(f"- {team_name}'s export doesn't have any Kit Configs - Warning\n")
        
        os.environ["LOG"] = "1"
        
        print(f"- {team_name}'s export doesn't have any Kit Configs.")


# If a Kit Textures folder exists and is not empty, check that the kit textures' filenames and type are correct
def kittextures_check(exportfolder_path, team_name):
    itemfolder_path = os.path.join(exportfolder_path, "Kit Textures")

    # Check if the folder exists
    if os.path.isdir(itemfolder_path):
        
        # Initialize the main error flag
        folder_error = False
        
        # Check if the folder is empty
        if os.listdir(itemfolder_path):
            
            file_error_tex_format = False

            # Check every texture
            for file_name in os.listdir(itemfolder_path):
                file_path = os.path.join(itemfolder_path, file_name)

                file_error_tex_format = texture_check(file_path)
                
                if file_error_tex_format:
                    break
                

            # If the folder has a non-dds texture
            if file_error_tex_format:
                
                # Skip the whole Kit Textures folder
                shutil.rmtree(itemfolder_path)

                # Write to log
                with open("memelist.txt", "a") as log:
                    log.write("- \n")
                    log.write(f"- {team_name}'s manager needs to get memed on (bad kit textures) - Kit Textures discarded.\n")
                
                os.environ["LOG"] = "1"

                # Print to console
                print("- ")
                print(f"- {team_name}'s manager needs to get memed on (bad kit textures).")
                print("- This is usually caused by png textures renamed to dds instead of saved as dds.")
                if fox_mode:
                    print("- Or by missing mipmaps.")
                print(f"- First game-crashing texture found: {file_name}")
                print("- The Kit Textures folder will be discarded since it's unusable.")
                print("- Closing the script's window and fixing it is recommended.")

                if pause_when_wrong:
                    input("Press Enter to continue...")
            
            else:
                
                file_error_any = False

                # For every texture
                for file_name in os.listdir(itemfolder_path):
                    
                    # Check that its name starts with u and that its name has p or g in the correct position
                    if not (file_name[0] == 'u' and (file_name[5] == 'p' or file_name[5] == 'g')):
                        
                        # Warn about the team having bad texture names
                        if not file_error_any:
                            print("- ")
                            print(f"- {team_name}'s manager needs to get memed on (bad kit texture names).")
                            file_error_any = True
                        
                        print(f"- The kit texture {file_name} is bad. File discarded.")
                        
                        # And skip it
                        file_path = os.path.join(itemfolder_path, file_name)
                        os.remove(file_path)
                
                # If the team has bad files close the previously opened message
                if file_error_any:
                    
                    print("- The kit textures mentioned above will be discarded since they're unusable.")
                    print("- Closing the script's window and fixing them is recommended.")
                    
                    if pause_when_wrong:
                        input("Press Enter to continue...")
                        
        # If the folder exists but is empty
        else:
            
            # Warn about it later
            folder_error = True
            
            # Delete the folder
            shutil.rmtree(itemfolder_path)
    
    # If the folder doesn't exist   
    else:
            
        # Warn about it later
        folder_error = True
        
    # If we need to warn about the folder
    if folder_error:
        
        # Warn about it
        with open("memelist.txt", "a") as log:
            log.write("- \n")
            log.write(f"- {team_name}'s export doesn't have any Kit Textures - Warning\n")
        
        os.environ["LOG"] = "1"
        
        print("- ")
        print(f"- {team_name}'s export doesn't have any Kit Textures.")


# If a Logo folder exists and is not empty, check that the three logo images' filenames are correct
def logo_check(exportfolder_path, team_name):
    itemfolder_path = os.path.join(exportfolder_path, "Logo")
    
    # Check if the folder exists
    if os.path.isdir(itemfolder_path):
        
        # Check if the folder is empty
        if os.listdir(itemfolder_path):
            
            # Initialize the variables
            file_error = False
            file_count = 0
            file_good_count = 0

            # For every image
            for file_name in os.listdir(itemfolder_path):
                
                # Check that its name starts with emblem_
                file_error = not file_name.lower().startswith("emblem_")
                
                # Check the suffix and increase the plus counter if present and correct
                if (file_name.lower().endswith(("_r.png", "_r_l.png", "_r_ll.png"))):
                    file_good_count += 1
                
                file_count += 1
                
                if file_error:
                    break
            
            # Check that there are three total images and they all have the correct suffix
            if (file_count != 3) or (file_good_count != 3):
                file_error = True
            
            # If something's wrong
            if file_error:
                
                # Skip the whole folder
                shutil.rmtree(itemfolder_path)
                
                # Write to memelist.txt
                with open("memelist.txt", "a") as log:
                    log.write("- \n")
                    log.write(f"- {team_name}'s manager needs to get memed on (wrong logo filenames)\n")
                    
                os.environ["LOG"] = "1"
                
                # Warn user
                print("- ")
                print(f"- {team_name}'s manager needs to get memed on (wrong logo filenames)")
                print("- The Logo folder will be discarded since it's unusable.")
                print("- Closing the script's window and fixing it is recommended.")
                
                if pause_when_wrong:
                    input("Press Enter to continue...")
                    
        else:
            # If the folder exists but is empty, delete it
            shutil.rmtree(itemfolder_path)


# If a Portraits folder exists and is not empty, check that the portraits' filenames are correct
def portraits_check(exportfolder_path, team_name):
    itemfolder_path = os.path.join(exportfolder_path, "Portraits")
    
    # Check if the folder exists
    if os.path.isdir(itemfolder_path):
        
        # Check if the folder is empty
        if os.listdir(itemfolder_path):
            
            file_error_any = False
            
            for file_name in os.listdir(itemfolder_path):
                
                file_error = False
                file_error_id = True
                
                # Check that the player number starts with "player_" and is within the 01-23 range
                file_error_id = not (file_name[:7] == "player_" and file_name[-6:-4].isdigit() and '01' <= file_name[-6:-4] <= '23')
                
                # Check that the texture is proper
                file_path = os.path.join(itemfolder_path, file_name)
                file_error_tex_format = texture_check(file_path)
                
                # If the file is bad
                if file_error:
                    with open("memelist.txt", "a") as log:
                        if not file_error_any:
                            file_error_any = True
                            log.write("- \n")
                            log.write(f"- {team_name}'s manager needs to get memed on (bad portraits)\n")
                            print("- ")
                            print(f"- {team_name}'s manager needs to get memed on (bad portraits)")
                    
                        # Give an error depending on the particular problem
                        log.write(f"- The portrait {file_name} is bad.")
                        print(f"- The portrait {file_name} is bad.")
                        
                        if file_error_id:
                            log.write(f"- (player number {file_name[-6:-4]} out of the 01-23 range) - File discarded\n")
                            print(f"- (player number {file_name[-6:-4]} out of the 01-23 range)")
                        if file_error_tex_format:
                            log.write(f"- (bad format) - File discarded\n")
                            print(f"- (bad format)")
                        
                    # And skip it
                    os.remove(os.path.join(itemfolder_path, file_name))
                        
            # If the team has bad files close the previously opened message
            if file_error_any:
                
                print("- These portraits will be discarded since they're unusable.")
                print("- Closing the script's window and fixing them is recommended.")
                
                os.environ["LOG"] = "1"
                
                if pause_when_wrong:
                    input("Press Enter to continue...")
                    
        else:
            # If the folder exists but is empty, delete it
            shutil.rmtree(itemfolder_path)


# If a Common folder exists and is not empty, check that the textures inside are fine
def common_check(exportfolder_path, team_name):
    itemfolder_path = os.path.join(exportfolder_path, "Common")

    # Check if the folder exists
    if os.path.isdir(itemfolder_path):
        
        # Check if the folder is empty
        if os.listdir(itemfolder_path):

            file_error_any = False
            
            # Check every texture
            for file_name in os.listdir(itemfolder_path):
                file_path = os.path.join(itemfolder_path, file_name)

                file_error_tex_format = texture_check(file_path)
                
                # If the file has something wrong
                if file_error_tex_format:
                    
                    # Warn about the team having bad common textures
                    with open("memelist.txt", "a") as log:
                        if not file_error_any:
                            file_error_any = True
                            log.write("- \n")
                            log.write(f"- {team_name}'s manager needs to get memed on (bad common textures)\n")
                            print("- ")
                            print(f"- {team_name}'s manager needs to get memed on (bad common textures)")

                        log.write(f"- The common texture {file_name} is bad.\n")
                        print(f"- The common texture {file_name} is bad.")
                        
                    # And skip it
                    os.remove(os.path.join(itemfolder_path, file_name))
            
            # If the team has bad common textures close the previously opened message
            if file_error_any:

                print("- The textures mentioned above will be discarded since they're unusable.")
                print("- Closing the script's window and fixing them is recommended.")
                print("- ")
                
                os.environ["LOG"] = "1"

                if pause_when_wrong:
                    input("Press Enter to continue...")

        else:
            # If the folder exists but is empty, delete it
            shutil.rmtree(itemfolder_path)

# If a Boots folder exists and is not empty, check that the boots folder names are correct
def boots_check(exportfolder_path, team_name):
    itemfolder_path = os.path.join(exportfolder_path, "Boots")
  
    # Check if the folder exists
    if os.path.isdir(itemfolder_path):
        
        # Check if the folder is empty
        if os.listdir(itemfolder_path):

            folder_error_any = None
            
            # For every subfolder
            for subfolder_name in os.listdir(itemfolder_path):
                
                subfolder_path = os.path.join(itemfolder_path, subfolder_name)
                
                # Initialize error subflags
                folder_error_name = False
                folder_error_nofpkxml = False
                folder_error_tex_format = False
                
                # Check that its name starts with a k and that the 4 characters after it are digits
                folder_error_name = not (subfolder_name.startswith('k') and subfolder_name[1:5].isdigit())
                
                if fox_mode:
                    # Check that the folder has the essential boots.fpk.xml file
                    folder_error_nofpkxml = not os.path.isfile(os.path.join(subfolder_path, 'boots.fpk.xml'))
                
                # Check every texture
                for file_name in os.listdir(subfolder_path):
                    file_path = os.path.join(subfolder_path, file_name)

                    folder_error_tex_format = texture_check(file_path)
                    
                    if folder_error_tex_format:
                        break
                
                # Set the main flag if any of the checks failed
                folder_error = (folder_error_name or
                                folder_error_nofpkxml or
                                folder_error_tex_format)
                
                # If the folder has something wrong
                if folder_error:
                    
                    # Open memelist.txt for appending
                    with open("memelist.txt", "a") as log:
                        
                        # Warn about the team having bad folders
                        if not folder_error_any:
                            folder_error_any = True
                            log.write("- \n")
                            log.write(f"- {team_name}'s manager needs to get memed on.\n")
                            print("- ")
                            print(f"- {team_name}'s manager needs to get memed on.")
                        
                        log.write(f"- The boots folder {subfolder_name} is bad.\n")
                        print(f"- The boots folder {subfolder_name} is bad.")
                        
                        # Give an error depending on the particular problem
                        if folder_error_name:
                            log.write("- (wrong boots folder name)\n")
                            print("- (wrong boots folder name)")
                        if folder_error_nofpkxml:
                            log.write("- (no boots.fpk.xml file inside)\n")
                            print("- (no boots.fpk.xml file inside)")
                        if folder_error_tex_format:
                            log.write(f"- ({file_name} is a bad texture)\n")
                            print(f"- ({file_name} is a bad texture)")
                        
                    # And skip it
                    shutil.rmtree(subfolder_path)
            
            # If there were any bad folders
            if folder_error_any:
                
                print("- The boots folders mentioned above will be discarded since they're unusable.")
                print("- Closing the script's window and fixing them is recommended.")
                print("- ")
                
                os.environ["LOG"] = "1"
                
                if pause_when_wrong:
                    input("Press Enter to continue...")

        # If the folder exists but is empty, delete it
        else:
            shutil.rmtree(itemfolder_path)

# If a Gloves folder exists and is not empty, check that the boots folder names are correct
def gloves_check(exportfolder_path, team_name):
    itemfolder_path = os.path.join(exportfolder_path, "Gloves")
  
    # Check if the folder exists
    if os.path.isdir(itemfolder_path):
        
        # Check if the folder is empty
        if os.listdir(itemfolder_path):

            folder_error_any = None
            
            # For every subfolder
            for subfolder_name in os.listdir(itemfolder_path):
                
                subfolder_path = os.path.join(itemfolder_path, subfolder_name)
                
                # Initialize error subflags
                folder_error_name = False
                folder_error_nofpkxml = False
                folder_error_tex_format = False
                
                # Check that its name starts with a g and that the 3 characters after it are digits
                folder_error_name = not (subfolder_name.startswith('g') and subfolder_name[1:4].isdigit())
                
                if fox_mode:
                    # Check that the folder has the essential glove.fpk.xml file
                    folder_error_nofpkxml = not os.path.isfile(os.path.join(subfolder_path, 'glove.fpk.xml'))
                
                # Check every texture
                for file_name in os.listdir(subfolder_path):
                    file_path = os.path.join(subfolder_path, file_name)

                    folder_error_tex_format = texture_check(file_path)
                    
                    if folder_error_tex_format:
                        break
                
                # Set the main flag if any of the checks failed
                folder_error = (folder_error_name or
                                folder_error_nofpkxml or
                                folder_error_tex_format)
                
                # If the folder has something wrong
                if folder_error:
                    
                    # Open memelist.txt for appending
                    with open("memelist.txt", "a") as log:
                        
                        # Warn about the team having bad folders
                        if not folder_error_any:
                            folder_error_any = True
                            log.write("- \n")
                            log.write(f"- {team_name}'s manager needs to get memed on.\n")
                            print("- ")
                            print(f"- {team_name}'s manager needs to get memed on.")
                        
                        log.write(f"\nThe gloves folder {subfolder_name} is bad.")
                        print(f"\nThe gloves folder {subfolder_name} is bad.")
                        
                        # Give an error depending on the particular problem
                        if folder_error_name:
                            log.write("- (wrong gloves folder name)\n")
                            print("- (wrong gloves folder name)")
                        if folder_error_nofpkxml:
                            log.write("- (no gloves.fpk.xml file inside)\n")
                            print("- (no gloves.fpk.xml file inside)")
                        if folder_error_tex_format:
                            log.write(f"- ({file_name} is a bad texture)\n")
                            print(f"- ({file_name} is a bad texture)")
                        
                    # And skip it
                    shutil.rmtree(subfolder_path)
            
            # If there were any bad folders
            if folder_error_any:
                
                print("- The gloves folders mentioned above will be discarded since they're unusable.\n")
                print("- Closing the script's window and fixing them is recommended.\n")
                
                os.environ["LOG"] = "1"
                
                if pause_when_wrong:
                    input("Press Enter to continue...")

        # If the folder exists but is empty, delete it
        else:
            shutil.rmtree(itemfolder_path)


# If an Other folder exists, check that it's not empty
def other_check(exportfolder_path, team_name):
    itemfolder_path = os.path.join(exportfolder_path, "Other")
  
    # Check if the folder exists
    if os.path.isdir(itemfolder_path):
        
        # Check if the folder is empty
        if not os.listdir(itemfolder_path):
        
            # If the folder exists but is empty, delete it
            shutil.rmtree(itemfolder_path)
            

# Function with all the checks
def export_check(exportfolder_path, team_name):
    
    # Read the necessary parameters
    global fox_mode, fox_19, fox_21, pause_when_wrong
    fox_mode = (int(os.environ.get('PES_VERSION', '19')) >= 18)
    fox_19 = (int(os.environ.get('PES_VERSION', '19')) >= 19)
    fox_21 = (int(os.environ.get('PES_VERSION', '19')) >= 21)
    pause_when_wrong = int(os.environ.get('PAUSE_WHEN_WRONG', '1'))

    nested_folders_fix(exportfolder_path, team_name)
    faces_check(exportfolder_path, team_name)
    kitconfigs_check(exportfolder_path, team_name)
    kittextures_check(exportfolder_path, team_name)
    logo_check(exportfolder_path, team_name)
    portraits_check(exportfolder_path, team_name)
    common_check(exportfolder_path, team_name)
    boots_check(exportfolder_path, team_name)
    gloves_check(exportfolder_path, team_name)
    other_check(exportfolder_path, team_name)
    