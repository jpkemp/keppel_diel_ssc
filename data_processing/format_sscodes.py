'''Template for data analyses'''
from datetime import timedelta, datetime
from zoneinfo import ZoneInfo
import pickle
from tqdm import tqdm
import re
import pandas as pd
from tools.environment.locations import KeppelMiddleIsland, KeppelNorthIsland
from tools.environment.astronomy import Astronomy, SunTransitions

def format_coords(x):
    dms_format = "'" in x
    negative = '-' in x
    x = x.replace(' ', '')

    if dms_format:
        x = x.replace('-', '')
        dms =  re.split('[°\'"]', x)
        for i, v in enumerate(dms):
            if v == '':
                dms[i] = 0

        deg, minutes, seconds = dms
        return str((float(deg) + float(minutes)/60 + float(seconds)/(60*60)) * (-1 if negative else 1))
    else:
        return x.replace('°', '').replace("'", '')

def get_matching_site_coords(coords, site, dt):
    mask = (coords["soundtrap"] == int(site)) & (coords['start'] <= dt) & (coords["end"] >= dt)
    ret = []
    for col in ('latitude', 'longitude'):
        loc = coords[mask][col].values.tolist()
        loc = format_coords(loc[0]) if loc else None
        ret.append(loc)

    return tuple(ret)

def convert_sountrap_strings_to_int(sscodes):
    def converter(x):
        filename = str(x).split('/')[-1]
        return int(filename.replace('.json',''))

    for data in sscodes.values():
        data["soundtrap"] = data["soundtrap"].apply(lambda x: converter(x))

def load_tide_data():
    tides = []
    for year in [2021, 2022, 2023]:
        tide_data = KeppelMiddleIsland.tide_data(year)
        tides.append(tide_data)

    all_tides = pd.concat(tides, ignore_index=True)
    all_tides = all_tides[["dt", "Height(m)"]]
    all_tides.columns = ["datetime", "tide_height"]


    return all_tides

def mask_drop_days(df, limit_to_all=False):
    if not limit_to_all:
        earliest = df["datetime"].min()
        latest = df["datetime"].max()
    else:
        earliest = df.groupby("soundtrap").agg({'datetime': 'min'}).max().iloc[0]
        latest = df.groupby("soundtrap").agg({'datetime': 'max'}).min().iloc[0]

    start = earliest + timedelta(days=1)
    end = latest - timedelta(days=1)
    mask = (df["datetime"] >= start)
    mask &= (df["datetime"] <= end)

    return df[mask].copy()

def format_data(input_data="data/keppel_sscodes.pkl", save_data="data/formatted_sscodes.pkl", include_tides=False, include_temperature=False, truncate_drop=False):
    astro = Astronomy()
    with open(input_data, 'rb') as f:
        sscodes = pickle.load(f)

    coords = pd.read_csv("data/keppel/coords.csv")
    coords["start"] = coords["start"].apply(lambda x: datetime.strptime(x, "%d/%m/%y"))
    coords["end"] = coords["end"].apply(lambda x: datetime.strptime(x, "%d/%m/%Y"))
    convert_sountrap_strings_to_int(sscodes)
    new_data = {}
    for band, data in tqdm(sscodes.items()):
        dt = pd.to_datetime(data["timestamp"]).apply(lambda x: x.replace(tzinfo=ZoneInfo('Australia/Brisbane')))
        data["datetime"] = pd.Series(dt)
        data = data.drop_duplicates()
        if truncate_drop:
            data = mask_drop_days(data, limit_to_all=True)
        # could reduce this.. separate table for this data, joined to band data on load...
        # only if all orders are the same
        data["location"] = data.apply(lambda x: get_matching_site_coords(coords, x["soundtrap"], x["timestamp"]), axis=1)
        for transition in list(SunTransitions):
            transition_name = transition.value
            data[transition_name] = astro.find_closest_sun_event_times(data, "location", "datetime", set_times=transition)
            if transition == SunTransitions.Transitions:
                mod = pd.DataFrame(data[transition_name].tolist(), index=data.index, columns=["modifier", transition_name])
                data[transition_name] = mod[transition_name]
                data[f"hours_from_closest_{transition_name}"] =  (data["datetime"] - data[transition_name]) * mod["modifier"]
                data["closest_to"] = mod["modifier"].apply(lambda x: "sunrise" if x == 1 else "sunset")
            else:
                data[f"hours_from_closest_{transition_name}"] =  data["datetime"] - data[transition_name]

        data["scaled_day"] = astro.find_scaled_day_percentage(data, "interp_location", "datetime")
        data['phase'] = astro.moon_phase_at_date(data["datetime"])
        data['time'] = data['datetime'].dt.time
        if include_tides:
            tides = load_tide_data()
            data = pd.merge_asof(data.sort_values('datetime'), tides.sort_values("datetime"), on="datetime", direction="nearest")
            start_date = datetime(2021, 1, 1, tzinfo=ZoneInfo("Australia/Brisbane"))
            end_date = datetime(2024, 1, 1, tzinfo=ZoneInfo("Australia/Brisbane"))
            tide_mask = (data['datetime'] >= start_date) & (data['datetime'] < end_date)
            data = data[tide_mask]

        if include_temperature:
            temperature = KeppelNorthIsland.temperature_data()
            temperature = temperature[["cal_val", "dt"]]
            temperature.columns = ["temperature", "dt"]
            temperature["datetime"] = temperature["dt"].astype(data["datetime"].dtype)
            data = pd.merge_asof(data.sort_values("datetime"), temperature, on="datetime", direction="nearest")

        new_data[band] = data

    if save_data:
        with open(save_data, 'wb') as f:
            pickle.dump(new_data, f)

if __name__ == "__main__":
    format_data(input_data="data/keppel_sscodes.pkl", save_data="data/formatted_sscodes.pkl", include_tides=True, include_temperature=True, truncate_drop=True)