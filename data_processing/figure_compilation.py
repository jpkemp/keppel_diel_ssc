from pathlib import Path
from PIL import Image
from plot_combiner import PlotCombiner

def combine_images(combiner:PlotCombiner, fls, name, nrows=3, fontsize=54):
    output_path = f"output/{name}"
    imgs = [Image.open(x) for x in fls]
    img = combiner.combine_images(imgs, rows=nrows, add_lettering_of_size=fontsize)
    img.save(output_path, dps=300)

if __name__ == "__main__":
    combiner = PlotCombiner()
    input_path = Path("output/")
    for band in ["broad", "fish", "invertebrate"]:
        expr = f"box*{band}*.png"
        fls = list(input_path.glob(expr))
        fls = [x for x in fls if "Dt" not in str(x) and "Ds" not in str(x)]
        name = f"{band}_combined.png"
        combine_images(combiner, fls, name)

    fls = ["invertebrate_D_7252", "invertebrate_acorr3_7257"]
    fls = [x for x in input_path.glob("*.png") if any(y in str(x) for y in fls)]
    fls = sorted(fls, reverse=True)
    name = f"example_combined.png"
    combine_images(combiner, fls, name, 1, 16)

    fls = [f"result_{x}_F1_weighted_plot_gap" for x in ["broad", "fish", "invertebrate"]]
    fls = sorted([x for x in input_path.glob("*.png") if any(y in str(x) for y in fls)])
    name = f"f1s_combined.png"
    combine_images(combiner, fls, name, 2, 16)


    # fls = [x for x in input_path.glob("full_*.png")]
    # name = f"cluster_combined.png"
    # combine_images(combiner, fls, name, 2, 54)

    fls = ["sunset_broad", "sunset_date_broad"]
    fls = [x for x in input_path.glob("*.png") if any(y in str(x) for y in fls)]
    fls = sorted(fls)
    name = f"sunset_combined.png"
    combine_images(combiner, fls, name, 1, 54)

    fls = input_path.glob("pca_*_combined*.png")
    fls = sorted(fls)
    name = f"pca_combined.png"
    combine_images(combiner, fls, name, 3, 54)