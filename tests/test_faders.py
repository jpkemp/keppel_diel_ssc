import unittest
import matplotlib as mpl
import numpy as np
import pandas as pd
from tools.definitions import blue_fader, three_colour_scale

class TestFaders(unittest.TestCase):
    c1 = '#1a5fb4'
    c2 = '#1f8888'
    c3 = '#26a269'


    def test_blue_fader(self):
        expected = [self.c3, self.c2, self.c1]
        for i, v in enumerate([1, 0 ,-1]):
            self.assertEqual(blue_fader(v), expected[i])

        c1=np.array(mpl.colors.to_rgb(self.c1))
        c2=np.array(mpl.colors.to_rgb(self.c2))
        c3= np.array(mpl.colors.to_rgb(self.c3))
        partial_pos = mpl.colors.to_hex(0.5 * c3 + 0.5 * c2)
        partial_neg = mpl.colors.to_hex(0.5 * c1 + 0.5 * c2)
        self.assertEqual(blue_fader(0.5), partial_pos)
        self.assertEqual(blue_fader(-0.5), partial_neg)

    def test_normalisation(self):
        data = pd.Series([6, 0, -34])
        out = three_colour_scale(data)
        self.assertEqual(out[2], self.c1)
        self.assertEqual(out[1], self.c2)

        c2=np.array(mpl.colors.to_rgb(self.c2))
        c3= np.array(mpl.colors.to_rgb(self.c3))
        mixed = mpl.colors.to_hex((1 - 6/34) * c2 + (6/34) * c3)
        self.assertEqual(out[0], mixed)