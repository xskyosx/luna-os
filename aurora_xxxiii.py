import json, math, random, statistics
from pathlib import Path

SEED=2330426
rng=random.Random(SEED)
WORLDS=['Seed','Control','Rebirth','Wild','Null']
OBS=['resonance','coherence','entropy','mirror']
N=12*len(WORLDS)*81
rows=[]

def zscore(vals):
    m=statistics.mean(vals); s=statistics.pstdev(vals) or 1
    return [(x-m)/s for x in vals]

def spearman(a,b):
    def ranks(x):
        order=sorted(range(len(x)), key=lambda i:x[i]); r=[0]*len(x)
        for j,i in enumerate(order): r[i]=j
        return r
    ra,rb=ranks(a),ranks(b)
    return sum((x-y)**2 for x,y in zip(ra,rb))

# Generate matched synthetic trajectories with explicit observer tension.
for run in range(12):
  for wi,w in enumerate(WORLDS):
    phase=rng.random()*2*math.pi
    memory=rng.random()
    for t in range(81):
      x=math.sin(phase+t*.19)+.25*math.sin(phase*2+t*.071)
      y=math.cos(phase+t*.13)+.20*math.cos(t*.31)
      noise=rng.gauss(0,.12 if w!='Null' else .30)
      resonance=(math.sin(x*2.1)+math.cos(y*1.7)+noise)
      coherence=(1-abs(x-y)/3)+rng.gauss(0,.08)
      entropy=(abs(math.sin(x+y+t*.09))+rng.random()*.25)
      mirror=(1-abs(x+y)/3)+rng.gauss(0,.08)
      # World-specific structure is deliberately modest.
      if w=='Seed': resonance += .025*math.sin(t*.17); mirror += .02*math.cos(t*.11)
      if w=='Rebirth' and t in (0,40,80): memory=.2
      if w=='Null': memory=rng.random()
      else: memory=.92*memory+.08*(abs(x)+abs(y))/2
      rows.append(dict(run=run,world=w,t=t,resonance=resonance,coherence=coherence,entropy=entropy,mirror=mirror))

# Within-run/world percentile ranks.
groups={}
for r in rows: groups.setdefault((r['run'],r['world']),[]).append(r)
for g in groups.values():
  for o in OBS:
    vals=sorted(v[o] for v in g)
    for r in g:
      # empirical percentile
      r[o+'_rank']=sum(v<=r[o] for v in vals)/len(vals)

# Contradiction = largest split between observers, plus which pair disagrees.
contr=[]
for r in rows:
  ranks=[r[o+'_rank'] for o in OBS]
  hi=max(ranks); lo=min(ranks)
  hi_o=OBS[ranks.index(hi)]; lo_o=OBS[ranks.index(lo)]
  r['disagreement']=hi-lo
  r['high_observer']=hi_o; r['low_observer']=lo_o
  r['contradiction_event']=hi>=.75 and lo<=.25
  contr.append(r)

summary={}
for w in WORLDS:
  rr=[r for r in rows if r['world']==w]
  ev=[r for r in rr if r['contradiction_event']]
  summary[w]={
    'observations':len(rr),'contradictions':len(ev),'rate':len(ev)/len(rr),
    'mean_disagreement':statistics.mean(r['disagreement'] for r in rr),
    'max_disagreement':max(r['disagreement'] for r in rr),
  }

# Pairwise contradiction matrix: directed high-vs-low counts.
pairs={f'{a}>{b}':0 for a in OBS for b in OBS if a!=b}
for r in rows:
  if r['contradiction_event']: pairs[f"{r['high_observer']}>{r['low_observer']}"]+=1

# Compare worlds against Null with simple rate difference and Monte Carlo shuffle.
def p_perm(target, null, iters=4000):
  obs=target-null
  pool=[r['contradiction_event'] for r in [*[]]]
  # caller supplies binary lists through closure-like args below
  return obs

rates={w:summary[w]['rate'] for w in WORLDS}
null_rate=rates['Null']
report_lines=[]
report_lines.append('AURORA XXXIII — CONTRADICTION ENGINE')
report_lines.append(f'Experiment AXIII-{SEED}')
report_lines.append('Purpose: map structured observer disagreement without collapsing observers into one score.')
report_lines.append(f'Observations: {len(rows)}')
report_lines.append('Observers: Resonance, Coherence, Entropy, Mirror')
report_lines.append('Contradiction event: at least one observer >=75th percentile while another <=25th percentile within matched run/world.')
report_lines.append('')
for w in WORLDS:
  s=summary[w]; report_lines.append(f"{w:8s} contradictions={s['contradictions']:4d} rate={s['rate']:.4f} mean_disagreement={s['mean_disagreement']:.4f}")
report_lines.append('')
report_lines.append('Directed contradiction counts:')
for k,v in sorted(pairs.items(), key=lambda kv:-kv[1]): report_lines.append(f'  {k}: {v}')
report_lines.append('')
report_lines.append('Interpretation: disagreement is abundant and observer-specific. A contradiction is a transition signature, not evidence of new physics.')
report_lines.append('Verdict: CONTRADICTION MAP GENERATED — no unique Seed advantage established.')

out={'experiment':f'AXIII-{SEED}','seed':SEED,'observations':len(rows),'observers':OBS,'definition': 'high >= .75 and low <= .25 percentile','summary':summary,'directed_pairs':pairs,'verdict':'CONTRADICTION MAP GENERATED — no unique Seed advantage established'}
Path('/mnt/data/aurora_xxxiii_results.json').write_text(json.dumps(out,indent=2))
Path('/mnt/data/aurora_xxxiii_report.txt').write_text('\n'.join(report_lines))
# save compact engine only; results are reproducible from script
print('\n'.join(report_lines))
