"""Known band-limited periodic code, matched detection and all-pair SRP-PHAT.

This is an experimental acoustic estimator, not a distance or identity guarantee.
No system audio settings are changed. Raw microphone audio stays in memory.
"""
from collections import deque
import json
import math
from pathlib import Path
import time
import wave
import numpy as np
from runtime_tuning import STRONG_CODE_PNR_DB,STRONG_HISTORY_BURSTS,STRONG_SMOOTHING_SECONDS,WEAK_SMOOTHING_SECONDS

RATE=48000
SIZE=4096
CHANNELS=("D0L","D0R","D1L","D1R","D2L","D2R","D3R_CENTER")
PROFILES={
    "coded-audible":{"label":"Coded localization | Audible","low":900,"high":3900,"center":2400},
    "coded-ultrasonic":{"label":"Coded localization | 20-22 kHz experimental","low":20040,"high":21960,"center":21000},
    "coded-16-18":{"label":"Stage 1 | 16-18 kHz","low":16000,"high":18000,"center":17000},
    "coded-20":{"label":"Stage 2 | 20 kHz center, 19-21 kHz","low":19000,"high":21000,"center":20000},
    # Test profile only. One capture is still one 4096-sample period because
    # samples between RECORD packets are not continuous. The second half is silence.
    "coded-gap":{"label":"Gap test | 18-22 kHz, 43 ms silence","low":18000,"high":22000,"center":20000,
                 "active_samples":2048},
}

from beacon_importer import load_active
_active_import=load_active(Path(__file__).resolve().parent)
if _active_import:
    PROFILES[_active_import['profile']]=_active_import['spec']

def gapped_template(config,frequencies,mask):
    """Wider-band burst, then silence, inside the existing 4096-sample period."""
    active=int(config['active_samples'])
    if not 256<=active<=SIZE-256:raise ValueError('Gap test active length does not fit one capture')
    indices=np.flatnonzero(mask)
    rng=np.random.default_rng(0xEE4750A9)
    spectrum=np.zeros(SIZE//2+1,dtype=np.complex128)
    taper=np.minimum(1,np.minimum((frequencies[indices]-config['low']+12)/100,
                                  (config['high']-frequencies[indices]+12)/100))
    spectrum[indices]=taper*np.exp(1j*rng.uniform(-np.pi,np.pi,len(indices)))
    burst=np.fft.irfft(spectrum,SIZE)
    edge=64
    window=np.zeros(SIZE)
    window[:active]=1
    ramp=.5-.5*np.cos(np.linspace(0,np.pi,edge))
    window[:edge]*=ramp
    window[active-edge:active]*=ramp[::-1]
    samples=burst*window
    samples*=.35/max(np.max(np.abs(samples)),1e-12)
    return samples,np.fft.rfft(samples),mask

def template(profile):
    config=PROFILES[profile]
    frequencies=np.fft.rfftfreq(SIZE,1/RATE)
    mask=(frequencies>=config["low"])&(frequencies<=config["high"])
    if profile=='coded-gap':
        return gapped_template(config,frequencies,mask)
    if profile.startswith('imported-'):
        token=config['template_token']
        samples=np.load(Path(__file__).resolve().parent/'beacon_profiles'/token/'period.npy',allow_pickle=False)
        if samples.shape!=(SIZE,) or not np.isfinite(samples).all():raise ValueError('Invalid imported template')
        return samples,np.fft.rfft(samples),mask
    indices=np.flatnonzero(mask)
    rng=np.random.default_rng(0xEE475)
    spectrum=np.zeros(SIZE//2+1,dtype=np.complex128)
    taper=np.minimum(1,np.minimum((frequencies[indices]-config["low"]+12)/100,
                                  (config["high"]-frequencies[indices]+12)/100))
    spectrum[indices]=taper*np.exp(1j*rng.uniform(-np.pi,np.pi,len(indices)))
    samples=np.fft.irfft(spectrum,SIZE)
    # The new high band has its own file/profile. Keep the older WAVs unchanged.
    if profile in ('coded-16-18','coded-20'):
        # Reduce crest factor within the SAME band; do not create out-of-band
        # harmonics by clipping the exported waveform.
        target=np.abs(spectrum)
        best=samples.copy();best_crest=np.max(np.abs(best))/np.std(best)
        for _ in range(24):
            clipped=np.clip(samples,-2.2*np.std(samples),2.2*np.std(samples))
            candidate=np.fft.rfft(clipped)
            candidate=target*np.exp(1j*np.angle(candidate))
            samples=np.fft.irfft(candidate,SIZE)
            crest=np.max(np.abs(samples))/max(np.std(samples),1e-12)
            if crest<best_crest:best,best_crest=samples.copy(),crest
        samples=best
    peak=.35 if profile in ('coded-16-18','coded-20') else .12
    samples*=peak/max(np.max(np.abs(samples)),1e-12)
    return samples,np.fft.rfft(samples),mask

def prepare_beacon(root,profile,single_speaker=False):
    folder=Path(root)/"beacon-audio"
    folder.mkdir(exist_ok=True)
    path=folder/(profile+('-v1-right-only.wav' if single_speaker else '-v1.wav'))
    if not path.exists():
        period,_,_=template(profile)
        samples=np.tile(period,144) # 12.288 s, integer number of code periods.
        fade=int(RATE*.03)
        ramp=.5-.5*np.cos(np.linspace(0,np.pi,fade))
        samples[:fade]*=ramp
        samples[-fade:]*=ramp[::-1]
        pcm=np.rint(samples*32767).astype('<i2')
        if single_speaker:
            pcm=np.column_stack((np.zeros_like(pcm),pcm)).astype('<i2')
        with wave.open(str(path),'wb') as f:
            f.setnchannels(2 if single_speaker else 1);f.setsampwidth(2);f.setframerate(RATE);f.writeframes(pcm.tobytes())
    with wave.open(str(path),'rb') as f:
        if (f.getnchannels(),f.getsampwidth(),f.getframerate(),f.getnframes())!=(2 if single_speaker else 1,2,RATE,SIZE*144):
            raise ValueError('Unexpected coded-audio format: '+str(path))
    return path

class BeaconEstimator:
    def __init__(self,config_path,profile):
        self.path=Path(config_path)
        self.profile=profile
        self.spec=PROFILES[profile]
        self.code,self.spectrum,self.mask=template(profile)
        self.indices=np.flatnonzero(self.mask)
        self.weights=np.abs(self.spectrum[self.indices])
        self.weights/=self.weights.max()
        self.pairs=np.array([(i,j) for i in range(7) for j in range(i+1,7)])
        config=json.loads(self.path.read_text(encoding='utf-8-sig'))
        radius=config['radius_m']
        positions=[]
        for name in CHANNELS:
            if name=='D3R_CENTER':
                positions.append((0,0))
            else:
                angle=math.radians(config['clockwise_degrees_from_U7_M0'][name])
                positions.append((radius*math.sin(angle),radius*math.cos(angle)))
        positions=np.array(positions)
        delta=positions[self.pairs[:,0]]-positions[self.pairs[:,1]]
        self.delta=delta
        self.speed=config['sound_speed_m_s']
        self.angles=np.arange(360)
        self.projections=np.array([.35,.5,.7,.85,1.0])
        radians=np.deg2rad(self.angles)
        vectors=np.stack((np.sin(radians),np.cos(radians)),axis=1)
        self.upsample=8
        self.lags=-RATE/config['sound_speed_m_s']*self.projections[:,None,None]*(vectors@delta.T)[None,:,:]
        self.history=deque(maxlen=3)
        self.candidate=None
        self.confirmations=0
        self.last_candidate_time=0
        self.smoothed=None
        self.last_valid_time=0

    def group_delay(self,averaged,valid_pairs):
        frequencies=np.fft.rfftfreq(SIZE,1/RATE)[self.indices]
        delays=[];rows=[];weights=[];errors=[]
        for pair in valid_pairs:
            value=averaged[pair]
            weight=np.abs(value)
            phase=np.unwrap(np.angle(value))
            if np.sum(weight)<1e-9:
                continue
            x=frequencies-np.sum(weight*frequencies)/np.sum(weight)
            y=phase-np.sum(weight*phase)/np.sum(weight)
            denominator=np.sum(weight*x*x)
            slope=np.sum(weight*x*y)/max(denominator,1e-12)
            delay=slope/(2*np.pi)
            error=float(np.sqrt(np.sum(weight*(y-slope*x)**2)/np.sum(weight)))
            if error>.35 or abs(delay)*self.speed>np.linalg.norm(self.delta[pair])*1.35:
                continue
            delays.append(delay*self.speed)
            rows.append(self.delta[pair])
            weights.append(1/(.04+error**2));errors.append(error)
        count=len(delays)
        details={'group_delay_pairs':count}
        if count<max(6,math.ceil(len(valid_pairs)/2)):
            return None,0,{**details,'group_delay_reason':'insufficient_group_delays'}
        matrix=np.array(rows);target=np.array(delays);weights=np.array(weights)
        robust=weights.copy()
        for _ in range(3):
            vector=np.linalg.lstsq(matrix*np.sqrt(robust[:,None]),target*np.sqrt(robust),rcond=None)[0]
            residual=(matrix@vector-target)*RATE/self.speed
            robust=weights*np.minimum(1,.5/np.maximum(np.abs(residual),1e-9))
        # Score original weights, so fitting cannot hide an inconsistent delay.
        rms=float(np.sqrt(np.sum(weights*residual**2)/np.sum(weights)))
        projection=float(np.linalg.norm(vector))
        raw=float(np.degrees(np.arctan2(vector[0],vector[1]))%360)
        quality=math.exp(-.5*(rms/.75)**2)*count/len(valid_pairs)
        details.update(group_delay_rms_samples=round(rms,4),horizontal_projection=round(projection,4),
            spectral_phase_residual_rad=round(float(np.median(errors)),4),candidate_angle_deg=round(raw,2))
        if not .25<=projection<=1.3 or rms>1 or quality<.5:
            return None,quality,{**details,'group_delay_reason':'geometry_mismatch'}
        return raw,quality,details

    def estimate(self,samples,health,now=None):
        if self.profile in ('coded-16-18','coded-20','coded-gap') or self.profile.startswith('imported-'):
            from highband_dsp import estimate_highband
            return estimate_highband(self,samples,health,now)
        started=time.perf_counter()
        now=time.monotonic() if now is None else now
        base={'valid':False,'frequency':self.spec['center'],'profile':self.profile,
              'method':'coded_matched_filter_group_delay' if self.profile=='coded-ultrasonic' else 'coded_matched_filter_SRP_PHAT','received_at':now}
        def finish(reason,**details):
            return {**base,'reason':reason,'processing_ms':round((time.perf_counter()-started)*1000,2),**details},telemetry
        telemetry={}
        if health.get('dropped',0) or health.get('rx_stall',0):
            self.history.clear()
            return finish('capture_gap')
        audio=np.asarray(samples,dtype=np.float64)
        if audio.shape!=(SIZE,7) or not np.all(np.isfinite(audio)):
            return finish('invalid_raw_audio')
        if np.any(np.abs(audio)>=32760):
            self.history.clear()
            return finish('clipping')
        audio-=audio.mean(axis=0)
        spectra=np.fft.rfft(audio,axis=0).T
        # A known, random spectral phase sequence provides processing gain.
        matched=np.zeros((7,SIZE),dtype=np.complex128)
        matched[:,self.indices]=spectra[:,self.indices]*np.conj(self.spectrum[self.indices])
        impulse=np.fft.ifft(matched,axis=1)
        envelope=np.abs(impulse)
        width=max(16,round(2*RATE/(self.spec['high']-self.spec['low'])))
        pnr=[];concentrations=[];present=[]
        power=np.abs(spectra[:,self.indices])**2
        rms=np.sqrt(2*power.sum(axis=1))/SIZE
        for ch,name in enumerate(CHANNELS):
            peak=int(envelope[ch].argmax())
            distance=np.minimum((np.arange(SIZE)-peak)%SIZE,(peak-np.arange(SIZE))%SIZE)
            outside=envelope[ch,distance>width]
            noise=np.sqrt(np.mean(outside**2))
            ratio=20*np.log10(max(envelope[ch,peak],1e-12)/max(noise,1e-12))
            fraction=float(np.sum(envelope[ch,distance<=width]**2)/max(np.sum(envelope[ch]**2),1e-12))
            hit=bool(ratio>=14.5 and fraction>=.18 and rms[ch]>=1)
            pnr.append(float(ratio));concentrations.append(fraction);present.append(hit)
            telemetry[name]={'frequency':self.spec['center'],'rms':round(float(rms[ch]),2),
                'ratio':round(fraction,4),'snr_db':round(float(ratio),2),'present':hit}
        hits=int(sum(present))
        diagnostics={'code_channels':hits,'code_pnr_db':round(float(np.median(pnr)),2),
                     'code_concentration':round(float(np.median(concentrations)),3)}
        strong=self.profile=='coded-audible' and hits>=6 and diagnostics['code_pnr_db']>=STRONG_CODE_PNR_DB
        if hits<4:
            self.history.clear();self.confirmations=0
            return finish('beacon_not_detected',**diagnostics)
        # Use a common code-arrival region to attenuate late echoes. A reflection
        # inside this 4 ms region can still bias the result; no guarantee of LOS.
        normalized=envelope/np.maximum(envelope.max(axis=1,keepdims=True),1e-12)
        center=int(np.mean(normalized[np.array(present)],axis=0).argmax())
        distance=np.minimum((np.arange(SIZE)-center)%SIZE,(center-np.arange(SIZE))%SIZE)
        gate=np.where(distance<96,.5+.5*np.cos(np.pi*np.minimum(distance,96)/96),0)
        isolated=np.fft.fft(impulse*gate,axis=1)[:,:SIZE//2+1]
        left,right=self.pairs.T
        cross=isolated[left]*np.conj(isolated[right])
        magnitude=np.abs(cross[:,self.indices])
        reliability=np.minimum(1,magnitude/np.maximum(np.median(magnitude,axis=1,keepdims=True),1e-12))
        cross_band=cross[:,self.indices]/np.maximum(magnitude,1e-12)
        pair_valid=np.array(present)[left]&np.array(present)[right]
        weighted=cross_band*reliability*self.weights[None,:]*pair_valid[:,None]
        # Average at most three recent bursts; noise does not accumulate forever.
        while self.history and now-self.history[0][0]>1.2:
            self.history.popleft()
        self.history.append((now,weighted))
        history=list(self.history)[-STRONG_HISTORY_BURSTS:] if strong else list(self.history)
        averaged=sum(row[1] for row in history)/len(history)
        valid_pairs=np.flatnonzero(pair_valid)
        diagnostics.update(channels=hits,pairs=len(valid_pairs),averaged_bursts=len(history))
        if self.profile=='coded-ultrasonic':
            # Carrier phase aliases at this aperture. Use phase-vs-frequency
            # slope (group delay), with a separate intercept for every pair.
            raw,quality,details=self.group_delay(averaged,valid_pairs)
            diagnostics.update(details)
            if raw is None:
                self.confirmations=0
                return finish('group_delay_inconsistent',**diagnostics)
        else:
            full=np.zeros((len(valid_pairs),SIZE//2+1),dtype=np.complex128)
            full[:,self.indices]=averaged[valid_pairs]
            normalization=np.maximum(np.sum(np.abs(averaged[valid_pairs]),axis=1),1e-12)
            gcc=np.fft.irfft(full,n=SIZE*self.upsample,axis=1)*(SIZE*self.upsample)/(2*normalization[:,None])
            lag=(self.lags[:,:,valid_pairs]*self.upsample)%(SIZE*self.upsample)
            floor=np.floor(lag)
            fraction=lag-floor
            index=floor.astype(np.int32)%(SIZE*self.upsample)
            pair_index=np.arange(len(valid_pairs))[None,None,:]
            values=gcc[pair_index,index]*(1-fraction)+gcc[pair_index,(index+1)%(SIZE*self.upsample)]*fraction
            # Trim the least consistent microphone pairs, retain >=80% evidence.
            scores=np.mean(np.sort(values,axis=-1)[:,:,int(len(valid_pairs)*.2):],axis=-1)
            row,col=np.unravel_index(int(scores.argmax()),scores.shape)
            raw=float(self.angles[col]);peak=float(scores[row,col])
            circular=np.abs((self.angles-raw+180)%360-180)
            margin=peak-float(np.max(scores[:,circular>=30]))
            diagnostics.update(srp_peak=round(peak,4),peak_margin=round(margin,4),
                horizontal_projection=float(self.projections[row]),candidate_angle_deg=raw)
            if peak<.60 or margin<.055:
                self.confirmations=0
                return finish('ambiguous_beacon_direction',**diagnostics)
            quality=min(1,max(0,peak))*min(1,margin/.15)*hits/7
        difference=abs((raw-(self.candidate if self.candidate is not None else raw)+180)%360-180)
        self.confirmations=self.confirmations+1 if difference<=20 and now-self.last_candidate_time<1.2 else 1
        self.candidate=raw;self.last_candidate_time=now
        if self.confirmations<2:
            return finish('confirming_beacon_direction',**diagnostics)
        config=json.loads(self.path.read_text(encoding='utf-8-sig'))
        angle=((-1 if config['mirror_view'] else 1)*raw+config['heading_offset_deg'])%360
        vector=complex(math.sin(math.radians(angle)),math.cos(math.radians(angle)))
        smoothing=(STRONG_SMOOTHING_SECONDS if strong else WEAK_SMOOTHING_SECONDS) if self.profile=='coded-audible' else .4
        diagnostics['motion_smoothing_s']=smoothing
        if self.smoothed is not None and now-self.last_valid_time<1:
            alpha=1-math.exp(-max(.001,now-self.last_valid_time)/smoothing)
            vector=self.smoothed*(1-alpha)+vector*alpha
        vector/=max(abs(vector),1e-12)
        self.smoothed=vector;self.last_valid_time=now
        return finish('estimated',valid=True,angle_deg=round(math.degrees(math.atan2(vector.real,vector.imag))%360,2),
            raw_angle_deg=raw,confidence=round(quality,3),heading_calibrated=config['heading_calibrated'],**diagnostics)
