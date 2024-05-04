def admin_check(folder_location):
    """
    Collection of system folders on which PES is usually installed
    These folders need admin rights for copying cpks into them

    Other folder names included in this check (they contain "Program"):
    "Programmes", "Programme", "Programfájlok", "Programmi", "Programmer",
    "Program", "Program Dosyaları", "Programfiler", "Programas"

    If you have pes installed in a system folder not included in this check
    please let me know and set admin_mode to 1 in the settings in the meanwhile
    """
    for folder in ["Program", "Archivos", "Arquivos", "Pliki", "Fisiere"]:
        if folder_location[3:].lower().startswith(folder.lower()):
            return 1
    return 0
