import struct


ENCODINGS = [
    'ascii', 'utf8', 'utf16', 'cp1252', 'iso-8859-1', 'shift_jis',
    'euc_jp', 'iso2022_jp', 'ibm437', 'ibm850', 'ibm852',
    'shift_jis_2004', 'shift_jisx0213', 'euc_jis_2004',
    'iso2022_jp_2004'
]

def try_decode(text):
    decoding_map = {}
    for enc in ENCODINGS:
        decoded_text = None
        try:
            decoded_text = text.decode(enc)
            print(f"Decoded text using {enc}: {decoded_text}")
            decoding_map[enc] = decoded_text
        except UnicodeDecodeError:
            print(f"Error decoding using {enc}")

        i = 0
        bytes = struct.unpack('B' * len(text), text)
        try:
            for b in bytes:
                b_d = b.to_bytes(1, 'little')
                # print(f"decoding byte[{i}] = {b_d=}[{type(b)}] using {enc=}")

                decoded_b = b_d.decode(enc)
                if decoded_text == None:
                    decoded_text = decoded_b
                else:
                    decoded_text += decoded_b
                i += 1
        except UnicodeDecodeError:
            print(f"  ➡  {hex(bytes[i])=} using {enc=}, successfully decoded '{decoded_text=}'")
    return decoding_map

try_decode(b'DRAGONQUEST 1\xa52      ')
