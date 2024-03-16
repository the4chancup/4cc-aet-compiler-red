REM - Collection of system folders where PES is usually installed
REM - These folders need admin rights for editing

if /i "%pes_download_folder_location:~4,7%"=="Program" (
  set admin_mode=1
)
if /i "%pes_download_folder_location:~4,8%"=="Archivos" (
  set admin_mode=1
)
if /i "%pes_download_folder_location:~4,8%"=="Arquivos" (
  set admin_mode=1
)
if /i "%pes_download_folder_location:~4,5%"=="Pliki" (
  set admin_mode=1
)
if /i "%pes_download_folder_location:~4,7%"=="Fisiere" (
  set admin_mode=1
)

REM - Other folder names included in the first check: 
REM - "Programmes", "Programme", "Programfájlok", "Programmi", "Programmer",
REM - "Program", "Program Dosyaları", "Programfiler", "Programas"

REM - If you have pes installed in a system folder not included in the checks above
REM - please let me know and set admin_mode to 1 in the settings in the meanwhile
