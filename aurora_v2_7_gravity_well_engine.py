#!/usr/bin/env python3
"""
AURORA v2.5 — THE QUESTION ENGINE
Pure Python 3 / no external packages.

A computational sandbox. Physics-like names are simulation constructs;
EMC4 is an experimental computational transform, not established physics.

New layer:
  KNOWN <-> UNKNOWN <-> SHADOW
  - extracts questions from the Lantern Ledger
  - runs repeated trials with controlled seeds
  - measures repeatability
  - promotes only repeatable patterns into the Aurora memory
  - keeps uncertainty instead of pretending it is knowledge
"""
import math
import random
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
    # Aurora-only expansion / gravity-like field variables.
    area_xyz: float = 1.0
    energy_density: float = 0.0
    gravity_field: float = 0.0
    self_fuel: float = 100.0
    velocity: float = 0.0

    def copy(self):
        return State(**self.__dict__)


def dist(a, b):
    keys = ('energy','x','y','phase','amplitude','information','resonance','stability')
    return math.sqrt(sum((getattr(a,k)-getattr(b,k))**2 for k in keys))


class Aurora:
    OPERANDS = [
        'ZERO','ADD','SUB','MUL','DIV','EMC2','EMC4','RESO','UNRESO',
        'MIRROR','PARTICLE','WAVE','CHAOS','ORDER','K2','OBSERVE',
        'EXPAND','CONTRACT','SELF_FUEL','ACCEL_C'
    ]

    def __init__(self, seed=20260911, c=3.0):
        self.seed = seed
        self.rng = random.Random(seed)
        self.c = c
        self.history = []
        self.memory = []
        self.questions = []
        self.unknown_basin = []
        self.experiments = []

    def op(self, name, state):
        o = state.copy()
        if name == 'ZERO': o.energy = 0.0
        elif name == 'ADD': o.energy += 1.0
        elif name == 'SUB': o.energy -= 1.0
        elif name == 'MUL': o.energy *= 1.25
        elif name == 'DIV': o.energy /= 1.25
        elif name == 'EMC2': o.energy = o.mass * self.c**2
        elif name == 'EMC4': o.energy = o.mass * self.c**4
        elif name == 'RESO':
            o.resonance = 0.5 + 0.5*math.sin(o.phase)
            o.information += 0.15*o.resonance
        elif name == 'UNRESO':
            o.resonance = 1.0-o.resonance
            o.stability *= 0.98
        elif name == 'MIRROR': o.x, o.y, o.phase = -o.x, -o.y, -o.phase
        elif name == 'PARTICLE':
            o.x = o.amplitude*math.cos(o.phase)
            o.y = o.amplitude*math.sin(o.phase)
        elif name == 'WAVE':
            o.amplitude = math.sqrt(abs(o.energy)+1e-12)
            o.phase = math.atan2(o.y,o.x)
        elif name == 'CHAOS':
            o.x += self.rng.gauss(0,0.12); o.y += self.rng.gauss(0,0.12)
            o.phase += self.rng.gauss(0,0.18); o.stability *= 0.95
        elif name == 'ORDER':
            o.x *= 0.85; o.y *= 0.85; o.phase *= 0.85
            o.stability = min(1.0,o.stability+0.04)
        elif name == 'K2':
            o.x, o.y = -o.x, -o.y
            o.resonance = 0.5+0.5*math.cos(2.0*o.phase)
            o.information += 0.10*o.resonance
        elif name == 'OBSERVE':
            o.observed = True; o.information += 0.05; o.stability *= 0.995
        elif name == 'EXPAND':
            # Aurora model: energy occupies more XYZ volume.
            # This is a simulation rule, not a claim about gravity physics.
            factor = 1.35
            o.area_xyz *= factor
            o.energy_density = abs(o.energy) / max(o.area_xyz, 1e-12)
            # Equal-and-opposite bookkeeping: expansion creates an inward
            # gravity-like confinement term in this sandbox.
            o.gravity_field = o.energy / max(o.area_xyz ** (2.0/3.0), 1e-12)
            o.information += 0.08 * math.log1p(o.area_xyz)
        elif name == 'CONTRACT':
            factor = 1.20
            o.area_xyz = max(1e-6, o.area_xyz / factor)
            o.energy_density = abs(o.energy) / max(o.area_xyz, 1e-12)
            o.gravity_field = o.energy / max(o.area_xyz ** (2.0/3.0), 1e-12)
            o.information += 0.04
        elif name == 'SELF_FUEL':
            # Convert a small portion of internal reserve into kinetic energy.
            draw = min(o.self_fuel, max(0.25, 0.05 * abs(o.energy) + 0.5))
            o.self_fuel -= draw
            o.energy += draw
            o.energy_density = abs(o.energy) / max(o.area_xyz, 1e-12)
            o.gravity_field = o.energy / max(o.area_xyz ** (2.0/3.0), 1e-12)
            o.information += 0.03
        elif name == 'ACCEL_C':
            # Relativistic kinetic-energy cost: K=(gamma-1)mc^2.
            # The engine approaches c but never reaches it for finite energy.
            target = min(0.999999, max(0.0, o.velocity + 0.10))
            gamma = 1.0 / math.sqrt(max(1e-12, 1.0 - target*target))
            required = (gamma - 1.0) * o.mass * self.c**2
            if required <= max(0.0, o.energy):
                o.velocity = target
            else:
                # Partial acceleration when the energy budget is insufficient.
                o.velocity = min(target, self.c * math.sqrt(
                    max(0.0, 1.0 - 1.0 / (1.0 + max(0.0, o.energy)/(o.mass*self.c**2)))
                ))
            o.energy = max(0.0, o.energy - required if required <= o.energy else o.energy * 0.15)
            o.energy_density = abs(o.energy) / max(o.area_xyz, 1e-12)
            o.gravity_field = o.energy / max(o.area_xyz ** (2.0/3.0), 1e-12)
        else: raise ValueError('Unknown operand: '+name)
        o.information=max(0.0,min(10.0,o.information))
        o.stability=max(0.0,min(1.0,o.stability))
        o.energy_density=abs(o.energy)/max(o.area_xyz,1e-12)
        o.gravity_field=o.energy/max(o.area_xyz**(2.0/3.0),1e-12)
        o.self_fuel=max(0.0,o.self_fuel)
        o.velocity=max(0.0,min(self.c*0.999999,o.velocity))
        self.history.append((name,o.copy()))
        return o

    def genome(self, state, genome):
        current=state.copy()
        for operand in genome: current=self.op(operand,current)
        return current

    def gravity_experiment(self, genome):
        """Run the new expansion/counter-reaction model.

        gravity_field is deliberately named as a simulation field: it is not
        Newtonian gravity and does not claim a new physical law.
        """
        state=State(energy=12.0, mass=1.0, self_fuel=18.0)
        ledger=[]
        for operand in genome:
            before=state.copy()
            state=self.op(operand,state)
            ledger.append({
                'operand':operand,
                'energy_before':before.energy,
                'energy_after':state.energy,
                'area_xyz':state.area_xyz,
                'energy_density':state.energy_density,
                'gravity_field':state.gravity_field,
                'self_fuel':state.self_fuel,
                'velocity':state.velocity,
            })
        return state, ledger

    def score(self,before,after):
        movement=dist(before,after)
        movement_quality=math.exp(-0.18*max(0.0,movement-2.0))
        return (2.0*after.information + 1.5*after.resonance +
                2.0*after.stability + 0.75*(after.information-before.information)+
                0.50*(after.resonance-before.resonance)+movement_quality)

    def mirror(self, genome):
        swaps={'RESO':'UNRESO','UNRESO':'RESO','ORDER':'CHAOS','CHAOS':'ORDER'}
        return [swaps.get(x,x) for x in reversed(genome)]

    def question_from(self, genome, state):
        if state.stability < 0.4:
            return 'Can stability be recovered without reducing information?'
        if state.information < 0.5:
            return 'Which operand increases information with the least disturbance?'
        if state.resonance > 0.7:
            return 'Does the resonance survive reversal and repeated trials?'
        return 'Which transformation is responsible for the largest measurable change?'

    def repeated_trial(self, genome, trials=9):
        """Repeat the same experiment under controlled but different random seeds."""
        records=[]
        for i in range(trials):
            self.rng = random.Random(self.seed+i)
            before=State()
            after=self.genome(before,genome)
            records.append(after)
        scores=[self.score(State(),s) for s in records]
        mean=sum(scores)/len(scores)
        spread=math.sqrt(sum((x-mean)**2 for x in scores)/len(scores))
        stability_mean=sum(s.stability for s in records)/len(records)
        return records, mean, spread, stability_mean

    def experiment(self, genome, trials=9):
        records, mean, spread, stability = self.repeated_trial(genome,trials)
        baseline=records[0]
        shadow_genome=self.mirror(genome)
        shadow_records, shadow_mean, shadow_spread, _=self.repeated_trial(shadow_genome,trials)
        gap=abs(mean-shadow_mean)
        # Repeatability is high when the score spread is small.
        repeatability=1.0/(1.0+spread)
        shadow_repeatability=1.0/(1.0+shadow_spread)
        confidence=repeatability*shadow_repeatability*(1.0-math.exp(-gap))
        question=self.question_from(genome,baseline)
        result={
            'genome':list(genome),'mean':mean,'spread':spread,
            'shadow':shadow_genome,'shadow_mean':shadow_mean,
            'shadow_spread':shadow_spread,'gap':gap,
            'repeatability':repeatability,
            'confidence':confidence,'question':question,
            'state':baseline.copy(),
        }
        self.experiments.append(result)
        return result

    def ask(self, candidates):
        """Select the next question from the most interesting candidate."""
        scored=[]
        for g in candidates:
            result=self.experiment(g)
            scored.append(result)
        scored.sort(key=lambda r:(r['confidence'],r['gap'],r['mean']),reverse=True)
        chosen=scored[0]
        self.questions.append(chosen['question'])
        return chosen, scored

    def promote(self,result,threshold=0.55):
        """Only promote patterns that repeat reliably and have a meaningful shadow gap."""
        if result['confidence'] >= threshold:
            self.memory.append({
                'genome':result['genome'],
                'confidence':result['confidence'],
                'gap':result['gap'],
                'question':result['question'],
            })
            return True
        self.unknown_basin.append(result)
        return False

    def run(self):
        print('AURORA v2.7 — THE GRAVITY WELL ENGINE')
        print('Computational sandbox; repeatability is evidence inside the model, not physical proof.')
        print('Pipeline: ENERGY -> EXPANSION -> COUNTER-REACTION -> GRAVITY-LIKE FIELD -> MEMORY\n')

        candidates=[
            ['ZERO','WAVE','RESO','ORDER'],
            ['ZERO','K2','RESO','MIRROR'],
            ['ZERO','EMC2','WAVE','ORDER'],
            ['ZERO','EMC4','UNRESO','CHAOS'],
            ['ZERO','CHAOS','MIRROR','UNRESO'],
            ['ZERO','PARTICLE','RESO','K2','ORDER'],
            ['ZERO','WAVE','K2','UNRESO','MIRROR'],
            ['ZERO','RESO','K2','RESO','ORDER'],
        ]

        chosen, all_results=self.ask(candidates)
        print('REPEATABILITY FIELD')
        for i,r in enumerate(all_results,1):
            print(f"{i}. conf={r['confidence']:.4f} gap={r['gap']:.4f} spread={r['spread']:.4f} | {r['genome']}")

        print('\nCHOSEN QUESTION')
        print(chosen['question'])
        print('chosen genome:',chosen['genome'])
        print(f"known mean={chosen['mean']:.4f}  shadow mean={chosen['shadow_mean']:.4f}")
        print(f"known spread={chosen['spread']:.4f} shadow spread={chosen['shadow_spread']:.4f}")
        print(f"confidence={chosen['confidence']:.4f}")

        promoted=self.promote(chosen)
        print('\nMEMORY GATE:', 'PROMOTED' if promoted else 'HELD IN UNKNOWN BASIN')
        print('memory:',len(self.memory),'unknown:',len(self.unknown_basin))


        print('\nGRAVITY-WELL EXPERIMENT')
        gravity_genome=['EMC2','EXPAND','EXPAND','SELF_FUEL','EXPAND','ACCEL_C','EXPAND']
        final_state, ledger=self.gravity_experiment(gravity_genome)
        print('genome:',gravity_genome)
        print(f"initial energy=12.0000  final energy={final_state.energy:.4f}")
        print(f"XYZ area={final_state.area_xyz:.4f}")
        print(f"energy density={final_state.energy_density:.4f}")
        print(f"gravity-like field={final_state.gravity_field:.4f}")
        print(f"self-fuel remaining={final_state.self_fuel:.4f}")
        print(f"velocity/c={final_state.velocity/self.c:.6f}")
        print('\nCOUNTER-REACTION LEDGER')
        for row in ledger:
            print(f"{row['operand']:>10} | area={row['area_xyz']:.4f} | density={row['energy_density']:.4f} | field={row['gravity_field']:.4f} | fuel={row['self_fuel']:.4f}")
        print('\nMODEL NOTE: gravity-like field is an Aurora-defined computational quantity, not established physics.')

        print('\nAURORA LEDGER')
        print('1. Do not confuse a high score with truth.')
        print('2. Repeat interesting behavior.')
        print('3. Compare the shadow.')
        print('4. Preserve uncertainty.')
        print('5. Promote only what survives the test.')
        print('\nAurora v2.5 result: the engine now asks what to test next instead of merely ranking what it already tested.')


if __name__=='__main__':
    Aurora().run()
