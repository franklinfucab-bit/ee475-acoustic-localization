# Stage 08 — Gap-test beacon

Date: 3 November 2026. Desktop launch remains RX4 `coded-20`. Firmware is unchanged.

## Intended behavior

`coded-20` stays the one-click profile: continuous 19–21 kHz, one 4096-sample period. A second profile, `coded-gap`, is selectable in the receiver menu.

Each gap-test period is still 4096 samples (85.333 ms) at 48 kHz. The first 2048 samples are an 18–22 kHz coded burst with 64-sample raised-cosine edges. The remaining 2048 samples are silence, about 43 ms. Pair-delay residual limits are unchanged. `coded-20` and `coded-gap` now share one tracking rule: Hit follows the peak and RMS, a miss does not clear history, each capture is estimated alone, and the arrival-time fit runs after any six-channel match. The 16–18 kHz profile keeps the older gates.

The period is not longer than one capture. `RECORD` does not keep the samples that occur while the host is between packets, so several packets cannot be stitched into one longer code.

## How to compare

1. Leave the phone on `audio/phone/HF2-20kHz/01_LOCATE_20kHz_19-21kHz.mp3` and the menu on **20 kHz beacon | 19-21 kHz**.
2. Switch the phone to `audio/phone/HF2-gap-test/01_LOCATE_18-22kHz_43ms-gap.wav` and the menu to **Gap test | 18-22 kHz**.
3. Keep distance, volume and phone orientation fixed. The wider band may be audible near 18 kHz.

Phone and receiver must use the same selection. This stage does not claim a better physical angle.
