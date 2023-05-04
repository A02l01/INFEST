#!/usr/bin/env python3

import argparse
import sys, os
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.patches as mpatches

from typing import cast


def main(prog: str | None = None, argv: list[str] | None = None):

    from os.path import join as pjoin

    if prog is None:
        prog = sys.argv[0]

    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(prog=prog)
    parser.add_argument(
        "layout",
        help="A tsv file detailing the experiment layout."
    )
    parser.add_argument(
        "image",
        help="The path to the image you want to overlay the layout onto."
    )
    parser.add_argument(
        "-o", "--outfile",
        help="Where to save the output file to.",
        default=pjoin("grid_layout", "panel.jpg")
    )
    parser.add_argument(
        "--dpi",
        help="What resolution to save the image as.",
        default=400,
        type=int
    )

    args = parser.parse_args(argv)

    check_layout(
        args.layout,
        args.image,
        args.outfile,
        args.dpi
    )
    return


def check_layout(layout: str, inimage: str, outimage: str, dpi: int = 400):

    back = mpimg.imread(inimage)
    fig, ax = plt.subplots(ncols=1, nrows=1, figsize=(6, 6))

    # Type annotation from subplots is FigureBase, which doesn't have savefig defined.
    fig = cast(Figure, fig)

    ax.imshow(back)

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
