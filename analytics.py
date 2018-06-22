from __future__ import division
import csv, copy, re, pickle, os, math
import statistics
import numpy as NP
import xlsxwriter as xw
import fileutils as fl
import datutils
import mathutils
#########################################
#This module is for statistical analysis
#of data and inferencing / reporting. All
#mathematical utilities are borrowed from
#mathutils.py
#########################################

#Global
summaryHeader = ['Sl.No','Company_Name/ID','CurrentPrice', 'FundamentalSummary', 'BalanceSheetSummary', 'Flags', 'TechnicalSummary', 'StockEvaluationSummary', 'CompositeRank', 'FundamentalRank', 'TechnicalRank']
DetailHeader = ['Sl.No', 'Company_Name/ID', 'CurrentPrice', 'expEstimate', 'P/E', 'EPS', 'Deliverables', 'MCapital', 'ComparitiveGrowth', 'RiskFactor', 'historicMean', 'curveType', 'price_b', 'price_a', 'price_compositeCorrel', 'vol_b', 'vol_a', 'vol_compositeCorrel', 'basisPrice']

def deTexDict(dictionary):
	newDict = {}
	for param in dictionary.keys():
		newDict[param] = mathutils.numeric(dictionary[param])
	return newDict

def initStrategy():
	termScale = raw_input('Enter investment term [S|M|L] as [Short|Medium|Long]: ')
	volScale = float(raw_input('Enter Budget (in Rupees): '))
	consvScale = raw_input('Conservative Scale [H|M] as [High-Risk|Moderate-Risk]: ')
	fScale = float(raw_input('From a scale of 1-10, enter how imporant fundamental analysis should be: '))
	tScale = float(raw_input('From a scale of 1-10, enter how imporant technical analysis should be: '))
	print "Building Strategy..."
	fScale = float(fScale/(fScale+tScale))
	tScale = float(tScale/(fScale+tScale))
	if consvScale == 'H':
		if termScale == 'M' or termScale == 'L':
			riskTh = 0.5
		else:
			riskTh = 0.65
	elif consvScale == 'M':
		if termScale == 'M' or termScale == 'L':
			riskTh = 0.6
		else:
			riskTh = 0.7
	else:
		riskTh = 0.7
	initials = (volScale, termScale, consvScale)
	params = (fScale, tScale, riskTh)
	return initials, params

def initPipeline():
	#Initializing company-wise fundamental analysis and technical analysis
	
	try:
		firList = [v[0] for v in fl.readLinesAndSplit('./ifirm.list', ',')]
	except:
		fileLoc = raw_input('ifirm.list data not found. Please pass firlist as <Company_Name>,<BSE>_<NSE> format: ')
		firList = [v[0] for v in fl.readLinesAndSplit(fileLoc, ',')]
	try:
		with open('./fData.dump','r') as f:
			fDataDump = pickle.load(f)
	except:
		print "Extracted fundamental analysis not found... Please run datautils and try again"
		exit(0)
	try:
		with open('./tData.dump','r') as f:
			tDataDump = pickle.load(f)
	except:
		print "Extracted technical analysis not found... Please run datautils and try again"
		exit(0)

	fRank = {}
	tRank = {}

	with open('./summary_report.csv','a') as s:
		for elem in summaryHeader:
			s.write(str(elem)+',')
		s.write('\n')

	with open('./detailed_report.csv','a') as d:
		for elem in DetailHeader:
			d.write(str(elem)+',')
		d.write('\n')		


	for serNo, firm in enumerate(firList):
		firmAliasf = None
		firmAliast = None

		ratio_factor = 0
		fl_factor = 0
		bs_factor = 0
		out_p_factor = 0

		print "Initilizing Analysis for : ", firm
		fRank[firm] = 0
		tRank[firm] = 0
		#Initiating fundamental analysis
		#For indexing rules check documentation #TODO
		firmAliasf = firm
		shareVal = 0.0
		print "Firm: ", firm, "Alias: ", firmAliasf
		if firmAliasf in fDataDump.keys():
			if fDataDump[firmAliasf]['fBasic'] != None:
				fBasicTemp = deTexDict(fDataDump[firmAliasf]['fBasic'])

				if fBasicTemp['6M-Returns'] >= -10.0 and fBasicTemp['1Y-Returns'] >= 15:
					fRank[firm] += 0.1*(math.tanh((mathutils.numeric(fBasicTemp['capital'])/100) + (mathutils.numeric(fBasicTemp['volume'])/100000)))
				else:
					fRank[firm] += -0.2
			if fDataDump[firmAliasf]['fRatios'] != None:
				shareVal = fDataDump[firmAliasf]['fRatios']['currPrice']
				fBasicTemp = deTexDict(fDataDump[firmAliasf]['fRatios'])
				ratio_factor = (2/(2+fBasicTemp['pe-ratio'])) + (fBasicTemp['eps-ratio']/10) + (fBasicTemp['deliv']/200)
				fRank[firm] += 0.4*(ratio_factor)

			if fDataDump[firmAliasf]['f-pl-data'] != None:
				fPlDataTemp = deTexDict(fDataDump[firmAliasf]['f-pl-data'])
				fl_factor = (mathutils.numeric(fPlDataTemp['sales_3Y'])/100) + (mathutils.numeric(fPlDataTemp['PAT_3Y'])/100)
				fRank[firm] += 0.3*(fl_factor)

			if fDataDump[firmAliasf]['f-bs-data'] != None: 
				bsDataTemp = deTexDict(fDataDump[firmAliasf]['f-bs-data'])
				bs_factor = (mathutils.numeric(bsDataTemp['total_asset_growth_3Y'])/100 + mathutils.numeric(bsDataTemp['total_liabilities_growth_3Y'])/100 + mathutils.numeric(bsDataTemp['total_reserves_change_3Y'])/100)
				fRank[firm] += 0.4*(bs_factor)

			if fDataDump[firmAliasf]['f-tech'] != None:
				ftDataTemp = deTexDict(fDataDump[firmAliasf]['f-tech'])
				out_p_factor = mathutils.numeric(ftDataTemp['growth_vs_sensex_3Y'])/100 + mathutils.numeric(ftDataTemp['growth_vs_NIFTY_3Y'])/100
				fRank[firm] += 0.4*(out_p_factor)

			print "fAnalysis completed successfully for: ", firmAliasf
		else:
			print "Something went wrong... fAnalysis did not complete"
		
		
		if firmAliast == None:
			for firmName in tDataDump.keys():
				if fDataDump[firm]['fIDs']['BSE'].split(' ')[0] == firmName.split('_')[0]:
					firmAliast = firmName
					break
		if firmAliast == None:
			for firmName in tDataDump.keys():
				if fDataDump[firm]['fIDs']['NSE'] in firmName.split('_')[1]:
					firmAliast = firmName
					break			
		#Continuing forward, we use the alias to assign the tRanks
		print "Firm: ", firm, "Alias: ", firmAliast

		price_sAvg = 0
		price_sVar = 0
		price_model = (0, 0, 0)
		vol_sAvg = 0
		vol_sVar = 0
		vol_model = (0, 0, 0)
		expectedPrice = 0

		if firmAliast in tDataDump.keys():
		
			if tDataDump[firmAliast]['t-price'] != None and len(tDataDump[firmAliast]['t-price']) > 2:
				tPriceTemp = tDataDump[firmAliast]['t-price']
				price_sAvg, price_sVar, price_model = mathutils.estProgParam(tPriceTemp)
				tRank[firm] += 0.6*(price_model[0] + 10*price_model[1] + price_model[2]**2)
				expectedPrice = price_model[0]*(2.718281828**(price_model[1]*(len(tPriceTemp)+1)))*mathutils.numeric(tPriceTemp[0][1])
				print firm, "Actual Price: ", shareVal, "Expected Price: ", expectedPrice
				if shareVal != 0.0 and shareVal < (expectedPrice - 1.5*price_sVar):
					if (0.3*fDataDump[firmAliasf]['fBasic']['6M-Returns'])+(0.7*fDataDump[firmAliasf]['fBasic']['1Y-Returns']) > 0:
						tRank[firm] += 1
					elif (0.3*fDataDump[firmAliasf]['fBasic']['6M-Returns'])+(0.7*fDataDump[firmAliasf]['fBasic']['1Y-Returns']) < 0:
						tRank[firm] -= 0.3
					else:
						tRank[firm] += 0.1
				elif shareVal != 0.0 and (expectedPrice - 0.5*price_sVar) < shareVal < (expectedPrice + 0.5*price_sVar):
					if (0.3*fDataDump[firmAliasf]['fBasic']['6M-Returns'])+(0.7*fDataDump[firmAliasf]['fBasic']['1Y-Returns']) > 0:
						tRank[firm] += 0.5
				elif shareVal != 0.0 and shareVal > (expectedPrice + price_sVar):
					if (0.3*fDataDump[firmAliasf]['fBasic']['6M-Returns'])+(0.7*fDataDump[firmAliasf]['fBasic']['1Y-Returns']) > 0:
						tRank[firm] -= 0.3
					else:
						tRank[firm] -= 0.5
				else:
					tRank[firm] += 0.05
			if tDataDump[firmAliast]['t-vol'] != None and len(tDataDump[firmAliast]['t-vol']) > 2:
				tVolTemp = tDataDump[firmAliast]['t-vol']
				vol_sAvg, vol_sVar, vol_model = mathutils.estProgParam(tVolTemp)
				tRank[firm] += 0.1*(vol_model[0] + vol_model[1] + vol_model[2]**2)
			
			print "tAnalysis completed successfully for: ", firmAliast
		else:
			print "Something went wrong... tAnalysis did not complete"
		print "\n\n"
		#Appending all information into report.
		FundamentalSummary = None
		BalanceSheetSummary = None
		TechnicalSummary = None
		StockEvaluationSummary = None
		
		try:

			if fDataDump[firmAliasf]['fBasic']['6M-Returns'] >= -10.0 and fDataDump[firmAliasf]['fBasic']['1Y-Returns'] >= 15:
				if ratio_factor > 1:
					FundamentalSummary = "Very Good"
				elif ratio_factor > 0:
					FundamentalSummary = "Good"
				else:
					FundamentalSummary = "Poor"
			elif (0.3*fDataDump[firmAliasf]['fBasic']['6M-Returns'])+(0.7*fDataDump[firmAliasf]['fBasic']['1Y-Returns']) > 0:
				if ratio_factor > 1:
					FundamentalSummary = "Good"
				elif ratio_factor > 0:
					FundamentalSummary = "Average"
				else:
					FundamentalSummary = "Poor"
			else:
				FundamentalSummary = "Poor"

			if bs_factor > 1:
				BalanceSheetSummary = "Very Good"
			elif bs_factor > 0:
				BalanceSheetSummary = "Good"
			else:
				BalanceSheetSummary = "Poor"


			if price_model[1] > 0 and price_model[2] > 0.75:
				TechnicalSummary = "Good"
			elif price_model[1] < 0:
				TechnicalSummary = "Poor"

			if shareVal != 0.0 and shareVal < (expectedPrice - 1.5*price_sVar):
				if out_p_factor > 0:
					StockEvaluationSummary = "\"Under-priced, Outperformer\""
				else:
					StockEvaluationSummary = "\"Under-priced, Non-performer\""
			elif shareVal != 0.0 and (expectedPrice - 0.5*price_sVar) < shareVal < (expectedPrice + 0.5*price_sVar):
				if out_p_factor > 0:
					StockEvaluationSummary = "\"apt-priced, Outperformer\""
				else:
					StockEvaluationSummary = "\"apt-priced, Non-performer\""
			elif shareVal != 0.0 and shareVal > (expectedPrice + price_sVar):
				if out_p_factor > 0:
					StockEvaluationSummary = "\"over-priced, Outperformer\""
				else:
					StockEvaluationSummary = "\"over-priced, Non-performer\""

			compositeRank = ((fRank[firm]/2)+tRank[firm])

			curveType = None
			if fDataDump[firmAliasf]['fBasic']['6M-Returns']*fDataDump[firmAliasf]['fBasic']['1Y-Returns'] < 0:
				curveType = "cyclic"
			elif fDataDump[firmAliasf]['fBasic']['6M-Returns']*fDataDump[firmAliasf]['fBasic']['1Y-Returns'] > 0:
				if price_model[1] > 0:
					curveType = "Basic-Positive"
				else:
					curveType = "Basic-Negative"
			with open('./summary_report.csv','a') as s:
				s.write(str(serNo)+','+str(firm)+','+str(shareVal)+','+str(FundamentalSummary)+','+str(BalanceSheetSummary)+','+str('None')+','+str(TechnicalSummary)+','+str(StockEvaluationSummary)+','+str(compositeRank)+','+str(fRank[firm])+','+str(tRank[firm])+'\n')

			with open('./detailed_report.csv','a') as d:
				d.write(str(serNo)+','+str(firm)+','+str(shareVal)+','+str(expectedPrice)+','+str(fDataDump[firmAliasf]['fRatios']['pe-ratio'])+','+str(fDataDump[firmAliasf]['fRatios']['eps-ratio'])+','+str(fDataDump[firmAliasf]['fRatios']['deliv'])+','+str(mathutils.numeric(fDataDump[firmAliasf]['fBasic']['capital']))+','+'\"'+str(fDataDump[firmAliasf]['f-tech'])+'\"'+','+str(price_sVar)+','+str(price_sAvg)+','+str(curveType)+','+str(price_model[1])+','+str(price_model[0])+','+str(price_model[2])+','+str(vol_model[1])+','+str(vol_model[0])+','+str(vol_model[2])+','+str(mathutils.numeric(tDataDump[firmAliast]['t-price'][0][1]))+'\n')

		except:
			with open('./summary_report.csv','a') as s:
				s.write(str(serNo)+','+str(firm)+','+'NA-NA-NA'+'\n')

			with open('./detailed_report.csv','a') as d:
				d.write(str(serNo)+','+str(firm)+','+'NA-NA-NA'+'\n')
				

if __name__=="__main__":
	initPipeline()


