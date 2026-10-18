import json, math, random
from pathlib import Path
from statistics import mean, pstdev

SEED=43043; REPS=128; STEPS=36; INTERVENTION_STEP=6; N=9
GRID=[(c,k,m,b) for c in (0.02,0.08,0.14) for k in (0.03,0.08,0.13) for m in (0.25,0.60,0.95) for b in (0.25,0.60,0.95)]

def init(r): return [r.uniform(-1,1) for _ in range(N)]
def evolve(x, coupling, k2, memory, r):
    y=[]; avg=sum(x)/N
    for i,v in enumerate(x):
        left=x[(i-1)%N]; right=x[(i+1)%N]; mirror=x[-1-i]
        phase=2*math.pi*(i+1)/N
        y.append((0.88*v + coupling*(left+right) + 0.035*mirror +
                  0.025*math.sin(phase+avg) + k2*0.02*math.tanh(avg-v)))
    # memory is retained through a small nonlinear trace
    return [math.tanh(memory*v + (1-memory)*math.tanh(v)) for v in y]

def rebirth(x,r,intensity):
    fresh=init(r); return [(1-intensity)*a + intensity*b for a,b in zip(x,fresh)]
def dist(a,b): return math.sqrt(sum((u-v)**2 for u,v in zip(a,b))/N)

def run_pair(r,c,k,m,b):
    a=init(r); cf=a[:]; curve=[]
    for t in range(STEPS):
        if t==INTERVENTION_STEP: a=rebirth(a,r,b)
        a=evolve(a,c,k,m,r); cf=evolve(cf,c,k,m,r); curve.append(dist(a,cf))
    return curve

results=[]
for gi,(c,k,m,b) in enumerate(GRID):
    vals=[]
    for rep in range(REPS):
        r=random.Random(SEED+gi*1000003+rep*9176)
        curve=run_pair(r,c,k,m,b)
        peak=max(curve[INTERVENTION_STEP:]); final=curve[-1]
        auc=sum(curve[INTERVENTION_STEP:])
        recon=final<0.01
        vals.append((peak,final,auc,recon))
    results.append({'coupling':c,'k2':k,'memory':m,'rebirth_intensity':b,
                    'peak':mean(v[0] for v in vals),'final':mean(v[1] for v in vals),
                    'auc':mean(v[2] for v in vals),'recon_rate':mean(v[3] for v in vals)})

# Boundary score: high recovery + low final divergence = reconvergence regime.
# classify by reconvergence rate; transition band 0.25..0.75.
for row in results:
    row['regime']='reconvergent' if row['recon_rate']>=0.75 else ('mixed' if row['recon_rate']>=0.25 else 'persistent')

best_recon=max(results,key=lambda x:x['recon_rate']); strongest=max(results,key=lambda x:x['final']); mixed=[r for r in results if r['regime']=='mixed']
# Marginal means by each parameter
marg={}
for idx,name in enumerate(['coupling','k2','memory','rebirth_intensity']):
    levels=sorted({r[name] for r in results}); marg[name]={str(v):mean(r['recon_rate'] for r in results if r[name]==v) for v in levels}

out={'experiment':'AXLIII-CONVERGENCE-HUNT','seed':SEED,'replicates_per_cell':REPS,'grid_cells':len(GRID),
     'steps':STEPS,'intervention_step':INTERVENTION_STEP,'results':results,'mixed_cells':mixed,
     'marginal_reconvergence':marg,'best_reconvergence':best_recon,'strongest_persistent':strongest,
     'verdict':'BOUNDARY MAPPED' if mixed else 'NO MIXED BOUNDARY FOUND'}
Path('/mnt/data/aurora_xliii_results.json').write_text(json.dumps(out,indent=2))
report=f'''Aurora XLIII — Convergence Hunt\nExperiment: AXLIII-CONVERGENCE-HUNT\n\nDesign: {len(GRID)} parameter cells × {REPS} replicates = {len(GRID)*REPS} paired trajectories.\nParameters: coupling, K2 strength, memory retention, rebirth intensity.\nIntervention: rebirth at step {INTERVENTION_STEP}; divergence followed for {STEPS} steps.\n\nVerdict: {out['verdict']}\nBest reconvergence cell: {best_recon}\nStrongest persistent cell: {strongest}\nMixed cells: {len(mixed)}\n\nInterpretation: This is a property of Aurora's abstract dynamical system, not evidence about physical quantum/subatomic behavior. A mixed cell is treated as a transition region, not a physical phase transition.\n'''
Path('/mnt/data/aurora_xliii_report.txt').write_text(report)
print(report)
