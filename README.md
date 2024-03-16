# 4cc AET Compiler Red
An aesthetics export compiler for the Pro Evolution Soccer series.
New python-based version, three times faster.

- Setting up
- Simple stuff
- Advanced stuff
- About the export format
- Troubleshooting


## Setting up

IMPORTANT: Make sure you have python 3.12 or higher installed on your pc.
You can download it from this link:
https://www.python.org/downloads/

Now open the settings txt file and set the following:
- PES Version: Set the PES version you're compiling exports for.
- Download Folder Path: Check if it's good.
You don't normally have to edit any of the other settings, but feel free to
take a look.


## Simple stuff

Read this if you're just packing /yourteam/'s export to test it on PES.

First of all, you need to make sure that the team name of the export you're
compiling is listed on the teams_list.txt file of the compiler, next to the
Team ID assigned to it. If it's not in there, then write it in.

Also make sure your export follows the proper AET format as described on the
following wikipage. Keep in mind that you don't need to edit the IDs in your
export, the compiler will take care of that!
https://implyingrigged.info/wiki/AET

Now put the export in the exports_to_add folder (folders, zip or 7z are all
fine) and run the 0_all_in_one script.

A cpk will be created and copied automatically to your PES download folder, if
you installed PES to the default location. Otherwise, the settings file will be
opened so you can set the correct folder path.

After you've run the compiler you only need to open PES and check your stuff.

Check the Troubleshooting section at the bottom if you run into trouble.


## Advanced stuff

Read this if you're making DLC for a cup or want to use the compiler to its
full potential.

Make sure to read the settings file for further customization options.
Keep in mind that "fox mode" is enabled when PES Version is 18 or higher.
A thorough description of the four main scripts follows.

### 1_exports_to_extracted

This script extracts the exports located in the exports_to_add folder into the
extracted_exports folder, then checks them for typical issues, discarding the
whole export or parts of it if it finds any.
It also makes a log file named memelist.txt with the list of problems it found,
and pauses at every error unless the pause_when_wrong setting has been disabled
in the settings file.

Here's a list of the stuff that the script checks after extracting an export,
before moving its content into folders shared by all the teams:
- Checks that the team name is in the teams_list file (if there's none, it uses
  the first word on the export's folder name as team name), and looks for the
  team name on the teams_list txt, to find the corresponding team ID.
- Checks for nested folders with repeated names (e.g. GD export/Faces/Faces),
  excluding the Other or Common folder, and tries to fix them by moving the
  folders down by one layer.
- Checks that the 4th and 5th characters of each face folder is in the 01-23
  range for player numbers.
- Checks that the face folders have the essential face.xml file inside, and
  that none has the unsupported face_edithair.xml inside.
  In fox mode, it checks for the presence of the face.fpk.xml file instead.
- Checks that the Faces folder doesn't have any extra non-folder files
  (like cpks) in it.
- Checks that the kit config files and the kit texture files follow the proper
  naming convention as described on the Kits wikipage.
- Check that the amount of kit config files is consistent with what's listed on
  the team txt.
- Checks that all of the dds files for face textures, kit textures and
  portraits are proper dds files to avoid stuff like renamed pngs.
- Checks that the png files in the Logo folder are three and are
  properly named.
- Checks that the dds files in the Portraits folder are properly named.
- Checks that the boots folder names in the Boots folder start with a "k".
- Checks that the gloves folder names in the Gloves folder start with a "g".

Having a Note txt file used to be compulsory but it isn't anymore. It's stil
recommended to have. If there's no txt, the compiler will try to use the first
word on the export's folder as team name to use when looking for the team ID,
which can be useful for packing midcup stuff more quickly without having to add
a Note txt every time.
The Note txt is needed when adding new kits and/or changing their menu colors.

After the checks are done, the script sorts the export's content into folders
which hold the contents of all the processed exports, while at the same time
replacing the team ID on every file and folder (even inside the kit configs)
with the proper team ID.

This means that the ID in the exports' files can be literally anything three
characters long, for example an old team ID, the current one or simply XXX
(recommended), since the compiler will ignore it and replace it with the proper
team ID it finds by looking for the team name on the teams_list file.
Thanks to this, you can use old exports from previous invitationals without
renaming anything manually.

It also copies the contents from all of the Note files into a single file
called teamnotes.txt, allowing you to read them all quickly without having
to open multiple files.

Use this script on its own if you only want to check the exports for
correctness and/or prepare the extracted_exports folder for the next step.


### 2_extracted_to_contents

This script makes a cpk/fpk for each of the folders in the Faces folder inside
the extracted_exports folder and stores it in the Singlecpk or Facescpk folder
inside the patches_contents folder.

It also moves the content from the other Kits, Boots, Gloves, Collars, Logo,
Portraits and Common folders to the proper folders in the Singlecpk, Facescpk
or Uniformcpk folder inside the patches_contents folder.
If fox mode is disabled, the contents of the Common folder will be moved to
  model/character/uniform/common/---/ (where --- is the team name),
otherwise they will be moved to 
  Assets/model/character/common/XXX/sourceimages/#windx11 (where XXX is the
  team ID).

Also, if Bins Update is enabled, the team color and kit color entries from the
txt files are added to the UniColor and TeamColor bin files in other_stuff, plus
(if fox mode is on) the kit configs are copied to the UniformParameter bin file.
Then the bins are copied to the Singlecpk or Binscpk folder.

The choice of using a Singlecpk folder or multiple folders depends on whether
the Multi cpk mode is enabled. This mode is recommended only when making cup DLC
for general release, after testing that everything is fine and nothing needs
fixing. The beta DLC for ATFing should be made with singlecpk mode set.

Use this script on its own when you want to prepare the patches_contents folder
with multiple exports in different moments before packing the final cpk(s).


### 3_contents_to_patches

This script takes the contents from the folder(s) in the patches_contents folder
and packs them into a cpk(s) in the patches_output folder, whose name(s) can be
set in the settings file.

Then, depending on the settings you've set, it'll move the cpk(s) to your PES
download folder.

Use this script on its own after you've finished preparing the content from the
exports with the extracted_to_content script to make the final patch.
Running it on its own is also useful after you've manually added some files to
the folder(s) in the patched_contents folder.


### 0_all_in_one

This script simply runs the three main scripts one after the other, with a few
changes like asking for admin permissions (if needed) at the start of the first
script instead of waiting till the end, so that you can leave your pc unattended
right from the beginning.

It's the best choice if you just have a few clean exports and want to compile
them quickly into a cpk.


### Extra info

You can rerun the script to compile the exports located in the exports_to_add
folder again, updating the cpks and the content stored in the patches_contents
folder.
If you don't need to update the content for some of the exports, for example
because they haven't changed, you can remove them from the exports_to_add folder
and the script will use the content stored previously instead of unnecessarily
recompiling every face. This way you can save time by only putting exports in
the exports_to_add folder when they need to be updated.


## About the export format

### The contents need to follow these names:

| Name                          | Notes |
| :---                          | :--- |
| ___ Note.txt                  | (recommended) |
| Faces                         | (recommended) |
| Faces\XXXxx - Player names    | (names required, no symbols allowed) |
| Kit Configs                   | (required) |
| Kit Textures                  | (required) |
| Logo                          | (required unless the team is a 4cc team, in which case it's recommended) |
| Portraits                     | (optional, putting them in the player face folders instead is recommended) |
| Boots                         | (optional) |
| Boots\k++++ - Player names    | (names recommended, no symbols allowed) |
| Gloves                        | (optional) |
| Gloves\g++++ - Player names   | (names recommended, no symbols allowed) |
| Collars                       | (optional) |
| Common                        | (optional) |
| Other                         | (optional) |

___ is your team's name
xx are the player numbers in the 01-23 range
XXX can be 'anything', as long as it's three characters long (new team ID, old
    team ID, literally XXX, any is fine)
++++ is a four digit ID in the 0000-9999 range, though you should check the
     Boots wikipage for the slots your team can use (Gloves use the same slots)


### The Note file should have these lines:
```
Team: /___/

Kit Colours:
- 1st player: #RRGGBB - #RRGGBB
- 2nd player: #RRGGBB - #RRGGBB
...

- 1st GK: #RRGGBB - #RRGGBB
```

___ is your team's name
#RRGGBB is the color used for the menu previews in hex format (you can also use
the classic RRR GGG BBB format).
If don't know what to write just use #000000 everywhere, the only important
thing is that you have as many kit lines as the amount of kits your team has.


## Troubleshooting

Q: Why is the script crashing?

A: Make sure that the folder you extracted the script to doesn't have a (1) or
similar in its name. That's the only thing that testing has found out which
could make the script crash, but if you get into trouble for any other reason
don't hesitate to ask for help on the /4ccg/ thread.


Q: Why wasn't the cpk created at all? It's not in the /downloads folder.

A: You probably have PES installed in a system folder not listed in the
admin_check file. Enable Force admin mode in the settings file and try again.


Q: Why is it telling me that some of the face folders are bad? They look fine.

A: Make sure that the folder names don't have any symbols or special characters
and try again.


Q: I've got some other problem/question.

A: Feel free to contact me, preferably on the thread or the /aesco/ discord so
that if someone else has the same problem they can also have it solved.



Tool by Shakes

Special thanks to Tomato, gio and Foreground for ideas and for the python
libraries used by this compiler
