import os
import sys
import subprocess
import configparser
import shutil
from datetime import datetime
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox
import re
import glob
import ctypes

# Global variable to control the spinner
spinner_running = False

class DreamcastImageBuilder:
    def __init__(self):
        self.application_path = self._get_application_path()
        self.config_path = os.path.join(self.application_path, 'settings.ini')
        self.emulator_path = 'emulator/emulator.exe'  # Default emulator path
        self.is_elf = False  # Track if we're building from ELF
        self.enable_hidpi()
        self.setup_gui()
        self.load_settings()

    @staticmethod
    def _get_application_path() -> str:
        return os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))

    def enable_hidpi(self):
        """Enable HiDPI support for Windows 10/11"""
        if sys.platform == 'win32':
            try:
                # Tell Windows this app is DPI aware
                ctypes.windll.shcore.SetProcessDpiAwareness(1)  # PROCESS_SYSTEM_DPI_AWARE
            except Exception:
                try:
                    # Fallback for older Windows versions
                    ctypes.windll.user32.SetProcessDPIAware()
                except Exception:
                    pass

    def setup_gui(self):
        self.root = tk.Tk()
        self.root.title("Dreamcast Image Builder")
        
        # Get screen scaling factor
        self.scaling_factor = self.root.winfo_fpixels('1i') / 96.0
        
        # Adjust window size based on DPI
        base_width = 380
        base_height = 380
        window_width = int(base_width * min(self.scaling_factor, 1.5))
        window_height = int(base_height * min(self.scaling_factor, 1.5))
        
        self.root.geometry(f"{window_width}x{window_height}")
        
        # Set minimum window size
        self.root.minsize(int(360 * min(self.scaling_factor, 1.5)), 
                         int(360 * min(self.scaling_factor, 1.5)))
        
        # Configure default font size based on scaling
        default_font_size = 9  # Keep original size
        self.default_font = ('Segoe UI', default_font_size)
        self.root.option_add('*Font', self.default_font)
        
        # Configure ttk styles for better HiDPI rendering
        style = ttk.Style()
        style.theme_use('vista' if sys.platform == 'win32' else 'clam')
        
        # Adjust padding for HiDPI
        self.base_padding = int(5 * min(self.scaling_factor, 1.3))
        
        # Initialize variables
        self.lba_var = tk.StringVar(value="11702")
        self.binary_var = tk.StringVar(value="0WINCEOS.BIN")
        self.volume_var = tk.StringVar(value="mygame")
        self.enable_emulator_var = tk.BooleanVar(value=False)
        self.enable_binhack_var = tk.BooleanVar(value=True)
        self.noob_mode_var = tk.BooleanVar(value=False)
        
        self.create_widgets()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        # Main frame with DPI-aware padding
        main_frame = ttk.Frame(self.root, padding=str(self.base_padding))
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Calculate padding values
        pady_small = max(2, int(2 * min(self.scaling_factor, 1.3)))
        pady_medium = max(5, int(5 * min(self.scaling_factor, 1.3)))
        pady_large = max(10, int(10 * min(self.scaling_factor, 1.3)))
        padx_medium = max(5, int(5 * min(self.scaling_factor, 1.3)))
        padx_checkbox = max(10, int(10 * min(self.scaling_factor, 1.3)))
        
        # Calculate entry widths based on scaling
        lba_width = max(10, int(10 * min(self.scaling_factor, 1.2)))
        binary_width = max(15, int(15 * min(self.scaling_factor, 1.2)))
        volume_width = max(20, int(20 * min(self.scaling_factor, 1.2)))
        
        row = 0
        
        # LBA setting
        ttk.Label(main_frame, text="LBA:").grid(row=row, column=0, sticky=tk.W, pady=pady_small)
        self.lba_entry = ttk.Entry(main_frame, textvariable=self.lba_var, width=lba_width)
        self.lba_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=pady_small, padx=padx_medium)
        row += 1
        
        # Binary setting
        ttk.Label(main_frame, text="Binary:").grid(row=row, column=0, sticky=tk.W, pady=pady_small)
        self.binary_entry = ttk.Entry(main_frame, textvariable=self.binary_var, width=binary_width)
        self.binary_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=pady_small, padx=padx_medium)
        row += 1
        
        # Volume name setting
        ttk.Label(main_frame, text="Volume:").grid(row=row, column=0, sticky=tk.W, pady=pady_small)
        self.volume_entry = ttk.Entry(main_frame, textvariable=self.volume_var, width=volume_width)
        self.volume_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=pady_small, padx=padx_medium)
        row += 1
        
        # Checkboxes - centered
        checkbox_frame = ttk.Frame(main_frame)
        checkbox_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=pady_medium)
        
        binhack_check = ttk.Checkbutton(checkbox_frame, text="Enable Binhack", 
                                       variable=self.enable_binhack_var)
        binhack_check.grid(row=0, column=0, padx=(0, padx_checkbox))
        
        emulator_check = ttk.Checkbutton(checkbox_frame, text="Run Emulator", 
                                        variable=self.enable_emulator_var)
        emulator_check.grid(row=0, column=1, padx=(0, padx_checkbox))
        
        noob_check = ttk.Checkbutton(checkbox_frame, text="Noob Mode", 
                                    variable=self.noob_mode_var,
                                    command=self.toggle_noob_mode)
        noob_check.grid(row=0, column=2)
        
        # Center the checkboxes
        checkbox_frame.columnconfigure(0, weight=1)
        checkbox_frame.columnconfigure(1, weight=1)
        checkbox_frame.columnconfigure(2, weight=1)
        row += 1
        
        # Build button centered
        self.build_button = ttk.Button(main_frame, text="Build Image", command=self.start_build_thread)
        self.build_button.grid(row=row, column=0, columnspan=2, pady=pady_large)
        row += 1
        
        # Status row
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=pady_small)
        
        ttk.Label(status_frame, text="Status:").grid(row=0, column=0, sticky=tk.W)
        
        right_frame = ttk.Frame(status_frame)
        right_frame.grid(row=0, column=1, sticky=tk.E)
        
        spinner_width = max(3, int(3 * min(self.scaling_factor, 1.2)))
        self.spinner_label = ttk.Label(right_frame, text="", width=spinner_width)
        self.spinner_label.grid(row=0, column=0, sticky=tk.W)
        
        self.progress_label = ttk.Label(right_frame, text="Ready")
        self.progress_label.grid(row=0, column=1, sticky=tk.W)
        
        status_frame.columnconfigure(1, weight=1)
        row += 1
        
        # Status text area with DPI-aware dimensions
        text_height = max(10, int(10 * min(self.scaling_factor, 1.2)))
        text_width = max(50, int(50 * min(self.scaling_factor, 1.2)))
        
        # Create font for text widget
        text_font_size = max(9, int(9 * min(self.scaling_factor, 1.2)))
        text_font = ('Consolas', text_font_size) if sys.platform == 'win32' else ('Courier', text_font_size)
        
        self.status_text = tk.Text(main_frame, height=text_height, width=text_width, font=text_font)
        self.status_text.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=pady_small)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.status_text.yview)
        scrollbar.grid(row=row, column=2, sticky=(tk.N, tk.S))
        self.status_text['yscrollcommand'] = scrollbar.set
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(row, weight=1)

    def toggle_noob_mode(self):
        if self.noob_mode_var.get():
            # Noob mode enabled - set predefined values
            self.lba_var.set("11702")
            self.binary_var.set("1ST_READ.BIN")
            self.volume_var.set("mygame")
            self.enable_binhack_var.set(True)
            self.enable_emulator_var.set(False)
            
            # Disable input fields
            self.lba_entry.config(state='disabled')
            self.binary_entry.config(state='disabled')
            self.volume_entry.config(state='disabled')
        else:
            # Noob mode disabled - enable input fields
            self.lba_entry.config(state='normal')
            self.binary_entry.config(state='normal')
            self.volume_entry.config(state='normal')

    def start_spinner(self):
        global spinner_running
        spinner_running = True
        self.spinner_thread = threading.Thread(target=self.update_spinner, daemon=True)
        self.spinner_thread.start()

    def stop_spinner(self):
        global spinner_running
        spinner_running = False
        if hasattr(self, 'spinner_thread'):
            self.spinner_thread.join(timeout=0.1)
        self.spinner_label.config(text="")

    def update_spinner(self):
        spinner_chars = ['|', '/', '-', '\\']
        index = 0
        while spinner_running:
            self.spinner_label.config(text=spinner_chars[index])
            index = (index + 1) % len(spinner_chars)
            time.sleep(0.1)
        self.spinner_label.config(text="")

    def log_message(self, message):
        self.status_text.insert(tk.END, message + "\n")
        self.status_text.see(tk.END)
        self.root.update_idletasks()

    def create_default_settings(self):
        config = configparser.ConfigParser()
        config['SETTINGS'] = {
            'lba': '11702',
            'binary': '1ST_READ.BIN',
            'volume': 'mygame',
            'enable_emulator': '0',
            'enable_binhack': '1',
            'noob_mode': '0',
            'emulator_path': 'emulator/emulator.exe'
        }
        with open(self.config_path, 'w') as f:
            config.write(f)
        self.log_message("Created default settings.ini file")

    def load_settings(self):
        if not os.path.exists(self.config_path):
            self.create_default_settings()
        config = configparser.ConfigParser()
        config.read(self.config_path)
        self.lba_var.set(config.get('SETTINGS', 'lba', fallback='11702'))
        self.binary_var.set(config.get('SETTINGS', 'binary', fallback='1ST_READ.BIN'))
        self.volume_var.set(config.get('SETTINGS', 'volume', fallback='mygame'))
        self.enable_emulator_var.set(config.getboolean('SETTINGS', 'enable_emulator', fallback=False))
        self.enable_binhack_var.set(config.getboolean('SETTINGS', 'enable_binhack', fallback=True))
        self.noob_mode_var.set(config.getboolean('SETTINGS', 'noob_mode', fallback=False))
        self.emulator_path = config.get('SETTINGS', 'emulator_path', fallback='emulator/emulator.exe')
        
        if self.noob_mode_var.get():
            self.toggle_noob_mode()

    def save_settings(self):
        config = configparser.ConfigParser()
        config['SETTINGS'] = {
            'lba': self.lba_var.get(),
            'binary': self.binary_var.get(),
            'volume': self.volume_var.get(),
            'enable_emulator': '1' if self.enable_emulator_var.get() else '0',
            'enable_binhack': '1' if self.enable_binhack_var.get() else '0',
            'noob_mode': '1' if self.noob_mode_var.get() else '0',
            'emulator_path': self.emulator_path
        }
        with open(self.config_path, 'w') as f:
            config.write(f)

    def find_emulator(self):
        if os.path.exists(self.emulator_path) and os.path.isfile(self.emulator_path):
            self.log_message(f"Using user-specified emulator: {self.emulator_path}")
            return self.emulator_path
        
        self.log_message(f"User-specified emulator not found: {self.emulator_path}")
        self.log_message("Searching for common Dreamcast emulators...")
        
        common_emulators = [
            'redream.exe', 'Redream.exe', 'redream',
            'emulator.exe', 'emulator',
            'demul.exe', 'flycast.exe', 'Flycast.exe', 'flycast'
        ]
        
        emulator_dir = 'emulator'
        if os.path.exists(emulator_dir) and os.path.isdir(emulator_dir):
            for emulator in common_emulators:
                emulator_path = os.path.join(emulator_dir, emulator)
                if os.path.exists(emulator_path) and os.path.isfile(emulator_path):
                    self.log_message(f"Found emulator: {emulator_path}")
                    return emulator_path
        
        for emulator in common_emulators:
            if os.path.exists(emulator) and os.path.isfile(emulator):
                self.log_message(f"Found emulator: {emulator}")
                return emulator
        
        self.log_message("ERROR: No emulator found!")
        self.log_message("Please place an emulator binary in the 'emulator' directory")
        return None

    def run_command(self, cmd, check=True):
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=check)
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.CalledProcessError as e:
            return False, e.stdout, e.stderr

    def convert_elf_to_binary(self, elf_file, settings):
        self.log_message(f"ELF binary detected: {os.path.basename(elf_file)}")
        self.log_message("KOS homebrew mode - converting ELF to 1ST_READ.BIN")
        
        objcopy_path = os.path.join('system', 'sh-elf-objcopy.exe')
        scramble_path = os.path.join('system', 'scramble.exe')
        
        if not os.path.exists(objcopy_path):
            self.log_message(f"ERROR: {objcopy_path} not found!")
            return False
        if not os.path.exists(scramble_path):
            self.log_message(f"ERROR: {scramble_path} not found!")
            return False
        
        unscrambled_path = os.path.join('data', 'unscrambled.bin')
        output_path = os.path.join('data', '1ST_READ.BIN')
        
        self.log_message("Converting ELF to binary format...")
        success, stdout, stderr = self.run_command(
            f'"{objcopy_path}" -O binary "{elf_file}" "{unscrambled_path}"',
            check=False
        )
        
        if not success or not os.path.exists(unscrambled_path):
            self.log_message(f"ERROR: Failed to convert ELF to binary: {stderr}")
            return False
        
        self.log_message("Scrambling binary...")
        success, stdout, stderr = self.run_command(
            f'"{scramble_path}" "{unscrambled_path}" "{output_path}"',
            check=False
        )
        
        if os.path.exists(unscrambled_path):
            os.remove(unscrambled_path)
        
        if not success or not os.path.exists(output_path):
            self.log_message(f"ERROR: Failed to scramble binary: {stderr}")
            return False
        
        if os.path.exists(output_path):
            os.remove(elf_file)
            self.log_message("Conversion successful - created 1ST_READ.BIN")
        
        settings['binary'] = '1ST_READ.BIN'
        self.is_elf = True
        
        kos_ipbin = os.path.join('system', 'precon', 'kos.bin')
        if os.path.exists(kos_ipbin):
            shutil.copy2(kos_ipbin, 'data/IP.BIN')
            self.log_message("Using KOS-compatible IP.BIN")
        else:
            self.log_message("WARNING: kos.bin not found in system/precon/")
        
        return True

    def verification(self, settings):
        self.log_message("Verifying files and patching binaries...")
        if not os.path.exists('data'):
            os.makedirs('data')
        
        self.is_elf = False
        
        elf_files = glob.glob('data/*.elf')
        
        if len(elf_files) > 1:
            self.log_message("ERROR: Multiple ELF files detected!")
            self.log_message("Please keep only ONE .elf file in the data folder")
            self.log_message("")
            self.log_message("Found ELF files:")
            for elf in elf_files:
                self.log_message(f"  - {os.path.basename(elf)}")
            return False
        
        if len(elf_files) == 1:
            if not self.convert_elf_to_binary(elf_files[0], settings):
                return False
            return True
        
        user_binary = settings['binary']
        if user_binary and os.path.exists(f'data/{user_binary}'):
            self.log_message(f"Found user-specified binary: {user_binary}")
            return True
        
        binary_files = ['1ST_READ.BIN', '0WINCEOS.BIN', '1NOSDC.BIN']
        found_binary = None
        for bfile in binary_files:
            if os.path.exists(f'data/{bfile}'):
                found_binary = bfile
                self.log_message(f"Found binary: {bfile}")
                break
        
        if not found_binary:
            self.log_message("ERROR: No binary file found in data directory!")
            self.log_message("Please place a binary or .elf file in the data directory")
            return False
        
        settings['binary'] = found_binary
        
        if os.name == 'nt':
            for file in os.listdir('data'):
                fp = os.path.join('data', file)
                if os.path.isfile(fp):
                    os.chmod(fp, 0o666)
        
        if not os.path.exists('data/IP.BIN'):
            self.log_message("Warning: IP.BIN not found")
            if os.path.exists('system/precon/katana.bin'):
                shutil.copy2('system/precon/katana.bin', 'data/IP.BIN')
                self.log_message("Created IP.BIN from katana.bin")
        
        if settings['binary'] == '1NOSDC.BIN' and os.path.exists('system/precon/lodoss-5167.bin'):
            shutil.copy2('system/precon/lodoss-5167.bin', 'data/IP.BIN')
            self.log_message("Created IP.BIN from lodoss-5167.bin for 1NOSDC.BIN")
        
        return True

    def binhack(self, settings):
        if self.is_elf:
            self.log_message("KOS homebrew detected - skipping binhack")
            return
        
        if not self.enable_binhack_var.get():
            self.log_message("Binhack disabled, skipping")
            return
        
        lba = settings['lba']
        binary = settings['binary']
        self.log_message("Running hack4 commands...")
        self.run_command('hack4.exe -w -p data\\*.bin', check=False)
        self.run_command(f'hack4.exe -w -n {lba} data\\*.bin', check=False)
        
        if binary == '0WINCEOS.BIN' and os.path.exists('bincon.exe'):
            self.run_command('bincon.exe data\\0WINCEOS.BIN data\\0WINCEOS.BIN data\\IP.BIN', check=False)
        
        if os.path.exists('binhack.exe'):
            self.log_message("Running binhack...")
            self.run_command(f'binhack.exe "data\\{binary}" "data\\IP.BIN" {lba} --output-dir "./data/" --quiet', check=False)
        
        if binary == '0WINCEOS.BIN' and os.path.exists('logo.exe'):
            self.run_command('logo system\\wince.mr data\\IP.BIN', check=False)

    def name_generator(self, settings):
        build = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"{settings['volume']}-{build}.cdi"
        settings['build'] = build
        self.log_message(f'Name is set as "{filename}"')
        return filename

    def make_image(self, settings):
        if os.path.exists('test.iso'):
            os.remove('test.iso')
        sort_cmd = "-sort sortfile.str" if os.path.exists('sortfile.str') else ""
        self.log_message("Building ISO with mkisofs...")
        mkisofs_cmd = (
            f'mkisofs -C 0,{settings["lba"]} -V "{settings["volume"]}" {sort_cmd} '
            f'-exclude IP.BIN -G data\\IP.BIN -l -J -r -o test.iso data'
        )
        success, _, stderr = self.run_command(mkisofs_cmd)
        if not success:
            self.log_message(f"Error creating ISO: {stderr}")
            return False
        self.log_message("Converting ISO to CDI with iso2cdi...")
        success, _, stderr = self.run_command(f'iso2cdi -i test.iso -l {settings["lba"]} -o image.cdi')
        if not success:
            self.log_message(f"Error converting to CDI: {stderr}")
            return False
        if os.path.exists('test.iso'):
            os.remove('test.iso')
        
        build = datetime.now().strftime("%Y%m%d-%H%M%S")
        final_filename = f"{settings['volume']}-{build}.cdi"
        temp_filename = f"{settings['volume']}-{build}.tmp"
        settings['build'] = build
        
        if not os.path.exists('archive'):
            os.makedirs('archive')
        
        for file in os.listdir('.'):
            if file.endswith('.cdi') and file != 'image.cdi':
                shutil.move(file, os.path.join('archive', file))
        
        if os.path.exists('image.cdi'):
            os.rename('image.cdi', temp_filename)
        
        if os.path.exists(temp_filename):
            os.rename(temp_filename, final_filename)
        
        settings['cdi_file'] = final_filename
        self.log_message(f'File "{final_filename}" is created.')
        return True

    def run_emulator(self, settings):
        self.log_message("Running Emulator if enabled...")
        if not self.enable_emulator_var.get():
            return
        
        emulator_path = self.find_emulator()
        
        if not emulator_path:
            self.log_message("Emulator launch aborted - no emulator found")
            return
        
        cdi_file = settings.get('cdi_file')
        if cdi_file and os.path.exists(cdi_file):
            abs_path = os.path.abspath(cdi_file)
            self.log_message(f"Starting emulator with {abs_path}")
            self.run_command(f'"{emulator_path}" "{abs_path}"', check=False)
        else:
            self.log_message(f"CDI file not found: {cdi_file}")

    def validate_inputs(self):
        try:
            lba = int(self.lba_var.get())
            if lba < 11702:
                lba = 11702
        except ValueError:
            lba = 11702
        
        volume = self.volume_var.get()
        if len(volume) > 32 or not re.match("^[a-zA-Z0-9_-]+$", volume):
            self.log_message("Volume name invalid, using default 'mygame'")
            volume = "mygame"
        
        binary = self.binary_var.get().strip()
        if binary and not os.path.exists(f'data/{binary}'):
            self.log_message(f"Warning: Binary '{binary}' not found, will auto-detect")
            binary = ""
        
        return {
            'lba': str(lba),
            'binary': binary,
            'volume': volume,
            'enable_emulator': '1' if self.enable_emulator_var.get() else '0',
            'enable_binhack': '1' if self.enable_binhack_var.get() else '0'
        }

    def build_image(self):
        self.status_text.delete(1.0, tk.END)
        self.progress_label.config(text="Building...")
        self.start_spinner()
        
        system_path = os.path.join(os.getcwd(), 'system')
        if system_path not in os.environ['PATH']:
            os.environ['PATH'] = system_path + os.pathsep + os.environ['PATH']
        
        settings = self.validate_inputs()
        self.save_settings()
        
        if not self.verification(settings):
            self.progress_label.config(text="Failed")
            self.stop_spinner()
            self.log_message("Build process stopped - verification failed")
            return
        
        if self.enable_binhack_var.get():
            self.binhack(settings)
        
        filename = self.name_generator(settings)
        
        if self.make_image(settings):
            self.run_emulator(settings)
            self.progress_label.config(text="Completed")
        else:
            self.progress_label.config(text="Failed")
        
        self.stop_spinner()
        self.log_message("Process completed.")

    def start_build_thread(self):
        self.build_button.config(state='disabled')
        thread = threading.Thread(target=self.build_image, daemon=True)
        thread.start()
        self.check_thread_status(thread)

    def check_thread_status(self, thread):
        if thread.is_alive():
            self.root.after(100, lambda: self.check_thread_status(thread))
        else:
            self.build_button.config(state='normal')

    def on_closing(self):
        self.save_settings()
        self.stop_spinner()
        self.root.destroy()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = DreamcastImageBuilder()
    app.run()
