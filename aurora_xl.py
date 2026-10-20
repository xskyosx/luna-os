import math, json, hashlib, random
from statistics import mean, pstdev
from pathlib import Path

OUT = Path(__file__).resolve().parent / "results"
OUT.mkdir(parents=True, exist_ok=True)
SEED=41039
REPS=384
STEPS=90
PHASES=9


def rng_for(*parts):
    h=hashlib.sha256('|'.join(map(str,parts)).encode()).hexdigest()
    return random.Random(int(h[:16],16))

def sim(seed, condition, perturb=0.45):
    r=rng_for(SEED, seed, condition)
    # 9-node state: ellipse-like positions/velocities, ring coupling, memory trace
    x=[r.uniform(-1,1) for _ in range(9)]
    v=[r.uniform(-.2,.2) for _ in range(9)]
    memory=[0.0]*9
    baseline=[math.sin(2*math.pi*i/9) for i in range(9)]
    if condition=='surrogate': baseline=[math.cos(2*math.pi*i/9) for i in range(9)]
    if condition=='randomized': baseline=[r.uniform(-1,1) for _ in range(9)]
    rows=[]
    intervention=54
    for t in range(STEPS):
        if t==intervention:
            if condition=='original': x=[(1-perturb)*a+perturb*b for a,b in zip(x,baseline)]
            elif condition=='surrogate': x=[(1-perturb)*a+perturb*b for a,b in zip(x,baseline)]
            else: x=[(1-perturb)*a+perturb*b for a,b in zip(x,baseline)]
            v=[z*(1-0.35*perturb) for z in v]
        phase=t%PHASES
        k=.06 + .025*math.sin(2*math.pi*phase/9)
        coupling=.08
        newv=[]
        for i in range(9):
            left=x[(i-1)%9]; right=x[(i+1)%9]
            force=-.11*x[i] - .025*v[i] + coupling*(left+right-2*x[i])
            force += k*math.sin(2*math.pi*i/9 + phase*math.pi/9)
            v[i]+=force
            newv.append(v[i])
        v=newv
        x=[x[i]+v[i] for i in range(9)]
        # K2 governor bounded
        energy=mean(a*a+b*b for a,b in zip(x,v))
        target=.30
        kk=max(-1, min(1, .08*(target-energy)))
        x=[a*(1+kk) for a in x]
        memory=[.92*m+.08*a for m,a in zip(memory,x)]
        # observers normalized locally to [0,1]
        energy_o=1/(1+energy)
        entropy=sum(abs(x[i]-x[(i+1)%9]) for i in range(9))/9
        entropy_o=entropy/(1+entropy)
        resonance=abs(sum(x[i]*math.cos(2*math.pi*i/9)+v[i]*math.sin(2*math.pi*i/9) for i in range(9)))/9
        resonance_o=resonance/(1+resonance)
        coherence=1/(1+pstdev(x))
        mirror=1/(1+mean(abs(x[i]-x[8-i]) for i in range(9)))
        novelty=mean(abs(x[i]-memory[i]) for i in range(9)); novelty=novelty/(1+novelty)
        rows.append(dict(t=t, x=x[:], resonance=resonance_o, coherence=coherence, entropy=entropy_o, mirror=mirror, energy=energy_o, novelty=novelty))
    return rows

def rank(vals):
    order=sorted(range(len(vals)), key=lambda i: vals[i]); out=[0]*len(vals)
    if len(vals)==1:return [0.5]
    for j,i in enumerate(order): out[i]=j/(len(vals)-1)
    return out

def analyze(rows):
    names=['resonance','coherence','entropy','mirror']
    rr={n:rank([row[n] for row in rows]) for n in names}
    # intersection of high observers; disagreement = std of four ranks
    inter=[]; disagree=[]
    for i,row in enumerate(rows):
        vals=[rr[n][i] for n in names]
        inter.append(min(vals))
        disagree.append(pstdev(vals))
    # transition lens: event after intervention when intersection changes sharply
    post=[i for i,row in enumerate(rows) if row['t']>=54]
    baseline=mean(inter[:54]); postmean=mean(inter[54:])
    maxjump=max((abs(inter[i]-inter[i-1]), i) for i in range(1,len(inter)))
    return {'intersection_mean':mean(inter),'post_intersection':postmean,'pre_intersection':baseline,
            'intersection_delta':postmean-baseline,'mean_disagreement':mean(disagree),
            'max_intersection_jump':maxjump[0], 'max_jump_t':rows[maxjump[1]]['t']}

records=[]
for rep in range(REPS):
    # common latent initial state by using same seed for each condition
    seed=100000+rep
    for cond in ['original','surrogate','randomized']:
        rows=sim(seed,cond)
        a=analyze(rows)
        # counterfactual shadow: compare original trajectory to alternative condition at same times
        records.append({'rep':rep,'condition':cond,**a})

summary={}
for c in ['original','surrogate','randomized']:
    vals=[r for r in records if r['condition']==c]
    summary[c]={k:mean(v[k] for v in vals) for k in ['intersection_mean','post_intersection','pre_intersection','intersection_delta','mean_disagreement','max_intersection_jump']}

# paired contrasts and stranger detector
contrasts={}
for metric in ['intersection_delta','post_intersection','max_intersection_jump']:
    by={c:{r['rep']:r[metric] for r in records if r['condition']==c} for c in ['original','surrogate','randomized']}
    for c in ['surrogate','randomized']:
        d=[by['original'][i]-by[c][i] for i in range(REPS)]
        contrasts[f'original_minus_{c}_{metric}']={'mean':mean(d),'sd':pstdev(d),'positive_rate':sum(z>0 for z in d)/REPS}

# stranger detector = observations where original beats both alternatives by > 0.15 in intersection_delta
strangers=[]
for rep in range(REPS):
    vals={r['condition']:r for r in records if r['rep']==rep}
    score=vals['original']['intersection_delta']-max(vals['surrogate']['intersection_delta'],vals['randomized']['intersection_delta'])
    if score>.15:
        strangers.append({'rep':rep,'score':score})

result={'experiment':'AXL-BASELINE-IDENTITY','seed':SEED,'replicates':REPS,'steps':STEPS,'conditions':summary,'paired_contrasts':contrasts,'stranger_events':strangers[:20],'stranger_count':len(strangers),
        'node9':{'agreement':'compare all three baselines rather than collapse to one score','question':'Does baseline identity produce a reproducible transition signature beyond matched perturbation?','verdict':'BASELINE IDENTITY SIGNAL NOT YET ESTABLISHED' if abs(contrasts['original_minus_surrogate_intersection_delta']['mean'])<.02 else 'CANDIDATE BASELINE SIGNAL; REPLICATE'}}

(OUT/'aurora_xl_results.json').write_text(json.dumps(result,indent=2))
report='Aurora XL — Baseline Identity Chamber\n\n'
report+=f'Replicates: {REPS}\n'
for c,s in summary.items(): report+=f"{c}: post_intersection={s['post_intersection']:.6f}, delta={s['intersection_delta']:.6f}, disagreement={s['mean_disagreement']:.6f}\n"
report+='\nPaired contrasts (original minus alternative):\n'
for k,v in contrasts.items(): report+=f"{k}: mean={v['mean']:.6f}, sd={v['sd']:.6f}, positive_rate={v['positive_rate']:.3f}\n"
report+=f'\nStranger events (>0.15 advantage): {len(strangers)}\n\nNode 9: '+result['node9']['verdict']+'\n\nThis is a toy dynamical-system test; it does not establish claims about physical quantum systems.\n'
(OUT/'aurora_xl_report.txt').write_text(report)
print(report)
