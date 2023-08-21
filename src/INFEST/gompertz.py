#!/usr/bin/env python3

import pandas as pd
import numpy as np 

from matplotlib import pyplot as plt
from typing import NamedTuple


class GompertzCoefs(NamedTuple):

    sample: str
    U: float
    L: float
    kG: float
    Ti: float
    slope: float
    yintercept: float
    sd: float
    statistic: str | None = None

    def update(
        self,
        sample: str | None = None,
        U: float | None = None,
        L: float | None = None,
        kG: float | None = None,
        Ti: float | None = None,
        slope: float | None = None,
        yintercept: float | None = None,
        sd: float | None = None,
        statistic: float | None = None
    ) -> "GompertzCoefs":
        return self.__class__(
            sample if (sample is not None) else self.sample,
            U if (U is not None) else self.U,
            L if (L is not None) else self.L,
            kG if (kG is not None) else self.kG,
            Ti if (Ti is not None) else self.Ti,
            slope if (slope is not None) else self.slope,
            yintercept if (yintercept is not None) else self.yintercept,
            sd if (sd is not None) else self.sd,
            statistic if (statistic is not None) else self.statistic
        )


class Gompertz(object):

    """ Fit and predict values using a Gompertz growth model.

    Honestly, this doesn't need to be a class. It would work just as/more
    cleanly with functions on a datastructure containing the parameters.
    But can't be bothered changing it now.
    """

    def __init__(self, sample: str):
        self.sample = sample
        return

    def reset(self):
        for a in ["U", "L", "kG", "Ti", "sd", "slope", "yintercept"]:
            if hasattr(self, a):
                delattr(self, a)
        return

    def __initialise(self, X: np.ndarray, y: np.ndarray) -> None:
        """ Find good starting values for fitting the gompertz function

        Arguments:
         x -- The x values we'll be fitting (e.g. time)
         y -- The y values we'll be fitting to (e.g. lesion area)
        """
        from scipy.stats import linregress

        self.reset()

        U = np.max(y) * 1.05
        L = np.min(y) * 0.95

        ## Linear regression on pseudo y values
        pseudoY = np.log(-np.log((y - L) / (U - L)))
        mask = np.isfinite(pseudoY)

        lm = linregress(X[mask], pseudoY[mask])
        k = lm.intercept
        kG = -lm.slope
        Ti = k / kG

        self.U = U
        self.L = L
        self.Ti = Ti
        self.kG = kG
        return

    def fit(self, X: np.ndarray, y: np.ndarray) -> "Gompertz":
        from scipy.optimize import least_squares

        self.__initialise(X, y)

        model = least_squares(
            self.__loss,
            [self.U, self.L, self.Ti, self.kG],
            args=(X, y),
            method="lm"
        )

        self.U = model.x[0]
        self.L = model.x[1]
        self.Ti = model.x[2]
        self.kG = model.x[3]

        self.sd = np.sqrt(np.mean(self.loss(X, y)))
        self.slope = self.derivative(self.Ti)
        self.yintercept = self.predict(self.Ti) - (self.Ti * self.slope)
        return self

    @property
    def coefs(self) -> GompertzCoefs:
        return GompertzCoefs(
            self.sample,
            self.U,
            self.L,
            self.kG,
            self.Ti,
            self.slope,
            self.yintercept,
            self.sd
        )

    @classmethod
    def __loss(
        cls,
        coefs: tuple[float, float, float, float],
        X: np.ndarray,
        y: np.ndarray
    ) -> np.ndarray:
        U, L, Ti, kG = coefs
        yhat = cls.__predict(X, U, L, Ti, kG)
        return (y - yhat) ** 2

    def loss(self, X: np.ndarray, y: np.ndarray) -> np.ndarray:
        return self.__loss(
            (self.U, self.L, self.Ti, self.kG),
            X,
            y
        )

    @staticmethod
    def __predict(
        X: np.ndarray,
        U: float,
        L: float,
        Ti:float,
        kG: float
    ) -> np.ndarray:
        return L + (U - L) * np.exp(-np.exp(-kG * (X - Ti)))

    def predict(self, X: np.ndarray) -> np.ndarray:
        """ Compute a gompertz function with parameters
         x  -- The x values (e.g. time)
         U  -- The upper plateau y value
         L  -- The lower plateau y value
         Ti -- The slope inflection point
         kG -- The growth rate
        """

        assert hasattr(self, "kG")
        return self.__predict(X, self.U, self.L, self.Ti, self.kG)

    def derivative(self, X: np.ndarray) -> np.ndarray:
        """ Finds the tangent for a gompertz function at point x. """
        assert hasattr(self, "kG")
        
        return (
            (self.U - self.L) *
            self.kG *
            np.exp(-np.exp(-self.kG * (X - self.Ti)) - self.kG * (X - self.Ti))
        )

    def __call__(self, X: np.ndarray, y: np.ndarray) -> tuple[GompertzCoefs, pd.DataFrame]:
        df = pd.DataFrame({
            "sample": self.sample,
            "x": X,
            "y": y,
            "yhat": self.predict(X),
            "derivative": self.derivative(X)
        })
        return self.coefs, df

    @classmethod
    def call(cls, X: np.ndarray, y: np.ndarray, sample: str) -> tuple["Gompertz", GompertzCoefs, pd.DataFrame]:
        self = cls(sample)
        self.fit(X, y)

        c, d = self(X, y)
        return self, c, d


def plot_gompertz(coefs, preds, **kwargs):
    fig, ax = plt.subplots(1, 1, **kwargs)

    if coefs.sample is not None:
        fig.suptitle(coefs.sample)

    ax.axvline(x=coefs.Ti, alpha = 0.5)
    ax.axhline(y=coefs.U, alpha = 0.5)
    ax.axhline(y=coefs.L, alpha = 0.5)

    ax.plot(preds["x"], preds["yhat"], color="red", lw=4, alpha=0.5)
    ax.scatter(preds["x"], preds["y"], alpha=1)
    ax.axline((0, coefs.yintercept), slope=coefs.slope, color="green")

    ymin = preds["y"].min()
    ymax = preds["y"].max()
    yoffset = (ymax - ymin) * 0.05
    xmin = preds["x"].min()
    xmax = preds["x"].max()
    xoffset = (xmax - xmin) * 0.05

    ax.set_ylim((ymin - yoffset, ymax + yoffset))
    ax.set_xlim((xmin - xoffset, xmax + xoffset))
    return fig, ax


def fit(infile, prefix):
    from matplotlib.backends.backend_pdf import PdfPages

    df = pd.read_csv(infile, sep="\t")

    coef_results = list()
    preds_results = list()

    with PdfPages(f"{prefix}-lesion_area.pdf") as la_pdf, \
            PdfPages(f"{prefix}-ichloro_sum.pdf") as ic_pdf:
        for sample, subdf in df.groupby("id"):
            _, coefs, preds = Gompertz.call(
                subdf["time"].values,
                subdf["lesion_area"].values,
                sample=sample
            )

            coefs.update(statistic="lesion_area")
            preds["statistic"] = "lesion_area"
            coef_results.append(coefs)
            preds_results.append(preds)

            fig, ax = plot_gompertz(coefs, preds, figsize=(6, 6))
            ax.set_xlabel("time")
            ax.set_ylabel("lesion_area")

            la_pdf.savefig(fig)
            plt.close()

            _, coefs, preds = Gompertz.call(
                subdf["time"].values,
                subdf["ichloro_sum"].values,
                sample=sample
            )

            coefs.update(statistic="ichloro_sum")
            preds["statistic"] = "ichloro_sum"
            coef_results.append(coefs)
            preds_results.append(preds)

            fig, ax = plot_gompertz(coefs, preds, figsize=(6, 6))
            ax.set_xlabel("time")
            ax.set_ylabel("ichloro_sum")

            ic_pdf.savefig(fig)
            plt.close()


    coef_df = pd.DataFrame(coef_results)
    coef_df.to_csv(f"{prefix}-coef.tsv", sep="\t", index=False)

    preds_df = pd.concat(preds_results)
    preds_df.to_csv(f"{prefix}-preds.tsv", sep="\t", index=False)



def main(prog: str = None, argv: list[str] | None = None):
    import sys
    from os.path import basename
    import argparse

    if prog is None:
        prog = sys.argv[0]

    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(prog=basename(prog))
    parser.add_argument(
        "infile",
        type=argparse.FileType("r"),
        help="The time-series data."
    )

    parser.add_argument(
        "-o", "--outprefix",
        type=str,
        default="infest_results",
        help="Where should we write the results?"
    )


    args = parser.parse_args(argv)
    fit(args.infile, args.outprefix)


