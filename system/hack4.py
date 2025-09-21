#!/usr/bin/env python3
"""
hack4.py - Dreamcast Binary Patcher Tool (Python Implementation)
A modern Python rewrite of kikuchan's hack4 v1.5 (2001/05/04)

This tool patches Dreamcast binaries to make CDI images bootable,
particularly useful for homebrew and translation patches.
"""

import argparse
import struct
import sys
import glob
import os
from pathlib import Path
from typing import List, Optional, Tuple


class Config:
    """Configuration class to hold all patch settings."""
    
    def __init__(self):
        self.old_pos: int = 0xafc8  # 45000 in decimal
        self.new_pos: int = 0x2db6  # 11702 in decimal
        self.hack0: bool = False
        self.hack1: bool = False
        self.hack2: bool = False
        self.hack3: bool = False
        self.unprotect: bool = False
        self.write_mode: bool = False


class DreamcastPatcher:
    """Main patcher class for Dreamcast binaries."""
    
    def __init__(self, config: Config):
        self.config = config
        
    def read_file(self, filename: str) -> bytes:
        """Read binary file and return its contents."""
        try:
            with open(filename, 'rb') as f:
                return f.read()
        except IOError as e:
            raise RuntimeError(f"Cannot read file {filename}: {e}")
    
    def write_file(self, filename: str, data: bytes) -> None:
        """Write binary data to file."""
        try:
            with open(filename, 'wb') as f:
                f.write(data)
        except IOError as e:
            raise RuntimeError(f"Cannot write file {filename}: {e}")
    
    def find_pattern(self, data: bytes, pattern: bytes) -> List[int]:
        """Find all occurrences of a pattern in data."""
        positions = []
        start = 0
        while True:
            pos = data.find(pattern, start)
            if pos == -1:
                break
            positions.append(pos)
            start = pos + 1
        return positions
    
    def find_uint32_value(self, data: bytes, value: int) -> List[int]:
        """Find all occurrences of a 32-bit little-endian value."""
        pattern = struct.pack('<I', value)
        return self.find_pattern(data, pattern)
    
    def replace_uint32_at_offset(self, data: bytearray, offset: int, new_value: int) -> None:
        """Replace 32-bit little-endian value at specific offset."""
        packed_value = struct.pack('<I', new_value)
        data[offset:offset+4] = packed_value
    
    def apply_unprotect_patch(self, data: bytearray) -> bool:
        """
        Apply unprotect patch: CD E4 43 6A -> 09 00 09 00
        
        This patch removes copy protection checks in Dreamcast binaries.
        The original bytes (CD E4 43 6A) represent an interrupt call,
        replaced with NOPs (09 00 09 00) to bypass the protection.
        """
        unprotect_pattern = bytes([0xCD, 0xE4, 0x43, 0x6A])
        unprotect_replace = bytes([0x09, 0x00, 0x09, 0x00])
        
        positions = self.find_pattern(data, unprotect_pattern)
        patched = False
        
        for pos in positions:
            print(f"Found unprotect pattern at offset: 0x{pos:x}")
            if self.config.write_mode:
                data[pos:pos+4] = unprotect_replace
                print("Applied unprotect patch")
                patched = True
            else:
                print("Would apply unprotect patch (use -w to write)")
        
        return patched
    
    def apply_position_patches(self, data: bytearray) -> bool:
        """
        Apply position-based patches (HACK0, HACK1, HACK2, HACK3).
        
        These patches modify memory addresses in the binary to relocate
        code or data structures. This is often needed when integrating
        translation patches or homebrew code that changes the binary layout.
        """
        patched = False
        
        # HACK0: Direct position replacement
        if self.config.hack0:
            positions = self.find_uint32_value(data, self.config.old_pos)
            for pos in positions:
                print(f"Found old position (HACK0) at offset: 0x{pos:x}")
                if self.config.write_mode:
                    self.replace_uint32_at_offset(data, pos, self.config.new_pos)
                    print("Applied HACK0 patch")
                    patched = True
                else:
                    print("Would apply HACK0 patch (use -w to write)")
        
        # HACK1: oldpos + 166 -> newpos + 166
        if self.config.hack1 or self.config.hack3:
            target_value = self.config.old_pos + 166
            replacement_value = self.config.new_pos + 166
            positions = self.find_uint32_value(data, target_value)
            for pos in positions:
                print(f"Found old position + 166 (HACK1) at offset: 0x{pos:x}")
                if self.config.write_mode:
                    self.replace_uint32_at_offset(data, pos, replacement_value)
                    print("Applied HACK1 patch")
                    patched = True
                else:
                    print("Would apply HACK1 patch (use -w to write)")
        
        # HACK2: oldpos + 150 -> newpos + 150
        if self.config.hack2 or self.config.hack3:
            target_value = self.config.old_pos + 150
            replacement_value = self.config.new_pos + 150
            positions = self.find_uint32_value(data, target_value)
            for pos in positions:
                print(f"Found old position + 150 (HACK2) at offset: 0x{pos:x}")
                if self.config.write_mode:
                    self.replace_uint32_at_offset(data, pos, replacement_value)
                    print("Applied HACK2 patch")
                    patched = True
                else:
                    print("Would apply HACK2 patch (use -w to write)")
        
        return patched
    
    def process_file(self, filename: str) -> None:
        """Process a single file with the configured patches."""
        try:
            print(f"Processing: {filename}")
            
            # Read the file
            data_bytes = self.read_file(filename)
            data = bytearray(data_bytes)
            
            # Apply patches
            patched = False
            
            if self.config.unprotect:
                if self.apply_unprotect_patch(data):
                    patched = True
            
            if any([self.config.hack0, self.config.hack1, self.config.hack2, self.config.hack3]):
                if self.apply_position_patches(data):
                    patched = True
            
            # Write back if in write mode and patches were applied
            if self.config.write_mode and patched:
                self.write_file(filename, bytes(data))
                print(f"Successfully patched: {filename}")
            
            print(f"Finished: {filename}\n")
            
        except Exception as e:
            print(f"Error processing {filename}: {e}", file=sys.stderr)


def expand_wildcards(patterns: List[str]) -> List[str]:
    """Expand wildcard patterns to actual file paths."""
    files = []
    for pattern in patterns:
        expanded = glob.glob(pattern)
        if expanded:
            files.extend(expanded)
        else:
            # If no wildcard match, add the pattern as-is (might be a direct filename)
            files.append(pattern)
    
    # Remove duplicates and ensure files exist
    unique_files = []
    for f in files:
        if f not in unique_files and os.path.isfile(f):
            unique_files.append(f)
    
    return unique_files


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="Dreamcast Binary Patcher Tool - Python Implementation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This tool patches Dreamcast binaries (typically ip.bin or 1st_read.bin) to make
CDI images bootable. It's commonly used for integrating translation patches or
homebrew code that modifies the binary layout.

Examples:
  python hack4.py -0 -w ip.bin           # Apply HACK0 and write changes
  python hack4.py -3 -p -w *.bin         # Apply HACK3 + unprotect to all .bin files
  python hack4.py -o 0x8000 -n 0x4000 -0 -w binary.bin  # Custom positions
        """
    )
    
    parser.add_argument('-o', '--old-pos', type=lambda x: int(x, 0), default=0xafc8,
                        help='Set old position (default: 0xafc8 / 45000)')
    
    parser.add_argument('-n', '--new-pos', type=lambda x: int(x, 0), default=0x2db6,
                        help='Set new position (default: 0x2db6 / 11702)')
    
    parser.add_argument('-0', '--hack0', action='store_true',
                        help='Apply HACK0: oldpos -> newpos')
    
    parser.add_argument('-1', '--hack1', action='store_true',
                        help='Apply HACK1: (oldpos+166) -> (newpos+166)')
    
    parser.add_argument('-2', '--hack2', action='store_true',
                        help='Apply HACK2: (oldpos+150) -> (newpos+150)')
    
    parser.add_argument('-3', '--hack3', action='store_true',
                        help='Apply HACK3: HACK1 + HACK2')
    
    parser.add_argument('-p', '--unprotect', action='store_true',
                        help='Apply unprotect mode (CD E4 43 6A -> 09 00 09 00)')
    
    parser.add_argument('-w', '--write', action='store_true',
                        help='Write mode - actually apply patches (BE CAREFUL!)')
    
    parser.add_argument('files', nargs='*',
                        help='Target file(s) - wildcards supported')
    
    return parser


def main():
    """Main entry point."""
    print("*** hack4.py (Python Implementation) ***")
    print("Dreamcast Binary Patcher Tool")
    print("Based on kikuchan's hack4 v1.5 (2001/05/04)\n")
    
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.files:
        parser.print_help()
        return 1
    
    # Create configuration
    config = Config()
    config.old_pos = args.old_pos
    config.new_pos = args.new_pos
    config.hack0 = args.hack0
    config.hack1 = args.hack1
    config.hack2 = args.hack2
    config.hack3 = args.hack3
    config.unprotect = args.unprotect
    config.write_mode = args.write
    
    # Expand wildcards
    target_files = expand_wildcards(args.files)
    
    if not target_files:
        print("Error: No valid target files found", file=sys.stderr)
        return 1
    
    # Create patcher and process files
    patcher = DreamcastPatcher(config)
    
    for filename in target_files:
        patcher.process_file(filename)
    
    print("Processing complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())