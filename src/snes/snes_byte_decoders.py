import src.snes.snes_constants as s_con
import src.common.byte_decoders as bd

def decodeMapSpeed(map_speed_byte):
    if(len(map_speed_byte) != 1):
        raise MemoryError("Map/Speed byte was not read from memory correctly")

    #TODO - test if I need to use a for loop here
    for b in map_speed_byte:
        checked_fixed_bits = [((b >> bit) & 1) == 0 for bit in s_con.MAPSPEED_BITS_FIXED_0] 
        checked_fixed_bits += [((b >> bit) & 1) == 1 for bit in s_con.MAPSPEED_BITS_FIXED_1]
        speed_bit = (b >> s_con.MAPSPEED_BIT_SPEED) & 1
        exBit = (b >> s_con.MAPSPEED_BIT_EX) & 1
        specialROMBit = (b >> s_con.MAPSPEED_BIT_SPECIAL)  & 1
        hiBit = (b >> s_con.MAPSPEED_BIT_HI_LO) & 1

        if False in checked_fixed_bits:
            raise ImportError("-> invalid fixed bits")

        map_mode_label = None
        if exBit:
            if hiBit == s_con.HI_LO_MODE_HIROM:
                map_mode_label = s_con.LABEL_ROM_EXHI
            else:
                raise ImportError("-> loRom mode cannot have extended hiRom mode enabled")
        else:
            map_mode_label = s_con.HI_LO_MODE_LABELS[hiBit]
            
        
        speed_label = s_con.SPEED_MODE_LABELS[speed_bit]

        special_rom_label = None
        if specialROMBit:
            if hiBit:
                if exBit:
                    special_rom_label = s_con.LABEL_ROM_UNKN
                else:
                    special_rom_label = s_con.LABEL_ROM_SA_1
            else:
                special_rom_label = s_con.LABEL_ROM_SDD_1
    return map_mode_label, speed_label, special_rom_label # todo make is a dictionary

def decode_ex_header_flag(flag_byte):
    if len(flag_byte) != 1:
        raise ImportError(f"flag_byte longer than expected (1). was {flag_byte}")
    byte_decoder = bd.DECODER_MAP[bd.ENCODING_BYTE]
    return byte_decoder(flag_byte) == s_con.VALUE_EX_HEADER_FLAG, byte_decoder(flag_byte)

def decode_chipset(chipset_byte):
    if len(chipset_byte) != 1 or not isinstance(chipset_byte, bytes):
        raise ImportError(f"chipset_byte is unexpected value. was expecting 1 byte of type bytes, got {chipset_byte}")
    nibble_decoder = bd.DECODER_MAP[bd.ENCODING_BYTE_NIBBLES]
    results = {}

    coprocessor_nibble, chipset_nibble = nibble_decoder(chipset_byte)
    decoded_chipset = s_con.CHIPSET_DICTIONARY[chipset_nibble]
    results[s_con.LABEL_CHIPSET] = (chipset_nibble, decoded_chipset)
    
    # decoded_coprocessor = None
    if chipset_nibble in s_con.CHIPSETS_WITH_COPROCESSOR:
        decoded_coprocessor = s_con.COPROCESSOR_DICTIONARY[coprocessor_nibble]
        results[s_con.LABEL_CHIPSET] = (coprocessor_nibble, decoded_coprocessor)
        
    elif coprocessor_nibble != 0x0:
        raise ImportError(f"coprocessor_nibble is unexpected value. was expecting {0x0}, got {coprocessor_nibble}")
    
    # chipset, coprocessor = "",""
    # print(results)
    return results
    


DECODER_MAP = bd.DECODER_MAP
DECODER_MAP.update(dict([
    [s_con.LABEL_MAPSPEED, decodeMapSpeed],
    [s_con.LABEL_CHIPSET, decode_chipset],
    [s_con.LABEL_EX_HEADER_FLAG, decode_ex_header_flag]
]))