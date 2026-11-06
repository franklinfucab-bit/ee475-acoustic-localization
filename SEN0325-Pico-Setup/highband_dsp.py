"""Known-code high-band reception; no hardware gain or range claims.

Partial spectral whitening reduces narrow electronic tones and response tilt.
Delay fitting uses a bounded complex phase-ramp search with a free intercept,
so carrier phase does not choose a spatially aliased direction. Strong coded
signals may use the arrival-consensus repair after the primary fit rejects.
HF1, HF2 and compatible imported references use this path. Legacy audible
and old 20-22 kHz profiles retain their earlier estimator.
"""
import json
import math
import time
import numpy as np

RATE=48000
SIZE=4096
CHANNELS=('D0L','D0R','D1L','D1R','D2L','D2R','D3R_CENTER')
PNR_MIN=12.5
CONCENTRATION_MIN=.12
MIN_CHANNELS=4

PROBE_FREQUENCIES=(1000,16000,17000,17500,18000,19000,19500,20000,20500,21000)

def probe_levels(samples=None,spectra=None,extra_frequencies=()):
    """Median channel RMS in +/-150 Hz windows, dBFS; no gain or SPL claim.

    Diagnostic windows respond to pure tones independently of code acceptance.
    Reuse the capture FFT when the high-band receiver has it.
    """
    if spectra is None:
        audio=np.asarray(samples,dtype=np.float64)
        if audio.shape!=(SIZE,7) or not np.all(np.isfinite(audio)):
            return {}
        spectra=np.fft.rfft(audio-audio.mean(axis=0),axis=0).T
    frequencies=np.fft.rfftfreq(SIZE,1/RATE)
    levels={}
    for hz in sorted(set(PROBE_FREQUENCIES)|set(extra_frequencies)):
        bins=np.abs(frequencies-hz)<=150
        rms=np.sqrt(2*np.sum(np.abs(spectra[:,bins])**2,axis=1))/SIZE
        levels[str(hz)]=round(float(np.median(20*np.log10(np.maximum(rms,1e-9)/32768))),1)
    return levels


def reset(receiver,reason='receiver_reset'):
    receiver.history.clear()
    receiver.confirmations=0
    receiver.candidate=None
    receiver.smoothed=None
    receiver.last_valid_time=0
    receiver._highband_code_time=None
    receiver._highband_code_reset=reason
    receiver._highband_pair_scores=None


def confirm_code(receiver,now):
    """Confirm repeated code presence independently of geometric-fit success.

    A missing/invalid capture still clears evidence. A rejected bearing does
    not erase a code that was just detected, and target motion is unrestricted.
    """
    previous=getattr(receiver,'_highband_code_time',None)
    gap=now-previous if previous is not None else None
    continuous=gap is not None and 0<gap<.75
    reset_reason=(getattr(receiver,'_highband_code_reset','first_code_hit') if previous is None
                  else 'none' if continuous else 'code_time_gap')
    receiver.confirmations=min(2,receiver.confirmations+1) if continuous else 1
    receiver._highband_code_time=now
    receiver._highband_code_reset='none'
    return {'code_confirmation_windows':receiver.confirmations,'code_confirmation_required':2,
            'code_confirmation_gap_s':round(gap,4) if gap is not None else None,
            'code_confirmation_reset_reason':reset_reason,'direction_angle_gate_enabled':False}


def fit_delays(receiver,averaged,valid_pairs):
    frequencies=np.fft.rfftfreq(SIZE,1/RATE)[receiver.indices]
    centered=frequencies-frequencies.mean()
    if not hasattr(receiver,'_highband_delay_bank'):
        extent=math.ceil(np.linalg.norm(receiver.delta,axis=1).max()/receiver.speed*RATE*1.25)+1
        grid=np.arange(-extent,extent+.0625,.125)
        bank=np.exp(-2j*np.pi*centered[:,None]*grid[None,:]/RATE)
        receiver._highband_delay_bank=(grid,bank)
    grid,bank=receiver._highband_delay_bank
    band=averaged[valid_pairs]
    weights=np.abs(band)
    totals=np.maximum(weights.sum(axis=1),1e-12)
    # einsum has predictable small-matrix cost without spawning BLAS workers.
    scores=np.abs(np.einsum('pf,fg->pg',band,bank,optimize=False))/totals[:,None]
    # The RX4 rescue reuses these exact observations; no second FFT/search.
    receiver._highband_pair_scores=(averaged,valid_pairs.copy(),grid,scores,totals,weights)
    delays=[];rows=[];pair_weights=[];coherences=[];diagnostics=[];accepted_rows=[]
    for row,pair in enumerate(valid_pairs):
        allowed=np.abs(grid)<=np.linalg.norm(receiver.delta[pair])/receiver.speed*RATE*1.25+.25
        curve=np.where(allowed,scores[row],-1.)
        index=int(curve.argmax());coherence=float(curve[index])
        support=float(totals[row]**2/max(np.sum(weights[row]**2),1e-12))
        spread=coherence-float(np.min(curve[allowed]))
        diag={'pair':[CHANNELS[ch] for ch in receiver.pairs[pair]],'pair_index':int(pair),
              'coherence':round(coherence,4),'support_bins':round(support,2),
              'coherence_spread':round(spread,4),'used_in_fit':False}
        diagnostics.append(diag)
        if coherence<.60 or support<32 or spread<.012:
            diag['rejection']='low_coherence' if coherence<.60 else 'few_bins' if support<32 else 'flat_delay_score'
            continue
        lag=float(grid[index])
        if 0<index<len(grid)-1 and allowed[index-1] and allowed[index+1]:
            a,b,c=scores[row,index-1:index+2]
            curvature=a-2*b+c
            if curvature<0:lag+=float(np.clip(.5*(a-c)/curvature,-1,1))*.125
        delays.append(lag*receiver.speed/RATE)
        diag.update(delay_samples=round(lag,4),used_in_fit=True)
        accepted_rows.append(diag)
        rows.append(receiver.delta[pair])
        pair_weights.append(coherence**4)
        coherences.append(coherence)
    count=len(rows)
    details={'group_delay_pairs':count,'delay_fit':'bounded_complex_coherence',
             'median_pair_coherence':round(float(np.median(coherences)),3) if count else 0,
             'pair_delay_diagnostics':diagnostics}
    if count<max(6,math.ceil(len(valid_pairs)/2)):
        return None,0,{**details,'group_delay_reason':'insufficient_group_delays'}
    matrix=np.array(rows);target=np.array(delays);weights=np.array(pair_weights)
    robust=weights.copy()
    for _ in range(4):
        vector=np.linalg.lstsq(matrix*np.sqrt(robust[:,None]),target*np.sqrt(robust),rcond=None)[0]
        residual=(matrix@vector-target)*RATE/receiver.speed
        robust=weights*np.minimum(1,.65/np.maximum(np.abs(residual),1e-9))
    # Trim no more than 20% of pairs, then report BOTH retained and all-pair
    # residuals. This prevents one poor microphone pair dominating a weak trial
    # without allowing the fit to silently discard most contradictory evidence.
    keep=np.ones(count,dtype=bool)
    if count>=10:
        keep[np.argsort(np.abs(residual))[-int(count*.2):]]=False
        vector=np.linalg.lstsq(matrix[keep]*np.sqrt(weights[keep,None]),
                               target[keep]*np.sqrt(weights[keep]),rcond=None)[0]
        residual=(matrix@vector-target)*RATE/receiver.speed
    all_rms=float(np.sqrt(np.sum(weights*residual**2)/np.sum(weights)))
    rms=float(np.sqrt(np.sum(weights[keep]*residual[keep]**2)/np.sum(weights[keep])))
    projection=float(np.linalg.norm(vector))
    raw=float(np.degrees(np.arctan2(vector[0],vector[1]))%360)
    quality=float(np.median(coherences))*math.exp(-.5*(rms/.9)**2)*int(keep.sum())/len(valid_pairs)
    for index,diag in enumerate(accepted_rows):
        diag.update(residual_samples=round(float(residual[index]),4),retained_in_fit=bool(keep[index]))
    details.update(group_delay_rms_samples=round(rms,4),all_pair_rms_samples=round(all_rms,4),
                   retained_delay_pairs=int(keep.sum()),horizontal_projection=round(projection,4),
                   candidate_angle_deg=round(raw,2))
    if not .25<=projection<=1.3 or rms>1.0 or all_rms>1.5 or quality<.48:
        return None,quality,{**details,'group_delay_reason':'geometry_mismatch'}
    return raw,quality,details


def estimate_highband(receiver,samples,health,now=None):
    started=time.perf_counter()
    now=time.monotonic() if now is None else now
    center=receiver.spec['center']
    base={'valid':False,'frequency':center,'profile':receiver.profile,
          'method':'coded_matched_filter_highband_delay','received_at':now,
          'stage':'GAP-TEST' if receiver.profile=='coded-gap' else 'HF2' if receiver.profile!='coded-16-18' else 'HF1.1',
          'band_low_hz':receiver.spec['low'],'band_high_hz':receiver.spec['high']}
    telemetry={}
    def finish(reason,**details):
        return {**base,'reason':reason,'processing_ms':round((time.perf_counter()-started)*1000,2),**details},telemetry
    if health.get('dropped',0) or health.get('rx_stall',0):
        reset(receiver,'capture_gap');return finish('capture_gap')
    audio=np.asarray(samples,dtype=np.float64)
    if audio.shape!=(SIZE,7) or not np.all(np.isfinite(audio)):
        reset(receiver,'invalid_raw_audio');return finish('invalid_raw_audio')
    if np.any(np.abs(audio)>=32760):
        reset(receiver,'clipping');return finish('clipping')
    audio=audio-audio.mean(axis=0)
    spectra=np.fft.rfft(audio,axis=0).T
    probe_frequencies=tuple(round(receiver.spec['low']+(receiver.spec['high']-receiver.spec['low'])*i/4) for i in range(5))
    base['probe_bands_dbfs']=probe_levels(spectra=spectra,extra_frequencies=probe_frequencies)
    base['probe_frequencies_hz']=probe_frequencies
    band=spectra[:,receiver.indices]
    magnitude=np.abs(band)
    rms=np.sqrt(2*np.sum(magnitude**2,axis=1))/SIZE
    level=20*np.log10(np.maximum(rms,1e-9)/32768)
    # Bounded, partial whitening: cap narrow spectral spikes while preserving
    # phase and keeping gain finite in spectral nulls. RMS remains UNAMPLIFIED.
    reference=np.maximum(np.median(magnitude,axis=1,keepdims=True),1e-9)
    whitening=(reference/np.maximum(magnitude,reference*.12))**.65
    whitening=np.clip(whitening,.025,3.)
    matched=np.zeros((7,SIZE),dtype=np.complex128)
    matched[:,receiver.indices]=band*np.conj(receiver.spectrum[receiver.indices])*whitening
    impulse=np.fft.ifft(matched,axis=1)
    envelope=np.abs(impulse)
    positions=np.arange(SIZE)
    width=max(16,round(2*RATE/(receiver.spec['high']-receiver.spec['low'])))
    # 19-21 kHz and the gap test share one tracking rule so the audio comparison
    # uses the same standard. Hit follows the peak. A wider peak still has the
    # code; the old concentration cut turned Hit off while the microphones were
    # still receiving it. Empty captures stay near 0.05. The 16-18 kHz profile
    # keeps the concentration gate.
    track_each_capture=receiver.profile in ('coded-20','coded-gap')
    concentration_min=0.10 if track_each_capture else CONCENTRATION_MIN
    pnr=[];concentrations=[];present=[];channel_diagnostics=[]
    for ch,name in enumerate(CHANNELS):
        peak=int(envelope[ch].argmax())
        distance=np.minimum((positions-peak)%SIZE,(peak-positions)%SIZE)
        noise=np.sqrt(np.mean(envelope[ch,distance>width]**2))
        ratio=float(20*np.log10(max(envelope[ch,peak],1e-12)/max(noise,1e-12)))
        fraction=float(np.sum(envelope[ch,distance<=width]**2)/max(np.sum(envelope[ch]**2),1e-12))
        hit=bool(ratio>=PNR_MIN and rms[ch]>=.25 and (track_each_capture or fraction>=concentration_min))
        pnr.append(ratio);concentrations.append(fraction);present.append(hit)
        a,b,c=np.log(np.maximum(envelope[ch,(peak+np.array([-1,0,1]))%SIZE],1e-12))
        offset=float(np.clip(.5*(a-c)/(a-2*b+c),-.5,.5)) if abs(a-2*b+c)>1e-12 else 0.
        channel_diagnostics.append({'channel':name,'present':hit,'pnr_db':round(ratio,2),
            'concentration':round(fraction,4),'band_dbfs':round(float(level[ch]),1),
            'peak_sample':round((peak+offset)%SIZE,4)})
        telemetry[name]={'frequency':center,'rms':round(float(rms[ch]),2),'band_dbfs':round(float(level[ch]),1),
                         'ratio':round(fraction,4),'snr_db':round(ratio,2),'present':hit}
    hits=int(sum(present))
    details={'code_channels':hits,'code_pnr_db':round(float(np.median(pnr)),2),
             'code_concentration':round(float(np.median(concentrations)),3),
             'band_rms16':round(float(np.median(rms)),3),'band_level_dbfs':round(float(np.median(level)),1),
             'receiver_pnr_threshold_db':PNR_MIN,'receiver_concentration_threshold':concentration_min,
             'receiver_gain_is_hardware':False,
             'code_channel_diagnostics':channel_diagnostics}
    if hits<MIN_CHANNELS:
        if not track_each_capture:reset(receiver,'beacon_not_detected')
        return finish('beacon_not_detected',**details)
    details.update(confirm_code(receiver,now))
    normalized=envelope/np.maximum(envelope.max(axis=1,keepdims=True),1e-12)
    center=int(np.mean(normalized[np.array(present)],axis=0).argmax())
    for diag in channel_diagnostics:
        diag['relative_peak_samples']=round((diag['peak_sample']-center+SIZE/2)%SIZE-SIZE/2,4)
    distance=np.minimum((positions-center)%SIZE,(center-positions)%SIZE)
    gate=np.where(distance<96,.5+.5*np.cos(np.pi*np.minimum(distance,96)/96),0)
    isolated=np.fft.fft(impulse*gate,axis=1)[:,:SIZE//2+1]
    left,right=receiver.pairs.T
    cross=isolated[left][:,receiver.indices]*np.conj(isolated[right][:,receiver.indices])
    amplitude=np.abs(cross)
    reliability=np.minimum(1,amplitude/np.maximum(np.median(amplitude,axis=1,keepdims=True),1e-12))
    pair_valid=np.array(present)[left]&np.array(present)[right]
    weighted=cross/np.maximum(amplitude,1e-12)*reliability*receiver.weights[None,:]*pair_valid[:,None]
    while receiver.history and now-receiver.history[0][0]>.75:
        receiver.history.popleft()
    receiver.history.append((now,weighted))
    # One capture for both comparison beacons, so a move is not mixed with the
    # previous place. The 16-18 kHz profile still uses two strong bursts or three weak ones.
    count=1 if track_each_capture else 2 if hits>=6 and details['code_pnr_db']>=20 else 3
    history=list(receiver.history)[-count:]
    averaged=sum(row[1] for row in history)/len(history)
    valid_pairs=np.flatnonzero(pair_valid)
    details.update(channels=hits,pairs=len(valid_pairs),averaged_bursts=len(history))
    raw,quality,fit=fit_delays(receiver,averaged,valid_pairs)
    # Both comparison beacons reach the arrival fit after six channel matches.
    # The 16-18 kHz profile still requires a 24 dB peak and concentration of 0.5.
    arrival_ready=hits>=6 and (track_each_capture or (details['code_pnr_db']>=24 and details['code_concentration']>=.5))
    if raw is None and arrival_ready:
        from arrival_dsp import fit_arrivals
        if not hasattr(receiver,'geometry_for_arrivals'):
            receiver.geometry_for_arrivals=json.loads(receiver.path.read_text(encoding='utf-8-sig'))
            receiver.arrival_channels=CHANNELS
        arrival,arrival_quality,arrival_details=fit_arrivals(receiver,envelope,present)
        primary_angle=raw if raw is not None else fit.get('candidate_angle_deg')
        disagreement=abs((arrival-primary_angle+180)%360-180) if arrival is not None and primary_angle is not None else None
        fit['primary_candidate_angle_deg']=primary_angle
        fit['arrival_candidate_angle_deg']=arrival
        fit['estimator_disagreement_deg']=round(disagreement,2) if disagreement is not None else None
        fit['arrival_fallback_attempted']=True
        fit['complex_fit_rejection']=fit.get('group_delay_reason','inconsistent')
        if arrival is not None and raw is None:
            raw,quality=arrival,arrival_quality
            fit.update(arrival_details)
            fit.pop('group_delay_reason',None)
            fit['direction_source']='strong_code_arrival_consensus'
            base['method']='coded_matched_filter_arrival_consensus'
        else:
            fit['arrival_rejection']=arrival_details.get('group_delay_reason')
            fit['arrival_rejection_counts']=arrival_details.get('arrival_rejection_counts',{})
            fit['arrival_peak_counts']=arrival_details.get('arrival_peak_counts',{})
            fit['arrival_clusters_evaluated']=arrival_details.get('arrival_clusters_evaluated',0)
    if raw is None and hits>=6:
        from joint_delay_dsp import fit_joint_spectral
        joint,joint_quality,joint_fit=fit_joint_spectral(receiver,averaged,valid_pairs)
        fit['joint_attempt']=joint_fit
        if joint is not None:
            raw,quality=joint,joint_quality
            fit['primary_fit_rejection']=fit.get('group_delay_reason')
            fit['delay_fit']='joint_spectral_delay_consensus'
            fit['candidate_angle_deg']=round(raw,2)
            fit['direction_source']='joint_spectral_delay_consensus'
            fit.pop('group_delay_reason',None)
            base['method']='coded_matched_filter_joint_spectral_delay'
    details.update(fit)
    if raw is None:
        return finish('group_delay_inconsistent',**details)
    difference=abs((raw-(receiver.candidate if receiver.candidate is not None else raw)+180)%360-180)
    # Record candidate changes for diagnosis; they are not a motion veto.
    details['candidate_turn_deg']=round(difference,2)
    receiver.candidate=raw;receiver.last_candidate_time=now
    if receiver.confirmations<2:return finish('confirming_beacon_direction',**details)
    config=json.loads(receiver.path.read_text(encoding='utf-8-sig'))
    angle=((-1 if config['mirror_view'] else 1)*raw+config['heading_offset_deg'])%360
    vector=complex(math.sin(math.radians(angle)),math.cos(math.radians(angle)))
    smoothing=.18 if count==2 else .28
    if receiver.smoothed is not None and now-receiver.last_valid_time<.75:
        alpha=1-math.exp(-max(.001,now-receiver.last_valid_time)/smoothing)
        vector=receiver.smoothed*(1-alpha)+vector*alpha
    vector/=max(abs(vector),1e-12)
    receiver.smoothed=vector;receiver.last_valid_time=now
    receiver.last_trusted_raw=raw;receiver.last_trusted_time=now
    return finish('estimated',valid=True,angle_deg=round(math.degrees(math.atan2(vector.real,vector.imag))%360,2),
                  raw_angle_deg=raw,confidence=round(quality,3),heading_calibrated=config['heading_calibrated'],
                  motion_smoothing_s=smoothing,**details)
