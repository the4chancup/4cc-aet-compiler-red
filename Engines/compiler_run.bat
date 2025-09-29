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
    set "DARK_YELLOW=%ESC%[33m"
    set "BRIGHT_MAGENTA=%ESC%[95m"
    set "RESET=%ESC%[0m"
) else (
    set "DARK_RED="
    set "DARK_YELLOW="
    set "BRIGHT_MAGENTA="
    set "RESET="
)

REM - Try to check if the version is dev from APP_DATA
set "APP_DATA_PATH=.\Engines\python\lib\utils\APP_DATA.py"
if exist "%APP_DATA_PATH%" (
    for /f "tokens=3" %%A in ('findstr /c:"APP_VERSION_DEV" "%APP_DATA_PATH%"') do (
        set "APP_VERSION_DEV=%%A"
    )
)

REM - Check if python is in the embed folder
if not exist ".\Engines\embed\python.exe" (
    if "%APP_VERSION_DEV%"=="False" (
        echo -
        echo - %DARK_RED%FATAL ERROR%RESET% - Missing embedded Python
        echo - The file python.exe was not found in the Engines\embed folder
        echo -
        echo - Please grab a clean compiler folder
        echo - Make sure to grab it from the "Releases" page of the GitHub repository:
        echo - https://github.com/the4chancup/4cc-aet-compiler-red/releases
        echo -
        pause

        exit /b 1
    )

    if not exist ".\Engines\state\missing_embed_warned.txt" (
        echo -
        echo - %DARK_YELLOW%WARNING%RESET% - Missing embedded Python
        echo - The file python.exe was not found in the Engines\embed folder
        echo -
        echo - This is a development version, so the embed folder was not included
        echo - You can copy the embed folder from a release version or, if you have
        echo - Python installed, you can prepare a new embed folder by running the
        echo - embed_prepare.bat script from the Engines\build folder
        echo -
        echo - The compiler will now be run with the Python installed in your system,
        echo - if avaliable
        echo -
        echo - You will not see this message again
        echo -
        pause

        echo This file tells the compiler that the embedded Python was not found. > .\Engines\state\missing_embed_warned.txt
    ) else (
        echo - %DARK_YELLOW%WARNING%RESET% - Running on system Python
    )

    REM - Check if python is installed and was added to the PATH
    if exist ".\Engines\python_check.bat" (
        call .\Engines\python_check.bat
        REM - This script sets the version on python_version
    ) else (
        echo -
        echo - %DARK_RED%FATAL ERROR%RESET% - Missing vital file
        echo - The file python_check.bat was not found in the Engines folder
        echo -
        echo - Please grab a clean compiler folder
        echo -
        pause

        exit /b 1
    )
)

REM - Set the python path
if not exist ".\Engines\embed\python.exe" (
    REM - This instruction is in a separate block to allow the python_version local to be read properly
    set "python_path=py -%python_version%"
) else (
    set "python_path=.\Engines\embed\python.exe"
)

REM - Set the running type from the first argument this script was called with
set running_type=%1

REM - Grab the number from the first character from the running type
set running_type_num=%running_type:~0,1%

REM - Invoke the main compiler script
if exist ".\Engines\compiler_main.py" (
    call %python_path% .\Engines\compiler_main.py %running_type_num%
) else (
    echo -
    echo - %DARK_RED%FATAL ERROR%RESET% - Missing vital file
    echo - The file compiler_main.py was not found in the Engines folder
    echo -
    echo - Please grab a clean compiler folder
    echo -
    pause

    exit /b 1
)

set crashed=%ERRORLEVEL%

REM - Run the log cleaner from the main script to remove the username from the logs
call %python_path% .\Engines\compiler_main.py -1


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
