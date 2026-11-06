"""Encode the gap-test phone file. Does not play audio or replace coded-20."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import numpy as np
import imageio_ffmpeg

PROJECT=Path(__file__).resolve().parents[1]
ROOT=PROJECT/'SEN0325-Pico-Setup'
DEST=PROJECT/'audio/phone/HF2-gap-test'
sys.path.insert(0,str(ROOT))
from beacon_dsp import RATE,SIZE,prepare_beacon,template

DEST.mkdir(parents=True,exist_ok=True)
wav=prepare_beacon(ROOT,'coded-gap',single_speaker=True)
import wave
with wave.open(str(wav),'rb') as audio:
    pcm=np.frombuffer(audio.readframes(audio.getnframes()),dtype='<i2').reshape(-1,2).copy()
phone_wav=DEST/'01_LOCATE_18-22kHz_43ms-gap.wav'
with wave.open(str(phone_wav),'wb') as audio:
    audio.setnchannels(2);audio.setsampwidth(2);audio.setframerate(RATE)
    audio.writeframes(pcm.tobytes())
encoder=imageio_ffmpeg.get_ffmpeg_exe()
target=DEST/'01_LOCATE_18-22kHz_43ms-gap.mp3'
options=['-c:a','libmp3lame','-q:a','0','-compression_level','0','-cutoff','22000','-joint_stereo','0','-write_xing','1']
source=pcm[RATE:-RATE,1]/32768
gain=1.
ratio=None
for _ in range(3):
    command=[encoder,'-hide_banner','-loglevel','error','-y','-f','s16le','-ar',str(RATE),'-ac','2','-i','pipe:0',
             '-af',f'volume={gain:.9f}',*options,str(target)]
    subprocess.run(command,input=pcm.tobytes(),check=True,capture_output=True)
    raw=subprocess.check_output([encoder,'-hide_banner','-loglevel','error','-i',str(target),'-f','f32le','-ar',str(RATE),'-ac','2','pipe:1'])
    decoded=np.frombuffer(raw,dtype='<f4').reshape(-1,2).astype(np.float64)
    steady=decoded[RATE:-RATE,1]
    ratio=20*np.log10(max(np.std(steady),1e-12)/max(np.std(source),1e-12))
    if abs(ratio)<.15:break
    gain*=10**(-ratio/20)
period,_spectrum,_mask=template('coded-gap')
reference=period/np.linalg.norm(period)
search=steady[:SIZE*4]
scores=np.array([np.dot(search[offset:offset+SIZE],reference)/max(np.linalg.norm(search[offset:offset+SIZE]),1e-12) for offset in range(SIZE)])
offset=int(scores.argmax())
aligned=steady[offset:offset+(len(steady)-offset)//SIZE*SIZE].reshape(-1,SIZE)
active=aligned[:,128:1920];quiet=aligned[:,2304:3968]
entry={'file':target.name,'wav':phone_wav.name,'wav_sha256':hashlib.sha256(phone_wav.read_bytes()).hexdigest(),
       'mp3_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'mp3_bytes':target.stat().st_size,
       'rms_change_db':round(float(ratio),3),'period_alignment_sample':offset,
       'period_correlation':round(float(scores[offset]),5),
       'decoded_active_rms':round(float(np.std(active)),6),
       'decoded_gap_rms':round(float(np.std(quiet)),6),
       'decoded_gap_to_active':round(float(np.std(quiet)/max(np.std(active),1e-12)),5),
       'left_channel_rms':float(np.std(decoded[:,0])),'peak_decoded':round(float(np.max(np.abs(decoded))),5)}
assert abs(ratio)<.5,entry
assert entry['decoded_gap_to_active']<0.08,entry
assert np.std(decoded[:,0])<1e-4,entry
assert np.max(np.abs(decoded))<.99,entry
report={'passed':True,'purpose':'Phone-file codec check only; not a room or angle test','file':entry}
out=PROJECT/'stages/08-gap-beacon'
out.mkdir(parents=True,exist_ok=True)
(out/'mp3-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
