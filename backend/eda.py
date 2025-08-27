from tools.plots import Plots
from tools.definitions import soundscape_sites, full_metrics

def create_boxplots(fltr, data):
    figs = []
    for metric in full_metrics:
        use_data = data
        if metric in ["Dt", "Ds", "D"]:
            use_data = data.dropna(subset=metric)

        Plots.basic_histogram(use_data[metric], f"histogram_{fltr}_{metric}", 10)
        site_plot_data = []
        labels = []
        for site, site_data in use_data.groupby("soundtrap"):
            labels.append(soundscape_sites[site])
            site_plot_data.append(site_data[metric].dropna())

        fig = Plots.create_boxplot_group(site_plot_data, labels, "", f"box_{fltr}_{metric}", ("Site", metric))
        figs.append((metric, fig))

    return figs
