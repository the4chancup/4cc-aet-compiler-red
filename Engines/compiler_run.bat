@echo off
REM ^ Don't write everything to screen

REM - Allow reading variables modified inside statements
setlocal EnableDelayedExpansion

REM - Check if python is installed and was added to the PATH
call .\Engines\python_check

REM - Load the settings
call .\Engines\settings_init


REM - Set the running type from the first argument this script was called with
set running_type=%1

REM - Grab the first character from the running type
set running_type_first=%running_type:~0,1%

REM - Invoke the main compiler
call py -3 .\Engines\compiler_main.py %running_type_first%


pause