import pickle
import matplotlib as mpl
from matplotlib.figure import Figure
import numpy as np
import pandas as pd
from datetime import datetime
from matplotlib import pyplot as plt, patches as mpatches

class Plots:
    '''container for plotting functions'''
    #https://clauswilke.com/dataviz/color-pitfalls.html
    default_color_scheme = ['#E69F00',
                            '#56B4E9',
                            '#009E73',
                            "#F0E442",
                            "#0072B2",
                            "#D55E00",
                            "#CC79A7",
                            "#000000"]

    @classmethod
    def save_plt_fig(cls, fig, filename, bbox_extra_artists=None, ext="png",
                     tight=True, include_timestamp=False, dpi=300, save_pickle=True) -> None:
        '''Save a plot figure to file with timestamp.

        fig: figure to save
        filename: output path
        bbox_extra_artists: additional plot elements for formatting
        ext: file type to save
        tight: tight layout
        include_timestamp: whether to include a timestamp as part of the filename. Suggested if multiple runs are to be compared.
        dpi: resolution with which to save the figure
        save_pickle: whether to save a pickle of the figure alongside the image file. Suggested if later editing of the figure is required.

        '''
        current = datetime.now().strftime("%Y%m%dT%H%M%S")
        current = f"_{current}" if include_timestamp else ""
        output_path = f"output/{filename}{current}.{ext}"
        pickle_path = f"{output_path}.pkl"
        if bbox_extra_artists is not None and not tight:
            fig.savefig(output_path, bbox_extra_artists=bbox_extra_artists, bbox_inches='tight', dpi=dpi)
        elif tight:
            fig.savefig(output_path, format=ext, bbox_inches='tight', dpi=dpi)
        else:
            fig.savefig(output_path, format=ext, dpi=dpi)

        if save_pickle:
            with open(pickle_path, 'wb') as f:
                pickle.dump(fig, f)

        plt.close(fig)

    @classmethod
    def scatter_plot(cls, x, y, labels, output_path, title=None, lines=False,
                        legend=None, color=None, date_axis=False, partial_legend_colours=None,
                        colbar=None, alpha=1) -> None:
        '''Create a scatter plot.

        x: data for the x axis
        y: data for the y axis. len(y) must match len(x)
        labels: takes a tuple with axis titles for (x, y)
        output_path: path to save the figure
        title: figure heading
        lines: whether to plot a scatter or line plot
        legend: list with classifications for each point. len(legend) must match len(x)
        color: colours for each point. len(color) must match len(x)
        date_axis: If dates are used as axis tick marks, set this to True to rotate the labels
        partial_legend_colours: used to create a legend with only some classes shown
        colbar: if the legend should be a colour bar instead of class labels, pass in the data to be used
        alpha: alpha blending value for the plot

        '''
        fig = plt.figure(dpi=300)
        ax = fig.add_subplot(111)
        if lines:
            artists = ax.plot(x, y, alpha=alpha)
        elif color is not None:
            if isinstance(color, pd.Series):
                color = color.values.tolist()

            artists = ax.scatter(x, y, c=color, marker='.', alpha=alpha)
        else:
            artists = ax.plot(x, y, linestyle="None", marker=".", alpha=alpha)

        ax.set_xlabel(labels[0])
        if date_axis:
            fig.autofmt_xdate(rotation=45)
        ax.set_ylabel(labels[1])
        extra = None
        if title is not None:
            ttl = fig.suptitle(title)
            extra = (ttl,)
        if legend is not None and colbar is None:
            if color:
                if partial_legend_colours is not None:
                    color = partial_legend_colours

                patches = cls._get_color_patches(color, legend)
                lgd = ax.legend(handles=patches, title="Legend", loc='center left', bbox_to_anchor=(1,0.5))
            else:
                lgd = ax.legend(labels=legend, title="Legend", loc='center left', bbox_to_anchor=(1,0.5))
            extra = (lgd,)
        if (legend is not None and colbar is None) and title:
            extra = (ttl, lgd,)
        if colbar:
            def create_colbar(one_bar, extra=None):
                norm, cmap, col_ttl = one_bar
                norm = mpl.colors.Normalize(min(norm), max(norm))
                cmap = mpl.colors.LinearSegmentedColormap.from_list('custom', cmap)
                mpbl = mpl.cm.ScalarMappable(norm=norm, cmap=cmap)
                cbar = fig.colorbar(mpbl, ax=ax, orientation='vertical', label=col_ttl)
                if extra:
                    extra = tuple([x for x in extra] + [cbar])
                else:
                    extra = (cbar,)

                return extra

            if isinstance(colbar, list):
                for b in colbar:
                    extra = create_colbar(b, extra)
            else:
                extra = create_colbar(colbar, extra)


        cls.save_plt_fig(fig, output_path, bbox_extra_artists=extra, save_pickle=False)

        return fig

    @classmethod
    def _get_color_patches(cls, color, legend):
        '''create colour patches for the legend. internal use only
        '''
        seen = set()
        patches = []
        for c in color:
            if c not in seen:
                i = len(seen)
                patch = mpatches.Patch(color=c, label=legend[i])
                patches.append(patch)
                seen.add(c)

        return patches

    @classmethod
    def multiline_scatter_plot(cls, x, ys, labels, line_labels, output_path, title=None,
                               colours=None, callback=None, legend_title=None) -> Figure:
        ''' create a multiline scatter plot.

        x: data for the x axis
        ys: data for the y axis, in nested list format where each element is the data for a new line.
        labels: takes a tuple with axis titles for (x, y)
        line_labels: labels for the legend, in order of ys
        output_path: path to save the figure
        title: figure heading
        colours: colour for each line, in order of ys
        callback: function for post-processing the figure
        legend_title: heading for the legend box

        '''
        fig = plt.figure()
        ax = fig.add_subplot(111)
        colours = colours if colours else cls.default_color_scheme
        for i, y in enumerate(ys):
            ax.plot(x, y, color=colours[i], label=line_labels[i])

        ax.set_xlabel(labels[0])
        ax.set_ylabel(labels[1])
        ax.tick_params(axis='x', labelrotation=90)
        lgd = ax.legend(title="Legend" if legend_title is None else legend_title, loc='center left', bbox_to_anchor=(1,0.5))

        if callback is not None:
            fig, ax, lgd = callback(fig, ax, lgd)

        if title is not None:
            ttl = fig.suptitle(title)

        cls.save_plt_fig(fig, output_path, bbox_extra_artists=(lgd,), tight=True, save_pickle=False)

    @classmethod
    def categorical_bar_plot(cls, x, y, title, filename, axis_labels=None, y_limits=None) -> Figure:
        '''creates a categorical bar plot

        x: bar labels
        y: data for each bar. len(y) must match len(x)
        title: figure heading
        filename: path to save the figure
        axis_labels: takes a tuple with axis titles for (x, y)
        y_limits: tuple of(min, max) to set the y range

        '''
        fig = plt.figure()
        ax = fig.add_subplot(111)
        assert len(x) == len(y)
        ax.bar(x, y)
        ax.tick_params(axis='x', labelrotation=45)
        if y_limits is not None:
            ax.set_ylim(y_limits)

        lgd = ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        ttl = fig.suptitle(title)
        if axis_labels is not None:
            ax.set_xlabel(axis_labels[0])
            ax.set_ylabel(axis_labels[1])

        cls.save_plt_fig(fig, filename, (lgd, ttl, ), save_pickle=False)

        return fig

    @classmethod
    def basic_histogram(cls, data, filename, n_bins="unique_values",
                        title=None, xlabel="Count", ylabel="Frequency") -> None:
        '''creates and saves a histogram

        data: vector/series/list of values
        filename: filename for the image
        n_bins: number of histogram bins. if n_bins == "unique_values", shows the frequency of each individual value.
        title: figure title
        xlabel: x axis label
        ylabel: y axis label

        '''
        if n_bins == "unique_values":
            n_bins = len(set(data))

        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.hist(data, n_bins, edgecolor='black', linewidth=1.2)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        if title is not None:
            ttl = fig.suptitle(title)

        cls.save_plt_fig(fig, filename)

    @classmethod
    def create_boxplot_group(cls, data, labels, title, filename, axis_labels=None,
                             show_outliers=True, figsize=(6.4, 4.8), ext="png") -> Figure:
        '''creates and saves a group of boxplots

        data: dataframe of the data to plot
        labels: Label for each boxplot. len(labels) match the number of columns in data
        title: figure title
        filename: for the saved figure
        axis_labels: axis labels in (x, y) format
        show_outliers: if True, outliers will be shown as circles outside the boxplot quartiles
        figsize: figure dimensions (x, y) in inches
        ext: file type extension

        '''
        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(111)
        ax.boxplot(data, showfliers=show_outliers)
        fig.suptitle(title)
        ax.set_xticklabels(labels, rotation=45, ha='right')
        if axis_labels is not None:
            ax.set_xlabel(axis_labels[0])
            ax.set_ylabel(axis_labels[1])

        cls.save_plt_fig(fig, filename, ext=ext, tight=True)

        return fig

    @classmethod
    def color_fader(cls, c1:str, c2:str, mix:float=0) -> str:
        '''mixes two colours proportionally on a range [0, 1] and returns a hex colour string

        c1: colour 1 in hex format
        c2: colour 2 in hex format
        mix: mix as a proportion 0-1, with 0 favouring colour 1 and 1 favouring colour 2

        '''
        c1=np.array(mpl.colors.to_rgb(c1))
        c2=np.array(mpl.colors.to_rgb(c2))
        mixed = (1-mix)*c1 + mix*c2

        return mpl.colors.to_hex(mixed)

    @classmethod
    def three_color_fader(cls, c1:str, c2:str, c3:str, mix:float=0) -> str:
        '''mixes three colours proportionally on a range [-1, 1] and returns a hex colour string

        c1: colour 1 in hex format
        c2: colour 2 in hex format
        c3: colour 3 in hex format
        mix: mix as a proportion 0-1, with 1 favouring colour 3, 0 favouring colour 2, and -1 favouring colour 1

        '''
        c1=np.array(mpl.colors.to_rgb(c1))
        c2=np.array(mpl.colors.to_rgb(c2))
        c3= np.array(mpl.colors.to_rgb(c3))
        mixed = (1-mix)*c2 + mix*c3 if mix >= 0 else (1+mix)*c2 + (-mix*c1)

        return mpl.colors.to_hex(mixed)

    @classmethod
    def blue_fader(cls, mix:float) -> str:
        '''mixes colours proportionally on a blue-green scale and returns a hex colour string

        mix: the proportion, as per three-colour fader

        '''
        c1 = '#1a5fb4'
        c2 = '#1f8888'
        c3 = '#26a269'
        return cls.three_color_fader(c1, c2, c3, mix)

    @classmethod
    def three_colour_scale(cls, temps:pd.Series) -> pd.Series:
        ''' normalises data and mixes using blue_fader and returns a series of hex colour strings

        temps: vector of mixes

        '''
        biggest = max(abs(temps.min()), abs(temps.max()))
        normalised = temps.apply(lambda x: x / biggest)
        colours = normalised.apply(cls.blue_fader)

        return colours