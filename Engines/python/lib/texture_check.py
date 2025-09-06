import os
import sys
import struct
import logging
import subprocess

from .utils.file_management import file_critical_check
from .utils.zlib_plus import get_bytes_hex
from .utils.zlib_plus import get_bytes_ascii
from .utils.zlib_plus import unzlib_file
from .utils.ftex import ftexToDds
from .utils.ftex import ddsToFtex
from .utils.FILE_INFO import TEXCONV_PATH


def dds_dxt5_conv(tex_path):
    tex_folder_path = os.path.dirname(tex_path)
    if sys.platform == "win32":
        # Convert the texture and store into its parent folder
        file_critical_check(TEXCONV_PATH)
        texconv_args = [TEXCONV_PATH, "-f", "DXT5", "-nologo", "-y", "-o", tex_folder_path, tex_path]
        try:
            result = subprocess.run(texconv_args, capture_output=True, text=True)
            if result.returncode != 0:
                print("- Error converting the texture: ", result.stderr)
        except Exception as e:
            print("- Exception converting the texture: ", str(e))
    else:
        # Prepare a dummy path to save the converted texture
        dummy_tex_path = os.path.join(tex_folder_path, '_dummy_.dds')
        # Convert the texture with imagemagick
        os.system(f"convert -format dds -define dds:compression=dxt5 {tex_path} {dummy_tex_path}")
        # Delete the original texture
        os.remove(tex_path)
        # Rename the dummy texture
        os.rename(dummy_tex_path, tex_path)


def get_image_type(image_path):
    '''Get the type of an image file based on its header'''
    if not os.path.exists(image_path) or not os.path.isfile(image_path):
        return None

    if get_bytes_ascii(image_path, 0, 3) == "DDS":
        return "DDS"
    elif get_bytes_ascii(image_path, 0, 4) == "FTEX":
        return "FTEX"
    elif get_bytes_ascii(image_path, 1, 3) == "PNG":
        return "PNG"
    elif get_bytes_ascii(image_path, 6, 4) == "JFIF":
        return "JPG"
    elif get_bytes_ascii(image_path, 0, 3) == "GIF":
        return "GIF"

    return "Unknown"


def textures_convert(folder_path, fox_mode=False, fox_19=False):
    '''If fox_mode is True, convert all .dds files in the folder to .ftex files

    If fox_19 is False, convert all DX10 files in the folder to DXT5 files'''

    dds_file_list = [f for f in os.listdir(folder_path) if f.endswith('.dds')]
    ftex_file_list = [f for f in os.listdir(folder_path) if f.endswith('.ftex')]

    for tex_file in dds_file_list:

        tex_path = os.path.join(folder_path, tex_file)
        tex_reconvert_needed = False

        # Prepare a temporary file path
        tex_unzlibbed_path = f"{tex_path}.unzlib"

        # Try to unzlib the file
        tex_zlibbed = unzlib_file(tex_path, tex_unzlibbed_path)

        if tex_zlibbed:
            # Set the unzlibbed file as file to check
            tex_check_path = tex_unzlibbed_path
        else:
            # Set the original file as file to check
            tex_check_path = tex_path

        # Check if it is a DX10 file (DX10 label starting from index 84)
        tex_reconvert_needed = get_bytes_ascii(tex_check_path, 84, 4) == 'DX10'

        if tex_reconvert_needed:
            # Convert it to DXT5
            dds_dxt5_conv(tex_check_path)

        # If it was zlibbed
        if tex_zlibbed:

            if fox_mode or tex_reconvert_needed:
                # Delete the original file
                os.remove(tex_path)

                # Rename the unzlibbed file
                os.rename(tex_unzlibbed_path, tex_path)

            else:
                # Delete the unzlibbed file
                os.remove(tex_unzlibbed_path)

        if fox_mode:
            ftex_path = os.path.splitext(tex_path)[0] + '.ftex'

            ddsToFtex(tex_path, ftex_path, None)
            os.remove(tex_path)

    if fox_19 or not fox_mode:
        return

    for tex_file in ftex_file_list:

        tex_path = os.path.join(folder_path, tex_file)
        tex_reconvert_needed = False

        # Check the ftex version number (2.03 in float starting from index 4)
        if not (get_bytes_hex(tex_path, 4, 4) == "85EB0140"):
            tex_reconvert_needed = True

        # Check if it is a BC7 file (value 10 on index 8)
        if (get_bytes_hex(tex_path, 8, 1) == "0B"):
            tex_reconvert_needed = True

        # If needed, reconvert it to DXT5 format
        if not tex_reconvert_needed:
            continue

        # Store a texture path with dds extension
        tex_path_dds = os.path.splitext(tex_path)[0] + ".dds"

        # Convert it to dds
        ftexToDds(tex_path, tex_path_dds)

        # Check if a dds file was created
        if not os.path.exists(tex_path_dds):
            logging.warning(f"- Converting {tex_path} failed - 2.04 or BC7 texture")
        else:
            # Convert the temp dds to DXT5
            dds_dxt5_conv(tex_path_dds)

            # Delete the original ftex
            os.remove(tex_path)

            # Convert the temp dds to ftex
            ddsToFtex(tex_path_dds, tex_path, None)

            # Delete the temp dds file
            os.remove(tex_path_dds)


def dimensions_check(dds_path):

    fox_mode = (int(os.environ.get('PES_VERSION', '19')) >= 18)

    dds_name = os.path.basename(dds_path)
    dds_folder_path = os.path.dirname(dds_path)
    dds_folder = os.path.basename(dds_folder_path)

    error = False

    inputStream = open(dds_path, 'rb')

    inputStream.seek(12)
    height = struct.unpack("<I", inputStream.read(4))[0]
    inputStream.seek(16)
    width = struct.unpack("<I", inputStream.read(4))[0]
    inputStream.seek(28)
    mips_count = struct.unpack("<I", inputStream.read(4))[0]

    inputStream.close()

    mips_missing = (mips_count == 0 or mips_count == 1)

    format = get_bytes_ascii(dds_path, 84, 4)
    format_uncompressed = (format == "\0\0\0\0")

    # Power of 2 check
    # 2^n will always have exactly 1 bit set, (2^n)-1 will always have all but 1 bit set, & cancels them out
    height_bad = not ((height & (height-1) == 0) and height != 0)
    width_bad = not ((width & (width-1) == 0) and width != 0)

    # Check if the texture is a main kit texture
    texture_type_kit = dds_folder.lower() == "kit textures" and dds_name.startswith('u0') and len(dds_name) == 11

    # Check if the texture is a portrait
    texture_type_portrait = dds_folder.lower() == "portraits"

    if texture_type_portrait:
        if (height_bad or width_bad):

            logging.error( "-")
            logging.error(f"- ERROR: Portrait Texture file with invalid dimensions ({str(width)}x{str(height)})")
            logging.error(f"- Folder:         {dds_folder}")
            logging.error(f"- Texture name:   {dds_name}")
            logging.error( "- This texture will crash the game")
            logging.error( "- Resize it so that both sizes are powers of 2")

            error = True

    else:
        if (height_bad or width_bad) and not mips_missing:

            logging.warning( "-")
            logging.warning(f"- Warning: Texture file with irregular dimensions ({str(width)}x{str(height)})")
            logging.warning(f"- Folder:         {dds_folder}")
            logging.warning(f"- Texture name:   {dds_name}")
            logging.warning( "- This texture might not work, in which case:")
            logging.warning( "- Resize it so that both sizes are powers of 2, or resave it without mipmaps")

        if mips_missing:

            logging.info( "-")
            logging.info( "- Info: Texture file without mipmaps")
            logging.info(f"- Folder:         {dds_folder}")
            logging.info(f"- Texture name:   {dds_name}")
            logging.info( "- This texture will work, but it will look better if you resave it with mipmaps")

    if height < 4 or width < 4:

        logging.error( "-")
        logging.error(f"- ERROR - Texture file with invalid dimensions ({str(width)}x{str(height)})")
        logging.error(f"- Folder:         {dds_folder}")
        logging.error(f"- Texture name:   {dds_name}")
        logging.error( "- This texture will not work")
        logging.error( "- Resize it so that both sizes are 4 or higher")

        error = True

    if (
        not fox_mode and texture_type_kit and
        (height > 2048 or width > 2048 or height_bad or width_bad)
    ):
        logging.error( "-")
        logging.error(f"- ERROR - Main Kit Texture file with invalid dimensions ({str(width)}x{str(height)})")
        logging.error(f"- Folder:         {dds_folder}")
        logging.error(f"- Texture name:   {dds_name}")
        logging.error( "- This texture will crash the game")
        logging.error( "- Resize it so that both sizes are 2048x2048 or less, and powers of 2")

        error = True

    if (not fox_mode and texture_type_kit and format_uncompressed):
        logging.error( "-")
        logging.error( "- ERROR - Main Kit Texture file in uncompressed format")
        logging.error(f"- Folder:         {dds_folder}")
        logging.error(f"- Texture name:   {dds_name}")
        logging.error( "- This texture will crash the game")
        logging.error( "- Resave it with a valid format like DXT5")

        error = True

    return error


# Check if the texture is a proper dds or ftex and unzlib if needed
def texture_check(tex_path):

    if tex_path.lower().endswith("dds"):
        tex_type = "DDS"
    elif tex_path.lower().endswith("ftex"):
        tex_type = "FTEX"
    else:
        return False

    # Read the necessary parameters
    pes_version = os.environ.get('PES_VERSION', '19')
    fox_mode = (int(pes_version) >= 18)

    # Store the name of the parent folder
    tex_folder = os.path.basename(os.path.dirname(tex_path))

    # Store the name of the texture and its parent folder
    tex_name = os.path.join(tex_folder, os.path.basename(tex_path))

    # DDS
    if tex_type == "DDS":

        error = False
        tex_zlibbed = False

        # Prepare a temporary file path
        tex_unzlibbed_path = f"{tex_path}.unzlib"

        # Try to unzlib the file
        tex_zlibbed = unzlib_file(tex_path, tex_unzlibbed_path)

        if tex_zlibbed:
            # Set the unzlibbed file as file to check
            tex_check_path = tex_unzlibbed_path
        else:
            # Set the original file as file to check
            tex_check_path = tex_path

        # Check if it is a real dds
        tex_header_type = get_image_type(tex_check_path)
        if not (tex_header_type == "DDS"):
            logging.error( "-")
            logging.error(f"- ERROR - Texture is not a real {tex_type} file")
            logging.error(f"- Folder:         {tex_folder}")
            logging.error(f"- Texture name:   {tex_name}")
            logging.error(f"- Real type:      {tex_header_type}")
            logging.error( "- The file will be deleted, please save it properly")
            error = True

        if not error:

            # Make sure the dimensions are powers of 2
            error = dimensions_check(tex_check_path)

        if not tex_zlibbed:
            return error

        # If it was zlibbed
        if fox_mode:
            # Delete the original file
            os.remove(tex_path)

            # Rename the unzlibbed file
            os.rename(tex_unzlibbed_path, tex_path)

        else:
            # Delete the unzlibbed file
            os.remove(tex_unzlibbed_path)

        return error

    # FTEX

    # If fox mode is disabled, reject the texture
    if not fox_mode:
        logging.error( "-")
        logging.error(f"- ERROR - Texture is an {tex_type} file")
        logging.error(f"- Folder:         {tex_folder}")
        logging.error(f"- Texture name:   {tex_name}")
        logging.error(f"- ftex textures are not supported on Pre-Fox PES versions ({pes_version} chosen)")
        return True

    # Check if it is a real ftex
    tex_header_type = get_image_type(tex_path)
    if not (tex_header_type == "FTEX"):
        logging.error( "-")
        logging.error(f"- ERROR - Texture is not a real {tex_type} file")
        logging.error(f"- Folder:         {tex_folder}")
        logging.error(f"- Texture name:   {tex_name}")
        logging.error(f"- Real type:      {tex_header_type}")
        logging.error( "- The file will be deleted, please save it properly")
        return True

    # Check if it has mipmaps (index 16)
    ftex_mipmaps = get_bytes_hex(tex_path, 16, 1)
    if (ftex_mipmaps == "00"):
        logging.warning( "-")
        logging.warning( "- Warning: Texture file without mipmaps")
        logging.warning(f"- Folder:         {tex_folder}")
        logging.warning(f"- Texture name:   {tex_name}")
        logging.warning( "- This texture will probably not work, please resave it with mipmaps")

    return False
