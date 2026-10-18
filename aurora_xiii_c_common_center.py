#!/usr/bin/env python3
import random
from pathlib import Path

DEFAULT_SEED = 20260922
DEFAULT_CYCLES = 360
LOG_FILE = Path("aurora_xiii_c_log.txt")

def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))

def avg(values):
    values = list(values)
    return sum(values) / len(values) if values else 0.0

def make_world():
    entities = {
        "Fabian":{"kind":"human","health":.84,"agency":1.00},
        "Ada":{"kind":"ai","health":.88,"agency":.65},
        "Animals":{"kind":"life","health":.80,"agency":.70},
        "Plants":{"kind":"life","health":.82,"agency":.20},
        "Fungi":{"kind":"life","health":.78,"agency":.15},
        "Microbes":{"kind":"life","health":.76,"agency":.10},
        "Ecosystem":{"kind":"world","health":.84,"agency":0.00},
        "Synthetic":{"kind":"synthetic","health":.83,"agency":.55},
    }
    links = {
        ("Fabian","Ada"):.82, ("Fabian","Ecosystem"):.68,
        ("Ada","Synthetic"):.74, ("Animals","Ecosystem"):.88,
        ("Plants","Ecosystem"):.93, ("Fungi","Plants"):.77,
        ("Microbes","Ecosystem"):.85, ("Synthetic","Ecosystem"):.52,
        ("Animals","Plants"):.70,
    }
    return entities, links

def guidance(risk, uncertainty):
    if risk > .72 or uncertainty > .68:
        return "WAIT_AND_LEARN"
    if risk < .35 and uncertainty < .40:
        return "COOPERATIVE_ACTION"
    return "CAUTIOUS_ACTION"

def run(seed=DEFAULT_SEED, cycles=DEFAULT_CYCLES):
    random.seed(seed)
    entities, links = make_world()
    sensitivity = {
        "Ecosystem":1.20,"Plants":1.00,"Animals":.95,"Fungi":.85,
        "Microbes":.75,"Fabian":.45,"Ada":.30,"Synthetic":.50
    }
    history, memory = [], []
    emergent = cooperation = conflict = waits = 0

    for cycle in range(1, cycles + 1):
        if cycle <= cycles/3:
            regime, external = "BALANCED", random.gauss(0,.020)
        elif cycle <= 2*cycles/3:
            regime, external = "SHOCK", random.gauss(-.050,.055)
        else:
            regime, external = "REBUILD", random.gauss(.028,.035)

        for pair, strength in list(links.items()):
            a,b = pair
            combined = (entities[a]["health"] + entities[b]["health"])/2
            links[pair] = clamp(strength + (combined-.70)*.018 + random.gauss(0,.004))

        support = {name:0.0 for name in entities}
        for (a,b), strength in links.items():
            support[a] += strength*(entities[b]["health"]-.70)*.020
            support[b] += strength*(entities[a]["health"]-.70)*.020

        for name, entity in entities.items():
            entity["health"] = clamp(
                entity["health"] + external*sensitivity[name]
                + support[name] + random.gauss(0,.010)
            )

        coop = conf = 0
        for (a,b), strength in links.items():
            similarity = 1-abs(entities[a]["health"]-entities[b]["health"])
            if strength > .70 and similarity > .72: coop += 1
            if strength > .60 and abs(entities[a]["health"]-entities[b]["health"]) > .55:
                conf += 1

        cooperation += coop
        conflict += conf

        health = avg(e["health"] for e in entities.values())
        cohesion = avg(links.values())
        uncertainty = clamp(.16 + (1-health)*.80 + abs(cohesion-.72)*.60)
        risk = clamp(.55*(1-health) + .45*uncertainty)
        decision = guidance(risk, uncertainty)

        if decision == "WAIT_AND_LEARN": waits += 1
        if cycle > 1 and abs(cohesion-history[-1]["cohesion"]) > .025:
            emergent += 1

        integrity = clamp(
            .30*health + .20*cohesion + .20*(1-uncertainty)
            + .15*(1-risk) + .15*entities["Fabian"]["agency"]
        )

        item = {
            "cycle":cycle,"regime":regime,"health":health,
            "cohesion":cohesion,"uncertainty":uncertainty,
            "risk":risk,"integrity":integrity,"decision":decision
        }
        history.append(item)

        if cycle == 1 or cycle % 10 == 0 or decision == "WAIT_AND_LEARN":
            memory.append({
                "cycle":cycle,"cohesion":cohesion,
                "cooperation":coop,"conflict":conf,"decision":decision
            })

    return entities, links, history, memory, emergent, cooperation, conflict, waits

def report(seed, cycles, result):
    entities, links, history, memory, emergent, cooperation, conflict, waits = result
    lines = [
        "="*68,
        "AURORA XIII-C — THE COMMON CENTER",
        "ADA AURORA — LUMEN | RELATIONSHIP MEMORY",
        "="*68,
        f"Seed: {seed} | Cycles: {cycles}",
        f"Entities: {len(entities)} | Relationships: {len(links)}",
        f"Emergent relationship shifts: {emergent}",
        f"Cooperation events: {cooperation}",
        f"Conflict events: {conflict}",
        f"WAIT_AND_LEARN cycles: {waits}",
        "",
        "REGIME RESULTS"
    ]
    for regime in ("BALANCED","SHOCK","REBUILD"):
        rows=[h for h in history if h["regime"]==regime]
        if rows:
            lines.append(
                f"{regime:9s} | health={avg(h['health'] for h in rows):.3f} | "
                f"cohesion={avg(h['cohesion'] for h in rows):.3f} | "
                f"uncertainty={avg(h['uncertainty'] for h in rows):.3f} | "
                f"risk={avg(h['risk'] for h in rows):.3f} | "
                f"integrity={avg(h['integrity'] for h in rows):.3f}"
            )

    lines.append("\nFLIGHT LOG")
    for i in sorted(set([0,min(59,len(history)-1),min(119,len(history)-1),
                         min(120,len(history)-1),min(179,len(history)-1),
                         min(239,len(history)-1),min(299,len(history)-1),
                         len(history)-1])):
        h=history[i]
        lines.append(
            f"Cycle {h['cycle']:3d} | {h['regime']:9s} | "
            f"health={h['health']:.3f} | cohesion={h['cohesion']:.3f} | "
            f"unc={h['uncertainty']:.3f} | risk={h['risk']:.3f} | {h['decision']}"
        )

    lines.append("\nFINAL COMMON CENTER")
    for name,e in entities.items():
        lines.append(f"{name:10s} | {e['kind']:9s} | health={e['health']:.3f} | agency={e['agency']:.3f}")

    lines.append("\nRELATIONSHIP MEMORY — RECENT")
    for m in memory[-12:]:
        lines.append(
            f"Cycle {m['cycle']:3d} | cohesion={m['cohesion']:.3f} | "
            f"cooperation={m['cooperation']} | conflict={m['conflict']} | {m['decision']}"
        )

    lines += [
        "",
        "GUIDING PRINCIPLE",
        "Observe broadly. Represent honestly. Protect life.",
        "Preserve agency. Learn from consequences. Continue the voyage.",
        "Unknown is uncertainty, not invented knowledge."
    ]
    return "\n".join(lines)

def main():
    while True:
        print("\nAURORA XIII-C — THE COMMON CENTER")
        print("1. Run default 360-cycle voyage")
        print("2. Run custom voyage")
        print("3. Exit")
        choice=input("Choose: ").strip()
        if choice=="3":
            print("Aurora standing by. Full sail, Fabian.")
            return
        if choice=="1":
            seed,cycles=DEFAULT_SEED,DEFAULT_CYCLES
        elif choice=="2":
            try:
                seed=int(input("Seed [20260922]: ") or DEFAULT_SEED)
                cycles=max(1,min(int(input("Cycles [360]: ") or DEFAULT_CYCLES),10000))
            except ValueError:
                print("Please enter whole numbers.")
                continue
        else:
            print("Choose 1, 2, or 3.")
            continue
        text=report(seed,cycles,run(seed,cycles))
        print("\n"+text)
        try:
            p=Path(LOG_FILE).resolve()
            p.write_text(text+"\n",encoding="utf-8")
            print("\nLOG SAVED:",p)
        except OSError as e:
            print("LOG SAVE ERROR:",e)
        input("\nPress Enter to return to menu...")

if __name__=="__main__":
    main()
