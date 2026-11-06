"""Bounded, local raw evidence for intermittent high-band direction output.

The capture worker only copies small blocks and queues completed snapshots.
File I/O runs on a separate thread; no playback, hardware commands or gain.
"""
from collections import Counter, deque
from datetime import datetime
import hashlib
import json
from pathlib import Path
import queue
import threading

import numpy as np


class DirectionDiagnostics:
    PRE_BLOCKS = 8
    POST_BLOCKS = 12
    FAILURE_TRIGGER = 6
    VALID_TRIGGER = 4
    COOLDOWN_S = 15.
    MAX_PER_KIND = 2

    def __init__(self, folder, session_name, geometry_path, event=None, checkpoint='RX3'):
        self.folder = Path(folder) / 'direction-diagnostics'
        self.session_name = session_name
        self.geometry_path = Path(geometry_path)
        self.event = event or (lambda *args, **kwargs: None)
        self.checkpoint = checkpoint
        self.ring = deque(maxlen=self.PRE_BLOCKS)
        self.pending = None
        self.context = None
        self.last_time = None
        self.last_trigger = float('-inf')
        self.streak = self.valid_streak = 0
        self.saved = Counter()
        self.jobs = queue.Queue(maxsize=2)
        self.worker = None
        self.closed = False

    def observe(self, audio, health, estimate, generation=0, wall_time=None):
        """Called only by the serial worker. Diagnostic errors cannot stop scan."""
        try:
            self._observe(audio, health, estimate, generation, wall_time)
        except Exception as error:
            self.event('direction_diagnostic_error', error=str(error))
            self.pending = None
            self.ring.clear()

    def _observe(self, audio, health, estimate, generation, wall_time):
        if self.closed:
            return
        profile = estimate.get('profile', '')
        now = float(estimate['received_at'])
        context = (profile, generation)
        if context != self.context or (self.last_time is not None and now-self.last_time >= .75):
            self._finish('capture_context_changed')
            self.ring.clear()
            self.streak = self.valid_streak = 0
        self.context = context
        self.last_time = now
        if profile not in ('coded-16-18', 'coded-20', 'coded-gap') and not profile.startswith('imported-'):
            return
        block = {'audio': np.asarray(audio, dtype='<i2').copy(), 'health': dict(health),
                 'estimate': dict(estimate), 'generation': generation,
                 'wall_time': wall_time or datetime.now().astimezone().isoformat()}
        self.ring.append(block)
        if self.pending is not None:
            self.pending['blocks'].append(block)
            self.pending['post_remaining'] -= 1
            if not self.pending['post_remaining']:
                self._finish('complete')
            return
        failure = (estimate.get('code_channels', 0) >= 4
                   and estimate.get('reason') == 'group_delay_inconsistent')
        self.streak = self.streak+1 if failure else 0
        self.valid_streak = self.valid_streak+1 if estimate.get('valid') else 0
        kind = ('delay_rejection' if self.streak >= self.FAILURE_TRIGGER else
                'valid_reference' if self.valid_streak >= self.VALID_TRIGGER else None)
        if (kind is None or self.saved[kind] >= self.MAX_PER_KIND
                or now-self.last_trigger < self.COOLDOWN_S):
            return
        # Snapshot geometry once at the trigger, never guess or recalibrate it.
        geometry = json.loads(self.geometry_path.read_text(encoding='utf-8-sig'))
        self.pending = {'kind': kind, 'trigger_sequence': int(health['seq']),
                        'trigger_time': now, 'profile': profile, 'geometry': geometry,
                        'blocks': list(self.ring), 'post_remaining': self.POST_BLOCKS}
        self.saved[kind] += 1
        self.last_trigger = now
        self.streak = self.valid_streak = 0
        self.event('direction_diagnostic_trigger', kind=kind, sequence=int(health['seq']),
                   pre_blocks=len(self.ring), post_blocks=self.POST_BLOCKS)

    def _finish(self, completion):
        if self.pending is None:
            return
        job, self.pending = self.pending, None
        job['completion'] = completion
        if self.worker is None:
            self.worker = threading.Thread(target=self._write_jobs, name='direction-evidence', daemon=True)
            self.worker.start()
        try:
            self.jobs.put_nowait(job)
        except queue.Full:
            self.event('direction_diagnostic_skipped', reason='writer_busy')

    def _write_jobs(self):
        while True:
            job = self.jobs.get()
            try:
                if job is None:
                    return
                self._write(job)
            except Exception as error:
                self.event('direction_diagnostic_error', error=str(error))
            finally:
                self.jobs.task_done()

    def _write(self, job):
        self.folder.mkdir(parents=True, exist_ok=True)
        stem = f"{self.session_name}-{job['kind']}-seq{job['trigger_sequence']}"
        raw_path = self.folder / (stem+'.npz')
        meta_path = self.folder / (stem+'.json')
        blocks = job.pop('blocks')
        with raw_path.with_suffix('.npz.tmp').open('wb') as output:
            np.savez(output, audio=np.stack([b['audio'] for b in blocks]),
                     sequence=np.array([b['health']['seq'] for b in blocks], dtype=np.int64),
                     received_at=np.array([b['estimate']['received_at'] for b in blocks]),
                     generation=np.array([b['generation'] for b in blocks], dtype=np.int64))
        raw_path.with_suffix('.npz.tmp').replace(raw_path)
        job.update(schema=1, checkpoint=self.checkpoint, raw_file=raw_path.name,
                   raw_sha256=hashlib.sha256(raw_path.read_bytes()).hexdigest(),
                   block_count=len(blocks), sample_rate_hz=48000,
                   channels=['D0L','D0R','D1L','D1R','D2L','D2R','D3R_CENTER'],
                   events=[{k:v for k,v in b.items() if k != 'audio'} for b in blocks],
                   limitation='Automatic local snapshot; phone playback state, distance and true bearing are unknown. Accepted output is not angular ground truth.')
        meta_path.with_suffix('.json.tmp').write_text(json.dumps(job, indent=2), encoding='utf-8')
        meta_path.with_suffix('.json.tmp').replace(meta_path)
        self.event('direction_diagnostic_saved', raw_file=str(raw_path), metadata_file=str(meta_path),
                   blocks=len(blocks), completion=job['completion'])

    def close(self):
        """Called after the serial loop ends, never on the GUI drawing thread."""
        if self.closed:
            return
        self.closed = True
        self._finish('session_closed')
        if self.worker is not None:
            self.jobs.join()
            self.jobs.put(None)
            self.worker.join(timeout=5)
