@echo off
REM ^ Don't write everything to screen

REM - Set the working folder
cd /D "%~dp0"

REM - Run the export upgrader with the embedded Python (or the system one)
if exist "..\embed\python.exe" (
    set "python_path=..\embed\python.exe"
) else (
    set "python_path=python"
)

%python_path% ".\export_upgrade.py"
pause
