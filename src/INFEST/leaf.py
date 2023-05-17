#!/usr/bin/env python3

import numpy as np
import scipy as sp
import matplotlib.pyplot as plt
from skimage.measure import label
from skimage.measure import regionprops
from skimage.color import rgb2gray, rgb2hsv
from skimage import io

__names__ = ["Leaf"]

class Leaf:
    def __init__(self, image, name, v):
        self.name = name
        self.i_source  = image
        self.verbose = v
        self.i_disease = image
        self.path = ""
        self.time = 0
        self.hsv = image
        self.s_disease = 0
        self.s_tot = self.i_source.size / 3
        self.leaf_area = 0

    def m_print(self,inp,level):
        if self.verbose > level:
            print(inp)

    def fill_hole(self,im):
        re = []
        out = []
        fill = im[:,:,0].copy()
        label_image = label(fill)

        for region in regionprops(label_image):
            minr, minc, maxr, maxc = region.bbox
            temp = [int(minr), int(minc), int(maxr), int(maxc)]
            re.append(temp)
            out.append(temp)
        for ii in range(0,len(re)):
            for jj in range(0,len(re)):
                if jj != ii :
                    if (
                        (re[ii][0] > re[jj][0]) &
                        (re[ii][2] < re[jj][2]) &
                        (re[ii][1] > re[jj][1]) &
                        (re[ii][3] < re[jj][3])
                    ):
                        out.pop(out.index(re[ii]))
                        for i in range(re[ii][0],re[ii][2]):
                            for j in range(re[ii][1],re[ii][3]):
                                if (im[i,j,0] == 255) :
                                    im[i,j,0] = 0
                                    im[i,j,2] = 255
                        break
        return im

    def get_disease(self):
        f = 1.1

        self.hsv = rgb2hsv(self.i_source)
        back = rgb2gray(self.i_source).copy()
        leaf = rgb2gray(self.i_source).copy()
        dise = rgb2gray(self.i_source).copy()

        # 1 remove background
        back[self.hsv[:, :, 1] < 0.3] = 0
        back[self.hsv[:, :, 1] >= 0.3] = 1

        # Use background as a mask
        leaf = np.multiply(back, leaf)

        # Green shades correspond to leaf
        leaf[(np.multiply(f * self.i_source[:, :, 0],back) - np.multiply(self.i_source[:, :, 1], back)) < 0] = 1
        leaf[(np.multiply(f * self.i_source[:, :, 0],back) - np.multiply(self.i_source[:, :, 1], back)) >= 0] = 0

        # Red shades to disease
        dise[(np.multiply(f * self.i_source[:, :, 0],back) - np.multiply(self.i_source[:, :, 1], back)) > 0] = 1
        dise[(np.multiply(f * self.i_source[:, :, 0],back) - np.multiply(self.i_source[:, :, 1], back)) <= 0] = 0

        # Invert background
        back[back == 0] = 2
        back[back == 1] = 0
        back[back == 2] = 1

        # Output
        res = self.i_source.copy()
        self.s_disease = np.sum(dise)
        self.leaf_area = self.s_disease + np.sum(leaf)

        res[:, :, 0] = back * 255
        res[:, :, 1] = leaf * 255
        res[:, :, 2] = dise * 255

        # Fill gap due to plugs
        self.i_disease = self.fill_hole(res)
        return

    @staticmethod
    def get_mask(img):
        from skimage.color import rgb2gray
        from skimage.filters import threshold_otsu
        from skimage.morphology import closing as skiclosing, square as skisquare

        img_gs = rgb2gray(img)
        threshold = threshold_otsu(img_gs)
        mask = skiclosing(img_gs > threshold, skisquare(3))
        mask = ~sp.ndimage.binary_fill_holes(~mask)
        # This extends the object size a bit to remove any edge artifacts around edges of objects.
        mask = sp.ndimage.binary_dilation(mask, structure=np.ones((3, 3)), iterations=1)
        return mask

    def get_simple_mask(self, threshold=0.3):
        mask = (self.hsv[:, :, 1] >= threshold) \
            | (self.i_disease[:, :, 1] > 0) \
            | (self.i_disease[:, :, 2] > 0)
        return mask

    def get_ichloro(self):
        img = self.i_source.copy()

        new = np.zeros(img.shape[:-1])
        coefs = [
            -0.0280 * 1.04938271604938,
            0.0190 * 1.04938271604938,
            -0.0030 * 1.04115226337449
        ]

        for i, coef in enumerate(coefs):
            new += coef * img[:, :, i]

        new = np.exp(new + 5.780)

        if not hasattr(self, "hsv"):
            self.get_disease()

        mask = self.get_simple_mask()
        new[~mask] = np.nan
        self.i_ichloro = new
        self.ichloro = np.nansum(new)
        return

    def get_mean(self, inp):
        tab = []
        for region in inp:
            tab.append(region.area)
        return np.mean(tab), np.std(tab)

    def plot_result(self, path=None, show=False, dpi=300):

        if (path is None) and not show:
            raise ValueError("Either path or show must be specified, otherwise we're not doing anything")

        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(
            ncols=2,
            nrows=2,
            figsize=(6, 6),
        )
        ax1.imshow(self.i_source)
        ax1.axis('off')

        ax2.axis('off')
        ax2.text(0, 10, "Disease ", fontsize=6, color='White', verticalalignment="top")
        ax2.imshow(self.i_disease[:, :, 2], cmap='inferno', alpha=0.9)

        ax3.axis('off')
        ax3.text(0, 10, "Leaf ", fontsize=6, color='White', verticalalignment="top")
        ax3.imshow(np.multiply(self.i_disease[:, :, 1], self.i_source[:, :, 1]), cmap='inferno', alpha=0.9)

        ax4.axis('off')
        ax4.text(0, 10, "Chloro ", fontsize=6, color='White', verticalalignment="top")
        ax4.imshow(self.i_ichloro, cmap='inferno')
        fig.subplots_adjust(hspace = 0, wspace = 0)

        if path is not None:
            plt.savefig(path, transparent=True, dpi=dpi, bbox_inches='tight', pad_inches=0)
        if show == True:
            plt.show()

        plt.close(fig)
        return

if __name__ == '__main__':
    samples = ["s1.jpg","s2.jpg","s3.jpg","s4.jpg","s5.jpg","s6.jpg","s7.jpg","s8.jpg"]
    for s in samples:
        image_inp = io.imread("./sample/" + s)
        l = Leaf(image_inp, s, 1)
        l.get_disease()
        l.plot_result(path="test.jpg", show=True)
