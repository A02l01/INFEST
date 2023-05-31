#!/usr/bin/env python3

import numpy as np
from scipy import ndimage as ndi


__names__ = ["watershed_mask", "threshold_mask", "otsu_mask", "original_mask"]


def watershed_mask(
    img,
    min_object_size: int = 500,
    orig: np.ndarray | None = None
):
    from skimage.color import rgb2gray
    from skimage.exposure import histogram
    from skimage.filters import sobel, threshold_multiotsu
    from skimage.morphology import remove_small_objects
    from skimage.segmentation import watershed

    try:
        gr = rgb2gray(img)
    except ValueError:
        gr = img

    if orig is not None:
        try:
            grorig = rgb2gray(orig)
        except:
            grorig = orig
        hist = histogram(grorig)
    else:
        hist = histogram(gr)

    elevation_map = sobel(gr)
    thresholds = threshold_multiotsu(gr, hist=hist)

    markers = np.zeros_like(elevation_map)
    markers[gr < thresholds[0]] = 1
    markers[gr > thresholds[1]] = 2

    seg = watershed(elevation_map, markers)

    mask = remove_small_objects(
        ndi.binary_fill_holes(1 - (seg - 1)),
        min_object_size
    )

    mask[np.isnan(gr)] = True
    return mask


def threshold_mask(
    img: np.ndarray,
    threshold: float = 0.3,
    min_object_size: int = 50,
):
    from skimage.color import rgb2hsv
    from skimage.morphology import remove_small_objects
    from skimage.morphology import closing as skiclosing, square as skisquare

    hsv = rgb2hsv(img)
    mask = skiclosing(hsv[:, :, 1] >= threshold, skisquare(3))
    mask = ndi.binary_fill_holes(mask)
    mask = remove_small_objects(mask, min_object_size)
    mask = ndi.binary_dilation(mask, structure=np.ones((3, 3)), iterations=1)
    return mask


def otsu_mask(img: np.ndarray):
    from skimage.color import rgb2gray
    from skimage.filters import threshold_otsu
    from skimage.morphology import closing as skiclosing, square as skisquare

    try:
        gr = rgb2gray(img)
    except ValueError:
        gr = img

    threshold = threshold_otsu(gr)
    mask = skiclosing(gr <= threshold, skisquare(3))
    mask = ndi.binary_fill_holes(mask)
    # This extends the object size a bit to remove any edge artifacts around edges of objects.
    mask = ndi.binary_dilation(mask, structure=np.ones((3, 3)), iterations=1)
    return mask


def original_mask(
    img: np.ndarray,
    threshold: float = 0.3,
):
    from skimage.color import rgb2hsv

    hsv = rgb2hsv(img)
    mask = hsv[:, :, 1] < threshold
    return ~mask
