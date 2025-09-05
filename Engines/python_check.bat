REM - Script for checking if python is in the PATH and that its version is 3.12 or 3.13

REM - Check if the Windows version is 7
ver | find "6.1." > nul
if %ERRORLEVEL% == 0 (
  REM - Windows 7
  set "python_link=https://github.com/adang1345/PythonWin7"
) else (
  REM - Windows 8 or newer
  set "python_link=https://www.python.org/downloads/"
)

REM - Check if python 3.13 is installed
for /f "tokens=*" %%A in ('py -3.13 -V 2^>nul') do (
  set python_version_line=%%A
)

set "python_version=%python_version_line:~7,4%"

if "%python_version_line:~0,6%"=="Python" (
  set python_installed=1

  if "%python_version%"=="3.13" (
    goto python_version_ok
  )
)

REM - Check if python 3.12 is installed
for /f "tokens=*" %%A in ('py -3.12 -V 2^>nul') do (
  set python_version_line=%%A
)

set "python_version=%python_version_line:~7,4%"

if "%python_version_line:~0,6%"=="Python" (
  set python_installed=1

  if "%python_version%"=="3.12" (
    goto python_version_ok
  )
)


if not defined python_installed (
  goto python_missing
)

if not defined python_version_ok (
  goto python_version_bad
)


:python_version_ok
exit /b 0


:python_missing
if not defined python_installed (

  echo -
  echo - Python is missing from your pc, please install version 3.13
  echo - (watch out, it might not be the latest^)
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


:python_version_bad
if not defined python_version_ok (

  echo -
  echo - Python is installed, but you need version 3.12 or 3.13, please install one
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
