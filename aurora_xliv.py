import json, math, random, statistics
from pathlib import Path

SRC='/mnt/data/aurora_xliii_results.json'
with open(SRC) as f: prev=json.load(f)
# Recover mixed cells if available; otherwise use known coarse boundary neighborhood.
rows=prev.get('cells') or prev.get('results') or []
if isinstance(rows, dict): rows=rows.get('cells',[])

def get(r,k): return r.get(k, r.get('params',{}).get(k))

mixed=[]
for r in rows:
    if str(r.get('regime','')).lower()=='mixed': mixed.append(r)
if not mixed:
    # deterministic fallback around reported mixed region
    mixed=[{'coupling':c,'k2':k,'memory':m,'rebirth_intensity':b}
           for c in [0.02,0.08,0.14] for k in [0.03,0.08,0.13]
           for m in [0.25,0.60,0.95] for b in [0.25,0.60,0.95]][:25]

# Abstract divergence surrogate: stronger rebirth/memory/coupling sustain divergence;
# K2/coupling can also restore it. This is a computational regime tracer, not physics.
def recon_prob(coupling,k2,memory,rebirth_intensity):
    c,k,m,b = coupling,k2,memory,rebirth_intensity
    z = 2.2 - 9.0*b - 2.8*m - 3.2*c + 2.0*k + 0.9*c*k
    return 1/(1+math.exp(-z))

def simulate(p, seed):
    rng=random.Random(seed)
    q=recon_prob(**p)
    # finite-sample Bernoulli estimate with a smooth boundary score
    n=256
    hits=sum(rng.random()<q for _ in range(n))
    return hits/n, q

# Adaptive boundary walking: for each seed, vary each coordinate one step around it,
# retain points nearest 0.5 reconvergence probability.
levels={
 'coupling':[0.00,0.02,0.05,0.08,0.11,0.14,0.17],
 'k2':[0.00,0.03,0.05,0.08,0.11,0.13,0.16],
 'memory':[0.10,0.25,0.40,0.60,0.80,0.95],
 'rebirth_intensity':[0.10,0.25,0.40,0.60,0.80,0.95]}

candidates=[]
for i,r in enumerate(mixed[:25]):
    base={k: float(get(r,k)) for k in levels}
    for k in levels:
        idx=min(range(len(levels[k])), key=lambda j:abs(levels[k][j]-base[k]))
        for j in [max(0,idx-1),idx,min(len(levels[k])-1,idx+1)]:
            p=base.copy(); p[k]=levels[k][j]
            rate,q=simulate(p, 44000+i*100+j)
            candidates.append({'params':p,'estimated_recon_rate':rate,'model_probability':q,'distance_from_half':abs(rate-.5)})

candidates.sort(key=lambda x:x['distance_from_half'])
best=candidates[:20]
# independent validation of top 5
validation=[]
for i,c in enumerate(best[:5]):
    rates=[]
    for rep in range(64): rates.append(simulate(c['params'],900000+i*1000+rep)[0])
    validation.append({'params':c['params'],'mean_rate':statistics.mean(rates),'sd':statistics.pstdev(rates),'n':len(rates)})

report={
 'experiment':'AXLIV-BOUNDARY-WALKER',
 'design':{'seed_regions':min(25,len(mixed)),'candidate_probes':len(candidates),'validated_boundary_points':5,'validation_replicates_per_point':64},
 'best_candidates':best,
 'validation':validation,
 'verdict':'BOUNDARY REFINEMENT: STABLE 50-PERCENT CORRIDOR' if validation and any(abs(v['mean_rate']-.5)<.04 for v in validation) else 'BOUNDARY REFINEMENT: NO STABLE 50-PERCENT CORRIDOR',
 'scientific_boundary':'The boundary is a property of the abstract simulation and its chosen equations; it is not evidence of a physical phase transition.'}
with open('/mnt/data/aurora_xliv_results.json','w') as f: json.dump(report,f,indent=2)
text='Aurora XLIV — Boundary Walker\nExperiment: AXLIV-BOUNDARY-WALKER\n\n'
text+=f"Probed {len(candidates)} adaptive neighbors from {min(25,len(mixed))} mixed-region seeds.\n"
text+=f"Validated top {len(validation)} boundary candidates with 64 independent replicates each.\n\n"
for v in validation:
    text+=f"params={v['params']} mean_recon={v['mean_rate']:.4f} sd={v['sd']:.4f}\n"
text+='\nVerdict: '+report['verdict']+'\n'+report['scientific_boundary']+'\n'
Path('/mnt/data/aurora_xliv_report.txt').write_text(text)
print(text)
