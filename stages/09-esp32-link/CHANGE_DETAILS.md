# Pico–ESP32 UART link

Firmware `main.c` opens UART0 on GP0/GP1 after USB stdio. Each `START` report window still emits the previous USB `FRAME`/`PHASE` lines when a PC is connected, and always copies a compact `FEAT,v1` line to UART0. `RECORD` still skips that window so the 57 344-byte USB payload is unchanged.

`sen0325_launcher.py` accepts both `SEN0325_SETUP v0.6;` and `v0.7`, so the published RAM image still enumerates. CMake program version is `0.7-LINK`; `firmware/sen0325_setup-RAM.uf2` is not rebuilt in this stage.

`esp32-link/esp32_doa/phase_doa.h` ports the 300–2000 Hz weighted phase fit from `direction_estimator.py`. It rejects out-of-band frequency, empty captures, and missing center tone. It does not add a prior-angle jump veto and does not emit motor commands. `view_doa.py` only prints parsed `DOA` lines from the ESP32 COM port.

`tests/verify_esp32_link.py` checks protocol round-trip, 20 kHz rejection, empty-frame rejection, and 1000 Hz plane-wave angles at 0/45/90/180/270°.
