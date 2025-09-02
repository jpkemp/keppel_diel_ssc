'''graph combination'''
import io
import pickle
from math import ceil
from string import ascii_lowercase
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

class PlotCombiner:
    '''graph combining functions'''
    @classmethod
    def rescale_figures(cls, filenames):
        '''combine multiple graphs of one type and re-scale them'''
        models = []
        maxes = []
        for filename in filenames:
            model = pickle.load(open(filename, 'rb'))
            _, _, _, y_max = model.gca().axis()
            models.append(model)
            maxes.append(y_max)

        new_y_max = max(maxes)
        for model in models:
            model.gca().set_ylim((0, new_y_max))

        return models

    @classmethod
    def combine_figures(cls, plots):
        '''combine graphs into one image'''
        bufs = [io.BytesIO() for i in range(len(plots))]
        try:
            images=[]
            for i, fig in enumerate(plots):
                buf = bufs[i]
                fig.savefig(buf, format="png")
                buf.seek(0)
                images.append(Image.open(buf))

            widths, heights = zip(*(i.size for i in images))
            total_width = sum(widths)
            max_height = max(heights)

            new_im = Image.new('RGB', (total_width, max_height))

            x_offset = 0
            for im in images:
                new_im.paste(im, (x_offset,0))
                x_offset += im.size[0]
        finally:
            for buf in bufs:
                buf.close()

        return new_im

    @classmethod
    def get_figures_from_folders(cls, folder_paths, only_include=None):
        '''get graphs from analysis output folders'''
        temp = []
        for path in folder_paths:
            filenames = [x for x in Path(path).iterdir() if (x.is_file() and x.suffix == '.pkl')]
            if only_include is not None:
                filenames = [x for x in filenames if only_include in str(x)]

            temp.append(filenames)

        n = len(temp[0])
        for i in temp:
            assert len(i) == n

        input_paths = list(zip(*temp))

        return input_paths

    @classmethod
    def get_plot_type_from_filename(cls, filenames):
        '''auto-detect plot type'''
        graph_types = []
        for filename in filenames:
            all_sets = [set(x.name.split('_')) for x in filename]
            all_matches = set.intersection(*all_sets)
            graph_types.append("_".join(all_matches))

        return graph_types

    @classmethod
    def combine_plots(cls, folder_paths, output_folder, only_include=None):
        '''wrapper for graph combining process'''
        filenames = cls.get_figures_from_folders(folder_paths, only_include)
        graph_types = cls.get_plot_type_from_filename(filenames)
        for i, graph_set in enumerate(filenames):
            models = cls.rescale_figures(graph_set)
            final_fig = cls.combine_figures(models)
            output_filename = str(output_folder) + f"/combined_{graph_types[i]}.png"
            final_fig.save(output_filename)

    @classmethod
    def combine_images(cls, images, rows=2, imgs_per_row=None, spacing=20, lgd=None, add_lettering_of_size=54):
        n_imgs = len(images)
        if imgs_per_row is None: imgs_per_row = ceil(len(images) / rows)
        mod = n_imgs % imgs_per_row
        final = []
        subset = images
        if mod:
            subset = images[:-mod]
            final = images[-mod:]

        widths, heights = zip(*(i.size for i in subset))
        lgd_width = 0
        if lgd:
            lgd_width += lgd.size[0] + spacing

        max_width = 0
        max_height = 0
        for i in range(0, len(subset), imgs_per_row):
            row_width = sum(widths[i:i+imgs_per_row])
            max_width = max(max_width, row_width)
            max_height += max(heights[i:i+imgs_per_row])

        total_width = max_width + lgd_width
        total_height = ceil(max(heights) * rows) + (rows - 1) * (int(spacing))

        new_im = Image.new('RGB', (total_width, total_height), color="white")
        if add_lettering_of_size:
            font = ImageFont.truetype("NotoSansMono-Regular.ttf", add_lettering_of_size)

        x_offset = 0
        y_offset = 0
        for i, im in enumerate(subset):
            if add_lettering_of_size:
                text_im = ImageDraw.Draw(im)
                text_im.text((0,0), f"({ascii_lowercase[i]})", fill=(0,0,0), font=font)

            if i and rows > 1 and not i % imgs_per_row:
                y_offset += im.size[1] + spacing
                x_offset = 0

            new_im.paste(im, (x_offset,y_offset))
            x_offset += im.size[0]

        n_subset = i + 1
        filler = ceil(im.size[0] * (imgs_per_row - len(final)) / imgs_per_row)
        x_offset = filler
        y_offset += im.size[1] + spacing
        for i, im in enumerate(final):
            if add_lettering_of_size:
                text_im = ImageDraw.Draw(im)
                text_im.text((0,0), f"({ascii_lowercase[n_subset + i]})", fill=(0,0,0), font=font)

            new_im.paste(im, (x_offset,y_offset))
            x_offset += filler

        if lgd:
            x_offset = total_width - lgd_width - spacing
            y_offset = ceil((total_height / 2) - (lgd.size[1] / 2)) + 10
            new_im.paste(lgd, (x_offset,y_offset))

        return new_im
