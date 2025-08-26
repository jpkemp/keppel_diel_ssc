import matplotlib as mpl
from matplotlib.cm import tab20
import pandas as pd
import numpy as np

partial_metrics = ['acorr3', 'B', 'lprms', 'lppk']
full_metrics = partial_metrics + ['D']

soundscape_sites = {
    5072: 'Mazie 5072',
    5073: 'Mazie 5073',
    6376: 'Mazie site 2',
    7252: 'Shelving site 1',
    7255: 'Monkey Taylor',
    7257: 'Miall Taylor',
    7259: 'Humpy',
    7262: 'Home Taylor',
    6407: 'Mazie Taylors',
    7254: 'Middle Taylor',
    7256: 'Halfway',
    7258: 'Clam Bay',
    7261: 'Home Cathie'
}

metric_full_names = {
    'acorr3': 'periodicity',
    'B': 'kurtosis',
    'D': 'dissimilarity',
    'lppk': 'peak sound level',
    'lprms': 'RMS sound level'
}

def color_fader(c1, c2, mix=0):
    c1=np.array(mpl.colors.to_rgb(c1))
    c2=np.array(mpl.colors.to_rgb(c2))
    mixed = (1-mix)*c1 + mix*c2

    return mpl.colors.to_hex(mixed)

def three_color_fader(c1, c2, c3, mix=0):
    c1=np.array(mpl.colors.to_rgb(c1))
    c2=np.array(mpl.colors.to_rgb(c2))
    c3= np.array(mpl.colors.to_rgb(c3))
    mixed = (1-mix)*c2 + mix*c3 if mix >= 0 else (1+mix)*c2 + (-mix*c1)

    return mpl.colors.to_hex(mixed)

def blue_fader(mix):
    c1 = '#1a5fb4'
    c2 = '#1f8888'
    c3 = '#26a269'
    return three_color_fader(c1, c2, c3, mix)

def three_colour_scale(temps):
    biggest = max(abs(temps.min()), abs(temps.max()))
    normalised = temps.apply(lambda x: x / biggest)
    colours = normalised.apply(blue_fader)

    return colours

def create_color_gradient(temps):
    def color_fader(mix=0):
        c1='#e93e3a'
        c2='#fff33b'
        c1=np.array(mpl.colors.to_rgb(c1))
        c2=np.array(mpl.colors.to_rgb(c2))
        c3= np.array(mpl.colors.to_rgb('#0343DF'))
        mixed = (1-mix)*c2 + mix*c1 if mix >= 0 else (1+mix)*c2 + (-mix*c3)
        return mpl.colors.to_hex(mixed)

    biggest = max(abs(temps.min()), abs(temps.max()))
    norm_temps = temps.apply(lambda x: x / biggest)

    return norm_temps.apply(color_fader)

def colour_plots(data:pd.DataFrame, band:str, plot_data:list[tuple],
                 colour_groups:list, plotter, labels=("Dim 0", "Dim 1"), temp_colours=False):
    for group_name in colour_groups:
        group_vals = data[group_name].astype("category")
        cat_codes = group_vals.cat.codes
        unique_vals = group_vals.unique()
        nunique = len(unique_vals)
        colors = pd.Series([tab20(float(x)/nunique) for x in cat_codes])
        colors.index = cat_codes.index
        if temp_colours:
            lgd_colors = colors
            colors = three_colour_scale(data[temp_colours])
        else:
            lgd_colors = None

        if group_name == "soundtrap": unique_vals = [soundscape_sites[int(x)] for x in unique_vals]
        for plot_nam, data_to_plot in plot_data:
            if isinstance(data_to_plot, pd.DataFrame):
                data_to_plot = data_to_plot.values
            if temp_colours:
                col_example_mixes = [0.05 * x for x in range(-20, 21)]
                index_vals = [x / 2 + 0.5 for x in col_example_mixes]
                cbars = []
                examples = [(index_vals[i], blue_fader(x)) for i, x in enumerate(col_example_mixes)]
                cbars.append(tuple([data[temp_colours], examples, temp_colours]))
            else:
                cbars = None

            plotter.scatter_plot(data_to_plot[:, 0], data_to_plot[:, 1], labels, f"{band}_{group_name}_{plot_nam}",
                f"SSC {plot_nam} for {band} coloured by {group_name}", color=colors,
                legend=unique_vals, partial_legend_colours=lgd_colors, colbar=cbars, alpha=0.5)

def get_category_colours(data, group_name):
    group_vals = data[group_name].astype("category")
    cat_codes = group_vals.cat.codes
    unique_vals = group_vals.unique()
    nunique = len(unique_vals)
    colors = pd.Series([tab20(float(x)/nunique) for x in cat_codes])
    colors.index = cat_codes.index
    if group_name == "soundtrap": unique_vals = [soundscape_sites[int(x)] for x in unique_vals]

    return colors, unique_vals
