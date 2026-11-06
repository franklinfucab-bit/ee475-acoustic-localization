# Setup on another Windows PC

## Desktop receiver

Use Windows and Python 3.12+ with Tcl/Tk. Clone/extract to a short ASCII path such as C:/Dev/ee475-acoustic-localization, especially if rebuilding firmware or Android.

```powershell
powershell -ExecutionPolicy Bypass -File .\Setup-Windows.ps1 -PythonExe 'C:\Path\To\Python312\python.exe'
```

This command creates .venv inside the project and installs SEN0325-Pico-Setup/requirements.txt. It checks source imports without starting a scan. Add -WithPlots for report generation. It does not install system drivers or flash a Pico. The dependency versions were verified on the owner's Windows installation; a clean teammate PC still needs a setup check.

Update-and-Start.cmd chooses EE475_PYTHON when supplied, then .venv/Scripts/pythonw.exe, then the owner's existing C:/Tools/Embedded runtime. Set the variable to a full configured Python executable if needed. For a console with useful errors:

```powershell
.\.venv\Scripts\python.exe .\SEN0325-Pico-Setup\sen0325_launcher.py --profile coded-gap
```

The launcher is a local source refresh/restart. It does not pull GitHub changes. Use git pull separately after reviewing local modifications.

## Pico and USB

Follow README's GPIO table. Firmware is RAM-only and is lost when USB power is removed. If the Pico comes back as the RPI-RP2 drive, the launcher copies the validated RAM image onto that drive; picotool and the RP2 Boot driver are not required for that path. picotool remains the fallback only when an old application is already running and the drive is absent. The running device uses VID 0x2E8A / PID 0x000A. A charge-only USB cable will not work.

```powershell
$env:EE475_PICOTOOL='C:\Path\To\picotool.exe'
.\.venv\Scripts\python.exe .\SEN0325-Pico-Setup\verify_ram.py .\SEN0325-Pico-Setup\firmware\sen0325_setup-RAM.uf2
.\Update-and-Start.cmd
```

The environment variable must be present in the process that launches the application. Connect only the intended Pico for loading. Keep the existing RAM image for initial tests; rebuilding/flashing is unnecessary for desktop handoff.

## Firmware rebuild, when needed

Build.ps1 and Load-RAM.ps1 retain the owner's established C:/Tools/Embedded layout; they are convenience scripts, not a universal tool installer. CMakeLists.txt also accepts PICO_SDK_PATH from CMake or the environment. Use the official Raspberry Pi SDK and ARM toolchain with CMake/Ninja and matching picotool/pioasm. The current application settings are PICO_BOARD=pico, PICO_NO_FLASH=ON, USB TX FIFO 4096 and endpoint software buffer 512. Preserve those when comparing firmware. Never treat rebuilding Flash as a routine handoff step.

## Android and offline validation

For phone use, install the supplied APK and read android-player/README.md. For rebuilding, edit a local copy of toolchain.example.json; SDK/JDK and the signing key are not bundled. For desktop checks without hardware:

```powershell
.\.venv\Scripts\python.exe .\tools\verify_handoff.py
```

Full saved-audio regressions need local-only recordings. See tests/README.md rather than silently skipping missing fixtures. Physical scanning, driver installation, microphone geometry and phone playback remain bench checks.
