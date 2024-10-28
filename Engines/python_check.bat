REM - Script to check if python is in the PATH and that its version is 3.12

setlocal EnableDelayedExpansion

REM - Check if the Windows version is 7
ver | find "6.1." > nul
if %ERRORLEVEL% == 0 (
  REM - Windows 7
  set "python_link=https://github.com/adang1345/PythonWin7"
) else (
  REM - Windows 8 or newer
  set "python_link=https://www.python.org/downloads/"
)

for /f "tokens=*" %%A in ('py -3 -V 2^>nul') do (

  set python_version_line=%%A

  if "!python_version_line:~0,6!"=="Python" (
    set python_installed=1
  )

  if "!python_version_line:~7,1!"=="3" (
    if "!python_version_line:~9,1!"=="1" (
      if "!python_version_line:~10,1!"=="2" (
        set python_version_ok=1
      )
    )
  )
)

if not defined python_installed (

  echo -
  echo - Python is missing from your pc, please install version 3.12 (not the latest^)
  echo -
  echo - When running the installer, choose Modify, click Next and make sure to check
  echo - the "Add Python to environment variables" checkbox, then click Install
  echo -
  echo Press any key to open the Python download webpage...

  pause >nul

  start "" %python_link%

  timeout /t 3 >nul

  echo -
  echo Press any key to resume the compiler after installing or fixing Python...

  pause >nul

  .\Engines\python_check
)

if not defined python_version_ok (

  echo -
  echo - Python is installed, but you need version 3.12, please install it
  echo -
  echo - When running the installer, choose Modify, click Next and make sure to check
  echo - the "Add Python to environment variables" checkbox, then click Install
  echo -
  echo - If it is already installed, open the Programs manager in the Control Panel
  echo - and uninstall any older and newer versions listed there
  echo -
  echo Press any key to open the Programs manager...

  pause >nul

  start "" appwiz.cpl

  timeout /t 3 >nul

  echo -
  echo Press any key to open the Python download webpage...

  pause >nul

  start "" %python_link%

  timeout /t 3 >nul

  echo -
  echo Press any key to resume the compiler after installing or fixing Python...

  pause >nul

  .\Engines\python_check
)
