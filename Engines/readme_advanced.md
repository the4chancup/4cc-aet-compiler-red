# 4cc AET Compiler Red
Read this advanced readme if you're making DLC for a cup or want to use the
compiler to its full potential.

Make sure to also read the settings file for further customization options.

- Compiling Referees
  - ref_marker File
  - refs.txt Template
- First Run Wizard
- Scripts
  - 1_exports_to_extracted
  - 2_extracted_to_contents
  - 3_contents_to_patches
  - 0_all_in_one
- XML-less Face Folders
  - Common Folder Links
- Texture Handling
- Dummy Kit Replacement
- Special Files and Folders
  - NO_USE File
  - Sideload Folder
  - Other Folder
- Message Types
- Log Username Cleaning
- Automatic Updates
- Dependency Self-Healing


## Compiling Referees
You first need a "refs export", which follows the next-generation format that
will be introduced in the future for team exports.
Here's an example:

refs  
│   refs.txt  
│   ref_marker.dds (optional)  
│  
└───Players  
    ├───coolguy  
    │   ├───boots  
    │   ├───common  
    │   ├───face  
    │   └───gloves  
    └───robocop  
        ├───boots  
        ├───common  
        ├───face  
        └───gloves  

The folder name of the refs export must start with "refs" so the compiler will
recognize it as a refs export. It must have a Players folder, which contains the
refs as "player folders", each of which is named after the ref's name and may
contain "boots", "common", "face" and "gloves" folders as needed.  
This allows each ref folder to be modular and independent of the others.

The refs.txt file must list the refs in the format "[slot number] [ref name]".  
See the next paragraph for an example.

Once the compiler recognizes a refs export, it first preprocesses each referee
folder by automatically moving textures and models to common subfolders named
after the referee. This means that when the same referee is assigned to multiple
slots, the textures and models are shared between them instead of being
duplicated, keeping the cpk size down.

After preprocessing, the compiler reads the refs.txt file and copies and splits
the referee folders across the Faces, Boots, Gloves and Common folders.  
Then, it compiles the resulting team export in the same way as any other, with
the exception that it is extracted to the "extracted_refs" folder instead of
"extracted_teams", then moved to a "Refscpk" folder (in the "patches_contents"
folder), instead of "Singlecpk" or "Facescpk", and finally packed into a cpk
file with the name listed for the Refs Cpk Name setting in the settings file.

### refs.txt Template

A template refs.txt file is included in the "Engines/templates" folder. It lists
all 35 referee slots with example referee names, and can be used as a starting
point when creating a new referee export.

Copy it into your referee export folder, then edit it to match your referee
assignments. The format is "[slot number] [ref name]", one per line, for
example:  
1 coolguy  
2 robocop  
3 coolguy  

Remember that there are always 35 slots, though some of them may not be used.  
PES 17 and latter seem not to use slots 11-15 nor 26-30 at all.  
You can assign the same referee to multiple slots.

### ref_marker File

When compiling a referee export, you can include a file called "ref_marker.dds"
in the root of the export folder (next to the refs.txt and Players folder).
This is the marker texture that appears in-game on the ground, below the
referees' feet (the cup logo, or a simplified version of it, is usually used).

How it's handled depends on the PES version:

- **Pre-Fox (PES 15-17):** The marker texture is moved directly into the refs
  CPK template folder, overwriting the existing marker texture. It will be
  included in the refs CPK when it's packed.

- **Fox (PES 18+):** The marker texture needs to be written into the dt00_x64
  system CPK inside PES's Data folder. The compiler will ask for your
  confirmation before overwriting this system file (only on the first time).
  Move Cpks mode must be enabled for this to work. If Move Cpks is disabled,
  the marker file will be skipped with a Notice.
  If you share the refs CPK, you'll need to share the dt00_x64 CPK as well.

If you don't need to update the marker texture, it's better to avoid including
the ref_marker.dds file in the export folder.


## First Run Wizard

The first time you run the compiler, a first run wizard will guide you through
the initial setup. It will:

1. Ask you to confirm or change the PES version.
2. Show you the current PES folder path and check if it exists.
3. If the path doesn't exist and Move Cpks is enabled, it will ask you to set
   the correct path in the settings file.

The wizard creates a state file ("Engines/state/first_run_done.txt") so it
won't run again on subsequent launches. If you want to re-trigger it (e.g.
after a fresh setup), delete that file.


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

If the PES Version is 17 or earlier, the contents of the "Common" folder will be
moved to  
  common/character1/model/character/uniform/common/XXX/ (where XXX is the team
  ID),  
otherwise they will be moved to  
  Asset/model/character/common/XXX/sourceimages/#windx11 (where XXX is the
  team ID).

For referee exports, the Common folder contains subfolders named after each
referee. These subfolders are preserved in the output, so that repeated
referees across multiple slots share the same textures and models.

Also, if "Bins Updating" is enabled, the team color and kit color entries from
the txt files are added to the "UniColor" and "TeamColor" bin files, plus
(if PES>=18) the kit configs are added to the "UniformParameter" bin file.
Then the bins are copied to the "Singlecpk" or "Binscpk" folder.

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


## XML-less Face Folders

On Pre-Fox versions of PES (PES 15-17), face folders normally require a face.xml
configuration file that lists the models and materials used by the face.
However, the compiler can handle face folders that don't have an xml file at
all, by automatically generating one.

When the compiler encounters a face folder without a face.xml file, it will:

1. Scan the folder (and any subfolders) for all .model files.
2. Determine the type of each model from its filename.
  The compiler can recognize the following types from the beginning of the
  filename:
    - face_neck
    - handL
    - handR
    - gloveL
    - gloveR
    - uniform
    - shirt
    - pants_nocloth
    - eye
    - mouth
3. If the type is not in the previous list, look in the model name for
   "model_type_" followed by any type name. If found, that type will be used.
   Failing both checks, the model will be assigned the default "parts" type.
4. Find a matching .mtl material file for each model. It first looks for an mtl
   file whose name matches the model's name, then for a "materials.mtl" file,
   then for any .mtl file in the same directory or the parent face folder.
5. If no face_neck model is found, a dummy face_neck model will be automatically
   added to ensure the player rotates properly in Edit mode.
6. If a face_diff.bin or face_diff.xml file is present, its data will be
   included in the generated xml as the diff block.
7. Model files that don't follow the "oral_{name}_win32.model" naming convention
   will be automatically renamed to match it.

The same xml auto-generation also works for glove folders. If a glove folder
doesn't have a glove.xml file, the compiler will generate one by looking for
left and right glove model files (glove_l.model and glove_r.model exactly).

Additionally, the compiler supports a "ratio_" keyword in model filenames. If a
model file's name contains "ratio_" followed by a number (e.g.
"tv_ratio_1.806.model"), the ratio value will be added as an attribute in the
generated xml. This is required for models using the "DigitalSignage" shader.

This feature is only relevant for pre-Fox PES versions (15-17), since Fox
versions (18+) use fmdl files and fpk packing instead of xml configuration and
are XML-less by design.

Note: Boots folders on Pre-Fox versions don't use xml files, but the compiler
still checks that their .model files have allowed names (boots.model,
boots_edit.model). Model files with other names will cause an error.

### Common Folder Links

On Pre-Fox PES versions (except 16), models can be loaded from the team's Common
folder instead of the face folder. To indicate that a model should be loaded
from Common, you can place a "link" file in the face folder instead of the
actual model file.

A link file is an empty file with the model's name plus a ".common" or
".common.txt" extension. For example, if you want to load "shirt.model"
from Common, place a file called "shirt.model.common" (or
"shirt.model.common.txt") in the face folder.

When the compiler encounters a link file during xml generation, it will:
- Use the Common folder path in the xml instead of the local "./" path.
- Look for the corresponding .mtl file in the Common folder as well.
- Delete the link files after the xml has been generated.

This allows face folders to reference shared models and materials without
duplicating them, keeping the export size smaller.


## Texture Handling

The compiler performs several automatic texture conversions depending on the
target PES version:

### DDS to FTEX (Fox versions, PES 18+)
All .dds textures in face, boots, gloves, common and kit texture folders are
automatically converted to .ftex format when compiling for Fox PES versions.

### DX10 to DXT5
If the version of PES is 18 or earlier, DDS textures using the DX10 format
(BC7 compression) are automatically converted to DXT5 format for compatibility.
On Windows this uses the DirectXTex texconv tool (included in the compiler),
on Linux it uses ImageMagick, which must be installed manually.

### FTEX version check (PES 18 only)
When compiling for PES 18, ftex files with version 2.04 are reconverted through
DDS to ensure compatibility. A warning is logged if the conversion fails.

### DDS zlib compression (PES 17 and earlier)
If the DDS Compression setting is enabled, all DDS textures will be zlib
compressed after processing. This is mainly useful when making cup DLC for
Pre-Fox versions.

### Kit mask textures (Pre-Fox)
On Pre-Fox versions, if a kit texture (e.g. u0XXXp1.dds) doesn't have a
corresponding "_mask" texture, the compiler will automatically copy a default
kit mask from the templates folder.

### Portraits
Portrait textures are always kept in DDS format regardless of the PES version,
since PES expects portraits as DDS files even on Fox versions.


## Dummy Kit Replacement

On Fox PES versions (18+), if a team has a Common folder with "dummy_kit"
textures (dummy_kit.ftex, dummy_kit_back.ftex, etc.), the compiler will
automatically replace them with the team's actual kit 1 textures after
processing the export.

This means you don't have to manually update the dummy textures in the Common
folder every time you change the team's first kit. The compiler handles it
automatically by copying the kit 1 textures (u0XXXp1.ftex, etc.) over the
dummy files.

If the team doesn't have a corresponding kit 1 texture for a dummy file, a
message will be printed and that particular dummy texture will be left as-is.


## Special Files and Folders

### NO_USE File

If you want to temporarily exclude an export from compilation without removing
it from the "exports_to_add" folder, you can place a file called "NO_USE" (or
"NO_USE.txt") inside the export's folder.

When the compiler finds a NO_USE file inside an export folder, it will skip that
export entirely and print a message saying it was skipped. This only works for
folder exports, not for zip or 7z archives.


### Sideload Folder

The "sideload" folder allows you to inject arbitrary files directly into the
output cpk without going through the normal export pipeline. Any files and
folders placed inside the "sideload" folder will be copied as-is into the
Singlecpk folder during the contents preparation step, overwriting any
conflicting files from the exports.

Key points:
- The sideload folder has **higher priority** than the exports folder: if both
  contain a file at the same path, the sideload version wins.
- No checks or modifications are performed on sideloaded files, so make sure
  you know what you're putting in there.
- The sideload folder will be used in **every compilation** until you remove it.
- The sideload folder is **not used** when Multi Cpk mode is enabled.
- The first time the compiler detects a sideload folder, it will show a Notice
  explaining the above. This notice will not be shown again afterwards.

This is useful when you need to include files that don't fit the standard AET
export format, such as custom stadium files, audio files, or any other content
that needs to go into the cpk.


### Other Folder

If an export contains folders that don't match any of the known folder names
(Faces, Kit Configs, Kit Textures, Logo, Portraits, Boots, Gloves, Collars,
Common), those folders will be moved to an "Other" folder in the extracted
directory, inside a subfolder named after the team ID and name.

After all exports have been processed, if there are any files in the Other
folder, the compiler will show a Notice asking you to check its contents. This
allows you to manually handle any non-standard files that were included in the
exports.


## Message Types

Here is a more detailed list of the types of message the compiler can output,
from least to most important:

### Info

These are just suggestions, they let you know about stuff which will always
work but isn't ideal, and which you can look into to improve your aesthetics.

[Not shown on screen] [Written to suggestions.log]

List:
- Texture file without mipmaps (dds)
- Missing MTL state names
- Non-recommended MTL state values for alphablend/zwrite
- Disallowed files found in model folders or common folder
  (when Strict File Type Check is disabled)

### Notice

These are informational messages that pause the program to make sure you see
them, but are **not logged** to any file. They are used for situations that
require your attention or acknowledgment but aren't errors or warnings about
the exports themselves.

[-Shown on screen-] [Not written to any log]

List:
- Update available (major, minor, or bugfix)
- PES version mismatch (exe found doesn't match settings)
- Sideload folder present (first time only)
- CPK name not listed on the DpFileList (when Move Cpks is disabled)
- Referee marker texture present but Move Cpks is disabled
- Referee marker texture present on a Fox PES version (dt00 overwrite notice)
- Files found in the Other folder after processing

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
- Non-recommended MTL state value for blendmode (should be 0)
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
- Failed to extract compressed export
- Missing path to listed file in XML
- Invalid Common folder path (missing three-character subfolder)
- Model file loaded from Common on PES16
- Custom model file name does not start with "oral_" on PES16
- Listed file does not exist (non-Texture types)
- Invalid XML file (parse error)
- Invalid root tag in config XML
- Missing model type in config XML
- Missing texture path in MTL
- Invalid MTL file (parse error)
- Material listed more than once
- Invalid MTL state values
  (ztest must be 1, blendmode must be 0 or 1, alphablend must be 0 or 1)
- Texture file with invalid dimensions (too small, less than 4x4)
- Portrait DDS with invalid dimensions (not powers of 2)
- Regular texture with invalid dimensions
  (not power of 2 on at least one side, Fox only)
- Regular texture with invalid dimensions (not divisible by 4, pre-Fox only)
- Main Kit Texture invalid dimensions
  (larger than 2048 or not powers of 2, pre-Fox only)
- Main Kit Texture in uncompressed format
- Unsupported uncompressed texture format
- Unsupported texture codec
- Texture is not a real DDS/FTEX file
- Conflicting portraits (in both face folder and Portraits folder)
- No usable files found in team export
- Duplicate Note file found
- Unusable team name (not in teams list)
- Team ID out of range
- Disallowed files found in model folders or common folder
  (unless Strict File Type Check is disabled)
- Bad face folders (number/repeated/unsupported XML/bad textures/broken MTL)
- Wrong kit config names (or duplicates)
- Bad kit textures (name/invalid texture)
- Wrong logo filenames
- Bad portrait (name/id/format)
- Bad common textures (invalid texture)
- Boots folders invalid (name/repeated/invalid texture/broken MTL)
- Gloves folders invalid (name/repeated/invalid texture/broken MTL)
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
- CPK name not listed on DpFileList (when Move Cpks is enabled)
- "patches_contents" folder not found
- No folders found in "patches_contents"
- Error removing old cpk (permissions)
- No "extracted" input folder found
- Error compiling UniformParameter
- Missing vital file in clean package
- compiler_run.bat not found in Engines (from the 0123_py bat scripts)
- python.exe not found in Engines\embed (from the 0123 bat scripts)
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


## Log Username Cleaning

When sharing log files (issues.log, crash.log) with others for troubleshooting,
your Windows username may appear in file paths inside the logs. The compiler
includes a log cleaner that replaces your username with a placeholder before you
share the files.

You can run it by passing the "-1" argument to compiler_main.py. On the Windows
release, this is done automatically by the bat scripts after the compiler
finishes. The username is replaced with "<username>" (or a truncated version if
your username is short) in both issues.log and crash.log.


## Automatic Updates

The compiler checks for updates automatically on startup (if the Updates
Checking setting has not been disabled). It queries the GitHub repository for
the latest release and compares it against the current version.

To avoid slowing down every run, the compiler only checks once per hour. The
time of the last check is stored in the "Engines/state" folder.

If an update is available, a Notice will be shown with the following options:
- **up** - Downloads the new version automatically, transfers your settings and
  teams list, moves your exports over, and opens the new folder.
- **info** - Opens the GitHub releases page in your browser so you can read the
  changelog and decide whether to update manually.
- **skip** - Skips this specific version and won't warn again until a newer one
  comes out.
- **fuckoff** - Disables update checking entirely (not recommended).
- **Enter** - Continues normally without updating.

During a major update, the settings file may be overhauled. The compiler will
transfer your settings to the new format automatically, and will show you which
settings were added, removed, or renamed. If the teams list has changed, a
side-by-side diff will be shown so you can choose whether to keep your current
list or use the new one.

The old compiler folder is always preserved after an update, so you can go back
to it if you find any issues with the new version.


## Dependency Self-Healing

When running the compiler from source (not from a compiled release), the
compiler can automatically detect and install missing Python dependencies.

On startup, it checks if all required packages are installed and at the correct
version. If any are missing, it will:
1. List the missing dependencies.
2. Offer to install them automatically via pip.
3. Close the program after installation so you can restart it cleanly.

On Linux, it also checks for ImageMagick (used for texture conversion) and
warns if it's not found.

Additionally, if a library file from the compiler's own codebase is missing,
the compiler will attempt to recover it automatically before giving up with a
fatal error. This "self-healing" mechanism helps keep the compiler running even
if individual files get accidentally deleted.
