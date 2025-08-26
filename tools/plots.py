import io
import pickle
import matplotlib as mpl
import pandas as pd
from datetime import datetime
from matplotlib import pyplot as plt, patches as mpatches

class Plots:
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
    def save_plt_fig(cls, fig, filename, bbox_extra_artists=None, ext="png", tight=True, include_timestamp=False, dpi=None, save_pickle=True):
        '''Save a plot figure to file with timestamp'''
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
                        legend=None, color=None, date_axis=False, partial_legend_colours=None, colbar=None, alpha=1):
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
    def multiline_scatter_plot(cls, x, ys, labels, line_labels, output_path, title=None, colours=None, callback=None, legend_title=None):
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
    def categorical_bar_plot(cls, x, y, title, filename, axis_labels=None, y_limits=None):
        '''creates a categorical bar plot'''
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
