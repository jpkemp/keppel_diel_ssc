import unittest
import numpy as np
import pandas as pd
from tools.pandas_mask import build_mask

class TestMaskBuilder(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        x = np.arange(30)
        y = np.arange(30, 60)
        data = pd.DataFrame([x,y]).transpose()
        data.columns = ['x', 'y']
        cls.data = data

    def test_mask_builder(self):
        data = self.data
        test_expected = [
            ({'&': [('x', '>', 15)]}, "x > 15", data['x'] > 15),
            ({'&': [('x', '<', 18), ('y', '>=', 40)]}, '(x < 18) & (y >= 40)', ((data['x'] < 18) & (data['y'] >= 40))),
            ({'|': {"1": [('x', '<', 18)], '2': [('y', '>=', 40)]}}, '(x < 18) | (y >= 40)', ((data['x'] < 18) | (data['y'] >= 40))),
            ({'|': {"&": [('x', '<', 18),
                          ('y', '>=', 40)],
                    'None': [('x', '>', 25)]}},
                '((x < 18) & (y >= 40)) | (x > 25)', (((data['x'] < 18) & (data['y'] >= 40)) | (data['x'] > 25))),
            ({'1': [('x', "[)", 15, 25)]}, '15 <= x < 25', ((data['x'] >= 15) & (data['x'] < 25))),
            ({'1': [('x', "()", 15, 25)]}, '15 < x < 25', ((data['x'] > 15) & (data['x'] < 25))),
            ({'1': [('x', "(]", 15, 25)]}, '15 < x <= 25', ((data['x'] > 15) & (data['x'] <= 25))),
            ({'1': [('x', "[]", 15, 25)]}, '15 <= x <= 25', ((data['x'] >= 15) & (data['x'] <= 25))),
        ]
        for fmask, expected_str, expected_mask in test_expected:
            mask = build_mask(data, fmask)
            self.assertEqual(str(mask), expected_str)
            self.assertEqual(mask.__repr__(), f"MaskRule: {expected_str}")
            self.assertTrue(expected_mask.equals(mask.mask))

