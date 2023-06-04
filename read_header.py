# Import the struct and sys modules
import struct
import sys

# Import the os module to check if the file exists
import os

# Define a function to print a line of the table
def print_line(address, size, description):
    # Format the address, size and description as strings
    address = f"${address:06X}"
    size = f"{size} bytes"
    # Print the line with a pipe separator
    print(f"| {address} | {size} | {description} |")

# Define a function to read and print the header data
def read_header(filename):
    # Check if the file exists
    if os.path.isfile(filename):
        # The file exists, try to open it in binary mode
        try:
            with open(filename, "rb") as f:
                # Seek to the end of the file
                f.seek(0, 2)
                # Get the file size in bytes
                size = f.tell()
                # Check if the file size is a multiple of 32 KB
                if size % 0x8000 == 0:
                    # No external header, seek to the internal header location
                    f.seek(size - 0x8000 + 0xFFC0)
                    # Print the outcome and variables of the conditional logic
                    print(f"No external header detected. [File size: {size} bytes | Internal header location: {f.tell()} bytes] | Rem bytes to Read: {size - f.tell()}")
                else:
                    # External header present, check if it is 200 or 512 bytes
                    if size % 1024 == 512:
                        # 512-byte external header, seek to a different location
                        f.seek(size - 0x8000 + 0xFFC0 - 0x200 - 0x100)
                        # Print the outcome and variables of the conditional logic
                        print(f"512-byte external header detected. File size: {size} bytes. Internal header location: {f.tell()} bytes.")
                    else:
                        # 200-byte external header, seek to the normal location
                        f.seek(size - 0x8000 + 0xFFC0 - 0x200)
                        # Print the outcome and variables of the conditional logic
                        print(f"200-byte external header detected. File size: {size} bytes. Internal header location: {f.tell()} bytes.")
                # Read 32 bytes of header data
                data = f.read(32)
                # Check if the data has enough bytes to unpack
                if len(data) < 32:
                    # Not enough bytes, print an error message and exit
                    print(f"Error: The file {filename} does not have a valid header. The header data is too short ({len(data)} bytes instead of 32 bytes). Please check the file format and try again.")
                    return
                # Unpack the data into fields
                title = data[:21].decode("ascii")
                map_mode = data[21]
                rom_type = data[22]
                rom_size = data[23]
                ram_size = data[24]
                region = data[25]
                version = data[26]
                checksum_complement = struct.unpack(">H", data[27:29])[0]
                checksum = struct.unpack(">H", data[29:31])[0]
                # Print the table header
                print(f"Header data for {filename}:")
                print(f"| Address | Size | Description |")
                print(f"| --- | --- | --- |")
                # Print the lines of the table using a loop and a function
                fields = [(title, "game title"), (map_mode, "map mode"), (rom_type, "ROM type"), (rom_size, "ROM size"), (ram_size, "RAM size"), (region, "region"), (version, "version"), (checksum_complement, "checksum complement"), (checksum, "checksum")]
                address = 0xFFC0
                for value, name in fields:
                    print_line(address, len(value), f"{value} ({name})")
                    address += len(value)
        except IOError as e:
            # An error occurred while opening or reading the file, print an error message and exit
            print(f"Error: The file {filename} could not be opened or read. {e}. Please check the file permissions and try again.")
            return
    else:
        # The file does not exist, print an error message and exit
        print(f"Error: The file {filename} does not exist. Please check the file name and path and try again.")
        return

# Check if an argument was given
if len(sys.argv) > 1:
    # Use the first argument as the file name
    filename = sys.argv[1]
    # Call the function with the file name
    read_header(filename)
else:
    # No argument given, print an error message
    print("Please provide a file name as an argument.")