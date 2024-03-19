import os
import sys
import shutil
from .lib import pes_cpk_pack as cpktool

def patches_from_contents():
    
    # Read the necessary parameters
    all_in_one = int(os.environ.get('ALL_IN_ONE', '0'))
    move_cpks = int(os.environ.get('MOVE_CPKS', '0'))
    pes_download_folder_location = os.environ.get('PES_DOWNLOAD_FOLDER_LOCATION', 'unknown')
    bins_updating = int(os.environ.get('BINS_UPDATING', '0'))

    multicpk_mode = int(os.environ.get('MULTICPK_MODE', '0'))
    cpk_name = os.environ.get('CPK_NAME', '4cc_79_midcup')
    faces_cpk_name = os.environ.get('FACES_CPK_NAME', '4cc_40_faces')
    uniform_cpk_name = os.environ.get('UNIFORM_CPK_NAME', '4cc_45_uniform')
    bins_cpk_name = os.environ.get('BINS_CPK_NAME', '4cc_08_bins')
    
    
    # Set the name for the folders to put stuff into
    if not multicpk_mode:

        faces_foldername = "Singlecpk"
        uniform_foldername = "Singlecpk"
        bins_foldername = "Singlecpk"
        
    else:

        faces_foldername = "Facescpk"
        uniform_foldername = "Uniformcpk"
        bins_foldername = "Binscpk"

    # Create output folder just in case
    os.makedirs("./patches_output", exist_ok=True)

    # Verify that the input folders exist, stop the script otherwise
    if (not os.path.exists(f"./patches_contents/{faces_foldername}") or
        not os.path.exists(f"./patches_contents/{uniform_foldername}") or
        (not os.path.exists(f"./patches_contents/{bins_foldername}") and bins_updating)):
        input("Input folder not found. Exiting...")
        exit()
        

    # Make the patches
    if multicpk_mode:
    
        # Make sure that the folders are not empty to avoid errors
        if not os.listdir(f"./patches_contents/{faces_foldername}"):
            open(f"./patches_contents/{faces_foldername}/placeholder", 'w').close()
        if not os.listdir(f"./patches_contents/{uniform_foldername}"):
            open(f"./patches_contents/{uniform_foldername}/placeholder", 'w').close()
        if bins_updating and not os.listdir(f"./patches_contents/{bins_foldername}"):
            open(f"./patches_contents/{bins_foldername}/placeholder", 'w').close()


        # Make the Faces patch (faces, portraits)
        print('-')
        print('- Packing the Faces patch')

        source_path = os.path.join("patches_contents", f"{faces_foldername}")
        source_contents_path_list = [os.path.join(source_path, x) for x in os.listdir(source_path)]
        destination_path = os.path.join("patches_output", f"{faces_cpk_name}.cpk")
        
        cpktool.main(destination_path, source_contents_path_list, True)

        # Make the Uniform patch (kits, logos, boots, gloves, etc.)
        print('-')
        print('- Packing the Uniform patch')

        source_path = os.path.join("patches_contents", f"{uniform_foldername}")
        source_contents_path_list = [os.path.join(source_path, x) for x in os.listdir(source_path)]
        destination_path = os.path.join("patches_output", f"{uniform_cpk_name}.cpk")
        
        cpktool.main(destination_path, source_contents_path_list, True)


        if bins_updating:

            # Make the Bins patch (unicolor, teamcolor)
            print('-')
            print('- Packing the Bins patch')

            source_path = os.path.join("patches_contents", f"{bins_foldername}")
            source_contents_path_list = [os.path.join(source_path, x) for x in os.listdir(source_path)]
            destination_path = os.path.join("patches_output", f"{bins_cpk_name}.cpk")
            
            cpktool.main(destination_path, source_contents_path_list, True)
        
    else:

        # Make sure that the folder is not empty to avoid errors
        if not os.listdir("./patches_contents/Singlecpk"):
            open("./patches_contents/Singlecpk/placeholder", 'w').close()


        # Make the single cpk patch
        print('-')
        print('- Packing the patch')
        
        source_path = os.path.join("patches_contents", "Singlecpk")
        source_contents_path_list = [os.path.join(source_path, x) for x in os.listdir(source_path)]
        destination_path = os.path.join("patches_output", f"{cpk_name}.cpk")
        
        cpktool.main(destination_path, source_contents_path_list, True)


    # If Move Cpks mode is enabled
    if move_cpks:

        print('-')
        print('- Move Cpks mode is enabled')
        print('-')
        print('- Moving the cpks to the download folder')
        print('-')

        if multicpk_mode:

            # Remove the cpks from the destination folder if present
            if os.path.exists(f"{pes_download_folder_location}/{faces_cpk_name}.cpk"):
                os.remove(f"{pes_download_folder_location}/{faces_cpk_name}.cpk")
            if os.path.exists(f"{pes_download_folder_location}/{uniform_cpk_name}.cpk"):
                os.remove(f"{pes_download_folder_location}/{uniform_cpk_name}.cpk")
            if bins_updating:
                if os.path.exists(f"{pes_download_folder_location}/{bins_cpk_name}.cpk"):
                    os.remove(f"{pes_download_folder_location}/{bins_cpk_name}.cpk")

            # Move the cpks to the destination folder
            shutil.move(f"patches_output/{faces_cpk_name}.cpk", pes_download_folder_location)
            shutil.move(f"patches_output/{uniform_cpk_name}.cpk", pes_download_folder_location)
            if bins_updating:
                shutil.move(f"patches_output/{bins_cpk_name}.cpk", pes_download_folder_location)

        else:

            # Remove the cpk from the destination folder if present
            if os.path.exists(f"{pes_download_folder_location}/{cpk_name}.cpk"):
                os.remove(f"{pes_download_folder_location}/{cpk_name}.cpk")

            # Move the cpk to the destination folder
            shutil.move(f"patches_output/{cpk_name}.cpk", pes_download_folder_location)


    print('-')
    print('- The patches have been created')
    print('-')

    log = int(os.environ.get('LOG', '0'))

    if all_in_one:
        if log:
            # Warn about there being some issues and about having to open memelist.txt
            print("- Warning: There were some issues in the exports.")
            print("- Please check the memelist.txt file for a log.")
            print('-')
        else:
            print('- No issues were found in the exports.')
            print('-')

        if sys.platform == "win32":
            os.system("color")
        print('- 4cc aet compiler ' + '\033[91m' + 'Red' + '\033[0m' + ' by Shakes')
        print('-')
        print('-')

        # Reset the all_in_one mode flag
        os.environ['ALL_IN_ONE'] = '0'
        