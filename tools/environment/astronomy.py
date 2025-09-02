from datetime import timedelta
from enum import Enum
from functools import partial
import numpy as np
import pandas as pd
import skyfield.api as sf
from skyfield import almanac
from skyfield.timelib import Time

class SunTransitions(Enum):
    Sunset = 'sunset'
    Sunrise = 'sunrise'
    Transitions = 'transition'

class Astronomy:
    def __init__(self):
        self.ts = sf.load.timescale()
        self.eph = sf.load('de421.bsp')

    def moon_phase_at_date(self, datetime_obj:pd.Series):
        '''Retreives the angle of the moon relative to self.eph at a given datetime or series of datetimes'''
        if hasattr(datetime_obj, '__iter__'):
            t = self.ts.from_datetimes(datetime_obj)
        else:
            t = self.ts.from_datetime(datetime_obj)

        phase = almanac.moon_phase(self.eph, t)

        return phase.degrees

    def find_observer(self, lat, lon):
        '''get astronomy format for the observer position

        lat: latitude
        lon: longitude
        '''
        N = sf.N if lat > 0 else sf.S
        E = sf.E if lon > 0 else sf.W
        lat = abs(lat)
        lon = abs(lon)

        return self.eph["Earth"] + sf.wgs84.latlon(lat * N, lon * E)

    def find_suntimes(self, lat, lon, datetimes, tz=None, func=almanac.find_settings) -> pd.Series:
        '''finds the times of sun events for a series of datetimes at a given location

        lat: latitude
        lon: longitude
        datetimes: list of datetimes
        tz: timezone
        func: which events function to use. defaults to almanac.find_settings (to find sunsets).

        returns: times of relevant events
        '''
        sun = self.eph['Sun']
        observer = self.find_observer(lat, lon)
        start = self.ts.utc(datetimes.min() - timedelta(1))
        end = self.ts.utc(datetimes.max() + timedelta(1))
        t = func(observer, sun, start, end)
        if len(t) == 2 and type(t[1]) != Time:
            t, _ = t

        if tz is None:
            tz = datetimes.iloc[0].tzinfo

        event_times = pd.Series(t.astimezone(tz))

        return event_times

    def find_closest(self, event_times, datetimes):
        '''find the closest sun events for a given series of datetimes'''
        get_closest_time = partial(self.get_closest_time, event_times)
        expanded = datetimes.apply(get_closest_time)

        return expanded

    def get_closest_time(self, transition_times, sample_time):
        '''find the closest sun transition for a given time

        transition times: list of the transition times
        sample_time: the time to find the closest transition to

        '''
        abs_diffs = abs(transition_times - sample_time)
        return transition_times[abs_diffs.idxmin()]

    def get_closest_sun_transition(self, risings, settings, x):
        rise_diffs = abs(risings - x)
        set_diffs = abs(settings - x)
        if rise_diffs.min() < set_diffs.min():
            return (1, risings[rise_diffs.idxmin()])
        else:
            return (-1, settings[set_diffs.idxmin()])

    def find_closest_sun_event_times(self, data, location_col, date_col, set_times:SunTransitions):
        loc_times = {}
        for loc, loc_data in data.groupby(location_col):
            if loc == (None, None): continue
            lat, lon = (float(x) for x in loc)
            if set_times != SunTransitions.Transitions:
                if set_times == SunTransitions.Sunset:
                    func = almanac.find_settings
                elif set_times == SunTransitions.Sunrise:
                    func = almanac.find_risings

                times = self.find_suntimes(lat, lon, loc_data[date_col], func=func)
                loc_times[loc] = times
            else:
                setting_times = self.find_suntimes(lat, lon, loc_data[date_col], func=almanac.find_settings)
                rise_times = self.find_suntimes(lat, lon, loc_data[date_col], func=almanac.find_risings)
                loc_times[loc] = (rise_times, setting_times)

        if set_times != SunTransitions.Transitions:
            transition_times = data.apply(lambda x: self.get_closest_time(loc_times[x[location_col]], x[date_col]), axis=1)
        else:
            transition_times = data.apply(lambda x: self.get_closest_sun_transition(*loc_times[x[location_col]], x[date_col]), axis=1)

        return transition_times

    def scale_day(self, rise_times, set_times, middays, midnights, x):
        def get_closest(diffs, time):
            return time[np.argmin(diffs)]

        rise_diffs = abs(rise_times - x)
        set_diffs = abs(set_times - x)
        midday_diffs = abs(middays - x)
        midnight_diffs = abs(midnights - x)
        pairs = [(rise_diffs, rise_times), (set_diffs, set_times), (midday_diffs, middays), (midnight_diffs, midnights)]
        closests = [get_closest(x, y) for x, y in pairs]
        if x > closests[0] and x <= closests[2]: # between sunrise and midday
            return 25 + (x - closests[0]) / (closests[2] - closests[0])*25
        elif x > closests[2] and x <= closests[1]: # between midday and sunset
            return 50 + (x - closests[2]) / (closests[1] - closests[2])*25
        elif x > closests[1] and x <= closests[3]: # between sunset and midnight
            return 75 + (x - closests[1]) / (closests[3] - closests[1])*25
        elif x > closests[3] and x <= closests[0]: # between midnight and sunrise
            return 0 + (x - closests[3]) / (closests[0] - closests[3])*25
        else:
            raise RuntimeError("My logic is incorrect")

    def find_antipode(self, lat, lon):
        anti_lat = lat * -1
        anti_lon = (180 - lon) * -1 if lon > 0 else (-180 - lon) * -1

        return anti_lat, anti_lon

    def find_scaled_day_percentage(self, data, location_col, date_col):
        loc_times = {}
        for loc, loc_data in data.groupby(location_col):
            if loc == (None, None): continue
            lat, lon = (float(x) for x in loc)
            setting_times = self.find_suntimes(lat, lon, loc_data[date_col], func=almanac.find_settings)
            rise_times = self.find_suntimes(lat, lon, loc_data[date_col], func=almanac.find_risings)
            solar_midday = self.find_suntimes(lat, lon, loc_data[date_col], func=almanac.find_transits)
            opp_lat, opp_lon = self.find_antipode(lat, lon)
            solar_midnight = self.find_suntimes(opp_lat, opp_lon, loc_data[date_col], func=almanac.find_transits)
            loc_times[loc] = (rise_times, setting_times, solar_midday, solar_midnight)

        return data.apply(lambda x: self.scale_day(*loc_times[x[location_col]], x[date_col]), axis=1)
