# Import sys module to get commandline arguments
import sys

import os

# Import module to get Sequence object for validation
import collections.abc

# Import snes_checksum module to use checksum functions
import snes_checksum as sc

# import snes_checksum_b as sc

# Define some constants
MAX_UNSIGNED_16BIT_INT = 0xFFFF
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
        rom_data_offset = 0
        if self.copierHeader == "Leading":
            p_msg("applying Leading Copier Header byte offset")
            rom_data_offset = COPIER_HEADER_SIZE
        
        
        with open(self.filename, 'rb') as f:
            f.seek(rom_data_offset, os.SEEK_SET)
            dataToCheck = f.read()


        dataLen = len(dataToCheck)
        checksum = None
        if sc.is_power_of_two(f_size):
            # p_msg(f"actual ROM Size is n^2: {dataLen=}")
            checksum = sc.calc_16bit_checksum(dataToCheck)
        else:
            # p_msg(f"actual ROM Size requires complex checksum: {dataLen=}")
            checksum = sc.calc_complex_checksum(dataToCheck, checkSumMethod)
        return hex(checksum)
    
    def validate(self):
        def compare_actual_to_expected(field_label, actual, expected, warn_only=False):
            comp_result = actual == expected
            error_label = "Error"
            if warn_only:
                error_label = "Warning"

            if not comp_result:
                p_msg(f"  ➡  {field_label}: ✖")
                p_msg(f"     {error_label}: Invalid {field_label} [Actual, Expected] [{actual}, {expected}]")
                if not warn_only:
                    self.valid = lambda : False
            else:
                p_msg(f"  ➡  {field_label}: ✔\t[{actual}:{type(actual)}]")
            return comp_result

        VALIDATION_FIELDS = {
            'MAP_MODE': {'LABEL':"Map Mode"},
            'CHECKSUM' : {'LABEL': "Checksum"},
            'COMPLEMENT' : {'LABEL' : "Complement"}
        }

        #Check 01 - Does the memory map stored at initialization, based on offset (actual) 
        #           match the memory map read from the file (excepted)
        expectMapLabel = self.memoryMap
        actualMapLabel = None
        mapSpeedByte = self.decodeField("Map/Speed")
 
        for sf in mapSpeedByte:
            if sf.label == VALIDATION_FIELDS['MAP_MODE']['LABEL']:
                actualMapLabel = sf.value()
                break
        if not compare_actual_to_expected(VALIDATION_FIELDS['MAP_MODE']['LABEL'], actualMapLabel, expectMapLabel):
            return self.valid()

        #Check 02 - Do the checksum/complement calculated off file's bytes (actual) 
        #           match the checksum/complement read from the file
        for cs_mode in ['nesdev', 'sneslab']:
            cs_label = VALIDATION_FIELDS['CHECKSUM']['LABEL']
            cs_actual = self.calculateCheckSum(cs_mode)
            cs_expected = self.decodeField(cs_label)
            cs_result = compare_actual_to_expected(
                f"{cs_label} ({cs_mode})", cs_actual, cs_expected, warn_only=True
            )
            
            #TODO Remove all hex conversion from storing integers and comparing them for the checksums to be less gross
            if cs_result:
                complmt_label = VALIDATION_FIELDS['COMPLEMENT']['LABEL']
                new_var = int(cs_actual,16)
                # print(f"{new_var=}:{type(new_var)=};{cs_actual=}:{type(cs_actual)=}")
                complmt_actual = ~new_var & MAX_UNSIGNED_16BIT_INT
                complmt_expected = self.decodeField(complmt_label)
                compare_actual_to_expected(
                    f"{complmt_label} ({cs_mode})", hex(complmt_actual), complmt_expected, warn_only=True
                )

        #Check 03.* - Confirm the validity of the extended header, if one is provided.

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
            self.decoder = lambda self : hex(int.from_bytes(self.rawData, 'little')) 
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
