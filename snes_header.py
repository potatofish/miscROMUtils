import field_definition as fd
from field_buffer import FieldBuffer
import snes_constants as s_con
import snes_checksum as s_cs
import os



class SNESHeader:
    def __init__(self, filename):
        fields = [fd.FieldDefinition(name, length) for name, length in s_con.HEADER_FIELDS]
        
        with open(filename, 'rb') as f:
            for mm, raw_offs  in s_con.HEADER_OFFSETS:
                for offs in [raw_offs, raw_offs + s_con.COPIER_HEADER_SIZE]:
                    f.seek(offs,os.SEEK_SET)
                    binary_data = f.read()
                    self.memory_map = mm
                    self.buffer = FieldBuffer(binary_data, fields, offs)
                    self.valid = lambda : False
                    self.has_copier_header = raw_offs != offs #TODO try make function
                    self.validate()
                    if self.valid():
                        break
                if self.valid():
                    break
            if not self.valid():
                raise ImportError(f"Buffer Contents Does Not Conform to Memory Map: {mm}")
    
    def calculateCheckSum(self, mode='nesdev'):
        rom_data_offset = 0
        if self.has_copier_header:
            print("applying Leading Copier Header byte offset")
            rom_data_offset = s_con.COPIER_HEADER_SIZE
        
        with open(self.filename, 'rb') as f:
            f.seek(rom_data_offset, os.SEEK_SET)
            f_binary_data = f.read() 

            f.seek(0, os.SEEK_END)
            f_size = f.tell()

        checksum = None
        if s_cs.is_power_of_two(f_size):
            checksum = s_cs.calc_16bit_checksum(f_binary_data)
        else:
            checksum = s_cs.calc_complex_checksum(f_binary_data, mode)
        return hex(checksum)

    def validate(self):
        #Check 01 - Does the memory map stored at initialization, based on offset (actual) 
        #           match the memory map read from the file (excepted)
        mapSpeedByte = self.buffer[s_con.LABEL_MAPSPEED]
        rom_map_mode = decodeMapSpeed(mapSpeedByte)[0]  # only need the map_mode, first returned
        if not fd.compare_actual_to_expected(s_con.LABEL_MAP_MODE, rom_map_mode, self.memory_map):
            return self.valid()

        #Check 02 - Do the checksum/complement calculated off file's bytes (actual) 
        #           match the checksum/complement read from the file
        for cs_mode in ['nesdev', 'sneslab']:
            cs_actual = self.calculateCheckSum(cs_mode)
            cs_expected = self.decodeField(s_con.LABEL_CHECKSUM)
            cs_result = fd.compare_actual_to_expected(
                f"{s_con.LABEL_CHECKSUM} ({cs_mode})", cs_actual, cs_expected, warn_only=True
            )
            
            #TODO Remove all hex conversion from storing integers and comparing them for the checksums to be less gross
            if cs_result:
                new_var = int(cs_actual,16)
                # print(f"{new_var=}:{type(new_var)=};{cs_actual=}:{type(cs_actual)=}")
                complmt_actual = ~new_var & s_cs.MAX_UNSIGNED_16BIT_INT
                complmt_expected = self.decodeField(s_con.LABEL_COMPLEMENT)
                fd.compare_actual_to_expected(
                    f"{s_con.LABEL_COMPLEMENT} ({cs_mode})", hex(complmt_actual), complmt_expected, warn_only=True
                )

        #Check 03.* - Confirm the validity of the extended header, if one is provided.

        self.valid = lambda : True
        return self.valid()
