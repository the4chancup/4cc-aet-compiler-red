@echo off
REM ^ Don't write everything to screen

REM - Set the working folder
cd /D "%~dp0\.."


REM - Set the ESC character and colors for text coloring
for /f "delims=" %%E in ('forfiles /p "%~dp0." /m "%~nx0" /c "cmd /c echo(0x1B"') do (
    set "ESC=%%E"
)
if not defined NO_COLOR (
    set "DARK_RED=%ESC%[31m"
    set "BRIGHT_MAGENTA=%ESC%[95m"
    set "RESET=%ESC%[0m"
) else (
    set "DARK_RED="
    set "BRIGHT_MAGENTA="
    set "RESET="
)

REM - Set the running type from the first argument this script was called with
set running_type=%1

REM - Grab the number from the first character from the running type
set running_type_num=%running_type:~0,1%

REM - Try to check if the version is dev from APP_DATA
set "APP_DATA_PATH=.\Engines\python\lib\utils\APP_DATA.py"
if exist "%APP_DATA_PATH%" (
    for /f "tokens=3" %%A in ('findstr /c:"APP_VERSION_DEV" "%APP_DATA_PATH%"') do (
        set "APP_VERSION_DEV=%%A"
    )
)

REM - Invoke the main compiler script
if exist ".\Engines\dist\compiler_main.exe" (
    call .\Engines\dist\compiler_main.exe %running_type_num%
) else (
    echo -
    echo - %DARK_RED%FATAL ERROR%RESET% - Missing vital file
    echo - The file compiler_main.exe was not found in the Engines\dist folder
    echo -
    if "%APP_VERSION_DEV%"=="False" (
        echo - Please grab a clean compiler folder
        echo - Make sure to grab it from the "Releases" page of the GitHub repository:
        echo - https://github.com/the4chancup/4cc-aet-compiler-red/releases
    ) else (
        echo - This is a development version, so no exe is available
        echo - You need to open the Engines folder and run compiler_run_py.bat
        echo - or 0_all_in_one_py.bat instead
    )
    echo -
    pause

    exit /b 1
)

set crashed=%ERRORLEVEL%

REM - Run the log cleaner from the main script to remove the username from the logs
call .\Engines\dist\compiler_main.exe -1


REM - If the compiler returned an error
if %crashed% GEQ 1 (

    echo -
    echo -
    echo - %BRIGHT_MAGENTA%CRASH%RESET% - The compiler has run into an unexpected error and stopped
    if exist ".\crash.log" (
        echo - A log file crash.log has been saved to the compiler's folder
        echo - Please post it on the /aesco/ server or the divegrass thread
    ) else (
        echo - Please take a screenshot and post it on the /aesco/ server
        echo - or the divegrass thread
    )
    echo -

    REM - Print custom pause message without a new line
    <nul set /p " =Press any key to exit... "

    REM - Pause without message
    pause >nul

    exit /b %crashed%
)
