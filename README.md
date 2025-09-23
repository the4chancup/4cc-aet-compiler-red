# 4cc AET Compiler Red
A "4chan Cup Aesthetic Export" compiler for the Pro Evolution Soccer series.  
New python-based version, three times faster.

This is a short readme, with just the information you need to compile your
team's aesthetics so that you can check them on PES.  
You can also find an advanced readme in the Engines folder, with full details on
how the compiler works. Read it if you're going to compile a full DLC for a cup.

- Setting up
- Compiling exports
- Message types
- Troubleshooting


## Setting up

Just open the settings.ini file on notepad and set the following:
- PES Version:  
  Set the PES version you're compiling exports for.
- PES Folder Path:  
  Check if it's good. Keep in mind this is the folder with the PES exe, not the
  download folder.

You don't normally have to edit any of the other settings, but feel free to
take a look. The "Run PES" setting, in particular, opens PES automatically after
packing a cpk.


## Compiling exports

First of all, you need to make sure that the name of the team whose export
you're compiling is listed in the teams_list.txt file of the compiler, next to
the team ID assigned to it. If it's not in there, then write it in.

Also make sure your export follows the proper AET format as described on the
following wikipage:  
https://implyingrigged.info/wiki/AET  
Keep in mind that you don't need to edit the team ID listed in your export's
files and folders, the compiler will take care of that!

Now put the export in the exports_to_add folder (folders, zip or 7z are all
fine, rar files are not) and run the 0_all_in_one script.
If you're using a Linux distro, run compiler_main.py from the Engines folder
instead, keep in mind that you need to have Python 3.12 or 3.13 installed.

A cpk will be created and copied automatically to your PES download folder.  
Now you just need to run PES and check your stuff.

Check the Message types and Troubleshooting sections if you run into trouble.  
Also, don't forget to read the advanced readme inside the Engines folder if you
want to know more about how the compiler works, or if you want to compile a
referees cpk.


## Message types

Here are the types of message the compiler can output, from least to most
important:

Only written to logs:
- Info (suggestions.log)  
  These are just suggestions about stuff which isn't ideal.
- Warning (issues.log)  
  These warn about stuff which -might- break things.

Written to logs and shown on screen:
- Error (issues.log)  
  Something in an export is broken in such a way that it can't be used, so it
  will be discarded. Fix it and compile the export again.
- Fatal Error (issues.log)  
  Something happened and the compiler can't run. This does not count as a crash,
  it is still something you can fix. Just follow the instructions on screen.
- Crash (crash.log)  
  The compiler crashed. This is something that can only be fixed by the
  developer, so please report it by posting the crash.log file from the folder.

You can find a slightly more detailed explanation in the advanced readme.


## Troubleshooting

Q: Why wasn't the cpk created at all? It's not in the downloads folder.  
  A: You probably have PES installed in a system folder not listed in the
  admin_check file. Enable Force Admin Mode in the settings file and try again.
  If that still doesn't help, disable Move Cpks and copy it yourself from the
  patches_output folder.

Q: Why is the script crashing?  
  A: There could be many reasons. If you got a Fatal Error, follow the
  instructions on screen. If you got a Crash, please post the crash.log file
  (which you can find in the compiler's folder) on the divegrass thread or the
  /aesco/ discord.

Q: Why is my antivirus blocking the exe?  
  A: The exe is a compiled version of the script and all the Python libraries
  it needs to run, so it has some tricks which might trigger some antivirus
  programs. If you don't trust it you can run the Python script directly from
  the Engines folder instead. Use compiler_run_py.bat or 0_all_in_one_py.bat if
  you're on Windows or compiler_main.py if you're on Linux.

Q: I've got some other problem/question.  
  A: Feel free to contact the developer, preferably on the divegrass thread or
  the /aesco/ discord, so that if someone else is having the same problem they
  can also have it solved.



Tool by Shakes

Special thanks for ideas and fixes, and for some of the libraries used:  
Tomato4cc, Giovani1906, fg4cc, blu_ray_

Huge thanks to Tim Peters for helping define the design philosophy of Python.
