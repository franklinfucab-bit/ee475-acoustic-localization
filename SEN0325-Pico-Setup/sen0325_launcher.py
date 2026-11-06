"""EE475 SEN0325 diagnostic launcher. USB serial control; RAM-only loading."""
from __future__ import annotations

import argparse
import ctypes
import json
import math
import os
from pathlib import Path
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
from collections import deque
from datetime import datetime

import serial
from serial.tools import list_ports
from direction_estimator import PhaseEstimator
from runtime_tuning import INTER_CAPTURE_WAIT_SECONDS

ROOT = Path(__file__).resolve().parent
DESKTOP_CHECKPOINT = 'RX4'
PICOTOOL = Path(os.environ.get("EE475_PICOTOOL", r"C:\Tools\Embedded\picotool\picotool\picotool.exe"))
CHANNELS = ("D0L", "D0R", "D1L", "D1R", "D2L", "D2R", "D3R_CENTER")
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def pico_ports():
    return [p for p in list_ports.comports() if p.vid == 0x2E8A and p.pid == 0x000A]


def bootsel_drives():
    if os.name != "nt":
        return []
    drives = []
    mask = ctypes.windll.kernel32.GetLogicalDrives()
    for i in range(26):
        if mask & (1 << i):
            drive = f"{chr(65 + i)}:\\"
            label = ctypes.create_unicode_buffer(261)
            ok = ctypes.windll.kernel32.GetVolumeInformationW(
                drive, label, len(label), None, None, None, None, 0)
            if ok and label.value == "RPI-RP2":
                drives.append(drive)
    return drives


def load_ram(serial_number=None):
    image = ROOT / "firmware" / "sen0325_setup-RAM.uf2"
    validation = subprocess.run(
        [sys.executable, str(ROOT / "verify_ram.py"), str(image)],
        capture_output=True, text=True, timeout=15, creationflags=NO_WINDOW)
    if validation.returncode:
        raise RuntimeError("RAM firmware validation failed: " + validation.stdout + validation.stderr)
    drives = bootsel_drives()
    if len(drives) > 1:
        raise RuntimeError("Multiple RPI-RP2 devices detected. Connect one Pico.")
    if drives:
        return copy_ram_image(image, drives[0])
    if not PICOTOOL.is_file():
        raise RuntimeError("RPI-RP2 drive was not found, and picotool is not installed. Reconnect USB while holding BOOTSEL.")
    args = [str(PICOTOOL), "load", "-v", "-x", str(image)]
    if serial_number:
        # Application firmware uses a placeholder serial; BOOTSEL has the chip's
        # serial. Do not carry the application serial across that USB transition.
        args += ["-f"]
    loaded = subprocess.run(args, capture_output=True, text=True,
                            timeout=35, creationflags=NO_WINDOW)
    if loaded.returncode:
        raise RuntimeError("RAM loading failed. Reconnect while holding BOOTSEL.\n" + loaded.stdout + loaded.stderr)
    return loaded.stdout.strip()


def copy_ram_image(image, drive):
    """Load RAM firmware through the RPI-RP2 drive. No picotool or RP2 Boot driver."""
    try:
        shutil.copyfile(image, Path(drive) / image.name)
    except OSError:
        # The Pico reboots and removes the drive once it accepts the UF2.
        pass
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline:
        if pico_ports():
            return f"RAM image copied to {drive}"
        time.sleep(0.25)
    if bootsel_drives():
        raise RuntimeError("RPI-RP2 is connected, but copying the RAM firmware did not start the Pico.")
    return f"RAM image copied to {drive}"


class Session:
    """Own the serial port in one worker; GUI communicates only through queues/events."""

    def __init__(self):
        self.desktop_checkpoint=DESKTOP_CHECKPOINT
        self.events = queue.Queue()
        self.stop = threading.Event()
        self.reconnect = threading.Event()
        self.want_running = threading.Event()
        self.want_running.set()
        self.thread = None
        self.frames = 0
        self.seen = set()
        self.last_channels = {}
        self.last_frame = {}
        self.last_load = 0.0
        self.frequency = 1000
        self.tone_frequency = 1000
        self.mode = 'tone'
        self.raw_bursts = 0
        self.inter_capture_wait = INTER_CAPTURE_WAIT_SECONDS
        self.capture_generation = 0
        self.beacon_estimator = None
        self.last_raw_audio = None
        self.last_packet_timing = {}
        self.commands = queue.Queue()
        self.notes = queue.Queue()
        self.last_tones = {}
        self.phase_rows = {}
        self.last_completed_phases = {}
        self.last_phase_frequency = None
        self.frame_tones = {}
        self.last_direction = {"valid":False}
        self.recent_directions=deque(maxlen=24)
        self.recent_audio=deque(maxlen=64)
        self.recent_audio_lock=threading.Lock()
        self.direction_estimator = PhaseEstimator(ROOT/"array_geometry.json")
        (ROOT / "logs").mkdir(exist_ok=True)
        self.log_path = ROOT / "logs" / (datetime.now().strftime("launcher-%Y%m%d-%H%M%S-%f") + ".txt")
        from direction_diagnostics import DirectionDiagnostics
        self.diagnostics=DirectionDiagnostics(ROOT/'logs',self.log_path.stem,ROOT/'array_geometry.json',self.mark_event,checkpoint=DESKTOP_CHECKPOINT)

    def start(self):
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def emit(self, kind, value):
        self.events.put((kind, value))

    def set_frequency(self, frequency):
        frequency = int(frequency)
        if not 300 <= frequency <= 22000:
            raise ValueError("Frequency must be within 300-22000 Hz.")
        self.frequency = frequency
        self.capture_generation+=1
        self.tone_frequency = frequency
        self.mode = 'tone'
        self.last_direction={"valid":False,"reason":"frequency_changing"}
        self.emit("direction",dict(self.last_direction))
        self.commands.put(frequency)

    def set_mode(self,mode):
        from beacon_dsp import PROFILES
        if mode!='tone' and mode not in PROFILES:
            raise ValueError('Unknown localization mode')
        self.mode=mode
        with self.recent_audio_lock:self.recent_directions.clear()
        self.capture_generation+=1
        self.frequency=self.tone_frequency if mode=='tone' else PROFILES[mode]['center']
        self.last_direction={'valid':False,'reason':'mode_changing'}
        self.emit('direction',dict(self.last_direction))
        self.mark_event('mode_change',mode=mode)

    def set_running(self,running):
        self.capture_generation+=1
        with self.recent_audio_lock:self.recent_directions.clear()
        if running:
            self.want_running.set()
        else:
            self.want_running.clear()
        self.last_direction={'valid':False,'reason':'acquisition_starting' if running else 'radar_stopped'}
        self.emit('direction',dict(self.last_direction))
        self.mark_event('radar_control',running=bool(running))

    def mark_event(self, event, **details):
        self.notes.put({"event": event, "monotonic": time.monotonic(),
                        "wall_time": datetime.now().astimezone().isoformat(), **details})

    def set_front(self):
        direction=self.last_direction
        if (not self.want_running.is_set() or not direction.get("valid")
                or direction.get("frequency")!=self.frequency
                or time.monotonic()-direction.get("received_at",0)>1.5):
            raise ValueError("Play the selected beacon and wait for a valid bearing before setting front.")
        with self.recent_audio_lock:
            rows=[r for r in self.recent_directions if r.get('profile')==self.mode and time.monotonic()-r['received_at']<2.5]
        if len(rows)<3:raise ValueError('Keep the phone fixed in front until at least three valid bearings are available, then select Set Front.')
        vector=sum(complex(math.cos(math.radians(r['raw_angle_deg'])),math.sin(math.radians(r['raw_angle_deg']))) for r in rows)
        mean=math.degrees(math.atan2(vector.imag,vector.real))%360
        spread=max(abs((r['raw_angle_deg']-mean+180)%360-180) for r in rows)
        if spread>15:raise ValueError('The recent bearings are unstable. Keep the phone fixed in front and wait before setting front.')
        self.direction_estimator.set_front(mean)
        if self.beacon_estimator is not None:
            self.beacon_estimator.smoothed=None
        self.mark_event("set_front",raw_angle=mean,calibration_windows=len(rows),spread_deg=round(spread,2))

    def set_mirror(self,value):
        with self.recent_audio_lock:self.recent_directions.clear()
        self.direction_estimator.set_mirror(value)
        if self.beacon_estimator is not None:
            self.beacon_estimator.smoothed=None
        self.mark_event("mirror_view",enabled=value)

    def send(self, link, log, command):
        log.write(f'# TX mono={time.monotonic():.6f} {command}\n')
        link.write((command + "\n").encode("ascii"))

    def run(self):
        try:
            self._run()
        finally:
            self.diagnostics.close()

    def _run(self):
        with self.log_path.open("w", encoding="utf-8", buffering=1) as log:
            log.write(f"EE475 SEN0325 diagnostic {datetime.now().isoformat()}\nROOT={ROOT}\n")
            log.write(f'DESKTOP checkpoint={DESKTOP_CHECKPOINT}; direction_fit=joint_spectral_rescue\n')
            while not self.stop.is_set():
                self.reconnect.clear()
                try:
                    ports = pico_ports()
                    drives = bootsel_drives()
                    if len(ports) + len(drives) > 1:
                        raise RuntimeError("Multiple Picos detected. Connect only the board being tested.")
                    if not ports:
                        if len(drives) > 1:
                            raise RuntimeError("Multiple RPI-RP2 devices detected. Connect one Pico.")
                        if drives:
                            self.reload(log)
                            self.stop.wait(1.5)
                            continue
                        self.emit("status", "Waiting for Pico: hold BOOTSEL while connecting USB; release when RPI-RP2 appears.")
                        self.stop.wait(2)
                        continue
                    port = ports[0]
                    self.emit("status", f"Connecting to {port.device}...")
                    identified = False
                    legacy_firmware = False
                    # Closing this context on every path releases the port for picotool.
                    with serial.Serial(port.device, 115200, timeout=0.15, write_timeout=1) as link:
                        # Let DTR/USB settle. A leading newline also clears a
                        # partial command left by a previous serial monitor.
                        self.stop.wait(0.35)
                        link.write(b"\nHELP\n")
                        deadline = time.monotonic() + 4
                        next_help = time.monotonic() + 0.8
                        while time.monotonic() < deadline and not self.stop.is_set():
                            line = link.readline().decode("utf-8", errors="replace").strip()
                            if line:
                                log.write(line + "\n")
                            if line.startswith("SEN0325_SETUP v0.5;"):
                                legacy_firmware = True
                                log.write('RX2_UPGRADE: replacing legacy v0.5 with validated RAM firmware\n')
                                break
                            if line.startswith("SEN0325_SETUP v0.6;") or line.startswith("SEN0325_SETUP v0.7"):
                                identified = True
                                break
                            if time.monotonic() > next_help:
                                link.write(b"\nHELP\n")
                                next_help = time.monotonic() + 0.8
                        if identified:
                            self.stream(link, log, port.device)
                    if not identified and not self.stop.is_set():
                        if not port.serial_number and not legacy_firmware:
                            raise RuntimeError("Diagnostic firmware is not running. Reconnect USB while holding BOOTSEL.")
                        self.reload(log, port.serial_number or 'legacy-v0.5')
                        self.stop.wait(1.5)
                except Exception as exc:
                    message = str(exc)
                    if isinstance(exc, serial.SerialException):
                        message = "Serial port unavailable. Close Arduino/VS Code serial monitors, then select Reconnect Pico.\n" + message
                    log.write("ERROR: " + message + "\n")
                    self.emit("status", message)
                    self.stop.wait(3)
            self.emit("closed", None)

    def reload(self, log, serial_number=None):
        drives = bootsel_drives()
        if time.monotonic() - self.last_load < (4 if drives else 15):
            if drives:
                return
            raise RuntimeError("Retry pending. If still disconnected, reconnect USB while holding BOOTSEL.")
        self.last_load = time.monotonic()
        self.emit("status", "RPI-RP2 found. Copying RAM firmware..." if drives else "Validating and loading RAM diagnostic firmware...")
        result = load_ram(serial_number)
        log.write("RAM_LOAD: " + result + "\n")
        self.emit("loaded", result)

    def stream(self, link, log, port):
        active = None
        active_mode = None
        # Stop an earlier session first so the counters and warm-up have a fresh start.
        self.send(link, log, "STOP")
        self.send(link, log, "LEDOFF")
        self.send(link, log, f"FREQ {self.frequency}")
        last_report = time.monotonic()
        warned = False
        packet_failures = 0
        try:
            while not self.stop.is_set() and not self.reconnect.is_set():
                while not self.notes.empty():
                    log.write("# EVENT " + json.dumps(self.notes.get_nowait(), ensure_ascii=False) + "\n")
                while not self.commands.empty():
                    frequency = self.commands.get_nowait()
                    if self.mode!='tone':
                        continue
                    self.send(link, log, "STOP")
                    self.send(link, log, f"FREQ {frequency}")
                    active = None
                target = self.want_running.is_set()
                if active_mode!=self.mode:
                    self.send(link,log,'STOP')
                    active=None
                    active_mode=self.mode
                    self.beacon_estimator=None
                    if active_mode=='tone':
                        self.send(link,log,f'FREQ {self.frequency}')
                if target != active:
                    self.send(link, log, "START" if target and active_mode=='tone' else "STOP")
                    active = target
                    last_report = time.monotonic()
                    warned = False
                    self.emit("status", f"{port} · {'Capturing at 48 kHz' if active else 'Paused; microphone clocks stopped'}")
                if active and active_mode!='tone':
                    from raw_packet import PacketError,stop_and_resynchronize
                    try:
                        self.record_beacon(link,log,active_mode)
                        packet_failures=0
                    except PacketError as error:
                        self.beacon_estimator=None
                        self.last_direction={'valid':False,'reason':'capture_gap','profile':active_mode}
                        self.emit('direction',dict(self.last_direction))
                        if self.stop.is_set() or self.reconnect.is_set():break
                        if error.category!='capture_cancelled':packet_failures+=1
                        self.emit('status',f'{port} · Resynchronizing raw packet ({error.category})...')
                        recovery=stop_and_resynchronize(link,lambda:self.send(link,log,'STOP'),
                            cancelled=lambda:self.stop.is_set() or self.reconnect.is_set())
                        log.write('# RECOVERY '+json.dumps(dict(recovery,error=error.category,
                            failed_seq=error.details.get('seq'),wall_time=datetime.now().astimezone().isoformat()))+'\n')
                        if self.stop.is_set() or self.reconnect.is_set():break
                        if not recovery['recovered'] or packet_failures>=3:
                            raise RuntimeError('Raw packet recovery failed repeatedly; reconnecting.')
                        self.emit('status',f'{port} · Packet synchronized; resuming capture')
                    self.stop.wait(self.inter_capture_wait)
                    continue
                line = link.readline().decode("utf-8", errors="replace").strip()
                if line:
                    if line.startswith("FRAME "):
                        log.write(f'# RX_FRAME mono={time.monotonic():.6f} wall={datetime.now().astimezone().isoformat()}\n')
                    log.write(line + "\n")
                    self.parse(line)
                    if line.startswith("FRAME "):
                        last_report = time.monotonic()
                        if warned:
                            self.emit("status", f"{port} · Capturing at 48 kHz")
                        warned = False
                if active and not warned and time.monotonic() - last_report > 4:
                    self.emit("status", f"{port} · Connected but no capture reports. Check firmware or reconnect.")
                    warned = True
        finally:
            try:
                link.write(b"STOP\n")
                link.flush()
            except serial.SerialException:
                pass

    def record_beacon(self,link,log,mode):
        from beacon_dsp import BeaconEstimator,SIZE,CHANNELS
        import numpy as np
        cycle_started=time.perf_counter()
        generation=self.capture_generation
        if (self.beacon_estimator is None or self.beacon_estimator.profile!=mode
                or getattr(self,'beacon_generation',None)!=generation):
            self.beacon_estimator=BeaconEstimator(ROOT/'array_geometry.json',mode)
            self.beacon_generation=generation
        from raw_packet import receive_packet, PacketError
        try:
            packet=receive_packet(link,lambda:self.send(link,log,'RECORD'),
                                  lambda line:log.write(line+'\n'),cancelled=lambda:
                                  self.stop.is_set() or self.reconnect.is_set() or
                                  generation!=self.capture_generation or not self.want_running.is_set())
        except PacketError as error:
            log.write(('# PACKET_CANCEL ' if error.category=='capture_cancelled' else '# PACKET_ERROR ')+json.dumps(dict(error.details,
                wall_time=datetime.now().astimezone().isoformat()),ensure_ascii=False)+'\n')
            log.flush()
            raise
        header,data=packet.header,packet.data
        self.last_packet_timing=dict(packet.timing)
        log.write('# PACKET '+json.dumps(dict(packet.timing,
            wall_time=datetime.now().astimezone().isoformat()),ensure_ascii=False)+'\n')
        samples=np.frombuffer(data,dtype='<i2').reshape(SIZE,7).copy()
        if generation!=self.capture_generation or not self.want_running.is_set() or mode!=self.mode:
            return
        self.last_raw_audio=samples
        health={key:int(header[key]) for key in ('frames','fs','seq','dropped','rx_stall','process_us')}
        self.raw_bursts+=1;self.frames+=1
        self.last_frame=health
        self.emit('frame',dict(health))
        dsp_started=time.perf_counter()
        estimate,tones=self.beacon_estimator.estimate(samples,health,time.monotonic())
        dsp_done=time.perf_counter()
        estimate['pipeline_timing']=dict(packet.timing,dsp_ms=round((dsp_done-dsp_started)*1000,3))
        if 'probe_bands_dbfs' not in estimate:
            from highband_dsp import probe_levels
            estimate['probe_bands_dbfs']=probe_levels(samples)
        estimate['capture_cycle_ms']=round((time.perf_counter()-cycle_started)*1000,2)
        # Ignore a result from a burst that began before the user switched modes.
        if mode!=self.mode or generation!=self.capture_generation or not self.want_running.is_set():
            return
        from signal_scope import signal_payload
        self.emit('signal',dict(signal_payload(samples,health['seq'],estimate['received_at']),profile=mode))
        for ch,name in enumerate(CHANNELS):
            raw=samples[:,ch].astype(np.float64)
            rms=float(np.std(raw))
            row={'rms16':rms,'dbfs':20*math.log10(max(rms,1e-6)/32768),
                 'min':int(raw.min()),'max':int(raw.max()),'zero_pct':float(np.mean(raw==0)*100),
                 'clips':int(np.sum(np.abs(raw)>=32760))}
            self.seen.add(name);self.last_channels[name]=row;self.emit('channel',(name,row))
            if name in tones:
                tones[name]=dict(tones[name],profile=mode)
                self.last_tones[name]=tones[name]
                self.emit('tone',(name,tones[name]))
        estimate['pipeline_timing']['postprocess_ms']=round((time.perf_counter()-dsp_done)*1000,3)
        estimate['direction_queued_at']=time.monotonic()
        estimate['direction_queued_perf']=time.perf_counter()
        estimate['request_to_queue_ms']=round((estimate['direction_queued_perf']-packet.timing['request_perf_counter'])*1000,3)
        self.last_direction=estimate
        with self.recent_audio_lock:
            if estimate.get('valid'):self.recent_directions.append(dict(estimate))
            self.recent_audio.append({'time':estimate['received_at'],'profile':mode,'seq':health['seq'],'audio':samples.copy()})
        self.emit('direction',dict(estimate))
        self.mark_event('beacon_estimate',**estimate,raw_crc32=header['crc32'])
        self.diagnostics.observe(samples,health,estimate,generation)

    def parse(self, line):
        if line.startswith("PHASE_END "):
            fields={key:int(value) for key,value in re.findall(r"(\w+)=(\d+)",line)}
            if fields.get("seq")!=self.last_frame.get("seq") or fields.get("freq")!=self.frequency:
                return
            self.last_completed_phases=dict(self.phase_rows)
            self.last_phase_frequency=fields["freq"]
            self.last_direction=self.direction_estimator.estimate(
                self.phase_rows,self.frame_tones,self.frequency,self.last_frame,time.monotonic())
            self.emit("direction",dict(self.last_direction))
            self.mark_event("bearing_estimate",**self.last_direction)
        elif line.startswith("PHASE,"):
            parts=line.split(",")
            try:
                if len(parts)!=6 or parts[1] not in CHANNELS[:6]:
                    return
                frequency,sequence=int(parts[2]),int(parts[3])
                phase,coherence=float(parts[4]),float(parts[5])
                if frequency!=self.frequency or sequence!=self.last_frame.get("seq"):
                    return
                if not math.isfinite(phase) or not -math.pi-.001<=phase<=math.pi+.001 or not 0<=coherence<=1:
                    return
                self.phase_rows[parts[1]]={"phase_rad":phase,"coherence":coherence}
            except ValueError:
                return
        elif line.startswith("TONE,"):
            parts = line.split(",")
            try:
                if len(parts) != 7 or parts[1] not in CHANNELS:
                    return
                frequency, rms, ratio, snr, present = int(parts[2]), float(parts[3]), float(parts[4]), float(parts[5]), int(parts[6])
                if not 300 <= frequency <= 22000 or not math.isfinite(rms) or not math.isfinite(snr) or rms < 0 or not 0 <= ratio <= 1 or present not in (0, 1):
                    return
                data = {"frequency": frequency, "rms": rms, "ratio": ratio, "snr_db":snr, "present": bool(present)}
                self.last_tones[parts[1]] = data
                self.frame_tones[parts[1]] = data
                self.emit("tone", (parts[1], data))
            except ValueError:
                return
        elif line.startswith("DOA "):
            try:
                fields = dict(token.split("=", 1) for token in line.split()[1:])
                valid = int(fields["valid"])
                if valid not in (0, 1):
                    return
                if not valid:
                    self.emit("direction", {"valid": False})
                    return
                angle, confidence = float(fields["angle_deg"]), float(fields["confidence"])
                if not math.isfinite(angle) or not math.isfinite(confidence) or not 0 <= confidence <= 1:
                    return
                self.emit("direction", {"valid": True, "angle_deg": angle % 360, "confidence": confidence})
            except (ValueError, KeyError):
                return
        elif line.startswith("FRAME "):
            self.phase_rows={}
            self.frame_tones={}
            self.last_frame = {key: int(value) for key, value in re.findall(r"(\w+)=(\d+)", line)}
            self.frames += 1
            self.emit("frame", dict(self.last_frame))
        elif line.startswith("CH,"):
            parts = line.split(",")
            if len(parts) == 8 and parts[1] in CHANNELS:
                try:
                    row = {"rms16": float(parts[2]), "dbfs": float(parts[3]),
                           "min": int(parts[4]), "max": int(parts[5]),
                           "zero_pct": float(parts[6]), "clips": int(parts[7])}
                    if not all(math.isfinite(row[k]) for k in ("rms16", "dbfs", "zero_pct")):
                        return
                except ValueError:
                    return
                self.seen.add(parts[1])
                self.last_channels[parts[1]] = row
                self.emit("channel", (parts[1], row))


def smoke_test(seconds, force_load):
    if force_load:
        ports = pico_ports()
        drives = bootsel_drives()
        if len(ports) == 1 and not drives and ports[0].serial_number:
            print(load_ram(ports[0].serial_number))
        elif not ports and len(drives) == 1:
            print(load_ram())
        else:
            raise SystemExit("Expected exactly one Pico for RAM loading")
        time.sleep(2)
    session = Session()
    session.start()
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        try:
            kind, value = session.events.get(timeout=0.3)
            if kind in ("status", "loaded"):
                print(kind, value, flush=True)
        except queue.Empty:
            pass
    session.stop.set()
    session.thread.join(timeout=40)
    result = {"root": str(ROOT), "frames": session.frames,
              "channels": session.last_channels, "last_frame": session.last_frame,
              "target_frequency": session.frequency, "tones": session.last_tones,
              "direction":session.last_direction,
              "log": str(session.log_path), "worker_stopped": not session.thread.is_alive(),
              "passed": len(session.seen) == 7 and session.frames >= 3 and not session.thread.is_alive()}
    output = ROOT / "logs" / "launcher-smoke-test.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


def gui(auto_close=None,initial_profile='coded-audible'):
    from sen0325_simple_view import run
    return run(Session, ROOT, CHANNELS, auto_close,initial_profile=initial_profile)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke-test", type=float, metavar="SECONDS")
    parser.add_argument("--reload-ram", action="store_true")
    parser.add_argument("--ui-smoke-test", type=float, metavar="SECONDS")
    parser.add_argument('--profile',choices=('coded-audible','coded-16-18','coded-20'),default='coded-20')
    args = parser.parse_args()
    try:
        raise SystemExit(smoke_test(args.smoke_test, args.reload_ram) if args.smoke_test else gui(args.ui_smoke_test,args.profile))
    except Exception:
        import traceback
        (ROOT / "logs").mkdir(exist_ok=True)
        (ROOT / "logs" / "launcher-error.txt").write_text(traceback.format_exc(), encoding="utf-8")
        if os.name == "nt" and not args.smoke_test:
            ctypes.windll.user32.MessageBoxW(None, "Startup failed. See logs/launcher-error.txt.", "EE475", 0)
        raise
