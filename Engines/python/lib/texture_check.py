import os
import struct
import logging

from .utils.zlib_plus import get_bytes_hex
from .utils.zlib_plus import get_bytes_ascii
from .utils.zlib_plus import unzlib_file


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

def texture_dimensions_check(dds_file_path):

    fox_mode = (int(os.environ.get('PES_VERSION', '19')) >= 18)

    dds_file_name = os.path.basename(dds_file_path)
    dds_folder_path = os.path.dirname(dds_file_path)
    dds_folder_name = os.path.basename(dds_folder_path)

    dds_file_stream = open(dds_file_path, 'rb')

    dds_file_stream.seek(12)
    height = struct.unpack("<I", dds_file_stream.read(4))[0]
    dds_file_stream.seek(16)
    width = struct.unpack("<I", dds_file_stream.read(4))[0]
    dds_file_stream.seek(28)
    mips_count = struct.unpack("<I", dds_file_stream.read(4))[0]

    dds_file_stream.close()

    mips_present = not (mips_count == 0 or mips_count == 1)

    format = get_bytes_ascii(dds_file_path, 84, 4)
    format_uncompressed = (format == "\0\0\0\0")

    # Divisible by 4 check
    height_divisible_by_4 = (height % 4 == 0)
    width_divisible_by_4 = (width % 4 == 0)

    # Power of 2 check
    # 2^n will always have exactly 1 bit set, (2^n)-1 will always have all but 1 bit set, & cancels them out
    height_power_two = ((height & (height-1) == 0) and height != 0)
    width_power_two = ((width & (width-1) == 0) and width != 0)

    # Check if the texture is a portrait
    type_portrait = (dds_folder_name.lower() == "portraits")

    type_regular = not type_portrait

    # Check if the texture is a main kit texture
    type_kit = (dds_folder_name.lower() == "kit textures" and dds_file_name.startswith('u0') and len(dds_file_name) == 11)

    error = False

    if height < 4 or width < 4:
        logging.error( "-")
        logging.error(f"- ERROR - Texture file with invalid dimensions ({str(width)}x{str(height)})")
        logging.error(f"- Folder:         {dds_folder_name}")
        logging.error(f"- Texture name:   {dds_file_name}")
        logging.error( "- This texture will not work")
        logging.error( "-")
        logging.error( "- Resize it so that both sizes are 4 or higher")

        error = True

    if type_portrait:
        if not (height_power_two and width_power_two):
            logging.error( "-")
            logging.error(f"- ERROR - Portrait Texture file with invalid dimensions ({str(width)}x{str(height)})")
            logging.error(f"- Folder:         {dds_folder_name}")
            logging.error(f"- Texture name:   {dds_file_name}")
            logging.error( "- This texture will crash the game")
            logging.error( "-")
            logging.error( "- Resize it so that both sizes are powers of 2")

            error = True

    if type_regular:
        if not (height_power_two or width_power_two) and mips_present and fox_mode:
            logging.error( "-")
            logging.error(f"- ERROR - Texture file with invalid dimensions ({str(width)}x{str(height)})")
            logging.error(f"- Folder:         {dds_folder_name}")
            logging.error(f"- Texture name:   {dds_file_name}")
            logging.error( "- This texture will not work")
            logging.error( "-")
            logging.error( "- Resize it so that at least one size is a power of 2,")
            logging.error( "- or resave it without mipmaps")

            error = True

        if not (height_divisible_by_4 and width_divisible_by_4) and not fox_mode:
            logging.error( "-")
            logging.error(f"- ERROR - Texture file with invalid dimensions ({str(width)}x{str(height)})")
            logging.error(f"- Folder:         {dds_folder_name}")
            logging.error(f"- Texture name:   {dds_file_name}")
            logging.error( "- This texture will not work")
            logging.error( "-")
            logging.error( "- Resize it so that both sizes are divisible by 4")

            error = True

        if not mips_present:
            logging.info( "-")
            logging.info( "- Info - Texture file without mipmaps")
            logging.info(f"- Folder:         {dds_folder_name}")
            logging.info(f"- Texture name:   {dds_file_name}")
            logging.info( "- This texture will work, but it will look better if you resave it with mipmaps")

    if type_kit and not fox_mode:
        if height > 2048 or width > 2048 or not (height_power_two and width_power_two):
            logging.error( "-")
            logging.error(f"- ERROR - Main Kit Texture file with invalid dimensions ({str(width)}x{str(height)})")
            logging.error(f"- Folder:         {dds_folder_name}")
            logging.error(f"- Texture name:   {dds_file_name}")
            logging.error( "- This texture will crash the game")
            logging.error( "-")
            logging.error( "- Resize it so that both sizes are 2048x2048 or less, and powers of 2")

            error = True

        if format_uncompressed:
            logging.error( "-")
            logging.error( "- ERROR - Main Kit Texture file in uncompressed format")
            logging.error(f"- Folder:         {dds_folder_name}")
            logging.error(f"- Texture name:   {dds_file_name}")
            logging.error( "- This texture will crash the game")
            logging.error( "-")
            logging.error( "- Resave it in a compressed format like DXT1 or DXT5")

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
            error = texture_dimensions_check(tex_check_path)

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
