import struct
import xml.etree.ElementTree as ET

from .zlib_plus import unzlib_file


def diff_bin_validate(bin_data):
    """
    Validates face_diff binary data.

    Checks the FACE magic bytes and that the file length matches the structure
    described by the header counts (block 2 count at offset 0x48, block 3 count
    at offset 0x4C, with block 2 starting at 0xF0).

    Returns:
        tuple: (is_valid, error_message). On success, error_message is None.
    """
    if len(bin_data) < 0x50:
        return False, f"File too small ({len(bin_data)} bytes, expected at least 80)"
    if bin_data[:4] != b'FACE':
        return False, f"Invalid magic (expected 'FACE', got {bin_data[:4]!r})"
    count2 = struct.unpack('<I', bin_data[0x48:0x4C])[0]
    count3 = struct.unpack('<I', bin_data[0x4C:0x50])[0]
    expected_len = 0xF0 + count2 * 0x10 + count3 * 0x20
    if len(bin_data) != expected_len:
        return False, (
            f"Length mismatch ({len(bin_data)} bytes, expected {expected_len} "
            f"based on header counts: {count2} block-2 entries, {count3} block-3 entries)"
        )
    return True, None


def diff_xml_extract_text(xml_path):
    """
    Extracts base64 text from a face_diff.xml file.

    Supports two formats:
    1. An XML file with a <dif> root element whose text content is base64 data.
    2. A plain text file containing only base64 data (no XML tags at all).

    Unzlibs the file in-place if needed.

    Returns:
        tuple: (text, error_message). On success, text is the base64 string and
            error_message is None. On failure, text is None.
    """
    unzlib_file(xml_path)

    with open(xml_path, 'r') as f:
        file_content = f.read()

    text = None
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        if root.tag == 'dif':
            text = (root.text or "").strip()
            if not text:
                return None, (
                    "The <dif> element has no base64 text content "
                    "(structured XML diff data is not supported)"
                )
        else:
            return None, f"Root tag is <{root.tag}>, must be <dif>"
    except ET.ParseError:
        # Not valid XML - treat the whole file content as raw base64 text
        text = file_content.strip()

    if not text:
        return None, "No base64 content found in the file"

    return text, None
