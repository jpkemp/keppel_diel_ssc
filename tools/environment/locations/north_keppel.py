from overrides import overrides
import pandas as pd
from .keppel_middle import KeppelMiddleIsland

class KeppelNorthIsland(KeppelMiddleIsland):
    location = (-23.073258,150.8951901)

    @classmethod
    @overrides
    def temperature_data(cls) -> pd.DataFrame:
        '''load the north keppel island temperature data'''
        temp_data = pd.read_csv("data/temperature/NKEPPSL1_Temperature.csv")
        time_col = "time"
        dt = pd.to_datetime(temp_data[time_col])
        temp_data["dt"] = cls.localise_time_series(dt, cls.timezone)

        return temp_data
