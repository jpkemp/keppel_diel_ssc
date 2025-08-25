'''Template for data analyses'''
from datetime import datetime, timedelta
from pathlib import Path
from multiprocessing import Pool
from numpy import NaN
import pandas as pd
import soundscapecode as ssc
from tqdm import tqdm
from tools.io import pickle_data

def convert_ssc_to_rows(sscode:ssc.SoundscapeCode, soundtrap:str|int, timestamp:datetime):
    seriess = []
    for i, pk in enumerate(sscode.Lppk):
        try:
            spectral = sscode.spectral_dissimilarities[i]
            temporal = sscode.temporal_dissimilarities[i]
            dissimilarity = sscode.dissimilarities[i]
        except IndexError:
            spectral = NaN
            temporal = NaN
            dissimilarity = NaN

        row = [soundtrap, timestamp, pk, sscode.Lprms[i], sscode.periodicity[i], sscode.kurtosis[i],
                spectral, temporal, dissimilarity]
        seriess.append(pd.Series(row, index=["soundtrap", "timestamp", "lppk", 'lprms', 'acorr3', 'B',
                                                "Ds", "Dt", "D"]))
        timestamp = timestamp + timedelta(minutes=1)

    return pd.concat(seriess, axis=1).transpose()

def calculate_ssc_from_file(fl):
    soundtrap, stamp = fl.stem.split('.')
    soundtrap_path = Path(f"data/calibration/{soundtrap}.json")
    soundtrap = str(soundtrap_path) if soundtrap_path.exists() else int(soundtrap)
    try:
        stamp = datetime.strptime(stamp, "%y%m%d%H%M%S")
    except ValueError:
        print(f"Date conversion failed for {fl}")
        stamp = datetime(2000, 1, 1, 1, 1, 1)

    fs, sound = ssc.soundtrap.open_wav(fl, soundtrap=soundtrap)
    ret = {}
    for name, bands in [("broad", (200, fs / 2)),
                        ("fish", (200,800)),
                        ("invertebrate", (2000, 5000))]:
        try:
            fltr = ssc.filters.highpass if name == "broad" else ssc.filters.bandpass
            band = bands[0] if name == "broad" else bands
            fltrd_sound = fltr(sound, band, fs)
            sscode = ssc.SoundscapeCode(fltrd_sound, fs, bands)
        except ValueError as e:
            print(f"Failed to calculate {fl} {name}")
            print(e)
            sscode = None

        soundtrap_name = soundtrap_name_converter(soundtrap)
        df = convert_ssc_to_rows(sscode, soundtrap_name, stamp) if sscode is not None else None
        ret[name] = df

    pickle_data(ret, f"ssc_{fl.stem}")
    return ret

def pool_ssc(sound_files, n_processes):
    with Pool(n_processes) as pool, tqdm(total=len(sound_files)) as pbar:
        ret = [pool.apply_async(calculate_ssc_from_file, args=(i,),
                                callback=lambda _:pbar.update(1)) for i in sound_files]
        res = [r.get() for r in ret if r]

    return res

def soundtrap_name_converter(sountrap_name):
    filename = str(sountrap_name).split('/')[-1]
    return int(filename.replace('.json',''))

def convert_sountrap_strings_to_int(self, sscodes):
    for data in sscodes.values():
        data["soundtrap"] = data["soundtrap"].apply(self.soundtrap_name_converter)

if __name__ == "__main__":
    print("Getting soundscape code")
    data_folder = Path(f"data/sound_recordings")
    sound_files = [x for x in data_folder.glob('**/*.[Ww][Aa][Vv]')]
    n_processes = 6
    if n_processes:
        results = pool_ssc(sound_files, n_processes)
    else:
        results = [calculate_ssc_from_file(fl) for fl in tqdm(sound_files)]

    ret = {}
    for name in ["broad", "fish", "invertebrate"]:
        current = [x[name] for x in results if x[name] is not None]
        sscodes = pd.concat(current).reset_index(drop=True)
        ret[name] = sscodes

    pickle_data(ret, "sscodes", save_to_data_folder=True)
