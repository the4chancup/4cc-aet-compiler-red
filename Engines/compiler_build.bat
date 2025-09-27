@echo off

REM - Set the python version
set "python_version=3.12"

REM - Set the main script name
set "main_script_name=compiler_main"

REM - Remove the dist folder
rmdir /s /q .\dist 2>nul

REM - Build the project
py -%python_version% -m nuitka %main_script_name%.py ^
--standalone ^
--include-data-files=./=./=**/*.py ^
--include-module=pygments.lexers.python

REM - Rename the dist folder
ren .\%main_script_name%.dist dist

REM - Remove the build folders
rmdir /s /q .\%main_script_name%.build
rmdir /s /q .\%main_script_name%.onefile-build 2>nul

echo.

REM - Pause the script
pause
