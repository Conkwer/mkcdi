import os
import sys
import subprocess
import configparser
import shutil
from datetime import datetime
import itertools
import threading
import time

# Global variable to control the spinner
spinner_running = False

def spinner():
    """Display a spinning progress indicator"""
    for c in itertools.cycle(['|', '/', '-', '\\']):
        if not spinner_running:
            break
        sys.stdout.write(f'\rBuilding image... {c}')
        sys.stdout.flush()
        time.sleep(0.1)
    sys.stdout.write('\rBuilding image... done!   \n')

def create_default_settings():
    """Create default settings.ini file if it doesn't exist"""
    config = configparser.ConfigParser()
    config['SETTINGS'] = {
        'lba': '11702',
        'binary': '0WINCEOS.BIN',
        'volume': 'mygame',
        'enable_emulator': '0'
    }
    
    with open('settings.ini', 'w') as configfile:
        config.write(configfile)
    print("Created default settings.ini file")

def load_settings():
    """Load settings from settings.ini or create default"""
    if not os.path.exists('settings.ini'):
        create_default_settings()
    
    config = configparser.ConfigParser()
    config.read('settings.ini')
    
    return {
        'lba': config.get('SETTINGS', 'lba', fallback='11702'),
        'binary': config.get('SETTINGS', 'binary', fallback='0WINCEOS.BIN'),
        'volume': config.get('SETTINGS', 'volume', fallback='mygame'),
        'enable_emulator': config.get('SETTINGS', 'enable_emulator', fallback='0')
    }

def run_command(cmd, check=True):
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=check)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr

def verification(settings):
    """Verify files and patch binaries"""
    print("Verificating files and patching binaries..")
    
    # Create data directory if it doesn't exist
    if not os.path.exists('data'):
        os.makedirs('data')
    
    # Determine binary file
    binary_files = ['1ST_READ.BIN', '0WINCEOS.BIN', '1NOSDC.BIN']
    for bfile in binary_files:
        if os.path.exists(f'data/{bfile}'):
            settings['binary'] = bfile
            break
    
    if not os.path.exists(f'data/{settings["binary"]}'):
        print("Warning: 1ST_READ.BIN not found.")
        return False
    
    # Remove read-only attributes (Windows only)
    if os.name == 'nt':
        for file in os.listdir('data'):
            filepath = os.path.join('data', file)
            if os.path.isfile(filepath):
                os.chmod(filepath, 0o666)  # Remove read-only
    
    # Create IP.BIN if it doesn't exist
    if not os.path.exists('data/IP.BIN'):
        print("Warning: IP.BIN not found")
        print("creating generic IP.BIN..")
        if os.path.exists('system/precon/katana.bin'):
            shutil.copy2('system/precon/katana.bin', 'data/IP.BIN')
    
    # Special case for 1NOSDC.BIN
    if settings['binary'] == '1NOSDC.BIN' and os.path.exists('system/precon/lodoss-5167.bin'):
        shutil.copy2('system/precon/lodoss-5167.bin', 'data/IP.BIN')
    
    return True

def binhack(settings):
    """Perform binary hacking operations"""
    lba = settings['lba']
    binary = settings['binary']
    
    # Run hack4 commands
    run_command('hack4.exe -w -p data\\*.bin', check=False)
    run_command(f'hack4.exe -w -n {lba} data\\*.bin', check=False)
    
    # Run bincon for 0WINCEOS.BIN
    if binary == '0WINCEOS.BIN':
        if os.path.exists('bincon.exe'):
            success, stdout, stderr = run_command(
                f'bincon.exe data\\0WINCEOS.BIN data\\0WINCEOS.BIN data\\IP.BIN', 
                check=False
            )
            if success:
                print()
    
    # Run binhack
    if os.path.exists('binhack.exe'):
        success, stdout, stderr = run_command(
            f'binhack.exe "data\\{binary}" "data\\IP.BIN" {lba} --output-dir "./data/" --quiet', 
            check=False
        )
        if success:
            print()
    
    # Run logo for Windows CE
    if binary == '0WINCEOS.BIN' and os.path.exists('logo.exe'):
        success, stdout, stderr = run_command(
            'logo system\\wince.mr data\\IP.BIN', 
            check=False
        )
        if success:
            print()

def name_generator(settings):
    """Generate name with timestamp"""
    build = datetime.now().strftime("%Y%m%d")
    settings['build'] = build
    filename = f"{settings['volume']}-{build}.cdi"
    print(f'Name is set as "{filename}"')
    print()
    return filename

def make_image(settings):
    """Create CDI image"""
    global spinner_running
    
    # Start the spinner in a separate thread
    spinner_running = True
    spinner_thread = threading.Thread(target=spinner)
    spinner_thread.start()
    
    try:
        # Remove test.iso if exists
        if os.path.exists('test.iso'):
            os.remove('test.iso')
        
        # Prepare sort command
        sort_cmd = ""
        if os.path.exists('sortfile.str'):
            sort_cmd = "-sort sortfile.str"
        
        # Build ISO
        mkisofs_cmd = (
            f'mkisofs -C 0,{settings["lba"]} -V "{settings["volume"]}" {sort_cmd} '
            f'-exclude IP.BIN -G data\\IP.BIN -l -J -r -o test.iso data'
        )
        
        success, stdout, stderr = run_command(mkisofs_cmd)
        if not success:
            print(f"Error creating ISO: {stderr}")
            return False
        
        # Convert to CDI
        iso2cdi_cmd = f'iso2cdi -i test.iso -l {settings["lba"]} -o image.cdi'
        success, stdout, stderr = run_command(iso2cdi_cmd)
        if not success:
            print(f"Error converting to CDI: {stderr}")
            return False
        
        # Clean up
        if os.path.exists('test.iso'):
            os.remove('test.iso')
        
        # Rename and organize files
        final_filename = f"{settings['volume']}-{settings['build']}.cdi"
        temp_filename = f"{settings['volume']}-{settings['build']}.tmp"
        
        if os.path.exists('image.cdi'):
            os.rename('image.cdi', temp_filename)
        
        # Create archive directory
        if not os.path.exists('archive'):
            os.makedirs('archive')
        
        # Move existing CDI files to archive
        for file in os.listdir('.'):
            if file.endswith('.cdi'):
                shutil.move(file, os.path.join('archive', file))
        
        # Rename temp to final
        if os.path.exists(temp_filename):
            os.rename(temp_filename, final_filename)
        
        print(f'file "{final_filename}" is created.')
        print('this window will be closed automatically')
        return True
    finally:
        # Stop the spinner
        spinner_running = False
        spinner_thread.join()

def run_emulator(settings):
    """Run emulator if enabled"""
    print()
    print("Running Emulator if enabled..")
    
    if settings['enable_emulator'] != '1':
        return
    
    if not os.path.exists('emulator/redream.exe'):
        return
    
    cdi_file = f"{settings['volume']}-{settings['build']}.cdi"
    if os.path.exists(cdi_file):
        run_command(f'emulator\\redream.exe "{cdi_file}"', check=False)

def main():
    """Main function"""
    # Add system directory to PATH
    system_path = os.path.join(os.getcwd(), 'system')
    if system_path not in os.environ['PATH']:
        os.environ['PATH'] = system_path + os.pathsep + os.environ['PATH']
    
    # Load settings
    settings = load_settings()
    
    # Run the process
    if not verification(settings):
        print("Verification failed. Exiting in 7 seconds...")
        import time
        time.sleep(7)
        sys.exit(1)
    
    binhack(settings)
    filename = name_generator(settings)
    
    if make_image(settings):
        run_emulator(settings)
    
    print("Process completed. Exiting in 5 seconds...")
    import time
    time.sleep(5)

if __name__ == "__main__":
    main()