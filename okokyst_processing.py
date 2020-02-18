import matplotlib
from pathlib import Path
import ctd
from ctd import movingaverage, lp_filter
from pathlib import Path

#matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
import numpy as np
import string
import matplotlib.pyplot as plt
import gsw

from netCDF4 import date2num, num2date
import pandas as pd
from datetime import datetime
import glob
import progressbar

# Local files
import okokyst_map
import okokyst_tools
from station.station_class import Station
import ctdConfig as CTDConfig

__author__ = 'Trond Kristiansen'
__email__ = 'trond.kristiansen@niva.no'
__created__ = datetime(2017, 2, 24)
__modified__ = datetime(2019, 1, 8)
__version__ = "1.0"
__status__ = "Development"
    
# ---------------------------------------------------
# OKOKYST_TOOLBOX INFO:
#
# To make use of this toolbox you also need to install python-ctd package. 
# In the source code for python-ctd localte the folder ctd/read.py and replace the content with the content 
# of file functionSAIV.py. Then recompile and install the python-ctd module using:
# cd python-ctd
# python setup.py develop
#
# This adds the possibility to read SAIV files
# to the toolbox. The python-ctd toolbox is found here:
# https://github.com/pyoceans/python-ctd

#
# Run this using : python okokyst_processing.py
# Requires:
# Data to be located in folders with specific structure:

#  =>/Users/trondkr/Dropbox/Sorfjorden_2017_2019/
#  ==> 2018-09-07/
#  ===> 2018-09-07 CTD data/
#  ====> SOE10.txt
# ---------------------------------------------------

# Main function that calls ctd module and reads the individual SAIV data and stores each cast
# as one station cast object in an array of stations.
def qualityCheckStation(filename, dateObject, station, CTDConfig):
    if CTDConfig.debug:
        print("=> Opening input file: %s" % (filename))

    cast, metadata = ctd.from_saiv(filename)
    downcast, upcast = cast.split()
    if (not downcast.empty and CTDConfig.useDowncast) or (not upcast.empty and not CTDConfig.useDowncast):
      
        if CTDConfig.useDowncast:
       
            downcast['dz/dtM'] = movingaverage(downcast['dz/dtM'], window_size=2)
            downcast['dz/dtM'] = downcast['dz/dtM'].fillna(0)
            downcast['dz/dtM'].replace([np.inf, -np.inf], 0.5)
          
            downcast = downcast[downcast['dz/dtM'] >= 0.1]  # Threshold velocity.
            window = okokyst_tools.findMaximumWindow(downcast, CTDConfig.tempName)
            window=10
            
            temperature = downcast[CTDConfig.tempName]\
                        .remove_above_water()\
                        .despike(n1=2, n2=20, block=window)\
                        .interpolate(method='index',\
                        limit_direction='both',
                        limit_area='inside')\
                        .smooth(window_len=2, window='hanning')
            salinity = downcast[CTDConfig.saltName]\
                        .remove_above_water()\
                        .despike(n1=2, n2=20, block=window)\
                        .interpolate(method='index',\
                        limit_direction='both',
                        limit_area='inside')\
                        .smooth(window_len=2, window='hanning')
            oxygen = downcast[CTDConfig.oxName]\
                        .remove_above_water()\
                        .despike(n1=2, n2=20, block=window)\
                        .interpolate(method='index',\
                        limit_direction='both',
                        limit_area='inside')\
                        .smooth(window_len=2, window='hanning')
            oxsat = downcast[CTDConfig.oxsatName]\
                        .remove_above_water()\
                        .despike(n1=2, n2=20, block=window)\
                        .interpolate(method='index',\
                        limit_direction='both',
                        limit_area='inside')\
                        .smooth(window_len=2, window='hanning')
            ftu = downcast[CTDConfig.ftuName]\
                        .remove_above_water()\
                        .despike(n1=2, n2=20, block=window)\
                        .interpolate(method='index',\
                        limit_direction='both',
                        limit_area='inside')\
                        .smooth(window_len=2, window='hanning')
    
            if CTDConfig.showStats:
                print("=> STATS FOR DOWNCAST TEMP at %s:\n %s" % (station.name, downcast[[CTDConfig.tempName]].describe()))
                print("=> STATS FOR DOWNCAST SALT at %s:\n %s" % (station.name, downcast[[CTDConfig.saltName]].describe()))
                print("=> STATS FOR DOWNCAST OXYGEN at %s:\n %s" % (station.name, downcast[[CTDConfig.oxName]].describe()))
                print("=> STATS FOR DOWNCAST FTU at %s:\n %s" % (station.name, downcast[[CTDConfig.ftuName]].describe()))
        else:
           
            upcast['dz/dtM'] = movingaverage(upcast['dz/dtM'], window_size=2)
        #    upcast['dz/dtM'] = upcast['dz/dtM'].fillna(0)
            upcast['dz/dtM'] = upcast['dz/dtM'].replace([np.inf, -np.inf], 0.5)
            upcast = upcast[upcast['dz/dtM'] >= 0.1]  # Threshold velocity.

            window = okokyst_tools.findMaximumWindow(upcast, CTDConfig.tempName)
          
            temperature = upcast[CTDConfig.tempName].despike(n1=1, n2=20, block=window)
            salinity = upcast[CTDConfig.saltName].despike(n1=1, n2=20, block=window)
            oxygen = upcast[CTDConfig.oxName].despike(n1=1, n2=20, block=window)
            oxsat = upcast[CTDConfig.oxsatName].despike(n1=1, n2=20, block=window)
            ftu = upcast[CTDConfig.ftuName].despike(n1=2, n2=10, block=window)
    
            if CTDConfig.showStats:
                print("=> STATS FOR UPCAST TEMP at %s:\n %s" % (station.name, upcast[[CTDConfig.tempName]].describe()))
                print("=> STATS FOR UPCAST SALT at %s:\n %s" % (station.name, upcast[[CTDConfig.saltName]].describe()))
                print("=> STATS FOR UPCAST OXYGEN at %s:\n %s" % (station.name, upcast[[CTDConfig.oxName]].describe()))
                print("=> STATS FOR UPCAST FTU at %s:\n %s" % (station.name, upcast[[CTDConfig.ftuName]].describe()))

        # Binning
       
        delta=1
        if CTDConfig.survey == "Soerfjorden":
            window_len=1
        if CTDConfig.survey in ["Sognefjorden","Hardangerfjorden", "MON"]:
            window_len=10
            
        # Smoothing and interpolation
        temperature = temperature.interpolate(method='linear')
       # temperature = temperature.smooth(window_len=window_len, window='hanning')

        oxygen = oxygen.interpolate(method='linear')
        #oxygen = oxygen.smooth(window_len=window_len, window='hanning')

        oxsat = oxsat.interpolate(method='linear')
       # oxsat = oxsat.smooth(window_len=window_len, window='hanning')
        
        ftu = ftu.interpolate(method='linear')
       # ftu = ftu.smooth(window_len=1, window='hanning')

        salinity = salinity.interpolate(method='linear')
      #  salinity = salinity.smooth(window_len=window_len, window='hanning')
        
        # Bin the data to delta intervals   
        temperature = temperature.bindata(delta=delta, method='interpolate')
        salinity = salinity.bindata(delta=delta, method='interpolate')
        oxygen = oxygen.bindata(delta=delta, method='interpolate')
        oxsat = oxsat.bindata(delta=delta, method='interpolate')
        
        if station.name not in ['SJON1','SJON2']:
            ftu = ftu.bindata(delta=delta, method='interpolate')
       
        df = pd.DataFrame(index=salinity.index, columns=["Depth", "Temperature", "Salinity", "Oxygen", "Oxsat", "FTU"])
       # df = df.fillna(0)
       # df = df.reset_index(drop=True)
        
       # oxsat = oxsat.reset_index(drop=True)
        df["Depth"]= salinity.index
        df["Temperature"] = temperature
        df["Salinity"] = salinity
        df["Oxygen"] = oxygen
        df["Oxsat"] = oxsat
        if station.name not in ['SJON1','SJON2']:
            df["FTU"] = ftu
       
        # Add data to station object for later
        station.addData(salinity, temperature, oxygen, oxsat, ftu, salinity.index,
                        date2num(dateObject, CTDConfig.refdate, calendar="standard"))
        return df

def createContours(stationsList, CTDConfig):
    for station in stationsList:
        station.createTimeSection(CTDConfig)
        station.createContourPlots(CTDConfig)

def createTimeseries(stationsList, CTDConfig):
    for station in stationsList:
        station.createTimeSection(CTDConfig)
        station.createTimeseriesPlot(CTDConfig)
        
def main(surveys, months, CTDConfig):
    
    for survey in surveys:
        CTDConfig.survey=survey
        if CTDConfig.survey in ["Hardangerfjorden","Sognefjorden","Soerfjorden"]:
            CTDConfig.useDowncast=True
        if CTDConfig.survey in ["MON"]:
            CTDConfig.useDowncast=False
        
        stationsList = []
        stationNamesList = []
            
        if CTDConfig.survey == "MON":
            basepath = "/Users/trondkr/Dropbox/MON-data/CONVERTED/"
            subStations = ['NORD1','NORD2','TYS1','TYS2','SAG1','SAG2',
                           'OFOT1','OFOT2','OKS1','OKS2','SJON1','SJON2']

            stationid = ["62215","62216","62217","62218","62219","62220",
                         "62221","62222","62223","62224","68577","68578"]

            subStations = ['OKS2']
            stationid=["62224"]

            projectid = '5482'
            method = 'AkvaplanNIVA'
            projectname = 'Marin overvåking Nordland'
                         
        if CTDConfig.survey == "Soerfjorden":
            basepath = "/Users/trondkr/Dropbox/Sorfjorden_2017_2019/"
            subStations = ["SOE72", "Lind1", "S22","S16","SOE10"]
            subStations = ["SOE72", "Lind1", "S22"]
            stationid = ["SOE72", "Lind1", "S22","S16","SOE10"]
            projectid = 'Soerfjorden'
            method = 'NIVA'
            projectname = 'Soerfjorden'
            
        if CTDConfig.survey == "Hardangerfjorden":
            basepath = "/Users/trondkr/Dropbox/ØKOKYST_NORDSJØENNORD_CTD/Hardangerfjorden/"
            projectid = '10526'
            method = 'Saiv CTD s/n 1270'
            projectname = 'OKOKYST Nordsjoen Nord'
            subStations = ["VT70", "VT69", "VT74", "VT53", "VT52", "VT75"]
            stationid = ["68910", "68908", "68913", "68911", "69164", "69165"]
          #  subStations = ["VT69"]
        if CTDConfig.survey == "Sognefjorden":
            basepath = "/Users/trondkr/Dropbox/ØKOKYST_NORDSJØENNORD_CTD/Sognefjorden/"
            projectid = '10526'
            method = 'Saiv CTD s/n 1330'
            projectname = 'OKOKYST Nordsjoen Nord'
            subStations = ["VT16", "VT79"]
            stationid = ["68915", "68914"]
        
        subdirectories = sorted(os.listdir(basepath))

       # pbar = progressbar.ProgressBar(widgets=[progressbar.Percentage(), progressbar.Bar()], maxval=len(subdirectories)).start()
        pbar = progressbar.ProgressBar(max_value=len(subdirectories), redirect_stdout=True).start()
        
        for sub_index,subStation in enumerate(subStations):
            station = Station(subStation, CTDConfig.survey, CTDConfig.survey)
            stationsList.append(station)
            station.stationid=stationid[sub_index]
            
            print("\nSurvey: {} => Adding station {}".format(survey, subStation))
            for i, folder in enumerate(subdirectories):
                pbar.update(i+1)
                if okokyst_tools.locateDir(basepath + folder):
                    dirLevel2 = basepath + folder + "/" + folder + " CTD data"
                    if okokyst_tools.locateDir(dirLevel2):
                        dateObject = datetime(int(folder[0:4]), int(folder[5:7]), int(folder[8:10]))
                        strmonth = str(dateObject.strftime("%b"))
                       
                        if strmonth in months:
                            filename = okokyst_tools.locateFile(dirLevel2, subStation)
                            if CTDConfig.debug:
                                print("=> Identified correct file: {} for month {}".format(filename, strmonth))

                            if filename != None:    
                                bb = os.path.basename(filename)
                                filestation = os.path.splitext(bb)

                                if filestation[0] in subStations:
                                    newfilename = okokyst_tools.createNewFile(filename, station, CTDConfig)
                                    qualityCheckStation(newfilename, dateObject, station, CTDConfig)
        pbar.finish()
        for st in stationsList:
            if CTDConfig.describeStation:
                st.describeStation(CTDConfig)
            if CTDConfig.createTSPlot:
                st.plotStationTS(survey)

            if CTDConfig.binDataWriteToNetCDF:
                st.binDataWriteToNetCDF(CTDConfig, basepath+"to_netCDF")

            if CTDConfig.write_to_excel:
                st.projectname=projectname
                st.method=method
                st.projectid=projectid
                st.write_station_to_excel(CTDConfig)
                
        if CTDConfig.createContourPlot:
            createContours(stationsList, CTDConfig)

        if CTDConfig.createTimeseriesPlot:
            createTimeseries(stationsList, CTDConfig)
            
        if CTDConfig.plotStationMap:
            okokyst_map.createMap(stationsList)

if __name__ == "__main__":
    
    # EDIT
    surveys = ["Hardangerfjorden", "Sognefjorden"]
    surveys = ["Soerfjorden","MON"]
    surveys = ["MON"]
 
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov","Dec"]
    
    # Define the depth levels (meters) you want to create plots showing the annual differences
    # Onoy used when createTimeseriesPlot=True
    selected_depths=[3,100,200]
    
    # NOTE: make sure the function "addStationMeadata" is up to date with info
    # MON survey needs to use upcast
    # ØKOKYST should use downcast
        
    CTDConfig = CTDConfig.CTDConfig(createStationPlot=False,
                                    createTSPlot=False,
                                    createContourPlot=True,
                                    createTimeseriesPlot=False,
                                    binDataWriteToNetCDF=False,
                                    describeStation=False,
                                    showStats=False,
                                    plotStationMap=False,
                                    tempName='Temp',
                                    saltName='Salinity',
                                    oxName='OxMgL',
                                    ftuName='FTU',
                                    oxsatName='OptOx',
                                    refdate="seconds since 1970-01-01:00:00:00",
                                    selected_depths=selected_depths,
                                    write_to_excel=True,
                                    conductivity_to_salinity=False,
                                    debug=False)

    kw = dict(compression=None)
    kw.update(below_water=True)

    main(surveys, months, CTDConfig)
