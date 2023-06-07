# Import sys module to get commandline arguments
import sys

import os

# Import module to get Sequence object for validation
import collections.abc

# Import snes_checksum module to use checksum functions
import snes_checksum as sc

# Define some constants
H_SIZE = 64 # Header size in bytes
loROM_OFFSET = 0x_7F_C0
H_OFFS = [
   loROM_OFFSET, 
   0x_FF_C0, 
   0x_40_FF_C0
] # Header offsets in ROM file

SPEED_MODES = {
   0: {"l":"Slow"},
   1: {"l":"Fast"}
}

OFFSET_DICTIONARY = {
   0x_7F_B0: {"flag": 0, "l": "LoROM"},
   0x_FF_B0: {"flag": 1, "l": "HiROM"},
   0x_40_FF_B0: {"flag": 5, "l": "ExHiROM"}
}


def decodeByteAsInt(self):
    return ord(self.rawData)

def decodeByMap(val, map):
    # print(f"val/map:{0x00 == 0}/[{map}]")
    result = 'Unknown' 
    try:
        result = map[val]
    except:
        pass
    return result

#$00 - Japan; #$01 - USA; #$02 - Europe (enables 50fps PAL mode)
COUNTRY_DICTIONARY = {
    0x00 : 'Japan',  #0x00
    0x01 : 'USA',    #0x01
    0x02 : 'Europe'  #0x02
}
def decodeCountryCode(self):
    return decodeByMap(ord(self.rawData), COUNTRY_DICTIONARY)

# The expanded header's presence is indicate by putting $33 in $00FFDA, which is the developer ID. 
# Some early games may indicate just $00FFBF by setting $00FFD4 to zero.
# - https://snes.nesdev.org/wiki/ROM_header#Header_Verification
EXTENDED_HEADER_FLAG = 0x33
def decodeExHeaderFlag(self):
    hasExHeader = ord(self.rawData)
    return (hasExHeader == EXTENDED_HEADER_FLAG)

PASSFAIL_DICTIONARY = {
    True : '✔ - pass',
    False : '✖ - FAIL' 
}
def decodeFixedByte(self, fixedValue):
    return decodeByMap((ord(self.rawData) == fixedValue), PASSFAIL_DICTIONARY)

# Chipset subtype, used if chipset is $F0-$FF
# $00 - SPC7110, $01 - ST010/ST011, $02 - ST018, $03 - CX4
CHIP_SUBTYPE_DICTIONARY = {
    0x00 : 'SPC7110',
    0x01 : 'ST010/ST011',
    0x02 : 'ST018',
    0x03 : 'CX4'
}
def decodeSubHardware(self):
    return decodeByMap(ord(self.rawData), CHIP_SUBTYPE_DICTIONARY)


def decodeHardware(self):
    rawHW = self.rawData

    coprocessor = None
    hardware = None

    for b in rawHW:
        coprocessor = b >> 4
        hardware =  b & 0x0F

    hwLabel, cpLabel = None, None
    hwLabels = ["ROM"]
    if hardware in [1, 2, 4, 5]: hwLabels.append("RAM")
    if hardware in [2, 5, 6]: hwLabels.append("Battery")
    if hardware > 3: hwLabels.append("Co-Processor")
    
    hwLabel = ", ".join(hwLabels)

    result = [HeaderField("Hardware Flags",f"[3:0]",hardware,lambda self : hwLabel)]
    if hardware > 3:
        result.append(HeaderField("Co-Processor",f"[7:4]",coprocessor,lambda self : cpLabel))

    return result


def decodeByteAsKBSize(self):
    return f"{pow(2, ord(self.rawData))}kb"

def decodeMapSpeed(self):
    # print(f"Map/Speed - {}")
    rawData = self.rawData
    speedBit = None
    mapModeNibble = None
    if(len(rawData) != 1):
        raise MemoryError("Map/Speed byte was not read from memory correctly")

    for b in rawData:
        speedBit = (b >> 3) & 1
        exBit = (b >> 2) & 1
        specialROMBit = (b >> 1)  & 1
        hiBit = (b >> 0) & 1
        mapModeNibble = b & 0x0F

    if exBit == True and hiBit != True:
        raise ValueError("Invalid ROM - loRom mode cannot have extended hiRom mode enabled")
    
    modeLabel = "Unknown"
    # prn_tbl([hiBit, exBit, hiBit*pow(2,0), exBit*pow(2,2), (hiBit*pow(2,0)) + (exBit*pow(2,2))])
    for mm in OFFSET_DICTIONARY.values():
        if mm['flag'] == (hiBit*pow(2,0) + exBit*pow(2,2)):
            modeLabel = mm['l']
            break

    speedLabel = SPEED_MODES[speedBit]['l']

    result = [
        HeaderField("Speed Flag",f"[4]",speedBit,lambda self : speedLabel ),
        HeaderField("Map Mode",f"[3:0]",(hiBit*pow(2,0) + exBit*pow(2,2)),lambda self : modeLabel)
    ]

    if specialROMBit:
        specialLabel = None
        if hiBit:
            if exBit:
                specialLabel = "Unknown ROM"
            else:
                specialLabel = "SA-1 ROM"
        else:
            specialLabel = "SDD-1 ROM"

        result.append(HeaderField("Special ROM",f"[3:0]",mapModeNibble,lambda self : specialLabel))

    return result


HEADER_OFFSET = [0x_7F_B0]
HEADER_FIELDS = [
    ("Maker Code", 2, "ascii"), 
    ("Game Code", 4, "ascii"), 
    ("Fixed Byte[0]", 1, lambda self : decodeFixedByte(self,0x00)), 
    ("Fixed Byte[1]", 1, lambda self : decodeFixedByte(self,0x00)), 
    ("Fixed Byte[2]", 1, lambda self : decodeFixedByte(self,0x00)), 
    ("Fixed Byte[3]", 1, lambda self : decodeFixedByte(self,0x00)), 
    ("Fixed Byte[4]", 1, lambda self : decodeFixedByte(self,0x00)), 
    ("Fixed Byte[5]", 1, lambda self : decodeFixedByte(self,0x00)), 
    ("ExFlash Size", 1, decodeByteAsKBSize), 
    ("ExRAM Size", 1, decodeByteAsKBSize), 
    ("Special Version", 1, "hex"), 
    ("Cart SubType", 1, decodeSubHardware), 
    ("Game title", 21, "jisx0201"), 
    ("Map/Speed", 1, decodeMapSpeed), 
    ("Hardware", 1, decodeHardware), 
    ("ROM Size", 1, decodeByteAsKBSize), 
    ("RAM Size", 1, decodeByteAsKBSize), 
    ("Country Code", 1, decodeCountryCode), 
    ("Has ExHeader", 1, decodeExHeaderFlag), 
    ("ROM version", 1, lambda self : f"v{decodeByteAsInt(self)}.0"),
    ("Complement", 2, "int"), 
    ("Checksum", 2, "int") 
]
F_SIZE_M = 1024 # File size modulo to check for copier header
COPIER_HEADER_SIZE = 512 # Copier header size in bytes
C_OFFS = 0x_1C # Checksum offset in header
CC_OFFS = 0x_1E # Checksum complement offset in header
MAP_MODE_OFFSET = 0x_15 # Map mode offset in header
H_FIELDS = [ # Header fields to read and print
 ("Game title", 21, "ascii"), 
 ("Map mode", 1, "hex"), 
 ("Cart type", 1, "hex"), 
 ("ROM size", 1, "hex"), 
 ("RAM size", 1, "hex"), 
 ("Country", 1, "hex"), 
 ("Dev ID", 1, "hex"), 
 ("ROM ver", 1, "hex")
]

ROW_DELIM = "\t|\t"

def r_byte(file, offset):
 """Read a byte from a file at a given offset."""
 file.seek(offset) # Seek to the offset
 return ord(file.read(1)) # Return the byte value as integer


def r_word(file, offset):
 """Read a word (two bytes) from a file at a given offset."""
 file.seek(offset) # Seek to the offset
 return ord(file.read(1)) + (ord(file.read(1)) << 8) # Return the word value as integer


def p_msg(message):
    """Print a message to stdout with a newline."""
    sys.stdout.write(message + "\n") # Write the message with a newline

def prn_tbl(row):
    """Print a row (array) to stdout with a newline, dividing the inputs"""
    message = row.pop(0)
    for cell in row:
        # print(f"{cell}")
        message = f"{message}{ROW_DELIM}{cell}"
    p_msg(message) # Write the message with a newline

# Get the filename from the commandline argument or use a default one if not provided
fname = sys.argv[1] if len(sys.argv) > 1 else "rom.smc"

# Open the ROM file in binary mode
rom_file = open(fname,"rb")

# Get and adjust the file size in bytes if needed
f_size = rom_file.seek(0,2)
hasCopierHeader = f_size % F_SIZE_M == COPIER_HEADER_SIZE
if hasCopierHeader:
   p_msg("The ROM file has a copier header.")
#    f_size -= COPIER_HEADER_SIZE # Subtract its size from the file size

# Define a map of memory_map to checksum function
cs_map = {
 0x_20: sc.cs_lorom,
 0x_21: sc.cs_hirom,
 0x_23: sc.cs_sa1,
 0x_25: sc.cs_exhirom,
 0x_32: sc.cs_sdd1,
 0x_34: sc.cs_superfx,
 0x_54: sc.cs_spc7110, # Add this case for SPC7110 ROM files
}

class FileHeader():
    def __init__(self, filename, offset):
        f = open(filename,"rb")
        f_size = f.seek(0,2)
        self.copierHeader = None
        f_size % F_SIZE_M == COPIER_HEADER_SIZE
        
        if offset > f_size: # If the offset is within bounds 
            message = "Byte offset is outside memory of filename.\n"
            message += f"\tFile: {filename} (Size: {f_size})\n"
            message += f"\tOffset: {offs}\n"
            raise IndexError(message)

        self.filename = filename

        self.offset = offset
        mapOffset = None
        if self.offset in OFFSET_DICTIONARY:
            mapOffset = self.offset
            if (f_size % F_SIZE_M == COPIER_HEADER_SIZE):
                self.copierHeader = "Trailing"

        if mapOffset == None and ((self.offset - COPIER_HEADER_SIZE) in OFFSET_DICTIONARY):
            mapOffset = self.offset - COPIER_HEADER_SIZE
            self.copierHeader = "Leading"

        self.memoryMap = OFFSET_DICTIONARY[mapOffset]['l']

        self.fields = {}
        self.valid = lambda : False

        f.seek(offset)
        for name, size, enc in HEADER_FIELDS: # Loop through the header fields to read and print them 
            start = f.tell()
            data = f.read(size) # Read the data of the field 
            aField = HeaderField(name, hex(start), data, enc)
            # prn_tbl([f"{hex(start)}:{hex(start+size-1)}", name, aField.value])
            self.fields[name] = aField

        f.close()

    def decodeField(self, label):
        return self.fields[label].value()
    
    def calculateCheckSum(self, checkSumMethod='nesdev'):

        # Any number which is a power of two has exactly one bit set to 1. 
        # When you subtract 1 from it that bit flips to 0 & all preceding bits flip to 1
        def is_power_of_two(n):
            return (n != 0) and (n & (n-1) == 0)
        
        def check_data_sum(binary_data):
            summedData = 0
            for i in range(0, len(binary_data), 2):
                # Get the next two bytes as a little-endian 16-bit integer
                value = int.from_bytes(binary_data[i:i+2], byteorder='little', signed=False)
                # Add the value to the result and discard any overflow
                summedData = (summedData + value) & 0xFFFF
            return summedData
        
        def highest_bit_length(binary_data):
            length = len(binary_data)
            highest_bit = length.bit_length() - 1
            return pow(2,highest_bit)
        

        

        # padding_functions = {'nesdev': padPer_nesdev_org}
        # def padData(binary_data, padding_type='nesdev'):
        #     p_msg(f"{len(binary_data)=}")
        #     paddedData = padding_functions[padding_type](binary_data)
        #     if not is_power_of_two(len(paddedData)):
        #         raise ValueError("Resulting filesize is not a power of 2")
        #     return paddedData
 

        def complexCheckSum(binary_data,checkSumMethod):
            def split_chip_data(dataToCheck):
                firstROMChipLen = highest_bit_length(dataToCheck)
                first_bytes = dataToCheck[:firstROMChipLen]
                remaining_bytes = dataToCheck[firstROMChipLen:]
                return first_bytes, remaining_bytes
            
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
                checksum = check_data_sum(first_bytes + padded_second_byte + padded_second_byte) 
                return checksum

            def complexCheckSum_sneslab(binary_data):
                first_bytes, remaining_bytes = split_chip_data(binary_data)
                paddedData = None
                subchipLen = len(first_bytes)//len(remaining_bytes)
                p_msg(f"{len(first_bytes)=},{len(remaining_bytes)=},{subchipLen=}")
                for i in range(subchipLen):
                    if i == 0:
                        paddedData = remaining_bytes
                    else:
                        paddedData += remaining_bytes
                checksum = (check_data_sum(first_bytes) + check_data_sum(paddedData)) & 0xFFFF
                return checksum

            checksum_functions = {
                'nesdev': complexCheckSum_nesdev, 
                'sneslab': complexCheckSum_sneslab
            }
            return checksum_functions[checkSumMethod](binary_data)
        
        rom_data_offset = 0
        if self.copierHeader == "Leading":
            p_msg("applying Leading Copier Header byte offset")
            rom_data_offset = COPIER_HEADER_SIZE
        
        
        with open(self.filename, 'rb') as f:
            f.seek(rom_data_offset, os.SEEK_SET)
            dataToCheck = f.read()


        dataLen = len(dataToCheck)
        checksum = None
        if is_power_of_two(f_size):
            p_msg(f"actual ROM Size is n^2: {dataLen=}")
            checksum = check_data_sum(dataToCheck)
        else:
            p_msg(f"actual ROM Size requires complex checksum: {dataLen=}")
            checksum = complexCheckSum(dataToCheck, checkSumMethod)
        return hex(checksum)


    
    def validate(self):
        #Check 00.01 - Does the map mode decoded (actual) match 
        #              the map mode offset for (expected)
        expectMapLabel = self.memoryMap
        actualMapLabel = None
        mapSpeedByte = self.decodeField("Map/Speed")
        for sf in mapSpeedByte:
            if sf.label == "Map Mode":
                actualMapLabel = sf.value()
                break

        if actualMapLabel != expectMapLabel:
            p_msg("  ➡  Map Mode: ✖")
            p_msg(f"     Error: Invalid Map Mode [Actual, Expected] [{actualMapLabel}, {expectMapLabel}]")
            self.valid = lambda : False
            return self.valid()
        p_msg("  ➡  Map Mode: ✔")
        
        actualChecksum = self.calculateCheckSum()
        if self.decodeField("Checksum") != actualChecksum:
            p_msg("  ➡  Checksum: ✖")
            p_msg(f"     Warning: Invalid CheckSum [Actual, Expected] [{actualChecksum}, {self.decodeField('Checksum')}]")
        else:
            p_msg("  ➡  Checksum: ✔")

        actualChecksum2 = self.calculateCheckSum('sneslab')
        if self.decodeField("Checksum") != actualChecksum2:
            p_msg("  ➡  Checksum: ✖")
            p_msg(f"     Warning: Invalid CheckSum [Actual, Expected] [{actualChecksum2}, {self.decodeField('Checksum')}]")
        else:
            p_msg("  ➡  Checksum: ✔")
        
        self.valid = lambda : True
        return self.valid()
    
    def makeDict(self):
        if not self.valid():
            raise ImportError("Data was imported, but not validated")
        return {'0':"BOO"}

    def printField(self, label, raw=True):
        p_msg(f"{label} :{self.decodeField(label)}")

    def printFields(self, raw=True):
        h_line_short = "-------"
        h_line_long = "--------------"
        header_A = ["Address", "Field\t", "Value"]
        header_B = [h_line_short, h_line_long, h_line_short]
        if raw:
            header_A.insert("RawBytes", 2)
            header_B.insert(h_line_short, 2)
        prn_tbl(header_A)
        prn_tbl(header_B)

        for field in self.fields.values():
            fieldData = [field.address, field.label]
            if raw:
                fieldData.append(field.rawData)
            if isinstance(field.value(), list):
                fieldData.append("...See Sub-Byte Fields On Next Lines")
                prn_tbl(fieldData)
                for subField in field.value():
                    subFieldData = [f"^{subField.address}", subField.label, subField.value()]
                    if raw:
                        subFieldData.insert(subField.rawData, 2)
                    prn_tbl(subFieldData)
            else:
                fieldData.append(field.value())
                prn_tbl(fieldData)

class HeaderField():
    # init method or constructor
    def __init__(self, l, a, r, enc):
        self.label = l
        self.address = a
        self.rawData = r
        if callable(enc):
            self.encoding = "user"
            self.decoder = enc
        else:
            self.encoding = enc
        # self.value = None

        if self.encoding == "ascii": 
            self.decoder = lambda self : self.rawData.decode("ascii") 
        elif self.encoding == "int" or self.encoding == "u_short": 
            self.decoder = lambda self : hex(int.from_bytes(self.rawData, 'big')) 
        elif self.encoding == "hex" or self.encoding == "byte": 
            self.decoder = lambda self : hex(ord(self.rawData)) # Convert to hex if needed 
        elif self.encoding == "jisx0201":
            self.decoder = lambda self : self.rawData.decode("shift_jis") # Convert to hex if needed 
        elif self.encoding == "latin1": 
            self.decoder = lambda self : self.rawData.decode("latin1") # Convert to hex if needed 
        elif self.encoding != "user":
            raise TypeError("Invalid Encoding") 
        
        # try:
        #     self.value = self.decoder(self)
        # except UnicodeDecodeError as e:
        #     raise TypeError(f"Decoder Failed to decode value\n\tMsg:\t{e}")

    def __repr__(self):
        return f"<HeaderField object:'{self.label}'>"

    def setDecoder(self, funct):
        self.decoder = funct

    def value(self):
        value = None
        try:
            value = self.decoder(self)
        except UnicodeDecodeError as e:
            raise TypeError(f"Decoder Failed to decode value\n\tMsg:\t{e}")
        return value

    def export(self):
        return [self.address, self.label, self.decode()]
    
def fillBuffer(fname, offs):
    header = None
    try:
        header = FileHeader(fname,offs)
    except (TypeError, IndexError) as e:
        p_msg(f"\tError for {hex(offs)}\n\t{e}")
    return header

for offs,value in OFFSET_DICTIONARY.items():
    p_msg(f"\nLooking for {value['l']} (Mode: {value['flag']}) header at offset {hex(offs)}:")
    header = fillBuffer(fname, offs)
    isValidHeader = (header != None)
    if(isValidHeader):
        isValidHeader = header.validate()

    if hasCopierHeader and not (isValidHeader):
        newOffset = offs+COPIER_HEADER_SIZE
        p_msg(f"\nLooking for {value['l']} (Mode: {value['flag']}) header at offset {hex(newOffset)}:")
        header = fillBuffer(fname, newOffset)
        isValidHeader = (header != None)
        if(isValidHeader):
            isValidHeader = header.validate()

    if isValidHeader:
        p_msg("\nValid Header Found\n--- PRINTING ---")
        for key, value in header.makeDict().items():
            prn_tbl([key, value])
        break

exit()

# Loop through the possible header offsets
header_buffer = None
header_buffer2 = None
for offs in HEADER_OFFSET:
    header_buffer = []
    header_buffer2 = []
    if offs < f_size: # If the offset is within bounds
        p_msg(f"Trying header at offset {hex(offs)}...")
        cs = r_word(rom_file,offs+C_OFFS) # Read the checkspyum from the header
        cs_cpl = r_word(rom_file,offs+CC_OFFS) # Read the checksum complement from the header
       
        map_mode = r_byte(rom_file,offs+MAP_MODE_OFFSET) & 0xF7 # Read and mask the map mode from the header
       
        # cs_func = cs_map.get(map_mode) # Get the checksum function from the map
       
        # if cs_func: # If there is a matching function 
        #    cs_calc = cs_func(rom_file,f_size) # Calculate the checksum of the ROM file 
        # else: # Unknown map mode 
        #     p_msg(f"Warning: Unknown map mode {hex(map_mode)}.") # Print the unknown map mode
        #     cs_calc = 0 # Set the calculated checksum to zero

        rom_file.seek(offs) # Seek to the offset of the header 
        prn_tbl(["Memory Address", "Field", "Value"])

        fieldTemplate = {
            "l": None,
            "address": None,
            "rawData" : None,
            "decoder" : None
        }

        for name, size, enc in HEADER_FIELDS: # Loop through the header fields to read and print them 
            start = rom_file.tell()
            data = rom_file.read(size) # Read the data of the field 
            # if size == 1 and int.from_bytes(data, 'big') != 0:
            # if name == "Map mode":
            #    for b in data:
            #       for i in range(8):
            #         bit = (b >> i) & 1
            def decodeMapMode(rawData):
                speedBit = None
                mapMode = 0
                for b in rawData:
                    for i in range(8):
                        bit = (b >> i) & 1
                        # print(f"bit{i}:{bit}")
                        if i == 4:
                            speedBit = bit
                        elif i < 4:
                            mapMode = mapMode << bit

                def decodeMapNibble(offset_key):
                    if OFFSET_DICTIONARY[offset_key]['flag'] == self.rawData:
                        return OFFSET_DICTIONARY[offset_key]['l']
                    else:
                        return None

                return [
                    HeaderField("Speed Flag",f"{hex(start)}@Bit:4", speedBit, lambda : SPEED_MODES[self.rawData]['l']),
                    HeaderField("Map Mode Nibble",f"{hex(start)}@Bits:3-0", mapMode, decodeMapNibble)
                ]
            
            if name == "Map mode":
                speedBit = None
                mapMode = 0
                for b in data:
                    for i in range(8):
                        bit = (b >> i) & 1
                        # print(f"bit{i}:{bit}")
                        if i == 4:
                            speedBit = bit
                        elif i < 4:
                            mapMode = mapMode << bit

            field = fieldTemplate
            field["l"] = name
            field['address'] = f"{hex(start)}:{hex(start+size-1)}"
            field["rawData"] = data
            field["decoder"] = lambda : None

            field2 = HeaderField(name, f"{hex(start)}:{hex(start+size-1)}", data, enc)
            header_buffer2.append(field2)

            # if enc == "ascii": data = data.decode("ascii") # Decode as ASCII if needed 
            # elif enc == "int": data = hex(int.from_bytes(data, 'big')) # Convert to hex if needed 
            # elif enc == "hex": data = hex(ord(data)) # Convert to hex if needed 
            # elif enc == "jisx0201": data.decode("shift_jis") # Convert to hex if needed 
            # elif enc == "latin1": data.decode("latin1") # Convert to hex if needed 
            if enc == "ascii": field["decoder"] = lambda : self["rawData"].decode("ascii") # Decode as ASCII if needed 
            elif enc == "int": data = hex(int.from_bytes(data, 'big')) # Convert to hex if needed 
            elif enc == "hex": data = hex(ord(data)) # Convert to hex if needed 
            elif enc == "jisx0201": data.decode("shift_jis") # Convert to hex if needed 
            elif enc == "latin1": data.decode("latin1") # Convert to hex if needed 
            pfx = f"[{field['address']}]\t::" # print message prefix
            pfx2 = f"[{hex(start)}:{hex(start+size-1)}]" # print message prefix
            # p_msg(f"{pfx}\t{name}\t::\t{data}") # Print the name and data of the field 
            header_buffer.append(field)
            prn_tbl([pfx2, name, data])
            
            if name == "Map mode":
                subFields = "->  speedBit"
                subFieldsMapped = f"{SPEED_MODES[speedBit]['l']}"
                subFieldsRaw = f"{speedBit}"
                prn_tbl([" ↑[0x\"*\":0x\"*\"]", subFields, f"{subFieldsMapped} [{subFieldsRaw}]"])

                subFields = "->  mapMode"
                subFieldsMapped = f"{OFFSET_DICTIONARY[offs]['l']}"
                subFieldsRaw = f"{mapMode}"
                prn_tbl([" ↑[0x\"*\":0x\"*\"]", subFields,  f"{subFieldsMapped} [{subFieldsRaw}]"])

                # p_msg(f"{pfx}\t\t ::\t \t::\t{speedBit}|{mapMode}")
                if OFFSET_DICTIONARY[offs]['flag'] != mapMode:
                    p_msg(f"{pfx}\tWARNING\t::\t{OFFSET_DICTIONARY[offs]['flag']} is expected mapMode") # Print the name and data of the field 
                   
        
        # if cs == cs_calc and cs_cpl == (cs^0xFFFF): # If both match 
        #     p_msg("Valid header!")
        #     p_msg(f"Checksum: {hex(cs)}")
        #     p_msg(f"Checksum complement: {hex(cs_cpl)}")
        #     break # Break the loop 
        # else:
        #     p_msg("Warning: Invalid checksum or checksum complement.")
        #     p_msg("Invalid header!")
        #     p_msg(f"Checksum (expected vs actual): {hex(cs)} / {hex(cs_calc)} [{cs}/{cs_calc}]")
        #     p_msg(f"Checksum complement (expected vs actual): {hex(cs_cpl)} / {hex(cs^0xFFFF)}")
    else:
        p_msg(f"Offset {hex(offs)} is out of bounds.")

#print results
for field in header_buffer2:
    prn_tbl([field.address, field.label, field.decode()])

    # print(f"XXX: {field.decode()}")
    # if enc == "ascii": data = data.decode("ascii") # Decode as ASCII if needed 
    # elif enc == "int": data = hex(int.from_bytes(data, 'big')) # Convert to hex if needed 
    # elif enc == "hex": data = hex(ord(data)) # Convert to hex if needed 
    # elif enc == "jisx0201": data.decode("shift_jis") # Convert to hex if needed 
    # elif enc == "latin1": data.decode("latin1") # Convert to hex if needed 
    # pfx = f"[{hex(start)}:{hex(start+size-1)}]\t::" # print message prefix
    # pfx2 = f"[{hex(start)}:{hex(start+size-1)}]" # print message prefix
    # # p_msg(f"{pfx}\t{name}\t::\t{data}") # Print the name and data of the field 
    # prn_tbl([pfx2, name, data])

#  Close the file
rom_file.close()
