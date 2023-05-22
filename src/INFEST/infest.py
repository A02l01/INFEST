#!/usr/bin/env python3

   ##     ###             ###     ##
  #       ###             ###       #
 #                                   #
 #        ###     ###     ###        #
 #        ###     ###     ###        #
  #        #       #       #        #
   ##     #       #       #       ##


import numpy as np
import pandas as pd
import sys
from skimage.color import rgb2gray
from skimage import io
from scipy.cluster.vq import kmeans, vq
from matplotlib import pyplot as plt
from matplotlib import animation as anim

from .leaf import Leaf
import os
from os.path import join as pjoin
from os.path import basename, splitext
from multiprocessing import Pool
from tempfile import TemporaryDirectory
import functools
import datetime
import argparse


__names__ = ["fit", "Panel"]


class Panel:
    def __init__(self, image, v, path, N):
        self.N = N
        self.verbose = v
        self.path = path
        # self.sub = []
        # self.read_sub()
        self.i_original = image
        self.i_rgb_thre = self.remove_background()
        self.leaf_stack = []
        self.i_file = rgb2gray(self.i_rgb_thre)
        self.Nx = 0
        self.Ny = 0
        self.exist_layout = self.test_layout()
        if self.exist_layout == False:
            sys.exit()
        else:
            self.order_bb1()

    def test_layout(self):
        out = False
        if not os.path.exists(pjoin(self.path, 'grid_layout')):
            os.makedirs(pjoin(self.path, 'grid_layout'), exist_ok=True)
            print("grid_layout directory has been created")
        else:
            out = os.path.isfile(pjoin(self.path, 'grid_layout', 'grid_layout.layout'))
        if out == False:
            print("No layout found !\nPlease create a file 'grid_layout.layout' in\n"+ pjoin(self.path, "grid_layout"))
            sys.exit()
        return out

    # def m_plot(self, s, sho):
    #     self.m_print("Plotting panel image",0)
    #     fig, ax = plt.subplots(ncols=1, nrows=1, figsize=(6, 6))
    #     ax.imshow(self.i_label_overlay)
    #     N =  0
    #     for r in self.to_plot:
    #         # draw rectangle around segmented coins
    #         minr, minc, maxr, maxc = r[0].bbox
    #         rect = mpatches.Rectangle((minc, minr), maxc - minc, maxr - minr, fill=False, edgecolor='red', linewidth=2)
    #         ax.add_patch(rect)
    #         ax.text(minc,minr, r[3].replace("_", "\n"), fontsize=4, color="white")
    #         N += 1

    #     if s == True:
    #         plt.savefig(pjoin(self.path, "grid_layout", f"panel{str(self.N)}.jpg"), dpi=250)
    #     if sho == True:
    #         plt.show()
    #     plt.close(fig)

    # def get_mean(self):
    #     tab = []
    #     for region in regionprops(self.label_image):
    #         tab.append(region.area)
    #     return np.mean(tab),np.std(tab)

    def get_layout(self):
        self.m_print("Finding panel layout", 0)
        found = False
        layout, tab = [], []
        for fi in os.listdir(self.path):
            if fi.endswith(".thelay"):
                with open(pjoin(self.path, fi),'r') as f:
                    for l in f.readlines():
                        tab = l.split()
                        self.Nx = len(tab)
                        for n in tab:
                            layout.append(n)
                        self.Ny += 1

                found = True

        if found == False:
            print("Layout file not found !")
            sys.exit(1)

        self.layout = layout

    def find_grid(self, inp):
        dx,dy = [],[]
        outx,outy = [],[]
        for i in inp:
            dy.append([i[2], 0])
        data = np.vstack(dy)
        centroids, _ = kmeans(data, self.Ny)
        idx, _ = vq(data, centroids)
        for ii in range(0, self.Ny):
            mini = np.min(data[idx == ii, 0])
            maxi = np.max(data[idx == ii, 0])
            outy.append([mini, maxi])

        outy = sorted(outy, key=lambda s:s[1])
        dx = []
        for i in inp:
            dx.append([i[1], 0])

        data = np.vstack(dx)
        centroids, _ = kmeans(data, self.Nx)
        idx, _ = vq(data, centroids)

        for ii in range(0, self.Nx):
            mini = np.min(data[idx == ii, 0])
            maxi = np.max(data[idx == ii, 0])
            outx.append([mini, maxi])

        outx.sort(key=lambda s: s[1])

        out = []
        for y in range(0, len(outy)):
            for x in range(0, len(outx)):
                k = 0
                for k in range(0, len(inp)):
                    if (inp[k][1] >= outx[x][0]) and (inp[k][1] <= outx[x][1]) and (inp[k][2] >= outy[y][0]) and (inp[k][2] <= outy[y][1]):
                        out.append(inp[k])
                    else:
                        k += 1
        return out

    def my_resize(self, minr, minc, maxr, maxc):
        margin = 5
        if minr - margin > 0:
            minr -= margin
        else :
            minr = 0
        if minc - margin > 0:
            minc -= margin
        else:
            minc = 0
        maxr += margin
        maxc += margin
        return minr, minc, maxr, maxc

    def order_bb1(self):
        # print("Use of existing layout")
        with open(pjoin(self.path, "grid_layout", "grid_layout.layout"),'r') as f:
            for l in f:
                tab = l[:-1].split()
                minr, minc, maxr, maxc = float(tab[1]), float(tab[2]), float(tab[3]), float(tab[4])
                minr, minc, maxr, maxc = self.my_resize(minr, minc, maxr, maxc)
                l = Leaf(
                    self.i_rgb_thre[int(minr):int(maxr), int(minc):int(maxc)],
                    tab[0],
                    self.verbose
                )
                self.leaf_stack.append(l)

    def m_print(self, inp, level):
        if self.verbose > level:
            print(inp)

    def remove_background(self):
        temp = self.i_original
        return temp


def write_animation(
    sample,
    time,
    lesion_area,
    leaf_area,
    ichloro,
    images_orig,
    images_lesion,
    images_leaf,
    images_ichloro,
    where_to,
    dpi=300,
    framestep=100,
):
    print(f"- {sample}")
    fig, axs = plt.subplots(
        ncols=2,
        nrows=4,
        figsize=(9, 9),
        width_ratios=[2, 1],
        sharex=False,
    )

    axs[0, 0].set_axis_off()
    axs[0, 0].text(0, 1, sample, fontsize=10, horizontalalignment="left")
    te = axs[0, 0].text(0, 0.5, "0", verticalalignment="bottom", horizontalalignment="right")

    axs[0, 1].set_axis_off()
    image_orig = axs[0, 1].imshow(io.imread(images_orig[0]), interpolation=None)

    axs[1, 0].scatter(x=time, y=lesion_area, s=10, marker="o", alpha=0.5)
    axs[1, 0].set_ylabel("Lesion area", fontsize=10)
    axs[1, 0].xaxis.set_ticklabels([])

    axs[1, 1].set_axis_off()
    image_lesion = axs[1, 1].imshow(io.imread(images_lesion[0]), interpolation=None)

    axs[2, 0].scatter(x=time, y=leaf_area, s=10, marker="o", alpha=0.5)
    axs[2, 0].set_ylabel("Leaf area", fontsize=10)
    axs[2, 0].xaxis.set_ticklabels([])

    axs[2, 1].set_axis_off()
    image_leaf = axs[2, 1].imshow(io.imread(images_leaf[0]), interpolation=None)

    axs[3, 0].scatter(x=time, y=ichloro, s=10, marker="o", alpha=0.5)
    axs[3, 0].set_ylabel("ichloro sum", fontsize=10)
    axs[3, 0].set_xlabel("Time", fontsize=10)

    axs[3, 1].set_axis_off()
    image_ichloro = axs[3, 1].imshow(io.imread(images_ichloro[0]), interpolation=None)

    vl2 = axs[1, 0].axvline(x=0, c="red")
    vl3 = axs[2, 0].axvline(x=0, c="red")
    vl4 = axs[3, 0].axvline(x=0, c="red")

    plt.tight_layout(pad=0.1)

    def update(frame):
        idx, orig, lesion_, leaf_, ichloro_ = frame
        image_orig.set_data(io.imread(orig))
        image_lesion.set_data(io.imread(lesion_))
        image_leaf.set_data(io.imread(leaf_))
        image_ichloro.set_data(io.imread(ichloro_))

        vl2.set_xdata([idx])
        vl3.set_xdata([idx])
        vl4.set_xdata([idx])
        te.set_text(str(idx))
        return image_orig, image_lesion, image_leaf, image_ichloro, vl2, vl3, vl4, te

    ani = anim.FuncAnimation(
        fig=fig,
        func=update,
        frames=list(zip(time, images_orig, images_lesion, images_leaf, images_ichloro)),
        interval=framestep,
        repeat=True
    )
    ani.save(pjoin(where_to, f"{sample}.mpeg"), writer="ffmpeg", dpi=dpi)
    plt.close()
    return

def write_animation2(
    sample,
    time,
    lesion_area,
    leaf_area,
    ichloro,
    images,
    where_to,
    dpi=300,
    framestep=100,
):
    print(f"- {sample}")
    fig, (ax1, ax2, ax3, ax4) = plt.subplots(
        ncols=1,
        nrows=4,
        figsize=(6, 9),
        height_ratios=[3, 2, 2, 2],
    )

    ax1.set_axis_off()
    image = ax1.imshow(io.imread(images[0]), interpolation=None)

    ax2.scatter(x=time, y=lesion_area, s=10, marker="o", alpha=0.5)
    ax2.set_ylabel("Lesion area", fontsize=10)

    ax3.scatter(x=time, y=leaf_area, s=10, marker="o", alpha=0.5)
    ax3.set_ylabel("Leaf area", fontsize=10)

    ax4.scatter(x=time, y=ichloro, s=10, marker="o", alpha=0.5)
    ax4.set_ylabel("ichloro sum", fontsize=10)
    ax4.set_xlabel("Time", fontsize=10)

    vl2 = ax2.axvline(x=0, c="red")
    vl3 = ax3.axvline(x=0, c="red")
    vl4 = ax4.axvline(x=0, c="red")
    te = ax2.text(len(lesion_area), 0, "0", verticalalignment="bottom", horizontalalignment="right")
    fig.subplots_adjust(hspace = 0, wspace = 0)

    fig.suptitle(sample, fontsize=10, horizontalalignment="left")

    plt.tight_layout(pad=0.1)

    def update(frame):
        idx, fname = frame
        i = io.imread(fname)
        image.set_data(i)
        vl2.set_xdata([idx])
        vl3.set_xdata([idx])
        vl4.set_xdata([idx])
        te.set_text(str(idx))
        return image, vl2, vl3, vl4, te

    ani = anim.FuncAnimation(
        fig=fig,
        func=update,
        frames=list(zip(time, images)),
        interval=framestep,
        repeat=True
    )
    ani.save(pjoin(where_to, f"{sample}.mpeg"), writer="ffmpeg", dpi=dpi)
    plt.close()
    return


def check_arg(path):
    import glob
    mstart, mstop = 0, 0
    file_list = glob.glob(pjoin(path, "*.jpg"))

    file_list.sort(key=lambda f: int("".join(filter(str.isdigit, f))))
    mstart = int(splitext(basename(file_list[0]))[0])
    mstop  = int(splitext(basename(file_list[-1]))[0])
    return mstart, mstop


def main(prog: str | None = None, argv: list[str] | None = None):

    if prog is None:
        prog = sys.argv[0]

    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(prog=basename(prog))
    parser.add_argument(
        "mpath",
        help="Path to the directory containing pictures"
    )
    parser.add_argument(
        "-f",
        "--first",
        type=int,
        help="Number of the first picture",
        default=0
    )
    parser.add_argument(
        "-l",
        "--last",
        type=int,
        help="Number of the last picture",
        default=0
    )
    parser.add_argument(
        "-w", "--write-video",
        type=str,
        help="Write videos of samples to this directory",
        default=None
    )
    parser.add_argument(
        "-n", "--ncpu",
        type=int,
        help="How many images to process in parallel.",
        default=1
    )
    parser.add_argument(
        "-d", "--dpi",
        type=int,
        help="If writing a video, what resolution should it have?",
        default=300,
    )
    parser.add_argument(
        "-s", "--framestep",
        type=int,
        help=(
            "If writing a video, how many milliseconds should each image be displayed for. "
            "E.g. framestep=100 (default) means 10 images will be displayed per second."
        ),
        default=100
    )
    args = parser.parse_args(argv)
    infest(
        mpath=args.mpath,
        first=args.first,
        last=args.last,
        write_video=args.write_video,
        ncpu=args.ncpu,
        framestep=args.framestep,
    )
    return


def process_image(
    N: int,
    fname: str,
    mpath: str,
    write_video: str | None,
    tmpdir: str,
):
    from matplotlib.colors import Normalize
    norm = Normalize(vmin=0, vmax=255)
    cm = plt.get_cmap("inferno")
    print(f'- processing image {fname}')


    image = io.imread(fname)
    output = list()
    p = Panel(image, 2, mpath, N)
    for l in p.leaf_stack:
        l.get_disease()
        l.get_ichloro()

        record = {
            "id": l.name,
            "time": N,
            "lesion_area": l.s_disease,
            "leaf_area": l.leaf_area,
            "ichloro_sum": l.ichloro,
            "fname_orig": None,
            "fname_lesion": None,
            "fname_leaf": None,
            "fname_ichloro": None,
        }

        if write_video is not None:
            bname = pjoin(tmpdir, f"{l.name}_time{N:0>5}")
            fname = f"{bname}_orig.jpg"
            record["fname_orig"] = fname
            io.imsave(fname, l.i_source, check_contrast=False)

            fname = f"{bname}_lesion.jpg"
            record["fname_lesion"] = fname
            img = cm(norm(l.i_disease[:, :, 2]))
            img = np.clip(img[:, :, :3] * 255, 0, 255).astype("uint8")
            io.imsave(fname, img, check_contrast=False)

            fname = f"{bname}_leaf.jpg"
            record["fname_leaf"] = fname
            img = cm(norm(l.i_disease[:, :, 1]))
            img = np.clip(img[:, :, :3] * 255, 0, 255).astype("uint8")
            io.imsave(fname, img, check_contrast=False)

            fname = f"{bname}_ichloro.jpg"
            record["fname_ichloro"] = fname
            img = cm(norm(l.i_ichloro))
            img = np.clip(img[:, :, :3] * 255, 0, 255).astype("uint8")
            io.imsave(fname, img, check_contrast=False)

        output.append(record)

    return pd.DataFrame(output)


def infest(
    mpath: str,
    first: int = 0,
    last: int = 0,
    write_video: str | None = None,
    ncpu: int = 1,
    dpi: int = 300,
    framestep: int = 100
):
    start, stop = check_arg(mpath)

    if first != 0 :
        start = first
    if last != 0 :
        stop = last

    if os.path.isfile(pjoin(mpath, "analyse.txt")) == False:
        f1 = pjoin(mpath, "analyse.txt")
    else:
        date_now = datetime.date.today().strftime("%Y%m%d")
        f1 = pjoin(mpath, f"analyse_{date_now}.txt")


    print(f"Processing images in: {mpath}")
    with open(f1, "w") as handle, TemporaryDirectory() as tmpdir:
        jpgs = []
        for N in range(start, stop):
            fname = pjoin(mpath, f"{N}.jpg")
            if os.path.exists(fname):
                jpgs.append((N, fname))
            else:
                print(f"WARNING: image does not exist in {mpath}")

        with Pool(ncpu) as p:
            results = p.starmap(
                functools.partial(process_image, mpath=mpath, write_video=write_video, tmpdir=tmpdir),
                jpgs
            )

        print("Done!")

        df = pd.concat(results)
        df.sort_values(by=["time", "id"])
        df.drop(
            columns=["fname_orig", "fname_lesion", "fname_leaf", "fname_ichloro"]
        ).to_csv(handle, sep="\t", header=True, index=False)

        if write_video is not None:
            print(f"Writing animation to: {write_video}")
            os.makedirs(write_video, exist_ok=True)
            jobs = []
            for name, subdf in df.groupby("id"):
                jobs.append((
                    name,
                    subdf["time"],
                    subdf["lesion_area"],
                    subdf["leaf_area"],
                    subdf["ichloro_sum"],
                    subdf["fname_orig"].tolist(),
                    subdf["fname_lesion"].tolist(),
                    subdf["fname_leaf"].tolist(),
                    subdf["fname_ichloro"].tolist()
                ))


            wa = functools.partial(
                write_animation,
                where_to=write_video,
                dpi=dpi,
                framestep=framestep
            )

            with Pool(ncpu) as p:
                p.starmap(wa, jobs)

    return


if __name__ == "__main__":
    main()
