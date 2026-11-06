# EE475 agent instructions

Read README.md and docs/ROLES.md before changes. Active desktop sources remain in SEN0325-Pico-Setup. Current checkpoint: stages/06-joint-delay; historical stages/reports are under legacy. Android work lives in android-player.

- Work in stages; explain intended behavior changes first. Save before/after evidence and update the phase notes, change details and relevant README.
- Do not reject, freeze or force a bearing solely because its change from the previous frame is large. Genuine motion may be unpredictable.
- Keep the computer receive-only. Playback belongs on the phone. Do not silently change frequency, sample rate, code or defaults on only one side.
- Distinguish processing rate, packet latency, accepted-bearing rate and physical accuracy. Radar rings do not measure range. User pauses and unrecorded movements are not automatically bugs.
- Preserve engineering tools, GPIO wiring and firmware unless the requested change requires them. No motor commands are part of this contribution.
- Treat legacy as reference history. Current tests may read its fixed fixtures; write new results to the current stage. For requested reorganization, preserve content hashes and a path map.
- Local microphone recordings remain local. Record exact packet sequences and finite capture durations. Do not fabricate phone pause times or true angles.
- Prefer conservative, optional audio processing; preserve original files. Phone gain normalization is not microphone ADC calibration or a guarantee of range.

Handoff update (2026-11-02): read docs/TEAM_HANDOFF.md, docs/AI_HANDOFF.md and docs/INTEGRATION.md. Stage 07 tracks packaging/portability; RX4 DSP is still stage 06. Stage 09 on branch Pico-ESP32 adds UART0 FEAT/DOA for a 300–2000 Hz ESP32 phase fit; it does not replace RX4 or command motors. tools/verify_handoff.py runs checks available in a fresh clone. Private recording fixtures are deliberately excluded, not fabricated. See docs/SHARING.md.
