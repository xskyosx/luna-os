import json, math, random
from pathlib import Path
from statistics import mean, pstdev
SEED=41041; REPS=384

def base(r): return [r.gauss(0,1) for _ in range(9)]
def metrics(x):
 n=len(x); return [abs(sum(x[i]*x[(i+1)%n] for i in range(n)))/n, abs(sum(x))/n, -sum((abs(v)+1e-9)*math.log(abs(v)+1e-9) for v in x)/n, abs(sum(x[i]*x[-1-i] for i in range(n)))/n]
REF=[[] for _ in range(4)]
for k in range(4000):
 r=random.Random(900000+k)
 for i,v in enumerate(metrics(base(r))): REF[i].append(v)
for a in REF:a.sort()
def pct(v,a):
 lo,hi=0,len(a)
 while lo<hi:
  m=(lo+hi)//2
  if a[m]<=v:lo=m+1
  else:hi=m
 return (lo-.5)/len(a)
def score(x): return mean(pct(v,REF[i]) for i,v in enumerate(metrics(x)))
def apply(x,op,r):
 if op=='state': return [.5*v+.5*r.gauss(0,1) for v in x]
 if op=='perturbation': y=x[:]; y[r.randrange(9)]+=1.; return y
 if op=='observer': return [math.tanh(v) for v in x]
 if op=='transition': return [.75*v for v in x]
 if op=='recovery': return [.95*v for v in x]
ops=['state','perturbation','observer','transition','recovery']; rows=[]
for rep in range(REPS):
 r=random.Random(SEED+rep*1009); x=base(r)
 for op in ops:
  b=score(x); y=apply(x,op,r); a=score(y)
  rows.append({'rep':rep,'op':op,'before':b,'after':a,'delta':a-b,'energy_change':mean(v*v for v in y)-mean(v*v for v in x)}); x=y
summary={}
for op in ops:
 q=[z for z in rows if z['op']==op]; ds=[z['delta'] for z in q]
 summary[op]={'mean_delta':mean(ds),'sd_delta':pstdev(ds),'positive_rate':mean(d>0 for d in ds),'mean_energy_change':mean(z['energy_change'] for z in q)}
# independent single-link reversals from same baseline
rev=[]
for rep in range(REPS):
 r=random.Random(SEED+rep*1009+7); x=base(r); b=score(x)
 for op in ['perturbation','transition','recovery']:
  y=apply(x,op,r); f=score(y)-b
  if op=='perturbation': z=x[:]; z[0]-=1
  elif op=='transition': z=[v/.75 for v in x]
  else: z=[v/.95 for v in x]
  rev.append((op,f,score(z)-b))
reversal={}
for op in ['perturbation','transition','recovery']:
 q=[f-r for o,f,r in rev if o==op]; reversal[op]={'mean_forward_minus_reverse':mean(q),'positive_rate':mean(v>0 for v in q)}
out={'experiment':'AXLI-CAUSAL-LADDER','seed':SEED,'replicates':REPS,'summary':summary,'reversal':reversal,'node9':'CAUSAL SEPARATION MAPPED; NO PHYSICAL INTERPRETATION'}
Path('/mnt/data/aurora_xli_results.json').write_text(json.dumps(out,indent=2)); Path('/mnt/data/aurora_xli_report.txt').write_text('Aurora XLI — Causal Ladder\n\n'+json.dumps(out,indent=2))
print('Aurora XLI — Causal Ladder')
for op,v in summary.items():print(f"{op}: delta={v['mean_delta']:.6f}, positive={v['positive_rate']:.3f}, energy_change={v['mean_energy_change']:.6f}")
print('Reversal tests:')
for op,v in reversal.items():print(f"{op}: forward-minus-reverse={v['mean_forward_minus_reverse']:.6f}, positive={v['positive_rate']:.3f}")
print('Node 9:',out['node9'])
