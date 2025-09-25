# 4cc AET Compiler Red
Read this advanced readme if you're making DLC for a cup or want to use the
compiler to its full potential.

Make sure to also read the settings file for further customization options.

- Compiling Referees
- Scripts
  - 1_exports_to_extracted
  - 2_extracted_to_contents
  - 3_contents_to_patches
  - 0_all_in_one
- Message Types


## Compiling Referees
You first need a "refs export", which follows the next-generation format that
will be introduced in the future for team exports.
Here's an example:

refs  
│   Refs.txt  
│  
└───Players  
    ├───primal  
    │   ├───boots  
    │   ├───common  
    │   ├───face  
    │   └───gloves  
    └───senturion  
        ├───boots  
        ├───common  
        ├───face  
        └───gloves  

The folder name of the refs export must start with "refs" so the compiler will
recognize it as a refs export. It must have a Players folder, which contains the
refs as "player folders", each of which is named after the ref's name and may
contain "boots", "common", "face" and "gloves" folders as needed.  
This allows each ref folder to be modular and independent of the others.

The Refs.txt file must list the refs in the format "[slot number] [ref name]".  
For example: 01 primal 02 primal 03 senturion 04 senturion 05 senturion  
Remember that there are always 35 slots, though some of them may not be used.  
PES 17 and latter seem not to use slots 11-15 nor 26-30 at all.

Once the compiler recognizes a refs export, it first processes it to convert it
into a regular team export, by reading the Refs.txt file and copying and
splitting the referee folders across the Faces, Boots and Gloves folders.  
Then, it compiles the resulting team export in the same way as any other, with
the exception that it is extracted to the "extracted_refs" folder instead of
"extracted_teams", then moved to a "Refscpk" folder (in the "patches_contents"
folder), instead of "Singlecpk" or "Facescpk", and finally packed into a cpk
file with the name listed for the Refs Cpk Name setting in the settings file.


## Scripts

### 1_exports_to_extracted

This script extracts the exports located in the "exports_to_add" folder into the
"extracted_teams" (and "extracted_refs" if there are refs) folder, then checks
them for typical issues, discarding the whole export or parts of it if it finds
any.  
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

Having a Note txt file used to be compulsory but it isn't anymore. It's still
recommended to have.
If there's no Note txt, the compiler will try to use the first word on the
export's folder name as team name to use when looking for the team ID, which can
be useful for packing midcup stuff more quickly without having to add a Note
txt every time.
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
correctness and/or prepare the "extracted" folders for the next step.


### 2_extracted_to_contents

This script makes a cpk/fpk for each of the folders in the "Faces" folder inside
the "extracted" folders and stores it in the "Singlecpk" or "Facescpk" folder
(or "Refscpk" if there are refs) inside the "patches_contents" folder.

It also moves the content from the other "Kits", "Boots", "Gloves", "Collars",
"Logo", "Portraits" and "Common" folders to the proper folders in the
"Singlecpk", "Facescpk" or "Uniformcpk" (or "Refscpk") folder inside the
"patches_contents" folder.  

If the PES Version is 18 or later, the contents of the "Common" folder will be
moved to  
  model/character/uniform/common/---/ (where --- is the team name),  
otherwise they will be moved to  
  Assets/model/character/common/XXX/sourceimages/#windx11 (where XXX is the
  team ID).

Also, if "Bins Update" is enabled, the team color and kit color entries from the
txt files are added to the "UniColor" and "TeamColor" bin files in other_stuff,
plus (if PES>=18) the kit configs are copied to the "UniformParameter"
bin file. Then the bins are copied to the "Singlecpk" or "Binscpk" folder.

When compiling team exports, the choice of using a "Singlecpk" folder or
multiple folders depends on whether the Multi Cpk mode is enabled. This mode
is recommended when making cup DLC, as it replaces the faces and uniform cpks
from the previous cup, avoiding conflicts. Even the beta DLC for ATFing should
be made with Multi Cpk mode enabled.

Use this script on its own when you want to prepare the "patches_contents"
folder with multiple exports in different moments before packing the final
cpk(s).


### 3_contents_to_patches

This script takes the contents from the folders in the "patches_contents"
folder and packs them into cpks in the "patches_output" folder, whose names
are set in the settings file.

Then, if Move Cpks is enabled, it will move the cpks to your PES "download"
folder.

Use this script on its own after you've finished preparing the content from the
exports with the "extracted_to_content" script to make the final patch.
Running it on its own is also useful after you've manually added some files to
the folders in the "patches_contents" folder.

Warning: Unless the Cache Clearing setting (enabled by default) is disabled,
this script will delete the "patches_contents" folder after it's run, to prevent
old stuff from accidentally getting into the cpks.


### 0_all_in_one

This script simply runs the three main scripts one after the other, with a few
additions like asking for admin permissions (if needed) at the start of the
first script instead of waiting till the end, so that you can leave your pc
unattended right from the beginning.

It's the best choice if you just have a few clean exports and want to compile
them quickly into a cpk.


## Message Types

Here is a more detailed list of the types of message the compiler can output,
from least to most important:

### Info

These are just suggestions, they let you know about stuff which will always
work but isn't ideal, and which you can look into to improve your aesthetics.

[Not shown on screen] [Written to suggestions.log]

List:
- Texture file without mipmaps (dds)
- Non-recommended MTL state values for alphablend/zwrite

### Warning

These warn about stuff which usually works fine as it is, but in some cases
might break things. You can ignore them, but if something is broken on PES you
should come back and look into them.

[Not shown on screen] [Written to issues.log]

List:
- Nested folders detected in export; auto-fix attempted
- Missing kit configs or Note txt kit color entries mismatch
- Texture with irregular dimensions (non-portrait)
- Texture file without mipmaps (ftex)
- Texture listed in XML does not exist
- Missing MTL state names
- No texture paths with IDs found in .fmdl
- Converting texture failed (2.04 or BC7)
- No face folder found for referee

### Error

Something in an export is broken in such a way that it can't be used, so it
will be discarded. Fix it and compile the export again.  
In some cases you might get errors for stuff which sometimes does work as it
is, but they're still a risk to keep. Fix them anyway.

[-Shown on screen-] [Written to issues.log]

List:
- Missing path to listed file in XML
- Invalid Common folder path (missing three-character subfolder)
- Model file loaded from Common on PES16
- Listed file does not exist (non-Texture types)
- Invalid XML file (parse error)
- Invalid root tag in config XML
- Missing model type in config XML
- Invalid MTL file (parse error)
- Material listed more than once
- Invalid MTL state value
- Portrait DDS with invalid dimensions or too small
- Main Kit Texture invalid dimensions or too large
- Main Kit Texture in uncompressed format
- Texture is not a real DDS/FTEX file
- FTEX on pre-Fox PES versions
- No usable files found in team export
- Duplicate Note file found
- Unusable team name (not in teams list)
- Team ID out of range
- Disallowed files in model folders
- Bad face folders (number/repeated/unsupported XML/bad textures/broken MTL)
- Wrong kit config names (or duplicates)
- Bad kit textures (name/invalid texture)
- Wrong logo filenames
- Bad portrait (name/id/format)
- Bad common textures (invalid texture)
- Boots folders invalid (name/repeated/bad textures/broken MTL)
- No team ID found during bins update
- Referee template folder not found
- Refs.txt not found in referee export
- No valid entries found in Refs.txt
- Referee folder listed in Refs.txt not found in Players folder

### Fatal Error

Something is missing in the compiler's folder (for example the teams list) or
is badly configured, so the compiler can't run.  
This does not count as a crash, it is still something the user (You) can fix.  
Just carefully follow the instructions on screen.

[-Shown on screen-] [Written to issues.log]

List:
- Missing settings file
- Missing required settings in settings file
- Invalid PES version selected
- PES download folder not found
- DpFileList not found in PES download folder
- CPK name not listed on DpFileList
- "patches_contents" folder not found
- No folders found in "patches_contents"
- Error removing old cpk (permissions)
- No "extracted" input folder found
- Error compiling UniformParameter
- Missing vital file in clean package
- compiler_run.bat not found in Engines (from the 0123_py bat scripts)
- compiler_main.exe not found in Engines (from the 0123 bat scripts)
- python_check.bat not found in Engines (from compiler_run_py.bat)
- compiler_main.py not found in Engines (from compiler_run_py.bat)
- Python not installed (from python_check.bat)
- Python installed but wrong version (from python_check.bat)

### Crash

The compiler ran into an unexpected error and simply crashed (also known as
unhandled exception). This is something that can only be fixed by the
developer, so please report it by posting the crash.log file from the folder.

[-Shown on screen-] [Written to crash.log]

List:
- Any unhandled exception during runtime (unexpected error in any script)
- We just don't know [🐦?]
