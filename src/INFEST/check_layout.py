#!/usr/bin/env python3

import argparse
import sys, os
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from skimage import io
import matplotlib.patches as mpatches

from matplotlib import animation as anim

from typing import cast


def main(prog: str | None = None, argv: list[str] | None = None):

    from os.path import join as pjoin
    from os.path import dirname, basename

    if prog is None:
        prog = sys.argv[0]

    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(prog=basename(prog))
    parser.add_argument(
        "layout",
        help="A tsv file detailing the experiment layout."
    )
    parser.add_argument(
        "images",
        nargs="+",
        help="The path to the image you want to overlay the layout onto."
    )
    parser.add_argument(
        "-a", "--animate",
        default=False,
        action="store_true",
        help="Should we write the output as an mpeg?"
    )
    parser.add_argument(
        "-o", "--outfile",
        help=(
            "Where to save the output file(s) to. "
            "If multiple images are provided, this should be a directory. "
            "If you specify multiple images and the --animate option, "
            "this should be the mpeg filename. If a single image is given, "
            "this should be the jpeg filename. "
            "Default: grid_layout/panel.jpg, grid_layout/panel/{0..1}.jpg, grid_layout/panel.mpeg"
        ),
        default=None
    )
    parser.add_argument(
        "--dpi",
        help="What resolution to save the image as.",
        default=400,
        type=int
    )

    args = parser.parse_args(argv)

    if len(args.images) == 1:
        if args.animate:
            raise ValueError("You specified --animate but only provided one image.")

        if args.outfile is None:
            outfile = pjoin("grid_layout", "panel.jpg")
        else:
            outfile = args.outfile

        if dirname(outfile) != "":
            os.makedirs(dirname(outfile), exist_ok=True)
        check_layout(
            args.layout,
            args.images[0],
            outfile,
            args.dpi
        )

    elif len(args.images) > 1 and args.animate:
        if args.outfile is None:
            outfile = pjoin("grid_layout", "panel.mpeg")
        else:
            outfile = args.outfile

        if dirname(outfile) != "":
            os.makedirs(dirname(outfile), exist_ok=True)
        check_layout_anim(
            args.layout,
            args.images,
            outfile
        )

    else:
        assert (len(args.images) > 1) and not args.animate, "This shouldn't happen"

        if args.outfile is None:
            outfile = pjoin("grid_layout", "panel")
        else:
            outfile = args.outfile

        if outfile != "":
            os.makedirs(outfile, exist_ok=True)

        for image in args.images:
            of = pjoin(outfile, basename(image))
            check_layout(
                args.layout,
                image,
                of,
                args.dpi
            )
    return


def check_layout(layout: str, inimage: str, outimage: str, dpi: int = 400):
    fig, ax = plt.subplots(ncols=1, nrows=1, figsize=(6, 6))

    # Type annotation from subplots is FigureBase, which doesn't have savefig defined.
    fig = cast(Figure, fig)

    ax.imshow(io.imread(inimage))

    with open(layout, "r") as target_f:
        for line in target_f:
            tab = line.rstrip("\n").split("\t")
            minr, minc, maxr, maxc = int(tab[1]), int(tab[2]), int(tab[3]), int(tab[4])
            rect = mpatches.Rectangle(
                (minc, minr),
                maxc - minc,
                maxr - minr,
                fill=False,
                edgecolor='red',
                linewidth=2
            )
            ax.add_patch(rect)
            ax.text(
                minc + (maxc - minc) * 0.1,
                minr + (maxr - minr) / 2,
                tab[0],
                fontsize=4,
                color="black"
            )

    os.makedirs(os.path.dirname(outimage), exist_ok=True)
    fig.savefig(outimage, dpi=dpi)


def check_file(string: str) -> int | None:
    from os.path import basename, splitext, exists

    if not exists(string):
        return None

    if splitext(string)[-1].lower() not in (".jpeg", ".jpg"):
        return None

    stripped = splitext(basename(string))[0]

    try:
        return int(stripped)
    except Exception:
        return None


def check_layout_anim(layout: str, images: list[str], outfile: str, dpi: int = 400):
    fig, ax = plt.subplots(ncols=1, nrows=1, figsize=(6, 6))

    images_dirty = [(check_file(f), f) for f in images]
    images_dirty = [(e, f) for e, f in images_dirty if e is not None]
    images = [
        f for _, f
        in sorted(images_dirty, key=lambda tup: tup[0])
    ]

    img = ax.imshow(io.imread(images[0]))

    with open(layout, "r") as target_f:
        for line in target_f:
            tab = line.rstrip("\n").split("\t")
            minr, minc, maxr, maxc = int(tab[1]), int(tab[2]), int(tab[3]), int(tab[4])
            rect = mpatches.Rectangle(
                (minc, minr),
                maxc - minc,
                maxr - minr,
                fill=False,
                edgecolor='red',
                linewidth=2
            )
            ax.add_patch(rect)
            ax.text(
                minc + (maxc - minc) * 0.1,
                minr + (maxr - minr) / 2,
                tab[0],
                fontsize=4,
                color="black"
            )

    def update(fname):
        img.set_data(io.imread(fname))
        return img

    ani = anim.FuncAnimation(fig=fig, func=update, frames=images, interval=200)
    ani.save(outfile, writer="ffmpeg", dpi=dpi)
    plt.close()
    return
