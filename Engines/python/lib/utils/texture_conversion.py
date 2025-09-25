import os
import sys
import logging
import subprocess

from .file_management import file_critical_check
from .zlib_plus import get_bytes_hex
from .zlib_plus import get_bytes_ascii
from .zlib_plus import unzlib_file
from .ftex import ftexToDds
from .ftex import ddsToFtex
from .FILE_INFO import TEXCONV_PATH


def dds_dxt5_conv(tex_path):
    tex_folder_path = os.path.dirname(tex_path)
    if sys.platform == "win32":
        # Convert the texture and store into its parent folder
        file_critical_check(TEXCONV_PATH)
        texconv_args = [TEXCONV_PATH, "-f", "DXT5", "-nologo", "-srgb", "-y", "-o", tex_folder_path, tex_path]
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
