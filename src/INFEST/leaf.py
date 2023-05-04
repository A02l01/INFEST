#!/usr/bin/env python3

import numpy as np
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
        # image_label_overlay = label2rgb(label_image, image=im)

        for region in regionprops(label_image):
            minr, minc, maxr, maxc = region.bbox
            temp = [int(minr), int(minc), int(maxr), int(maxc)]
            re.append(temp)
            out.append(temp)
        for ii in range(0,len(re)):
            for jj in range(0,len(re)):
                if jj != ii :
                    if (re[ii][0]>re[jj][0]) & (re[ii][2]<re[jj][2]) & (re[ii][1]>re[jj][1]) & (re[ii][3]<re[jj][3]) :
                        out.pop(out.index(re[ii]))
                        for i in range(re[ii][0],re[ii][2]):
                            for j in range(re[ii][1],re[ii][3]):
                                if (im[i,j,0] == 255) :
                                    im[i,j,0]=0
                                    im[i,j,2]=255
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


    def get_mean(self, inp):
        tab = []
        for region in inp:
            tab.append(region.area)
        return np.mean(tab), np.std(tab)

    def plot_result(self, s, path, sho):

        fig, ((ax1,ax3,ax4,ax5)) = plt.subplots(ncols=1, nrows=4)
        plt.subplots_adjust( hspace=0)
        ##
        ax1.imshow(self.i_source)
        ax1.axis('off')
        ax1.text(0,10,"Original "+self.name, fontsize=15, color='Black')
        ##
        ax3.axis('off')
        ax3.text(0,10,"Disease ", fontsize=15, color='White')
        ax3.imshow(self.i_disease[:, :, 2], cmap='inferno', alpha=0.9)
        ##
        ax4.axis('off')
        ax4.text(0, 10, "Background ", fontsize=15, color='Black')
        ax4.imshow(np.multiply(self.i_disease[:,:,0], self.i_source[:,:,1]), cmap='inferno', alpha=0.9)
        ##
        ax5.axis('off')
        ax5.text(0, 10, "Leaf ", fontsize=15, color='White')
        ax5.imshow(np.multiply(self.i_disease[:, :, 1], self.i_source[:, :, 1]), cmap='inferno', alpha=0.9)

        if s == True:
            plt.savefig(path, transparent=True)
        if sho == True:
            plt.show()

        plt.close(fig)
        return

if __name__ == '__main__':
    samples = ["s1.jpg","s2.jpg","s3.jpg","s4.jpg","s5.jpg","s6.jpg","s7.jpg","s8.jpg"]
    for s in samples:
        image_inp = io.imread("./sample/" + s)
        l = Leaf(image_inp, s, 1)
        l.get_disease()
        l.plot_result(False, "test", True)
