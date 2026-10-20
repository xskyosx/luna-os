import json, math, random
from pathlib import Path
from statistics import mean, pstdev

SEED=42042
KIND_OFFSETS={'perturbed': 101, 'rebirth': 202, 'mirror_reset': 303}
REPS=512
STEPS=24
INTERVENTION_STEP=6
N=9
KIND_OFFSETS = {"perturbed": 101, "rebirth": 202, "mirror_reset": 303}
OUT = Path(__file__).resolve().parent / "results"
OUT.mkdir(parents=True, exist_ok=True)

def init(r):
    return [r.uniform(-1,1) for _ in range(N)]

def evolve(x, r, k2=0.08):
    # Aurora's abstract 9-node coupled oscillator; deliberately not a physical model.
    y=[0.0]*N
    avg=sum(x)/N
    for i,v in enumerate(x):
        left=x[(i-1)%N]; right=x[(i+1)%N]; mirror=x[-1-i]
        phase=2*math.pi*(i+1)/N
        y[i]=(0.88*v + 0.055*(left+right) + 0.035*mirror
              + 0.025*math.sin(phase + avg) + k2*0.02*math.tanh(avg-v))
    return [math.tanh(v) for v in y]

def perturb(x, r, strength=0.35):
    y=x[:]
    j=r.randrange(N)
    y[j]+=strength*r.choice([-1,1])
    return y

def dist(a,b):
    return math.sqrt(sum((u-v)**2 for u,v in zip(a,b))/N)

def run_pair(r, kind):
    x=init(r)
    actual=x[:]
    counter=x[:]
    rows=[]
    for t in range(STEPS):
        if t==INTERVENTION_STEP:
            if kind=='perturbed': actual=perturb(actual,r)
            elif kind=='rebirth': actual=init(r)
            elif kind=='mirror_reset': actual=list(reversed(actual))
        # counterfactual never receives intervention
        actual=evolve(actual,r)
        counter=evolve(counter,r)
        d=dist(actual,counter)
        rows.append(d)
    return rows

kinds=['perturbed','rebirth','mirror_reset']
all_curves={k:[] for k in kinds}
for rep in range(REPS):
    for kind in kinds:
        r=random.Random(SEED + rep*10007 + KIND_OFFSETS[kind])
        all_curves[kind].append(run_pair(r,kind))

summaries={}
for kind,curves in all_curves.items():
    final=[c[-1] for c in curves]
    peak=[max(c[INTERVENTION_STEP:]) for c in curves]
    # time to fall below 10% of peak after intervention
    half=[]
    for c,p in zip(curves,peak):
        target=0.1*p
        hit=next((i-INTERVENTION_STEP for i,v in enumerate(c[INTERVENTION_STEP:],start=INTERVENTION_STEP) if v<=target), None)
        if hit is not None: half.append(hit)
    summaries[kind]={
        'final_divergence':mean(final),
        'final_sd':pstdev(final),
        'peak_divergence':mean(peak),
        'time_to_10pct_median': sorted(half)[len(half)//2] if half else None,
        'reconverged_rate': mean(v<0.01 for v in final),
    }

# Compare intervention kinds at each time using the same summary statistic.
time_means={k:[mean(c[t] for c in curves) for t in range(STEPS)] for k,curves in all_curves.items()}
# A simple path-dependence index: area under divergence curve normalized by peak.
path_index={}
for k,curves in all_curves.items():
    vals=[]
    for c in curves:
        peak=max(c[INTERVENTION_STEP:]) or 1e-12
        vals.append(sum(c[INTERVENTION_STEP:])/(len(c[INTERVENTION_STEP:])*peak))
    path_index[k]=mean(vals)

out={
    'experiment':'AXLII-COUNTERFACTUAL-TWIN',
    'seed':SEED,'replicates':REPS,'steps':STEPS,'intervention_step':INTERVENTION_STEP,
    'summaries':summaries,'mean_divergence_curves':time_means,'path_dependence_index':path_index,
    'node9':{
        'finding':'Interventions create separable counterfactual trajectories, with recovery/reconvergence differing by intervention type.',
        'warning':'This is a property of the simulation rules, not evidence about physical particles or quantum systems.'
    }
}
(OUT / 'aurora_xlii_results.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
report=['Aurora XLII — Counterfactual Twin','',f'Replicates: {REPS}',f'Steps: {STEPS}',f'Intervention step: {INTERVENTION_STEP}','']
for k,v in summaries.items():
    report.append(f'{k}: final={v["final_divergence"]:.6f}, peak={v["peak_divergence"]:.6f}, reconverged={v["reconverged_rate"]:.3f}, path_index={path_index[k]:.3f}')
report += ['', 'Node 9:', out['node9']['finding'], out['node9']['warning']]
(OUT / 'aurora_xlii_report.txt').write_text('\n'.join(report), encoding='utf-8')
print('\n'.join(report))
