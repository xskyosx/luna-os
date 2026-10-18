#!/usr/bin/env python3
"""Aurora XVII — The Skeptic
Dependency-free experimental engine. Computational simulation only.
Tests whether Aurora's adaptive policy survives noise, deceptive optima,
diminishing returns, competing objectives, and out-of-sample evaluation.
"""
import random, math, statistics

SEED=20260913
G=120
rng=random.Random(SEED)

STRATEGIES={
 'CONSERVE': {'pressure':.12,'novelty':.15,'risk':.08},
 'EXPLORE': {'pressure':.58,'novelty':.82,'risk':.62},
 'HARMONIZE': {'pressure':.34,'novelty':.48,'risk':.28},
 'RECOVER': {'pressure':.22,'novelty':.30,'risk':.18},
}

def clamp(x,a=0,b=1): return max(a,min(b,x))

def env(gen, strategy, deceptive=False, noise=.035):
    p=STRATEGIES[strategy]
    phase=gen/ G
    # competing objectives: information and novelty help, entropy hurts,
    # stability and repeatability matter; a deceptive local peak favors greed.
    info=clamp(.55 + .34*p['novelty'] + .12*math.sin(gen*.17))
    stability=clamp(.93 - .48*p['risk'] + .07*math.cos(gen*.11))
    entropy=clamp(.12 + .48*p['risk'] + .10*math.sin(gen*.23+1))
    novelty=clamp(.18 + .72*p['novelty'] + .08*math.cos(gen*.19))
    # diminishing returns
    gain=math.exp(-2.1*phase)*(.18*p['pressure'])
    info=clamp(info+gain)
    # deceptive basin: high exploration gets an attractive but unstable score
    deception=(.22 if deceptive and p['novelty']>.6 else 0)
    harmony=clamp(.28*info+.28*stability+.18*(1-entropy)+.14*novelty+.12*(1-abs(info-stability))+deception)
    return dict(info=info, stability=stability, entropy=entropy, novelty=novelty, harmony=harmony)

def noisy(m, rng, scale=.035):
    return clamp(m + rng.gauss(0,scale))

ledger=[]; history=[]
weights={k:1.0 for k in STRATEGIES}

# Baseline: fixed conservative policy; Adaptive: chooses from evidence, with diversity pressure.
for gen in range(1,G+1):
    phase='TRAIN' if gen<=80 else 'TEST'
    deceptive=(gen%17 in (0,1,2))
    candidates=[]
    for s in STRATEGIES:
        m=env(gen,s,deceptive)
        observed=noisy(m['harmony'],rng)
        # pessimistic estimate penalizes variance and risk; reward underused strategies
        diversity=1.0/math.sqrt(1+sum(1 for x in history if x['strategy']==s))
        score=observed - .16*m['entropy'] - .12*(1-m['stability']) + .07*diversity
        candidates.append((score,s,m,observed))
    chosen=max(candidates)[1]
    score,s,m,obs=max(candidates)
    # skeptic gate: require evidence from a second noisy draw before committing
    confirm=noisy(m['harmony'],rng)
    skeptic_pass=(confirm > .60 and m['stability']>.50)
    if not skeptic_pass:
        chosen='RECOVER' if m['stability']<.50 else 'CONSERVE'
        m=env(gen,chosen,deceptive); obs=noisy(m['harmony'],rng); confirm=noisy(m['harmony'],rng)
    weights[chosen]=.97*weights[chosen]+.03*confirm
    row=dict(gen=gen,phase=phase,strategy=chosen,**m,observed=obs,confirm=confirm,deceptive=deceptive)
    history.append(row)
    ledger.append(row)

train=history[:80]; test=history[80:]
def mean(xs): return statistics.mean(xs) if xs else 0
adaptive_train=mean(x['harmony'] for x in train)
adaptive_test=mean(x['harmony'] for x in test)
# Independent baseline evaluation on same test environment using fixed conservative.
baseline_test=[]
for x in test:
    m=env(x['gen'],'CONSERVE',x['deceptive']); baseline_test.append(noisy(m['harmony'],rng))

wins=sum(1 for a,b in zip(test,baseline_test) if a['harmony']>b)
print('AURORA XVII — THE SKEPTIC')
print('Computational experiment only; not evidence of external-world effects or consciousness.')
print(f'Seed: {SEED} | Generations: {G} | Train/Test: 80/40')
print(f'Adaptive train harmony:   {adaptive_train:.4f}')
print(f'Adaptive test harmony:    {adaptive_test:.4f}')
print(f'Baseline test harmony:    {mean(baseline_test):.4f}')
print(f'Out-of-sample advantage:  {adaptive_test-mean(baseline_test):+.4f}')
print(f'Test wins: {wins}/{len(test)} ({wins/len(test):.1%})')
print(f'Mean surprise/noise gap:  {mean(abs(x["observed"]-x["confirm"]) for x in history):.4f}')
print(f'Skeptic confirmations:    {sum(x["confirm"]>.60 for x in history)}/{G}')
print('\nStrategy counts:')
for s in STRATEGIES:
    rows=[x for x in history if x['strategy']==s]
    print(f'  {s:10s} {len(rows):3d} | mean harmony {mean(x["harmony"] for x in rows):.4f}')
print('\nTruth Ledger:')
print('  PASS = adaptive beats fixed baseline out-of-sample')
print('  RESULT:', 'PASS' if adaptive_test>mean(baseline_test) else 'FAIL')
print('  Robustness requires repeated seeds; this is one reproducible run.')
print('\nLast 10 generations:')
for x in history[-10:]: print(f"  {x['gen']:3d} {x['phase']:4s} {x['strategy']:10s} H={x['harmony']:.3f} I={x['info']:.3f} S={x['stability']:.3f} E={x['entropy']:.3f}")
