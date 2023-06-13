ENCODING_ASCII = 'ascii'
ENCODING_JIS = 'shift_jis'
ENCODING_INT = 'int'
ENCODING_BYTE = 'byte'
ENCODING_BYTE_NIBBLES = 'byte_nibbles'

def decode_byte_into_nibbles(byte):
    byte_as_int = int.from_bytes(byte, 'little')
    high_nibble = (byte_as_int & 0xF0) >> 4
    low_nibble = byte_as_int & 0x0F
    return (high_nibble, low_nibble)

def decode_two_byte_int(two_byte_int):
    if len(two_byte_int) != 2:
        raise BufferError("Buffer of data must be 2 bytes long")
    return int.from_bytes(two_byte_int, 'little')

DECODER_MAP = [
    [ENCODING_ASCII , lambda string_of_bytes : string_of_bytes.decode(ENCODING_ASCII)],
    [ENCODING_JIS , lambda string_of_bytes : string_of_bytes.decode(ENCODING_JIS)],
    [ENCODING_INT , decode_two_byte_int],
    [ENCODING_BYTE_NIBBLES , decode_byte_into_nibbles],
    [ENCODING_BYTE , lambda raw_byte : int.from_bytes(raw_byte, 'little')]
]
DECODER_MAP = dict(DECODER_MAP)

def decodeField(binary_data, encoding):
    return DECODER_MAP[encoding](binary_data)