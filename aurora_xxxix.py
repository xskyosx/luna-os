import json, math, random, statistics
from pathlib import Path

SEED=39039
N=512
CONDS=['memory_preserved','memory_erased','memory_replaced']

def obs(x, hist):
    r=[math.sin(v) for v in x]
    coherence=abs(sum(r))/len(r)
    resonance=sum(math.cos(v*3) for v in x)/len(x)
    entropy=-sum((abs(math.sin(v))+1e-9)*math.log(abs(math.sin(v))+1e-9) for v in x)/len(x)
    mirror=sum(abs(math.sin(v)-math.sin(-v)) for v in x)/len(x)
    # history-sensitive recurrence
    recurrence=math.exp(-abs(statistics.mean(x)-statistics.mean(hist))) if hist else 0.0
    return [resonance,coherence,entropy,mirror], recurrence

def trial(rng, cond):
    x=[rng.uniform(-math.pi,math.pi) for _ in range(9)]
    hist=list(x)
    for t in range(12):
        prev=x[:]
        x=[0.84*v + 0.16*math.sin(prev[(i-1)%9]+prev[(i+1)%9]) + rng.gauss(0,0.08) for i,v in enumerate(prev)]
        hist.append(statistics.mean(x))
    baseline=x[:]
    if cond=='memory_preserved':
        x=[v + 0.35*math.sin(v*2) for v in baseline]
        hist2=hist[:]
    elif cond=='memory_erased':
        x=[v + 0.35*math.sin(v*2) for v in baseline]
        hist2=[]
    else:
        x=[v + 0.35*math.sin(v*2) for v in baseline]
        repl=statistics.mean(baseline)
        hist2=[repl+rng.gauss(0,0.03) for _ in hist]
    vals=[]
    for k in range(4):
        x=[0.88*v+0.12*math.sin(v*3)+rng.gauss(0,0.04) for v in x]
        o,rec=obs(x,hist2)
        vals.append(sum(o)/4)
    return statistics.mean(vals), vals[-1]

rng=random.Random(SEED)
raw={c:[trial(rng,c) for _ in range(N)] for c in CONDS}
means={c:statistics.mean(v[0] for v in a) for c,a in raw.items()}
# Pairwise differences on matched replicate index
pairs={}
for a,b in [('memory_erased','memory_preserved'),('memory_replaced','memory_preserved'),('memory_erased','memory_replaced')]:
    d=[raw[a][i][0]-raw[b][i][0] for i in range(N)]
    pairs[f'{a}_minus_{b}']={'mean':statistics.mean(d),'sd':statistics.stdev(d),'positive_rate':sum(z>0 for z in d)/N}
# simple permutation p for erased vs preserved
observed=pairs['memory_erased_minus_memory_preserved']['mean']
vals=[]
for _ in range(4000):
    s=0
    for i in range(N):
        d=raw['memory_erased'][i][0]-raw['memory_preserved'][i][0]
        s += d if rng.random()<.5 else -d
    vals.append(s/N)
p=(sum(v>=observed for v in vals)+1)/(len(vals)+1)
result={'experiment':'AXXXIX-MEMORYTRIAL','seed':SEED,'replicates_per_condition':N,'means':means,'pairwise':pairs,'permutation_p_erased_vs_preserved':p}
Path('/mnt/data/aurora_xxxix_results.json').write_text(json.dumps(result,indent=2))
report=f'''Aurora XXXIX — Memory Trial\n\nReplicates per condition: {N}\nConditions: memory preserved, memory erased, memory replaced\n\nMean observer-intersection proxy:\n'''+''.join(f'  {c}: {means[c]:.6f}\n' for c in CONDS)+f'''\nPaired contrasts:\n'''+''.join(f"  {k}: mean={v['mean']:.6f}, sd={v['sd']:.6f}, positive_rate={v['positive_rate']:.3f}\n" for k,v in pairs.items())+f'''\nPermutation p (erased - preserved): {p:.6f}\n\nInterpretation:\nThis is a toy dynamical-system test. It does not establish claims about physical quantum systems. The coded result tests whether history handling changes the observer proxy under matched perturbation.\n'''
Path('/mnt/data/aurora_xxxix_report.txt').write_text(report)
print(report)
