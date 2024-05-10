@echo off
REM ^ Don't write everything to screen

REM - Set the working folder
cd /D "%~dp0\.."


REM - Check if python is installed and was added to the PATH
if exist "Engines\python_check" (
    call .\Engines\python_check
) else (
    echo -
    echo - FATAL ERROR - Missing vital file
    echo - The file python_check.bat was not found in the Engines folder
    echo -
    echo - Please grab a clean compiler folder
    echo -
    pause
)

REM - Set the running type from the first argument this script was called with
set running_type=%1

REM - Grab the number from the first character from the running type
set running_type_num=%running_type:~0,1%

REM - Invoke the main compiler script
if exist "Engines\compiler_main.py" (
    call py -3 .\Engines\compiler_main.py %running_type_num%
) else (
    echo -
    echo - FATAL ERROR - Missing vital file
    echo - The file compiler_main.py was not found in the Engines folder
    echo -
    echo - Please grab a clean compiler folder
    echo -
    pause
)



REM - Pause if the compiler returned an error and run the log cleaner
if ERRORLEVEL 1 (
    call py -3 .\Engines\log_username_clean.py

    echo -
    echo -
    echo - CRASH - The compiler has run into an unexpected error
    echo - A log file crash.log has been saved to the compiler's folder
    echo - Please post it on the /aesco/ server or the cup thread
    echo -
    pause
)