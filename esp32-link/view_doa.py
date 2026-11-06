"""Display-only viewer for ESP32 DOA lines. Does not estimate bearing or send RECORD."""
import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from protocol import parse_doa

try:
    import serial
except ImportError as exc:
    raise SystemExit('pyserial is required: pip install pyserial') from exc


def main():
    parser = argparse.ArgumentParser(description='Read DOA lines from the ESP32 USB serial port.')
    parser.add_argument('port', help='ESP32 COM port, for example COM5')
    parser.add_argument('--baud', type=int, default=115200)
    args = parser.parse_args()
    with serial.Serial(args.port, args.baud, timeout=0.2) as link:
        print(f'Display-only. Listening on {args.port}. Invalid/stale results are not shown as 0°.')
        last_print = 0
        while True:
            raw = link.readline().decode('utf-8', errors='replace')
            if not raw:
                continue
            line = raw.strip()
            if not line:
                continue
            doa = parse_doa(line)
            now = time.monotonic()
            if doa is None:
                if now - last_print > 1:
                    print(line)
                    last_print = now
                continue
            if doa['valid']:
                print(f"bearing {doa['angle_deg']:.1f}°  quality {doa['quality']:.2f}  seq {doa['seq']}")
            else:
                print(f"no bearing  reason={doa['reason']}  seq {doa['seq']}")
            last_print = now


if __name__ == '__main__':
    main()
