# Team handoff — 2 November 2026

This is the SEN0325/Pico acoustic-bearing contribution to **Tagalong (EE475)**.
Current receiver: **RX4**. Pico firmware: **v0.6-RX2**, RAM image. Android transmitter: **Beacon Loop 1.1**.

## Read first

1. [Project README](../README.md): hardware wiring, quick start, scope.
2. [Setup on another Windows PC](SETUP_WINDOWS.md).
3. [Architecture and interfaces](INTEGRATION.md): what exists and what is still a proposal.
4. [File catalog](FILE_CATALOG.md): every published file and its purpose.
5. [AI handoff](AI_HANDOFF.md), then [repository instructions](../AGENTS.md).
6. [Illustrated RX4 report](../reports/RX4-2026-10-29/ANALYSIS_ZH.md).

## What is delivered

| Component | Current behavior | Limit |
|---|---|---|
| SEN0325 + Pico | Seven simultaneous channels, I2S/PIO/DMA capture, CRC-protected USB blocks | GPIO and physical geometry must be checked against the supplied board |
| Windows receiver | Beacon matching, delay estimation, bearing radar and received waveform/spectrum | Receive-only; radar rings do not measure range |
| RX4 estimator | Adds a joint spectral fit only after earlier fits fail | More accepted fits do not prove that the bearing is correct |
| Android player | Pick a local file, play/pause, repeat indefinitely; bundled current WAV | APK built and signed; S25 Ultra hardware/background playback still needs testing |
| Evidence | Saved measurements, model regressions, plots, replay methods | No synchronized physical ground-truth angles or reliable range acceptance yet |

The 29 October recording contains several playback rounds and manual interruptions. Its initial two-loop protocol was abandoned. Do not classify all pauses as receiver bugs. Identical-input replay produced 52 accepted RX3 outputs and 81 RX4 outputs, retaining previous accepted raw angles. These are replay counts, not accuracy percentages. Normal result intervals had a median of 187 ms; this is not acoustic-onset-to-correct-bearing latency.

## First bench session

Use the GPIO table in the root README, connect Pico, launch the desktop app and select Start Scan. Install [BeaconLoop-1.1.apk](../android-player/releases/BeaconLoop-1.1.apk) on the phone, then play 19-21 kHz beacon or Gap test 18-22 kHz. Use the same choice on the PC. Start at about 0.5 m with a fixed phone position and fixed volume. Check that the received spectrum shows the expected 19–21 kHz band before judging the arrow. Log the true physical angle and all intentional pauses.

Try the same file at known bearings and distances, changing only one variable per run. Keep normalization off for the baseline. The phone speaker and microphone array do not have a calibrated acoustic transfer function; software gain is not receiver ADC calibration.

## Responsibility boundaries

- This contribution owns microphone capture, beacon recognition, bearing estimation, visualizations and the local phone player.
- The operator owns wiring, safe supply, phone pose/volume, physical angle references and pause notes.
- ESP32 motor control, the forward distance sensor, obstacle handling and autonomous following are integration work. No motor-control path is implemented here.
- No teammate names or unconfirmed assignments are invented. Agree owners in the team before integration.

## Next work, in order

1. Test Android import, looping, pause/resume and screen-off playback on S25 Ultra.
2. Record fixed known bearings with timestamps; inspect both raw and displayed bearings.
3. Investigate current-frame arrival-fit alternatives and multipath using that evidence. Do not freeze or reject a large turn just because it is large.
4. Compare waveform experiments separately. Any new beacon must match the desktop reference; ordinary music or an arbitrary alarm file is not automatically compatible.
5. On branch `Pico-ESP32`, bench the optional UART link with a 1000 Hz tone (`esp32-link/README.md`). Keep RX4 for the 19–21 kHz coded beacon. Do not attach motors to `DOA` lines.

## History and sharing

Active source remains in SEN0325-Pico-Setup. Historical material is under legacy. Stages 01–05 are historical; stage 06 records RX4; stage 07 records this handoff. The repository includes current source, Android APK, firmware, audio, reports and selected historical source/docs. Original microphone recordings, runtime logs, machine settings, signing keys and redundant old binary archives are not uploaded. They are preserved in the owner's complete local ZIP and indexed locally. See [sharing policy](SHARING.md).

The project is a private team handoff. No open-source licence has been assigned. Third-party documents retain their original ownership.
