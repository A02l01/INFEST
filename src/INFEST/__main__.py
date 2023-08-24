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
        "layout",
        type=str,
        help="Provide the locations of the leaves in your images."
    )

    parser.add_argument(
        "images",
        nargs="+",
        help="The path(s) to the image(s) you want to process."
    )

    parser.add_argument(
        "-o", "--outdir",
        help=("Where to save the pipeline results to."),
        default="infest_results"
    )

    parser.add_argument(
        "--cn-type",
        type=str,
        choices=["nonuniform", "uniform", "none"],
        default="nonuniform",
        help=(
            "How should we perform colour correction?"
        ),
    )

    parser.add_argument(
        "--cn-gridsize",
        type=int,
        default=10,
        help=(
            "How big should the grid be? "
            "NOTE: Smaller values use more memory. "
            "Default: 10"
        ),
    )

    parser.add_argument(
        "--cn-minsize",
        type=int,
        default=500,
        help=(
            "The minimum size of a foreground object "
            "for background detection. Default: 500."
        )
    )

    parser.add_argument(
        "--cn-masktype",
        type=str,
        choices=["threshold", "otsu", "watershed"],
        default="otsu",
        help=(
            "What algorithm to use to detect the background during colour normalisation. "
            "Note that the threshold method is not recommended, and was included for illustrative purposes. "
            "OTSU (the default) usually yeilds good results, but may yield weird results if you have "
            "lots of dark patches (e.g. shadows) or if your leaves have a similar colour as your background. "
            "The watershed method is more accurate for those kinds of situations, but takes a bit longer."
        )
    )

    parser.add_argument(
        "--qu-masktype",
        type=str,
        choices=["threshold", "otsu", "watershed", "original", "none"],
        default="none",
        help=(
            "What algorithm to use to detect the background during quantification. "
            "Default: none"
        )
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
        default="none",
        help=(
            "Write the layouts and quantifiation steps as animations in this format. "
            "By default, no animations are written. "
            "If you only want animations for layout or quantification, use the --animate-steps option."
        )

    )

    parser.add_argument(
        "--animate-steps",
        choices=["layout", "quant", "both"],
        default="both",
        help=(
            "Get the animations for only the check-layout step or the quantification step. "
            "Only used if --animate is specified. "
            "Default: both"
        )
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
        default=150,
        help="What resolution should the output images and animations have? Default: 150"
    )

    args = parser.parse_args(argv)

    pipeline(
        args.layout,
        args.images,
        args.outdir,
        args.cn_type,
        args.cn_gridsize,
        args.cn_minsize,
        args.cn_masktype,
        args.qu_masktype,
        args.animate,
        args.animate_steps,
        args.framestep,
        args.dpi,
        args.ncpu
    )
    return


def pipeline(
    layout,
    images,
    outdir,
    cn_type,
    cn_gridsize,
    cn_minsize,
    cn_masktype,
    qu_masktype,
    animate,
    animate_steps,
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

    if cn_type != "none":
        cn_outdir = pjoin(outdir, "colour_normed")
        images = apply_norm_parallel(
            images,
            cn_outdir,
            uniform=cn_type == "uniform",
            layout=layout,
            minsize=cn_minsize,
            gridsize=cn_gridsize,
            masktype=cn_masktype,
            ncpu=ncpu
        )

    if (animate == "none") or (animate_steps == "quant"):
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

    should_animate_quant = (animate != "none") and (animate_steps != "layout")

    infest(
        images,
        layout,
        quant_outfile,
        leaf_mask_type=qu_masktype,
        write_video=quant_animdir if should_animate_quant else None,
        video_filetype="mp4" if (animate == "none") else animate,
        ncpu=ncpu,
        dpi=dpi,
        framestep=framestep
    )

    fit(quant_outfile, pjoin(outdir, "gompertz"))
    return
