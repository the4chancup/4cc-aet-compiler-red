"""PES 19/21 EDIT00000000 reader for the export upgrader.

Container crypto ported from the converters' save19.py/save21.py; the player
record layouts and master keys are verified against 4ccEditor and the
pesXdecrypter sources. The version is auto-detected from the header.
"""
import struct

masterKeyPes19 = [
    0xFD, 0x60, 0x4A, 0x3E, 0xFD, 0x69, 0x20, 0xD1,
    0x93, 0x92, 0x37, 0xD7, 0x60, 0xD8, 0x30, 0xEE,
    0x65, 0x66, 0xFD, 0x6C, 0xE6, 0x9E, 0x48, 0xF8,
    0x0A, 0x0D, 0xC1, 0x23, 0x7F, 0xAC, 0x89, 0x05,
    0x1D, 0xF8, 0x5A, 0x79, 0x10, 0x7E, 0xAD, 0x81,
    0xAC, 0xAE, 0x9A, 0x6A, 0xAB, 0x16, 0xA6, 0x81,
    0xC2, 0xD2, 0x18, 0xC0, 0xF4, 0xE6, 0x5C, 0x27,
    0x74, 0xF6, 0xC1, 0x9F, 0xF5, 0x01, 0x38, 0x72,
]

masterKeyPes21 = [
    0x90, 0x61, 0xD8, 0x66, 0x43, 0x77, 0x24, 0xF8,
    0x92, 0xBA, 0xB8, 0x71, 0x21, 0xC7, 0x60, 0x63,
    0xF0, 0x91, 0x9A, 0x7D, 0xED, 0x47, 0x80, 0xDE,
    0x51, 0xF5, 0xDD, 0xD1, 0x08, 0xFE, 0x32, 0x84,
    0xF5, 0x09, 0x92, 0x00, 0xB2, 0x3E, 0x88, 0x9F,
    0xEB, 0x24, 0x43, 0x05, 0x58, 0x76, 0x00, 0x22,
    0x9B, 0xFE, 0xEC, 0xF6, 0x50, 0x00, 0x29, 0xD3,
    0x42, 0x75, 0x50, 0xB9, 0xEC, 0xD2, 0xF6, 0x75,
]

# Player record layout per version (offsets inside one record):
#   stride      record size in bytes
#   app_id      appearance playerID offset (u32 LE)
#   boots_gloves  boots/gloves u32 offset (boots = bits 4-17, gloves = bits 18-31)
#   name        player name offset (null-terminated UTF-8)
#   name_len    player name field length
VERSIONS = {
    19: {"stride": 188, "app_id": 116, "boots_gloves": 120, "name": 52, "name_len": 46, "key": masterKeyPes19},
    21: {"stride": 312, "app_id": 240, "boots_gloves": 244, "name": 54, "name_len": 61, "key": masterKeyPes21},
}


class ParseError(Exception):
    pass


class mersenne_rng(object):
    def __init__(self, seed=5489):
        self.state = [0] * 624
        self.f = 1812433253
        self.m = 397
        self.u = 11
        self.s = 7
        self.b = 0x9D2C5680
        self.t = 15
        self.c = 0xEFC60000
        self.l = 18
        self.index = 624
        self.lower_mask = (1 << 31) - 1
        self.upper_mask = 1 << 31

        if type(seed) == list:
            self.seed_list(seed)

    def seed(self, seed):
        self.state[0] = seed
        for i in range(1, 624):
            self.state[i] = self.int_32(self.f * (self.state[i - 1] ^ (self.state[i - 1] >> 30)) + i)

    def seed_list(self, data):
        self.seed(19650218)
        i = 1
        j = 0
        for k in range(max(len(self.state), len(data))):
            temp = ((self.state[i - 1] ^ (self.state[i - 1] >> 30)) * 1664525) & 0xffffffff
            self.state[i] = ((self.state[i] ^ temp) + data[j] + j) & 0xffffffff
            i += 1
            if i >= len(self.state):
                self.state[0] = self.state[len(self.state) - 1]
                i = 1
            j = (j + 1) % len(data)
        for k in range(len(self.state) - 1):
            temp = ((self.state[i - 1] ^ (self.state[i - 1] >> 30)) * 1566083941) & 0xffffffff
            self.state[i] = ((self.state[i] ^ temp) + 0x100000000 - i) & 0xffffffff
            i += 1
            if i >= len(self.state):
                self.state[0] = self.state[len(self.state) - 1]
                i = 1
        self.state[0] = 0x80000000

    def twist(self):
        for i in range(624):
            temp = (self.state[i] & self.upper_mask) + (self.state[(i + 1) % 624] & self.lower_mask)
            temp_shift = temp >> 1
            if temp % 2 != 0:
                temp_shift = temp_shift ^ 0x9908b0df
            self.state[i] = self.state[(i + self.m) % 624] ^ temp_shift
        self.index = 0

    def get_random_number(self):
        if self.index >= 624:
            self.twist()
        y = self.state[self.index]
        y = y ^ (y >> self.u)
        y = y ^ ((y << self.s) & self.b)
        y = y ^ ((y << self.t) & self.c)
        y = y ^ (y >> self.l)
        self.index += 1
        return self.int_32(y)

    def int_32(self, number):
        return int(0xFFFFFFFF & number)


def effective_key(master_key):
    """The raw key with bytes reversed within each 8-byte block."""
    return bytes([master_key[(i & ~7) + 7 - (i & 7)] for i in range(len(master_key))])


def crypt_stream(key, length):
    foo = struct.unpack('< 16I', key)
    twister = mersenne_rng(list(foo))
    output = bytearray((length + 3) // 4 * 4)

    c0 = twister.get_random_number()
    c1 = twister.get_random_number()
    c2 = twister.get_random_number()
    c3 = twister.get_random_number()

    def rol(value, bits):
        return ((value << bits) & 0xffffffff) | (value >> (32 - bits))

    def ror(value, bits):
        return rol(value, 32 - bits)

    for i in range((length + 3) // 4):
        c4 = twister.get_random_number()
        v = c4 ^ c3 ^ c2 ^ c1 ^ c0

        c0 = ror(c1, 15)
        c1 = rol(c2, 11)
        c2 = rol(c3, 7)
        c3 = ror(c4, 13)

        struct.pack_into('< I', output, i * 4, v)
    return output[0:length]


def xor(data, key):
    return bytearray([data[i] ^ key[i % len(key)] for i in range(len(data))])


def crypt_data(key, data):
    return xor(data, crypt_stream(key, len(data)))


def decrypt_salt(salt, effective_master_key):
    header_key = xor(effective_master_key, salt[256:320])
    decrypted_salt = crypt_data(header_key, salt[0:256]) + salt[256:320]
    return xor(xor(xor(xor(
        decrypted_salt[0:64],
        decrypted_salt[64:128]),
        decrypted_salt[128:192]),
        decrypted_salt[192:256]),
        decrypted_salt[256:320])


def load_players(savefile_path):
    """Decrypt an EDIT00000000 and return (version, {player_id: record_bytes}).

    The version is auto-detected by checking the decrypted header against each
    version's effective master key.
    """
    data = open(savefile_path, 'rb').read()

    salt = data[0:320]
    offset = 320

    for version, layout in VERSIONS.items():
        eff_key = effective_key(layout["key"])
        try:
            key = decrypt_salt(salt, eff_key)
            header = crypt_data(xor(key, struct.pack('< Q', 208)), data[offset:offset + 208])
            if header[0:64] != eff_key:
                raise ParseError()
        except (ParseError, struct.error, IndexError):
            continue

        (payload_size, _logo_size, _description_size, _serial_size) = struct.unpack('< 4I', header[64:80])
        offset += 208
        offset += _description_size + _logo_size
        payload = crypt_data(xor(key, struct.pack('< Q', 2)), data[offset:offset + payload_size])

        (player_count,) = struct.unpack('< H', payload[0x60:0x62])
        players = {}
        for i in range(player_count):
            record = payload[0x7c + layout["stride"] * i: 0x7c + layout["stride"] * (i + 1)]
            (player_id,) = struct.unpack('< I', record[layout["app_id"]:layout["app_id"] + 4])
            players[player_id] = record
        return version, players

    raise ParseError("Unrecognized savefile (no version's master key matched)")


def player_name(record, version):
    layout = VERSIONS[version]
    return record[layout["name"]:layout["name"] + layout["name_len"]].split(b"\x00")[0]


def player_boots_gloves(record, version):
    layout = VERSIONS[version]
    (word,) = struct.unpack('< I', record[layout["boots_gloves"]:layout["boots_gloves"] + 4])
    boots_id = (word >> 4) & ((1 << 14) - 1)
    gloves_id = (word >> 18) & ((1 << 14) - 1)
    return boots_id, gloves_id
