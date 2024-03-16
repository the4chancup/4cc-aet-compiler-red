import struct
import zlib
import os

class DecodeError(Exception):
	pass

def encodeHeader(compressedBuffer, uncompressedBuffer):
	return struct.pack('< 3B 5s II',
		0x00,
		0x10,
		0x01,
		'WESYS'.encode('UTF-8'),
		len(compressedBuffer),
		len(uncompressedBuffer),
	)

def decodeHeader(byteBuffer):
	if len(byteBuffer) < 16:
		return None
	header = byteBuffer[0:16]
	(magic, ) = struct.unpack('< 4x 4s 8x', header)
	if magic != b'ESYS':
		return None
	return memoryview(byteBuffer)[16:]

def compress(byteBuffer):
	compressedBuffer = zlib.compress(byteBuffer)
	return encodeHeader(compressedBuffer, byteBuffer) + compressedBuffer

def tryCompress(byteBuffer):
	compressedBuffer = zlib.compress(byteBuffer)
	if len(compressedBuffer) + 16 < len(byteBuffer):
		return encodeHeader(compressedBuffer, byteBuffer) + compressedBuffer
	else:
		return byteBuffer

def decompress(byteBuffer):
	compressedBuffer = decodeHeader(byteBuffer)
	if compressedBuffer is None:
		raise DecodeError()
	try:
		return zlib.decompress(compressedBuffer)
	except:
		raise DecodeError()

def tryDecompress(byteBuffer):
	compressedBuffer = decodeHeader(byteBuffer)
	if compressedBuffer is None:
		return byteBuffer
	try:
		return zlib.decompress(compressedBuffer)
	except:
		raise DecodeError()

def isCompressed(byteBuffer):
	compressedBuffer = decodeHeader(byteBuffer)
	return compressedBuffer is not None

# Returns the hex representation of the bytes read from the specified file
def get_bytes_hex(file_path, start, length):
    with open(file_path, 'rb') as file:
        file.seek(start)  # Skip to the start position
        bytes_data = file.read(length)
    return ''.join(f'{byte:02x}' for byte in bytes_data).upper()

# Returns the ascii representation of the bytes read from the specified file
def get_bytes_ascii(file_path, start, length):
	with open(file_path, 'rb') as file:
		file.seek(start)  # Skip to the start position
		bytes_data = file.read(length)
	return ''.join(chr(byte) for byte in bytes_data)

# Unzlibs a file if it was zlibbed
def unzlib_file(source_file_path, destination_file_path = None):
    
    unzlib_needed = False
    if destination_file_path is None:
        destination_file_path = source_file_path

    # Check if it is zlibbed (WESYS label starting from index 3)
    if get_bytes_ascii(source_file_path, 3, 5) == 'WESYS':

        # Unzlib it
        with open(source_file_path, 'rb') as f:
            data = zlib.decompress(f.read())

        with open(destination_file_path, 'wb') as f:
            f.write(data)

        unzlib_needed = True

    return unzlib_needed
