from dataclasses import dataclass
from typing import List, Dict
import math, random

@dataclass
class Signal:
    name: str
    value: float
    confidence: float

class TruthStrip:
    def evaluate(self, candidates: List[Signal]) -> Signal:
        return max(candidates, key=lambda s: s.confidence)

class ShadowStrip:
    def evaluate(self, candidates: List[Signal], chosen: Signal) -> List[Signal]:
        return [s for s in candidates if s.name != chosen.name]

class BridgeStrip:
    def reconcile(self, truth: Signal, shadows: List[Signal]) -> Signal:
        if not shadows:
            return truth
        pressure = sum(s.value * (1 - s.confidence) for s in shadows) / len(shadows)
        value = 0.72 * truth.value + 0.28 * pressure
        confidence = max(0.0, min(1.0, truth.confidence - abs(pressure) * 0.08))
        return Signal("bridge_resolution", value, confidence)

class Quadpole:
    def __init__(self):
        self.past = 0.0
        self.future = 0.0
        self.self_state = 0.0
        self.correction = 0.0

    def update(self, resolved: Signal) -> Dict[str, float]:
        self.past = self.self_state
        self.self_state = 0.64 * self.self_state + 0.36 * resolved.value
        self.future = self.self_state + (self.self_state - self.past)
        self.correction = self.future - resolved.value
        return {"past": self.past, "future": self.future, "self": self.self_state, "correction": self.correction}

class Resolver:
    def resolve(self, bridge: Signal, quadpole: Dict[str, float]) -> Signal:
        value = bridge.value + 0.18 * quadpole["correction"]
        confidence = max(0.0, min(1.0, bridge.confidence - abs(quadpole["correction"]) * 0.05))
        return Signal("final_output", value, confidence)

class StabilityMonitor:
    def score(self, truth: Signal, bridge: Signal, final: Signal, quadpole: Dict[str, float]) -> float:
        coherence = final.confidence
        continuity = 1.0 - min(1.0, abs(quadpole["self"] - quadpole["past"]))
        bridge_load = 1.0 - min(1.0, abs(truth.value - bridge.value))
        return max(0.0, min(1.0, 0.42 * coherence + 0.34 * continuity + 0.24 * bridge_load))

class CoherenceEngine:
    def __init__(self):
        self.truth = TruthStrip()
        self.shadow = ShadowStrip()
        self.bridge = BridgeStrip()
        self.quadpole = Quadpole()
        self.resolver = Resolver()
        self.monitor = StabilityMonitor()

    def step(self, candidates: List[Signal]) -> Dict:
        truth = self.truth.evaluate(candidates)
        shadows = self.shadow.evaluate(candidates, truth)
        bridge = self.bridge.reconcile(truth, shadows)
        q = self.quadpole.update(bridge)
        final = self.resolver.resolve(bridge, q)
        stability = self.monitor.score(truth, bridge, final, q)
        return {"truth": truth, "shadows": shadows, "bridge": bridge, "quadpole": q, "final": final, "stability": stability}

def demo():
    rng = random.Random(7)
    engine = CoherenceEngine()
    for t in range(1, 13):
        candidates = [
            Signal("candidate_A", math.sin(t * 0.30) + rng.gauss(0, 0.03), 0.78 + rng.random() * 0.12),
            Signal("candidate_B", math.cos(t * 0.22) + rng.gauss(0, 0.05), 0.62 + rng.random() * 0.20),
            Signal("candidate_C", math.sin(t * 0.17 + 1.5) + rng.gauss(0, 0.04), 0.55 + rng.random() * 0.25),
        ]
        r = engine.step(candidates)
        print(f"cycle={t:02d} truth={r['truth'].name} final={r['final'].value:.3f} confidence={r['final'].confidence:.3f} stability={r['stability']:.3f}")

if __name__ == "__main__":
    demo()
