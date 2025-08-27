from datetime import datetime
from zoneinfo import ZoneInfo
import unittest
import numpy as np
from tools.environment.astronomy import Astronomy, Phases

class TestAstronomy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.astro = Astronomy()
        cls.tz = ZoneInfo('Australia/Perth')

    def test_moon_phase(self):
        def converter(str):
            dat = datetime.strptime(str, "%Y%m%d").replace(tzinfo=self.tz)
            return dat

        test = {"20250213": Phases.Full,
                "20250310": Phases.First,
                "20250621": Phases.Last,
                "20250923": Phases.New}

        test = {converter(x): y for x, y in test.items()}
        for date, expected in test.items():
            deg = self.astro.moon_phase_at_date(date)
            phase = self.astro.get_closest_moon_phase(deg)
            self.assertEqual(phase, expected)

    def test_day_scale(self):
        rises = np.array([datetime(2025, 3, 1, 6), datetime(2025, 3, 2, 6)])
        sets = np.array([datetime(2025, 3, 1, 18), datetime(2025, 3, 2, 18)])
        middays = np.array([datetime(2025, 3, 1, 12), datetime(2025, 3, 2, 12)])
        midnights = np.array([datetime(2025, 3, 1, 0), datetime(2025, 3, 2, 0)])
        tests = [(datetime(2025, 3, 1, 9), 37.5),
                 (datetime(2025, 3, 2, 18), 75),
                 (datetime(2025, 3, 1, 2), 25/3),
                 (datetime(2025, 3, 1, 13), 50 + 25/6)]
        for test, expected in tests:
            result = self.astro.scale_day(rises, sets, middays, midnights, test)
            self.assertAlmostEqual(result, expected)
