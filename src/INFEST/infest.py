#!/usr/bin/env python3

   ##     ###             ###     ##
  #       ###             ###       #
 #                                   #
 #        ###     ###     ###        #
 #        ###     ###     ###        #
  #        #       #       #        #
   ##     #       #       #       ##


import numpy as np
import sys
from skimage.color import rgb2gray
from skimage import io
from scipy.cluster.vq import kmeans, vq
from .leaf import Leaf
import os
from os.path import join as pjoin
from os.path import basename, splitext
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
        else :
            if os.path.isfile(self.path+'grid_layout/grid_layout.layout'):
                out = True
        if out == False:
            print("No layout found !\nPlease create a file 'grid_layout.layout' in\n"+self.path+"grid_layout")
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

def check_arg(path):
    import glob
    mstart, mstop = 0, 0
    file_list = glob.glob(pjoin(path, "*.jpg"))

    file_list.sort(key=lambda f: int("".join(filter(str.isdigit, f))))
    mstart = int(splitext(basename(file_list[0]))[1])
    mstop  = int(splitext(basename(file_list[-1]))[1])
    return mstart, mstop


def main(prog: str | None = None, argv: list[str] | None = None):

    if prog is None:
        prog = sys.argv[0]

    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(prog=prog)
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
    args = parser.parse_args(argv)
    infest(mpath=args.mpath, first=args.first, last=args.last)
    return


def infest(mpath: str, first: int = 0, last: int = 0):
    start, stop = check_arg(mpath)

    if first != 0 :
        start = first
    if last != 0 :
        stop = last

    if os.path.isfile(pjoin(mpath, "analyse.txt")) == False:
        f1 = pjoin(mpath, "analyse.txt")
    else:
        date_now = datetime.date.today().strftime("%B %d, %Y")
        f1 = pjoin(mpath, f"analyse_{date_now}.txt")

    f2 = pjoin(mpath, "area.txt")

    with open(f1, "w") as handle1, open(f2, "w") as handle2:
        # headers
        print("Id\ttime\tLesion", file=handle1)
        print("Id\tArea", file=handle2)
        for N in range(start, stop):
            out = ""
            print(f'\nImage {mpath} {str(N)}.jpg -> {str(stop)}.jpg')

            try:
                image = io.imread(pjoin(mpath, f"{str(N)}.jpg"))
                p = Panel(image, 2, mpath, N)
                for l in p.leaf_stack:
                    l.get_disease()
                    out = "\t".join([l.name, str(N), l.s_disease])
                    print(out, file=handle1)
                    s = "\t".join([l.name, str(l.leaf_area)])
                    print(s, file=handle2)

            except IOError:
                print(f"Image does not exist in {mpath}")
    return


if __name__ == "__main__":
    main()
