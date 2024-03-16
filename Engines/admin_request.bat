@echo off
REM ^ Don't write everything to screen

REM - Request for admin permissions

REM - Check for the all_in_one mode and make a blank temp file if enabled
if defined all_in_one (
  type nul > .\Engines\delete_me
)


REM  --> Check for permissions
IF "%PROCESSOR_ARCHITECTURE%" EQU "amd64" (
  >nul 2>&1 "%SYSTEMROOT%\SysWOW64\cacls.exe" "%SYSTEMROOT%\SysWOW64\config"
) else (
  >nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config"
)

REM --> If error flag set, we do not have admin rights
if '%errorlevel%' NEQ '0' (
    
  echo - 
  echo - Your PES is installed in a system folder and Move Cpks mode is enabled.
  echo - Administrative privileges are needed to move the cpk directly to the download folder.
  echo - 
  
  if not exist .\Engines\admin_warned.txt (
  
    echo - Either accept the incoming request or disable Move Cpks mode in the settings file.
    echo - 
    
    pause
    
    echo This file tells the compiler that you know why the request for admin privileges is needed. > .\Engines\admin_warned.txt
    
  )
  
  goto UACPrompt
  
) else (

  goto gotAdmin
  
)

:UACPrompt
  
  echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
  set params= %*
  echo UAC.ShellExecute "cmd.exe", "/c ""%~s0"" %params:"=""%", "", "runas", 1 >> "%temp%\getadmin.vbs"

  "%temp%\getadmin.vbs"
  del "%temp%\getadmin.vbs"
  exit /B

:gotAdmin

  pushd "%CD%"
  CD /D "%~dp0"


REM - Stop asking for admin permissions
set admin_enabled=1


REM - Delete the temp file if present and invoke the relevant part of the process
if exist .\delete_me (
  
  del .\delete_me
  
  ..\0_all_in_one
  
) else (

  ..\3_contents_to_patches
  
)
