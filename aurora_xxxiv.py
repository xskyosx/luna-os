import math, json, random, hashlib
from collections import defaultdict

SEED=34034
WORLDS=['Seed','Control','Rebirth','Wild','Null']
OBS=['resonance','coherence','entropy','mirror']
PHASES=9
CYCLES=8
RUNS=12


def clamp(x,a=0,b=1): return max(a,min(b,x))
def rng_for(*parts):
    s='|'.join(map(str,(SEED,)+parts)).encode(); return random.Random(int(hashlib.sha256(s).hexdigest()[:16],16))

def trajectory(run, world):
    r=rng_for(run,world)
    state=[r.random() for _ in range(9)]
    prev=None; rows=[]
    for c in range(CYCLES):
        for p in range(PHASES):
            t=c*PHASES+p
            k=0.04+0.10*(r.random())
            if world=='Seed': k*=0.95
            elif world=='Wild': k*=1.25
            elif world=='Null': k*=0.75
            # ring/coupling + elliptical-like nonlinear oscillator abstraction
            nxt=[]
            for i,x in enumerate(state):
                left=state[(i-1)%9]; right=state[(i+1)%9]
                drive=0.5*(left+right)-x
                phase=math.sin(2*math.pi*(p+1)/9 + i*0.37 + c*0.11)
                y=clamp(x + 0.16*drive + 0.035*phase + k*(r.random()-0.5))
                if world=='Rebirth' and p==8 and c>0: y=0.15+0.7*r.random()
                nxt.append(y)
            state=nxt
            mean=sum(state)/9
            var=sum((x-mean)**2 for x in state)/9
            entropy=-sum((max(x,1e-9))*math.log(max(x,1e-9)) for x in state)/9
            mirror=sum(abs(state[i]-state[-1-i]) for i in range(9))/9
            resonance=clamp(1-var*5)
            coherence=clamp(1-sum(abs(state[i]-state[(i+1)%9]) for i in range(9))/9*2)
            entropy=clamp(entropy/math.log(9))
            mirror=clamp(1-mirror*2)
            obs={'resonance':resonance,'coherence':coherence,'entropy':entropy,'mirror':mirror}
            # contradiction at this point: one high and one low observer
            vals=list(obs.values()); contradiction=(max(vals)>=0.75 and min(vals)<=0.25)
            disagreement=max(vals)-min(vals)
            if prev is None:
                transition='start'
            elif contradiction and not prev['contradiction']: transition='entry'
            elif contradiction and prev['contradiction']: transition='persist'
            elif (not contradiction) and prev['contradiction']: transition='exit'
            else: transition='none'
            rows.append({'run':run,'world':world,'cycle':c,'phase':p,'t':t,'obs':obs,'contradiction':contradiction,'disagreement':disagreement,'transition':transition})
            prev=rows[-1]
    return rows

rows=[]
for run in range(RUNS):
    for w in WORLDS: rows.extend(trajectory(run,w))

# Transition lens: compare observer values immediately before, at, after contradiction entries.
entries=[]; exits=[]; windows=[]
by=defaultdict(list)
for row in rows: by[(row['run'],row['world'])].append(row)
for key, seq in by.items():
    for i,row in enumerate(seq):
        if row['transition']=='entry' and i>0 and i+1<len(seq):
            entries.append(row)
            windows.append({'run':row['run'],'world':row['world'],'before':seq[i-1]['obs'],'at':row['obs'],'after':seq[i+1]['obs'],'before_disagreement':seq[i-1]['disagreement'],'at_disagreement':row['disagreement'],'after_disagreement':seq[i+1]['disagreement']})
        if row['transition']=='exit': exits.append(row)

summary={}
for w in WORLDS:
    rr=[x for x in rows if x['world']==w]
    ww=[x for x in windows if x['world']==w]
    entry_rate=len(ww)/len(rr)
    avg_delta=(sum(x['after_disagreement']-x['before_disagreement'] for x in ww)/len(ww)) if ww else 0
    avg_peak=(sum(x['at_disagreement']-0.5*(x['before_disagreement']+x['after_disagreement']) for x in ww)/len(ww)) if ww else 0
    summary[w]={'observations':len(rr),'entry_events':len(ww),'entry_rate':entry_rate,'mean_disagreement_delta_before_to_after':avg_delta,'mean_contradiction_peak':avg_peak}

# Directed observer transitions: which observer changes most from before -> at -> after at entries?
deltas=defaultdict(list)
for x in windows:
    for o in OBS:
        deltas[o].append(x['at'][o]-x['before'][o])
observer_shift={o:{'mean_before_to_entry':sum(v)/len(v),'mean_abs_shift':sum(abs(z) for z in v)/len(v)} for o,v in deltas.items()}

# Matched null: shuffle contradiction labels within each run/world while preserving event rate.
null_counts=[]
r=rng_for('null')
for b in range(500):
    count=0
    for key,seq in by.items():
        n=sum(x['contradiction'] for x in seq)
        flags=[True]*n+[False]*(len(seq)-n); r.shuffle(flags)
        for i,f in enumerate(flags):
            if f and i>0 and i+1<len(seq) and not flags[i-1]: count+=1
    null_counts.append(count)
obs_entries=len(windows)
null_mean=sum(null_counts)/len(null_counts)
null_sd=(sum((x-null_mean)**2 for x in null_counts)/len(null_counts))**0.5
z=(obs_entries-null_mean)/null_sd if null_sd else 0

report={
 'experiment':'AXXXIV-TRANSITION-LENS-34034','observations':len(rows),'windows':len(windows),
 'summary':summary,'observer_entry_shifts':observer_shift,
 'null_entry_events_mean':null_mean,'null_entry_events_sd':null_sd,'z_vs_null':z,
 'verdict':'TRANSITION SIGNATURE MAPPED' if abs(z)>=2 else 'NO ROBUST TRANSITION SIGNATURE',
 'scientific_note':'This is a computational dynamical-system result, not evidence for new physical phenomena.'}

with open('/mnt/data/aurora_xxxiv_results.json','w') as f: json.dump(report,f,indent=2)
with open('/mnt/data/aurora_xxxiv_report.txt','w') as f:
    f.write('AURORA XXXIV — TRANSITION LENS\n')
    f.write(report['experiment']+'\n\n')
    f.write(f"Observations: {len(rows)} | contradiction-entry windows: {len(windows)}\n\n")
    for w,s in summary.items(): f.write(f"{w:8s} entries={s['entry_events']:3d} rate={s['entry_rate']:.4f} delta={s['mean_disagreement_delta_before_to_after']:+.4f} peak={s['mean_contradiction_peak']:+.4f}\n")
    f.write('\nObserver mean shift at contradiction entry:\n')
    for o,v in observer_shift.items(): f.write(f"  {o:11s} shift={v['mean_before_to_entry']:+.5f} abs={v['mean_abs_shift']:.5f}\n")
    f.write(f"\nNull entry events: {null_mean:.2f} ± {null_sd:.2f}; z={z:.3f}\n")
    f.write('Verdict: '+report['verdict']+'\n')
    f.write(report['scientific_note']+'\n')
print('AURORA XXXIV — TRANSITION LENS')
print(report['experiment'])
print('Observations:',len(rows),'entry windows:',len(windows))
for w,s in summary.items(): print(f"{w:8s} entries={s['entry_events']:3d} rate={s['entry_rate']:.4f} before→after={s['mean_disagreement_delta_before_to_after']:+.4f} peak={s['mean_contradiction_peak']:+.4f}")
print('Observer shifts:', {k:round(v['mean_before_to_entry'],5) for k,v in observer_shift.items()})
print(f'Null: {null_mean:.2f} ± {null_sd:.2f}; z={z:.3f}')
print('Verdict:',report['verdict'])
