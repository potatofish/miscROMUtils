# Import sys module to get commandline arguments
import sys

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
   0x_7F_B0: {"flag": 0, "l": "LoRom"},
   0x_FF_B0: {"flag": 1, "l": "HiRom"},
   0x_40_FF_B0: {"flag": 5, "l": "ExHiRom"}
}

HEADER_OFFSET = [0x_7F_B0]
HEADER_FIELDS = [
    ("Maker Code", 2, "ascii"), 
    ("Game Code", 4, "ascii"), 
    ("Fixed Byte", 1, "hex"), 
    ("Fixed Byte", 1, "hex"), 
    ("Fixed Byte", 1, "hex"), 
    ("Fixed Byte", 1, "hex"), 
    ("Fixed Byte", 1, "hex"), 
    ("Fixed Byte", 1, "hex"), 
    ("Fixed Byte?", 1, "hex"), 
    ("Expansion RAM Size", 1, "hex"), 
    ("Special Version", 1, "hex"), 
    ("Cartridge Type (Sub-number)", 1, "hex"), 
    ("Game title", 21, "jisx0201"), 
    ("Map mode", 1, "hex"), 
    ("Cartridge type", 1, "hex"), 
    ("ROM size", 1, "hex"), 
    ("RAM size", 1, "hex"), 
    ("Country/Destination Code", 1, "hex"), 
    ("Fixed Byte", 1, "hex"), 
    ("ROM ver", 1, "hex"),
    ("Complement Check", 2, "int"), 
    ("Check Sum", 2, "int") 
]
F_SIZE_M = 1024 # File size modulo to check for copier header
H2_SIZE = 512 # Copier header size in bytes
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

ROW_DELIM = "::"

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
        message = f"{message}\t{ROW_DELIM}\t{cell}"
    p_msg(message) # Write the message with a newline

# Get the filename from the commandline argument or use a default one if not provided
fname = sys.argv[1] if len(sys.argv) > 1 else "rom.smc"

# Open the ROM file in binary mode
rom_file = open(fname,"rb")

# Get and adjust the file size in bytes if needed
f_size = rom_file.seek(0,2)
if f_size % F_SIZE_M == H2_SIZE: # If there is a copier header
   p_msg("The ROM file has a copier header.")
   f_size -= H2_SIZE # Subtract its size from the file size

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

class HeaderField():
    # init method or constructor
    def __init__(self, l, a, r, e):
        self.label = l
        self.address = a
        self.rawData = r
        self.encoding = e
        self.decoder = None

        if enc == "ascii": 
            self.decoder = lambda : self.rawData.decode("ascii") 
        elif enc == "int" or enc == "u_short": 
            self.decoder = lambda : hex(int.from_bytes(self.rawData, 'big')) 
        elif enc == "hex" or enc == "byte": 
            self.decoder = lambda : hex(ord(self.rawData)) # Convert to hex if needed 
        elif enc == "jisx0201":
            self.decoder = lambda : self.rawData.decode("shift_jis") # Convert to hex if needed 
        elif enc == "latin1": 
            self.decoder = lambda : self.rawData.decode("latin1") # Convert to hex if needed 
        elif enc != "user":
            raise TypeError("Invalid Encoding") 

    def setDecoder(self, funct):
        self.decoder = funct

    def decode(self):
        return self.decoder()

    def export(self):
        return [self.address, self.label, self.decode()]


# Loop through the possible header offsets
header_buffer = None
header_buffer2 = None
for offs in HEADER_OFFSET:
    header_buffer = []
    header_buffer2 = []
    if offs < f_size: # If the offset is within bounds
        p_msg(f"Trying header at offset {hex(offs)}...")
        cs = r_word(rom_file,offs+C_OFFS) # Read the checksum from the header
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
                return [
                    HeaderField("Speed Flag",f"{hex(start)}@Bit:4", speedBit, lambda : SPEED_MODES[self.rawData]['l']),
                    HeaderField("Map Mode Nibble",f"{hex(start)}@Bits:3-0", mapMode, lambda : SPEED_MODES[self.offset]['l'])
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
