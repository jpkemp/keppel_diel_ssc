from enum import Enum
import contextily as cx
import geopandas as gpd
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from matplotlib.transforms import Bbox
from shapely import Point, Polygon

class Shapefiles(Enum):
    marine = "data/shapefile/cstauscd_r.mif"
    high_res = "data/shapefile/MB_2021_AUST_SHP_GDA2020/MB_2021_AUST_GDA2020.shp"

def get_boundary_coords(polygons):
    lo_mi = []
    la_mi = []
    lo_ma = []
    la_ma = []
    for poly in polygons.boundary:
        bounds = np.dstack(poly.coords.xy)
        lon_min, lat_min = bounds.min(axis=1)[0]
        lon_max, lat_max = bounds.max(axis=1)[0]
        lo_mi.append(lon_min)
        lo_ma.append(lon_max)
        la_mi.append(lat_min)
        la_ma.append(lat_max)


    coords = [lon_min.min(), lon_max.max(), lat_min.min(), lat_max.max()]

    return coords

def create_bounding_box(lon_min, lon_max, lat_min, lat_max, modifier=0):
    coords = [(lon_min - modifier, lat_min - modifier),
              (lon_min - modifier, lat_max + modifier),
              (lon_max + modifier, lat_max + modifier),
              (lon_max + modifier, lat_min - modifier)]
    box = Polygon(coords)
    gdf = gpd.GeoDataFrame({'name': ['location_box'], 'geometry': [box]})

    return gdf

def get_australia_shape(map_style:Shapefiles=Shapefiles.marine):
    data = gpd.read_file(map_style.value)

    return data

def get_keppel_shape():
    data = get_australia_shape(Shapefiles.marine)

    return data[data["GROUP_NAME"] == "KEPPEL ISLES"].reset_index(drop=True)

def plot_map_data(map_data:pd.DataFrame, title=None, scale_fig=3):
    ax = map_data.plot(figsize=(6.4*scale_fig, 4.8*scale_fig), color="#000000")
    ax.ticklabel_format(useOffset=False, style='plain')
    fig = ax.get_figure()
    fig.set_dpi(300)
    if title is not None:
        fig.suptitle = title

    return fig, ax

def convert_lat_lon_to_markers(lat_lon, crs):
    geometry = lat_lon.apply(lambda x: Point(x["Lon"], x["Lat"]), axis=1)
    points = gpd.GeoDataFrame(lat_lon, geometry=geometry, crs=crs)

    return points

def plot_satellite_map(map_data:pd.DataFrame, lat_lon, colour, title=None, scale_fig=3, xlim=None, ylim=None):
    points = convert_lat_lon_to_markers(lat_lon, map_data.crs)
    ax = points.plot(figsize=(6.4*scale_fig, 4.8*scale_fig), marker="x", markersize=25*scale_fig, c=colour)
    for lim_vals, lim_fun in [(xlim, ax.set_xlim), (ylim, ax.set_ylim)]:
        if lim_vals is not None:
            lim_fun(lim_vals)

    # cx.add_basemap(ax, source=cx.providers.Esri.WorldImagery, crs=map_data.crs, attribution="")
    cx.add_basemap(ax, source=cx.providers.Esri.WorldImagery, crs=map_data.crs)
    fig = ax.get_figure()
    fig.set_dpi(300)
    if title is not None:
        fig.suptitle = title

    return fig, ax

def add_annotations_to_map_plot(ax, lat_lon, crs, color, scale=5):
    points = convert_lat_lon_to_markers(lat_lon, crs)
    points.plot(ax=ax, marker='o', c=color, markersize=6*scale)

def plot_to_inset(ax, shape, size, draw_bounding_box, drop_margins=True):
    inset = ax.inset_axes(size)
    shape.plot(ax=inset, color='tab:brown', linewidth=0, edgecolor='b')
    inset.set_facecolor('b')
    for markers in (inset.get_xaxis(), inset.get_yaxis()):
        markers.set_visible(False)

    if drop_margins:
        inset.margins(0)

    if draw_bounding_box is not None:
        draw_bounding_box.plot(ax=inset, color='none', edgecolor='r')

    return inset

def clip_shape(clip_shape, clip_by, crs):
    for shape in (clip_by, clip_shape):
        if shape.crs is None:
            shape.crs = crs
        else:
            if shape.crs != crs:
                shape.to_crs(crs)

    return clip_shape.clip(clip_by)


def add_australia_inset(ax, box_location=None, subbox=None):
    australia = get_australia_shape(Shapefiles.marine)
    large_inset_coords = (0.5, 0.593, 0.5, 0.5)
    if subbox is None:
        plot_to_inset(ax, australia, large_inset_coords, box_location)
        return

    small_inset_coords = (0.5, 0.53, 0.5, 0.5)
    big_australia = get_australia_shape(Shapefiles.high_res)
    subset = clip_shape(big_australia, box_location, big_australia.crs)
    inset = plot_to_inset(ax, subset, large_inset_coords, subbox)
    plot_to_inset(inset, australia, small_inset_coords, box_location)

def create_map_legend(ax, label_colors:dict, marker='o', marker_size=5):
    custom_lines = []
    for colour in label_colors.values():
        custom_lines.append(Line2D([0], [0], color='w', marker=marker, markersize=marker_size,
                                   markerfacecolor=colour, markeredgecolor=colour, linestyle='None'))

    lgd = ax.legend(custom_lines, list(label_colors.keys()))
    handles = lgd.legendHandles
    labels = [x.get_text() for x in lgd.texts]
    hl = sorted(zip(handles, labels), key=lambda x: x[1])
    handles_sorted, labels_sorted = zip(*hl)
    ax.legend(handles_sorted, labels_sorted, title="Legend", loc='center right', bbox_to_anchor=(1,0.565),
              fontsize=10, title_fontsize=12)

    return lgd
