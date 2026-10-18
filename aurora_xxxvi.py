import math,json,random,hashlib,statistics
SEED=36036; OBS=['resonance','coherence','entropy','mirror']
REPS=256; CYCLES=10; PHASES=9
STRENGTHS=[0.0,0.25,0.5,0.75,1.0]

def clamp(x,a=0,b=1): return max(a,min(b,x))
def rng_for(*parts):
 s='|'.join(map(str,(SEED,)+parts)).encode(); return random.Random(int(hashlib.sha256(s).hexdigest()[:16],16))
def observers(s):
 m=sum(s)/9; v=sum((x-m)**2 for x in s)/9
 ent=-sum(max(x,1e-9)*math.log(max(x,1e-9)) for x in s)/9
 mir=sum(abs(s[i]-s[-1-i]) for i in range(9))/9
 return {'resonance':clamp(1-v*5),'coherence':clamp(1-sum(abs(s[i]-s[(i+1)%9]) for i in range(9))/9*2),'entropy':clamp(ent/math.log(9)),'mirror':clamp(1-mir*2)}
def run(rep,strength):
 r=rng_for(rep,strength); s=[r.random() for _ in range(9)]; out=[]
 for c in range(CYCLES):
  for p in range(PHASES):
   k=.04+.10*r.random(); ns=[]
   for i,x in enumerate(s):
    drive=.5*(s[(i-1)%9]+s[(i+1)%9])-x
    phase=math.sin(2*math.pi*(p+1)/9+i*.37+c*.11)
    ns.append(clamp(x+.16*drive+.035*phase+k*(r.random()-.5)))
   s=ns
   if c==4 and p==8 and strength>0:
    baseline=[.5]*9
    fresh=[.15+.7*r.random() for _ in range(9)]
    s=[(1-strength)*baseline[i]+strength*fresh[i] for i in range(9)]
   out.append((c,p,observers(s)))
 return out
def dist(a,b): return math.sqrt(sum((a[o]-b[o])**2 for o in OBS))
def agreement(o): return 1-(max(o.values())-min(o.values()))
results={}
for strength in STRENGTHS:
 rows=[]
 for rep in range(REPS):
  rr=run(rep,strength); post=[x for x in rr if x[0] in (5,6,7)]
  immediate=[x for x in rr if x[0]==4 and x[1]==8][0][2]
  end=[x for x in rr if x[0]==7 and x[1]==8][0][2]
  rows.append({'agreement':statistics.mean(agreement(x[2]) for x in post),'recovery_distance':dist(immediate,end),**{o:statistics.mean(x[2][o] for x in post) for o in OBS}})
 results[str(strength)]={k:statistics.mean(x[k] for x in rows) for k in rows[0]}
# paired contrast against no-reset baseline using identical rep seeds per strength
baseline=[]
for rep in range(REPS):
 rr=run(rep,0.0); post=[x for x in rr if x[0] in (5,6,7)]; imm=[x for x in rr if x[0]==4 and x[1]==8][0][2]; end=[x for x in rr if x[0]==7 and x[1]==8][0][2]
 baseline.append({'agreement':statistics.mean(agreement(x[2]) for x in post),'recovery_distance':dist(imm,end),**{o:statistics.mean(x[2][o] for x in post) for o in OBS}})
contrasts={}
for st in STRENGTHS[1:]:
 rr=results[str(st)]; contrasts[str(st)]={'agreement_delta':rr['agreement']-results['0.0']['agreement'],'recovery_distance_delta':rr['recovery_distance']-results['0.0']['recovery_distance']}
# linear dose-response on agreement and recovery
xs=STRENGTHS; ya=[results[str(x)]['agreement'] for x in xs]; yr=[results[str(x)]['recovery_distance'] for x in xs]
def corr(a,b):
 ma=statistics.mean(a); mb=statistics.mean(b); den=math.sqrt(sum((x-ma)**2 for x in a)*sum((y-mb)**2 for y in b)); return sum((x-ma)*(y-mb) for x,y in zip(a,b))/den if den else 0
report={'experiment':'AXXXVI-RECOVERY-OBSERVATORY-36036','replicates_per_strength':REPS,'strengths':STRENGTHS,'intervention':'cycle 4 phase 8; reset strength blends deterministic baseline with fresh random state','recovery_window':[5,6,7],'results':results,'contrasts_vs_zero':contrasts,'dose_response_correlation':{'agreement':corr(xs,ya),'recovery_distance':corr(xs,yr)},'verdict':'DOSE-RESPONSE DETECTED' if abs(corr(xs,yr))>.8 else 'NO CLEAR DOSE-RESPONSE','scientific_note':'Computational dynamical-system result only; not evidence for physical phenomena.'}
json.dump(report,open('/mnt/data/aurora_xxxvi_results.json','w'),indent=2)
with open('/mnt/data/aurora_xxxvi_report.txt','w') as f:
 f.write('AURORA XXXVI — RECOVERY OBSERVATORY\n'+report['experiment']+'\n\n')
 for k,v in report.items(): f.write(f'{k}: {v}\n')
print('AURORA XXXVI — RECOVERY OBSERVATORY'); print('Experiment:',report['experiment'])
for s in STRENGTHS: print('strength',s, {k:round(v,6) for k,v in results[str(s)].items()})
print('Dose-response:',{k:round(v,6) for k,v in report['dose_response_correlation'].items()}); print('Verdict:',report['verdict'])
