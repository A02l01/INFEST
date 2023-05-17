#!/usr/bin/env python3

import argparse
import sys
import numpy as np
import scipy as sp
from skimage import io



def get_grid(img, size=100):
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


def get_img_training_data(img, grid):
    xs = []
    ys = []

    for i in range(grid.shape[0]):
        r = grid[i,]
        pixels = img[r[0]:r[1], r[2]:r[3]]
        pixels = pixels.reshape(-1, 3)
        y = np.nanmean(pixels, axis=0)
        if np.isnan(y).any():
            continue
        xs.append(r[[0, 2]])
        ys.append(y)
    
    xs = np.stack(xs)
    ys = np.array(ys)
    return xs, ys


def apply_gaussian_filter(img, niters=1, sigma=10, radius=250):
    new = np.copy(img)

    for _ in range(niters):
        new = np.stack([
            sp.ndimage.gaussian_filter(new[:, :, i], sigma=sigma, radius=radius)
            for i in (0, 1, 2)
        ], axis=-1)

    return new


def find_mask(img):
    from skimage.color import rgb2gray
    from skimage.filters import threshold_otsu
    from skimage.morphology import closing as skiclosing, square as skisquare

    img_gs = rgb2gray(img)
    threshold = threshold_otsu(img_gs)
    mask = skiclosing(img_gs > threshold, skisquare(3))
    mask = sp.ndimage.binary_fill_holes(~mask)

    # This extends the object size a bit to remove any edge artifacts around edges of objects.
    mask = sp.ndimage.binary_dilation(mask, structure=np.ones((20, 20)), iterations=1)
    return mask


def find_uniform_background(img):
    mask = find_mask(img)

    #img = apply_gaussian_filter(img, niters=2, sigma=5, radius=10)
    return np.median(img[~mask], axis=0)


def find_background(img, gridsize=100, blur_sigma=10, blur_niters=5):
    from sklearn.gaussian_process import GaussianProcessRegressor
    from sklearn.gaussian_process.kernels import ConstantKernel, RBF, WhiteKernel
    
    mask = find_mask(img)

    img_nan = np.copy(img)
    img_nan[np.where(mask)] = np.nan

    grid = get_grid(img_nan, gridsize)
    xs, ys = get_img_training_data(img_nan, grid)

    gpr = GaussianProcessRegressor(ConstantKernel(1.0) * RBF(2.5 * gridsize) + WhiteKernel(noise_level=0.5))
    gpr.fit(xs, ys)

    yhat = gpr.sample_y(grid[:, [0, 2]], n_samples=100).mean(axis=-1)

    bg = np.zeros_like(img)

    for i in range(grid.shape[0]):
        x = grid[i]
        y = yhat[i].T
        bg[x[0]:x[1], x[2]:x[3]] = y

    bg = apply_gaussian_filter(bg, sigma=blur_sigma, radius=2 * gridsize, niters=blur_niters)
    return bg


def apply_norm(img, bg):
    normed = img * (np.nanmax(img / 255) / bg)
    normed = np.clip(normed, 0, 255).astype("uint8")
    return normed


def main(prog: str | None = None, argv: list[str] | None = None):

    from os.path import join as pjoin
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
        "-o", "--outdir",
        help=("Where to save the output file(s) to."),
        default="images_corrected"
    )
    parser.add_argument(
        "-u", "--uniform",
        action="store_true",
        help="Instead of applying region specific normalisation, normalise by average background",
        default=False
    )
    parser.add_argument(
        "-g", "--gridsize",
        type=int,
        help=(
            "How big should the grid be? "
            "NOTE: Smaller values use more memory. "
            "Default: 100"
        ),
        default=100,
    )
    parser.add_argument(
        "-s", "--sigma",
        type=int,
        help=(
            "The sigma value for gaussian blurring. Default: 5."
        ),
        default=5,
    )
    parser.add_argument(
        "-n", "--niter",
        type=int,
        help=(
            "How many iterations of blurring should the background "
            "interpolation have? NOTE: This needs to increase if "
            "gridsize is increased. Default: 5"
        ),
        default=5,
    )

    args = parser.parse_args(argv)

    for img_path in args.images:
        img = io.imread(img_path)

        if args.uniform:
            bg = find_uniform_background(img / 255)
            normed = apply_norm(img, bg.reshape(1, 1, 3))
        else:
            normed = norm_one(img, gridsize=args.gridsize)

        io.imsave(pjoin(args.outdir, basename(img_path)), normed)
    return


def norm_one(img, gridsize=100):
    bg = find_background(img / 255, gridsize=gridsize)
    normed = apply_norm(img, bg)
    return normed
