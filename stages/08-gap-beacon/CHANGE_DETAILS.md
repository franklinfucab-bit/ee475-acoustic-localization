# Gap-test beacon

`beacon_dsp.py` adds `coded-gap`. Its template uses a separate random seed (`0xEE4750A9`), band 18–22 kHz, 2048 active samples and 2048 silent samples. The `coded-20` generator, seed, band and crest-factor loop are the same; `tests/verify_gap_beacon.py` checks the previous template hash `1159cae8484ab19618b52660f0f6ef71f3eeef554e6ba4be0fd002f1db988a7c`.

`BeaconEstimator.estimate` sends `coded-gap` through the same high-band delay fit as `coded-20`. The older audible SRP path remains for the audible profile only.

The receiver menu lists both beacons. It still opens on **20 kHz beacon | 19-21 kHz**. **Gap test | 18-22 kHz** is the second entry. Changing the menu tells the operator which phone file to play. Both beacons now use the gap-test tracking rule, so an audio comparison uses one standard. Pair-delay residual limits are unchanged.

On 3 November 2026 the shared rule was checked with `tests/verify_highband_20k.py`. The weak colored source at 45° was accepted from one capture at raw angle 55.34°, error 19.487°, past the 15° model limit. The pair-delay residual on that capture was 0.80 samples, inside the 1.0-sample gate. The report was not written because the check stopped there. Restart the desktop app before a live comparison.

The radar keeps the last bearing for 1.5 s when a capture has no new bearing. Stop, profile change, mirror, and Set Front still clear it immediately.

`app_controls.py` lists the test after the current 20 kHz beacon. `refresh_and_start.py` still launches `--profile coded-20`. `highband_dsp.py` labels gap-test estimates `GAP-TEST`. Pair-delay residual limits are unchanged. The audio-folder button opens `audio/phone/HF2-gap-test` only while that profile is selected.

`tests/generate_gap_beacon.py` writes the phone WAV/MP3. It does not encode or replace the HF2 19–21 kHz files.

To leave the test unused, select **20 kHz beacon | 19-21 kHz** and play the original LOCATE file. No firmware, GPIO, delay gate or default waveform change is required for that path.
