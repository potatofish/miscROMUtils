# Import sys module to get commandline arguments
import sys

from snes_header import SNESHeader

def print_help():
    print("\tNeeds a valid SNES ROM as an argument")

fname = sys.argv[1] if len(sys.argv) == 2 else None
if fname != None:
    SNESHeader(fname)
else:
    print_help()
exit()

