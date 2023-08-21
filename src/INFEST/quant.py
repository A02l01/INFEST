#!/usr/bin/env python3

   ##     ###             ###     ##
  #       ###             ###       #
 #                                   #
 #        ###     ###     ###        #
 #        ###     ###     ###        #
  #        #       #       #        #
   ##     #       #       #       ##


from os.path import join as pjoin
from typing import Literal
# import logging

import numpy as np
from skimage import io
from matplotlib import pyplot as plt

# from .leaf import Leaf
from .panel import Panel


__names__ = ["fit", "Panel"]


def write_animation(
    sample,
    time,
    lesion_area,
    leaf_area,
    ichloro,
    images_orig,
    images_lesion,
    images_leaf,
    images_ichloro,
    where_to,
    filetype: Literal["gif", "mp4"] = "gif",
    dpi=150,
    framestep=100,
):
    from matplotlib import animation as anim

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

    print(f"- {sample}")

    #height, width = io.imread(images_orig[0]).shape
    height_per_image = 1.5

    fig, axs = plt.subplots(
        ncols=2,
        nrows=4,
        figsize=(6, 6),
        width_ratios=[2, 1],
        sharex=False,
    )

    axs[0, 0].set_axis_off()
    axs[0, 0].text(0, 1, sample, fontsize=10, horizontalalignment="left")
    te = axs[0, 0].text(0, 0.5, "0", verticalalignment="bottom", horizontalalignment="right")

    axs[0, 1].set_axis_off()
    image_orig = axs[0, 1].imshow(io.imread(images_orig[0]), interpolation=None)

    axs[1, 0].scatter(x=time, y=lesion_area, s=10, marker="o", alpha=0.5)
    axs[1, 0].set_ylabel("Lesion area", fontsize=10)
    axs[1, 0].xaxis.set_ticklabels([])

    axs[1, 1].set_axis_off()
    image_lesion = axs[1, 1].imshow(io.imread(images_lesion[0]), interpolation=None)

    axs[2, 0].scatter(x=time, y=leaf_area, s=10, marker="o", alpha=0.5)
    axs[2, 0].set_ylabel("Leaf area", fontsize=10)
    axs[2, 0].xaxis.set_ticklabels([])

    axs[2, 1].set_axis_off()
    image_leaf = axs[2, 1].imshow(io.imread(images_leaf[0]), interpolation=None)

    axs[3, 0].scatter(x=time, y=ichloro, s=10, marker="o", alpha=0.5)
    axs[3, 0].set_ylabel("ichloro sum", fontsize=10)
    axs[3, 0].set_xlabel("Time", fontsize=10)

    axs[3, 1].set_axis_off()
    image_ichloro = axs[3, 1].imshow(io.imread(images_ichloro[0]), interpolation=None)

    vl2 = axs[1, 0].axvline(x=0, c="red")
    vl3 = axs[2, 0].axvline(x=0, c="red")
    vl4 = axs[3, 0].axvline(x=0, c="red")

    plt.tight_layout(pad=0.1)

    def update(frame):
        idx, orig, lesion_, leaf_, ichloro_ = frame
        image_orig.set_data(io.imread(orig))
        image_lesion.set_data(io.imread(lesion_))
        image_leaf.set_data(io.imread(leaf_))
        image_ichloro.set_data(io.imread(ichloro_))

        vl2.set_xdata([idx])
        vl3.set_xdata([idx])
        vl4.set_xdata([idx])
        te.set_text(str(idx))
        return image_orig, image_lesion, image_leaf, image_ichloro, vl2, vl3, vl4, te

    ani = anim.FuncAnimation(
        fig=fig,
        func=update,
        frames=list(zip(time, images_orig, images_lesion, images_leaf, images_ichloro)),
        interval=framestep,
        repeat=True
    )
    ani.save(pjoin(where_to, f"{sample}.{filetype}"), writer=writer, dpi=dpi)
    plt.close()
    return


def find_outfile(outfile: str | None, images: list[str]) -> str:
    from os.path import dirname, exists
    import datetime

    if outfile is None:
        outfile = pjoin(dirname(images[0]), "analysis.txt")

        if exists(outfile):
            date_now = datetime.date.today().strftime("%Y%m%d")
            outfile = pjoin(dirname(images[0]), f"analyse_{date_now}.txt")
    else:
        outfile = outfile

    return outfile


def find_file_int(s: str) -> int:
    from os.path import basename, splitext

    p = splitext(basename(s))[0]

    try:
        i = int(p)
    except Exception:
        raise ValueError(f"Could not find an integer for image '{s}'")

    return i


def find_file_order(images: list[str]) -> list[tuple[int, str]]:

    tups = [
        (find_file_int(s), s)
        for s
        in images
    ]
    return sorted(
        tups,
        key=lambda t: t[0]
    )


def write_grayscale_img(fname: str, img: np.ndarray):
    import numpy as np
    from matplotlib.colors import Normalize

    norm = Normalize(vmin=0, vmax=255)
    cm = plt.get_cmap("inferno")

    img = cm(norm(np.clip((img * 255), 0, 255).astype(int)))
    img = np.clip(img[:, :, :3] * 255, 0, 255).astype("uint8")
    io.imsave(fname, img, check_contrast=False)
    return


def main(prog: str | None = None, argv: list[str] | None = None):
    import sys
    from os.path import basename
    import argparse

    if prog is None:
        prog = sys.argv[0]

    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(prog=basename(prog))
    parser.add_argument(
        "layout",
        help="Provide the locations of the leaves for quantification."
    )

    parser.add_argument(
        "images",
        nargs="+",
        help="The pictures you want to quantify."
    )

    parser.add_argument(
        "-o", "--outfile",
        default=None,
        help="Where should we write the results?"
    )

    parser.add_argument(
        "-w", "--write-video",
        type=str,
        help="Write videos of samples to this directory",
        default=None
    )

    parser.add_argument(
        "-a", "--animate",
        default="mp4",
        choices=["gif", "mp4"],
        help=(
            "If --write-video is specified, what video format should the files be? "
            "Should we write the output animations as a gif or mp4?"
        )
    )

    parser.add_argument(
        "-n", "--ncpu",
        type=int,
        help="How many images to process in parallel.",
        default=1
    )

    parser.add_argument(
        "-d", "--dpi",
        type=int,
        help="If writing a video, what resolution should it have?",
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

    parser.add_argument(
        "--normalise",
        type=str,
        choices=["uniform", "nonuniform"],
        help=(
            "Normalise the image background colour before leaf analysis."
        ),
        default=None
    )

    parser.add_argument(
        "-t", "--masktype",
        type=str,
        choices=["threshold", "otsu", "watershed", "original", "none"],
        default="watershed",
        help="What algorithm to use to detect the background. Default: watershed",
    )

    args = parser.parse_args(argv)

    outfile = find_outfile(args.outfile, args.images)

    infest(
        images=args.images,
        layout=args.layout,
        outfile=outfile,
        write_video=args.write_video,
        video_filetype=args.animate,
        leaf_mask_type=args.masktype,
        ncpu=args.ncpu,
        framestep=args.framestep,
    )
    return


def process_image(
    i: int,
    path: str,
    layout: str,
    leaf_mask_type: Literal["threshold", "otsu", "watershed", "original", "none"],
    normalise: Literal["uniform", "nonuniform"] | None,
    write_video: str | None,
    tmpdir: str,
):
    import pandas as pd
    print(f'- processing image {path}')


    image = io.imread(path)
    output = list()

    p = Panel(
        image,
        layout,
        time=i,
        leaf_mask_type=leaf_mask_type
    )

    if normalise == "uniform":
        p = p.correct_uniform()
    elif normalise == "nonuniform":
        p = p.correct_nonuniform()

    for leaf in p:
        img_original = leaf.img_original
        img_lesion = leaf.lesion()
        img_leaf = leaf.leaf()
        img_ichloro = leaf.ichloro()

        record = leaf.stats(
            lesion=img_lesion,
            leaf=img_leaf,
            ichloro=img_ichloro
        ).as_dict()

        if write_video is not None:
            bname = pjoin(tmpdir, f"{leaf.id}_time{i:0>5}")

            fname = f"{bname}_orig.jpg"
            record["fname_orig"] = fname
            io.imsave(fname, img_original, check_contrast=False)

            fname = f"{bname}_lesion.jpg"
            record["fname_lesion"] = fname
            write_grayscale_img(fname, img_lesion)

            fname = f"{bname}_leaf.jpg"
            record["fname_leaf"] = fname
            write_grayscale_img(fname, img_leaf)

            fname = f"{bname}_ichloro.jpg"
            record["fname_ichloro"] = fname
            write_grayscale_img(fname, img_ichloro)
        else:
            record.update({
                "fname_orig": None,
                "fname_lesion": None,
                "fname_leaf": None,
                "fname_ichloro": None,
            })

        output.append(record)

    return pd.DataFrame(output)


def infest(
    images: list[str],
    layout: str,
    outfile: str,
    leaf_mask_type: Literal["threshold", "otsu", "watershed", "original", "none"],
    normalise: Literal["uniform", "nonuniform"] | None = None,
    write_video: str | None = None,
    video_filetype: Literal["gif", "mp4"] = "gif",
    ncpu: int = 1,
    dpi: int = 300,
    framestep: int = 100
):
    from multiprocessing import Pool
    from tempfile import TemporaryDirectory
    import functools
    from os import makedirs

    import pandas as pd

    image_tups = find_file_order(images)

    with open(outfile, "w") as handle, TemporaryDirectory() as tmpdir:
        with Pool(ncpu) as p:
            results = p.starmap(
                functools.partial(
                    process_image,
                    layout=layout,
                    leaf_mask_type=leaf_mask_type,
                    normalise=normalise,
                    write_video=write_video,
                    tmpdir=tmpdir
                ),
                image_tups
            )

        print("Done!")

        df = pd.concat(results)
        df.sort_values(by=["time", "id"])
        df.drop(
            columns=["fname_orig", "fname_lesion", "fname_leaf", "fname_ichloro"]
        ).to_csv(handle, sep="\t", header=True, index=False)

        if write_video is not None:
            print(f"Writing animation to: {write_video}")
            makedirs(write_video, exist_ok=True)
            jobs = []
            for name, subdf in df.groupby("id"):
                jobs.append((
                    name,
                    subdf["time"],
                    subdf["lesion_area"],
                    subdf["leaf_area"],
                    subdf["ichloro_sum"],
                    subdf["fname_orig"].tolist(),
                    subdf["fname_lesion"].tolist(),
                    subdf["fname_leaf"].tolist(),
                    subdf["fname_ichloro"].tolist()
                ))


            wa = functools.partial(
                write_animation,
                where_to=write_video,
                filetype=video_filetype,
                dpi=dpi,
                framestep=framestep
            )

            with Pool(ncpu) as p:
                p.starmap(wa, jobs)

    return


if __name__ == "__main__":
    main()
