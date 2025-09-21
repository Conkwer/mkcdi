@echo off
rem examples: 45000; 11702
set lba=11702
set binary=0WINCEOS.BIN
set volume=mygame
set enable_emulator=1

setlocal
set PATH=.\system;%PATH%

call :Verification
call :Binhack
call :NameGenerator
call :MakeImage
call :Emulator

timeout /t 5
exit

:NameGenerator
for /f "delims=" %%i in ('.\system\date.exe') do set build=%%i
sfk echo -spat Name is set as \q[cyan]"%volume%-%build%.cdi\q"[def]
echo.
goto :eof

:MakeImage
sfk echo [green]Building Image..
if exist test.iso del test.iso
set sort=&&if exist sortfile.str set sort=-sort sortfile.str
mkisofs -C 0,%lba% -V "%volume%" %sort% -exclude IP.BIN -G data\IP.BIN -l -J -r -o test.iso data
iso2cdi -i .\test.iso -l %lba% -o .\image.cdi
if exist image.cdi del test.iso
rem ren image.cdi "%volume%-%build%.tmp"&&del *.cdi&&ren *.tmp *.cdi
ren image.cdi "%volume%-%build%.tmp"
if not exist archive mkdir archive
if exist *.cdi move *.cdi .\archive\>NUL
ren *.tmp *.cdi
echo.
sfk echo file [cyan]"%volume%-%build%.cdi"[def] is created.
sfk echo this windows will be closed automatically
goto :eof

:Emulator
echo.
sfk echo [green]Running Emulator if enabled..

if exist ".\emulator\redream.exe" set emulator=redream
if exist ".\emulator\demul.exe" set emulator=demul
if exist ".\emulator\flycast.exe" set emulator=flycast
if exist ".\emulator\nullDC_Win32_Release-NoTrace.exe" set emulator=nullDC_Win32_Release-NoTrace
if exist ".\emulator\nulldc" set emulator=nulldc

if not exist .\emulator\%emulator%.exe goto :eof
if "%enable_emulator%"=="1" ".\emulator\%emulator%.exe" "%volume%-%build%.cdi"
goto :eof

:Binhack
hack4.exe -w -p data\*.bin >NUL
hack4.exe -w -n %lba% data\*.bin >NUL
::if exist ".\data\0WINCEOS.BIN" python .\system\bincon.py ./data/0WINCEOS.BIN ./data/IP.BIN --output ./data/0WINCEOS.BIN

if "%binary%"=="0WINCEOS.BIN" bincon.exe .\data\0WINCEOS.BIN .\data\0WINCEOS.BIN .\data\IP.BIN&&echo.

binhack.exe ".\data\%binary%" ".\data\IP.BIN" %lba% --output-dir "./data/" --quiet&&echo.
if "%binary%"=="0WINCEOS.BIN" logo .\system\wince.mr .\data\IP.BIN&&echo.
goto :eof


:Verification
sfk echo [green]Verificating files and patching binaries..
if not exist data mkdir data
if exist .\data\1ST_READ.BIN set binary=1ST_READ.BIN
if exist .\data\0WINCEOS.BIN set binary=0WINCEOS.BIN
if exist .\data\1NOSDC.BIN set binary=1NOSDC.BIN
if not exist ".\data\%binary%" sfk echo [yellow]Warning: 1ST_READ.BIN not found.[def]&&timeout /t 7&&exit

attrib -R data\*.* >NUL

if not exist .\data\IP.BIN sfk echo [yellow]Warning: IP.BIN not found[def]&&echo creating generic IP.BIN..&&.\system\busybox.exe sleep 2&&cls
if not exist .\data\IP.BIN busybox cp ./system/precon/katana.bin ./data/IP.BIN

if exist .\data\1NOSDC.BIN busybox cp .\system\precon\lodoss-5167.bin .\data\IP.BIN
::&&busybox cp .\system\precon\wince.bin .\data\IP.BIN
goto :eof
