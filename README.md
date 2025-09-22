# MkCDI: Fast Dreamcast Image Builder

## Overview

Dreamcast Image Builder is a tool (or a compact toolchain, if one prefers to call it that) for creating bootable Dreamcast CDI images from game data files. This release provides both a command-line script (mkcdi.cmd) and a GUI (mkcdi_gui.exe) for building images with the correct LBA settings and IP.BIN configuration.

This tool builds images suitable for testing, bypassing ECC/EDC generation for speed,
For mastering a final CD-R release, you should use a full-featured toolchain like LazyBoot whatever that have a proper dummy support, **CDDA**, data/data mode and ECC.

## Features

- **Dual Interface**: Choose between powerful command-line control or user-friendly GUI
- **Automatic Binary Detection**: Automatically detects 1ST_READ.BIN, 0WINCEOS.BIN, or 1NOSDC.BIN
- **LBA Support**: Configurable LBA values (like 11702 and 45000)
- **IP.BIN Handling**: Automatic IP.BIN patching
- **Emulator Integration**: Built-in support for Redream emulator testing
- **Archive Management**: Automatically organizes previous builds
- **Noob Mode**: Simplified one-click building for beginners

## System Requirements

- Windows 7 or newer
- Python 3.8+ (for source version)
- Dreamcast game files (extracted from GDI/CDI)

<img width="376" height="398" alt="screenshot" src="https://github.com/user-attachments/assets/e76a376b-0063-4d50-a0a2-b8ad0b9401e1" />


## Directory Structure

```text
./
├── archive/          # Stores previous CDI builds
├── data/             # Place game files here (extracted from GDI/CDI)
├── emulator/         # Optional: an emulator and BIOS files goes here
├── system/           # Core tools and utilities
│   ├── build/
│   ├── dist/
│   ├── precon/       # Preconfigured IP.BIN templates
│   ├── src/          # Source code for tools
│   └── tmp/
├── mkcdi.cmd         # Command-line interface
├── mkcdi_gui.exe     # GUI executable
├── mkcdi.py          # Python source (CLI)
├── mkcdi_gui.py      # Python source (GUI)
├── settings.ini      # Configuration file
└── info.txt          # This file
```

## Installation

1. Extract the release archive to your desired location
2. Place your Dreamcast game files in the `data/` directory:
   - Files can be extracted from GDI/CDI using tools like:
     - GDI Explorer
     - 7-Zip with Iso7z plugin
   - Required files typically include:
     - 1ST_READ.BIN (main executable)
     - IP.BIN (boot information)
     - Other game data files

3. (Optional) For emulator testing:
   - Place an emulator here so you can run it from the GUI

	examples:

	.\emulator\redream.exe
	.\emulator\redream.key
	.\emulator\boot.bin

	other emulators also can be used:

	.\emulator\emulator.exe
	or
	.\emulator\demul.exe
	or
	.\emulator\flycast.exe
	   - Ensure you have the required BIOS file (boot.bin)

## Usage

### GUI Method (Recommended for beginners)

1. Run `mkcdi_gui.exe`
2. Configure settings:
   - **LBA**: Use 11702 for standard audio/data Dreamcast CDI images (faster to build but modifies the binary). Use 45000 for files extracted from a GDI if you do not want 1ST_READ.BIN be modified for LBA11702 and want to use for GDIBuilder later.
   - **Binary**: Auto-detected, but can be manually specified
   - **Volume**: Name for your image
   - **Enable Binhack**: Recommended for proper IP.BIN patching
   - **Run Emulator**: Launch redream after successful build
   - **Noob Mode**: Simplified one-click operation
  
3. Click "Build Image" to create your CDI

### Command-Line Method (Advanced users)

1. Open a command prompt in the application directory
2. Edit `mkcdi.cmd` to adjust settings:
   - Set `lba` to your desired value
   - Adjust `binary` if auto-detection fails
   - Set `volume` to your preferred image name
   - Set `enable_emulator=1` to auto-launch redream

3. Run `mkcdi.cmd` to build your image

## Toolchain Components

### Core Tools (Open Source)
- `bincon.exe` - Binary converter
- `binhack.exe` - IP.BIN patcher
- `hack4.exe` - Binary patcher
- `iso2cdi.exe` - ISO to CDI converter
- `mkisofs.exe` - ISO image creator
- `date.exe` - Build timestamp generator
- `logo.exe` - IP.BIN logo patcher
- `sfk.exe` - Swiss File Knife (text processing)
- `busybox.exe` - Unix utilities for Windows

### Optional Tools (Proprietary)
- `BinPATCH.exe` - Legacy binary patcher (may be removed in future)
- `IP.BIN 4 Win.exe` - IP.BIN editor (may be removed in future)

## Common Settings

### LBA Values
- **11702**
- **45000**
- any other LBA if you want to shift it instead of using dummy file

### Binary Types
- **1ST_READ.BIN**: Standard Katana SDK games
- **0WINCEOS.BIN**: Windows CE based games
- **1NOSDC.BIN**: Special format (e.g., Lodoss War)

## Building from Source

If you have Python installed, you can run the scripts directly:

```
python mkcdi.py          # Command-line version
python mkcdi_gui.py      # GUI version
```


## Troubleshooting

1. **"Binary not found" error**
   - Ensure game files are properly extracted to the `data/` directory
   - Verify you have at least 1ST_READ.BIN or 0WINCEOS.BIN

2. **"IP.BIN not found" error**
   - The tool will attempt to create a generic IP.BIN
   - For best results, provide a proper IP.BIN from your source image

3. **Emulator doesn't start**
   - Verify redream.exe is in the `emulator/` directory
   - Ensure you have a proper BIOS file (boot.bin)

4. **Image doesn't boot**
   - Verify LBA setting matches your source material
   - Check that all required game files are present

## Legacy Notes

- BinPATCH.exe and IP.BIN 4 Win.exe are legacy tools that may be removed in future versions
- The toolchain is designed to work with properly extracted Dreamcast game files
- For best results, always start with a known good GDI source

## Credits

This toolchain combines various open-source and custom tools to provide a complete Dreamcast image building solution. Special thanks to the Dreamcast homebrew community for their ongoing efforts.

## Legal (IP.BIN and Game Files)

*   The **IP.BIN** files created by this tool are generated from generic templates or code written by the homebrew community.
*   To build an image, you must provide your own game files (e.g., `1ST_READ.BIN`, `IP.BIN` and data files) from a legally sourced copy of a game.
*   This tool is intended for **preservation, education, and homebrew development** only. You must own the original games to use this software legally.

## License

MkCDI is licensed under the **GNU General Public License v3.0**.

This means you are free to use, modify, and distribute this software, provided you:
1.  Disclose your source code if you distribute modified versions.
2.  Use the same license (GPLv3) for your distributed work.

The project incorporates and reimplements tools from the Dreamcast homebrew community, originally released under GPL-compatible terms. See the `LICENSE` file for full details and component attribution.

## Disclaimer

This software is provided for educational and preservation purposes. You must own the original games to use this software legally. The authors are not responsible for any misuse of this software.


---

*Test Build, 20250922; from International Dreamcast homebrew community*
