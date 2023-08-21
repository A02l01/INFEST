#!/usr/bin/env python3

import argparse
import sys
import numpy as np
from skimage import io

from matplotlib import pyplot as plt

from typing import Literal

__names__ = [
    "spline_interpolate_leaves",
    "colour_correct_img",
    "correct_uniform",
    "correct_nonuniform"
]


def get_img_coords(img):
    """ Helper function to get the grid coordinates of all pixels.

    Used to predict pixel values based on splines.
    """
    rowints = np.repeat(np.arange(img.shape[0]), img.shape[1])
    colints = np.tile(np.arange(img.shape[1]), img.shape[0])
    return (rowints, colints)


def get_grid(img, size=100):
    """ Fitting the model on all pixels is a bit too slow
    and memory intensive. This gives us coordinates
    of non-overlapping squares to reduce by.
    """

    xr = np.arange(0, img.shape[0] - 1, size)
    yr = np.arange(0, img.shape[1] - 1, size)

    xrr = np.repeat(xr, yr.size)
    yrr = np.tile(yr, xr.size)
    return np.stack([
        xrr,
        xrr + size,
        yrr,
        yrr + size
    ]).T


def get_img_training_data(img, grid, threshold: float = 0.5):
    """ Get data to train the splines from.

    Returns a 3 tuple.
    x and y are the mid points of the grid.
    z is the mean value of the grid for each channel.
    """

    xs = []
    ys = []
    zs = []

    for i in range(grid.shape[0]):
        r = grid[i,]
        pixels = img[r[0]:r[1], r[2]:r[3]]
        pixels = pixels.reshape(-1, 3)

        # Exclude sections that are mostly missing
        if np.isnan(pixels).mean() > threshold:
            continue

        z = np.nanmean(pixels, axis=0)
        if np.isnan(z).any():
            continue

        xs.append(r[[0, 1]].mean())
        ys.append(r[[2, 3]].mean())
        zs.append(z)

    xs = np.stack(xs).astype(int)
    ys = np.stack(ys).astype(int)
    zs = np.stack(zs)
    return xs, ys, zs


def find_uniform_background(img: np.ndarray):
    return np.nanmedian(img, axis=(0, 1)).reshape(1, 1, 3)


def spline_interpolate_leaves(
    img: np.ndarray,
    size: int = 10
):
    from scipy.interpolate import SmoothBivariateSpline

    if img.max() > 1:
        raise ValueError(
            "This function must be called on a float "
            "array with pixel values between 0 and 1."
        )

    grid = get_grid(img, size)
    xs, ys, zs = get_img_training_data(img, grid)

    out_img = np.zeros(img.shape)
    rows, cols = get_img_coords(img)

    for channel in range(img.shape[-1]):
        model = SmoothBivariateSpline(
            xs,
            ys,
            zs[:, channel],
            bbox=[0, img.shape[0], 0, img.shape[1]]
        )
        rows, cols = get_img_coords(img)
        vals = model.ev(rows, cols)
        out_img[rows, cols, channel] = vals

    return np.clip(out_img, 0, 1)


def colour_correct_img(
    img: np.ndarray,
    background: np.ndarray
):
    if img.max() > 1:
        raise ValueError(
            "This function must be called on a float "
            "array with pixel values between 0 and 1."
        )

    background[background == 0] = np.nan
    corrected = img * (1 / background)
    corrected[np.isnan(corrected)] = 1
    return np.clip(corrected, 0, 1)


def correct_uniform(
    img: np.ndarray,
    min_object_size: int = 500,
    mask_type: Literal["threshold", "otsu", "watershed"] = "otsu",
    grid: np.ndarray | None = None,
    orig: np.ndarray | None = None,
    exclude_mask: np.ndarray | None = None
):
    from INFEST.mask import watershed_mask, threshold_mask, otsu_mask

    if np.nanmax(img) > 1:
        img = img.astype(float) / 255

    masked = img.copy()

    if (exclude_mask is not None) and not exclude_mask.all():
        masked[exclude_mask] = np.nan

    # We want to set any objects outside of our targets to be non-objects
    if grid is not None:
        masked[~grid] = np.nan

    if mask_type == "threshold":
        mask = threshold_mask(img)
    elif mask_type == "otsu":
        mask = otsu_mask(img)
    elif mask_type == "watershed":
        mask = watershed_mask(img, min_object_size=min_object_size, orig=orig)
    else:
        raise ValueError("mask_type is invalid.")

    masked[mask] = np.nan

    background = find_uniform_background(masked)
    corrected = colour_correct_img(img, background)

    corrected[np.isnan(img)] = 1
    corrected = (corrected * 255).astype("uint8")
    return corrected


def correct_nonuniform(
    img: np.ndarray,
    min_object_size: int = 500,
    size: int = 10,
    mask_type: Literal["threshold", "otsu", "watershed"] = "otsu",
    grid: np.ndarray | None = None,
    orig: np.ndarray | None = None,
    exclude_mask: np.ndarray | None = None
):
    from INFEST.mask import watershed_mask, threshold_mask, otsu_mask

    if np.nanmax(img) > 1:
        img = img.astype(float) / 255

    masked = img.astype(float).copy()

    if (exclude_mask is not None) and not exclude_mask.all():
        masked[exclude_mask] = np.nan

    # We want to set any objects outside of our targets to be non-objects
    if grid is not None:
        masked[~grid] = np.nan

    if mask_type == "threshold":
        mask = threshold_mask(img)
    elif mask_type == "otsu":
        mask = otsu_mask(img)
    elif mask_type == "watershed":
        mask = watershed_mask(img, min_object_size=min_object_size, orig=orig)
    else:
        raise ValueError("mask_type is invalid.")

    masked[mask] = np.nan

    background = spline_interpolate_leaves(masked, size=size)
    corrected = colour_correct_img(img, background)

    corrected[np.isnan(img)] = 1
    corrected = (corrected * 255).astype("uint8")
    return corrected


def main(prog: str | None = None, argv: list[str] | None = None):
    from os.path import basename

    if prog is None:
        prog = sys.argv[0]

    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(prog=basename(prog))
    parser.add_argument(
        "images",
        nargs="+",
        help="The path to the image you want to overlay the layout onto."
    )
    parser.add_argument(
        "-l", "--layout",
        default=None,
        help="Provide the locations of the leaves to help in finding the background."
    )
    parser.add_argument(
        "-o", "--outdir",
        help=("Where to save the output file(s) to."),
        default="images_corrected"
    )
    parser.add_argument(
        "-u", "--uniform",
        action="store_true",
        default=False,
        help=(
            "Instead of applying region specific normalisation, "
            "normalise by average background"
        ),
    )
    parser.add_argument(
        "-g", "--gridsize",
        type=int,
        default=10,
        help=(
            "How big should the grid be? "
            "NOTE: Smaller values use more memory. "
            "Default: 10"
        ),
    )
    parser.add_argument(
        "-m", "--minsize",
        type=int,
        default=500,
        help=(
            "The minimum size of a foreground object "
            "for background detection. Default: 500."
        ),
    )
    parser.add_argument(
        "-t", "--masktype",
        type=str,
        choices=["threshold", "otsu", "watershed"],
        default="otsu",
        help="What algorithm to use to detect the background. Default: otsu",
    )
    parser.add_argument(
        "-n", "--ncpu",
        type=int,
        help="How many images to process in parallel.",
        default=1
    )
    args = parser.parse_args(argv)

    apply_norm_parallel(
        args.images,
        args.outdir,
        args.uniform,
        args.layout,
        args.minsize,
        args.gridsize,
        args.masktype,
        args.ncpu
    )

    return


def apply_norm_parallel(
    images,
    outdir,
    uniform,
    layout,
    minsize,
    gridsize,
    masktype,
    ncpu=1
):
    import functools
    from multiprocessing import Pool
    from os import makedirs

    makedirs(outdir, exist_ok=True)
    with Pool(ncpu) as p:
        pnames = p.map(
            functools.partial(
                norm_one,
                outdir=outdir,
                uniform=uniform,
                layout=layout,
                minsize=minsize,
                gridsize=gridsize,
                masktype=masktype
            ),
            images
        )
    return pnames


def norm_one(img_path, outdir, uniform, layout, minsize, gridsize, masktype):
    from os.path import join as pjoin
    from os.path import basename

    from .panel import Panel

    img = io.imread(img_path)

    if uniform and (layout is None):
        normed = correct_uniform(
            img,
            min_object_size=minsize,
            mask_type=masktype
        )
    elif uniform:
        pa = Panel(
            img,
            layout=layout,
            panel_mask_type=masktype,
        )
        panorm = pa.correct_uniform(
            min_object_size=minsize
        )
        normed = panorm.img_original
    elif (layout is None):
        normed = correct_nonuniform(
            img,
            min_object_size=minsize,
            size=gridsize,
            mask_type=masktype
        )
    else:
        pa = Panel(
            img,
            layout=layout,
            panel_mask_type=masktype,
        )
        panorm = pa.correct_nonuniform(
            min_object_size=minsize,
            size=gridsize
        )
        normed = panorm.img_original

    full_path = pjoin(outdir, basename(img_path))
    io.imsave(full_path, normed)
    plt.close()
    return full_path
