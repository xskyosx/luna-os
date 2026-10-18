#!/usr/bin/env python3
"""
AURORA v2.3 — OPERAND GENOME
Pure Python 3 / no external packages.

A computational sandbox for exploring user-defined operands.
Physics-like names here are simulation constructs; EMC4 is explicitly
an experimental computational transform, not established physics.
"""
import math
import random
from dataclasses import dataclass
from typing import List, Tuple


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

    def copy(self):
        return State(**self.__dict__)


def dist(a: State, b: State) -> float:
    keys = ('energy', 'x', 'y', 'phase', 'amplitude',
            'information', 'resonance', 'stability')
    return math.sqrt(sum((getattr(a, k) - getattr(b, k)) ** 2 for k in keys))


class Aurora:
    OPERANDS = [
        'ZERO', 'ADD', 'SUB', 'MUL', 'DIV', 'EMC2', 'EMC4',
        'RESO', 'UNRESO', 'MIRROR', 'PARTICLE', 'WAVE',
        'CHAOS', 'ORDER', 'K2', 'OBSERVE'
    ]

    def __init__(self, seed=20260911, c=3.0):
        self.rng = random.Random(seed)
        self.c = c
        self.checkpoints = {}
        self.history = []
        self.missing = []
        self.archive = []

    def save(self, name, state):
        self.checkpoints[name] = state.copy()
        self.history.append(('CHECKPOINT:' + name, state.copy()))

    def undo(self, name):
        state = self.checkpoints[name].copy()
        self.history.append(('UNDO:' + name, state.copy()))
        return state

    def redo(self, name):
        state = self.checkpoints[name].copy()
        self.history.append(('REDO:' + name, state.copy()))
        return state

    def jump(self, name):
        state = self.checkpoints[name].copy()
        self.history.append(('JUMP:' + name, state.copy()))
        return state

    def op(self, name, state):
        o = state.copy()
        if name == 'ZERO':
            o.energy = 0.0
        elif name == 'ADD':
            o.energy += 1.0
        elif name == 'SUB':
            o.energy -= 1.0
        elif name == 'MUL':
            o.energy *= 1.25
        elif name == 'DIV':
            o.energy /= 1.25
        elif name == 'EMC2':
            o.energy = o.mass * self.c ** 2
        elif name == 'EMC4':
            o.energy = o.mass * self.c ** 4
        elif name == 'RESO':
            o.resonance = 0.5 + 0.5 * math.sin(o.phase)
            o.information += 0.15 * o.resonance
        elif name == 'UNRESO':
            o.resonance = 1.0 - o.resonance
            o.stability *= 0.98
        elif name == 'MIRROR':
            o.x, o.y, o.phase = -o.x, -o.y, -o.phase
        elif name == 'PARTICLE':
            o.x = o.amplitude * math.cos(o.phase)
            o.y = o.amplitude * math.sin(o.phase)
        elif name == 'WAVE':
            o.amplitude = math.sqrt(abs(o.energy) + 1e-12)
            o.phase = math.atan2(o.y, o.x)
        elif name == 'CHAOS':
            o.x += self.rng.gauss(0, 0.12)
            o.y += self.rng.gauss(0, 0.12)
            o.phase += self.rng.gauss(0, 0.18)
            o.stability *= 0.95
        elif name == 'ORDER':
            o.x *= 0.85
            o.y *= 0.85
            o.phase *= 0.85
            o.stability = min(1.0, o.stability + 0.04)
        elif name == 'K2':
            # User-defined computational K2 / kaos operand.
            o.x, o.y = -o.x, -o.y
            o.resonance = 0.5 + 0.5 * math.cos(2.0 * o.phase)
            o.information += 0.10 * o.resonance
        elif name == 'OBSERVE':
            o.observed = True
            o.information += 0.05
            o.stability *= 0.995
        else:
            raise ValueError('Unknown operand: ' + name)

        o.information = max(0.0, min(10.0, o.information))
        o.stability = max(0.0, min(1.0, o.stability))
        self.history.append((name, o.copy()))
        return o

    def orbit(self, state, a=1.0, b=0.62, steps=8):
        o = state.copy()
        points = []
        for i in range(steps):
            t = 2.0 * math.pi * i / steps
            points.append((a * math.cos(t), b * math.sin(t)))
        o.x, o.y = points[1]
        o.phase = 2.0 * math.pi / steps
        o.amplitude = math.hypot(o.x, o.y)
        return o, points

    def genome(self, state, genome):
        current = state.copy()
        for operand in genome:
            current = self.op(operand, current)
        return current

    def illumination_score(self, before, after):
        """Higher is better: information + resonance + stability - instability."""
        info_gain = after.information - before.information
        resonance_gain = after.resonance - before.resonance
        stability_term = after.stability
        movement = dist(before, after)
        # A moderate movement is rewarded; enormous jumps are treated as noise.
        movement_quality = math.exp(-0.18 * max(0.0, movement - 2.0))
        score = (
            2.0 * after.information
            + 1.5 * after.resonance
            + 2.0 * stability_term
            + 0.75 * info_gain
            + 0.50 * resonance_gain
            + movement_quality
        )
        return score

    def mutate(self, genome, rate=0.30):
        child = list(genome)
        if self.rng.random() < rate:
            i = self.rng.randrange(len(child))
            child[i] = self.rng.choice(self.OPERANDS)
        if self.rng.random() < rate and len(child) < 8:
            i = self.rng.randrange(len(child) + 1)
            child.insert(i, self.rng.choice(self.OPERANDS))
        if self.rng.random() < rate and len(child) > 2:
            child.pop(self.rng.randrange(len(child)))
        return child

    def mirror_run(self, state, genome):
        """Run a genome and its mirrored reverse; compare endpoint symmetry."""
        forward = self.genome(state, genome)
        mirrored = self.genome(state, list(reversed(genome)))
        symmetry_gap = dist(forward, mirrored)
        return forward, mirrored, symmetry_gap

    def integrity_gate(self, before, after, genome):
        """Reject candidates that become numerically unstable or lose too much stability."""
        finite = all(math.isfinite(v) for v in (
            after.energy, after.x, after.y, after.phase,
            after.amplitude, after.information, after.resonance,
            after.stability))
        stability_ok = after.stability >= max(0.0, before.stability - 0.30)
        return finite and stability_ok and bool(genome)

    def find_missing_operand(self, before, target, genome):
        """Try one-step repairs when replaying a path does not recover the target."""
        replay = self.genome(before, genome)
        baseline = dist(replay, target)
        best = (baseline, None)
        for candidate in self.OPERANDS:
            trial = self.op(candidate, replay)
            error = dist(trial, target)
            if error < best[0]:
                best = (error, candidate)
        if best[1] is not None and best[0] + 1e-9 < baseline:
            self.missing.append({
                'base_error': baseline,
                'repaired_error': best[0],
                'candidate': best[1],
            })
        return best

    def evolve(self, seed_genome, generations=8, population=18):
        """Small deterministic evolutionary search for illuminated genomes."""
        population_genomes = [list(seed_genome)]
        while len(population_genomes) < population:
            population_genomes.append(self.mutate(seed_genome, rate=0.9))

        root = State()
        for generation in range(generations):
            scored = []
            for genome in population_genomes:
                result = self.genome(root, genome)
                score = self.illumination_score(root, result)
                integrity = self.integrity_gate(root, result, genome)
                if integrity:
                    scored.append((score, genome, result))
            scored.sort(key=lambda item: item[0], reverse=True)
            if not scored:
                break
            elites = scored[:max(2, population // 4)]
            for score, genome, result in elites[:3]:
                self.archive.append({
                    'generation': generation,
                    'score': score,
                    'genome': list(genome),
                    'state': result.copy(),
                })
            next_population = [list(item[1]) for item in elites]
            while len(next_population) < population:
                parent = self.rng.choice(elites)[1]
                next_population.append(self.mutate(parent, rate=0.65))
            population_genomes = next_population

        self.archive.sort(key=lambda item: item['score'], reverse=True)
        return self.archive[:5]

    def triad_jump(self, triad, name):
        return [self.jump(name) for _ in triad]

    def run(self):
        print('AURORA v2.3 — OPERAND GENOME')
        print('Computational sandbox; EMC4 is experimental, not established physics.')
        print('New: mutation, illumination scoring, mirror runs, integrity gate, missing-operand repair.\n')

        root = State()
        self.save('R0', root)

        # 1) Preserve the earlier universal operand field.
        e2 = self.op('EMC2', root)
        e4 = self.op('EMC4', root)
        print(f'EMC2={e2.energy:.3f}  EMC4={e4.energy:.3f}')

        orbit_state, points = self.orbit(root)
        print('ellipse sample=', tuple(round(v, 4) for v in points[1]))

        # 2) Three independent zero-energy branches.
        triad = [State(), State(), State()]
        genomes = [
            ['ZERO', 'K2', 'RESO', 'MIRROR'],
            ['ZERO', 'EMC2', 'WAVE', 'ORDER'],
            ['ZERO', 'EMC4', 'UNRESO', 'CHAOS'],
        ]
        for i, genome in enumerate(genomes):
            result = self.genome(triad[i], genome)
            self.save('A' + str(i + 1), result)
            print(
                f'branch {i+1}: {genome} -> '
                f'E={result.energy:.3f} I={result.information:.3f} '
                f'R={result.resonance:.3f} S={result.stability:.3f}'
            )

        # 3) Mirror-of-the-mirror experiment.
        seed = ['ZERO', 'WAVE', 'RESO', 'K2', 'MIRROR', 'ORDER']
        forward, mirrored, gap = self.mirror_run(State(), seed)
        print(f'mirror gap={gap:.6f}  forward_R={forward.resonance:.3f}  reverse_R={mirrored.resonance:.3f}')

        # 4) Genome evolution: Aurora searches its own operand combinations.
        winners = self.evolve(['ZERO', 'WAVE', 'RESO', 'ORDER'], generations=8, population=18)
        print('\nTOP ILLUMINATED GENOMES')
        for rank, item in enumerate(winners, 1):
            s = item['state']
            print(
                f'{rank}. score={item["score"]:.4f} | {item["genome"]} | '
                f'I={s.information:.3f} R={s.resonance:.3f} S={s.stability:.3f}'
            )

        # 5) Missing-state repair demonstration.
        target = self.genome(State(), ['ZERO', 'WAVE', 'RESO', 'ORDER'])
        repair = self.find_missing_operand(State(), target, ['ZERO', 'WAVE', 'ORDER'])
        print(f'\nmissing-operand repair: candidate={repair[1]} error={repair[0]:.6f}')

        # 6) Atomic triad jump.
        print('JUMP-3:', [x.energy for x in self.triad_jump(triad, 'R0')])
        print('Archive size:', len(self.archive), 'Missing repairs:', len(self.missing))
        print('History records:', len(self.history))
        print('\nAurora result: the system does not declare a discovery; it ranks computational patterns for further observation.')


if __name__ == '__main__':
    Aurora().run()
