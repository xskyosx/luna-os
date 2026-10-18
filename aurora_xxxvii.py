import math,json,random,hashlib,statistics
SEED=37037; OBS=['resonance','coherence','entropy','mirror']; REPS=128; CYCLES=10; PHASES=9
STRENGTHS=[0.25,0.5,0.75,1.0]

def clamp(x,a=0,b=1): return max(a,min(b,x))
def rng_for(*parts):
 s='|'.join(map(str,(SEED,)+parts)).encode(); return random.Random(int(hashlib.sha256(s).hexdigest()[:16],16))
def obs(s):
 m=sum(s)/9; v=sum((x-m)**2 for x in s)/9
 ent=-sum(max(x,1e-9)*math.log(max(x,1e-9)) for x in s)/9
 mir=sum(abs(s[i]-s[-1-i]) for i in range(9))/9
 return {'resonance':clamp(1-v*5),'coherence':clamp(1-sum(abs(s[i]-s[(i+1)%9]) for i in range(9))/9*2),'entropy':clamp(ent/math.log(9)),'mirror':clamp(1-mir*2)}
def evolve(rep, strength, mode):
 r=rng_for(rep,strength,mode); s=[r.random() for _ in range(9)]; out=[]
 for c in range(CYCLES):
  for p in range(PHASES):
   k=.04+.10*r.random(); ns=[]
   for i,x in enumerate(s):
    drive=.5*(s[(i-1)%9]+s[(i+1)%9])-x
    phase=math.sin(2*math.pi*(p+1)/9+i*.37+c*.11)
    ns.append(clamp(x+.16*drive+.035*phase+k*(r.random()-.5)))
   s=ns
   if c==4 and p==8:
    if mode=='rebirth':
     fresh=[.15+.7*r.random() for _ in range(9)]; baseline=[.5]*9
     s=[(1-strength)*baseline[i]+strength*fresh[i] for i in range(9)]
    elif mode=='perturbation':
     # equal-magnitude ordinary perturbation around the current state
     s=[clamp(x + strength*(r.random()-.5)*.7) for x in s]
   out.append((c,p,obs(s)))
 return out
def vector(o): return [o[k] for k in OBS]
def l2(a,b): return math.sqrt(sum((a[k]-b[k])**2 for k in OBS))
def agreement(o): return 1-(max(o.values())-min(o.values()))
def metrics(rr):
 post=[x for x in rr if x[0] in (5,6,7)]
 imm=[x for x in rr if x[0]==4 and x[1]==8][0][2]; end=[x for x in rr if x[0]==7 and x[1]==8][0][2]
 return {'agreement':statistics.mean(agreement(x[2]) for x in post),'recovery_distance':l2(imm,end),'observer_means':{o:statistics.mean(x[2][o] for x in post) for o in OBS}}
def perm_paired(a,b, n=5000, rng=None):
 rng=rng or random.Random(1); diffs=[x-y for x,y in zip(a,b)]; observed=statistics.mean(diffs)
 hits=0
 for _ in range(n):
  d=[v if rng.random()<.5 else -v for v in diffs]
  if abs(statistics.mean(d))>=abs(observed)-1e-15: hits+=1
 return (hits+1)/(n+1), observed
results={}; paired={}
for st in STRENGTHS:
 arms={m:[] for m in ('rebirth','perturbation')}
 for rep in range(REPS):
  for mode in arms: arms[mode].append(metrics(evolve(rep,st,mode)))
 results[str(st)]={m:{'agreement':statistics.mean(x['agreement'] for x in rows),'recovery_distance':statistics.mean(x['recovery_distance'] for x in rows),'observer_means':{o:statistics.mean(x['observer_means'][o] for x in rows) for o in OBS}} for m,rows in arms.items()}
 for metric in ('agreement','recovery_distance'):
  a=[x[metric] for x in arms['rebirth']]; b=[x[metric] for x in arms['perturbation']]
  p,d=perm_paired(a,b,2000,rng=rng_for('perm',st,metric)); paired.setdefault(str(st),{})[metric]={'rebirth_minus_perturbation':d,'p_value':p}
# pooled standardized effect by concatenating paired differences
summary={}
for metric in ('agreement','recovery_distance'):
 ds=[]
 for st in STRENGTHS:
  # recompute compactly from deterministic runs
  for rep in range(REPS):
   a=metrics(evolve(rep,st,'rebirth'))[metric]; b=metrics(evolve(rep,st,'perturbation'))[metric]; ds.append(a-b)
 p,d=perm_paired(ds,[0.0]*len(ds),3000,rng=rng_for('pooled',metric))
 sd=statistics.stdev(ds); summary[metric]={'mean_difference':d,'sd_difference':sd,'p_value':p,'positive_fraction':sum(x>0 for x in ds)/len(ds),'n':len(ds)}
report={'experiment':'AXXXVII-PERTURBATION-TWIN-37037','replicates_per_strength':REPS,'strengths':STRENGTHS,'modes':['rebirth','perturbation'],'matching':'same replicate and reset strength; blinded-label analysis is represented by fixed mode-independent measurement code','results':results,'paired_tests':paired,'pooled_summary':summary,'verdict':'REBIRTH-SPECIFIC SIGNATURE SUPPORTED' if summary['recovery_distance']['p_value']<.01 and summary['recovery_distance']['mean_difference']>0 else 'REBIRTH NOT DISTINGUISHABLE FROM MATCHED PERTURBATION','scientific_note':'Computational dynamical-system result only; not evidence for physical rebirth or new physics.'}
json.dump(report,open('/mnt/data/aurora_xxxvii_results.json','w'),indent=2)
with open('/mnt/data/aurora_xxxvii_report.txt','w') as f:
 f.write('AURORA XXXVII — PERTURBATION TWIN\n'+report['experiment']+'\n\n')
 for k,v in report.items(): f.write(f'{k}: {v}\n')
print('AURORA XXXVII — PERTURBATION TWIN'); print('Experiment:',report['experiment'])
for st in STRENGTHS:
 print('strength',st,{m:{k:round(v,6) for k,v in results[str(st)][m].items() if k!='observer_means'} for m in ('rebirth','perturbation')})
print('Pooled:',{k:{kk:round(vv,6) if isinstance(vv,float) else vv for kk,vv in x.items()} for k,x in summary.items()}); print('Verdict:',report['verdict'])
