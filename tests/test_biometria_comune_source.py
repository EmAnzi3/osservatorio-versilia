import json
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from biometria_comune_config import MUNICIPALITY_ORDER, BAND_IDS, BAND_SUM_TOLERANCE

SOURCE = ROOT / "data/sources/territorio/biometria-comune.json"

class BiometriaComuneSourceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(SOURCE.read_text(encoding="utf-8"))

    def test_scope_is_exactly_seven_versilia_municipalities(self):
        self.assertEqual(list(self.data["municipalities"]), MUNICIPALITY_ORDER)

    def test_eight_altitude_bands(self):
        for row in self.data["municipalities"].values():
            self.assertEqual(list(row["altitudeBandsPct"]), BAND_IDS)

    def test_band_percentages_are_valid(self):
        for name,row in self.data["municipalities"].items():
            values=list(row["altitudeBandsPct"].values())
            self.assertTrue(all(0 <= v <= 100 for v in values), name)
            self.assertLessEqual(abs(sum(values)-100), BAND_SUM_TOLERANCE + 1e-9, name)

    def test_derived_thresholds(self):
        for name,row in self.data["municipalities"].items():
            values=list(row["altitudeBandsPct"].values())
            self.assertEqual(round(sum(values[:2]),1), row["below600Pct"], name)
            self.assertEqual(round(sum(values[1:]),1), row["from300Pct"], name)

    def test_unverified_altimetry_is_not_fabricated(self):
        for row in self.data["municipalities"].values():
            self.assertIsNone(row["altitudeMinM"])
            self.assertIsNone(row["altitudeMeanM"])
            self.assertIsNone(row["altitudeMaxM"])
            self.assertEqual(row["altitudeStatus"], "pending-istat-2021-xlsx")

if __name__ == "__main__":
    unittest.main()
