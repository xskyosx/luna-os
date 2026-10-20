"""Static portability and deterministic-seeding checks for Aurora scripts."""
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class AuroraPortabilityTests(unittest.TestCase):
    def test_aurora_xlii_uses_fixed_kind_offsets_not_python_hash(self):
        source = (ROOT / "aurora_xlii.py").read_text(encoding="utf-8")
        self.assertIn('"perturbed": 101', source)
        self.assertIn('"rebirth": 202', source)
        self.assertIn('"mirror_reset": 303', source)
        self.assertIn("KIND_OFFSETS[kind]", source)
        self.assertNotIn("hash(kind)", source)

    def test_aurora_outputs_are_relative_to_the_project(self):
        for name in ("aurora_xlii.py", "aurora_xl.py"):
            with self.subTest(script=name):
                source = (ROOT / name).read_text(encoding="utf-8")
                self.assertNotIn("/mnt/data", source)
                self.assertIn('Path(__file__).resolve().parent / "results"', source)

    def test_experiments_label_themselves_as_simulations(self):
        xlii = (ROOT / "aurora_xlii.py").read_text(encoding="utf-8")
        xl = (ROOT / "aurora_xl.py").read_text(encoding="utf-8")
        self.assertIn("not evidence about physical particles or quantum systems", xlii)
        self.assertIn("does not establish claims about physical quantum systems", xl)


if __name__ == "__main__":
    unittest.main()
