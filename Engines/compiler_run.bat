@echo off
REM ^ Don't write everything to screen

REM - Allow reading variables modified inside statements
setlocal EnableDelayedExpansion

REM - Check if python is installed and was added to the PATH
call .\Engines\python_check

REM - Load the settings
call .\Engines\settings_init

echo - 
echo - 
echo - 4cc aet compiler [91mRed[0m
echo - 
echo - 

REM - Check the running type
if %running_type%==0_all_in_one (
  set all_in_one=1
  set exports_to_extracted_run=1
  set extracted_to_contents_run=1
  set contents_to_patches_run=1
)
if %running_type%==1_exports_to_extracted (
  set all_in_one=0
  set exports_to_extracted_run=1
)
if %running_type%==2_extracted_to_contents (
  set all_in_one=0
  set extracted_to_contents_run=1
)
if %running_type%==3_contents_to_patches (
  set all_in_one=0
  set contents_to_patches_run=1
)


REM - If move_cpks mode is enabled
if %move_cpks%==1 (

  REM - Check the PES download folder
  if not exist %pes_download_folder_location%\ (
    
    echo - 
    echo - 
    echo - PES download folder not found.
    echo - Please set its correct path in the settings file.
    echo - The script will restart automatically after you close notepad.
    echo - 
    echo - 
    pause
    
    notepad .\settings.txt
    
    REM - Restart the script
    %0
    
  ) else (
  
    REM - Check if admin mode is needed
    call .\Engines\admin_check
    
    REM - If admin mode is needed or has been forced
    if !admin_mode!==1 (
    
      REM - If permissions haven't been asked yet
      if not defined admin_enabled (
        
        REM - Ask for admin permissions
        .\Engines\admin_request  
      )
    )
  
  )
  
)


REM - Invoke the export extractor
if defined exports_to_extracted_run (
  call py -3 .\Engines\python\1_exports_to_extracted.py
)

REM - Invoke the contents packer
if defined extracted_to_contents_run (
  call py -3 .\Engines\python\2_extracted_to_contents.py 
)

REM - Invoke the cpk packer
if defined contents_to_patches_run (
  call py -3 .\Engines\python\3_contents_to_patches.py
)


pause