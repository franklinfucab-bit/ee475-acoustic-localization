# Hardware and Wiring

## Current bench assembly

- Raspberry Pi Pico with RP2040, connected to Windows by USB.
- DFRobot SEN0325 / Sipeed R6+1 microphone array: six outer microphones and one center microphone.
- Breadboard and short jumper wires.
- Samsung S25 Ultra for the intended phone-beacon playback test.

The SEN0325 supplies raw microphone data. The current software computes direction on the computer; the array does not send a ready-made direction to the Pico.

## Working pin assignment

Use GPIO names and the board silkscreen to verify the connection. In the user's installed orientation, with the USB socket at the top and component side facing up, the left row runs from GP0 to GP15; the right row runs from VBUS down to GP16. A back-side photograph reverses left and right.

| SEN0325 label | Pico connection | Pico physical pin |
| --- | --- | --- |
| VIN | 3V3 OUT | 36 |
| GND | GND | 13 |
| MIC_D0 | GP6 | 9 |
| MIC_D1 | GP7 | 10 |
| MIC_D2 | GP8 | 11 |
| MIC_D3 | GP9 | 12 |
| MIC_CK | GP10 | 14 |
| MIC_WS | GP11 | 15 |
| LED_CK | GP12 | 16 |
| LED_DA | GP13 | 17 |

In the supplied connector photograph, viewed from the side carrying the connector labels, the five rows are:

```text
LED_DA    LED_CK
MIC_D1    MIC_D0
MIC_D3    MIC_D2
MIC_CK    MIC_WS
GND       VIN
```

Keep the known working 3.3 V microphone-test supply. Vendor documents for related revisions differ on VIN; this milestone does not change the supply or validate a 5 V configuration. The Pico GPIO uses 3.3 V logic. Disconnect USB before changing wiring and do not confuse 3V3 OUT with 3V3_EN. LED illumination needs a separately reviewed power design. The optional ESP32 path may light one dim ring LED after a valid `DOA`; use `LEDOFF` and stop if the 3.3 V microphone rail sags.

## Optional Pico–ESP32 UART (branch Pico-ESP32)

Do not move GP6–GP13. Add only these three wires. Power Pico and ESP32 from separate USB cables; common ground only. Do not feed the ESP32 from Pico 3V3 OUT.

| Pico | Pico physical pin | ESP32 DevKit V1 (WROOM) |
| --- | --- | --- |
| GP0 (UART0 TX) | 1 | GPIO16 (UART2 RX) |
| GP1 (UART0 RX) | 2 | GPIO17 (UART2 TX) |
| GND | any GND | GND |

TX must be crossed. NINA-B306 is not part of this link. See [esp32-link/README.md](../esp32-link/README.md).

## Capture configuration

The Pico generates 3.072 MHz bit clock and 48 kHz word select. Four parallel I2S data lines are captured using PIO and DMA. Each stereo frame has two 32-bit slots; the microphone data has 24 significant bits and the current host packet carries a 16-bit representation for seven channels.

| Slot | Nominal array angle |
| --- | --- |
| D0L | 0° |
| D0R | 60° |
| D1L | 120° |
| D1R | 180° |
| D2L | 240° |
| D2R | 300° |
| D3R_CENTER | Center |
| D3L | Unused; not an eighth microphone |

The geometry file uses a nominal 40 mm outer radius and a 343 m/s sound speed. Physical orientation and per-channel timing calibration remain to be verified. Front-reference and mirror controls support initial setup; they do not replace that validation.

Original datasheets, schematic and photographs are preserved under `references/hardware/`. Historical detailed wiring notes are retained in the workspace and archive.
