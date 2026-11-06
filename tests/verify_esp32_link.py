"""Host checks for the Pico-ESP32 FEAT/DOA text and the 300-2000 Hz phase estimator."""
import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'esp32-link'))
sys.path.insert(0, str(ROOT / 'SEN0325-Pico-Setup'))
from direction_estimator import PhaseEstimator
from protocol import feat_to_estimator_inputs, format_feat, parse_doa, parse_feat

OUTER = ('D0L', 'D0R', 'D1L', 'D1R', 'D2L', 'D2R')


def wrap(angle):
    return (angle + math.pi) % (2 * math.pi) - math.pi


def plane_wave_feat(seq, freq, direction_deg, dropped=0):
    k = 2 * math.pi * freq / 343.0
    radius = 0.04
    channels = []
    for index in range(6):
        bearing = index * 60.0
        phase = wrap(-k * radius * math.cos(math.radians(direction_deg - bearing)))
        channels.append((phase, 0.95, 1))
    line = format_feat(seq, freq, dropped, 0, 4096, channels, 1)
    return line, parse_feat(line)


def estimate_python(feat, now=10.0):
    estimator = PhaseEstimator(ROOT / 'SEN0325-Pico-Setup' / 'array_geometry.json')
    estimator.smoothed = None
    estimator.previous_dropped = None
    phases, tones, freq, health = feat_to_estimator_inputs(feat)
    return estimator.estimate(phases, tones, freq, health, now)


def angle_error(a, b):
    return abs((a - b + 180) % 360 - 180)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT / 'stages/09-esp32-link/verification/build-checks.json')
    args = parser.parse_args()
    checks = []

    feat_line, feat = plane_wave_feat(3, 1000, 90)
    checks.append({'name': 'parse_roundtrip', 'passed': feat is not None and feat['seq'] == 3 and feat['freq'] == 1000})

    doa = parse_doa('DOA,v1,3,12,1,estimated,90.2,0.71')
    checks.append({'name': 'parse_valid_doa', 'passed': bool(doa and doa['valid'] and abs(doa['angle_deg'] - 90.2) < 1e-6)})
    rejected = parse_doa('DOA,v1,4,10,0,no_reference_tone,0.0,0.00')
    checks.append({'name': 'invalid_doa_not_zero_bearing', 'passed': bool(rejected and not rejected['valid'] and rejected['reason'] == 'no_reference_tone')})

    high = parse_feat(format_feat(1, 20000, 0, 0, 4096, [(0, 0.95, 1)] * 6, 1))
    high_est = estimate_python(high)
    checks.append({'name': 'reject_20khz_phase_path', 'passed': (not high_est['valid']) and high_est['reason'] == 'frequency_outside_doa_range'})

    empty = parse_feat(format_feat(2, 1000, 0, 0, 0, [(0, 0, 0)] * 6, 0))
    empty_est = estimate_python(empty)
    checks.append({'name': 'reject_empty_capture', 'passed': (not empty_est['valid']) and empty_est['reason'] == 'capture_gap'})

    for direction in (0, 45, 90, 180, 270):
        _, feat = plane_wave_feat(10 + direction, 1000, direction)
        est = estimate_python(feat, now=20 + direction)
        ok = est.get('valid') and angle_error(est['raw_angle_deg'], direction) < 3
        checks.append({'name': f'python_phase_{direction}', 'passed': bool(ok),
                       'raw_angle_deg': est.get('raw_angle_deg'), 'reason': est.get('reason')})

    report = {
        'passed': all(item['passed'] for item in checks),
        'checked_at_utc': datetime.now(timezone.utc).isoformat(),
        'note': 'Host protocol and 1000 Hz phase-model checks. No Pico/ESP32 hardware, no motor output, not RX4.',
        'feat_example': feat_line,
        'checks': checks,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'passed': report['passed'], 'checks': len(checks), 'report': str(args.output)}))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
