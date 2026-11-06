# Tagalong | Acoustic Localization

**EE475 · Desktop RX4 · 29 October 2026 · Pico firmware v0.6-RX2**

A phone emits a known beacon. The SEN0325 6+1 array and Raspberry Pi Pico capture seven synchronous audio channels. The Windows app estimates bearing and shows the received waveform and spectrum. Radar rings are a visual guide, not a distance measurement.

RX4 adds a joint spectral-delay rescue after the existing estimators fail. It evaluates a common physical delay field using all reliable pair-score curves. It does not reject a direction because of its change from the previous frame. Manual playback interruptions are separate from receiver failures.


## Team handoff — 2 November 2026

Start with the [English handoff](docs/TEAM_HANDOFF.md) or [中文交接](docs/TEAM_HANDOFF_ZH.md). For a coding agent, read [AI_HANDOFF.md](docs/AI_HANDOFF.md) and [AGENTS.md](AGENTS.md). [FILE_CATALOG.md](docs/FILE_CATALOG.md) lists every published file and its purpose; [INTEGRATION.md](docs/INTEGRATION.md) describes interfaces and future robot work.

**Phone player:** [Beacon Loop 1.1 APK](android-player/releases/BeaconLoop-1.1.apk), [usage and build instructions](android-player/README.md). **New Windows PC:** [setup instructions](docs/SETUP_WINDOWS.md). **Offline checks:** `python tools/verify_handoff.py`.

The repository is a selected team package. Original microphone captures, runtime logs, local configuration and redundant historical binary archives remain in the complete local archive. See [SHARING.md](docs/SHARING.md). The root FILE_INDEX.txt is local-only; the published file catalog describes what a clone actually contains. The [stage 07 notes](stages/07-team-handoff/README.md) record packaging changes without changing the RX4 estimator. Optional Pico–ESP32 UART wiring and a 1000 Hz phase path are on branch `Pico-ESP32`; see [esp32-link/README.md](esp32-link/README.md) and [stage 09](stages/09-esp32-link/README.md). That path does not replace RX4.

## Start

1. Connect the wired Pico over USB.
2. Double-click **Update-and-Start.cmd** or **一键启动雷达.cmd**. The launcher validates local RX4 source files, gracefully closes a compatible running instance and confirms the new process/version before returning. This refreshes the local program; it does not download updates or flash firmware.
3. Select **Start Scan**, then play **audio/phone/HF2-20kHz/01_LOCATE_20kHz_19-21kHz.mp3** on the phone. The computer remains receive-only.
4. For another compatible periodic beacon, select **Import Beacon** in the Windows app and play the same file on the phone. Do not change one side's frequency or code independently.
5. **Set Front** calibrates the view after stable measurements. **Advanced** retains detailed channels and manually labelled trials. Automatic short diagnostic captures remain enabled.

The same 90.11 s phone recording produced 52 accepted outputs with RX3 and 81 with RX4; all previously accepted raw angles were preserved. This is an identical-input comparison, not a representative success rate or physical accuracy measurement. Unstable direction fits remain. Read the [illustrated Chinese analysis report](reports/RX4-2026-10-29/ANALYSIS_ZH.md).

## Folder structure and roles

| Location | Role |
| --- | --- |
| `SEN0325-Pico-Setup/` | Active firmware source, Windows app, current RAM image and runtime logs. Existing SDK/build alias remains valid. |
| `audio/phone/HF2-20kHz/` | Current phone beacon and level probes. Pure probes do not authorize a bearing. |
| `audio/reference/` | Current lossless reference copy. |
| `tests/` | Current repeatable checks, raw trial capture, replay and plot tools. |
| `stages/06-joint-delay/` | RX4 checkpoint: validation, source backup, original raw recordings and machine-readable analysis. |
| `reports/RX4-2026-10-29/` | Human-readable analysis with waveform, spectrum and direction plots. |
| `docs/` | Current architecture, operation, hardware, roles and legacy path map. |
| `references/` | Original project proposal, notes, schematics, datasheets and photographs. |
| `android-player/` | Local phone loop-player project and its own delivery notes. |
| `legacy/` | Superseded stages, reports, releases, audio, setup records and exploratory scripts. Reference material, not the current launch path. |
| `docs/FILE_CATALOG.md` | Published files and purposes; local FILE_INDEX.txt additionally covers private archives. |

Old absolute paths in frozen reports are intentionally preserved. Resolve them using the local migration map (docs/LEGACY_MIGRATION.csv, excluded from Git). Historical file content was checked after moving. A locked old `releases/` directory may retain only a location notice; its package files are under `legacy/releases/`.

Read [project roles](docs/ROLES.md), [角色与工作范围](docs/ROLES_ZH.md), [current operation](docs/USER_GUIDE.md), [architecture](docs/ARCHITECTURE.md), and [agent instructions](AGENTS.md).

## SEN0325-to-Pico GPIO wiring

The table below matches the current firmware pin assignments. **GPIO numbers and physical pin numbers are different**: for example, GP6 is physical pin 9.

| SEN0325 pin label | Pico signal / GPIO | Pico physical pin | Function |
| --- | --- | --- | --- |
| VIN | 3V3 OUT | 36 | 3.3 V supply for the current microphone test |
| GND | GND | 13 | Common ground |
| MIC_D0 | GP6 | 9 | Microphone data line 0, array → Pico |
| MIC_D1 | GP7 | 10 | Microphone data line 1, array → Pico |
| MIC_D2 | GP8 | 11 | Microphone data line 2, array → Pico |
| MIC_D3 | GP9 | 12 | Microphone data line 3, array → Pico |
| MIC_CK | GP10 | 14 | I2S bit clock (BCLK), Pico → array |
| MIC_WS | GP11 | 15 | I2S word select (WS/LRCLK), Pico → array |
| LED_CK | GP12 | 16 | LED clock, Pico → array |
| LED_DA | GP13 | 17 | LED data, Pico → array |

**Pico orientation:** with the USB connector at the top and the component side facing you, the left row runs from GP0 to GP15; the right row runs from VBUS down to GP16. The back-side photograph reverses left and right. Follow the GPIO names and physical pin numbers rather than the breadboard row numbers.

**SEN0325 connector orientation:** viewed from the side carrying the connector and its printed labels, as in the supplied photograph:

```text
Left      Right
LED_DA    LED_CK
MIC_D1    MIC_D0
MIC_D3    MIC_D2
MIC_CK    MIC_WS
GND       VIN
```

Disconnect USB before changing wires. Keep the current 3.3 V supply and ring LEDs off; do not confuse **3V3 OUT (pin 36)** with **3V3_EN (pin 37)** or VBUS. See [hardware and wiring notes](docs/HARDWARE.md) for the board-revision and power-supply details.


## Validation and limitations

- 15 focused RX4 checks passed, including 171 nonphysical coded delay fields rejected, score-cache reuse, fresh-data handling and unrestricted large turns.
- Existing 20 kHz model regression and receive-only controls passed. These are model checks, not physical angular acceptance.
- Actual GUI/Pico check passed all 21 checks, retaining four main buttons and seven-channel capture.
- The 90 s phone record has a median normal result interval of 187 ms and packet completion of 161.8 ms. These are pipeline measurements, not sound-onset-to-correct-bearing latency.
- The receiver still rejects inconsistent measurements. Known physical bearings, reliable range and an inaudibility acceptance test remain outstanding.

Shared compilers and Python remain outside the project under `C:/Tools/Embedded`. No Pico Flash payload or GPIO mapping changed in RX4. See the [checkpoint README](stages/06-joint-delay/README.md) and [validation guide](docs/VALIDATION.md).
