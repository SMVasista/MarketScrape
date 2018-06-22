from __future__ import division
import csv, copy, re, pickle, os, math
import statistics
import numpy as NP
import fileutils as fl
########################################
#All customized mathematical calculations
#are defined here.
########################################

#Global
e = 2.718281828

def numeric(string):
	try:
		if type(string) != float:
			if ',' in string:
				u = re.sub('\,', '', string)
			else:
				u = float(string)
		else:
			u = float(string)
	except:
		u = 0.0
	return u

def estCurveTrend(series):
	#Fits a curve y = ae^bx + y(0) for a given series
	#Hence ln(y) = ln(a) + bx - Ignoring the tivial case
	#Which fits a curve y = mx+c
	
	xaxis = []
	for i in range(len(series)):
		xaxis.append(float(i))

	o = [math.log((v/series[0]), e) for v in series]

	sigmaxi = 0
	sigmax2i = 0
	sigmaxiyi = 0
	sigmayi = 0
	for i in range(len(xaxis)):
		#Computing co-efficient components for the matrix
		sigmayi += o[i]
		sigmaxi += xaxis[i]
		sigmax2i += xaxis[i]*xaxis[i]
		sigmaxiyi += o[i]*xaxis[i]
	A_matrix = NP.matrix([[len(xaxis), sigmaxi], [sigmaxi, sigmax2i]])
	B_matrix = NP.matrix([[sigmayi], [sigmaxiyi]])
	result = NP.dot(A_matrix.I, B_matrix)
	ln_a = float(result[0][0])
	b = float(result[1][0])
	

	#Result matrix contains [ ln(a), b ]

	pred = [((e**ln_a * e**(b*i))*series[0]) for i in range(len(series))]

	correl = NP.corrcoef(series, pred)
	
	return e**ln_a, b, correl[0][1]


def estMAVSeries(series):
	ser = [float(series[0])]
	for elem in series:
		ser.append((ser[len(ser)-1]*(len(ser))+elem))
		ser[len(ser)-1] = ser[len(ser)-1]/(len(ser))
	ser.pop(0)
	return ser
	

def estProgParam(tupSeries):
	#Given a time-series data tuple-list, calculates moving average series, standard deviation and curve.
	val = [numeric(v[1]) for v in sorted(tupSeries)]
	mAvgSeries = estMAVSeries(val)
	
	seriesAvg = NP.mean(val)
	seriesStdv = NP.std(val)

	
	a_actual, b_actual, correl_actual = estCurveTrend(val)
	a_MAV, b_MAV, correl_MAV = estCurveTrend(estMAVSeries(val))

	return seriesAvg, seriesStdv, (a_MAV, b_MAV, correl_actual)


if __name__=="__main__":
		script = sys.argv
		pass




