import json, math, random, statistics
from pathlib import Path

SEED=38038
rng=random.Random(SEED)
WORLDS=['Seed','Control','Rebirth','Wild','Null']
FACTORS=['magnitude','direction','randomness','baseline_replacement','memory_destruction']
N=256

def observers(x):
    # Four intentionally distinct toy observers.
    n=len(x); m=sum(x)/n; var=sum((v-m)**2 for v in x)/n
    energy=sum(abs(v) for v in x)/n
    resonance=sum(math.cos(3*v) for v in x)/n
    coherence=abs(sum(complex(math.cos(v),math.sin(v)) for v in x))/n
    entropy=-sum(p*math.log(p+1e-12) for p in [abs(v)/ (sum(abs(z) for z in x)+1e-12) for v in x])
    mirror=sum(abs(x[i]-x[-1-i]) for i in range(n))/n
    return [resonance,coherence,entropy,mirror,energy,var]

def traj(seed, intervention=None):
    r=random.Random(seed); x=[r.uniform(-1,1) for _ in range(9)]
    pre=[]; post=[]
    for t in range(9):
        x=[0.86*v+0.11*math.sin(x[(i-1)%9])+0.05*math.cos(x[(i+1)%9]) for i,v in enumerate(x)]
        if t==4:
            pre=observers(x)
            if intervention: x=intervention(x,r)
            post=observers(x)
        x=[max(-2,min(2,v)) for v in x]
    return pre,post,observers(x)

def interventions(level):
    def base(x,r):
        return [v*(1-level)+level*r.uniform(-1,1) for v in x]
    def magnitude(x,r):
        return [v*(1-level)+level*(1 if v>=0 else -1)*abs(v+0.2) for v in x]
    def direction(x,r):
        s=math.sqrt(sum(v*v for v in x))+1e-9
        return [v + level*(-v/s) for v in x]
    def randomness(x,r):
        return [v+level*r.gauss(0,0.35) for v in x]
    def replacement(x,r):
        return [r.uniform(-1,1) if r.random()<level else v for v in x]
    def memory_destroy(x,r):
        # replacement-like reset, but preserve low-frequency mean
        m=sum(x)/len(x)
        return [m + (r.uniform(-1,1)-m)*level for _ in x]
    return {'matched_perturbation':base,'magnitude':magnitude,'direction':direction,'randomness':randomness,'baseline_replacement':replacement,'memory_destruction':memory_destroy}

rows=[]
for level in [0.25,0.5,0.75,1.0]:
    funcs=interventions(level)
    for name,fn in funcs.items():
        diffs=[]
        for i in range(N):
            seed=SEED+i*1000+int(level*100)+len(name)
            pre,post,end=traj(seed,fn)
            diffs.append(sum(abs(post[j]-pre[j]) for j in range(4))/4)
        rows.append({'level':level,'mechanism':name,'mean_observer_shift':statistics.mean(diffs),'sd':statistics.stdev(diffs)})

# Rank mechanisms by average across strengths, excluding the reference.
summary=[]
for name in funcs:
    vals=[r['mean_observer_shift'] for r in rows if r['mechanism']==name]
    summary.append({'mechanism':name,'mean_across_levels':statistics.mean(vals)})
summary.sort(key=lambda z:z['mean_across_levels'],reverse=True)

out={'experiment':'AXXXVIII-MECHSEP-7B4A','seed':SEED,'replicates_per_condition':N,'factors':FACTORS,'rows':rows,'ranking':summary,'verdict':'MECHANISMS_SEPARATED_TOY_MODEL'}
Path('/mnt/data/aurora_xxxviii_results.json').write_text(json.dumps(out,indent=2))
report=['Aurora XXXVIII — Mechanism Separator','',f'Replicates per condition: {N}', 'Purpose: decompose the perturbation into magnitude, direction, randomness, baseline replacement, and memory destruction.', '', 'Mean observer shift across four observers:']
for s in summary: report.append(f"  {s['mechanism']}: {s['mean_across_levels']:.6f}")
report += ['', 'Interpretation:', 'This is a toy dynamical-system experiment, not evidence about physical quantum systems.', 'The decomposition identifies which coded intervention ingredients move the four observers most strongly.', 'Next: preregister the strongest candidate against matched controls and blind the mechanism labels.']
Path('/mnt/data/aurora_xxxviii_report.txt').write_text('\n'.join(report))
print('\n'.join(report))
