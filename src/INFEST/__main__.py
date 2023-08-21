#!/usr/bin/env python3


def main(prog: str | None = None, argv: list[str] | None = None):
    import argparse
    import sys

    from os.path import basename

    if prog is None:
        prog = sys.argv[0]

    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(prog=basename(prog))
    parser.add_argument(
        "-l", "--layout",
        default=argparse.FileType,
        help="Provide the locations of the leaves to help in finding the background."
    )

    parser.add_argument(
        "images",
        nargs="+",
        help="The path to the image you want to overlay the layout onto."
    )

    parser.add_argument(
        "-o", "--outdir",
        help=("Where to save the pipeline results to."),
        default="infest_results"
    )

    parser.add_argument(
        "--cc-type",
        type=str,
        choices=["nonuniform", "uniform", "none"],
        default="nonuniform",
        help=(
            "How should we perform colour correction?"
        ),
    )

    parser.add_argument(
        "--cc-gridsize",
        type=int,
        default=10,
        help=(
            "How big should the grid be? "
            "NOTE: Smaller values use more memory. "
            "Default: 10"
        ),
    )
    parser.add_argument(
        "--cc-minsize",
        type=int,
        default=500,
        help=(
            "The minimum size of a foreground object "
            "for background detection. Default: 500."
        ),
    )
    parser.add_argument(
        "--cc-masktype",
        type=str,
        choices=["threshold", "otsu", "watershed"],
        default="otsu",
        help="What algorithm to use to detect the background. Default: otsu",
    )

    parser.add_argument(
        "--qu-masktype",
        type=str,
        choices=["threshold", "otsu", "watershed", "original", "none"],
        default="none",
        help="What algorithm to use to detect the background. Default: none",
    )

    parser.add_argument(
        "-n", "--ncpu",
        type=int,
        help="How many images to process in parallel.",
        default=1
    )

    parser.add_argument(
        "-a", "--animate",
        choices=["mp4", "gif", "none"],
        default="none"
    )

    parser.add_argument(
        "--framestep",
        type=int,
        help=(
            "If writing a video, how many milliseconds should each image be displayed for. "
            "E.g. framestep=50 (default) means 20 images will be displayed per second."
        ),
        default=50
    )

    parser.add_argument(
        "--dpi",
        type=int,
        default=150
    )

    args = parser.parse_args(argv)


    pipeline(
        args.layout,
        args.images,
        args.outdir,
        args.cc_type,
        args.cc_gridsize,
        args.cc_minsize,
        args.cc_masktype,
        args.qu_masktype,
        args.animate,
        args.framestep,
        args.dpi,
        args.ncpu
    )
    return


def pipeline(
    layout,
    images,
    outdir,
    cc_type,
    cc_gridsize,
    cc_minsize,
    cc_masktype,
    qu_masktype,
    animate,
    framestep,
    dpi,
    ncpu=1
):
    from os import makedirs
    from os.path import basename
    from os.path import join as pjoin

    from .norm_colours import apply_norm_parallel
    from .check_layout import check_layout, check_layout_anim
    from .quant import infest
    from .gompertz import fit

    makedirs(outdir, exist_ok=True)

    if cc_type != "none":
        cc_outdir = pjoin(outdir, "colour_normed")
        images = apply_norm_parallel(
            images,
            cc_outdir,
            uniform=cc_type == "uniform",
            layout=layout,
            minsize=cc_minsize,
            gridsize=cc_gridsize,
            masktype=cc_masktype,
            ncpu=ncpu
        )

    if animate == "none":
        cl_outdir = pjoin(outdir, "check_layout")
        makedirs(cl_outdir, exist_ok=True)

        for image in images:
            check_layout(
                layout,
                image,
                pjoin(cl_outdir, basename(image)),
                dpi
            )
    else:
        cl_outfile = pjoin(outdir, f"check_layout.{animate}")
        check_layout_anim(
            layout,
            images,
            cl_outfile,
            filetype=animate,
            dpi=dpi,
            framestep=framestep
        )

    quant_outfile = pjoin(outdir, "quantification_results.tsv")
    quant_animdir = pjoin(outdir, "quantification_animations")

    infest(
        images,
        layout,
        quant_outfile,
        leaf_mask_type=qu_masktype,
        normalise=None,
        write_video=None if (animate == "none") else quant_animdir,
        video_filetype="mp4" if (animate == "none") else animate,
        ncpu=ncpu,
        dpi=dpi,
        framestep=framestep
    )

    fit(quant_outfile, pjoin(outdir, "gompertz"))
    return
