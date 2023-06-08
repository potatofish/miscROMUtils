# Define named constants
VALID_ENDIANNESS = ['big', 'little']
MAX_UNSIGNED_16BIT_INT = 0xFFFF

def highest_bit_length(binary_data):
    length = len(binary_data)
    highest_bit = length.bit_length() - 1
    return pow(2,highest_bit)
        
def is_power_of_two(n):
    return (n != 0) and (n & (n-1) == 0)

def split_chip_data(data_to_split):
    firstROMChipLen = highest_bit_length(data_to_split)
    first_bytes = data_to_split[:firstROMChipLen]
    remaining_bytes = data_to_split[firstROMChipLen:]
    return first_bytes, remaining_bytes

def calc_complex_checksum(binary_data,checkSumMethod):
    def complexCheckSum_nesdev(binary_data):
        def makeZeroPadding(num_zero_bytes):
            zero_bytes = b'\x00' * num_zero_bytes
            return zero_bytes

        def makePaddedData(dataToPad):
            byteLen = len(dataToPad)
            if not is_power_of_two(byteLen):
                smallestPowerOfTwo = 2 ** byteLen.bit_length()
                dataToPad += makeZeroPadding(smallestPowerOfTwo - byteLen)
            return dataToPad
        
        first_bytes, second_bytes = split_chip_data(binary_data)
        padded_second_byte = makePaddedData(second_bytes) 
        checksum = calc_16bit_checksum(first_bytes + padded_second_byte + padded_second_byte) 
        return checksum

    def complexCheckSum_sneslab(binary_data):
        first_bytes, remaining_bytes = split_chip_data(binary_data)
        paddedData = None
        subchipLen = len(first_bytes)//len(remaining_bytes)
        # p_msg(f"{len(first_bytes)=},{len(remaining_bytes)=},{subchipLen=}")
        for i in range(subchipLen):
            if i == 0:
                paddedData = remaining_bytes
            else:
                paddedData += remaining_bytes
        checksum = (calc_16bit_checksum(first_bytes) + calc_16bit_checksum(paddedData)) & 0xFFFF
        return checksum

    checksum_functions = {
        'nesdev': complexCheckSum_nesdev, 
        'sneslab': complexCheckSum_sneslab
    }
    return checksum_functions[checkSumMethod](binary_data)


def check_parameter(name, type, value, check_function=None):
    type_check = isinstance(value, type)
    if not type_check:
        return False
    
    if check_function == None:
        return True
    
    if not check_function(value):
        raise ValueError(f'Invalid value for parameter {name} : {value[:20]}')

def check_sum_of_binary(binary_to_sum, endianness='little', byte_size=1, signed=False):
    # Check parameters
    check_parameter('binary_to_sum', bytes, binary_to_sum)
    check_parameter('endianness', str, endianness, lambda end_val : end_val in VALID_ENDIANNESS)
    check_parameter('byte_size', int, byte_size, lambda int_val : int_val > 0)
    check_parameter('signed', bool, signed)
    
    # Check that the length of binary_to_sum is divisible by byte_size
    if len(binary_to_sum) % byte_size != 0:
        raise ValueError(f'Invalid value for parameter {binary_to_sum} : {binary_to_sum[:20]}')
    
    # Initialize the sum of bytes to 0
    sum_of_bytes = 0
    
    # Iterate over the binary data in steps of byte_size
    for i in range(0, len(binary_to_sum), byte_size):
        # Get the next byte_size bytes
        current_bytes = binary_to_sum[i:i+byte_size]
        
        # Interpret the current bytes as an integer
        current_value = int.from_bytes(current_bytes,
                                    byteorder=endianness,
                                    signed=signed)
        
        # Add the current value to the sum of bytes and discard any overflow
        sum_of_bytes = (sum_of_bytes + current_value) & MAX_UNSIGNED_16BIT_INT
    
    # Calculate the one's complement of the sum of bytes
    ones_complement = ~sum_of_bytes & MAX_UNSIGNED_16BIT_INT
    
    # Return both the sum of bytes and its one's complement
    return sum_of_bytes, ones_complement


def check_data_sum(binary_to_sum):
    sum_of_bytes = 0
    for i in range(0, len(binary_to_sum), 2):
        # Get the next two bytes as a little-endian 16-bit integer
        value = int.from_bytes(binary_to_sum[i:i+2], byteorder='little', signed=False)
        # value = int.from_bytes(binary_data[i:i+2], byteorder='little', signed=True)
        # value = int.from_bytes(binary_data[i:i+2], byteorder='big', signed=False)
        # value = int.from_bytes(binary_data[i:i+2], byteorder='big', signed=True)
        # Add the value to the result and discard any overflow
        sum_of_bytes = (sum_of_bytes + value) & MAX_UNSIGNED_16BIT_INT
    
    ones_complement = ~sum_of_bytes & MAX_UNSIGNED_16BIT_INT
    return sum_of_bytes, ones_complement

def calc_16bit_checksum(binary_to_sum, mode='check_sum_of_binary'):
    mode_to_function = {
        'check_data_sum': check_data_sum,
        'check_sum_of_binary': check_sum_of_binary
    }
    if mode in mode_to_function:
        checkSum, complement = mode_to_function[mode](binary_to_sum)
        print(f"{hex(checkSum)=},{hex(complement)=},{type(checkSum)}")
        return checkSum
    raise ValueError('Invalid mode')