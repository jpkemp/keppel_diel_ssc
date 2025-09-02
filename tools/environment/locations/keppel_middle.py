import pandas as pd
from datetime import datetime
from overrides import overrides
from zoneinfo import ZoneInfo
from .locations import BaseLocation

class KeppelMiddleIsland(BaseLocation):
    location = (-23.1690437,150.9206769)
    timezone = "Australia/Brisbane"

    @classmethod
    @overrides
    def tide_data(cls, year:int) -> pd.DataFrame:
        '''load tide data for a given year

        year: which year to load

        '''
        def format_time(row):
            temp = row["Date"] + row["Time"]
            return datetime.strptime(temp, "%d/%m/%Y%H:%M").replace(tzinfo=ZoneInfo('Australia/Brisbane'))

        path = f"data/tides/59672_eqspaced_{year}.txt"
        data = pd.read_csv(path, sep=' ', skiprows=11)
        data["dt"] = data.apply(format_time, axis=1)

        return data