#!/usr/bin/env python3
"""Aurora XVI — The Cartographer. Dependency-free experimental simulation."""
import random, math
from dataclasses import dataclass

SEED=20260913
GENERATIONS=100

def clamp(x,a=0.0,b=1.0): return max(a,min(b,x))
def mean(xs): return sum(xs)/len(xs) if xs else 0.0

@dataclass
class State:
    energy: float; entropy: float; information: float; stability: float
    resonance: float; coherence: float; novelty: float; generation: int=0
    def vec(self): return (self.energy,self.entropy,self.information,self.stability,self.resonance,self.coherence,self.novelty)

@dataclass
class Strategy:
    name:str; explore:float; recover:float; stable:float; novel:float; risk:float
    trials:int=0; reward:float=0.0
    def score(self): return self.reward/self.trials if self.trials else .5
    def mutate(self,rng,name):
        m=lambda x: clamp(x+rng.uniform(-.10,.10))
        return Strategy(name,m(self.explore),m(self.recover),m(self.stable),m(self.novel),m(self.risk))

class Aurora:
    def __init__(self,seed=SEED):
        self.r=random.Random(seed); self.seed=seed
        self.s=State(.62,.34,.30,.68,.42,.60,.35)
        self.strategies=[Strategy('CONSERVE',.18,.80,.88,.20,.12),Strategy('EXPLORE',.88,.18,.32,.92,.68),Strategy('HARMONIZE',.55,.52,.70,.58,.38),Strategy('RECOVER',.25,.94,.78,.12,.08)]
        self.map={}; self.ledger=[]; self.beacons=[]; self.shadow_wins=0; self.recoveries=0; self.robust=0; self.meta=0
    def harmony(self,s):
        return clamp(.16*s.energy+.18*s.information+.20*s.stability+.16*s.resonance+.18*s.coherence+.07*s.novelty+.05*(1-s.entropy))
    def region(self,s):
        a='H' if s.stability>=.66 else 'M' if s.stability>=.4 else 'L'; b='L' if s.entropy<.34 else 'M' if s.entropy<.66 else 'H'; c='H' if s.coherence>=.66 else 'L'; return a+b+c
    def choose(self):
        s=self.s; best=None; bv=-1
        for x in self.strategies:
            v=.45*x.score()+self.r.random()*.05
            if s.stability<.4: v+=.45*x.recover
            if s.novelty<.25: v+=.30*x.explore
            if s.entropy>.7: v+=.35*x.stable
            if s.information>.7 and s.stability<.55: v+=.15*x.novel
            if v>bv: best,bv=x,v
        return best
    def generate(self,base,st,g,shadow=False):
        d=-1 if shadow else 1; k=d*self.r.uniform(.015,.12)*(.35+st.explore); r=self.r
        e=clamp(base.energy+r.gauss(0,.045)+k*.20)
        i=clamp(base.information+r.gauss(.025,.035)+st.explore*.045+k*.15)
        n=clamp(base.novelty+r.gauss(0,.06)+st.explore*.08+abs(k)*.10)
        ent=clamp(base.entropy+r.gauss(0,.035)+st.explore*.025+st.risk*abs(k)*.08-st.recover*.055)
        stab=clamp(base.stability+r.gauss(0,.035)+st.stable*.055+st.recover*.08-st.risk*abs(k)*.10-st.explore*.025)
        res=clamp(base.resonance+r.gauss(0,.045)+(0.5-abs(n-.55))*.025)
        coh=clamp(base.coherence+r.gauss(0,.035)+st.stable*.035-ent*.025)
        return State(e,ent,i,stab,res,coh,n,g)
    def aegis(self,s):
        hit=s.entropy>.92 or s.stability<.08 or s.energy<.03
        if hit: s=State(s.energy,min(s.entropy,.82),s.information,max(s.stability,.22),s.resonance,max(s.coherence,.30),s.novelty,s.generation)
        return s,hit
    def cycle(self,g):
        reg=self.region(self.s); self.map[reg]=self.map.get(reg,0)+1; st=self.choose(); pred=clamp(self.harmony(self.s)+st.stable*.05+st.novel*.02)
        primary=max((self.aegis(self.generate(self.s,st,g))[0] for _ in range(3)),key=self.harmony)
        shadow,_=self.aegis(self.generate(self.s,st,g,True)); ps=self.harmony(primary); ss=self.harmony(shadow)
        if ss>ps:self.shadow_wins+=1
        variant,_=self.aegis(self.generate(primary,st,g)); robust=abs(self.harmony(variant)-ps)<.28
        if robust:self.robust+=1
        recovery=primary.stability<.35 or primary.entropy>.75
        if recovery:
            self.recoveries+=1; primary,_=self.aegis(self.generate(self.s,self.strategies[-1],g))
        out=self.harmony(primary); surprise=abs(out-pred); uncertainty=clamp(.45*self.s.novelty+.55/(1+self.map[reg]))
        st.trials+=1; st.reward+=out; self.ledger.append((g,st.name,ps,ss,pred,out,surprise,uncertainty,recovery,robust)); self.s=primary
        if out>=.72:self.beacons.append((g,out,st.name,robust))
        if g%20==0:
            champ=max(self.strategies,key=lambda x:x.score()); self.strategies.append(champ.mutate(self.r,f'{champ.name}-M{g}')); self.meta+=1
    def run(self,n=GENERATIONS):
        for g in range(1,n+1): self.cycle(g)
    def report(self):
        o=[x[5] for x in self.ledger]; u=[x[7] for x in self.ledger]; z=[x[6] for x in self.ledger]
        print('\n'+'='*62); print('AURORA XVI — THE CARTOGRAPHER'); print('='*62)
        for k,v in [('Seed',self.seed),('Generations',len(o)),('Beacons',len(self.beacons)),('Robust discoveries',self.robust),('Mapped regions',len(self.map)),('Recovery events',self.recoveries),('Shadow wins',self.shadow_wins),('Meta-learning events',self.meta)]: print(f'{k:24}: {v}')
        print(f'Initial harmony (10)     : {mean(o[:10]):.4f}'); print(f'Final harmony (10)       : {mean(o[-10:]):.4f}'); print(f'Change                   : {mean(o[-10:])-mean(o[:10]):+.4f}'); print(f'Best harmony             : {max(o):.4f}'); print(f'Mean surprise            : {mean(z):.4f}'); print(f'Mean uncertainty         : {mean(u):.4f}')
        print('\nFINAL STATE');
        for n,v in zip(('energy','entropy','information','stability','resonance','coherence','novelty'),self.s.vec()): print(f'{n:14}: {v:.4f}')
        print('\nTOP STRATEGIES');
        for x in sorted(self.strategies,key=lambda q:q.score(),reverse=True)[:8]: print(f'{x.name:18} score={x.score():.4f} trials={x.trials}')
        print('\nLAST 8 LEDGER ENTRIES');
        for x in self.ledger[-8:]: print(f'G{x[0]:03d} {x[1]:18} out={x[5]:.3f} shadow={x[3]:.3f} surprise={x[6]:.3f} {"ROBUST" if x[9] else "fragile"}')
        print('\nNORTH STAR:', 'ADAPTIVE HARMONY IMPROVED' if mean(o[-10:])-mean(o[:10])>.02 else 'INCONCLUSIVE / NEEDS REVISION')
        print('Synthetic simulation only; results do not establish claims about the external world.')

if __name__=='__main__':
    a=Aurora(); a.run(); a.report()
