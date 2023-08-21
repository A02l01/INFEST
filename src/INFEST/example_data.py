#!/usr/bin/env python3

import argparse
from shutil import copytree
import os
import sys

from INFEST.data import gmax_dir, atha_dir, marca_dir

def main(prog: str | None = None, argv: list[str] | None = None):
    from os.path import basename

    if prog is None:
        prog = sys.argv[0]

    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(prog=basename(prog))
    parser.add_argument(
        "dataset",
        choices=["atha", "gmax", "marca"],
        help="Which dataset to get."
    )
    parser.add_argument(
        "-o", "--outdir",
        help=(
            "Where to save the example directory to. "
            "Will raise an error if the target directory already exits."
        ),
        default=None
    )
    args = parser.parse_args(argv)

    if args.outdir is None:
        args.outdir = args.dataset

    if os.path.exists(args.outdir):
        raise ValueError(
            f"Targeted outdir '{args.outdir}' already exists. "
            "Please delete it or specify a new outdir with --outdir."
        )

    if args.dataset == "atha":
        copytree(atha_dir, args.outdir)
    elif args.dataset == "gmax":
        copytree(gmax_dir, args.outdir)
    elif args.dataset == "marca":
        copytree(marca_dir, args.outdir)
    else:
        raise ValueError("This shouldn't be possible.")

    return
