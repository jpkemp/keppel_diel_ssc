import pandas as pd
from matplotlib.cm import tab20
from backend.diel_vector import get_habitat_cover, normalise, get_daily_metrics
from tools.definitions import soundscape_sites
from tools.environment import map_creator as mc
from tools.io import unpickle_data
from tools.plots import Plots

def get_habitat_colours(sites):
    habitat = get_habitat_cover()
    hab_min = habitat.min()
    hab_max = habitat.max()
    habitat_colours = sites.apply(lambda x: Plots.blue_fader(normalise(hab_min, hab_max, habitat[x])))

    return habitat_colours

def get_site_colours(data):
    data['lprms'] = data['lprms'].astype(float)
    data["scaled_group"] = data["scaled_day"].apply(lambda x: int(5*x/25))
    _, labels = get_daily_metrics(data, ['lprms'])
    labels = labels['lprms']
    group_vals = labels.astype("category")
    cat_codes = group_vals.cat.codes
    nunique = group_vals.nunique()
    colors = pd.Series([tab20(float(x)/nunique) for x in cat_codes])

    df = pd.concat([labels, colors], axis=1)
    df.columns = ["labels", "colours"]
    df.groupby(["labels", "colours"]).size().reset_index().drop(0, axis=1)

    return df['colours'].to_list(), df['labels'].to_list()

def create_maps():
    data = unpickle_data("data/formatted_sscodes.pkl")["broad"]
    data["site_names"] = [soundscape_sites[x] for x in data["soundtrap"]]
    locs = data.groupby(["location", "site_names"]).size().reset_index()
    site_colours, labels = get_site_colours(data)
    habitat_colours = get_habitat_colours(locs["site_names"])
    for colours, title in [(site_colours, "site"), (habitat_colours, "habitat")]:
        keppel = mc.get_keppel_shape()
        fig, ax = mc.plot_map_data(keppel)
        ax.ticklabel_format(axis='x', scilimits=(0,0))
        ax.set_xlabel("Longitude", fontsize=18)
        ax.set_ylabel("Latitude", fontsize=18)
        xy = pd.DataFrame(locs["location"].tolist(), index=locs["site_names"])
        xy.columns = ["Lat", "Lon"]
        mc.add_annotations_to_map_plot(ax, xy, keppel.crs, colours)
        if len(colours) <= 11:
            lgd_keys = {locs["site_names"][x]: v for x, v in colours.items()}
        else:
            lgd_keys = {soundscape_sites[labels[i]]: v for  i, v in enumerate(colours)}

        mc.create_map_legend(ax, lgd_keys)
        Plots.save_plt_fig(fig, f"keppel_map_{title}", save_pickle=False)
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        sat_fig, sat_ax = mc.plot_satellite_map(keppel, xy, colours, xlim=xlim, ylim=ylim)
        coords = mc.create_bounding_box(*xlim, *ylim, modifier=1)
        subbox = mc.create_bounding_box(*xlim, *ylim, modifier=0)
        mc.add_australia_inset(sat_ax, coords, subbox)
        mc.create_map_legend(sat_ax, lgd_keys, marker='x', marker_size=15)
        Plots.save_plt_fig(sat_fig, f"keppel_sat_map_{title}", save_pickle=False)

if __name__ == "__main__":
    create_maps()