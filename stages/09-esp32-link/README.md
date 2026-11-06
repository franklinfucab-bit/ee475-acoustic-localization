# Stage 09 — Pico–ESP32 UART link

Date: 3 November 2026. Built on branch `Pico-ESP32` as four additive steps. Desktop RX4 and the published v0.6 RAM image remain the coded-beacon path.

## Intended behavior

- Pico keeps GP6–GP13 and the USB `RECORD` / CRC packet format.
- After `START` (not during `RECORD`), Pico also writes one `FEAT,v1,...` line on UART0 (GP0/GP1, 115200 8N1).
- ESP32 estimates a 300–2000 Hz phase bearing and prints `DOA,v1,...` on USB and back to the Pico.
- Pico may light one dim ring LED for a valid DOA and turns the ring off on invalid or ~400 ms stale data.
- A laptop script reads ESP32 USB only. It does not run RX4 and does not send `RECORD`.
- No motor commands. NINA-B306 is unused.

## Builds, in order

1. Pico UART0 + `FEAT` transmit; USB identify accepts `v0.6` and `v0.7`.
2. Shared text protocol and ESP32 phase estimator (port of `direction_estimator.py`).
3. Pico `DOA` receive and dim LED.
4. Display-only viewer and this stage note.

## How to compare

Leave `Update-and-Start.cmd` on coded-20 for the old path. For the new path, wire GP0/GP1/GND as in `esp32-link/README.md`, flash `esp32_doa`, rebuild Pico `v0.7-LINK`, send `FREQ 1000` + `START`, and play a 1000 Hz tone. Do not treat a 20 kHz locate file as a valid input to this estimator.

Host checks: `python tests/verify_esp32_link.py`. They do not replace a wired bench test or claim physical accuracy.
