#!/usr/bin/env python3
import math, random
from dataclasses import dataclass

@dataclass
class State:
    energy: float = 0.0
    mass: float = 1.0
    x: float = 0.0
    y: float = 0.0
    phase: float = 0.0
    amplitude: float = 0.0
    information: float = 0.0
    resonance: float = 0.0
    stability: float = 1.0
    observed: bool = False
    def copy(self): return State(**self.__dict__)

def dist(a,b):
    keys=('energy','x','y','phase','amplitude','information','resonance','stability')
    return math.sqrt(sum((getattr(a,k)-getattr(b,k))**2 for k in keys))

class Aurora:
    def __init__(self, seed=20260911, c=3.0):
        self.rng=random.Random(seed); self.c=c
        self.checkpoints={}; self.history=[]; self.missing=[]
    def save(self,name,s): self.checkpoints[name]=s.copy(); self.history.append(('CHECKPOINT:'+name,s.copy()))
    def undo(self,name):
        s=self.checkpoints[name].copy(); self.history.append(('UNDO:'+name,s.copy())); return s
    def redo(self,name):
        s=self.checkpoints[name].copy(); self.history.append(('REDO:'+name,s.copy())); return s
    def jump(self,name):
        s=self.checkpoints[name].copy(); self.history.append(('JUMP:'+name,s.copy())); return s
    def op(self,name,s):
        o=s.copy()
        if name=='ZERO': o.energy=0
        elif name=='ADD': o.energy+=1
        elif name=='SUB': o.energy-=1
        elif name=='MUL': o.energy*=1.25
        elif name=='DIV': o.energy/=1.25
        elif name=='EMC2': o.energy=o.mass*self.c**2
        elif name=='EMC4': o.energy=o.mass*self.c**4  # experimental symbolic transform
        elif name=='RESO':
            o.resonance=.5+.5*math.sin(o.phase); o.information+=.15*o.resonance
        elif name=='UNRESO': o.resonance=1-o.resonance; o.stability*=.98
        elif name=='MIRROR': o.x,o.y,o.phase=-o.x,-o.y,-o.phase
        elif name=='PARTICLE': o.x=o.amplitude*math.cos(o.phase); o.y=o.amplitude*math.sin(o.phase)
        elif name=='WAVE': o.amplitude=math.sqrt(abs(o.energy)+1e-12); o.phase=math.atan2(o.y,o.x)
        elif name=='CHAOS':
            o.x+=self.rng.gauss(0,.12); o.y+=self.rng.gauss(0,.12); o.phase+=self.rng.gauss(0,.18); o.stability*=.95
        elif name=='ORDER': o.x*=.85; o.y*=.85; o.phase*=.85; o.stability=min(1,o.stability+.04)
        elif name=='K2':
            o.x,o.y=-o.x,-o.y; o.resonance=.5+.5*math.cos(2*o.phase); o.information+=.1*o.resonance
        elif name=='OBSERVE': o.observed=True; o.information+=.05; o.stability*=.995
        else: raise ValueError('Unknown operand: '+name)
        o.information=max(0,min(10,o.information)); o.stability=max(0,min(1,o.stability))
        self.history.append((name,o.copy())); return o
    def orbit(self,s,a=1,b=.62,steps=8):
        o=s.copy(); pts=[]
        for i in range(steps):
            t=2*math.pi*i/steps; pts.append((a*math.cos(t),b*math.sin(t)))
        o.x,o.y=pts[1]; o.phase=2*math.pi/steps; o.amplitude=math.hypot(o.x,o.y)
        return o,pts
    def genome(self,s,g):
        for op in g: s=self.op(op,s)
        return s
    def triad_jump(self,triad,name): return [self.jump(name) for _ in triad]
    def run(self):
        print('AURORA v2.2 — UNIVERSAL OPERAND FIELD')
        print('Computational sandbox; EMC4 is experimental, not established physics.\n')
        root=State(); self.save('R0',root)
        e2=self.op('EMC2',root); e4=self.op('EMC4',root)
        print('EMC2:',e2.energy,' EMC4:',e4.energy)
        orb,_=self.orbit(root); print('elliptical orbit:',round(orb.x,4),round(orb.y,4))
        triad=[State(),State(),State()]; self.save('ZERO',triad[0])
        genomes=[['ZERO','K2','RESO','MIRROR'],['ZERO','EMC2','WAVE','ORDER'],['ZERO','EMC4','UNRESO','CHAOS']]
        for i,g in enumerate(genomes):
            s=self.genome(triad[i],g); self.save('A'+str(i+1),s); back=self.undo('ZERO'); replay=self.redo('A'+str(i+1)); err=dist(s,replay)
            print(f'Instance {i+1}: {g} | E={s.energy:.3f} R={s.resonance:.3f} S={s.stability:.3f} redo_error={err:.6f}')
        print('JUMP-3:',[x.energy for x in self.triad_jump(triad,'ZERO')])
        print('History records:',len(self.history))
        print('Done.')

if __name__=='__main__': Aurora().run()
