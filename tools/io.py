import pickle
from pathlib import Path

def get_project_root() -> Path:
    return Path(__file__).parent.parent.parent.parent

def pickle_data(data, filename, save_to_data_folder=False) -> None:
    filename = str(filename)
    if filename[-4:] != ".pkl":
        filename = filename + ".pkl"

    if save_to_data_folder:
        filename = get_project_root() / f'data/{filename}'
    else:
        filename = get_project_root() / f'output/{filename}'

    with open(filename, 'wb') as f:
        pickle.dump(data, f)

def unpickle_data(filename, check_data_folder=True):
    filepath = None
    if check_data_folder:
        filepath = get_project_root() / f'data/{filename}'
        if not filepath.is_file():
            filepath = None

    if filepath is None:
        filepath = Path(filename)

    with open(filepath, 'rb') as f:
        data = pickle.load(f)

    return data
