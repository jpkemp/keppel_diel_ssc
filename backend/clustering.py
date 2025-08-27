from multiprocessing import Pool
from matplotlib.cm import tab20
import pandas as pd
from tools.ml import pca_nd
from tools.process_dataframe import soundscape_sites
from tools.plots import Plots

def dimension_reduction(data:pd.DataFrame, band:str):
    metrics = ['lppk', 'lprms', 'acorr3', 'B', 'D']
    partial_data = data[metrics].dropna()
    pca, _, _ = pca_nd(partial_data)
    plot_data = [("PCA", pca)]
    figs = colour_plots(data.loc[partial_data.index], band, plot_data)

    return band, figs[0]

def colour_plots(data:pd.DataFrame, band:str, plot_data:list[tuple]):
    ret = []
    group_vals = data['soundtrap'].astype("category")
    cat_codes = group_vals.cat.codes
    unique_vals = group_vals.unique()
    nunique = len(unique_vals)
    colors = [tab20(float(x)/nunique) for x in cat_codes]
    for plot_nam, data_to_plot in plot_data:
        if isinstance(data_to_plot, pd.DataFrame):
            data_to_plot = data_to_plot.values

        fig = Plots.scatter_plot(data_to_plot[:, 0], data_to_plot[:, 1],
            ("Dim 0", "Dim 1"), f"{band}_{plot_nam}",
            "", color=colors, legend=unique_vals)
        ret.append(fig)

    return ret

def clustering(sscodes, n_processes):
    if n_processes:
        with Pool(min(n_processes, len(sscodes))) as pool:
            ret = [pool.apply_async(dimension_reduction,
                                    args=(sscodes[name], name)) for name in sscodes]
            res = [r.get() for r in ret]
    else:
        res = []
        for name, data in sscodes.items():
            fig = dimension_reduction(data, name)
            res.append(fig)

    return res

def convert_sountrap_strings_to_int(sscodes):
    def converter(x):
        filename = str(x).split('/')[-1]
        return int(filename.replace('.json',''))

    for data in sscodes.values():
        data["soundtrap"] = data["soundtrap"].apply(lambda x: soundscape_sites[converter(x)])

