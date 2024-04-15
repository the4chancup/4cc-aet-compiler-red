import struct
import os
import sys
import fnmatch
import re
import logging

def transfer(fn, id, teamid = "000"):

    b = open(fn, 'rb')

    logging.debug("[MTLTools] Working on file " + fn)

    #Grab actually important values from header
    b.seek(32)
    sec0 = struct.unpack("<I", b.read(4))[0] #Number of items in section 0
    sec1 = struct.unpack("<I", b.read(4))[0] #Number of items in section 1
    head = struct.unpack("<I", b.read(4))[0] #Header length
    b.seek(4, 1)
    sec1off = struct.unpack("<I", b.read(4))[0] #Sector 1 offset

    #Then start working on the rest of the file
    b.seek(64, 0)

    #Go through blockmap 0
    texoff = 0 #Texture offset
    texc = 0 #Texture count
    stroff = 0 #Str offset
    strc = 0 #Str count
    bcv = 0 #Block Check Value, make sure all blocks were found
    for i in range(sec0):
        dat = b.read(2)
        items = b.read(2)
        off = b.read(4)
        if(struct.unpack("<H", dat)[0] == 6): #Texture block
            texoff = struct.unpack("<I", off)[0]
            texc = struct.unpack("<H", items)[0]
            bcv = bcv + 1
        elif(struct.unpack("<H", dat)[0] == 12): #String block
            stroff = struct.unpack("<I", off)[0]
            strc = struct.unpack("<H", items)[0]
            bcv = bcv + 1

    #Go through blockmap 1
    strend = 0
    strlen = 0
    for i in range(sec1):
        dat = b.read(4)
        off = b.read(4)
        blen = b.read(4)
        if(struct.unpack("<I", dat)[0] == 3):
            strend = struct.unpack("<I", off)[0]
            strlen = struct.unpack("<I", blen)[0]

    #Check if all required blocks were found.
    ##NOTE: Change this when a new block is added
    if(bcv == 2):
        #We have all the required offsets now, start building output
        b.seek(head+stroff)

        #Store string lengths
        lens = []
        for i in range(strc):
            b.seek(2, 1)
            lens.append(struct.unpack('<H', b.read(2))[0])
            b.seek(4, 1)

        #Then process MTL
        strs = [] #Store strings in a list
        b.seek(sec1off + strend)
        for i in range(strc):
            ln = b.read(lens[i]+1).rstrip(b'\0').decode('utf-8')
            if(ln):
                strs.append(ln)

        #Scan textures
        b.seek(head + texoff)
        paths = [] #Store texture paths
        for i in range(texc):
            texp = struct.unpack("<H", b.read(2))[0] #Texture path
            if texp not in paths:
                paths.append(texp)

        #Close file for now, we're done reading
        b.close()

        #Texture Path Count, for error reporting
        tpc = 0
        #Process the paths
        for path in paths:
            spath = strs[path-1].split("/") #Split path to individual pieces

            #Make sure our magic piece is the player ID and the path is the correct path
            #Faces path
            if(len(spath) == 10 and re.fullmatch("[0-9]{5}", spath[7])):
                if(id.isdigit() and len(id) == 5):
                    logging.debug("[MTLTools] Successfully changed ID for path " + strs[path-1])
                    spath[7] = str(id) #Change the ID
                    npath = "/".join(spath) #Combine the path
                    strs[path-1] = npath #Overwrite old path in string list
                    tpc = tpc + 1
                else:
                    logging.debug("[MTLTools] Incorrect player ID " + id + ", please make sure the ID is exactly 5 digits long", file=sys.stderr)

            #Refs path
            if(len(spath) == 10 and re.fullmatch("referee[0-9]{3}", spath[7])):
                if(re.fullmatch("referee[0-9]{3}", id)):
                    logging.debug("[MTLTools] Successfully changed ID for path " + strs[path-1])
                    spath[7] = str(id) #Change the ID
                    npath = "/".join(spath) #Combine the path
                    strs[path-1] = npath #Overwrite old path in string list
                    tpc = tpc + 1
                else:
                    logging.debug("[MTLTools] Incorrect referee name " + id, file=sys.stderr)

            #Boots path
            elif(len(spath) == 8 and re.fullmatch("k[0-9]{4}", spath[6])):
                if(re.fullmatch("k[0-9]{4}", id)):
                    logging.debug("[MTLTools] Successfully changed ID for path " + strs[path-1])
                    spath[6] = id #Change the ID
                    npath = "/".join(spath) #Combine the path
                    strs[path-1] = npath #Overwrite old path in string list
                    tpc = tpc + 1
                else:
                    logging.debug("[MTLTools] Incorrect boots ID " + id + ", please make sure the ID is exactly 5 characters long and follows the 'kXXXX' format", file=sys.stderr)

            #Gloves path
            elif(len(spath) == 8 and re.fullmatch("g[0-9]{4}", spath[6])):
                if(re.fullmatch("g[0-9]{4}", id)):
                    logging.debug("[MTLTools] Successfully changed ID for path " + strs[path-1])
                    spath[6] = id #Change the ID
                    npath = "/".join(spath) #Combine the path
                    strs[path-1] = npath #Overwrite old path in string list
                    tpc = tpc + 1
                else:
                    logging.debug("[MTLTools] Incorrect gloves ID " + id + ", please make sure the ID is exactly 5 characters long and follows the 'gXXXX' format", file=sys.stderr)

            #Balls path
            elif(len(spath) == 7 and re.fullmatch("ball[0-9]{3}", spath[5])):
                if(re.fullmatch("ball[0-9]{3}", id)):
                    logging.debug("[MTLTools] Successfully changed ID for path " + strs[path-1])
                    spath[5] = id #Change the ID
                    npath = "/".join(spath) #Combine the path
                    strs[path-1] = npath #Overwrite old path in string list
                    tpc = tpc + 1
                else:
                    logging.debug("[MTLTools] Incorrect ball ID " + id + ", please make sure the ID is exactly 7 characters long and follows the 'ballXXX' format", file=sys.stderr)

            #Common path
            elif(len(spath) == 9 and re.fullmatch("[0-9]{3}", spath[6])):
                if(re.fullmatch("[0-9]{3}", teamid)):
                    logging.debug("[MTLTools] Successfully changed ID for path " + strs[path-1])
                    spath[6] = teamid #Change the ID
                    npath = "/".join(spath) #Combine the path
                    strs[path-1] = npath #Overwrite old path in string list
                    tpc = tpc + 1
                else:
                    logging.debug("[MTLTools] Incorrect Team ID " + teamid + ", please make sure the ID is exactly 3 characters long and follows the 'XXX' format", file=sys.stderr)

            else:
                logging.debug("[MTLTools] No ID found in path " + strs[path-1])

        #Yell if there were no paths with IDs at all
        if(tpc == 0):
            logging.debug("[MTLTools] No paths with IDs found in file " + fn)
            print("[MTLTools] No paths with IDs found in file " + fn, file=sys.stderr)

        #Re-open file for writing
        b = open(fn, "r+b")

        #Seek to string block
        b.seek(sec1off + strend)

        #Re-write FMDL strings
        for s in strs:
            b.write(struct.pack("B", 0))
            b.write(bytes(s, 'utf-8'))

        #Done, close file for good and exit
        b.close()

    else:
        logging.debug("1") #Error code 1 - Didn't find required blocks in file (texture definition, string block)
        b.close()

def main():
    if not((len(sys.argv) >= 3) and (len(sys.argv) <= 4)):
        logging.debug("[MTLTools] Error: Invalid arguments.\nUsage: id.exe <.fmdl file> <new ID> [team ID]", file=sys.stderr)
    elif not(os.path.isfile(sys.argv[1])):
        logging.debug("[MTLTools] Error: Provided file " + sys.argv[1] + " doesn't exist or is not a valid file", file=sys.stderr)
    elif not(fnmatch.fnmatch(sys.argv[1], '*.fmdl')):
        logging.debug("[MTLTools] Error: Provided file " + sys.argv[1] + " doesn't appear to be a .fmdl file", file=sys.stderr)
        logging.debug("[MTLTools] Please make sure the file ends in \".fmdl\"", file=sys.stderr)
    else:
        transfer(sys.argv[1], sys.argv[2], sys.argv[3])

if __name__ == '__main__':
    main()