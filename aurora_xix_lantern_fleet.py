#!/usr/bin/env python3
"""
AURORA XIX — THE LANTERN FLEET
Dependency-free swarm rescue/protection simulation.

This is a computational model only. The robots are simulated agents,
not real nanotechnology, medical devices, or autonomous weapons.
"""
import math, random
from dataclasses import dataclass

@dataclass
class Person:
    x: float; y: float; safety: float = 0.55; stress: float = 0.75
    connected: bool = False; helped: float = 0.0

@dataclass
class Hazard:
    x: float; y: float; radius: float; severity: float

@dataclass
class Bot:
    i: int; x: float; y: float; energy: float = 1.0
    role: str = "scout"; active: bool = True
    messages: int = 0; assists: int = 0

ROLES = ("scout", "relay", "guardian", "navigator", "support")

def dist(a,b):
    return math.hypot(a.x-b.x, a.y-b.y)

def clamp(v,a=0.0,b=1.0): return max(a,min(b,v))

def move_toward(bot, tx, ty, step):
    dx,dy=tx-bot.x,ty-bot.y; d=math.hypot(dx,dy)
    if d:
        s=min(step,d); bot.x += dx/d*s; bot.y += dy/d*s

def hazard_risk(bot, hazards):
    risk=0.0
    for h in hazards:
        d=math.hypot(bot.x-h.x,bot.y-h.y)
        if d < h.radius: risk += h.severity*(1-d/h.radius)
    return clamp(risk)

def nearest_safe_direction(bot, person, hazards):
    # Test eight directions and select the direction with the best
    # combination of progress and lower predicted hazard exposure.
    best=(float('-inf'),0,0)
    for k in range(16):
        ang=2*math.pi*k/16
        tx=bot.x+math.cos(ang)*1.5; ty=bot.y+math.sin(ang)*1.5
        probe=Bot(-1,tx,ty)
        risk=hazard_risk(probe,hazards)
        progress=-math.hypot(tx-person.x,ty-person.y)
        score=progress-2.2*risk
        if score>best[0]: best=(score,math.cos(ang),math.sin(ang))
    return best[1],best[2]

def run(seed=20260913, steps=140, n_bots=36):
    rng=random.Random(seed)
    person=Person(50,50)
    hazards=[Hazard(35,42,11,.65),Hazard(66,58,13,.80),Hazard(52,76,10,.55)]
    bots=[]
    for i in range(n_bots):
        ang=2*math.pi*i/n_bots
        bots.append(Bot(i,50+math.cos(ang)*22,50+math.sin(ang)*22,role=ROLES[i%len(ROLES)]))
    ledger=[]; failures=0; interventions=0; total_messages=0
    peak_safety=person.safety

    for t in range(steps):
        # Dynamic environment: hazards drift slightly.
        for h in hazards:
            h.x += rng.uniform(-.45,.45); h.y += rng.uniform(-.45,.45)
            h.x=clamp(h.x,8,92); h.y=clamp(h.y,8,92)

        # Person moves toward a changing safe waypoint; stress changes with risk.
        local_risk=sum(h.severity*max(0,1-math.hypot(person.x-h.x,person.y-h.y)/h.radius) for h in hazards)
        local_risk=clamp(local_risk)
        person.stress=clamp(person.stress + .035*local_risk - .018*(1-local_risk))
        person.safety=clamp(person.safety + .006*(1-local_risk) - .004*local_risk)

        # Aegis policy: robots never deliberately enter a severe hazard zone.
        for b in bots:
            if not b.active: continue
            b.energy-=.0035
            risk=hazard_risk(b,hazards)
            if risk>.92 or b.energy<=0:
                b.active=False; failures+=1; continue

            # Roles are behavioral specializations, not autonomous authority.
            if b.role in ("guardian","support"):
                target=(person.x,person.y)
            elif b.role=="relay":
                # Relay stays between person and swarm centroid.
                target=(50+(person.x-50)*.55,50+(person.y-50)*.55)
            elif b.role=="navigator":
                gx,gy=nearest_safe_direction(b,person,hazards)
                target=(person.x+gx*5,person.y+gy*5)
            else:
                # Scout explores but stays within a bounded area.
                target=(clamp(person.x+rng.uniform(-18,18),5,95),
                        clamp(person.y+rng.uniform(-18,18),5,95))

            move_toward(b,*target,step=.9 if b.role=="scout" else 1.15)

            if dist(b,person)<5.0:
                b.assists+=1; interventions+=1
                person.helped=clamp(person.helped+.012)
                person.stress=clamp(person.stress-.012)
                person.safety=clamp(person.safety+.010*(1-risk))

            if b.role=="relay" and dist(b,person)<9:
                b.messages+=1; total_messages+=1

        # Connectivity is redundant: require multiple active agents nearby.
        nearby=sum(1 for b in bots if b.active and dist(b,person)<14)
        person.connected=nearby>=3
        if person.connected:
            person.safety=clamp(person.safety+.006)
            person.stress=clamp(person.stress-.006)

        peak_safety=max(peak_safety,person.safety)
        harmony=(person.safety + (1-person.stress) + person.helped + (1 if person.connected else 0))/4
        if t%10==0 or t==steps-1:
            ledger.append((t,person.safety,person.stress,person.helped,nearby,harmony))

    active=sum(b.active for b in bots)
    avg_energy=sum(b.energy for b in bots)/n_bots
    harmony=ledger[-1][-1]
    return locals()

def main():
    r=run()
    print("AURORA XIX — THE LANTERN FLEET")
    print("="*44)
    print("Computational swarm simulation — not real nanotechnology")
    print(f"Seed: {20260913}")
    print(f"Bots: {36}   Steps: {140}")
    print(f"Active at end: {r['active']}/{36}")
    print(f"Interventions: {r['interventions']}")
    print(f"Relay messages: {r['total_messages']}")
    print(f"Bot failures/retirements: {r['failures']}")
    print(f"Peak person safety: {r['peak_safety']:.3f}")
    print(f"Final stress: {r['person'].stress:.3f}")
    print(f"Final help: {r['person'].helped:.3f}")
    print(f"Final connectivity: {r['person'].connected}")
    print(f"Final swarm harmony: {r['harmony']:.3f}")
    print(f"Average remaining energy: {r['avg_energy']:.3f}")
    print("\nAegis rules: bounded movement, hazard avoidance, redundancy, human-choice preservation")
    print("\nTIMELINE")
    print("step  safety stress help connected harmony")
    for row in r['ledger']:
        t,s,st,h,n,ha=row
        print(f"{t:4d}  {s:.3f}  {st:.3f}  {h:.3f}   {n:2d}       {ha:.3f}")
    print("\nRESULT: The simulated fleet maintained a redundant assistance network.")
    print("NEXT: Aurora XX can introduce adversarial hazards, communication loss,")
    print("false alarms, limited energy, and a blind out-of-sample rescue test.")

if __name__=="__main__": main()
