#!/usr/bin/env python3

   ##     ###             ###     ##
  #       ###             ###       #
 #                                   #
 #        ###     ###     ###        #
 #        ###     ###     ###        #
  #        #       #       #        #
   ##     #       #       #       ##


import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys
import argparse


__names__ = ["infest"]


def integrate(qm2, df3, ft):
    t = np.arange(0,df3.t.tolist()[-1],0.5)
    ys = np.poly1d(qm2[0])(t)
    ii=0
    tau_600 = 0
    tau_300 = 0

    while (ii < len(ys) - 1):
        if(ys[ii] < ft) & (ys[ii + 1] >= ft):
            tau_300 = t[ii]
        if(ys[ii] < 2 * ft) & (ys[ii + 1] >= 2 * ft):
            tau_600 = t[ii]
            break
        ii += 1

    return tau_600 - tau_300, tau_600


def m_plot(qm2, df2, l):
    from os.path import basename
    plt.figure(basename(l))
    plt.plot(
        df2.t,
        np.poly1d(qm2[0])(df2.t),
        '--',
        label="model"
    )
    plt.plot(df2.t, df2.Lesion, '.', label="Lesion raw")
    plt.legend()
    plt.show()


def main(prog: str | None = None, argv: list[str] | None = None):
    from os.path import basename

    if prog is None:
        prog = sys.argv[0]

    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(prog=basename(prog))
    parser.add_argument(
        "path_in",
        help="the path to the file containing temporal data computed by INFEST"
    )
    parser.add_argument(
        "path_out",
        help="the path to the file containing LDT and Latency",
        default=''
    )
    parser.add_argument(
        "-ft",
        "--first",
        help="the first time to consider for the computation of the LDT",
        type=int,
        default=300
    )
    parser.add_argument(
        "-g",
        "--graph",
        action="store_true",
        help="monitoring the fit of the curve"
    )

    args = parser.parse_args(argv)

    infest(
        args.path_in,
        args.path_out,
        args.first,
        args.graph
    )
    return


def infest(
    path_in: str,
    path_out: str,
    first: int = 300,
    graph: bool = False,
):

    # print(f"Open {path_in}")
    df = pd.read_csv(path_in, sep="\t")

    df['t'] = df['time'] * 10

    out = "Id\ta1\ta2\ta3\ta4\ta5\tresiduals\tLDT\tLatency\n"
    for leaf, subdf in df.groupby("Id"):
        if subdf.loc[subdf["Lesion"] > 300, "t"].size > 10:
            qm2 = np.polyfit(subdf["t"], subdf["Lesion"], 4, full=True)
            if graph:
                m_plot(qm2, subdf, f"{path_in}{str(leaf)}")

            res = qm2[1][0]
            puissance63, puissance60 = integrate(qm2, subdf, first)
            new_out = "\t".join([
                str(leaf),
                str(qm2[0][0]),
                str(qm2[0][1]),
                str(qm2[0][2]),
                str(qm2[0][3]),
                str(qm2[0][4]),
                str(res),
                str(puissance63),
                str(puissance60)
            ]) + "\n"
            out+= new_out
        else:
            new_out = f"{leaf}\t0\t0\t0\t0\t0\t0\t0\t0\n"
            print("Bad Data: Lesion size < 30 pxl")

    print(f"save as {path_out}")
    with open(path_out, "w") as handle:
        handle.write(out)
    return


if __name__=="__main__":
    main()
