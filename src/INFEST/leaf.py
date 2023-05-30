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
    time: int | None
    position: tuple[float, float] | None = None


    @classmethod
    def from_images(
        cls,
        id: str,
        lesion: np.ndarray,
        leaf: np.ndarray,
        ichloro: np.ndarray,
        time: int | None = None,
        position: tuple[float, float] | None = None
    ) -> "LeafStats":
        lesion_area = np.sum(lesion)
        leaf_area = np.sum(leaf) + np.sum(lesion)
        ichloro_area = np.sum(ichloro)
        return cls(
            id,
            lesion_area,
            leaf_area,
            ichloro_area,
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
        mask_type: Literal["threshold", "otsu", "watershed", "original"] = "watershed",
        mask: np.ndarray | None = None,
        mask_erode: int | None = None,
        min_object_size: int = 30
    ):
        self.id = id
        self.time = time
        self.position = position
        self.img_original  = img
        self.mask_type = mask_type
        self.mask = mask
        self.mask_erode = mask_erode
        self.min_object_size = min_object_size
        return

    def get_mask(
        self,
        mask_type: Literal["threshold", "otsu", "watershed", "original"] | None = None,
        erode: int | None = None
    ):
        from skimage.color import rgb2gray
        from scipy import ndimage as ndi
        from INFEST.mask import watershed_mask, threshold_mask, otsu_mask, original_mask

        if mask_type is None:
            mask_type_ = self.mask_type
        else:
            mask_type_ = mask_type

        if erode is None:
            erode = self.mask_erode

        if erode is None:
            if mask_type_ in ("otsu", "watershed"):
                erode_ = 2
            else:
                erode_ = 0
        else:
            erode_ = erode

        if mask_type_ == "threshold":
            mask = threshold_mask(self.img_original)
        elif mask_type_ == "otsu":
            mask = otsu_mask(self.img_original)
        elif mask_type_ == "watershed":
            mask = watershed_mask(rgb2gray(self.img_original), min_object_size=100)
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
        return mask

    # Since this was only used to fill the plug when plotting
    # the images, i've removed the definition.
    # It doesn't help the analysis and may prevent interpretability.
    # @staticmethod
    # def __fill_hole(img: np.ndarray) -> np.ndarray:
    #     from skimage.measure import label
    #     from skimage.measure import regionprops
    #     re = []
    #     out = []
    #     fill = img[:, :, 0].copy()
    #     label_image = label(fill)

    #     for region in regionprops(label_image):
    #         minr, minc, maxr, maxc = region.bbox
    #         temp = [int(minr), int(minc), int(maxr), int(maxc)]
    #         re.append(temp)
    #         out.append(temp)

    #     for ii in range(0,len(re)):
    #         for jj in range(0,len(re)):
    #             if jj != ii :
    #                 if (
    #                     (re[ii][0] > re[jj][0]) &
    #                     (re[ii][2] < re[jj][2]) &
    #                     (re[ii][1] > re[jj][1]) &
    #                     (re[ii][3] < re[jj][3])
    #                 ):
    #                     out.pop(out.index(re[ii]))
    #                     for i in range(re[ii][0],re[ii][2]):
    #                         for j in range(re[ii][1],re[ii][3]):
    #                             if (img[i, j, 0] == 255):
    #                                 img[i, j, 0] = 0
    #                                 img[i, j, 2] = 255
    #                     break
    #     return img

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
        new[~mask] = 0
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

        lesion[~mask] = False
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
        leaf[~mask] = False
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

        return LeafStats.from_images(
            id=self.id,
            lesion=lesion_,
            leaf=leaf_,
            ichloro=ichloro_,
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
