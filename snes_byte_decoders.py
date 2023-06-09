from . import snes_constants as s_con
from . import byte_decoders as bd

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
    return map_mode_label, speed_label, special_rom_label

DECODER_MAP = bd.DECODER_MAP
DECODER_MAP += [s_con.LABEL_MAPSPEED , decodeMapSpeed]