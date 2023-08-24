#!/usr/bin/env python3

import argparse
import sys, os
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from skimage import io
import matplotlib.patches as mpatches

from matplotlib import animation as anim

from typing import cast, Literal


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
        help="The path(s) to the image(s) you want to overlay the layout onto."
    )
    parser.add_argument(
        "-a", "--animate",
        choices=["gif", "mp4"],
        help=(
            "Should we write the output as a gif or mp4? "
            "Default will predict from extension if outfile is given. "
            "This option is provided in case you want a gif or mp4 but don't want the usual extension, "
            "or you don't want to explicitly set the outfile name but want an animation."
        )
    )
    parser.add_argument(
        "-o", "--outfile",
        help=(
            "Where to save the output file(s) to. "
            "If multiple images are provided, this should be a directory. "
            "If you specify multiple images and the --animate option, "
            "this should be the gif or mp4 filename. If a single image is given, "
            "this should be the jpeg filename. "
            "Default: grid_layout/panel.jpg, grid_layout/panel/{0..1}.jpg, grid_layout/panel.mp4, grid_layout/panel.gif"
        ),
        default=None
    )
    parser.add_argument(
        "-d", "--dpi",
        type=int,
        help="What resolution should the output image(s) or animation have? Default: 150",
        default=150,
    )
    parser.add_argument(
        "-s", "--framestep",
        type=int,
        help=(
            "If writing a video, how many milliseconds should each image be displayed for. "
            "E.g. framestep=50 (default) means 20 images will be displayed per second."
        ),
        default=50
    )

    args = parser.parse_args(argv)

    if args.animate is None:
        if args.outfile is None:
            raise ValueError(
                "If the -a flag is not provided, you need to specify an "
                "--outfile so we can infer the filetype from the extension."
            )

        if args.outfile.endswith(".gif"):
            animate: Literal["gif", "mp4"] = "gif"
        elif args.outfile.endswith(".mp4") or args.outfile.endswith(".mpeg"):
            animate = "mp4"
        else:
            animate = "mp4"
    else:
        animate = args.animate

    assert animate in ("gif", "mp4"), "This shouldn't be possible"

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

    elif len(args.images) > 1 and (animate is not None):
        if args.outfile is None:
            outfile = pjoin("grid_layout", f"panel.{animate}")
        else:
            outfile = args.outfile

        if dirname(outfile) != "":
            os.makedirs(dirname(outfile), exist_ok=True)

        check_layout_anim(
            args.layout,
            args.images,
            outfile,
            filetype=animate,
            dpi=args.dpi,
            framestep=args.framestep
        )

    else:
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
            is_exclude = tab[0].lower() in ("exclude", "exclure")
            rect = mpatches.Rectangle(
                (minc, minr),
                maxc - minc,
                maxr - minr,
                fill="red" if is_exclude else False,
                alpha=0.3,
                edgecolor="black" if is_exclude else 'red',
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

    dn = os.path.dirname(outimage)

    if dn != "":
        os.makedirs(dn, exist_ok=True)

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


def check_layout_anim(
    layout: str,
    images: list[str],
    outfile: str,
    filetype: Literal["gif", "mp4"] = "gif",
    dpi: int = 300,
    framestep: int = 100
):
    im0 = io.imread(images[0])
    height = (im0.shape[0] / im0.shape[1]) * 6

    if filetype == "mp4":
        ffmpeg_extras = [
            '-c:v',
            "libx264",
            "-strict",
            "-2",
            "-preset", "slow",
            "-pix_fmt", "yuv420p",
            "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2"
        ]
        writer = anim.FFMpegWriter(extra_args=ffmpeg_extras)
    elif filetype == "gif":
        writer = anim.PillowWriter()
    else:
        raise ValueError(
            "Sorry, you asked to write an animation but specified an unsupported filetype."
        )

    fig, ax = plt.subplots(ncols=1, nrows=1, figsize=(6, height))

    images_dirty_tmp = [(check_file(f), f) for f in images]
    images_dirty = [(e, f) for e, f in images_dirty_tmp if e is not None]
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

    ax.set_axis_off()
    plt.subplots_adjust(
        top = 1, bottom = 0, right = 1, left = 0,
        hspace = 0, wspace = 0
    )
    plt.margins(0,0)

    ani = anim.FuncAnimation(fig=fig, func=update, frames=images, interval=framestep)
    ani.save(outfile, writer=writer, dpi=dpi, savefig_kwargs={"pad_inches": 0})
    plt.close()
    return
