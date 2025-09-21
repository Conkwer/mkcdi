#!/usr/bin/env python3
"""
0WINCEOS.BIN -> 1ST_READ.BIN Converter v2

usage: bincon.py <0WINCEOS.BIN file> <new 1ST_READ.BIN to create> <IP.BIN filename>
example: bincon.py 0WINCEOS.BIN 1ST_READ.BIN IP.BIN

It does what it says it does. Works on:
- Midway Arcade Classics - 100%
- Sega Rally 2 - 100%
- Rearview Mirror WinCE Dev Kit Demo - 100%

Source released under the GNU General Public License:
http://www.fsf.org/copyleft/gpl.html

by dopefish on 7/28/00
basic binary check by Shoometsu 1/26/08
Python rewrite
"""

import sys
import os

def main():
    # Argument check
    if len(sys.argv) != 4:
        print("\nUsage: bincon.py <0WINCEOS.BIN file> <new 1ST_READ.BIN to create> <IP.BIN filename>")
        print("Example: bincon.py 0WINCEOS.BIN 1ST_READ.BIN IP.BIN")
        return 1

    binary_in_path = sys.argv[1]
    binary_out_path = sys.argv[2]
    bootsector_path = sys.argv[3]

    try:
        # Open 0winceos.bin
        with open(binary_in_path, 'rb') as binary_in:
            # Get size of 0winceos.bin
            binary_in.seek(0, os.SEEK_END)
            lsize = binary_in.tell()
            binary_in.seek(0)
            
            # Try to do a very basic check for a file already converted
            binary_in.seek(lsize - 0x1000)
            chunk1 = binary_in.read(0x800)
            
            binary_in.seek(lsize - 0x800)
            chunk2 = binary_in.read(0x800)
            
            if chunk1 != chunk2:
                # File wasn't converted yet, so let's do it
                binary_in.seek(0x800)
                binary_data = binary_in.read(lsize - 0x800)
                
                # Read IP.BIN data
                with open(bootsector_path, 'rb') as bootsector_in:
                    bootsector_data = bootsector_in.read(0x8000)
                
                # Create 1ST_READ.BIN
                with open(binary_out_path, 'wb') as binary_out:
                    # Write full binary to file then the last 2k again
                    binary_out.write(binary_data)
                    binary_out.write(binary_data[-0x1000:-0x800])  # Last 2k again
                
                # Modify IP.BIN
                bootsector_modified = bytearray(bootsector_data)
                bootsector_modified[0x3E] = 0x30  # Set byte at offset 0x3E to 0x30
                
                with open(bootsector_path, 'wb') as bootsector_out:
                    bootsector_out.write(bootsector_modified)
                
                print(f"Successfully converted {binary_in_path} to {binary_out_path}")
                print(f"Modified {bootsector_path} with byte 0x30 at offset 0x3E")
            else:
                print(f"The file {binary_in_path} seems to be already converted. Nothing to do.")
                
    except FileNotFoundError as e:
        print(f"Error: cannot open file {e.filename}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())