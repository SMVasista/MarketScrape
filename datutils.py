from __future__ import division
import csv, copy, re, pickle, os, math, random, sys
from bs4 import BeautifulSoup as soup
from selenium import webdriver
from time import sleep
import requests
import fileutils as fl
#######################################
#This utils will be used to manage data
#including  data scraping modification,
#editing rewriting, visualization.
#######################################

#######################################

driverpath = '/home/user1/Desktop/sumanth/MarketScrape-master/geckodriver'
cwd = os.getcwd()
cap = {}
cap["marionette"] = False
soS = 'http://www.hdfcsec.com'

def extractLinkList(sourceList):
	#This function extracts company links from hdfc securities datasite: www.hdfcsec.com#
	src = {}
	for i, source in enumerate(sourceList):
		print "Extracting Links from page: ", source, "(", i,"/",len(sourceList), ")" 
		driver = webdriver.Firefox(capabilities=cap, executable_path=driverpath)
		driver.get(source)
		html = unicode(driver.page_source.encode("utf-8"), "utf-8")
		data = soup(html, 'html.parser')
		driver.quit()
		b = data.findAll("div", {"class": "companyList"})
		for elem in b:
			try:
				link = elem.a['href']
				name = elem.a.get_text()
				src[str(link)] = str(name)
			except:
				pass
		wait = int(random.randint(-1,6) + 3)
		sleep(wait)
	print "Identified :", len(src), "companies for analysis"

	with open('./links.dump','w') as f:
		pickle.dump(src, f)

	return src

def scrapeData(linkSource):
	#Extract links iteratively, download information and store in specified datastructure#
	dump = {}
	for link in linkSource.keys():
		print "Extracting Data for: ", linkSource[link]
		mark = str(linkSource[link])
		dump[mark] = {}
		try:
			driver = webdriver.Firefox(capabilities=cap, executable_path=driverpath)
			driver.get(soS+str(link))
			html = unicode(driver.page_source.encode("utf-8"), "utf-8")
			data = soup(html, 'html.parser')
			driver.quit()
		except:
			print "Could not access/extract data for:", linkSource[link]
			exit(0)
				
		#Extracting company IDs#
		dump[mark]['fIDs'] = {'BSE': '', 'NSE': ''}
		try:
			ids = data.findAll("span", {"class": "group"})
			for elem in ids:
				if 'BSE' in elem.get_text().split(':')[0]:
					dump[mark]['fIDs']['BSE'] = elem.get_text().split(':')[1]
				elif 'NSE' in elem.get_text().split(':')[0]:
					dump[mark]['fIDs']['NSE'] = elem.get_text().split(':')[1]
				else:
					dump[mark]['fIDs'][elem.get_text().split(':')[0]] = elem.get_text().split(':')[1]
		except:
			print "ID extraction had an issue..."
			dump[mark]['fIDs'] = None
			
		#Extracting f-basic values#
		dump[mark]['fBasic'] = {}
		try:
			sData = data.findAll("div", {"id": "DvCompanySnapShotDetails"})
			r = sData[0].findAll("span", {"class":"name"})
			p = sData[0].findAll("span", {"class":"value"})
			kvPair = {}
			for i in range(len(r)):
				kvPair[str(r[i].get_text())] = str(p[i].get_text())
			try:
				dump[mark]['fBasic']['6M-Returns'] = float(kvPair['6M return'].split('%')[0])
			except:
				dump[mark]['fBasic']['6M-Returns'] = 0.0
			try:
				dump[mark]['fBasic']['1Y-Returns'] = float(kvPair['1Y return'].split('%')[0])
			except:
				dump[mark]['fBasic']['1Y-Returns'] = 0.0
			try:
				dump[mark]['fBasic']['capital'] = kvPair['MCap(Rs. in Cr.)']
			except:
				dump[mark]['fBasic']['capital'] = 0.0
			try:
				dump[mark]['fBasic']['volume'] = kvPair['Total Volume']
			except:
				dump[mark]['fBasic']['volume'] = 0.0
		except:
			print "Basic value extraction had an issue..."
			dump[mark]['fBasic'] = None

		#Extracting f-Ratios#
		dump[mark]['fRatios'] = {}
		try:
			try:
				dump[mark]['fRatios']['pe-ratio'] = float(data.findAll("div", {"id":"peRatio"})[0].get_text())
			except:
				dump[mark]['fRatios']['pe-ratio'] = 0.0
			try:
				dump[mark]['fRatios']['eps-ratio'] = float(data.findAll("div", {"id":"epsRATIO"})[0].get_text())
			except:
				dump[mark]['fRatios']['eps-ratio'] = 0.0
			try:
				dump[mark]['fRatios']['deliv'] = float(data.findAll("div", {"id":"deliverableRatio"})[0].get_text().split('%')[0])
			except:
				dump[mark]['fRatios']['deliv'] = 0.0
			#try:
			if True:
				tCurrPrice = data.findAll("div", {"id":"sliderDailyValue"})[0].get_text()
				if ',' in str(tCurrPrice):
					newVal = re.sub('\,', '', str(tCurrPrice))
					dump[mark]['fRatios']['currPrice'] = float(newVal)
				else:
					dump[mark]['fRatios']['currPrice'] = float(tCurrPrice)
			#except:
			#	dump[mark]['fRatios']['currPrice'] = 0.0
		except:
			print "Basic Ratios extraction had an issue..."
			dump[mark]['fRatios'] = None

		#Extracting Profit/Loss statements#
		dump[mark]['f-pl-data'] = {}
		try:
			try:
				dump[mark]['f-pl-data']['sales_3Y'] = data.findAll("span", {"id": "profitlossSales"})[0].get_text().split('%')[0]
			except:
				dump[mark]['f-pl-data']['sales_3Y'] = 0.0
			try:
				dump[mark]['f-pl-data']['sales_IAvg_3Y'] = data.findAll("span", {"id": "profitlossSalesAvg"})[0].get_text().split('%')[0]
			except:
				dump[mark]['f-pl-data']['sales_IAvg_3Y'] = 0.0
			try:
				dump[mark]['f-pl-data']['PAT_3Y'] = data.findAll("span", {"id": "profitlossPAT"})[0].get_text().split('%')[0]
			except:
				dump[mark]['f-pl-data']['PAT_3Y'] = 0.0
			try:
				dump[mark]['f-pl-data']['PAT_IAvg_3Y'] = data.findAll("span", {"id": "profitlossPATAvg"})[0].get_text().split('%')[0]
			except:
				dump[mark]['f-pl-data']['PAT_IAvg_3Y'] = 0.0
		except:
			print "P/L data extraction had an issue..."
			dump[mark]['f-pl-data'] = None

		#Extracting Balance Sheet summary#
		dump[mark]['f-bs-data'] = {}
		try:
			try:
				dump[mark]['f-bs-data']['total_asset_growth_3Y'] = data.findAll("span", {"id": "3yearAssetGrowthBlnsht"})[0].get_text().split('%')[0]
			except:
				dump[mark]['f-bs-data']['total_asset_growth_3Y'] = 0.0
			try:
				dump[mark]['f-bs-data']['total_liabilities_growth_3Y'] = data.findAll("span", {"id": "3yearliabilityGrowthBlnsht"})[0].get_text().split('%')[0]
			except:
				dump[mark]['f-bs-data']['total_liabilities_growth_3Y'] = 0.0
			try:
				dump[mark]['f-bs-data']['total_reserves_change_3Y'] = data.findAll("span", {"id": "3yearReservesGrowthBlnsht"})[0].get_text().split('%')[0]
			except:
				dump[mark]['f-bs-data']['total_reserves_change_3Y'] = 0.0
		except:
			print "Balance Sheet data extraction had an issue..."
			dump[mark]['f-bs-data'] = None

		#Extracting comparative Techinicals#
		dump[mark]['f-tech'] = {}
		try:
			try:
				dump[mark]['f-tech']['growth_vs_sensex_3Y'] = data.findAll("span", {"id":"SENSEX_3YEAR"})[0].get_text().split('%')[0]
			except:
				dump[mark]['f-tech']['growth_vs_sensex_3Y'] = 0.0
			try:
				dump[mark]['f-tech']['growth_vs_NIFTY_3Y'] = data.findAll("span", {"id":"NIFTY_3YEAR"})[0].get_text().split('%')[0]
			except:
				dump[mark]['f-tech']['growth_vs_NIFTY_3Y'] = 0.0
			try:
				dump[mark]['f-tech']['growth_vs_MF_3Y'] = data.findAll("span", {"id":"MF_3YEAR"})[0].get_text().split('%')[0]
			except:
				dump[mark]['f-tech']['growth_vs_MF_3Y'] = 0.0
		except:
			print "comparative technicals extraction had an issue..."
			dump[mark]['f-tech'] = None

		#Extracting flag-indicators#
		dump[mark]['fFlags'] = {}
		#TODO
		
		#Finished one iter of data extraction. i.e one company fundamentals

		wait = int(random.randint(0,7) + 3)
		sleep(wait)
		print 'Sleeping:', wait,'seconds\n'

	with open('./ifirm.list','w') as f:
		for elem in dump.keys():
			f.write(str(elem)+','+str(dump[elem]['fIDs']['BSE']+'_'+dump[elem]['fIDs']['NSE'])+'\n')
	
	return dump

def parseBhavData(bhavDataLoc):
	#Identifies consolidated Bhav report (2y) and parses company-wise data. Other functions are defined in mathutils#
	print "Extracting BHAV data"
	data = fl.readLinesAndSplit(bhavDataLoc, ',')
	TS_DATA = {}
	uniqCName = []
	for line in data:
		if str(line[1])+'_'+str(line[2]) not in uniqCName:
			uniqCName.append(str(line[1])+'_'+str(line[2]))
	for cName in uniqCName:
		TS_DATA[cName] = {'t-price': [], 't-vol': [], 't-share': []}
		for line in data:
			if line[0] != "DATE":
				if cName.split('_')[0] == line[1] or cName.split('_')[1] == line[2]:
					TS_DATA[cName]['t-price'].append((line[0], line[8]))
					TS_DATA[cName]['t-vol'].append((line[0], line[11]))
					TS_DATA[cName]['t-share'].append((line[0], line[12]))

	return TS_DATA

def appendBhavData(base, bhavDataLoc):
	#Appends new information to existing bhav-data-base#
	with open(base,'r') as f:
		ext = pickle.load(f)

	newData = fl.readLinesAndSplit(bhavDataLoc, ',')
	for line in newData:
		if str(line[1])+'_'+str(line[2]) not in uniqCName:
			uniqCName.append(str(line[1])+'_'+str(line[2]))
	for cName in uniqCName:
		if cName not in ext.keys():
			ext[cName] = {'t-price': [], 't-vol': [], 't-share': []}
		for line in data:
			if line[0] != "DATE":
				if cName.split('_')[0] == line[1] or cName.split('_')[1] == line[2]:
					ext[cName]['t-price'].append((line[0], line[8]))
					ext[cName]['t-vol'].append((line[0], line[11]))
					ext[cName]['t-share'].append((line[0], line[12]))
	return ext

if __name__=="__main__":
	script, mSource, bhavDataLoc = sys.argv
	
	with open(mSource,'r') as f:
		data_ = f.readlines()
		data = []
		for elem_ in data_:
			elem = elem_.split('\n')[0]
			data.append(elem)


	if os.path.isfile('./links.dump') == False:
		linkList = extractLinkList(data)
	else:
		with open('./links.dump','r') as f:
			linkList = pickle.load(f)
	DATA = scrapeData(linkList)

	with open('./fData.dump','w') as f:
		pickle.dump(DATA,f)

	TS_DATA = parseBhavData(bhavDataLoc)

	with open('./tData.dump','w') as f:
		pickle.dump(TS_DATA,f)
