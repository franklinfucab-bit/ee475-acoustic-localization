# Current repeatable checks

Configured runtime: C:/Tools/Embedded/venv/Scripts/python.exe.

- verify_joint_delay.py: RX4 geometry, cache, motion, negative-input and same-input raw replay checks.
- verify_highband_20k.py --output stages/06-joint-delay/model-validation.json: original 20 kHz synthetic regression.
- verify_controls.py: receive-only state/cancellation regression.
- capture_rx4_phone_trial.py --gui --seconds 90: finite raw capture with the standard radar visible; Start Scan begins capture. No computer playback.
- analyze_rx4_phone_trial.py <trial.json> --plots: timeline, digital noise/spectrum analysis, CSV and PNG figures.
- replay_rx4_trial.py <trial.json>: exact RX3/RX4 comparison using the preserved before-RX4 source.
- plot_beacon_waveform.py: plot the unmodified current phone MP3.
- verify_raw_packet.py, verify_crc32_hardware.py, verify_packet_recovery_hardware.py and benchmark_latency.py: transport checks; live tools require exclusive serial access.
- verify_esp32_link.py: Pico–ESP32 FEAT/DOA text and 1000 Hz phase-model checks. Not RX4 and not a hardware UART test.

Old phase-specific tools are in legacy/tests. Current fixtures may be read from legacy/stages; current output belongs in stages/06-joint-delay. Plotting uses Matplotlib; the configured Python base installation supplies Pillow if the embedded venv lacks it. No physical accuracy claim follows from generated tests or replay counts.


## Fresh clone / team package

Run `python tools/verify_handoff.py` for source compilation, protocol/model/control checks and the RAM image check without private recordings. Its outputs go to stage 07. Plot dependencies are listed in requirements-plots.txt. See ../docs/SETUP_WINDOWS.md for a project-local Python environment.

verify_joint_delay.py performs a full historical raw-audio replay and therefore requires local-only legacy capture fixtures. It is intentionally not part of the fresh-clone check. Do not treat missing fixtures as a passing replay. Capture, recovery and live GUI tools need the physical Pico and exclusive serial access. Tests may write results; preserve old stage evidence before rerunning archival tests.
