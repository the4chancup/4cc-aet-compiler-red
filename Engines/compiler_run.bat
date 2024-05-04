@echo off
REM ^ Don't write everything to screen

REM - Set the working folder
cd /D "%~dp0\.."


REM - Check if python is installed and was added to the PATH
call .\Engines\python_check

REM - Set the running type from the first argument this script was called with
set running_type=%1

REM - Grab the number from the first character from the running type
set running_type_num=%running_type:~0,1%

REM - Invoke the main compiler
call py -3 .\Engines\compiler_main.py %running_type_num%


REM - Pause if the compiler returned an error and run the log cleaner
if ERRORLEVEL 1 (
    call py -3 .\Engines\log_username_clean.py

    echo -
    echo -
    echo - A log file error.log has been saved to the compiler's folder
    echo - Please post it on the /aesco/ server or the cup thread
    echo -
    pause
)