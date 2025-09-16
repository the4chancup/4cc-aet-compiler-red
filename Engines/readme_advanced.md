# 4cc AET Compiler Red
Read this advanced readme if you're making DLC for a cup or want to use the
compiler to its full potential.

Make sure to read the settings file for further customization options.
Keep in mind that "fox mode" is enabled automatically when PES Version is 18 or
higher.

- 1_exports_to_extracted
- 2_extracted_to_contents
- 3_contents_to_patches
- 0_all_in_one
- Extra info


## 1_exports_to_extracted

This script extracts the exports located in the "exports_to_add" folder into the
"extracted" folder, then checks them for typical issues, discarding the
whole export or parts of it if it finds any.
It also saves a log file named "issues.log" with the list of problems it found,
and pauses at every error unless the "pause_allow" setting has been disabled
in the settings file.

Here's a list of the stuff that the script checks after extracting an export,
before moving its content into folders shared by all the teams:
- Checks that the team name is in the "teams_list" file (if there's none, it
  uses the first word on the export's folder name as team name), and looks for
  the team name on the "teams_list" txt, to find the corresponding team ID.
- Checks for nested folders with repeated names (e.g. GD export/Faces/Faces),
  excluding the "Other" or "Common" folder, and tries to fix them by moving the
  folders down by one layer.
- Checks that the 4th and 5th characters of each face folder is in the 01-23
  range for player numbers.
- Checks that none of the face folders have the unsupported "face_edithair.xml"
  file inside.
- Checks that the "Faces" folder doesn't have any extra non-folder files
  (like cpks) in it.
- Checks that the kit config files and the kit texture files follow the proper
  naming convention as described on the "Kits" wikipage.
- Check that the amount of kit config files is consistent with what's listed on
  the team txt.
- Checks that all of the dds files for face textures, kit textures and
  portraits are proper dds files to avoid stuff like renamed pngs.
- Checks that the png files in the "Logo" folder are three and are
  properly named.
- Checks that the dds files in the "Portraits" folder are properly named.
- Checks that the boots folder names in the "Boots" folder start with a "k".
- Checks that the glove folder names in the "Gloves" folder start with a "g".

Having a Note txt file used to be compulsory but it isn't anymore. It's stil
recommended to have.
If there's no Note txt, the compiler will try to use the first word on the
export's folder as team name to use when looking for the team ID, which can be
useful for packing midcup stuff more quickly without having to add a Note txt
every time.
The Note txt is needed when adding new kits and/or changing their menu colors.

After the checks are done, the script sorts the export's content into folders
which hold the contents of all the processed exports, while at the same time
replacing the team ID on every file and folder (even inside the kit configs)
with the proper team ID.

This means that the team ID in the exports' files can be literally anything
three characters long, for example an old team ID, the current one or simply
XXX (recommended), since the compiler will ignore it and replace it with the
proper team ID it finds by looking for the team name on the teams_list file.
Thanks to this, you can use old exports from previous invitationals without
renaming anything manually.

It also copies the contents from all of the Note txt files into a single file
called "teamnotes.txt", allowing you to read them all quickly without having
to open multiple files.

Use this script on its own if you only want to check the exports for
correctness and/or prepare the "extracted" folder for the next step.


## 2_extracted_to_contents

This script makes a cpk/fpk for each of the folders in the "Faces" folder inside
the "extracted" folder and stores it in the "Singlecpk" or "Facescpk" folder
inside the "patches_contents" folder.

It also moves the content from the other "Kits", "Boots", "Gloves", "Collars",
"Logo", "Portraits" and "Common" folders to the proper folders in the
"Singlecpk", "Facescpk" or "Uniformcpk" folder inside the "patches_contents"
folder.
If "fox mode" is disabled, the contents of the "Common" folder will be moved to
  model/character/uniform/common/---/ (where --- is the team name),
otherwise they will be moved to
  Assets/model/character/common/XXX/sourceimages/#windx11 (where XXX is the
  team ID).

Also, if "Bins Update" is enabled, the team color and kit color entries from the
txt files are added to the "UniColor" and "TeamColor" bin files in other_stuff,
plus (if "fox mode" is on) the kit configs are copied to the "UniformParameter"
bin file. Then the bins are copied to the "Singlecpk" or "Binscpk" folder.

The choice of using a "Singlecpk" folder or multiple folders depends on whether
the "Multi Cpk" mode is enabled. This mode is recommended only when making cup
DLC for general release, after testing that everything is fine and nothing needs
fixing. The beta DLC for ATFing should be made with singlecpk mode set.

Use this script on its own when you want to prepare the "patches_contents"
folder with multiple exports in different moments before packing the final
cpk(s).


## 3_contents_to_patches

This script takes the contents from the folder(s) in the "patches_contents"
folder and packs them into a cpk(s) in the "patches_output" folder, whose
name(s) can be set in the settings file.

Then, depending on the settings you've set, it'll move the cpk(s) to your PES
"download" folder.

Use this script on its own after you've finished preparing the content from the
exports with the "extracted_to_content" script to make the final patch.
Running it on its own is also useful after you've manually added some files to
the folder(s) in the "patches_contents" folder.

Warning: Unless the "Cache Clearing" setting is disabled (enabled by default),
this script will delete the "patches_contents" folder after it's run, to prevent
old stuff from accidentally getting into the cpk(s).


## 0_all_in_one

This script simply runs the three main scripts one after the other, with a few
changes like asking for admin permissions (if needed) at the start of the first
script instead of waiting till the end, so that you can leave your pc unattended
right from the beginning.

It's the best choice if you just have a few clean exports and want to compile
them quickly into a cpk.


## Extra info

If you disable the "Cache Clearing" setting (enabled by default):
You can rerun the script to compile the exports located in the "exports_to_add"
folder again, updating the cpks and the content stored in the "patches_contents"
folder.
If you don't need to update the content for some of the exports, for example
because they haven't changed, you can remove them from the "exports_to_add"
folder and the script will use the content stored previously instead of
unnecessarily recompiling every face. This way you can save time by only putting
exports in the "exports_to_add" folder when they need to be updated.
