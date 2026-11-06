# Pico–ESP32 UART link

Optional path on branch `Pico-ESP32`. The laptop RX4 USB `RECORD` path stays available. This link sends compact 300–2000 Hz phase features from Pico UART0 to an ESP32, which estimates bearing and prints `DOA` lines. It does not replace 19–21 kHz RX4 and does not command motors.

## Wires (classic 30-pin ESP32 DevKit / WROOM)

Disconnect USB on both boards before changing wires. Keep the existing SEN0325 cables on GP6–GP13.

| Pico | Pico physical pin | Direction | ESP32 DevKit | Notes |
| --- | --- | --- | --- | --- |
| **GP0** | 1 | Pico TX → | **GPIO16** (RX2) | Crossed data |
| **GP1** | 2 | Pico RX ← | **GPIO17** (TX2) | Crossed data |
| **GND** | 3, 8, 13, 18, 23, 28, 33 or 38 | common | **GND** | Required |

Do **not** connect 5 V / VIN between the boards. Power each board from its own USB. Do **not** use Pico 3V3 OUT for the ESP32; that rail already feeds the microphone array.

NINA-B306 stays unconnected. Do not tap Pico TX to two receivers.

If the ESP32 is an S3, C3, or WROVER (PSRAM on 16/17), change `PIC_RX` / `PIC_TX` in `esp32_doa/esp32_doa.ino` and use those GPIOs instead. Avoid GPIO0, 2, 12 and 15.

## What each USB cable is for

- Pico USB: existing RX4 / `RECORD` (unchanged).
- ESP32 USB: flash the sketch, then `python esp32-link/view_doa.py COMx` for display-only text.

## Bench sequence

1. Wire the three lines above. Leave microphone wiring in place.
2. Flash `esp32_doa/esp32_doa.ino` (115200).
3. Rebuild/load Pico firmware from this branch (`v0.7-LINK`). The stock `firmware/sen0325_setup-RAM.uf2` is still the old v0.6 image until you rebuild.
4. On the Pico USB console: `FREQ 1000` then `START`. Play a 1000 Hz tone, not the 19–21 kHz locate file.
5. ESP32 USB should print `DOA,v1,...`. Invalid results are not a 0° command. Lights stay off until `valid=1`; one dim LED, then off after about 400 ms without a new valid line.

`LEDOFF` turns the ring black. Ring current is still on the 3.3 V microphone supply; stop if capture dies when a LED lights.
