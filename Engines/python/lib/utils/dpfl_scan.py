def dpfl_scan(file_path):
    '''Scan a DPFL file and return a list of all the cpks listed in it.
    
    Args:
        file_path (str): The path to the DPFL file
    
    Returns:
        list[str]: A list of all the cpks listed on the DPFL file
    
    DPFL files are files named "DpFileList.bin" and contained in the PES download folder.
    They are binary files with a list of all the cpks in the PES download folder which PES should load.
    Each cpk is in its own line, each line is 48 characters long. The name of the cpk is at the position 0x10 on each line.
    This function returns a list of all the cpks listed on the DPFL file. It stops at the first empty line.
    '''
    
    with open(file_path, 'rb') as f:
        cpks = []
        while True:
            line = f.read(48)
            if not line:
                break
            if line[16:17] == b'\x00':
                break
            for i, c in enumerate(line[16:]):
                if c == 0:
                    cpks.append(line[16:16+i].decode('ascii'))
                    break
    return cpks
