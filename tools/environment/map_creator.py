import pandas as pd
import geopandas as gpd
from matplotlib.lines import Line2D
from shapely import Point

def get_keppel_shape():
    path = "data/shapefile/cstauscd_r.mif"
    data = gpd.read_file(path)
    data.plot()

    return data[data["GROUP_NAME"] == "KEPPEL ISLES"].reset_index(drop=True)

def plot_map_data(map_data:pd.DataFrame, title=None, scale_fig=3):
    ax = map_data.plot(figsize=(6.4*scale_fig, 4.8*scale_fig), color="#000000")
    ax.ticklabel_format(useOffset=False, style='plain')
    fig = ax.get_figure()
    fig.set_dpi(300)
    if title is not None:
        fig.suptitle = title

    return fig, ax

def add_annotations_to_map_plot(ax, x, y, crs, color, scale=5):
    points = pd.DataFrame([x, y]).transpose()
    points.columns = ["Lon", "Lat"]
    geometry = points.apply(lambda x: Point(x["Lon"], x["Lat"]), axis=1)
    points = gpd.GeoDataFrame(points, geometry=geometry, crs=crs)
    points.plot(ax=ax, marker='o', c=color, markersize=6*scale)

def create_map_legend(ax, label_colors:dict):
    custom_lines = []
    for colour in label_colors.values():
        custom_lines.append(Line2D([0], [0], color='w', marker='o', markersize=5, markerfacecolor=colour))

    lgd = ax.legend(custom_lines, list(label_colors.keys()))
    handles = lgd.legendHandles
    labels = [x.get_text() for x in lgd.texts]
    hl = sorted(zip(handles, labels), key=lambda x: x[1])
    handles_sorted, labels_sorted = zip(*hl)
    ax.legend(handles_sorted, labels_sorted, title="Legend", loc='center left', bbox_to_anchor=(1,0.5), fontsize=18, title_fontsize=18)

    return lgd
