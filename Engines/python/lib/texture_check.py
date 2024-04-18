import os
import sys
import struct

from .utils.zlib_plus import get_bytes_hex
from .utils.zlib_plus import get_bytes_ascii
from .utils.zlib_plus import unzlib_file
from .utils.ftex import ftexToDds
from .utils.ftex import ddsToFtex


def dds_dxt5_conv(tex_path):
    tex_folder_path = os.path.dirname(tex_path)
    if sys.platform == "win32":
        # Convert the texture and store into its parent folder
        os.system(f'Engines\\texconv.exe -f DXT5 -nologo -y -o "{tex_folder_path}" "{tex_path}" >nul')
    else:
        # Prepare a dummy path to save the converted texture
        dummy_tex_path = os.path.join(tex_folder_path, '_dummy_.dds')
        # Convert the texture
        os.system(f'convert -format dds -define dds:compression=dxt5 {tex_path} {dummy_tex_path}')
        # Delete the original texture
        os.remove(tex_path)
        # Rename the dummy texture
        os.rename(dummy_tex_path, tex_path)


def dimensions_check(dds_path):

    dds_name = os.path.basename(dds_path)
    dds_folder_path = os.path.dirname(dds_path)
    dds_folder = os.path.basename(dds_folder_path)

    inputStream = open(dds_path, 'rb')

    inputStream.seek(12)
    height = struct.unpack("<I", inputStream.read(4))[0]
    inputStream.seek(16)
    width = struct.unpack("<I", inputStream.read(4))[0]
    inputStream.seek(28)
    mips_count = struct.unpack("<I", inputStream.read(4))[0]

    inputStream.close()

    # Power of 2 check
    # 2^n will always have exactly 1 bit set, (2^n)-1 will always have all but 1 bit set, & cancels them out
    height_bad = not ((height & (height-1) == 0) and height != 0)
    width_bad = not ((width & (width-1) == 0) and width != 0)

    if (height_bad or width_bad) and not (mips_count == 0 or mips_count == 1):

        print(f"- Warning - Texture file with invalid dimensions ({str(width)}x{str(height)})")
        print(f"- Folder:         {dds_folder}")
        print(f"- DDS name:       {dds_name}")
        print( "- This texture will probably not work")
        print( "- Resize it so that both sizes are powers of 2, or resave it without mipmaps")
        print( "-")


# Check if the texture is a proper dds or ftex and unzlib if needed
def texture_check(tex_path):

    # Read the necessary parameters
    fox_mode = (int(os.environ.get('PES_VERSION', '19')) >= 18)
    fox_19 = (int(os.environ.get('PES_VERSION', '19')) >= 19)

    # Store the name of the parent folder
    tex_folder_name = os.path.basename(os.path.dirname(tex_path))

    # Store the name of the texture and its parent folder
    tex_name = os.path.join(tex_folder_name, os.path.basename(tex_path))

    tex_zlibbed = None
    tex_reconvert_needed = None
    #tex_mips_none = None

    tex_error_format = None

    tex_type = None
    if tex_name.lower().endswith('dds'):
        tex_type = 'dds'
    elif tex_name.lower().endswith('ftex'):
        tex_type = 'ftex'

    if tex_type == 'dds':

        # Prepare a temporary file path
        tex_unzlibbed_path = f'{tex_path}.unzlib'

        # Try to unzlib the file
        tex_zlibbed = unzlib_file(tex_path, tex_unzlibbed_path)

        if tex_zlibbed:
            # Set the unzlibbed file as file to check
            tex_check_path = tex_unzlibbed_path
        else:
            # Set the original file as file to check
            tex_check_path = tex_path

        # Check if it is a real dds (DDS label starting from index 0)
        if not (get_bytes_ascii(tex_check_path, 0, 3) == 'DDS'):
            print(f'- Texture {tex_name} is not a real {tex_type}')
            print('- The file will be deleted, please save it properly')
            tex_error_format = True

        if not tex_error_format:

            # Make sure the dimensions are powers of 2
            dimensions_check(tex_check_path)

            if fox_mode and not fox_19:

                # Check if it is a BC7 file (DX10 label starting from index 84)
                if not (get_bytes_ascii(tex_check_path, 84, 4) == 'DX10'):
                    # Convert it to DXT5
                    dds_dxt5_conv(tex_check_path)

        # If it was zlibbed
        if tex_zlibbed:

            if fox_mode:
                # Delete the original file
                os.remove(tex_path)

                # Rename the unzlibbed file
                os.rename(tex_unzlibbed_path, tex_path)

            else:
                # Delete the unzlibbed file
                os.remove(tex_unzlibbed_path)

    elif tex_type == 'ftex':

        if not fox_mode:

            # If fox mode is disabled, reject the texture
            print(f"- Texture {tex_name} is a {tex_type} file")
            print(f"- {tex_type} textures are not supported on the chosen PES version")

            tex_error_format = True

        if not tex_error_format:
            # Check if it is a real ftex (FTEX label starting from index 0)
            if not (get_bytes_ascii(tex_path, 0, 4) == 'FTEX'):
                print(f'- Texture {tex_name} is not a real {tex_type}')
                print('- The file will be deleted, please save it properly')
                tex_error_format = True

        if not tex_error_format:
            # Check if it has mipmaps (index 16)
            if (get_bytes_hex(tex_path, 16, 1) == '00'):
                print(f'- Texture {tex_name} is missing mimaps')
                print('- The file will be deleted, please save it properly')
                tex_error_format = True

        if not tex_error_format:
            # Check the ftex version number (2.03 in float starting from index 4)
            if not (get_bytes_hex(tex_path, 4, 4) == '85EB0140'):
                tex_reconvert_needed = 1

            # Check if it is a BC7 file (value 10 on index 8)
            if (get_bytes_hex(tex_path, 8, 1) == '0B'):
                tex_reconvert_needed = 1

            # If needed, reconvert it to DXT5 format
            if tex_reconvert_needed:

                # Store a texture path with dds extension
                tex_path_dds = os.path.splitext(tex_path)[0] + '.dds'

                # Convert it to dds
                ftexToDds(tex_path, tex_path_dds)

                # Check if a dds file was created
                if not os.path.exists(tex_path_dds):
                    print(f'- Converting {tex_name} failed - 2.04 or BC7 texture')
                else:
                    # Convert the temp dds to DXT5
                    dds_dxt5_conv(tex_path_dds)

                    # Delete the original ftex
                    os.remove(tex_path)

                    # Convert the temp dds to ftex
                    ddsToFtex(tex_path_dds, tex_path, None)

                    # Delete the temp dds file
                    os.remove(tex_path_dds)

    return tex_error_format
