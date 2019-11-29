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
from pymodelfit import *
from pymodelfit import FunctionModel1DAuto
import numpy as np
import sys
import argparse

class PolyModel(FunctionModel1DAuto):
	def f(self,x,a1=0.1,a2=0.1,a3=1,a4=2,a5=1):
		return a1*x**4+a2*x**3+a3*x**2+a4*x+a5

def get_residuals(model,fit_parameter,original_x,original_y):
	if model == "PolyModel":
		m = PolyModel()
		res = (original_y - m.f(original_x,a1=qm.pardict['a1'],a2=qm.pardict['a2'],a3=qm.pardict['a3'],a4=qm.pardict['a4'],a5=qm.pardict['a5']))**2
		res = np.mean(res)
	return res

def integrate(qm,df3):
	qb = PolyModel()
	t = np.arange(0,df3.t.tolist()[-1],0.5)
	ys = qb.f(t,a1=qm.pardict['a1'],a2=qm.pardict['a2'],a3=qm.pardict['a3'],a4=qm.pardict['a4'],a5=qm.pardict['a5']).tolist()
	ys -= qm.pardict['a5']
	ii=0
	tau_600 = 0
	tau_300 = 0
	while (ii<len(ys)-1):
		if(ys[ii]<300) & (ys[ii+1]>=300):
			tau_300 = t[ii]
		if(ys[ii]<800) & (ys[ii+1]>=800):
			tau_600 = t[ii]
			break
		ii+=1
	return tau_600-tau_300,tau_600

def m_plot(qm,df2,l):
	plt.figure(l.split('/')[-1])
	qm.plot()
	plt.plot(df2.t,df2.Lesion,'.',label="Lesion raw")
	plt.legend()
	show()

if __name__=="__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("path_in", help="the path to the file containing temporal data computed by INFEST")
	parser.add_argument("path_out", help="the path to the file containing LDT and Latency",default='')
	parser.add_argument("-g","--graph", action="store_true",help="monitoring the fit of the curve")
	args = parser.parse_args()

	# path = "/media/ab/Zeus/Phyto/Laz-5/res"+sys.argv[1]+"/"#+"/Nav"+sys.argv[3]+"/"

	print("Open "+args.path_in)
	df=pd.read_csv(args.path_in,sep="\t")

	df['t'] = (df['time'])*10
	leaf = np.unique(df.Id)

	out = "Nom\ta1\ta2\ta3\ta4\ta5\tres\tLDT\tLatency\n"
	ii = 0
	for l in leaf:
		df2 = df[(df.Id == l) & (df.t<1500)  & (df.t>600)]
		if size(df2.t[df2.Lesion>300]) > 10 :
			qm = PolyModel()
			qm.fitData(df2.t,df2.Lesion)
			if args.graph:
				m_plot(qm,df2,args.path_in+l)
			res = get_residuals("PolyModel",qm,df2.t,df2.Lesion)
			puissance63,puissance60 =  integrate(qm,df2)
			new_out = l+"\t"+str(qm.pardict['a1'])+"\t"+str(qm.pardict['a2'])+"\t"+str(qm.pardict['a3'])+"\t"+str(qm.pardict['a4'])+"\t"+str(qm.pardict['a5'])+"\t"+str(res)+"\t"+str(puissance63)+"\t"+str(puissance60)+"\n"
			out+= new_out
		else:
			fig = plt.figure(l.split('/')[-1])
			new_out = l+"\t"+str(0)+"\t"+str(0)+"\t"+str(0)+"\t"+str(0)+"\t"+str(0)+"\t"+str(0)+"\t"+str(0)+"\t"+str(0)+"\n"
			print("Bad Data: Lesion size < 30 pxl")

	print("save as "+args.path_out)
	f = open(args.path_out,"w")
	f.write(out)
	f.close()
