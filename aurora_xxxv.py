import math,json,random,hashlib,statistics
SEED=35035
OBS=['resonance','coherence','entropy','mirror']
N=256; CYCLES=10; PHASES=9

def clamp(x,a=0,b=1): return max(a,min(b,x))
def rng_for(*parts):
    s='|'.join(map(str,(SEED,)+parts)).encode(); return random.Random(int(hashlib.sha256(s).hexdigest()[:16],16))

def observers(state):
    mean=sum(state)/9; var=sum((x-mean)**2 for x in state)/9
    ent=-sum(max(x,1e-9)*math.log(max(x,1e-9)) for x in state)/9
    mir=sum(abs(state[i]-state[-1-i]) for i in range(9))/9
    res=clamp(1-var*5)
    coh=clamp(1-sum(abs(state[i]-state[(i+1)%9]) for i in range(9))/9*2)
    ent=clamp(ent/math.log(9)); mir=clamp(1-mir*2)
    return {'resonance':res,'coherence':coh,'entropy':ent,'mirror':mir}

def run_pair(rep, arm):
    r=rng_for(rep,'pair')
    state=[r.random() for _ in range(9)]; rows=[]
    for c in range(CYCLES):
        for p in range(PHASES):
            k=.04+.10*r.random()
            nxt=[]
            for i,x in enumerate(state):
                left=state[(i-1)%9]; right=state[(i+1)%9]
                drive=.5*(left+right)-x
                phase=math.sin(2*math.pi*(p+1)/9+i*.37+c*.11)
                y=clamp(x+.16*drive+.035*phase+k*(r.random()-.5))
                nxt.append(y)
            state=nxt
            # intervention at cycle 4 phase 8; both arms get same timing
            if c==4 and p==8 and arm=='rebirth':
                state=[.15+.7*r.random() for _ in range(9)]
            obs=observers(state)
            rows.append({'rep':rep,'arm':arm,'cycle':c,'phase':p,'obs':obs})
    return rows

allrows=[]
for rep in range(N):
    allrows += run_pair(rep,'rebirth'); allrows += run_pair(rep,'control')

# Predefined recovery windows: cycles 5-7 following intervention; compare each observer and a strict 4-observer agreement score.
def agreement(obs):
    vals=list(obs.values()); return 1-(max(vals)-min(vals))

def mean_metric(rep,arm,cycles):
    rr=[x for x in allrows if x['rep']==rep and x['arm']==arm and x['cycle'] in cycles]
    return {o:statistics.mean(x['obs'][o] for x in rr) for o in OBS} | {'agreement':statistics.mean(agreement(x['obs']) for x in rr)}

paired=[]
for rep in range(N):
    a=mean_metric(rep,'rebirth',[5,6,7]); b=mean_metric(rep,'control',[5,6,7])
    paired.append({'rep':rep,'rebirth':a,'control':b,'delta':{k:a[k]-b[k] for k in a}})

# blinded-style permutation: shuffle arm labels at replicate level
observed=statistics.mean(x['delta']['agreement'] for x in paired)
r=rng_for('permutation'); null=[]
for _ in range(2000):
    vals=[]
    for x in paired:
        sign=1 if r.random()<.5 else -1
        vals.append(sign*x['delta']['agreement'])
    null.append(statistics.mean(vals))
p=sum(v>=observed for v in null)/len(null)

# recovery slope: distance from immediate post-intervention state to cycle-7 observer vector
recovery=[]
for rep in range(N):
    for arm in ['rebirth','control']:
        rr=[x for x in allrows if x['rep']==rep and x['arm']==arm]
        at=[x for x in rr if x['cycle']==4 and x['phase']==8][0]['obs']
        end=[x for x in rr if x['cycle']==7 and x['phase']==8][0]['obs']
        d=math.sqrt(sum((at[o]-end[o])**2 for o in OBS))
        recovery.append((arm,d))
reb=[d for a,d in recovery if a=='rebirth']; ctl=[d for a,d in recovery if a=='control']

report={
'experiment':'AXXXV-REBIRTH-CHAMBER-35035','replicates':N,'paired_trials':N,
'intervention':'cycle 4 phase 8; rebirth resets state, control continues without reset',
'recovery_cycles':[5,6,7],
'agreement_rebirth_mean':statistics.mean(x['rebirth']['agreement'] for x in paired),
'agreement_control_mean':statistics.mean(x['control']['agreement'] for x in paired),
'agreement_delta':observed,'permutation_p_one_sided':p,
'recovery_distance_rebirth_mean':statistics.mean(reb),'recovery_distance_control_mean':statistics.mean(ctl),
'observer_deltas':{o:statistics.mean(x['delta'][o] for x in paired) for o in OBS},
'verdict':'REBIRTH SIGNATURE DETECTED' if p<.01 and abs(observed)>.01 else 'NO ROBUST REBIRTH SIGNATURE',
'scientific_note':'Computational dynamical-system result only; not evidence for new physical phenomena.'}
with open('/mnt/data/aurora_xxxv_results.json','w') as f: json.dump(report,f,indent=2)
with open('/mnt/data/aurora_xxxv_report.txt','w') as f:
    f.write('AURORA XXXV — REBIRTH CHAMBER\n'+report['experiment']+'\n\n')
    for k,v in report.items():
        if k not in ('experiment','scientific_note'): f.write(f'{k}: {v}\n')
    f.write('\n'+report['scientific_note']+'\n')
print('AURORA XXXV — REBIRTH CHAMBER')
print(report['experiment']); print('Replicates:',N)
print('Agreement rebirth/control:',round(report['agreement_rebirth_mean'],5),round(report['agreement_control_mean'],5),'delta',round(observed,5))
print('Permutation p:',round(p,5))
print('Recovery distance:',round(statistics.mean(reb),5),round(statistics.mean(ctl),5))
print('Observer deltas:',{o:round(v,5) for o,v in report['observer_deltas'].items()})
print('Verdict:',report['verdict'])
