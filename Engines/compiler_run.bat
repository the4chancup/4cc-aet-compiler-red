@echo off
REM ^ Don't write everything to screen

REM - Set the working folder
cd /D "%~dp0\.."


REM - Check if python is installed and was added to the PATH
if exist ".\Engines\python_check.bat" (
    call .\Engines\python_check.bat
    REM - This script sets the version on python_version
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
if exist ".\Engines\compiler_main.py" (
    call py -%python_version% .\Engines\compiler_main.py %running_type_num%
) else (
    echo -
    echo - FATAL ERROR - Missing vital file
    echo - The file compiler_main.py was not found in the Engines folder
    echo -
    echo - Please grab a clean compiler folder
    echo -
    pause
)

set crashed=%ERRORLEVEL%

REM - Run the log cleaner
call py -%python_version% .\Engines\log_username_clean.py


REM - Set the ESC character and colors for text coloring
for /f "delims=" %%E in ('forfiles /p "%~dp0." /m "%~nx0" /c "cmd /c echo(0x1B"') do (
    set "ESC=%%E"
)
if not defined NO_COLOR (
    set "BRIGHT_MAGENTA=%ESC%[95m"
    set "RESET=%ESC%[0m"
) else (
    set "BRIGHT_MAGENTA="
    set "RESET="
)

REM - If the compiler returned an error
if %crashed% GEQ 1 (

    echo -
    echo -
    echo - %BRIGHT_MAGENTA%CRASH%RESET% - The compiler has run into an unexpected error and stopped
    if exist ".\crash.log" (
        echo - A log file crash.log has been saved to the compiler's folder
        echo - Please post it on the /aesco/ server or the cup thread
    ) else (
        echo - Please take a screenshot and post it on the /aesco/ server
        echo - or the cup thread
    )
    echo -

    REM - Print custom pause message without a new line
    <nul set /p " =Press any key to exit... "

    REM - Pause without message
    pause >nul
)
