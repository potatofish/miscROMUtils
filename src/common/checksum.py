from src.common.constants import BYTE_ORDER_LITTLE_ENDIAN as LITTLE_ENDIAN
from src.common.constants import LABEL_CHECKSUM
from src.common.constants import LABEL_COMPLEMENT
from src.common.constants import MAX_TWO_BYTE_INT
import os

def is_2byte_int(two_byte_int):
    return two_byte_int.bit_length() <= 16

def is_checksum(checksum, complement):
    def validate_2byte_int(two_byte_int, label="value"):
        if not is_2byte_int(two_byte_int):
            e_msg = f'Invalid byte-length for {f"{label}={two_byte_int}"}'
            raise ValueError(e_msg)
        
    validate_2byte_int(checksum, LABEL_CHECKSUM) 
    validate_2byte_int(complement, LABEL_COMPLEMENT)
   
    is_valid_sum = checksum + complement == MAX_TWO_BYTE_INT
    return is_valid_sum

def checksum_complement_search_fwd(f_handle,byte_order=LITTLE_ENDIAN):
    f_handle.seek(0,os.SEEK_END)
    file_size = f_handle.tell()
    f_handle.seek(0,os.SEEK_SET)

    def  two_byte_read_fwd():
        fh_pos = f_handle.tell()
        if file_size - fh_pos < 2:
            return False
        return [f_handle.read(2),fh_pos]

    checksum_two_byte_read = two_byte_read_fwd()
    if not checksum_two_byte_read:
        return
    checksum, checksum_pos = checksum_two_byte_read

    while f_handle.tell() < file_size:
        complement_two_byte_read = two_byte_read_fwd()
        if not complement_two_byte_read:
            return
        complement, complement_pos = complement_two_byte_read
        checksum_integer = int.from_bytes(checksum, byte_order)
        complement_integer = int.from_bytes(complement, byte_order)
        if is_checksum(checksum_integer, complement_integer):
            yield checksum_pos
        checksum, checksum_pos = complement, complement_pos

def checksum_complement_search_bkwd(f_handle, byte_order=LITTLE_ENDIAN):
    f_handle.seek(0,os.SEEK_END)

    def two_byte_read_bkwd():
        fh_pos = f_handle.tell()
        if fh_pos < 2:
            return False
        f_handle.seek(fh_pos - 2)
        return [f_handle.read(2), fh_pos - 2]
    
    complement_two_byte_read = two_byte_read_bkwd()
    if not complement_two_byte_read:
        return
    complement, complement_pos = complement_two_byte_read

    while complement_pos >= 0:
        checksum_two_byte_read = two_byte_read_bkwd()
        if not checksum_two_byte_read:
            return
        checksum, checksum_pos = checksum_two_byte_read
        checksum_integer = int.from_bytes(checksum, byte_order)
        complement_integer = int.from_bytes(complement, byte_order)
        if is_checksum(checksum_integer, complement_integer):
            yield checksum_pos
        complement, complement_pos = checksum, checksum_pos

CHECKSUM_SEARCH_FORWARD = 'forward'
CHECKSUM_SEARCH_BACKWARD = 'backward'
CHECKSUM_SEARCH_FUNCTIONS_DICTIONARY = {
    CHECKSUM_SEARCH_FORWARD : checksum_complement_search_fwd,
    CHECKSUM_SEARCH_BACKWARD : checksum_complement_search_bkwd
}

def checksum_complement_search(file_path,direction=CHECKSUM_SEARCH_FORWARD,byte_order=LITTLE_ENDIAN):
    try:
        with open(file_path, 'rb') as f:
            for result in CHECKSUM_SEARCH_FUNCTIONS_DICTIONARY[direction](f,byte_order):  
                yield result
    except FileNotFoundError:
        print(f"Error: File {file_path} not found")  
    except KeyError:
        print(f"Error: Invalid direction {direction}")

