@echo off

REM - Set the python version
set "python_version=3.12"

REM - Set the main script name
set "main_script_name=compiler_main"

REM - Set the options
set "options=--onefile --include-data-files=./=./=**/*.py --include-module=pygments.lexers.python"

REM - Build the project
py -%python_version% -m nuitka %options% %main_script_name%.py

REM - Remove the build folders
rmdir /s /q .\%main_script_name%.dist
rmdir /s /q .\%main_script_name%.build
rmdir /s /q .\%main_script_name%.onefile-build

REM - Pause the script
pause
