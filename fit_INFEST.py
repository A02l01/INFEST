#!/usr/bin/python

   ##     ###             ###     ##
  #       ###             ###       #
 #                                   #
 #        ###     ###     ###        #
 #        ###     ###     ###        #
  #        #       #       #        #
   ##     #       #       #       ##


import pandas as pd
from pylab import *
import matplotlib.pyplot as plt
import numpy as np
import sys
import argparse

def get_residuals(model,fit_parameter,original_x,original_y):
	if model == "PolyModel":
		m = PolyModel()
		res = (original_y - m.f(original_x,a1=qm.pardict['a1'],a2=qm.pardict['a2'],a3=qm.pardict['a3'],a4=qm.pardict['a4'],a5=qm.pardict['a5']))**2
		res = np.mean(res)
	return res

def integrate(qm2,df3,ft):
	t = np.arange(0,df3.t.tolist()[-1],0.5)
	ys = np.poly1d(qm2[0])(t)
	# ys -= qm2[0][4]
	ii=0
	tau_600 = 0
	tau_300 = 0

	while (ii<len(ys)-1):
		if(ys[ii]<ft) & (ys[ii+1]>=ft):
			tau_300 = t[ii]
		if(ys[ii]<2*ft) & (ys[ii+1]>=2*ft):
			tau_600 = t[ii]
			break
		ii+=1

	return tau_600-tau_300,tau_600

def m_plot(qm2,df2,l):
	plt.figure(l.split('/')[-1])
	plt.plot(df2.t,np.poly1d(qm2[0])(df2.t),'--',label="model")
	plt.plot(df2.t,df2.Lesion,'.',label="Lesion raw")
	plt.legend()
	show()

if __name__=="__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("path_in", help="the path to the file containing temporal data computed by INFEST")
	parser.add_argument("path_out", help="the path to the file containing LDT and Latency",default='')
	parser.add_argument("-ft","--first", help="the first time to consider for the computation of the LDT",type=int,default=300,)
	parser.add_argument("-g","--graph", action="store_true",help="monitoring the fit of the curve")
	args = parser.parse_args()

	print("Open "+args.path_in)
	df=pd.read_csv(args.path_in,sep="\t")

	df['t'] = (df['time'])*10
	leaf = np.unique(df.Id)

	out = "Id\ta1\ta2\ta3\ta4\ta5\tresiduals\tLDT\tLatency\n"
	ii = 0
	for l in leaf:
		# df2 = df[(df.Id == l) & (df.t<1500)  & (df.t>600)]
		df2 = df[(df.Id == l)]
		if size(df2.t[df2.Lesion>300]) > 10 :
			qm2 = np.polyfit(df2.t,df2.Lesion,4,full=True)
			if args.graph:
				m_plot(qm2,df2,args.path_in+l)
			res = qm2[1][0]
			puissance63,puissance60 =  integrate(qm2,df2,args.first)
			new_out = l+"\t"+str(qm2[0][0])+"\t"+str(qm2[0][1])+"\t"+str(qm2[0][2])+"\t"+str(qm2[0][3])+"\t"+str(qm2[0][4])+"\t"+str(res)+"\t"+str(puissance63)+"\t"+str(puissance60)+"\n"
			out+= new_out
		else:
			fig = plt.figure(l.split('/')[-1])
			new_out = l+"\t"+str(0)+"\t"+str(0)+"\t"+str(0)+"\t"+str(0)+"\t"+str(0)+"\t"+str(0)+"\t"+str(0)+"\t"+str(0)+"\n"
			print("Bad Data: Lesion size < 30 pxl")

	print("save as "+args.path_out)
	f = open(args.path_out,"w")
	f.write(out)
	f.close()
