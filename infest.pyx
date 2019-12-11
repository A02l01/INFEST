
   ##     ###             ###     ##
  #       ###             ###       #
 #                                   #
 #        ###     ###     ###        #
 #        ###     ###     ###        #
  #        #       #       #        #
   ##     #       #       #       ##


import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import sys
from skimage import data
from skimage import data, io
from skimage.filters import threshold_otsu
from skimage.segmentation import clear_border
from skimage.measure import label
from skimage.morphology import closing, square
from skimage.measure import regionprops
from skimage.color import label2rgb
from skimage.color import rgb2gray
from skimage import data, io
from matplotlib import pyplot as plt
from skimage.measure import regionprops
from skimage import io
from scipy.cluster.vq import *
from my_image import *
from leaf import *
import os
import datetime
import argparse

class panel:
	def __init__(self,image,v,path,N):
		self.N = N
		self.verbose = v
		self.path = path
		# self.sub = []
		# self.read_sub()
		self.i_original = image
		self.i_rgb_thre = self.remove_background()
		self.leaf_stack=[]
		self.i_file = rgb2gray(self.i_rgb_thre)
		self.Nx = 0
		self.Ny = 0
		self.exist_layout = self.test_layout()
		if self.exist_layout == False:
			sys.exit()
		else :
			self.order_bb1()

	def test_layout(self):
		out = False
		if not os.path.exists(self.path+'grid_layout/'):
			os.mkdir(self.path+'grid_layout/')
			print("grid_layout directory has been created")
		else :
			if os.path.isfile(self.path+'grid_layout/grid_layout.layout'):
				out = True
		if out == False:
			print("No layout found !\nPlease create a file 'grid_layout.layout' in\n"+self.path+"grid_layout")
			sys.exit()
		return out
#
#
	def m_plot(self,s,sho):
		self.m_print("Plotting panel image",0)
		fig, ax = plt.subplots(ncols=1, nrows=1, figsize=(6, 6))
		ax.imshow(self.i_label_overlay)
		N =  0
		for r in self.to_plot:
			# draw rectangle around segmented coins
			minr, minc, maxr, maxc = r[0].bbox
			rect = mpatches.Rectangle((minc, minr), maxc - minc, maxr - minr,fill=False, edgecolor='red', linewidth=2)
			ax.add_patch(rect)
			ax.text(minc,minr, r[3].replace("_","\n"), fontsize=4,color="white")
			N = N+1
		if s == True:
			plt.savefig(self.path+"grid_layout/panel"+str(self.N)+".jpg",dpi=250)
		if sho == True:
			plt.show()
		plt.close(fig)
#
	def get_mean(self):
		tab = []
		for region in regionprops(self.label_image):
			tab.append(region.area)
		return np.mean(tab),np.std(tab)

	def get_layout(self):
		self.m_print("Finding panel layout",0)
		found = False
		layout,tab = [],[]
		for fi in os.listdir(self.path):
			if fi.endswith(".thelay"):
				f = open(self.path+fi,'r')
				for l in f.readlines():
					tab = l.split()
					self.Nx = len(tab)
					for n in tab:
						layout.append(n)
					self.Ny += 1
				f.close()
				found = True
		if found == False:
			print("Layout file not found !",0)
			sys.exit(0)
		self.layout = layout

	def find_grid(self,inp):
		dx,dy = [],[]
		outx,outy = [],[]
		for i in inp:
			dy.append([i[2],0])
		data = np.vstack(dy)
		centroids,_ = kmeans(data,self.Ny)
		idx,_ = vq(data,centroids)
		for ii in range(0,self.Ny):
			mini = np.min(data[idx==ii,0])
			maxi = np.max(data[idx==ii,0])
			outy.append([mini,maxi])
		outy = sorted(outy[:],key=lambda s:s[1])
		dx = []
		for i in inp:
			dx.append([i[1],0])
		data = np.vstack(dx)
		centroids,_ = kmeans(data,self.Nx)
		idx,_ = vq(data,centroids)
		for ii in range(0,self.Nx):
			mini = np.min(data[idx==ii,0])
			maxi = np.max(data[idx==ii,0])
			outx.append([mini,maxi])
		outx = sorted(outx[:],key=lambda s:s[1])

		out = []
		for y in range(0,len(outy)):
			for x in range(0,len(outx)):
				k = 0
				for k in range(0,len(inp)):
					if (inp[k][1]>= outx[x][0]) and (inp[k][1]<=outx[x][1]) and (inp[k][2]>=outy[y][0]) and (inp[k][2]<=outy[y][1]):
						out.append(inp[k])
					else:
						k+=1
		return out

	def my_resize(self,minr,minc,maxr,maxc):
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
		return minr,minc,maxr,maxc

	def order_bb1(self):
		# print("Use of existing layout")
		f = open(self.path+"grid_layout/grid_layout.layout",'r')
		for l in f:
			tab = l[:-1].split()
			minr, minc, maxr, maxc = float(tab[1]),float(tab[2]),float(tab[3]),float(tab[4])
			minr, minc, maxr, maxc = self.my_resize(minr, minc, maxr, maxc)
			l = leaf(self.i_rgb_thre[int(minr):int(maxr),int(minc):int(maxc)],tab[0],self.verbose)
			self.leaf_stack.append(l)
		f.close()
#
	def m_print(self,inp,level):
		if self.verbose > level:
			print(inp)
#
	def remove_background(self):
		temp = self.i_original
		return temp

def check_arg(path):
	import glob
	mstart,mstop=0,0
	file_list = glob.glob(path+"*.jpg")
	file_list.sort(key=lambda f: int(filter(str.isdigit, f)))
	mstart = int(file_list[0].split('/')[-1].split('.')[0])
	mstop  = int(file_list[-1].split('/')[-1].split('.')[0])
	return mstart, mstop

if __name__ == "__main__":
	#sys.argv[1] -> path
	#sys.argv[2] -> first picture
	#sys.argv[3] -> last picture

	# mpath = "/media/ab/Zeus/Phyto/Marie/Exp7/"
	parser = argparse.ArgumentParser()
	parser.add_argument("mpath", help="Path to the directory containing pictures")
	parser.add_argument("-f", "--first",type=int, help="Number of the first picture",default=0)
	parser.add_argument("-l", "--last",type=int, help="Number of the last picture",default=0)
	args = parser.parse_args()
	# start,stop = 0,0
	start,stop = check_arg(args.mpath)

	if args.first != 0 :
		start = args.first
	if args.last != 0 :
		stop = args.last

	if(os.path.isfile(args.mpath+"/analyse.txt")==False):
		f1 = open(args.mpath+"/analyse.txt","w")
	else :
		date_now = datetime.date.today().strftime("%B %d, %Y")
		f1 = open(args.mpath+"/analyse"+"_"+date_now+".txt","w")
	# headers
	f1.write("Id\ttime\tLesion\n")
	for N in range(start,stop):
		out=""
		sys.stdout.write('\rImage '+args.mpath+str(N)+".jpg -> "+str(stop)+".jpg")
		sys.stdout.flush()
		try:
			image = io.imread(args.mpath+str(N)+".jpg")
			p = panel(image,2,args.mpath,N)
			for l in p.leaf_stack:
				l.get_disease()
				out = l.name+"\t"+str(N)+"\t"+str(l.s_disease)+"\n"
				f1.write(out)
		except IOError:
			print("Image does not exist in "+args.mpath)
			pass
	f1.close()
