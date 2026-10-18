#!/usr/bin/env python3
"""
AURORA IV — CONSTELLATION ENGINE
Dependency-free Python 3

Purpose:
  A multi-observer experimental sandbox with:
    - independent constellation nodes
    - a dedicated Skeptic node
    - null controls
    - Unknown Space exploration
    - Discovery Vault
    - Failure Memory
    - Common Center

This is a simulation framework. It does not establish new physical laws.
"""

import json
import math
import random
import statistics
import time
from dataclasses import dataclass, asdict

SEED = 20260927


def mean(xs):
    return statistics.mean(xs) if xs else 0.0


def sd(xs):
    return statistics.stdev(xs) if len(xs) > 1 else 0.0


def corr(a, b):
    if len(a) != len(b) or not a:
        return 0.0
    ma, mb = mean(a), mean(b)
    da = math.sqrt(sum((x - ma) ** 2 for x in a))
    db = math.sqrt(sum((y - mb) ** 2 for y in b))
    if da == 0 or db == 0:
        return 0.0
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / (da * db)


@dataclass
class Observation:
    node: str
    mode: str
    seed: int
    signal: float
    correlation: float
    information: float
    stability: float
    provenance: str


class FailureMemory:
    def __init__(self):
        self.records = []

    def remember(self, hypothesis, reason, evidence):
        self.records.append({
            "time": time.time(),
            "hypothesis": hypothesis,
            "reason": reason,
            "evidence": evidence,
        })

    def show(self):
        if not self.records:
            print("  Failure Memory: empty")
            return
        for r in self.records[-8:]:
            print(f"  • {r['hypothesis']}: {r['reason']}")


class DiscoveryVault:
    def __init__(self):
        self.items = []

    def add(self, name, status, evidence):
        self.items.append({
            "id": f"D-{len(self.items)+1:04d}",
            "name": name,
            "status": status,
            "evidence": evidence,
        })

    def show(self):
        print("\nDISCOVERY VAULT")
        if not self.items:
            print("  empty")
        for x in self.items:
            print(f"  {x['id']} | {x['status']:12} | {x['name']}")
            print(f"       {x['evidence']}")


class Node:
    def __init__(self, name, role, seed):
        self.name = name
        self.role = role
        self.seed = seed

    def observe(self, x, y, mode):
        r = random.Random(self.seed)
        jitter = r.uniform(-0.02, 0.02)
        c = corr(x, y) + jitter
        signal = abs(c)
        return Observation(
            node=self.name,
            mode=mode,
            seed=self.seed,
            signal=signal,
            correlation=c,
            information=min(1.0, abs(c) * 2.0),
            stability=max(0.0, 1.0 - abs(jitter)),
            provenance="SIMULATION",
        )


class SkepticNode(Node):
    def challenge(self, x, y):
        # Independent randomized-label null test.
        r = random.Random(self.seed + 991)
        shuffled = list(y)
        r.shuffle(shuffled)
        observed = abs(corr(x, y))
        null = abs(corr(x, shuffled))
        return {
            "observed": observed,
            "null": null,
            "survives": observed > max(0.10, null * 1.75),
        }


class CommonCenter:
    def __init__(self):
        self.history = []

    def synthesize(self, observations, challenge):
        signals = [o.signal for o in observations]
        agreement = 1.0 - min(1.0, sd(signals) * 3.0)
        replication = mean(signals)
        return {
            "replication_signal": replication,
            "agreement": agreement,
            "skeptic_survives": challenge["survives"],
            "nodes": len(observations),
        }


class UnknownSpace:
    """Explores combinations without treating novelty as truth."""

    DIMENSIONS = [
        "TIME", "FREQUENCY", "GEOMETRY", "STATISTICS",
        "INFORMATION", "COHERENCE", "SWARM", "NULL"
    ]

    def __init__(self, seed=SEED):
        self.rng = random.Random(seed)

    def generate(self, count=6):
        pairs = []
        for _ in range(count):
            a, b = self.rng.sample(self.DIMENSIONS, 2)
            pairs.append(f"{a} × {b}")
        return pairs


class ConstellationEngine:
    def __init__(self, seed=SEED, nodes=8):
        self.seed = seed
        self.rng = random.Random(seed)
        self.center = CommonCenter()
        self.vault = DiscoveryVault()
        self.failures = FailureMemory()
        self.unknown = UnknownSpace(seed + 77)

        self.nodes = [
            Node(f"AURORA-{i:02d}", "OBSERVER", seed + i * 101)
            for i in range(1, nodes + 1)
        ]
        self.skeptic = SkepticNode("AURORA-08", "SKEPTIC", seed + 808)

    def generate_dataset(self, n=300, candidate=True):
        r = random.Random(self.seed + (17 if candidate else 91))
        x = [r.gauss(0, 1) for _ in range(n)]

        if candidate:
            # Deliberately synthetic nonlinear candidate pattern.
            # It is NOT a claim about nature.
            y = [
                0.30 * (v * v - 1.0) + r.gauss(0, 1)
                for v in x
            ]
        else:
            y = [r.gauss(0, 1) for _ in range(n)]
        return x, y

    def run_experiment(self):
        print("\n=== AURORA IV — CONSTELLATION ENGINE ===")
        print("Lantern status : LIT")
        print("Scientific mode: SIMULATION")
        print("Rule           : pattern ≠ proof\n")

        x, y = self.generate_dataset(candidate=True)

        observations = [
            node.observe(x, y, "CANDIDATE")
            for node in self.nodes
        ]

        challenge = self.skeptic.challenge(x, y)
        synthesis = self.center.synthesize(observations, challenge)
        self.center.history.append(synthesis)

        print("CONSTELLATION OBSERVATIONS")
        for o in observations:
            print(
                f"  {o.node} | corr={o.correlation:+.4f} "
                f"| info={o.information:.3f} | stability={o.stability:.3f}"
            )

        print("\nSKEPTIC NODE")
        print(f"  observed magnitude : {challenge['observed']:.4f}")
        print(f"  randomized null    : {challenge['null']:.4f}")
        print(f"  survives challenge : {challenge['survives']}")

        print("\nCOMMON CENTER")
        for k, v in synthesis.items():
            print(f"  {k:20}: {v}")

        if challenge["survives"]:
            self.vault.add(
                "synthetic nonlinear candidate",
                "CANDIDATE",
                "Replicated in independent simulation nodes; survived one randomized-label challenge."
            )
        else:
            self.failures.remember(
                "synthetic nonlinear candidate",
                "candidate did not survive the skeptic",
                synthesis,
            )

        self.null_experiment()
        self.unknown_space()

    def null_experiment(self):
        print("\nNULL CONTROL")
        x, y = self.generate_dataset(candidate=False)
        obs = [n.observe(x, y, "NULL") for n in self.nodes]
        m = mean([abs(o.correlation) for o in obs])
        print(f"  mean |correlation| : {m:.4f}")
        print("  interpretation     : control measurement, not proof of absence.")

    def unknown_space(self):
        print("\nUNKNOWN SPACE")
        for idea in self.unknown.generate():
            print(f"  ? {idea}")
        print("  Unknown combinations are hypotheses for testing, not discoveries.")

    def challenge_vault(self):
        print("\nCHALLENGE PASS")
        for item in self.vault.items:
            if item["status"] != "CANDIDATE":
                continue

            x, y = self.generate_dataset(candidate=True)
            ch = self.skeptic.challenge(x, y)

            if ch["survives"]:
                item["status"] = "UNDER_TEST"
                item["evidence"] += " Second challenge survived."
            else:
                item["status"] = "REJECTED"
                self.failures.remember(
                    item["name"],
                    "failed a later challenge",
                    ch,
                )

    def report(self):
        print("\n" + "=" * 60)
        print("AURORA IV FLIGHT LOG")
        print("=" * 60)
        self.vault.show()

        print("\nFAILURE MEMORY")
        self.failures.show()

        print("\nCOMMON CENTER HISTORY")
        for i, h in enumerate(self.center.history, 1):
            print(f"  run {i}: {h}")

        print("\nGUIDING RULE")
        print("  Explore boldly. Measure honestly. Remember everything.")
        print("  Never confuse a fascinating pattern with proof.")

    def save(self, filename="aurora_constellation_log.json"):
        data = {
            "engine": "AURORA IV — CONSTELLATION ENGINE",
            "seed": self.seed,
            "vault": self.vault.items,
            "failures": self.failures.records,
            "history": self.center.history,
        }
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"\nSaved: {filename}")


def main():
    engine = ConstellationEngine()
    engine.run_experiment()
    engine.challenge_vault()
    engine.report()
    engine.save()


if __name__ == "__main__":
    main()
