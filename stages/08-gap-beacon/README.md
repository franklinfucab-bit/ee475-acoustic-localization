# Stage 08 — Gap-test beacon

Date: 5 November 2026. One-click launch opens on `coded-gap`. Firmware is unchanged.

## Intended behavior

The window opens on **Gap test | 18-22 kHz**. **20 kHz beacon | 19-21 kHz** stays in the menu. The 19–21 kHz waveform is unchanged.

Each gap-test period is still 4096 samples (85.333 ms) at 48 kHz. The first 2048 samples are an 18–22 kHz coded burst with 64-sample raised-cosine edges. The remaining 2048 samples are silence, about 43 ms. Pair-delay residual limits are unchanged. `coded-20` and `coded-gap` now share one tracking rule: Hit follows the peak and RMS, a miss does not clear history, each capture is estimated alone, and the arrival-time fit runs after any six-channel match. The 16–18 kHz profile keeps the older gates.

The period is not longer than one capture. `RECORD` does not keep the samples that occur while the host is between packets, so several packets cannot be stitched into one longer code.

## How to compare

1. The PC opens on **Gap test | 18-22 kHz**. Play `audio/phone/HF2-gap-test/01_LOCATE_18-22kHz_43ms-gap.wav`.
2. For the older beacon, select **20 kHz beacon | 19-21 kHz** and play `audio/phone/HF2-20kHz/01_LOCATE_20kHz_19-21kHz.mp3`.
3. Keep distance, volume and phone orientation fixed. The wider band may be audible near 18 kHz.

Phone and receiver must use the same selection. This stage does not claim a better physical angle.
