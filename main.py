# Import sys module to get commandline arguments
import sys
import os

from snes_header import SNESHeader

invalid_files = {}
valid_files = {}

def print_help():
    print("\tNeeds a valid SNES ROM as an argument")

def print_headers():
    print(f"*****VALID ROMS [Total: {len(valid_files.keys())}]****")
    #TODO only print log if requested
    for f, h in valid_files.items():
        print(f"{h.validation_log()}\n")
    #TODO print header as well

def print_file_errors():
    print(f"*****INVALID ROMS [Error Type Total: {len(invalid_files.keys())}]****")
    for e, f_list in invalid_files.items():
        print(f"  **Error '{e}' [Total {len(f_list)}]**\n  ➡  Found in files:")
        for f_name in f_list:
            print(f"\t  ➡  {f_name}")


def process_file(file_path):
    try:
        header = SNESHeader(file_path)
        valid_files[file_path] = header
    except Exception as e:
        # invalid_files[file_path] = e
        e_string = f"{e}"
        # print(e_string)
        if not (e_string in invalid_files):
            invalid_files[e_string] = []
        invalid_files[e_string].append(file_path)

def __main__():
    f_path = sys.argv[1] if len(sys.argv) == 2 else None
    if f_path != None:
        if os.path.isfile(f_path):
            process_file(f_path)
        elif os.path.isdir(f_path):
            for fp_file in os.listdir(f_path):
                full_file_path = os.path.join(f_path, fp_file)
                if os.path.isfile(full_file_path):
                    process_file(full_file_path)
        print_headers()
        print_file_errors()
    else:
        print_help()

#executiion block
__main__()
exit()