"""Gap-test profile checks. These do not measure a physical angle."""
from pathlib import Path
import hashlib
import json
import math
import sys
import tempfile
import numpy as np

PROJECT=Path(__file__).resolve().parents[1]
ROOT=PROJECT/'SEN0325-Pico-Setup'
sys.path.insert(0,str(ROOT))
from app_controls import PROFILES as MENU
from beacon_dsp import BeaconEstimator,template,RATE,SIZE

CODED20_SHA256='1159cae8484ab19618b52660f0f6ef71f3eeef554e6ba4be0fd002f1db988a7c'
report={'passed':False,'checks':[]}

def check(name,ok,detail):
    report['checks'].append({'name':name,'passed':bool(ok),'detail':detail})
    print(f'{name}: {"PASS" if ok else "FAIL"} {detail}',flush=True)
    return ok

current,spectrum,_=template('coded-20')
gap,gap_spectrum,_=template('coded-gap')
current_hash=hashlib.sha256(np.ascontiguousarray(current).tobytes()).hexdigest()
check('coded20_template_unchanged',current_hash==CODED20_SHA256,current_hash)
active=gap[128:1920];quiet=gap[2304:3968]
active_rms=float(np.std(active));quiet_rms=float(np.std(quiet))
ratio=quiet_rms/max(active_rms,1e-12)
check('gap_is_quiet',ratio<0.05,{'active_rms':round(active_rms,5),'gap_rms':round(quiet_rms,5),'ratio':round(ratio,5)})
band=np.fft.rfftfreq(SIZE,1/RATE)
power=np.abs(gap_spectrum)**2
occupied=float(power[(band>=18000)&(band<=22000)].sum()/max(power.sum(),1e-18))
check('energy_in_18_22k',occupied>0.9,round(occupied,6))
check('launch_menu_keeps_coded20_first',tuple(MENU.values())[0]=='coded-20' and 'coded-gap' in MENU.values(),tuple(MENU))
launcher=(ROOT/'refresh_and_start.py').read_text(encoding='utf-8')
check('one_click_starts_gap_test',"'--profile','coded-gap'" in launcher,True)
routed,_=BeaconEstimator(ROOT/'array_geometry.json','coded-gap').estimate(
    np.zeros((SIZE,7),dtype='<i2'),{},0)
check('gap_uses_highband_delay',routed.get('method')=='coded_matched_filter_highband_delay',routed.get('method'))
config=json.loads((ROOT/'array_geometry.json').read_text(encoding='utf-8-sig'))
config.update(heading_offset_deg=0,mirror_view=False,heading_calibrated=False)
frequency=np.fft.rfftfreq(SIZE,1/RATE)
rng=np.random.default_rng(20261103)
angles=[]
with tempfile.TemporaryDirectory() as temporary:
    geometry=Path(temporary)/'geometry.json'
    geometry.write_text(json.dumps(config),encoding='utf-8')
    normalized=gap_spectrum/max(np.std(gap),1e-12)
    for angle in (45,90,270):
        receiver=BeaconEstimator(geometry,'coded-gap')
        errors=[]
        for i in range(6):
            channels=[]
            for ch in range(7):
                tau=0 if ch==6 else .04*math.cos(math.radians(angle-ch*60))/343
                shifted=np.fft.irfft(normalized*np.exp(2j*np.pi*frequency*tau)*120,SIZE)
                channels.append(shifted+rng.normal(0,20,SIZE))
            result,_=receiver.estimate(np.rint(np.column_stack(channels)).astype('<i2'),{},1+i*.22)
            if result.get('valid'):errors.append(abs((result['raw_angle_deg']-angle+180)%360-180))
        row={'angle':angle,'accepted_windows':len(errors),'max_error_deg':round(max(errors),3) if errors else None}
        angles.append(row)
        check(f'synthetic_direction_{angle}',len(errors)>=3 and max(errors)<15,row)
report['synthetic_angles']=angles
report['passed']=all(item['passed'] for item in report['checks'])
out=PROJECT/'stages/08-gap-beacon'
out.mkdir(parents=True,exist_ok=True)
(out/'model-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({'passed':report['passed'],'checks':len(report['checks'])}))
raise SystemExit(0 if report['passed'] else 1)
