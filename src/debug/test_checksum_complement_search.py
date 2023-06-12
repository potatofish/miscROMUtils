import sys, os
from src.snes.snes_byte_decoders import  DECODER_MAP
from src.snes.snes_header import SNESHeader
from src.snes.snes_checksum import calculate_check_sum
from src.snes.snes_constants import NORMAL_HEADER_FIELDS, HEADER_FIELDS, EX_HEADER_FIELDS
from src.snes.snes_constants import COPIER_HEADER_SIZE, HEADER_OFFSETS
from src.snes.snes_constants import (
        LABEL_GAME_TITLE, LABEL_MAPSPEED, LABEL_CHIPSET, 
        LABEL_ROM_SIZE, LABEL_RAM_SIZE,
        LABEL_COUNTRY_CODE, LABEL_EX_HEADER_FLAG, LABEL_ROM_VERSION,
        LABEL_CHECKSUM, LABEL_COMPLEMENT
    )
from src.snes.snes_constants import LABEL_COUNTRY_UNKNOWN, LABEL_CHIP_RAM
from src.common.checksum import checksum_complement_search
from src.common.constants import BYTE_ORDER_LITTLE_ENDIAN as LITTLE_ENDIAN
from src.common.byte_decoders import ENCODING_JIS, ENCODING_BYTE, ENCODING_ASCII, ENCODING_INT
from src.common.header_buffer import HeaderBuffer


# HEADER_SIZE = 
def try_decode(raw_text, encoding):
    working_raw = raw_text[:len(raw_text)]
    # print(f"{working_raw}")
    decodeable_data = ""
    for i in range(len(raw_text)):
        byte = working_raw[:i]
        working_raw = working_raw[i:]
        try:
            decodeable_data += byte.decode(encoding)
        except Exception:
            pass
    return decodeable_data

def is_snes_header(file_path, byte_pos_of_checksum, mode='quiet'):
    # print(f"looking for header @ {hex(byte_pos_of_checksum)} in {file_path}")
    # Seek to pos-28 in the file
    hb = HeaderBuffer(NORMAL_HEADER_FIELDS)
    # hb = HeaderBuffer(HEADER_FIELDS)
    pre_checksum_byte_width = hb.get_byte_width(0,LABEL_CHECKSUM)
    offset = byte_pos_of_checksum - pre_checksum_byte_width
    extended_header_length = HeaderBuffer(EX_HEADER_FIELDS).get_byte_width()
    
    validity_score = 0

    with open(file_path, 'rb') as f:
         f.seek(offset)
         buffer_len = hb.get_byte_width()
         binary_data = f.read(buffer_len)
        #  print(f"raw_data@{hex(offset)}={binary_data}")
         hb.fill_buffer(binary_data,overflow=True)
         f.seek(0, os.SEEK_END)
         file_size = f.tell()
    
    # Read and decode bytes one by one until an invalid character is found
    # for i in hb.get_field_position
    # checksum, complement = hb.get_field_data([LABEL_CHECKSUM, LABEL_COMPLEMENT])
    # ",".join([f"{hex(var)}" for var in [checksum, complement]])
    # print(f"{','.join([f'{hex(var)}' for var in [checksum, complement]])}")
    # f_offset = offset
    # for i in range(hb.field_count()):
    #     f_label = hb.get_field_label_by_position(i)
    #     # print(f"{type(i)=}")

    #     f_rawdata = hb.get_field_data(i)
    #     print(f"{f_label}@{hex(f_offset)}={f_rawdata}")
    #     f_offset += len(f_rawdata)

    
    f_raw_title = hb.get_field_data(LABEL_GAME_TITLE)
    decodeable_title = try_decode(f_raw_title,ENCODING_JIS)
    
    
    if len(decodeable_title) != 21:
        if mode == 'debug' : 
            print (f"Invalid length for field='{LABEL_GAME_TITLE}' in Buffer @ {hex(offset)} {decodeable_title=}")
        validity_score = float('-inf')
        return [validity_score, hb]
    
    # print(f"{HEADER_FIELDS=}\n{NORMAL_HEADER_FIELDS=}")
    
    f_raw_ex_header_flag = hb.get_field_data(LABEL_EX_HEADER_FLAG)
    ex_flag_decoder = DECODER_MAP[LABEL_EX_HEADER_FLAG]
    ex_flag_bool, ex_flag_act = ex_flag_decoder(f_raw_ex_header_flag)
    if ex_flag_bool:
        ex_hb = HeaderBuffer(EX_HEADER_FIELDS)
        with open(file_path, 'rb') as f:
            f.seek(offset- extended_header_length)
            binary_data = f.read(extended_header_length)
            ex_hb.fill_buffer(binary_data,overflow=True)
            full_hb = hb.join(ex_hb, 0)
            print(f"{full_hb.get_values_as_dict()=}")

        # offset = byte_pos_of_checksum - pre_checksum_byte_width
        print(f"TODO - implement reading the extended header {extended_header_length=}")

    f_raw_map_speed = hb.get_field_data(LABEL_MAPSPEED)
    map_speed_decoder = DECODER_MAP[LABEL_MAPSPEED]
    try:
        map_speed_fields = map_speed_decoder(f_raw_map_speed)  # only need the map_mode, first returned
    except:
        if mode == 'debug' : 
            print (f"Invalid value for field='{LABEL_MAPSPEED}' in Buffer @ @ {hex(offset)} {f_raw_map_speed=}")
        validity_score = float('-inf')
        return [validity_score, hb]
    rom_memory_map, rom_speed_mode, rom_special_mode = map_speed_fields
    expected_rom_start_offset = HEADER_OFFSETS[rom_memory_map]
    start_of_rom_pos = offset - extended_header_length - expected_rom_start_offset
    if start_of_rom_pos < 0:
        validity_score = float('-inf')
        return [validity_score, hb]


    f_raw_chipset = hb.get_field_data(LABEL_CHIPSET)
    chipset_decoder = DECODER_MAP[LABEL_CHIPSET]
    try:
        rom_chipset = chipset_decoder(f_raw_chipset)  # only need the map_mode, first returned
    except:
        validity_score = float('-inf')
        return [validity_score, hb]
    
    f_raw_checksum = hb.get_field_data(LABEL_CHECKSUM)
    int_decoder = DECODER_MAP[ENCODING_BYTE]
    calculated_checksum = calculate_check_sum(file_path, start_of_rom_pos)
    if calculated_checksum == int_decoder(f_raw_checksum):
        print(f"VALID CHECKSUM - this ROM is {decodeable_title}")
        validity_score = float('inf')
        return [validity_score, hb]
    
    # all non-fuzzy validity checks have been applied

    byte_decoder = DECODER_MAP[ENCODING_BYTE]
    f_raw_rom_size = hb.get_field_data(LABEL_ROM_SIZE)
    BYTES_PER_KB = pow(2,10)
    decoded_rom_size = pow(2, byte_decoder(f_raw_rom_size)) * BYTES_PER_KB
    actual_rom_size = file_size - start_of_rom_pos
    if decoded_rom_size < actual_rom_size:
        validity_score -= 1
    elif decoded_rom_size > actual_rom_size:
        validity_score -= 5
    else: #they match
        validity_score += 2
    
    f_raw_ram_size = hb.get_field_data(LABEL_RAM_SIZE)
    MAX_RAM_SIZE_VALUE = 7
    decoded_ram_size_byte = byte_decoder(f_raw_ram_size)
    decoded_ram_size = pow(2, decoded_ram_size_byte) * BYTES_PER_KB
    if decoded_ram_size_byte > MAX_RAM_SIZE_VALUE:
        times_larger = decoded_ram_size_byte//MAX_RAM_SIZE_VALUE
        validity_score -= 5 * times_larger
    if not LABEL_CHIP_RAM in rom_chipset[LABEL_CHIPSET][1]: #todo fix this - I don't like this hard coded index
        validity_score -= 5 

    f_raw_country = hb.get_field_data(LABEL_COUNTRY_CODE)
    country_decoder = DECODER_MAP[LABEL_COUNTRY_CODE]
    rom_country = country_decoder(f_raw_country)  # only need the map_mode, first returned
    if rom_country != LABEL_COUNTRY_UNKNOWN:
        validity_score -= 1

    f_raw_rom_version = hb.get_field_data(LABEL_ROM_VERSION)
    validity_score -= byte_decoder(f_raw_rom_version)//10

    f_raw_complement = hb.get_field_data(LABEL_COMPLEMENT)

    def print_field(field_label, suffix):
        print(f"  ➡  {field_label}\t@{hex(offset+hb.get_byte_width(0,field_label))}\tis {suffix}")

    if mode != 'quiet':
        printable_list = [offset, expected_rom_start_offset, start_of_rom_pos, file_size]
        printables = list(map(hex, printable_list))
        printables.extend(list(map(lambda x : f"{x}", printable_list)))

        print(f"\npossible header @ {hex(byte_pos_of_checksum)} in {file_path} [{validity_score=}]")
        print(f"{pre_checksum_byte_width} bytes before pos is {hex(offset)} (pos_sans_copier={hex(offset-COPIER_HEADER_SIZE)})")
        print(f"[offset, expected_rom_start_offset, start_of_rom_pos, file_size]={printables}")
        print(f"  ➡  {LABEL_GAME_TITLE}\t@{hex(offset)}\tis {f_raw_title}:'{decodeable_title}'")
        print_field(LABEL_MAPSPEED, f"{f_raw_map_speed}: 0b{bin(int.from_bytes(f_raw_map_speed,LITTLE_ENDIAN))[2:].zfill(8)} maps to '{map_speed_fields}'")
        print_field(LABEL_CHIPSET, f"{f_raw_chipset}:'{hex(byte_decoder(f_raw_chipset))}' maps to '{rom_chipset}'")
        
        print_field(LABEL_ROM_SIZE, f"{f_raw_rom_size}:'{byte_decoder(f_raw_rom_size)}' meaning {decoded_rom_size}B (Actual is {actual_rom_size}B)")
        print_field(LABEL_RAM_SIZE, f"{f_raw_ram_size}:'{byte_decoder(f_raw_ram_size)}' meaning {decoded_ram_size}B")
        print_field(LABEL_COUNTRY_CODE, f"{f_raw_country}:'{byte_decoder(f_raw_ram_size)}' maps to '{rom_country}'")
        
        print_field(LABEL_EX_HEADER_FLAG, f"{f_raw_ex_header_flag}:'{hex(ex_flag_act)}'")
        
        print_field(LABEL_ROM_VERSION, f"{f_raw_rom_version}:'{byte_decoder(f_raw_rom_version)}'")
        print_field(LABEL_CHECKSUM, f"{f_raw_checksum}:'{hex(int_decoder(f_raw_checksum))} vs {hex(calculated_checksum)=}'")
        print_field(LABEL_COMPLEMENT, f"{f_raw_complement}:'{hex(int_decoder(f_raw_complement))}'")
        # print("")
    return [validity_score, hb]




def parse_search_results(file_path):
    candidates = {}
    for pos in checksum_complement_search(file_path):
        score, hb = is_snes_header(file_path, pos, 'normal')
        candidates[pos] = {'validity': score, 'buffer': hb}

    max_validity = float('-inf')
    max_pos = None
    for pos, candidate in candidates.items():
        if candidate['validity'] > max_validity:
            max_validity = candidate['validity']
            max_pos = pos
    most_valid_buffer = candidates[max_pos]['buffer']
    snes_header = SNESHeader(file_path, most_valid_buffer, max_pos)
    print(snes_header.validation_log())

    

def test_checksum_complement_search():
    if len(sys.argv) < 2:
        print("Usage: python debug.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]

    print(f"Searching for checksums and complements in {file_path}...")

    parse_search_results(file_path)
