"""Build the team ZIP from Git-selected files; keep a separate complete local archive."""
from pathlib import Path
from collections import Counter
import argparse, csv, hashlib, io, json, os, re, subprocess, zipfile

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--local-archive',action='store_true')
args=parser.parse_args()
OUT=ROOT/'delivery';OUT.mkdir(exist_ok=True)

def write(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name(path.name+'.new');temp.write_text(text,encoding='utf-8');os.replace(temp,path)

def tracked():
    return sorted(p for p in subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode('utf-8').split('\0') if p)

PURPOSE={
 'README.md':'Main project overview / entry point',
 'AGENTS.md':'Repository instructions and constraints for coding agents',
 'TEAM_HANDOFF.md':'English teammate handoff and next steps',
 'TEAM_HANDOFF_ZH.md':'Chinese teammate handoff and next steps',
 'AI_HANDOFF.md':'AI continuation map, constraints, evidence and verification',
 'INTEGRATION.md':'System composition, USB/data contracts and unimplemented robot boundary',
 'SETUP_WINDOWS.md':'Environment setup on another Windows computer',
 'SHARING.md':'Published versus local-only content and archive policy',
 'FILE_CATALOG.md':'Every published file with its role and purpose',
 'FILE_CATALOG.csv':'Machine-readable published file catalog',
 'SHA256SUMS.txt':'SHA-256 integrity list for published files except itself',
 'Setup-Windows.ps1':'Create project-local Python environment and validate dependencies',
 'Update-and-Start.cmd':'Select configured Python and invoke graceful local refresh/start',
 '一键启动雷达.cmd':'Chinese shortcut to current receiver launcher',
 'Open-Project.cmd':'Open the engineering workspace in VS Code',
 'main.c':'Pico firmware: synchronous capture, control commands and USB packets',
 'sen0325_i2s.pio':'PIO program for simultaneous digital microphone capture',
 'crc32_fast.h':'Table CRC32 implementation for raw packet protection',
 'tone_filter.h':'Firmware tone-filter helper',
 'CMakeLists.txt':'Pico SDK build definition and USB buffer settings',
 'sen0325_launcher.py':'Desktop Session, Pico discovery/loading, serial worker and application entry',
 'sen0325_simple_view.py':'Main receive-only UI, controls and event handling',
 'sen0325_view.py':'Advanced diagnostic/channel view',
 'app_controls.py':'Scan/profile state and cancellation rules',
 'app_instance.py':'Instance nonce and graceful restart coordination',
 'refresh_and_start.py':'Source check, graceful restart request and new-instance confirmation',
 'runtime_tuning.py':'Host capture scheduling parameters',
 'raw_packet.py':'Bounded USB read, header/length/CRC/trailer validation and resynchronization',
 'beacon_dsp.py':'Reference generation, beacon profiles and receiver object',
 'highband_dsp.py':'High-band code detection, delay/arrival path selection and display smoothing',
 'arrival_dsp.py':'Matched-code arrival fallback estimator',
 'joint_delay_dsp.py':'RX4 full-angle joint spectral-delay rescue',
 'direction_estimator.py':'Lower-frequency phase estimator and view calibration',
 'direction_diagnostics.py':'Finite asynchronous raw snapshots for delay diagnosis',
 'array_geometry.json':'Array channel geometry and display heading/mirror configuration',
 'beacon_importer.py':'Validate/import a compatible periodic MP3/WAV reference',
 'radar_canvas.py':'2D bearing radar drawing',
 'signal_scope.py':'Received waveform/spectrum computation and drawing',
 'tracking_audio.py':'Audio reference/playback utilities retained outside normal receive-only controls',
 'make_regular_tones.py':'Generate diagnostic tone files',
 'verify_ram.py':'Validate that the supplied UF2 targets RAM rather than Flash',
 'Load-RAM.ps1':'Owner-layout picotool RAM loading helper',
 'Monitor.ps1':'Owner-layout serial monitor helper',
 'check_protocol.py':'Firmware protocol validation helper',
 'MainActivity.java':'Android local file picker, play/pause and status UI',
 'LoopService.java':'Android PCM loop, notification controls and audio-focus handling',
 'AudioLoader.java':'Android media decode and format/size/duration limits',
 'PcmGain.java':'Optional bounded constant PCM gain with peak ceiling',
 'PcmGainTest.java':'Nine host-side checks for optional gain behavior',
 'AndroidManifest.xml':'Android component, SDK and permission declarations',
 'toolchain.example.json':'Example local SDK/JDK/Python/signing-key locations',
 'sdk-downloads.json':'Original official SDK package download provenance',
 'merge_apk.py':'Insert compiled dex into unsigned APK resources',
 'BeaconLoop-1.0.apk':'Signed development Android loop-player installation package',
 'BeaconLoop-1.1.apk':'Beacon Loop 1.1 with built-in 19-21 kHz and gap-test choices',
 'default-beacon.wav':'Bundled unmodified current lossless phone beacon',
 'verify_handoff.py':'Offline checks runnable without private recordings or a connected board',
 'package_release.py':'Generate file catalogs, checksums and share/local ZIP packages',
 'verify_joint_delay.py':'Full RX4 model/cache/turn checks plus private saved-recording replay',
 'verify_highband_20k.py':'Synthetic high-band receiver regression with old code baseline',
 'verify_controls.py':'Receive-only controls, profile state and cancelled capture checks',
 'verify_raw_packet.py':'Simulated packet faults, timeout, cancellation and resynchronization',
 'verify_english_ui.py':'English UI smoke checks; needs the intended environment/device',
 'verify_beacon_import.py':'Compatible reference import regression',
 'verify_crc32_hardware.py':'Physical USB packet CRC check',
 'verify_packet_recovery_hardware.py':'Physical malformed/partial packet recovery check',
 'benchmark_latency.py':'Measure physical packet/pipeline timing',
 'capture_rx4_phone_trial.py':'Finite seven-channel phone trial capture with optional GUI',
 'analyze_rx4_phone_trial.py':'Analyze saved trial timing, spectra, level and bearing events',
 'replay_rx4_trial.py':'Run exact saved samples through RX3 and RX4',
 'generate_phone_mp3_20k.py':'Generate and validate current phone MP3 beacon/probes',
 'plot_beacon_waveform.py':'Plot original beacon amplitude, sample detail and spectrogram',
}

def purpose(rel):
    p=Path(rel);name=p.name
    if name=='Build.ps1':return 'Android SDK/JDK build and development signing' if rel.startswith('android-player/') else 'Owner-layout Pico SDK RAM/Flash build helper'
    if name in PURPOSE:return PURPOSE[name]
    if name.startswith('01_LOCATE'):return 'Phone coded localization beacon (match receiver profile)'
    if 'TONE' in name.upper():return 'Frequency/level probe; does not alone authorize a bearing'
    if p.suffix=='.uf2':return 'Pico firmware image; use current firmware/ image unless testing this historical version'
    if p.suffix=='.elf':return 'Pico firmware debug/executable artifact'
    if p.suffix in ('.wav','.mp3'):return 'Generated transmitter/reference audio: '+p.stem
    if p.suffix=='.png':return 'Report visualization: '+p.stem.replace('-',' ')
    if p.suffix in ('.jpg','.jpeg'):return 'User-supplied hardware/reference photograph'
    if p.suffix=='.pdf':return 'Original board/microphone technical reference'
    if p.suffix in ('.docx','.pptx'):return 'Original team project notes/proposal'
    if p.suffix=='.zip':return 'Reviewed source baseline needed by regression/replay tools'
    if p.suffix in ('.json','.csv','.sha256'):return 'Recorded configuration, validation or provenance: '+p.stem.replace('-',' ')
    if p.suffix in ('.md','.txt'):return 'Instructions/report: '+p.stem.replace('_',' ').replace('-',' ')
    if p.suffix in ('.py','.ps1','.cmd','.c','.h','.pio'):return 'Utility/source: '+p.stem.replace('_',' ').replace('-',' ')
    if p.suffix=='.xml':return 'Android UI resource/configuration'
    return 'Project configuration/artifact: '+name

def role(rel):
    if rel.startswith('legacy/'):return 'Historical reference; not active launch code'
    if rel.startswith('stages/'):return 'Stage record / reproducibility evidence'
    if rel.startswith('references/'):return 'Original hardware/project reference'
    if rel.startswith('reports/'):return 'Human-readable findings and figures'
    if rel.startswith('android-player/'):return 'Android transmitter'
    if rel.startswith('SEN0325-Pico-Setup/'):return 'Active Pico + desktop receiver'
    if rel.startswith('audio/'):return 'Transmitter/reference audio'
    if rel.startswith(('tests/','tools/')):return 'Verification / maintenance'
    return 'Project documentation / entry'

files=sorted(set(tracked()+['docs/FILE_CATALOG.md','docs/FILE_CATALOG.csv','SHA256SUMS.txt']))
rows=[{'path':x,'role':role(x),'purpose':purpose(x)} for x in files]
buf=io.StringIO(newline='');w=csv.DictWriter(buf,fieldnames=['path','role','purpose']);w.writeheader();w.writerows(rows)
write(ROOT/'docs/FILE_CATALOG.csv',buf.getvalue())
md=['# Published file catalog','',f'{len(rows)} files. Relative paths start at the repository root. Historical entries are reference material, not the launch path. Original captures/logs and repeated local binary archives are intentionally excluded; see [SHARING.md](SHARING.md).','',
    '| File | Role | Function |','|---|---|---|']
md.extend('| `'+r['path']+'` | '+r['role']+' | '+r['purpose'].replace('|','/')+' |' for r in rows)
write(ROOT/'docs/FILE_CATALOG.md','\n'.join(md)+'\n')

# Inspect secret-like material without ever printing a matching value.
patterns=[rb'gh[pousr]_[A-Za-z0-9]{25,}',rb'github_pat_[A-Za-z0-9_]{25,}',
          rb'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----',rb'AKIA[0-9A-Z]{16}',rb'xox[baprs]-[A-Za-z0-9-]{20,}']
findings=[]
for rel in files:
    if rel=='SHA256SUMS.txt':continue
    path=ROOT/rel
    if path.suffix.lower() in ('.jks','.keystore','.pem','.p12','.npz') or any(part in ('logs','captures','trials','runtime-logs','build-ram') for part in path.relative_to(ROOT).parts):
        findings.append({'path':rel,'reason':'excluded category unexpectedly tracked'})
    data=path.read_bytes()
    if len(data)>90*1024*1024:findings.append({'path':rel,'reason':'oversize Git object'})
    if any(re.search(pattern,data) for pattern in patterns):findings.append({'path':rel,'reason':'credential-like pattern'})
if findings:
    write(OUT/'audit-findings.json',json.dumps(findings,indent=2));raise RuntimeError('Resolve delivery/audit-findings.json before publishing; no secret values printed.')

sha_lines=[hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()+'  '+rel for rel in files if rel!='SHA256SUMS.txt']
write(ROOT/'SHA256SUMS.txt','\n'.join(sha_lines)+'\n')
team_zip=OUT/'EE475-Team-Handoff-2026-11-02.zip'
with zipfile.ZipFile(team_zip,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for rel in files:z.write(ROOT/rel,'ee475-acoustic-localization/'+rel)
with zipfile.ZipFile(team_zip) as z:
    assert z.testzip() is None
    for line in sha_lines:
        digest,rel=line.split('  ',1)
        assert hashlib.sha256(z.read('ee475-acoustic-localization/'+rel)).hexdigest()==digest

local=[]
for path in ROOT.rglob('*'):
    if not path.is_file():continue
    rel=path.relative_to(ROOT).as_posix()
    if rel.startswith(('.git/','delivery/')):continue
    local.append({'path':rel,'published':rel in files,'role':role(rel),'purpose':purpose(rel),'bytes':path.stat().st_size})
local.sort(key=lambda x:x['path'])
buf=io.StringIO(newline='');w=csv.DictWriter(buf,fieldnames=list(local[0]));w.writeheader();w.writerows(local)
write(ROOT/'docs/LOCAL_FILE_INDEX.csv',buf.getvalue())
index='EE475 COMPLETE LOCAL FILE INDEX / 2026-11-02\nPublished subset: docs/FILE_CATALOG.md. Private raw recordings and historical packages remain local.\n\n'
index+='\n'.join(r['path']+' | '+('GITHUB' if r['published'] else 'LOCAL ONLY')+' | '+r['purpose'] for r in local)+'\n'
write(ROOT/'FILE_INDEX.txt',index);write(ROOT/'00_全部文件索引.txt',index)

result={'date':'2026-11-02','published_files':len(files),'team_zip':team_zip.name,
        'team_zip_bytes':team_zip.stat().st_size,'team_zip_sha256':hashlib.sha256(team_zip.read_bytes()).hexdigest(),
        'local_files_indexed':len(local),'credential_pattern_findings':0,
        'excluded_original_recordings':True,'excluded_signing_keys':True,'zip_crc_and_file_hashes_verified':True}
if args.local_archive:
    local_zip=OUT/'EE475-Complete-Local-Archive-2026-11-02.zip'
    candidates=[f for f in ROOT.rglob('*') if f.is_file() and not f.relative_to(ROOT).as_posix().startswith(('.git/','delivery/'))]
    with zipfile.ZipFile(local_zip,'w',zipfile.ZIP_DEFLATED,compresslevel=3) as z:
        for path in candidates:z.write(path,'EE475/'+path.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(local_zip) as z:assert z.testzip() is None
    result.update(local_zip=local_zip.name,local_zip_files=len(candidates),local_zip_bytes=local_zip.stat().st_size,
                  local_zip_sha256=hashlib.sha256(local_zip.read_bytes()).hexdigest())
write(OUT/'PACKAGE_MANIFEST.json',json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
