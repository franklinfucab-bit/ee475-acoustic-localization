# Beacon Loop 1.1 — Android local audio player

[Install APK](releases/BeaconLoop-1.1.apk) · [Chinese quick start](QUICKSTART_ZH.md)

A small offline transmitter companion for EE475. Choose a local audio file, then play/pause an infinite loop. Two beacons are bundled: the current 19–21 kHz file and the 18–22 kHz gap test. The first launch still plays 19–21 kHz. Android 8.0+ (API 26), target API 35, package org.ee475.beaconloop.

## Use

1. Install the APK on the phone. Android may ask you to permit installation from the app used to open it.
2. Open Beacon Loop. Choose 19-21 kHz beacon, Gap test 18-22 kHz, or Choose audio file. On the PC, select the matching beacon before Start Scan.
3. Press Play. Use the phone's media volume buttons; Pause stops playback.
4. Keep Normalize off for baseline localization tests. Notification controls provide pause/play and stop while the playback service is active.

WAV is preferred for precise repeat tests. Supported files depend on the Android media decoder; mono/stereo files only, at most 120 seconds, 64 MiB source and 32 MiB decoded PCM. Files are decoded once and played with a native static AudioTrack loop. Existing source silence, fades or codec padding are not removed. Physical gapless output, screen-off behavior and S25 Ultra audio processing have not yet been accepted on a device.

Normalize is an optional constant gain, capped at +3 dB and with a -3 dBFS peak ceiling. Loud inputs may be attenuated; silence is not amplified. Original files, frequency, code, timing and channel layout are preserved. It is not microphone ADC calibration and does not guarantee more acoustic range. The phone's own equalizer/processing and speaker response remain external variables.

The PC receiver accepts only a compatible periodic localization code. A file that this player can play may still fail receiver import or code matching. For a custom beacon, import the same compatible reference on the PC.

## Source map

| File | Purpose |
|---|---|
| MainActivity.java | Built-in beacon buttons, file picker, play/pause and status |
| LoopService.java | PCM looping, foreground notification and audio focus |
| AudioLoader.java | Media decoding and size/duration/channel checks |
| PcmGain.java | Optional bounded constant gain |
| app/src/main/assets/default-beacon.wav | Unmodified 19–21 kHz lossless reference; first-launch default |
| app/src/main/assets/gap-beacon.wav | Unmodified 18–22 kHz gap-test WAV |
| tests/PcmGainTest.java | Nine host checks for gain behavior |
| Build.ps1 | Local Windows SDK/JDK build and development signing |

## Build

Copy toolchain.example.json to toolchain.json and set Java, Android platform JAR/build-tools, Python and keystore paths. Use an ASCII source directory; source_alias may be null unless you intentionally set a matching junction. Run Build.cmd. The existing development build used JDK 22 and Android platform/build-tools 35. No Gradle daemon or network runtime dependency is required by the app. SDKs are separate tools; sdk-downloads.json records the original official packages.

Keep the signing key outside Git. A build signed with another key cannot update an installed APK bearing the original key; use your own consistent team signing process. The provided APK is for direct team testing, not a Play Store release.

## Validation and permissions

APK packaging, signature verification, ZIP alignment and nine PcmGain host checks passed. See validation.json for hashes and the handoff check date. Real Android installation, file picker, media focus and background playback still require a phone test.

Declared permissions: foreground service, media-playback foreground service and notifications. No network, microphone recording or broad storage permission is declared. Audio selection uses the Android document picker and a private cached copy.
