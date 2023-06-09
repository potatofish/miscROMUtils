import field_definition as fd
from header_buffer import HeaderBuffer
import snes_constants as s_con
import snes_checksum as s_cs
import snes_byte_decoders as s_bd
import byte_decoders as bd
import os

class SNESHeader:
    def __init__(self, file_name):
        fields = [fd.FieldDefinition(name, length) for name, length in s_con.HEADER_FIELDS]
        
        self.file_name = file_name
        with open(self.file_name, 'rb') as f:
            for mm, raw_offs  in s_con.HEADER_OFFSETS.items():
                for offs in [raw_offs, raw_offs + s_con.COPIER_HEADER_SIZE]:
                    f.seek(offs,os.SEEK_SET)
                    binary_data = f.read()
                    self.memory_map = mm
                    hb = HeaderBuffer(binary_data, fields)
                    # hb.print_raw()
                    self.buffer = hb.buffer
                    self.valid = lambda : False
                    self.has_copier_header = raw_offs != offs #TODO try make function
                    self.validate()
                    if self.valid():
                        break
                if self.valid():
                    break
            if not self.valid():
                raise ImportError(f"Buffer Contents Does Not Conform to Memory Map: {mm}")

    def validate(self):
        comp = fd.compare_actual_to_expected #compare function

        #Check 01 - Does the memory map stored at initialization, based on
        #            offset (actual)  match the memory map read from the 
        #            file (excepted)
        ms_byte = self.buffer[s_con.LABEL_MAPSPEED]
        ms_decoder = s_bd.DECODER_MAP[s_con.LABEL_MAPSPEED]
        rom_map_mode = ms_decoder(ms_byte)[0]  # only need the map_mode, first returned
        # rom_map_mode = s_bd.decodeMapSpeed(mapSpeedByte)[0]  # only need the map_mode, first returned
        if not comp(s_con.LABEL_MAP_MODE, rom_map_mode, self.memory_map):
            return self.valid()

        #Check 02 - Do the checksum/1s-complement calculated off file's bytes (actual) 
        #           match the checksum/1s-complement read from the file
        int_decoder = s_bd.DECODER_MAP[bd.ENCODING_INT] #TODO - Re-add this to the Field list
        byte_decoder = s_bd.DECODER_MAP[bd.ENCODING_BYTE] #TODO - Re-add this to the Field list
        for cs_mode in ['nesdev', 'sneslab']:
            cs_actual = s_cs.calculate_check_sum(self.file_name, self.has_copier_header, cs_mode)
            cs_bytes = self.buffer[s_con.LABEL_CHECKSUM]
            cs_expected = int_decoder(cs_bytes)
            cs_comp_label = f"{s_con.LABEL_CHECKSUM} ({cs_mode})"
            cs_result = comp(cs_comp_label, cs_actual, cs_expected, warn_only=True, cb=hex)
            
            if cs_result:
                oc_actual = ~cs_actual & s_cs.MAX_UNSIGNED_16BIT_INT 
                oc_bytes = self.buffer[s_con.LABEL_COMPLEMENT]
                oc_expected = int_decoder(oc_bytes)
                oc_comp_label = f"{s_con.LABEL_COMPLEMENT} ({cs_mode})"
                comp(oc_comp_label, oc_actual, oc_expected, warn_only=True, cb=hex)

        #Check 03.* - Confirm the validity of the extended header, if one is provided.
        ex_flag_byte = self.buffer[s_con.LABEL_EX_HEADER_FLAG]
        ex_flag_decoder = s_bd.DECODER_MAP[s_con.LABEL_EX_HEADER_FLAG]
        ex_flag_bool, ex_flag_act = ex_flag_decoder(ex_flag_byte)
        comp("Has Ex Header?", ex_flag_bool,True, warn_only=True,cb=lambda x : hex(ex_flag_act))
        if ex_flag_bool:
            res_expected_byte = s_con.VALUE_EX_HEADER_RESERVED
            for rs_label in s_con.LABELS_EX_HEADER_RESERVED:
                rs_byte = self.buffer[rs_label]
                comp(rs_label, byte_decoder(rs_byte), res_expected_byte, warn_only=True, cb=hex)


        self.valid = lambda : True
        return self.valid()
