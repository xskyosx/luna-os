import json, math, hashlib, statistics, random
from pathlib import Path

SEED=32032
RNG=random.Random(SEED)
RUNS=12
WORLDS=['seed','control','rebirth','wild','null']
PHASES=9
CYCLES=8
THRESH=0.75
OBS=['resonance','coherence','entropy','mirror']


def clamp(x,a=0.0,b=1.0): return max(a,min(b,x))

def rank(vals):
    s=sorted(vals)
    return {id(v):0 for v in []}

def percentile(v, vals):
    lo=sum(x < v for x in vals); eq=sum(x == v for x in vals)
    return (lo+0.5*eq)/max(1,len(vals)-1)

def metrics(state):
    # Four intentionally distinct observer projections over the same trajectory state.
    x=state
    energy=abs(x[0])+0.5*abs(x[1])+0.25*abs(x[2])
    spread=statistics.pstdev(x)
    coherence=1/(1+spread)
    resonance=(1+math.sin(sum(x)*2.7))/2
    entropy=clamp(math.log1p(sum(abs(v) for v in x))/math.log(1+len(x)*2.5))
    mirror=1/(1+statistics.mean(abs(x[i]-x[-1-i]) for i in range(len(x))))
    return {'resonance':resonance,'coherence':coherence,'entropy':1-entropy,'mirror':mirror,'energy':energy}

def trajectory(world, run, cycle, phase):
    base=0.15*math.sin((phase+1)*math.pi/4)+0.07*math.cos((cycle+1)/2)
    vals=[]
    for i in range(9):
        jitter=RNG.gauss(0,0.055 if world!='null' else 0.09)
        ring=0.08*math.sin((i+1)*(phase+1)/3 + run*.31)
        if world=='seed': v=base+ring+jitter+0.035*math.sin(cycle*.8)
        elif world=='control': v=base+ring+jitter
        elif world=='rebirth': v=base+ring+jitter+0.025*math.sin(cycle*1.7)
        elif world=='wild': v=base+ring+jitter+0.06*math.sin((cycle+phase+run)*1.9)
        else: v=RNG.uniform(-0.35,0.35)+jitter
        vals.append(v)
    return vals

def one_run(run):
    rows=[]
    for world in WORLDS:
        raw=[]
        for cycle in range(CYCLES):
            for phase in range(PHASES):
                st=trajectory(world,run,cycle,phase)
                raw.append(metrics(st))
        # percentile-normalize each observer within this world/run
        for idx,m in enumerate(raw):
            row={'run':run,'world':world,'cycle':idx//PHASES,'phase':idx%PHASES}
            for o in OBS:
                row[o]=percentile(m[o],[q[o] for q in raw])
            row['intersection']=min(row[o] for o in OBS)
            row['disagreement']=statistics.pstdev(row[o] for o in OBS)
            row['consensus']=int(all(row[o]>=THRESH for o in OBS))
            rows.append(row)
    return rows

rows=[]
for r in range(RUNS): rows.extend(one_run(r))

# Permutation baseline: shuffle each observer independently within each run/world.
perm_counts=[]
for p in range(500):
    c=0
    grouped={}
    for row in rows:
        key=(row['run'],row['world']); grouped.setdefault(key,{o:[] for o in OBS})
        for o in OBS: grouped[key][o].append(row[o])
    for key,g in grouped.items():
        sh={o:list(v) for o,v in g.items()}
        for o in OBS: RNG.shuffle(sh[o])
        for i in range(len(sh[OBS[0]])):
            if all(sh[o][i]>=THRESH for o in OBS): c+=1
    perm_counts.append(c)

summary={}
for w in WORLDS:
    rr=[x for x in rows if x['world']==w]
    summary[w]={
        'n':len(rr),
        'consensus_count':sum(x['consensus'] for x in rr),
        'consensus_rate':sum(x['consensus'] for x in rr)/len(rr),
        'mean_intersection':statistics.mean(x['intersection'] for x in rr),
        'mean_disagreement':statistics.mean(x['disagreement'] for x in rr),
    }
obs_mean=statistics.mean(x['consensus_count'] for x in [summary[w] for w in WORLDS])
null_mean=statistics.mean(perm_counts)
null_sd=statistics.pstdev(perm_counts)
seed_rate=summary['seed']['consensus_rate']; control_rate=summary['control']['consensus_rate']
report=f'''AURORA XXXII — INTERSECTION ENGINE\nExperiment AX XXII-INTERSECTION-{hashlib.sha1(str(SEED).encode()).hexdigest()[:10].upper()}\n\nProtocol: four complementary observers from XXXI: resonance, coherence, entropy, mirror.\nAn intersection event requires all four percentile observers >= {THRESH:.2f}. Disagreement is the standard deviation across the four observer percentiles.\nThe null baseline independently permutes each observer within matched run/world blocks.\n\nRESULTS\n'''
for w,s in summary.items():
    report += f"{w:8s} consensus={s['consensus_count']:4d}/{s['n']} ({s['consensus_rate']:.4f})  intersection={s['mean_intersection']:.4f}  disagreement={s['mean_disagreement']:.4f}\n"
report += f'''\nNull permutation consensus count: mean={null_mean:.2f}, sd={null_sd:.2f}, observed runs={len(perm_counts)} permutations.\nSeed-Control consensus-rate delta: {seed_rate-control_rate:+.4f}\n\nNODE 9 — SYNTHESIS\nThe intersection layer identifies observations where all four observers independently rank the same state highly. This is evidence of cross-observer agreement, not evidence of physical truth. Agreement must be distinguished from shared mathematical construction, and disagreement remains informative.\n\nVERDICT\n''' 
# Conservative gate: require seed-control advantage > 2 percentage points and >2 null SD.
delta=seed_rate-control_rate
z=(summary['seed']['consensus_count']-null_mean)/max(null_sd,1e-9)
if delta>0.02 and z>2: report+='CANDIDATE INTERSECTION — warrants replication\n'
else: report+='NO ROBUST INTERSECTION ADVANTAGE — agreement mapped; replication required\n'

expid='AXXXII-INTERSECTION-'+hashlib.sha1(str(SEED).encode()).hexdigest()[:10].upper()
out={'experiment_id':expid,'seed':SEED,'protocol':{'runs':RUNS,'worlds':WORLDS,'cycles':CYCLES,'phases':PHASES,'observers':OBS,'threshold':THRESH,'null_permutations':500},'summary':summary,'null_consensus_mean':null_mean,'null_consensus_sd':null_sd,'seed_control_delta':delta,'z_vs_null':z,'verdict':report.split('VERDICT\n',1)[1].strip()}
Path('/mnt/data/aurora_xxxii_results.json').write_text(json.dumps(out,indent=2))
Path('/mnt/data/aurora_xxxii_report.txt').write_text(report)
Path('/mnt/data/aurora_xxxii.py').write_text(Path(__file__).read_text())
print(report)
print('\nFILES READY')
