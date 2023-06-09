ENCODING_ASCII = 'ascii'
ENCODING_INT = 'int'
ENCODING_BYTE = 'byte'

def decode_two_byte_int(two_byte_int):
    if len(two_byte_int) != 2:
        raise BufferError("Buffer of data must be 2 bytes long")
    return lambda two_byte_int : int.from_bytes(two_byte_int, 'little')

DECODER_MAP = [
    [ENCODING_ASCII , lambda string_of_bytes : string_of_bytes.decode(ENCODING_ASCII)],
    [ENCODING_INT , decode_two_byte_int],
    [ENCODING_BYTE , lambda raw_byte : ord(raw_byte, 'little')]
]
DECODER_MAP = dict(DECODER_MAP)

def decodeField(binary_data, encoding):
    return DECODER_MAP[encoding](binary_data)