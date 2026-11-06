# Published file catalog

336 files. Relative paths start at the repository root. Historical entries are reference material, not the launch path. Original captures/logs and repeated local binary archives are intentionally excluded; see [SHARING.md](SHARING.md).

| File | Role | Function |
|---|---|---|
| `.gitattributes` | Project documentation / entry | Project configuration/artifact: .gitattributes |
| `.gitignore` | Project documentation / entry | Project configuration/artifact: .gitignore |
| `AGENTS.md` | Project documentation / entry | Repository instructions and constraints for coding agents |
| `Open-Project.cmd` | Project documentation / entry | Open the engineering workspace in VS Code |
| `README.md` | Project documentation / entry | Main project overview / entry point |
| `SEN0325-Pico-Setup/Build.ps1` | Active Pico + desktop receiver | Owner-layout Pico SDK RAM/Flash build helper |
| `SEN0325-Pico-Setup/CMakeLists.txt` | Active Pico + desktop receiver | Pico SDK build definition and USB buffer settings |
| `SEN0325-Pico-Setup/Load-RAM.ps1` | Active Pico + desktop receiver | Owner-layout picotool RAM loading helper |
| `SEN0325-Pico-Setup/Monitor.ps1` | Active Pico + desktop receiver | Owner-layout serial monitor helper |
| `SEN0325-Pico-Setup/README.md` | Active Pico + desktop receiver | Main project overview / entry point |
| `SEN0325-Pico-Setup/app_controls.py` | Active Pico + desktop receiver | Scan/profile state and cancellation rules |
| `SEN0325-Pico-Setup/app_instance.py` | Active Pico + desktop receiver | Instance nonce and graceful restart coordination |
| `SEN0325-Pico-Setup/array_geometry.json` | Active Pico + desktop receiver | Array channel geometry and display heading/mirror configuration |
| `SEN0325-Pico-Setup/arrival_dsp.py` | Active Pico + desktop receiver | Matched-code arrival fallback estimator |
| `SEN0325-Pico-Setup/beacon-audio/coded-16-18-v1-right-only.wav` | Active Pico + desktop receiver | Generated transmitter/reference audio: coded-16-18-v1-right-only |
| `SEN0325-Pico-Setup/beacon-audio/coded-20-v1-right-only.wav` | Active Pico + desktop receiver | Generated transmitter/reference audio: coded-20-v1-right-only |
| `SEN0325-Pico-Setup/beacon-audio/coded-audible-v1-right-only.wav` | Active Pico + desktop receiver | Generated transmitter/reference audio: coded-audible-v1-right-only |
| `SEN0325-Pico-Setup/beacon-audio/coded-audible-v1.wav` | Active Pico + desktop receiver | Generated transmitter/reference audio: coded-audible-v1 |
| `SEN0325-Pico-Setup/beacon-audio/coded-ultrasonic-v1-right-only.wav` | Active Pico + desktop receiver | Generated transmitter/reference audio: coded-ultrasonic-v1-right-only |
| `SEN0325-Pico-Setup/beacon-audio/coded-ultrasonic-v1.wav` | Active Pico + desktop receiver | Generated transmitter/reference audio: coded-ultrasonic-v1 |
| `SEN0325-Pico-Setup/beacon_dsp.py` | Active Pico + desktop receiver | Reference generation, beacon profiles and receiver object |
| `SEN0325-Pico-Setup/beacon_importer.py` | Active Pico + desktop receiver | Validate/import a compatible periodic MP3/WAV reference |
| `SEN0325-Pico-Setup/check_protocol.py` | Active Pico + desktop receiver | Firmware protocol validation helper |
| `SEN0325-Pico-Setup/crc32_fast.h` | Active Pico + desktop receiver | Table CRC32 implementation for raw packet protection |
| `SEN0325-Pico-Setup/direction_diagnostics.py` | Active Pico + desktop receiver | Finite asynchronous raw snapshots for delay diagnosis |
| `SEN0325-Pico-Setup/direction_estimator.py` | Active Pico + desktop receiver | Lower-frequency phase estimator and view calibration |
| `SEN0325-Pico-Setup/firmware/README.txt` | Active Pico + desktop receiver | Instructions/report: README |
| `SEN0325-Pico-Setup/firmware/sen0325_setup-RAM.elf` | Active Pico + desktop receiver | Pico firmware debug/executable artifact |
| `SEN0325-Pico-Setup/firmware/sen0325_setup-RAM.uf2` | Active Pico + desktop receiver | Pico firmware image; use current firmware/ image unless testing this historical version |
| `SEN0325-Pico-Setup/highband_dsp.py` | Active Pico + desktop receiver | High-band code detection, delay/arrival path selection and display smoothing |
| `SEN0325-Pico-Setup/joint_delay_dsp.py` | Active Pico + desktop receiver | RX4 full-angle joint spectral-delay rescue |
| `SEN0325-Pico-Setup/main.c` | Active Pico + desktop receiver | Pico firmware: synchronous capture, control commands and USB packets |
| `SEN0325-Pico-Setup/make_regular_tones.py` | Active Pico + desktop receiver | Generate diagnostic tone files |
| `SEN0325-Pico-Setup/radar_canvas.py` | Active Pico + desktop receiver | 2D bearing radar drawing |
| `SEN0325-Pico-Setup/raw_packet.py` | Active Pico + desktop receiver | Bounded USB read, header/length/CRC/trailer validation and resynchronization |
| `SEN0325-Pico-Setup/refresh_and_start.py` | Active Pico + desktop receiver | Source check, graceful restart request and new-instance confirmation |
| `SEN0325-Pico-Setup/requirements.txt` | Active Pico + desktop receiver | Instructions/report: requirements |
| `SEN0325-Pico-Setup/runtime_tuning.py` | Active Pico + desktop receiver | Host capture scheduling parameters |
| `SEN0325-Pico-Setup/sen0325_i2s.pio` | Active Pico + desktop receiver | PIO program for simultaneous digital microphone capture |
| `SEN0325-Pico-Setup/sen0325_launcher.py` | Active Pico + desktop receiver | Desktop Session, Pico discovery/loading, serial worker and application entry |
| `SEN0325-Pico-Setup/sen0325_simple_view.py` | Active Pico + desktop receiver | Main receive-only UI, controls and event handling |
| `SEN0325-Pico-Setup/sen0325_view.py` | Active Pico + desktop receiver | Advanced diagnostic/channel view |
| `SEN0325-Pico-Setup/signal_scope.py` | Active Pico + desktop receiver | Received waveform/spectrum computation and drawing |
| `SEN0325-Pico-Setup/tone_filter.h` | Active Pico + desktop receiver | Firmware tone-filter helper |
| `SEN0325-Pico-Setup/tracking_audio.py` | Active Pico + desktop receiver | Audio reference/playback utilities retained outside normal receive-only controls |
| `SEN0325-Pico-Setup/verify_ram.py` | Active Pico + desktop receiver | Validate that the supplied UF2 targets RAM rather than Flash |
| `esp32-link/README.md` | Optional Pico–ESP32 UART | Wiring, 1000 Hz bench steps and board-pin notes |
| `esp32-link/protocol.py` | Optional Pico–ESP32 UART | FEAT/DOA text parse and format |
| `esp32-link/view_doa.py` | Optional Pico–ESP32 UART | Display-only ESP32 USB reader; no RX4 and no RECORD |
| `esp32-link/esp32_doa/esp32_doa.ino` | Optional Pico–ESP32 UART | ESP32 UART2 sketch: parse FEAT, print DOA, no motors |
| `esp32-link/esp32_doa/phase_doa.h` | Optional Pico–ESP32 UART | 300–2000 Hz phase estimator ported from direction_estimator.py |
| `SHA256SUMS.txt` | Project documentation / entry | SHA-256 integrity list for published files except itself |
| `Setup-Windows.ps1` | Project documentation / entry | Create project-local Python environment and validate dependencies |
| `Update-and-Start.cmd` | Project documentation / entry | Select configured Python and invoke graceful local refresh/start |
| `android-player/Build.cmd` | Android transmitter | Utility/source: Build |
| `android-player/Build.ps1` | Android transmitter | Android SDK/JDK build and development signing |
| `android-player/QUICKSTART_ZH.md` | Android transmitter | Instructions/report: QUICKSTART ZH |
| `android-player/README.md` | Android transmitter | Main project overview / entry point |
| `android-player/app/src/main/AndroidManifest.xml` | Android transmitter | Android component, SDK and permission declarations |
| `android-player/app/src/main/assets/default-beacon.wav` | Android transmitter | Bundled unmodified current lossless phone beacon |
| `android-player/app/src/main/java/org/ee475/beaconloop/AudioLoader.java` | Android transmitter | Android media decode and format/size/duration limits |
| `android-player/app/src/main/java/org/ee475/beaconloop/LoopService.java` | Android transmitter | Android PCM loop, notification controls and audio-focus handling |
| `android-player/app/src/main/java/org/ee475/beaconloop/MainActivity.java` | Android transmitter | Android local file picker, play/pause and status UI |
| `android-player/app/src/main/java/org/ee475/beaconloop/PcmGain.java` | Android transmitter | Optional bounded constant PCM gain with peak ceiling |
| `android-player/app/src/main/res/drawable/ic_beacon.xml` | Android transmitter | Android UI resource/configuration |
| `android-player/app/src/main/res/values/styles.xml` | Android transmitter | Android UI resource/configuration |
| `android-player/releases/BeaconLoop-1.0.apk` | Android transmitter | Signed development Android loop-player installation package |
| `android-player/releases/BeaconLoop-1.1.apk` | Android transmitter | Beacon Loop 1.1 with built-in 19-21 kHz and gap-test choices |
| `android-player/sdk-downloads.json` | Android transmitter | Original official SDK package download provenance |
| `android-player/tests/PcmGainTest.java` | Android transmitter | Nine host-side checks for optional gain behavior |
| `android-player/toolchain.example.json` | Android transmitter | Example local SDK/JDK/Python/signing-key locations |
| `android-player/tools/merge_apk.py` | Android transmitter | Insert compiled dex into unsigned APK resources |
| `android-player/validation.json` | Android transmitter | Recorded configuration, validation or provenance: validation |
| `audio/phone/HF2-20kHz/01_LOCATE_20kHz_19-21kHz.mp3` | Transmitter/reference audio | Phone coded localization beacon (match receiver profile) |
| `audio/phone/HF2-20kHz/11_TONE_19000Hz_level-only.mp3` | Transmitter/reference audio | Frequency/level probe; does not alone authorize a bearing |
| `audio/phone/HF2-20kHz/12_TONE_19500Hz_level-only.mp3` | Transmitter/reference audio | Frequency/level probe; does not alone authorize a bearing |
| `audio/phone/HF2-20kHz/13_TONE_20000Hz_level-only.mp3` | Transmitter/reference audio | Frequency/level probe; does not alone authorize a bearing |
| `audio/phone/HF2-20kHz/14_TONE_20500Hz_level-only.mp3` | Transmitter/reference audio | Frequency/level probe; does not alone authorize a bearing |
| `audio/phone/HF2-20kHz/15_TONE_21000Hz_level-only.mp3` | Transmitter/reference audio | Frequency/level probe; does not alone authorize a bearing |
| `audio/phone/HF2-20kHz/README.txt` | Transmitter/reference audio | Instructions/report: README |
| `audio/phone/README.txt` | Transmitter/reference audio | Instructions/report: README |
| `audio/reference/coded_20khz_19_21_right.wav` | Transmitter/reference audio | Generated transmitter/reference audio: coded_20khz_19_21_right |
| `docs/AI_HANDOFF.md` | Project documentation / entry | AI continuation map, constraints, evidence and verification |
| `docs/ARCHITECTURE.md` | Project documentation / entry | Instructions/report: ARCHITECTURE |
| `docs/FILE_CATALOG.csv` | Project documentation / entry | Machine-readable published file catalog |
| `docs/FILE_CATALOG.md` | Project documentation / entry | Every published file with its role and purpose |
| `docs/HARDWARE.md` | Project documentation / entry | Instructions/report: HARDWARE |
| `docs/INTEGRATION.md` | Project documentation / entry | System composition, USB/data contracts and unimplemented robot boundary |
| `docs/ROLES.md` | Project documentation / entry | Instructions/report: ROLES |
| `docs/ROLES_ZH.md` | Project documentation / entry | Instructions/report: ROLES ZH |
| `docs/SETUP_WINDOWS.md` | Project documentation / entry | Environment setup on another Windows computer |
| `docs/SHARING.md` | Project documentation / entry | Published versus local-only content and archive policy |
| `docs/TEAM_HANDOFF.md` | Project documentation / entry | English teammate handoff and next steps |
| `docs/TEAM_HANDOFF_ZH.md` | Project documentation / entry | Chinese teammate handoff and next steps |
| `docs/USER_GUIDE.md` | Project documentation / entry | Instructions/report: USER GUIDE |
| `docs/VALIDATION.md` | Project documentation / entry | Instructions/report: VALIDATION |
| `legacy/README-before-RX4-organization.md` | Historical reference; not active launch code | Instructions/report: README before RX4 organization |
| `legacy/README.md` | Historical reference; not active launch code | Main project overview / entry point |
| `legacy/audio/HF1-MP3/01_LOCATE_16-18kHz.mp3` | Historical reference; not active launch code | Phone coded localization beacon (match receiver profile) |
| `legacy/audio/HF1-MP3/02_LOCATE_Audible.mp3` | Historical reference; not active launch code | Generated transmitter/reference audio: 02_LOCATE_Audible |
| `legacy/audio/HF1-MP3/11_TONE_1000Hz_level-only.mp3` | Historical reference; not active launch code | Frequency/level probe; does not alone authorize a bearing |
| `legacy/audio/HF1-MP3/12_TONE_16000Hz_level-only.mp3` | Historical reference; not active launch code | Frequency/level probe; does not alone authorize a bearing |
| `legacy/audio/HF1-MP3/13_TONE_17000Hz_level-only.mp3` | Historical reference; not active launch code | Frequency/level probe; does not alone authorize a bearing |
| `legacy/audio/HF1-MP3/14_TONE_17500Hz_level-only.mp3` | Historical reference; not active launch code | Frequency/level probe; does not alone authorize a bearing |
| `legacy/audio/HF1-MP3/15_TONE_18000Hz_level-only.mp3` | Historical reference; not active launch code | Frequency/level probe; does not alone authorize a bearing |
| `legacy/audio/HF1-MP3/README.txt` | Historical reference; not active launch code | Instructions/report: README |
| `legacy/audio/audible_beacon_right.wav` | Historical reference; not active launch code | Generated transmitter/reference audio: audible_beacon_right |
| `legacy/audio/coded_16_18khz_stage1_right.wav` | Historical reference; not active launch code | Generated transmitter/reference audio: coded_16_18khz_stage1_right |
| `legacy/audio/ultrasonic_experimental_right.wav` | Historical reference; not active launch code | Generated transmitter/reference audio: ultrasonic_experimental_right |
| `legacy/docs/ARCHITECTURE.md` | Historical reference; not active launch code | Instructions/report: ARCHITECTURE |
| `legacy/docs/HARDWARE.md` | Historical reference; not active launch code | Instructions/report: HARDWARE |
| `legacy/docs/SLACK_WEEKLY_UPDATE_ZH.txt` | Historical reference; not active launch code | Instructions/report: SLACK WEEKLY UPDATE ZH |
| `legacy/docs/USER_GUIDE.md` | Historical reference; not active launch code | Instructions/report: USER GUIDE |
| `legacy/docs/VALIDATION.md` | Historical reference; not active launch code | Instructions/report: VALIDATION |
| `legacy/docs/WEEKLY_UPDATE_BILINGUAL.md` | Historical reference; not active launch code | Instructions/report: WEEKLY UPDATE BILINGUAL |
| `legacy/docs/WEEKLY_UPDATE_EN.md` | Historical reference; not active launch code | Instructions/report: WEEKLY UPDATE EN |
| `legacy/docs/WEEKLY_UPDATE_SHORT_BILINGUAL.txt` | Historical reference; not active launch code | Instructions/report: WEEKLY UPDATE SHORT BILINGUAL |
| `legacy/docs/WEEKLY_UPDATE_ZH.md` | Historical reference; not active launch code | Instructions/report: WEEKLY UPDATE ZH |
| `legacy/experiments/RX4-prototypes/common-weights-experiment.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: common weights experiment |
| `legacy/experiments/RX4-prototypes/direct-model-negative-prototype.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: direct model negative prototype |
| `legacy/experiments/RX4-prototypes/gate-experiment.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: gate experiment |
| `legacy/experiments/RX4-prototypes/inconsistent-delay-prototype-negative.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: inconsistent delay prototype negative |
| `legacy/experiments/RX4-prototypes/joint-spectral-experiment.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: joint spectral experiment |
| `legacy/experiments/RX4-prototypes/joint-spectral-v2-experiment.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: joint spectral v2 experiment |
| `legacy/experiments/RX4-prototypes/prototype-replay.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: prototype replay |
| `legacy/experiments/RX4-prototypes/subset-delay-experiment.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: subset delay experiment |
| `legacy/launchers/Start-16-18kHz.cmd` | Historical reference; not active launch code | Utility/source: Start 16 18kHz |
| `legacy/launchers/一键启动麦克风测试.cmd` | Historical reference; not active launch code | Utility/source: 一键启动麦克风测试 |
| `legacy/launchers/类雷达声音定位.cmd` | Historical reference; not active launch code | Utility/source: 类雷达声音定位 |
| `legacy/reports/README.txt` | Historical reference; not active launch code | Instructions/report: README |
| `legacy/reports/delay-diagnosis-2026-10-22/DELAY_DIAGNOSIS.txt` | Historical reference; not active launch code | Instructions/report: DELAY DIAGNOSIS |
| `legacy/reports/delay-diagnosis-2026-10-22/DELAY_DIAGNOSIS_ZH.md` | Historical reference; not active launch code | Instructions/report: DELAY DIAGNOSIS ZH |
| `legacy/reports/delay-diagnosis-2026-10-22/diagnostic-evidence.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: diagnostic evidence |
| `legacy/reports/delay-diagnosis-2026-10-22/packet-error-context.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: packet error context |
| `legacy/reports/delay-followup-2026-10-27/DELAY_FOLLOWUP_ZH.md` | Historical reference; not active launch code | Instructions/report: DELAY FOLLOWUP ZH |
| `legacy/reports/delay-followup-2026-10-27/DELAY_FOLLOWUP_ZH.txt` | Historical reference; not active launch code | Instructions/report: DELAY FOLLOWUP ZH |
| `legacy/reports/direction-continuity-2026-10-27/DIRECTION_CONTINUITY_ZH.md` | Historical reference; not active launch code | Instructions/report: DIRECTION CONTINUITY ZH |
| `legacy/reports/direction-continuity-2026-10-27/README.md` | Historical reference; not active launch code | Main project overview / entry point |
| `legacy/reports/latency-reduction-2026-10-27/LATENCY_REDUCTION_ZH.md` | Historical reference; not active launch code | Instructions/report: LATENCY REDUCTION ZH |
| `legacy/reports/latency-reduction-2026-10-27/LATENCY_REDUCTION_ZH.txt` | Historical reference; not active launch code | Instructions/report: LATENCY REDUCTION ZH |
| `legacy/reports/packaging-validation.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: packaging validation |
| `legacy/reports/phone-observation-2026-10-27/OBSERVATION_ZH.md` | Historical reference; not active launch code | Instructions/report: OBSERVATION ZH |
| `legacy/reports/phone-observation-2026-10-27/README.md` | Historical reference; not active launch code | Main project overview / entry point |
| `legacy/reports/phone-observation-2026-10-27/observation.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: observation |
| `legacy/reports/pre-packaging-manifest.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: pre packaging manifest |
| `legacy/reports/release-files.sha256` | Historical reference; not active launch code | Recorded configuration, validation or provenance: release files |
| `legacy/reports/release-verification.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: release verification |
| `legacy/reports/validation/beacon-hardware-coded-audible-negative-1000hz.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: beacon hardware coded audible negative 1000hz |
| `legacy/reports/validation/beacon-hardware-coded-audible-right-only.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: beacon hardware coded audible right only |
| `legacy/reports/validation/beacon-hardware-coded-ultrasonic-right-only.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: beacon hardware coded ultrasonic right only |
| `legacy/reports/validation/beacon-model-validation.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: beacon model validation |
| `legacy/reports/validation/english-ui-validation.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: english ui validation |
| `legacy/reports/validation/ram-validation.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: ram validation |
| `legacy/reports/validation/refresh-rate-benchmark.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: refresh rate benchmark |
| `legacy/reports/validation/refresh-response-validation.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: refresh response validation |
| `legacy/reports/validation/simple-controls-validation.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: simple controls validation |
| `legacy/reports/validation/simple-ui-smoke-test.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: simple ui smoke test |
| `legacy/stages/01-16-18kHz/CHANGE_DETAILS.md` | Historical reference; not active launch code | Instructions/report: CHANGE DETAILS |
| `legacy/stages/01-16-18kHz/HF1_1_UPDATE.md` | Historical reference; not active launch code | Instructions/report: HF1 1 UPDATE |
| `legacy/stages/01-16-18kHz/PROGRESS_NOTES.md` | Historical reference; not active launch code | Instructions/report: PROGRESS NOTES |
| `legacy/stages/01-16-18kHz/README-before-HF1.md` | Historical reference; not active launch code | Instructions/report: README before HF1 |
| `legacy/stages/01-16-18kHz/README.md` | Historical reference; not active launch code | Main project overview / entry point |
| `legacy/stages/01-16-18kHz/TEST_NOTES.md` | Historical reference; not active launch code | Instructions/report: TEST NOTES |
| `legacy/stages/01-16-18kHz/arrival-scope-validation.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: arrival scope validation |
| `legacy/stages/01-16-18kHz/before-stage-1-hashes.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: before stage 1 hashes |
| `legacy/stages/01-16-18kHz/before-stage-1.zip` | Historical reference; not active launch code | Reviewed source baseline needed by regression/replay tools |
| `legacy/stages/01-16-18kHz/controls-validation.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: controls validation |
| `legacy/stages/01-16-18kHz/english-ui-validation.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: english ui validation |
| `legacy/stages/01-16-18kHz/model-validation.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: model validation |
| `legacy/stages/01-16-18kHz/mp3-validation.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: mp3 validation |
| `legacy/stages/01-16-18kHz/phone-debug/arrival-replay.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: arrival replay |
| `legacy/stages/01-16-18kHz/phone-debug/highband-before-fix.py` | Historical reference; not active launch code | Utility/source: highband before fix |
| `legacy/stages/01-16-18kHz/phone-debug/peak-analysis.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: peak analysis |
| `legacy/stages/01-16-18kHz/phone-debug/phone-capture-metrics.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: phone capture metrics |
| `legacy/stages/01-16-18kHz/phone-debug/ui-before-signal-chart.py` | Historical reference; not active launch code | Utility/source: ui before signal chart |
| `legacy/stages/01-16-18kHz/pico-capture-summary.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: pico capture summary |
| `legacy/stages/01-16-18kHz/pico-ui-before-scanner-only.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: pico ui before scanner only |
| `legacy/stages/01-16-18kHz/pico-ui-validation.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: pico ui validation |
| `legacy/stages/01-16-18kHz/release-manifest.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: release manifest |
| `legacy/stages/01-16-18kHz/release-summary.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: release summary |
| `legacy/stages/01-16-18kHz/unchanged-hardware-assets.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: unchanged hardware assets |
| `legacy/stages/02-20kHz/CHANGE_DETAILS.md` | Historical reference; not active launch code | Instructions/report: CHANGE DETAILS |
| `legacy/stages/02-20kHz/PROGRESS_NOTES.md` | Historical reference; not active launch code | Instructions/report: PROGRESS NOTES |
| `legacy/stages/02-20kHz/README.md` | Historical reference; not active launch code | Main project overview / entry point |
| `legacy/stages/02-20kHz/controls-validation.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: controls validation |
| `legacy/stages/02-20kHz/direction-guard-validation.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: direction guard validation |
| `legacy/stages/02-20kHz/english-ui-validation.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: english ui validation |
| `legacy/stages/02-20kHz/import-validation.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: import validation |
| `legacy/stages/02-20kHz/live-before-reverse-fix.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: live before reverse fix |
| `legacy/stages/02-20kHz/model-validation.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: model validation |
| `legacy/stages/02-20kHz/mp3-validation.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: mp3 validation |
| `legacy/stages/02-20kHz/rejected-guard-policy/README.txt` | Historical reference; not active launch code | Instructions/report: README |
| `legacy/stages/02-20kHz/rejected-guard-policy/verify_direction_guards.py` | Historical reference; not active launch code | Utility/source: verify direction guards |
| `legacy/stages/03-packet-timing/CHANGE_DETAILS.md` | Historical reference; not active launch code | Instructions/report: CHANGE DETAILS |
| `legacy/stages/03-packet-timing/PROGRESS_NOTES.md` | Historical reference; not active launch code | Instructions/report: PROGRESS NOTES |
| `legacy/stages/03-packet-timing/README.md` | Historical reference; not active launch code | Main project overview / entry point |
| `legacy/stages/03-packet-timing/baseline-manifest.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: baseline manifest |
| `legacy/stages/03-packet-timing/checkpoint-files.sha256` | Historical reference; not active launch code | Recorded configuration, validation or provenance: checkpoint files |
| `legacy/stages/03-packet-timing/checkpoint-validation.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: checkpoint validation |
| `legacy/stages/03-packet-timing/controls-validation.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: controls validation |
| `legacy/stages/03-packet-timing/hardware-recovery-validation.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: hardware recovery validation |
| `legacy/stages/03-packet-timing/high-resolution-baseline.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: high resolution baseline |
| `legacy/stages/03-packet-timing/host-baseline.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: host baseline |
| `legacy/stages/03-packet-timing/packet-fault-validation.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: packet fault validation |
| `legacy/stages/03-packet-timing/preserved-components.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: preserved components |
| `legacy/stages/03-packet-timing/ui-validation.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: ui validation |
| `legacy/stages/03-packet-timing/updated-ui-timing.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: updated ui timing |
| `legacy/stages/04-latency-reduction/CHANGE_DETAILS.md` | Historical reference; not active launch code | Instructions/report: CHANGE DETAILS |
| `legacy/stages/04-latency-reduction/PROGRESS_NOTES.md` | Historical reference; not active launch code | Instructions/report: PROGRESS NOTES |
| `legacy/stages/04-latency-reduction/README.md` | Historical reference; not active launch code | Main project overview / entry point |
| `legacy/stages/04-latency-reduction/auto-upgrade-validation.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: auto upgrade validation |
| `legacy/stages/04-latency-reduction/automatic-upgrade.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: automatic upgrade |
| `legacy/stages/04-latency-reduction/baseline-manifest.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: baseline manifest |
| `legacy/stages/04-latency-reduction/checkpoint-files.sha256` | Historical reference; not active launch code | Recorded configuration, validation or provenance: checkpoint files |
| `legacy/stages/04-latency-reduction/checkpoint-validation.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: checkpoint validation |
| `legacy/stages/04-latency-reduction/controls-validation.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: controls validation |
| `legacy/stages/04-latency-reduction/crc32-hardware-validation.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: crc32 hardware validation |
| `legacy/stages/04-latency-reduction/ep1024-candidate.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: ep1024 candidate |
| `legacy/stages/04-latency-reduction/ep1024-ram-validation.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: ep1024 ram validation |
| `legacy/stages/04-latency-reduction/experiments/fast-crc-4096-1024-RAM.uf2` | Historical reference; not active launch code | Pico firmware image; use current firmware/ image unless testing this historical version |
| `legacy/stages/04-latency-reduction/experiments/fast-crc-4096-512-RAM.uf2` | Historical reference; not active launch code | Pico firmware image; use current firmware/ image unless testing this historical version |
| `legacy/stages/04-latency-reduction/experiments/instrumented-64-64-RAM.uf2` | Historical reference; not active launch code | Pico firmware image; use current firmware/ image unless testing this historical version |
| `legacy/stages/04-latency-reduction/experiments/original-v0.5-RAM.elf` | Historical reference; not active launch code | Pico firmware debug/executable artifact |
| `legacy/stages/04-latency-reduction/experiments/original-v0.5-RAM.uf2` | Historical reference; not active launch code | Pico firmware image; use current firmware/ image unless testing this historical version |
| `legacy/stages/04-latency-reduction/experiments/usb-4096-512-RAM.uf2` | Historical reference; not active launch code | Pico firmware image; use current firmware/ image unless testing this historical version |
| `legacy/stages/04-latency-reduction/experiments/usb-4096-512-rx512-RAM.uf2` | Historical reference; not active launch code | Pico firmware image; use current firmware/ image unless testing this historical version |
| `legacy/stages/04-latency-reduction/fast-crc-ram-validation.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: fast crc ram validation |
| `legacy/stages/04-latency-reduction/fast-crc.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: fast crc |
| `legacy/stages/04-latency-reduction/firmware-manifest.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: firmware manifest |
| `legacy/stages/04-latency-reduction/hardware-recovery-validation.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: hardware recovery validation |
| `legacy/stages/04-latency-reduction/instrumented-64-64.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: instrumented 64 64 |
| `legacy/stages/04-latency-reduction/legacy-ram-validation.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: legacy ram validation |
| `legacy/stages/04-latency-reduction/packet-fault-validation.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: packet fault validation |
| `legacy/stages/04-latency-reduction/preserved-components.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: preserved components |
| `legacy/stages/04-latency-reduction/ui-timing.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: ui timing |
| `legacy/stages/04-latency-reduction/ui-validation.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: ui validation |
| `legacy/stages/04-latency-reduction/usb-batching.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: usb batching |
| `legacy/stages/04-latency-reduction/usb-ram-validation.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: usb ram validation |
| `legacy/stages/05-direction-diagnostics/CHANGE_DETAILS.md` | Historical reference; not active launch code | Instructions/report: CHANGE DETAILS |
| `legacy/stages/05-direction-diagnostics/PROGRESS_NOTES.md` | Historical reference; not active launch code | Instructions/report: PROGRESS NOTES |
| `legacy/stages/05-direction-diagnostics/README.md` | Historical reference; not active launch code | Main project overview / entry point |
| `legacy/stages/05-direction-diagnostics/after-files.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: after files |
| `legacy/stages/05-direction-diagnostics/before-files.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: before files |
| `legacy/stages/05-direction-diagnostics/checkpoint-files.sha256` | Historical reference; not active launch code | Recorded configuration, validation or provenance: checkpoint files |
| `legacy/stages/05-direction-diagnostics/checkpoint-validation.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: checkpoint validation |
| `legacy/stages/05-direction-diagnostics/confirmation-diagnostics-validation.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: confirmation diagnostics validation |
| `legacy/stages/05-direction-diagnostics/controls-validation.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: controls validation |
| `legacy/stages/05-direction-diagnostics/gui-validation.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: gui validation |
| `legacy/stages/05-direction-diagnostics/live-observation.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: live observation |
| `legacy/stages/05-direction-diagnostics/model-validation.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: model validation |
| `legacy/stages/05-direction-diagnostics/pair-closure-analysis.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: pair closure analysis |
| `legacy/stages/05-direction-diagnostics/replays/launcher-20261027-175338-954951-delay_rejection-seq6635-analysis.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: launcher 20261027 175338 954951 delay_rejection seq6635 analysis |
| `legacy/stages/05-direction-diagnostics/replays/launcher-20261027-175338-954951-delay_rejection-seq6725-analysis.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: launcher 20261027 175338 954951 delay_rejection seq6725 analysis |
| `legacy/stages/05-direction-diagnostics/single-burst-experiment.json` | Historical reference; not active launch code | Recorded configuration, validation or provenance: single burst experiment |
| `legacy/tests/analyze_delay_closure.py` | Historical reference; not active launch code | Utility/source: analyze delay closure |
| `legacy/tests/analyze_highband_capture.py` | Historical reference; not active launch code | Utility/source: analyze highband capture |
| `legacy/tests/capture_highband_diagnostic.py` | Historical reference; not active launch code | Utility/source: capture highband diagnostic |
| `legacy/tests/diagnose_delay_pipeline.py` | Historical reference; not active launch code | Utility/source: diagnose delay pipeline |
| `legacy/tests/explore_direction_capture.py` | Historical reference; not active launch code | Utility/source: explore direction capture |
| `legacy/tests/explore_highband_arrivals.py` | Historical reference; not active launch code | Utility/source: explore highband arrivals |
| `legacy/tests/finalize_highband_stage1.py` | Historical reference; not active launch code | Utility/source: finalize highband stage1 |
| `legacy/tests/generate_phone_mp3.py` | Historical reference; not active launch code | Utility/source: generate phone mp3 |
| `legacy/tests/package_highband_stage1.py` | Historical reference; not active launch code | Utility/source: package highband stage1 |
| `legacy/tests/probe_packet_timing.py` | Historical reference; not active launch code | Utility/source: probe packet timing |
| `legacy/tests/replay_direction_diagnostics.py` | Historical reference; not active launch code | Utility/source: replay direction diagnostics |
| `legacy/tests/verify_arrival_scope.py` | Historical reference; not active launch code | Utility/source: verify arrival scope |
| `legacy/tests/verify_beacon_model.py` | Historical reference; not active launch code | Utility/source: verify beacon model |
| `legacy/tests/verify_direction_diagnostics.py` | Historical reference; not active launch code | Utility/source: verify direction diagnostics |
| `legacy/tests/verify_highband_stage1.py` | Historical reference; not active launch code | Utility/source: verify highband stage1 |
| `legacy/tests/write_delay_diagnosis_report.py` | Historical reference; not active launch code | Utility/source: write delay diagnosis report |
| `references/README.txt` | Original hardware/project reference | Instructions/report: README |
| `references/Tagalong_Project_Notes.docx` | Original hardware/project reference | Original team project notes/proposal |
| `references/Tagalong_Proposal.pptx` | Original hardware/project reference | Original team project notes/proposal |
| `references/hardware/MSM261S4030H0.pdf` | Original hardware/project reference | Original board/microphone technical reference |
| `references/hardware/Pico-backside-user.jpg` | Original hardware/project reference | User-supplied hardware/reference photograph |
| `references/hardware/Pico-installed-user.jpg` | Original hardware/project reference | User-supplied hardware/reference photograph |
| `references/hardware/SEN0325-array-datasheet.pdf` | Original hardware/project reference | Original board/microphone technical reference |
| `references/hardware/SEN0325-connector-user.jpg` | Original hardware/project reference | User-supplied hardware/reference photograph |
| `references/hardware/SEN0325-schematic.pdf` | Original hardware/project reference | Original board/microphone technical reference |
| `reports/README.md` | Human-readable findings and figures | Main project overview / entry point |
| `reports/RX4-2026-10-29/ANALYSIS_ZH.md` | Human-readable findings and figures | Instructions/report: ANALYSIS ZH |
| `reports/RX4-2026-10-29/README.md` | Human-readable findings and figures | Main project overview / entry point |
| `reports/RX4-2026-10-29/figures/high-band-spectrum.png` | Human-readable findings and figures | Report visualization: high band spectrum |
| `reports/RX4-2026-10-29/figures/original-beacon-waveform.json` | Human-readable findings and figures | Recorded configuration, validation or provenance: original beacon waveform |
| `reports/RX4-2026-10-29/figures/original-beacon-waveform.png` | Human-readable findings and figures | Report visualization: original beacon waveform |
| `reports/RX4-2026-10-29/figures/received-spectrum.png` | Human-readable findings and figures | Report visualization: received spectrum |
| `reports/RX4-2026-10-29/figures/signal-and-direction.png` | Human-readable findings and figures | Report visualization: signal and direction |
| `stages/06-joint-delay/CHANGE_DETAILS.md` | Stage record / reproducibility evidence | Instructions/report: CHANGE DETAILS |
| `stages/06-joint-delay/PROGRESS_NOTES.md` | Stage record / reproducibility evidence | Instructions/report: PROGRESS NOTES |
| `stages/06-joint-delay/README.md` | Stage record / reproducibility evidence | Main project overview / entry point |
| `stages/06-joint-delay/backups/before-RX4.zip` | Stage record / reproducibility evidence | Reviewed source baseline needed by regression/replay tools |
| `stages/06-joint-delay/before-files.json` | Stage record / reproducibility evidence | Recorded configuration, validation or provenance: before files |
| `stages/06-joint-delay/checkpoint-validation.json` | Stage record / reproducibility evidence | Recorded configuration, validation or provenance: checkpoint validation |
| `stages/06-joint-delay/controls-validation.json` | Stage record / reproducibility evidence | Recorded configuration, validation or provenance: controls validation |
| `stages/06-joint-delay/gui-validation.json` | Stage record / reproducibility evidence | Recorded configuration, validation or provenance: gui validation |
| `stages/06-joint-delay/joint-delay-validation.json` | Stage record / reproducibility evidence | Recorded configuration, validation or provenance: joint delay validation |
| `stages/06-joint-delay/model-validation.json` | Stage record / reproducibility evidence | Recorded configuration, validation or provenance: model validation |
| `stages/06-joint-delay/one-click-validation.json` | Stage record / reproducibility evidence | Recorded configuration, validation or provenance: one click validation |
| `stages/06-joint-delay/selected-source-sha256.json` | Stage record / reproducibility evidence | Recorded configuration, validation or provenance: selected source sha256 |
| `stages/07-team-handoff/CHANGE_DETAILS.md` | Stage record / reproducibility evidence | Instructions/report: CHANGE DETAILS |
| `stages/07-team-handoff/PROGRESS_NOTES.md` | Stage record / reproducibility evidence | Instructions/report: PROGRESS NOTES |
| `stages/07-team-handoff/README.md` | Stage record / reproducibility evidence | Main project overview / entry point |
| `stages/09-esp32-link/README.md` | Stage record / reproducibility evidence | Pico–ESP32 UART stage notes |
| `stages/09-esp32-link/CHANGE_DETAILS.md` | Stage record / reproducibility evidence | Firmware/protocol/viewer change list |
| `stages/09-esp32-link/verification/build-checks.json` | Stage record / reproducibility evidence | Host FEAT/DOA and 1000 Hz phase-model results |
| `tests/verify_esp32_link.py` | Verification / maintenance | FEAT/DOA protocol and 1000 Hz phase-model checks |
| `stages/07-team-handoff/preserved-components.json` | Stage record / reproducibility evidence | Recorded configuration, validation or provenance: preserved components |
| `stages/07-team-handoff/validation.json` | Stage record / reproducibility evidence | Recorded configuration, validation or provenance: validation |
| `stages/07-team-handoff/verification/controls.json` | Stage record / reproducibility evidence | Recorded configuration, validation or provenance: controls |
| `stages/07-team-handoff/verification/joint-private-replay.json` | Stage record / reproducibility evidence | Recorded configuration, validation or provenance: joint private replay |
| `stages/07-team-handoff/verification/model.json` | Stage record / reproducibility evidence | Recorded configuration, validation or provenance: model |
| `stages/07-team-handoff/verification/packet-faults.json` | Stage record / reproducibility evidence | Recorded configuration, validation or provenance: packet faults |
| `stages/07-team-handoff/verification/validation.json` | Stage record / reproducibility evidence | Recorded configuration, validation or provenance: validation |
| `tests/README.md` | Verification / maintenance | Main project overview / entry point |
| `tests/analyze_rx4_phone_trial.py` | Verification / maintenance | Analyze saved trial timing, spectra, level and bearing events |
| `tests/benchmark_latency.py` | Verification / maintenance | Measure physical packet/pipeline timing |
| `tests/capture_rx4_phone_trial.py` | Verification / maintenance | Finite seven-channel phone trial capture with optional GUI |
| `tests/generate_phone_mp3_20k.py` | Verification / maintenance | Generate and validate current phone MP3 beacon/probes |
| `tests/plot_beacon_waveform.py` | Verification / maintenance | Plot original beacon amplitude, sample detail and spectrogram |
| `tests/replay_rx4_trial.py` | Verification / maintenance | Run exact saved samples through RX3 and RX4 |
| `tests/requirements-audio.txt` | Verification / maintenance | Instructions/report: requirements audio |
| `tests/requirements-plots.txt` | Verification / maintenance | Instructions/report: requirements plots |
| `tests/verify_beacon_import.py` | Verification / maintenance | Compatible reference import regression |
| `tests/verify_controls.py` | Verification / maintenance | Receive-only controls, profile state and cancelled capture checks |
| `tests/verify_crc32_hardware.py` | Verification / maintenance | Physical USB packet CRC check |
| `tests/verify_english_ui.py` | Verification / maintenance | English UI smoke checks; needs the intended environment/device |
| `tests/verify_highband_20k.py` | Verification / maintenance | Synthetic high-band receiver regression with old code baseline |
| `tests/verify_joint_delay.py` | Verification / maintenance | Full RX4 model/cache/turn checks plus private saved-recording replay |
| `tests/verify_packet_recovery_hardware.py` | Verification / maintenance | Physical malformed/partial packet recovery check |
| `tests/verify_raw_packet.py` | Verification / maintenance | Simulated packet faults, timeout, cancellation and resynchronization |
| `tools/package_release.py` | Verification / maintenance | Generate file catalogs, checksums and share/local ZIP packages |
| `tools/verify_handoff.py` | Verification / maintenance | Offline checks runnable without private recordings or a connected board |
| `一键启动雷达.cmd` | Project documentation / entry | Chinese shortcut to current receiver launcher |
