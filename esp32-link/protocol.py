"""FEAT/DOA text lines for the Pico UART0 <-> ESP32 UART2 link."""
OUTER = ('D0L', 'D0R', 'D1L', 'D1R', 'D2L', 'D2R')
CENTER = 'D3R_CENTER'


def format_feat(seq, freq, dropped, rx_stall, frames, channels, center_present):
    parts = ['FEAT', 'v1', str(int(seq)), str(int(freq)), str(int(dropped)),
             str(int(rx_stall)), str(int(frames))]
    if len(channels) != 6:
        raise ValueError('need six outer channels')
    for phase, coherence, present in channels:
        parts.extend((f'{float(phase):.6f}', f'{float(coherence):.4f}', str(int(bool(present)))))
    parts.append(str(int(bool(center_present))))
    return ','.join(parts)


def parse_feat(line):
    parts = line.strip().split(',')
    if len(parts) != 26 or parts[0] != 'FEAT' or parts[1] != 'v1':
        return None
    try:
        seq, freq, dropped, rx_stall, frames = (int(parts[2]), int(parts[3]), int(parts[4]),
                                                int(parts[5]), int(parts[6]))
        channels = []
        for i in range(6):
            base = 7 + i * 3
            channels.append((float(parts[base]), float(parts[base + 1]), int(parts[base + 2])))
        center_present = int(parts[25])
    except ValueError:
        return None
    if rx_stall not in (0, 1) or center_present not in (0, 1):
        return None
    if not all(on in (0, 1) and 0 <= coh <= 1 for _, coh, on in channels):
        return None
    return {'seq': seq, 'freq': freq, 'dropped': dropped, 'rx_stall': rx_stall,
            'frames': frames, 'channels': channels, 'center_present': center_present}


def parse_doa(line):
    parts = line.strip().split(',')
    if len(parts) != 8 or parts[0] != 'DOA' or parts[1] != 'v1':
        return None
    try:
        seq, age_ms, valid = int(parts[2]), int(parts[3]), int(parts[4])
        reason, angle, quality = parts[5], float(parts[6]), float(parts[7])
    except ValueError:
        return None
    if valid not in (0, 1) or not 0 <= quality <= 1:
        return None
    return {'seq': seq, 'age_ms': age_ms, 'valid': bool(valid), 'reason': reason,
            'angle_deg': angle, 'quality': quality}


def feat_to_estimator_inputs(feat):
    phases, tones = {}, {}
    for name, (phase, coherence, present) in zip(OUTER, feat['channels']):
        phases[name] = {'phase_rad': phase, 'coherence': coherence}
        tones[name] = {'present': bool(present), 'frequency': feat['freq']}
    tones[CENTER] = {'present': bool(feat['center_present']), 'frequency': feat['freq']}
    health = {'dropped': feat['dropped'], 'rx_stall': feat['rx_stall'], 'frames': feat['frames']}
    return phases, tones, feat['freq'], health
