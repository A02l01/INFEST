#!/usr/bin/env python3

import numpy as np
from typing import NamedTuple, Literal, Any

import pandas as pd


__names__ = ["Leaf", "LeafStats"]


class LeafStats(NamedTuple):

    id: str
    lesion_area: int
    leaf_area: int
    ichloro_sum: float
    mask_area: int
    time: int | None
    position: tuple[float, float] | None = None


    @classmethod
    def from_images(
        cls,
        id: str,
        lesion: np.ndarray,
        leaf: np.ndarray,
        ichloro: np.ndarray,
        mask: np.ndarray,
        time: int | None = None,
        position: tuple[float, float] | None = None
    ) -> "LeafStats":
        lesion_area = np.sum(lesion)
        leaf_area = np.sum(leaf) + np.sum(lesion)
        ichloro_area = np.sum(ichloro)
        mask_area = np.sum(mask)
        return cls(
            id,
            lesion_area,
            leaf_area,
            ichloro_area,
            mask_area,
            time,
            position
        )

    @classmethod
    def header(cls) -> str:
        return "\t".join([
            "id",
            "time",
            "lesion_area",
            "leaf_area",
            "ichloro_sum",
            "mask_area",
            "x",
            "y"
        ])

    def __str__(self) -> str:
        if self.time is None:
            time = "."
        else:
            time = str(self.time)

        row = [
            self.id,
            time,
            str(self.lesion_area),
            str(self.leaf_area),
            str(round(self.ichloro_sum, 2)),
            str(self.mask_area),
        ]

        if self.position is None:
            row.extend([".", "."])
        else:
            row.extend([
                str(round(self.position[0], 1)),
                str(round(self.position[1], 1))
            ])

        return "\t".join(row)

    def as_dict(self) -> dict[str, Any]:
        if self.position is None:
            x = None
            y = None
        else:
            x, y = self.position

        return {
            "id": self.id,
            "time": self.time,
            "lesion_area": self.lesion_area,
            "leaf_area": self.leaf_area,
            "ichloro_sum": self.ichloro_sum,
            "mask_area": self.mask_area,
            "x": x,
            "y": y
        }

    def as_pandas(self) -> pd.Series:
        return pd.Series(self.as_dict())


class Leaf:
    def __init__(
        self,
        id,
        img,
        time: int | None = None,
        position: tuple[float, float] | None = None,
        mask_type: Literal["threshold", "otsu", "watershed", "original", "none"] = "watershed",
        mask: np.ndarray | None = None,
        exclude_mask: np.ndarray | None = None,
        mask_erode: int | None = None,
        min_object_size: int = 30
    ):
        self.id = id
        self.time = time
        self.position = position
        self.img_original  = img
        self.mask_type = mask_type
        self.mask = mask
        self.exclude_mask = exclude_mask
        self.mask_erode = mask_erode
        self.min_object_size = min_object_size
        return

    def get_mask(
        self,
        mask_type: Literal["threshold", "otsu", "watershed", "original", "none"] | None = None,
        erode: int | None = None
    ):
        import sys
        from skimage.color import rgb2gray
        from scipy import ndimage as ndi
        from INFEST.mask import (
            watershed_mask,
            threshold_mask,
            otsu_mask,
            original_mask,
            OTSUException
        )

        if mask_type is None:
            mask_type_ = self.mask_type
        else:
            mask_type_ = mask_type

        self.mask_type = mask_type_

        if erode is None:
            erode = self.mask_erode

        if erode is None:
            if mask_type_ in ("otsu", "watershed", "none"):
                erode_ = 2
            else:
                erode_ = 0
        else:
            erode_ = erode

        if mask_type_ == "threshold":
            mask = threshold_mask(self.img_original)
        elif mask_type_ == "otsu":
            try:
                mask = otsu_mask(self.img_original)
            except OTSUException:
                mask = np.full(self.img_original.shape[:-1], True)
                erode_ = 0
                print(
                    f"WARNING: While processing sample {self.id}, very low contrast.",
                    f"WARNING: Skipping this timepoint.",
                    file=sys.stderr
                )

        elif mask_type_ in ("watershed", "none"):
            try:
                mask = watershed_mask(
                    rgb2gray(self.img_original),
                    min_object_size=self.min_object_size
                )
            except OTSUException:
                mask = np.full(self.img_original.shape[:-1], True)
                erode_ = 0
                print(
                    f"WARNING: While processing sample {self.id}, very low contrast.",
                    f"WARNING: Skipping this timepoint.",
                    file=sys.stderr
                )

        elif mask_type_ == "original":
            mask = original_mask(self.img_original)
        else:
            raise ValueError("mask_type is invalid.")

        # This shrinks the mask to exclude some of the weird
        # edge bits.
        if erode_ > 0:
            mask = ndi.binary_erosion(
                mask,
                structure=np.ones((3, 3)),
                iterations=erode_
            )

        self.mask = mask

        if self.exclude_mask is not None:
            self.mask[self.exclude_mask] = 0
        return mask

    def ichloro(self):
        if self.mask is None:
            mask = np.asarray(self.get_mask())
        else:
            mask = np.asarray(self.mask)

        # This assertion is only for the type checker
        assert mask is not None

        if self.img_original.max() > 1:
            img = self.img_original
        else:
            img = np.clip(self.img_original * 255, 0, 255).astype("uint8")

        new = np.zeros(img.shape[:-1])
        coefs = [
            -0.0280 * 1.04938271604938,
            0.0190 * 1.04938271604938,
            -0.0030 * 1.04115226337449
        ]

        for i, coef in enumerate(coefs):
            new += coef * img[:, :, i]

        new = np.exp(new + 5.780)

        if self.mask_type != "none":
            new[~mask] = 0

        if self.exclude_mask is not None:
            new[self.exclude_mask] = 0

        return np.clip(new / 255, 0, 1)

    def lesion(self, f: float = 1.1):

        if self.mask is None:
            mask = np.asarray(self.get_mask())
        else:
            mask = np.asarray(self.mask)

        # This assertion is only for the type checker
        assert mask is not None

        img = self.img_original

        # Lesion is wherever the red is bigger than green channel.
        lesion = (f * img[:, :, 0]) > img[:, :, 1]

        if self.mask_type != "none":
            lesion[~mask] = False

        if self.exclude_mask is not None:
            lesion[self.exclude_mask] = False

        return lesion.astype(int)

    def leaf(self, f: float = 1.1):

        if self.mask is None:
            mask = np.asarray(self.get_mask())
        else:
            mask = np.asarray(self.mask)

        # This assertion is only for the type checker
        assert mask is not None

        img = self.img_original

        # leaf is wherever the green channel is bigger than red channel
        leaf = (f * img[:, :, 0]) < img[:, :, 1]

        if self.mask_type != "none":
            leaf[~mask] = False

        if self.exclude_mask is not None:
            leaf[self.exclude_mask] = False

        return leaf.astype(int)

    def stats(
        self,
        lesion: np.ndarray | None = None,
        leaf: np.ndarray | None = None,
        ichloro: np.ndarray | None = None,
    ) -> LeafStats:
        if lesion is None:
            lesion_ = self.lesion()
        else:
            lesion_ = lesion

        if leaf is None:
            leaf_ = self.leaf()
        else:
            leaf_ = leaf

        if ichloro is None:
            ichloro_ = self.ichloro()
        else:
            ichloro_ = ichloro

        if self.mask is None:
            mask = np.asarray(self.get_mask())
        else:
            mask = np.asarray(self.mask)

        return LeafStats.from_images(
            id=self.id,
            lesion=lesion_,
            leaf=leaf_,
            ichloro=ichloro_,
            mask=mask,
            time=self.time,
            position=self.position
        )

    def plot(
        self,
        lesion: np.ndarray | None = None,
        leaf: np.ndarray | None = None,
        ichloro: np.ndarray | None = None,
        path=None,
        show=False,
        dpi=300
    ):
        import matplotlib.pyplot as plt

        if (path is None) and not show:
            raise ValueError("Either path or show must be specified, otherwise we're not doing anything")

        if lesion is None:
            lesion_ = self.lesion()
        else:
            lesion_ = lesion

        if leaf is None:
            leaf_ = self.leaf()
        else:
            leaf_ = leaf

        if ichloro is None:
            ichloro_ = self.ichloro()
        else:
            ichloro_ = ichloro

        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(
            ncols=2,
            nrows=2,
            figsize=(6, 6),
        )
        ax1.imshow(self.img_original)
        ax1.axis('off')

        ax2.axis('off')
        ax2.text(0, 10, "Disease ", fontsize=6, color='White', verticalalignment="top")
        ax2.imshow(lesion_, cmap='inferno', alpha=0.9)

        ax3.axis('off')
        ax3.text(0, 10, "Leaf ", fontsize=6, color='White', verticalalignment="top")
        ax3.imshow(leaf_, cmap='inferno', alpha=0.9)

        ax4.axis('off')
        ax4.text(0, 10, "Chloro ", fontsize=6, color='White', verticalalignment="top")
        ax4.imshow(ichloro_, cmap='inferno')
        fig.subplots_adjust(hspace = 0, wspace = 0)

        if path is not None:
            plt.savefig(path, transparent=True, dpi=dpi, bbox_inches='tight', pad_inches=0)
        if show == True:
            plt.show()

        plt.close(fig)
        return fig
