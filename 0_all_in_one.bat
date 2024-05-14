@echo off
REM ^ Don't write everything to screen

REM - Set the working folder
cd /D "%~dp0"


REM - Set the running type from the bat file's name
set running_type=%~n0

REM - Call the runner
if exist ".\Engines\compiler_run.bat" (
    .\Engines\compiler_run.bat %running_type%
) else (
    echo -
    echo - FATAL ERROR - Missing vital file
    echo - The file compiler_run.bat was not found in the Engines folder
    echo -
    echo - Please grab a clean compiler folder
    echo -
    pause
)
