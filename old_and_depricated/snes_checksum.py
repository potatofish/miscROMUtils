# Define a function to calculate the checksum of a LoROM file
def cs_lorom(f,s):
    c = 0 # Initialize the checksum to zero
    b = 32768 # Set the bank size to 32KB
    o = 16384 # Set the offset to 16KB
    for i in range(s): # Loop through all bytes in the file
        a = (i % b) + o + ((i // b) * 65536) # Calculate the SNES address of the byte
        f.seek(a) # Seek to the SNES address
        c += ord(f.read(1)) & 0xFFFF # Add and mask the byte value to the checksum
    return c # Return the checksum

# Define a function to calculate the checksum of a HiROM file
def cs_hirom(f,s):
    c = 0 # Initialize the checksum to zero
    b = 65536 # Set the bank size to 64KB
    o = 0 # Set the offset to 0KB
    for i in range(s): # Loop through all bytes in the file
        a = (i % b) + o + ((i // b) * 65536) # Calculate the SNES address of the byte
        f.seek(a) # Seek to the SNES address
        c += ord(f.read(1)) & 0xFFFF # Add and mask the byte value to the checksum
    return c # Return the checksum

# Define a function to calculate the checksum of an ExHiROM file
def cs_exhirom(f,s):
    c = 0 # Initialize the checksum to zero
    b = 65536 # Set the bank size to 64KB
    o = 0 # Set the offset to 0KB
    for i in range(s): # Loop through all bytes in the file
        a = (i % b) + o + ((i // b) * 65536) # Calculate the SNES address of the byte
        if a >= 0x400000: a += 0xC00000 # Add an extra offset for banks above $40
        f.seek(a) # Seek to the SNES address
        c += ord(f.read(1)) & 0xFFFF # Add and mask the byte value to the checksum
    return c # Return the checksum

# Define a function to calculate the checksum of an SA-1 file
def cs_sa1(f,s):
    c = 0 # Initialize the checksum to zero
    b = 65536 # Set the bank size to 64KB
    o = 0 # Set the offset to 0KB
    for i in range(s): # Loop through all bytes in the file
        a = (i % b) + o + ((i // b) * 65536) # Calculate the SNES address of the byte
        if a >= 0x400000: a += 0x400000 # Add an extra offset for banks above $40
        f.seek(a) # Seek to the SNES address
        c += ord(f.read(1)) & 0xFFFF # Add and mask the byte value to the checksum
    return c # Return the checksum

# Define a function to calculate the checksum of an S-DD1 file
def cs_sdd1(f,s):
    c = 0 # Initialize the checksum to zero
    b = 32768 # Set the bank size to 32KB
    o = 16384 # Set the offset to 16KB
    for i in range(s): # Loop through all bytes in the file
        a = (i % b) + o + ((i // b) * 65536) # Calculate the SNES address of the byte
        if a >= 0x400000: a += 0x400000 # Add an extra offset for banks above $40
        f.seek(a) # Seek to the SNES address
        c += ord(f.read(1)) & 0xFFFF # Add and mask the byte value to the checksum
    return c # Return the checksum

# Define a function to calculate the checksum of a SuperFX file
def cs_superfx(f,s):
    c = 0 # Initialize the checksum to zero
    b = 32768 # Set the bank size to 32KB
    o = 8192 # Set the offset to 8KB
    for i in range(s): # Loop through all bytes in the file
        a = (i % b) + o + ((i // b) * 65536) # Calculate the SNES address of the byte
        if a >= 0x400000: a += 0x400000 # Add an extra offset for banks above $40
        f.seek(a) # Seek to the SNES address
        c += ord(f.read(1)) & 0xFFFF # Add and mask the byte value to the checksum
    return c # Return the checksum

def cs_spc7110(file, file_size):
    """Calculate the checksum of a SPC7110 ROM file."""
    file.seek(0) # Seek to the beginning of the file
    checksum = 0 # Initialize the checksum to zero
    while file.tell() < file_size: # While not at the end of the file
        byte = ord(file.read(1)) # Read a byte from the file
        checksum += byte # Add it to the checksum
        checksum &= 0xFFFF # Mask the checksum to 16 bits
    return checksum # Return the checksum
