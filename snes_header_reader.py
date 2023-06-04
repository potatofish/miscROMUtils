# Import sys module to get commandline arguments
import sys

# Import snes_checksum module to use checksum functions
import snes_checksum as sc

# Define some constants
H_SIZE = 64 # Header size in bytes
H_OFFS = [0x_7F_C0, 0x_FF_C0, 0x_40_FF_C0] # Header offsets in ROM file
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

# Loop through the possible header offsets
for offs in H_OFFS:
    if offs < f_size: # If the offset is within bounds
        p_msg(f"Trying header at offset {hex(offs)}...")
        cs = r_word(rom_file,offs+C_OFFS) # Read the checksum from the header
        cs_cpl = r_word(rom_file,offs+CC_OFFS) # Read the checksum complement from the header
       
        map_mode = r_byte(rom_file,offs+MAP_MODE_OFFSET) & 0xF7 # Read and mask the map mode from the header
       
        cs_func = cs_map.get(map_mode) # Get the checksum function from the map
       
        if cs_func: # If there is a matching function 
           cs_calc = cs_func(rom_file,f_size) # Calculate the checksum of the ROM file 
        else: # Unknown map mode 
            p_msg(f"Warning: Unknown map mode {hex(map_mode)}.") # Print the unknown map mode
            cs_calc = 0 # Set the calculated checksum to zero
       
        for name, size, enc in H_FIELDS: # Loop through the header fields to read and print them 
            rom_file.seek(offs) # Seek to the offset of the header 
            data = rom_file.read(size) # Read the data of the field 
            if enc == "ascii": data = data.decode("ascii") # Decode as ASCII if needed 
            elif enc == "hex": data = hex(ord(data)) # Convert to hex if needed 
            elif enc == "latin1": data.decode("latin1") # Convert to hex if needed 
            p_msg(f"{name}: {data}") # Print the name and data of the field 
        
        if cs == cs_calc and cs_cpl == (cs^0xFFFF): # If both match 
            p_msg("Valid header!")
            p_msg(f"Checksum: {hex(cs)}")
            p_msg(f"Checksum complement: {hex(cs_cpl)}")
            break # Break the loop 
        else:
            p_msg("Warning: Invalid checksum or checksum complement.")
            p_msg("Invalid header!")
            p_msg(f"Checksum (expected vs actual): {hex(cs)} / {hex(cs_calc)} [{cs}/{cs_calc}]")
            p_msg(f"Checksum complement (expected vs actual): {hex(cs_cpl)} / {hex(cs^0xFFFF)}")
    else:
        p_msg(f"Offset {hex(offs)} is out of bounds.")
 
#  Close the file
rom_file.close()
