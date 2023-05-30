#!/usr/bin/env python3

import os

from typing import NamedTuple, Literal
from typing import Iterator, Iterable
from typing import cast

import numpy as np

from .leaf import Leaf

__names__ = ["Panel", "LayoutRow"]


def maxclamp(integer: int, margin: int):
    return max([integer - margin, 0])


def minclamp(integer: int, margin: int, max_value: int | None = None):
    if max_value is not None:
        return min([integer + margin, max_value])
    else:
        return integer + margin


class LayoutRow(NamedTuple):

    id: str
    minr: int
    minc: int
    maxr: int
    maxc: int

    @classmethod
    def from_line(cls, line: str) -> "LayoutRow":
        sline = line.strip().split("\t")
        ints: list[int] = []
        for i, cn in enumerate(["minr", "minc", "maxr", "maxc"], 1):
            try:
                ints.append(int(sline[i]))
            except ValueError:
                raise ValueError(
                    f"Could not convert {cn} value '{sline[i]}' into an integer."
                )

        assert len(ints) == 4
        return cls(
            sline[0],
            ints[0],
            ints[1],
            ints[2],
            ints[3]
        )

    @classmethod
    def from_file(cls, handle: Iterable[str]) -> Iterator["LayoutRow"]:
        for i, line in enumerate(handle):
            try:
                yield cls.from_line(line)
            except ValueError as e:
                raise ValueError(f"Error while parsing on line {i}. {str(e)}")

        return
 
    def apply_margin(self, margin: int, maxr_val: int | None = None, maxc_val: int | None = None):
        minr = maxclamp(self.minr, margin)
        minc = maxclamp(self.minc, margin)
        maxr = minclamp(self.maxr, margin, maxr_val)
        maxc = minclamp(self.maxc, margin, maxc_val)
        return self.__class__(self.id, minr, minc, maxr, maxc)

    def get_position(self) -> tuple[float, float]:
        return ((self.minr + self.maxr) / 2, (self.minc + self.maxc) / 2)


class Panel:

    def __init__(
        self,
        image,
        layout: str,
        time: int | None = None,
        margin: int = 5,
        leaf_mask_type: Literal["threshold", "otsu", "watershed", "original"] = "watershed",
        panel_mask_type: Literal["threshold", "otsu", "watershed"] = "watershed",
    ):
        self.margin: int = margin
        self.leaf_mask_type = leaf_mask_type
        self.panel_mask_type = panel_mask_type
        self.time = time

        self.layout_path: str = layout
        self.layout: dict[str, LayoutRow] = self.__parse_layout(layout)
        self.img_original = image

        return

    def __parse_layout(self, layout: str | None = None) -> dict[str, LayoutRow]:

        if layout is None:
            gl = self.layout_path
        else:
            gl = layout

        if not os.path.exists(gl):
            raise ValueError(f"The grid_layout file in {gl} does not exist.")

        out: dict[str, LayoutRow] = dict()

        with open(gl, "r") as handle:
            for lr in LayoutRow.from_file(handle):
                out[lr.id] = lr

        return out

    def __getitem__(self, key: str) -> Leaf:
        it = self.get(key)

        if it is None:
            raise KeyError(f"There are no samples called {key}.")
        else:
            return it

    def get(
        self,
        key: str, margin: int | None = None,
        mask_type: Literal["threshold", "otsu", "watershed", "original"] | None = None,
    ) -> Leaf | None:

        if mask_type is None:
            mask_type_ = self.leaf_mask_type
        else:
            mask_type_ = mask_type

        # For the type checkers
        assert mask_type_ in ("threshold", "otsu", "watershed", "original")

        lr = self.layout.get(key, None)

        if lr is None:
            return None

        if margin is None:
            margin_: int = self.margin
        else:
            margin_ = margin

        if margin_ != 0:
            lr = lr.apply_margin(
                margin_,
                maxr_val=self.img_original.shape[0],
                maxc_val=self.img_original.shape[1]
            )

        img = self.img_original[lr.minr:lr.maxr, lr.minc:lr.maxc]
        return Leaf(
            lr.id,
            img,
            time=self.time,
            position=lr.get_position(),
            mask_type=mask_type_
        )

    def __iter__(self) -> Iterator[Leaf]:
        for key in self.layout.keys():
            yield self.__getitem__(key)
        return

    def get_grid_mask(self):
        grid = np.full(self.img_original.shape[:-1], False)

        for lr in self.layout.values():
            grid[lr.minr:lr.maxr, lr.minc:lr.maxc] = True

        return grid

    def correct_uniform(
        self,
        min_object_size: int = 500,
        mask_type: Literal["threshold", "otsu", "watershed"] | None = "otsu"
    ):
        from .norm_colours import correct_uniform

        if mask_type is None:
            mask_type_ = self.panel_mask_type
        else:
            mask_type_ = mask_type

        # For the type checkers
        assert mask_type_ in ("threshold", "otsu", "watershed")
        leaf_mask_type = self.leaf_mask_type
        assert leaf_mask_type in ("threshold", "otsu", "watershed", "original")

        grid = self.get_grid_mask()

        corrected = correct_uniform(
            self.img_original,
            min_object_size=min_object_size,
            mask_type=mask_type_,
            grid=grid
        )
        return Panel(
            corrected,
            layout=self.layout_path,
            margin=self.margin,
            leaf_mask_type=leaf_mask_type,
            panel_mask_type=mask_type_
        )

    def correct_nonuniform(
        self,
        min_object_size: int = 500,
        size: int = 10,
        mask_type: Literal["threshold", "otsu", "watershed"] | None = "otsu"
    ):
        from .norm_colours import correct_nonuniform

        if mask_type is None:
            mask_type_ = self.panel_mask_type
        else:
            mask_type_ = mask_type

        # For the type checkers
        assert mask_type_ in ("threshold", "otsu", "watershed")
        leaf_mask_type = self.leaf_mask_type
        assert leaf_mask_type in ("threshold", "otsu", "watershed", "original")

        grid = self.get_grid_mask()

        corrected = correct_nonuniform(
            self.img_original,
            min_object_size=min_object_size,
            size=size,
            mask_type=mask_type_,
            grid=grid
        )
        p = Panel(
            corrected,
            layout=self.layout_path,
            margin=self.margin,
            leaf_mask_type=leaf_mask_type,
            panel_mask_type=mask_type_
        )
        return p


    def plot_layout(self, dpi: float | None = None):
        import matplotlib
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches

        if dpi is None:
            dpi_ = matplotlib.rcParams['figure.dpi']
        else:
            dpi_ = dpi

        #height, width, _ = self.img_original.shape

        # What size does the figure need to be in inches to fit the image?
        #figsize = (width / dpi_, height / dpi_)

        fig = plt.figure(
            figsize=(6, 6),
            dpi=dpi_
        )
        ax = fig.add_subplot()
        ax.set_axis_off()

        ax.imshow(self.img_original)

        for lr in self.layout.values():
            rect = mpatches.Rectangle(
                (lr.minc, lr.minr),
                lr.maxc - lr.minc,
                lr.maxr - lr.minr,
                fill=False,
                edgecolor='red',
                linewidth=2
            )
            ax.add_patch(rect)
            ax.text(
                lr.minc + (lr.maxc - lr.minc) * 0.1,
                lr.minr + (lr.maxr - lr.minr) / 2,
                lr.id,
                fontsize=4,
                color="black"
            )
        return fig

    def save(
        self,
        path: str,
        layout: bool = False,
        dpi: float = 150
    ):
        import os

        os.makedirs(os.path.dirname(path), exist_ok=True)

        # Type annotation from subplots is FigureBase, which doesn't have savefig defined.

        if layout:
            from matplotlib.figure import Figure
            fig = self.plot_layout(dpi=dpi)
            fig = cast(Figure, fig)
            fig.savefig(path)
        else:
            from skimage.io import imsave
            imsave(path, self.img_original)
        return
