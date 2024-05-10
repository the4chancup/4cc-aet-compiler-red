# 4cc AET Compiler Red
A "4chan Cup Aesthetic Export" compiler for the Pro Evolution Soccer series.
New python-based version, three times faster.

- Setting up
- Compiling exports
- Message types
- Troubleshooting


## Setting up

IMPORTANT: Make sure you have python 3.12 or higher installed on your pc.
You can download it from this link.
https://www.python.org/downloads/
Make sure to enable the "Add to PATH" setting during the installation.

Now open the settings txt file and set the following:
- PES Version:
  Set the PES version you're compiling exports for.
- Download Folder Path:
  Check if it's good.

You don't normally have to edit any of the other settings, but feel free to
take a look. The "Run PES" setting, in particular, opens PES automatically after
packing a cpk.


## Compiling exports

First of all, you need to make sure that the team name of the export you're
compiling is listed on the teams_list.txt file of the compiler, next to the
team ID assigned to it. If it's not in there, then write it in.

Also make sure your export follows the proper AET format as described on the
following wikipage:
https://implyingrigged.info/wiki/AET
Keep in mind that you don't need to edit the team ID listed in your export's
files, the compiler will take care of that!

Now put the export in the exports_to_add folder (folders, zip or 7z are all
fine) and run the 0_all_in_one script.

A cpk will be created and copied automatically to your PES download folder.
Now you only need to run PES and check your stuff.

Check the Troubleshooting section at the bottom if you run into trouble.
It the compiler throws a message at you and you don't know why, read below.


## Message types

Here are the types of message the compiler can output, from least to more
important:

- Info

  These are just suggestions, they let you know about stuff which will always
  work but isn't ideal, and which you can look into to improve your aesthetics.

  [Not shown on screen] [Written to suggestions.log]

- Warning

  These warn about stuff which usually works fine as it is, but in some cases
  might break things. You can ignore them, but if something is broken on PES you
  should come back and look into them.

  [Not shown on screen] [Written to issues.log]

- Error

  Something in an export is broken in such a way that it can't be used, so it
  will be discarded. Fix it and compile the export again.
  In some cases you might get errors for stuff which sometimes does work as it
  is, but they're still a risk to keep. Fix them anyway.

  [-Shown on screen-] [Written to issues.log]

- Fatal Error

  A file from the compiler's folder is missing (for example the teams list), so
  the compiler can't run. This does not count as a crash, it is still something
  the user can fix, either by grabbing a new compiler folder or by letting it
  fix itself (the compiler will offer to "self-heal" when possible).

  [-Shown on screen-] [Written to issues.log]

- Crash

  The compiler ran into an unexpected error and simply crashed (also known as
  unhandled exception). This is something that can only be fixed by the
  developer, so please report it by posting the crash.log file from the folder.

  [-Shown on screen-] [Written to crash.log]


## Troubleshooting

Q: Why is the script crashing?

  A: There could be many reasons. Please post the log file you can find in the
  compiler's folder to the /4ccg/ thread or the /aesco/ discord.

Q: Why wasn't the cpk created at all? It's not in the /downloads folder.

  A: You probably have PES installed in a system folder not listed in the
  admin_check file. Enable Force admin mode in the settings file and try again.
  If that still doesn't help, disable Move Cpks and copy it yourself from the
  patches_output folder.

Q: I've got some other problem/question.

  A: Feel free to contact the developer, preferably on the thread or the /aesco/
  discord, so that if someone else is having the same problem they can also have
  it solved.



Tool by Shakes

Special thanks for ideas and fixes, and for some of the libraries used:
Tomato4cc, Giovani1906, fg4cc, blu_ray_
