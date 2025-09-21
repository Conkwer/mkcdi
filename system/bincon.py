#!/usr/bin/env python3
"""
0WINCEOS.BIN -> 1ST_READ.BIN Converter v2 (Enhanced)

usage: bincon.py <0WINCEOS.BIN file> <IP.BIN filename> [--replace]
example: bincon.py 0WINCEOS.BIN IP.BIN --replace

Features:
1. Converts 0WINCEOS.BIN to proper 1ST_READ.BIN format
2. Removes WINCE flag from IP.BIN (sets byte 0x3E to 0x30)
3. Optional: Replace original 0WINCEOS.BIN with converted version

Works on:
- Midway Arcade Classics - 100%
- Sega Rally 2 - 100%
- Rearview Mirror WinCE Dev Kit Demo - 100%
"""

import sys
import os
import argparse

def remove_wince_flag(bootsector_path):
    """Remove WINCE flag from IP.BIN by setting byte 0x3E to 0x30"""
    try:
        with open(bootsector_path, 'r+b') as bootsector_file:
            bootsector_file.seek(0x3E)
            current_byte = bootsector_file.read(1)
            
            if current_byte == b'\x30':
                print(f"WINCE flag already removed from {bootsector_path}")
                return True
                
            bootsector_file.seek(0x3E)
            bootsector_file.write(b'\x30')
            print(f"Removed WINCE flag from {bootsector_path} (set byte 0x3E to 0x30)")
            return True
            
    except Exception as e:
        print(f"Error modifying {bootsector_path}: {e}")
        return False

def convert_binary(input_path, output_path):
    """Convert 0WINCEOS.BIN to 1ST_READ.BIN format"""
    try:
        with open(input_path, 'rb') as binary_in:
            # Get file size
            binary_in.seek(0, os.SEEK_END)
            lsize = binary_in.tell()
            binary_in.seek(0)
            
            # Check if already converted
            binary_in.seek(lsize - 0x1000)
            chunk1 = binary_in.read(0x800)
            
            binary_in.seek(lsize - 0x800)
            chunk2 = binary_in.read(0x800)
            
            if chunk1 == chunk2:
                print(f"{input_path} is already in converted format")
                return False
                
            # Read and convert the binary
            binary_in.seek(0x800)
            binary_data = binary_in.read(lsize - 0x800)
            
            # Write converted binary
            with open(output_path, 'wb') as binary_out:
                binary_out.write(binary_data)
                binary_out.write(binary_data[-0x1000:-0x800])  # Append last 2k again
            
            print(f"Successfully converted {input_path} to {output_path}")
            return True
            
    except Exception as e:
        print(f"Error converting {input_path}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Convert 0WINCEOS.BIN to 1ST_READ.BIN format and remove WINCE flag from IP.BIN')
    parser.add_argument('binary_file', help='Path to 0WINCEOS.BIN file')
    parser.add_argument('ip_bin_file', help='Path to IP.BIN file')
    parser.add_argument('--replace', action='store_true', help='Replace original 0WINCEOS.BIN with converted version')
    parser.add_argument('--output', help='Optional output filename (default: 1ST_READ.BIN)')
    
    args = parser.parse_args()
    
    # Set output filename
    output_filename = args.output if args.output else "1ST_READ.BIN"
    
    # Remove WINCE flag from IP.BIN
    if not remove_wince_flag(args.ip_bin_file):
        return 1
    
    # Convert the binary
    if not convert_binary(args.binary_file, output_filename):
        return 1
    
    # Optional: Replace original file
    if args.replace:
        try:
            os.remove(args.binary_file)
            os.rename(output_filename, args.binary_file)
            print(f"Replaced original {args.binary_file} with converted version")
        except Exception as e:
            print(f"Error replacing file: {e}")
            return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())