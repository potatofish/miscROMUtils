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
        
        self.valid_log = ""
        self.valid_log +=  f"Decoding {file_name}\n"
        self.file_name = file_name
        with open(self.file_name, 'rb') as f:
            for mm, raw_offs  in s_con.HEADER_OFFSETS.items():
                for offs in [raw_offs, raw_offs + s_con.COPIER_HEADER_SIZE]:
                    f.seek(offs,os.SEEK_SET)
                    binary_data = f.read()
                    self.memory_map = mm
                    hb = HeaderBuffer(binary_data, fields)
                    # hb.print_raw()
                    self.valid_log += f"- trying for map {mm} @ {hex(offs)}\n"
                    self.encoded_header = hb
                    self.valid = lambda : False
                    self.has_copier_header = raw_offs != offs #TODO try make function
                    # self.valid_log += f"{self.validate(hb)}"
                    self.validate(hb)
                    if self.valid():
                        break
                if self.valid():
                    break
            if not self.valid():
                raise ImportError(f"Buffer Contents Does Not Conform to Memory Map: {mm}")
            
    def validation_log(self):
        log_copy = self.valid_log
        return log_copy

    def validate(self, header_buffer):
        def comp(l,a,e,ll,cb=lambda x : x): 
            result, log = fd.compare_actual_to_expected(l,a,e,ll,cb) #compare function
            self.valid_log += log
            return result
        
        buffer_dict = header_buffer.buffer
        int_decoder = s_bd.DECODER_MAP[bd.ENCODING_INT] #TODO - Re-add this to the Field list
        byte_decoder = s_bd.DECODER_MAP[bd.ENCODING_BYTE] #TODO - Re-add this to the Field list
        ascii_decoder = s_bd.DECODER_MAP[bd.ENCODING_ASCII] #TODO - Re-add this to the Field list
        jis_decoder = s_bd.DECODER_MAP[bd.ENCODING_JIS] #TODO - Re-add this to the Field list

        #Check 01 - Does the memory map stored at initialization, based on
        #            offset (actual)  match the memory map read from the 
        #            file (excepted)
        ms_byte = buffer_dict[s_con.LABEL_MAPSPEED]
        ms_decoder = s_bd.DECODER_MAP[s_con.LABEL_MAPSPEED]
        try:
            rom_map_mode = ms_decoder(ms_byte)[0]  # only need the map_mode, first returned
        except:
            return self.valid()
        # rom_map_mode = s_bd.decodeMapSpeed(mapSpeedByte)[0]  # only need the map_mode, first returned
        if not comp(s_con.LABEL_MAP_MODE, rom_map_mode, self.memory_map, fd.LOG_LEVEL_VERBOSE):
            return self.valid()

        #Check 02 - Do the checksum/1s-complement calculated off file's bytes (actual) 
        #           match the checksum/1s-complement read from the file
        for cs_mode in ['nesdev', 'sneslab']:
            cs_actual = s_cs.calculate_check_sum(self.file_name, self.has_copier_header, cs_mode)
            cs_bytes = buffer_dict[s_con.LABEL_CHECKSUM]
            cs_expected = int_decoder(cs_bytes)
            cs_comp_label = f"{s_con.LABEL_CHECKSUM} ({cs_mode})"
            cs_result = comp(cs_comp_label, cs_actual, cs_expected, fd.LOG_LEVEL_VERBOSE, cb=hex)
            
            if cs_result:
                oc_actual = ~cs_actual & s_cs.MAX_UNSIGNED_16BIT_INT 
                oc_bytes = buffer_dict[s_con.LABEL_COMPLEMENT]
                oc_expected = int_decoder(oc_bytes)
                oc_comp_label = f"{s_con.LABEL_COMPLEMENT} ({cs_mode})"
                comp(oc_comp_label, oc_actual, oc_expected, fd.LOG_LEVEL_VERBOSE, cb=hex)

        #Check 03 - Confirm the validity of the extended header, if one is provided.
        ex_flag_byte = buffer_dict[s_con.LABEL_EX_HEADER_FLAG]
        ex_flag_decoder = s_bd.DECODER_MAP[s_con.LABEL_EX_HEADER_FLAG]
        ex_flag_bool, ex_flag_act = ex_flag_decoder(ex_flag_byte)
        comp("Has Ex Header?", ex_flag_bool,True, fd.LOG_LEVEL_NORMAL,cb=lambda x : [format(ex_flag_act, '04x'), ex_flag_bool])
        if ex_flag_bool:
            res_expected_byte = s_con.VALUE_EX_HEADER_RESERVED
            for rs_label in s_con.LABELS_EX_HEADER_RESERVED:
                rs_byte = buffer_dict[rs_label]
                comp(rs_label, byte_decoder(rs_byte), res_expected_byte, fd.LOG_LEVEL_VERBOSE, cb=hex)

        #Check 04 - Confirm that all ASCII fields have ascii characters
        if ex_flag_bool:
            ascii_fields = [fd[0] for fd in s_con.EX_HEADER_ASCII_FIELDS]
            # print(f"{ascii_fields}")
            for as_field in ascii_fields:
                as_bytes = buffer_dict[as_field]
                try:
                    plain_text = ascii_decoder(as_bytes)
                    comp(as_field, as_field, as_field, fd.LOG_LEVEL_VERBOSE, cb=lambda x : f"'{plain_text}'")
                except:
                    print(f"{as_bytes=}")
                    return self.valid()

        jis_fields = [s_con.LABEL_GAME_TITLE]
        for jis_field in jis_fields:
            jis_bytes = buffer_dict[jis_field]
            try:
                plain_text = jis_decoder(jis_bytes)
                comp(jis_field, jis_field, jis_field, fd.LOG_LEVEL_VERBOSE, cb=lambda x : f"'{plain_text}'")
            except:
                # print(f"{jis_bytes=}:{jis_decoder=}")
                return self.valid()


        self.valid = lambda : True
        return self.valid()
