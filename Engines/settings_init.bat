REM - Script for loading the settings file, or some default settings if the file or any settings are missing

if exist settings.txt (
  
  rename settings.txt settings.cmd
  call settings
  rename settings.cmd settings.txt
  
) else (
  
  echo - Warning:
  echo - The settings.txt file is missing.
  echo - The compiler will run with the default settings.
  echo - 
  echo - Getting a settings file from the zip is recommended.
  echo - 
  pause

  set settings_default_init=1
)

if not defined settings_default_init (

    if not defined pes_version (
      set settings_missing=1
    )
    if not defined cpk_name (
      set settings_missing=1
    )
    if not defined move_cpks (
      set settings_missing=1
    )
    if not defined pes_download_folder_location (
      set settings_missing=1
    )
    if not defined bins_updating (
      set settings_missing=1
    )
    if not defined multicpk_mode (
      set settings_missing=1
    )
    if not defined fmdl_id_editing (
      set settings_missing=1
    )
    if not defined pause_when_wrong (
      set settings_missing=1
    )
    if not defined pass_through (
      set settings_missing=1
    )
    if not defined admin_mode (
      set settings_missing=1
    )
    
)

if defined settings_missing (
    
  echo - Warning:
  echo - The settings.txt file is outdated or missing some settings.
  echo - The compiler will run with the default settings.
  echo - 
  echo - Getting a new settings file from the zip is recommended.
  echo - 
  pause

  set settings_default_init=1
)
    
if defined settings_default_init (
  
  set pes_version=19
  set cpk_name=4cc_90_test
  set move_cpks=1
  set pes_download_folder_location="C:\Program Files (x86)\Pro Evolution Soccer 2018\download"
  set bins_updating=1
  set multicpk_mode=0
  set fmdl_id_editing=1
  set pause_when_wrong=1
  set pass_through=0
  set admin_mode=0
)