import os
from datetime import datetime

import ctd
import numpy as np
import pandas as pd
import progressbar
from ctd import movingaverage
from netCDF4 import date2num

import ctdConfig as CTDConfig
# Local files
import okokyst_map
import okokyst_tools
from station.station_class import Station
import okokyst_station_mapping as sm
from pathlib import Path

__author__ = 'Trond Kristiansen'
__email__ = 'trond.kristiansen@niva.no'
__created__ = datetime(2017, 2, 24)
__modified__ = datetime(2021, 11, 15)
__version__ = "1.0"
__status__ = "Development"


# ---------------------------------------------------
# OKOKYST_TOOLBOX INFO:
#
# To make use of this toolbox you also need to install python-ctd package. 
# In the source code for python-ctd locate the folder ctd/read.py and replace the content with the content
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
    # if CTDConfig.debug:
    #  print("=> Opening input file: %s" % (filename))

    cast, metadata = ctd.from_saiv(filename)
    downcast, upcast = cast.split()

    if station.name in ["OKS2"] and dateObject.year == 2019:
        upcast = downcast

    if (not downcast.empty and CTDConfig.useDowncast) or (not upcast.empty and not CTDConfig.useDowncast):
        if CTDConfig.useDowncast:
            downcast_copy = downcast.copy()

            downcast_copy['dz/dtM'] = movingaverage(downcast['dz/dtM'], window_size=1)
            downcast['dz/dtM'].loc[downcast_copy['dz/dtM'] == np.nan].fillna(0)
            downcast['dz/dtM'].replace([np.inf, -np.inf], 0.5)

            downcast = downcast[downcast['dz/dtM'] >= 0.05]  # Threshold velocity.
            window = okokyst_tools.findMaximumWindow(downcast, CTDConfig.tempName)
            window = 10

            temperature = downcast[CTDConfig.tempName] \
                .remove_above_water() \
                .despike(n1=2, n2=20, block=window) \
                .interpolate(method='index', \
                             limit_direction='both',
                             limit_area='inside') \
                .smooth(window_len=2, window='hanning')
            salinity = downcast[CTDConfig.saltName] \
                .remove_above_water() \
                .despike(n1=2, n2=20, block=window) \
                .interpolate(method='index', \
                             limit_direction='both',
                             limit_area='inside') \
                .smooth(window_len=2, window='hanning')

            # Make sure that oxygen is in ml O2/L
            if 'OxMgL' in downcast.columns:
                df = downcast.astype({'OxMgL': float})
                df['OxMgL'] = df.OxMgL.values / 1.42905
                df = sm.to_rename_columns(df, 'OxMgL', 'OxMlL')
            elif 'OxMlL' in downcast.columns:
                df = downcast.astype({'OxMlL': float})
            else:
                raise Exception("Unable to find oxygen in dataformat: {}".format(downcast.columns))

            oxygen = df["OxMlL"] \
                .remove_above_water() \
                .despike(n1=2, n2=20, block=window) \
                .interpolate(method='index', \
                             limit_direction='both',
                             limit_area='inside') \
                .smooth(window_len=2, window='hanning')
            oxsat = downcast[CTDConfig.oxsatName] \
                .remove_above_water() \
                .despike(n1=2, n2=20, block=window) \
                .interpolate(method='index', \
                             limit_direction='both',
                             limit_area='inside') \
                .smooth(window_len=2, window='hanning')
            ftu = downcast[CTDConfig.ftuName] \
                .remove_above_water() \
                .despike(n1=2, n2=20, block=window) \
                .interpolate(method='index', \
                             limit_direction='both',
                             limit_area='inside') \
                .smooth(window_len=2, window='hanning')

            if CTDConfig.showStats:
                print("=> STATS FOR DOWNCAST TEMP at %s:\n %s" % (
                    station.name, downcast[[CTDConfig.tempName]].describe()))
                print("=> STATS FOR DOWNCAST SALT at %s:\n %s" % (
                    station.name, downcast[[CTDConfig.saltName]].describe()))

                if 'OxMgL' in downcast.columns:
                    print("=> STATS FOR DOWNCAST OXYGEN at %s:\n %s" % (
                        station.name, downcast[["OxMgL"]].describe()))
                else:
                    print("=> STATS FOR DOWNCAST OXYGEN at %s:\n %s" % (
                        station.name, downcast[["OxMlL"]].describe()))
                print(
                    "=> STATS FOR DOWNCAST FTU at %s:\n %s" % (station.name, downcast[[CTDConfig.ftuName]].describe()))
        else:

            upcast['dz/dtM'] = movingaverage(upcast['dz/dtM'], window_size=2)
            #    upcast['dz/dtM'] = upcast['dz/dtM'].fillna(0)
            upcast['dz/dtM'] = upcast['dz/dtM'].replace([np.inf, -np.inf], 0.5)
            upcast = upcast[upcast['dz/dtM'] >= 0.05]  # Threshold velocity.

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
        delta = 1
        if CTDConfig.survey == "Soerfjorden":
            window_len = 1
        if CTDConfig.survey in ["Sognefjorden", "Hardangerfjorden", "MON"]:
            window_len = 10

        # Smoothing and interpolation
        temperature = temperature.interpolate(method='linear')
        # temperature = temperature.smooth(window_len=window_len, window='hanning')

        oxygen = oxygen.interpolate(method='linear')
        # oxygen = oxygen.smooth(window_len=window_len, window='hanning')

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

        if station.name not in ['SJON1', 'SJON2']:
            ftu = ftu.bindata(delta=delta, method='interpolate')

        df = pd.DataFrame(index=salinity.index, columns=["Depth", "Temperature", "Salinity", "Oxygen", "Oxsat", "FTU"])
        # df = df.fillna(0)
        # df = df.reset_index(drop=True)

        # oxsat = oxsat.reset_index(drop=True)
        df["Depth"] = salinity.index
        df["Temperature"] = temperature
        df["Salinity"] = salinity
        df["Oxygen"] = oxygen
        df["Oxsat"] = oxsat
        if station.name not in ['SJON1', 'SJON2']:
            df["FTU"] = ftu

        # Add data to station object for later
        station.addData(salinity, temperature, oxygen, oxsat, ftu, salinity.index,
                        date2num(dateObject, CTDConfig.refdate, calendar="standard"))
        return df


# Add data from Aquamonitor (netcdf) files to be able to plot longer time series.
def addHistoricalData(station, CTDConfig, work_dir):
    if station.name in ['VT69']:
        ds = xr.open_dataset('/Users/trondkr/Dropbox/NIVA/OKOKYST/Historical_oekokyst_data/VT69_2013_2016.nc')
    elif station.name in ['VT70']:
        ds = xr.open_dataset('/Users/trondkr/Dropbox/NIVA/OKOKYST/Historical_oekokyst_data/VT70_2013_2016.nc')
    else:
        raise Exception("Should not call addHistoricalData unless station is VT69 or VT70 due to available timeseries")

    df = ds.to_dataframe().groupby(['time', 'depth']).mean()
    first = True

    for date_depth_index, row in df.iterrows():

        if first:
            old_date = date_depth_index[0]
            temperature = []
            depth = []
            salinity = []
            oxsat = []
            oxygen = []
            ftu = []

            first = False

        if old_date == date_depth_index[0]:
            temperature.append(row['temp'])
            salinity.append(row['salt'])
            oxsat.append(row['O2sat'])
            oxygen.append(row['O2vol'])
            depth.append(float(date_depth_index[1]))
            ftu.append(row['O2vol'] * np.nan)
        else:
            print("Storing data for time {}".format(date_depth_index[0]))
            depth = pd.Series(depth)
            temperature = pd.Series(temperature, index=depth)
            salinity = pd.Series(salinity, index=depth)
            oxygen = pd.Series(oxygen, index=depth)
            oxsat = pd.Series(oxsat, index=depth)
            ftu = pd.Series(ftu, index=depth)

            df_new = pd.DataFrame(columns=["Depth", "Temperature", "Salinity", "Oxygen", "Oxsat", "FTU"])

            df_new.set_index('Depth', inplace=True, drop=False)

            df_new["Depth"] = depth
            df_new["Temperature"] = temperature
            df_new["Salinity"] = salinity
            df_new["Oxygen"] = oxygen
            df_new["Oxsat"] = oxsat

            # Add data to station object for later
            station.addData(salinity, temperature, oxygen, oxsat, ftu, salinity.index,
                            date2num(date_depth_index[0], CTDConfig.refdate, calendar="standard"))

            temperature = []
            depth = []
            salinity = []
            oxsat = []
            oxygen = []
            ftu = []

            old_date = date_depth_index[0]
            temperature.append(row['temp'])
            salinity.append(row['temp'])
            oxsat.append(row['O2sat'])
            oxygen.append(row['O2vol'])
            depth.append(float(date_depth_index[1]))
            ftu.append(row['O2vol'] * np.nan)


def createContours(stationsList, CTDConfig):
    for station in stationsList:
        station.createTimeSection(CTDConfig)
        station.createContourPlots(CTDConfig)


def createHistoricalTimeseries(stationsList, CTDConfig):
    for station in stationsList:
        if station.name in ["VT69", "VT70"]:
            station.createTimeSection(CTDConfig)
            station.createHistoricalTimeseries(CTDConfig)


def createTimeseries(stationsList, CTDConfig):
    for station in stationsList:
        station.createTimeSection(CTDConfig)
        station.createTimeseriesPlot(CTDConfig)


ctd_config = {
    'MON': {
        'useDowncast': False},
    "Hardangerfjorden": {
        'useDowncast': True},
    "Sognefjorden": {
        'useDowncast': True},
    "Soerfjorden": {
        'useDowncast': True},
    "RMS": {
        'useDowncast': True},
    "Aqua_kompetanse": {
        'useDowncast': True}
}


def main(surveys, months, CTDConfig):
    for survey in surveys:

        if survey in ["Aqua_kompetanse", "RMS"]:
            domain = "Norskehavet_Sor"
        elif survey in ["Hardangerfjorden", "Sognefjorden"]:
            domain = "Nordsjoen_Nord"
        elif survey in ["Soerfjorden"]:
            domain = "Soerfjorden"

        # Root folder on One Drive for Økokyst data
        CTDConfig.work_dir = r"/Users/trondkr/OneDrive - NIVA/Okokyst_CTD/{}/".format(domain)

        # All folders containing station files (e.g. VT8.txt) needs to contain this prefix
        prefix = " CTD data"
        if survey in ["Soerfjorden"]:
            prefix = "-CTD-data"

        CTDConfig.survey = survey
        CTDConfig.useDowncast = ctd_config[survey]['useDowncast']

        stationsList = []
        stationNamesList = []

        if CTDConfig.survey == "MON":
            basepath = "/Users/trondkr/Dropbox/MON-data/CONVERTED/"
            subStations = ['NORD1', 'NORD2', 'TYS1', 'TYS2', 'SAG1', 'SAG2',
                           'OFOT1', 'OFOT2', 'OKS1', 'OKS2', 'SJON1', 'SJON2']

            stationid = ["62215", "62216", "62217", "62218", "62219", "62220",
                         "62221", "62222", "62223", "62224", "68577", "68578"]

            projectid = '5482'
            method = 'AkvaplanNIVA'
            projectname = 'Marin overvåking Nordland'

        if CTDConfig.survey == "Soerfjorden":
            basepath = "/Users/trondkr/OneDrive - NIVA/Okokyst_CTD/{}/".format(domain)
            subStations = ["SOE72", "Lind1", "S22", "S16", "SOE10"]
            subStations = ["SOE72", "Lind1", "S22"]
            stationid = ["SOE72", "Lind1", "S22", "S16", "SOE10"]
            projectid = 'Soerfjorden'
            method = 'NIVA'
            projectname = 'Soerfjorden'

        if CTDConfig.survey == "Hardangerfjorden":
            basepath = os.path.join(CTDConfig.work_dir, 'Hardangerfjorden/')

            projectid = '10526'
            method = 'Saiv CTD s/n 1270'
            projectname = 'OKOKYST Nordsjoen Nord'
            subStations_before_2020 = ["VT70", "VT69", "VT74", "VT53", "VT52", "VT75"]
            subStations = ["VT70", "VT74", "VT53", "VT8", "VR48", "VR49"]
            stationid = ["68910", "68913", "68911", "missing_add_me", "missing_add_me", "missing_add_me"]

          #  subStations = ["VR48"]
          #  stationid = ["missing_add_me"]

        #  subStations = ["VR48"]
        #  stationid = ["missing_add_me"]

        if CTDConfig.survey == "Sognefjorden":
            basepath = os.path.join(CTDConfig.work_dir, 'Sognefjorden')

            projectid = '10526'
            method = 'Saiv CTD s/n 1330'
            projectname = 'OKOKYST Nordsjoen Nord'
            subStations = ["VT16", "VT79"]
            stationid = ["68915", "68914"]

        if CTDConfig.survey == "RMS":
            basepath = os.path.join(CTDConfig.work_dir, 'RMS')

            projectid = 'missing_project_id_add_me'
            method = 'Saiv CTD s/n 1330'
            projectname = 'OKOKYST Norskehavet Soer'
            subStations = ["VT71", "VR51"]
            stationid = ["missing_add_me", "missing_add_me"]

        if CTDConfig.survey == "Aqua_kompetanse":
            basepath = os.path.join(CTDConfig.work_dir, 'Aqua_kompetanse')

            projectid = 'missing_project_id_add_me'
            method = 'Saiv CTD s/n 1330'
            projectname = 'OKOKYST Norskehavet Soer'
            subStations = ["VR52", "VR61", "VR31"]
            stationid = ["missing_add_me", "missing_add_me",  "missing_add_me"]

        path, dirs, files = next(os.walk(basepath))
        pbar = progressbar.ProgressBar(maxval=len(files)).start()

        for sub_index, subStation in enumerate(subStations):
            station = Station(subStation, CTDConfig.survey, CTDConfig.survey)
            stationsList.append(station)
            station.stationid = stationid[sub_index]
            counter = 0
            if CTDConfig.createHistoricalTimeseries:
                if station.name in ["VT69", "VT70"]:
                    addHistoricalData(station, CTDConfig, CTDConfig.work_dir)

            print("\nSurvey: {} => Adding station {}".format(survey, subStation))
            for folder, subdirs, files in os.walk(basepath):
                subdirs.sort()
                pbar.update(counter + 1)
                if okokyst_tools.locateDir(folder):

                    # Check if the folder contains station data based on prefix
                    if prefix in folder:
                        # Get the date from the folder name
                        date_formats = ['%Y/%m/%d', '%Y-%m-%d', '%Y%m%d','%d.%m.%Y', '%m/%d/%Y', '%m-%d-%Y']
                        for date_format in date_formats:
                            try:
                                dateObject = datetime.strptime(Path(folder).stem.replace(prefix, ""), date_format)
                                break
                            except ValueError as e:
                                pass

                        strmonth = str(dateObject.strftime("%b"))

                        if strmonth in months:
                            filename = okokyst_tools.locateFile(folder, subStation)

                            if filename is not None:
                                if CTDConfig.debug:
                                    print("=> Identified correct file: {} for month {}".format(filename, strmonth))

                                bb = os.path.basename(filename)
                                filestation = os.path.splitext(bb)

                                st = filestation[0].replace("_edited", "")

                                if st in subStations:
                                    # newfilename = okokyst_tools.createNewFile(filename, station, CTDConfig)
                                    qualityCheckStation(filename, dateObject, station, CTDConfig)

        pbar.finish()
        if CTDConfig.createHistoricalTimeseries:
            createHistoricalTimeseries(stationsList, CTDConfig)

        for st in stationsList:
            if CTDConfig.describeStation:
                st.describeStation(CTDConfig)

            if CTDConfig.createTSPlot:
                st.plotStationTS(survey)

            if CTDConfig.binDataWriteToNetCDF:
                st.binDataWriteToNetCDF(CTDConfig, basepath + "to_netCDF")

            if CTDConfig.write_to_excel:
                st.projectname = projectname
                st.method = method
                st.projectid = projectid
                st.write_station_to_excel(CTDConfig)

        if CTDConfig.createContourPlot:
            print("Create contours")
            createContours(stationsList, CTDConfig)

        if CTDConfig.createTimeseriesPlot:
            createTimeseries(stationsList, CTDConfig)

        if CTDConfig.plotStationMap:
            okokyst_map.createMap(stationsList)


if __name__ == "__main__":
    # EDIT

    # surveys = ["Sognefjorden"]
    # "Hardangerfjorden","MON"
    surveys = ["Hardangerfjorden", "Sognefjorden", "Aqua_kompetanse", "RMS"]
  #  surveys = ["Sognefjorden"]
   # surveys=["RMS"]

    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    # Define the depth levels (meters) you want to create plots showing the annual differences
    # Only used when createTimeseriesPlot=True
    selected_depths = [5, 100, 200]

    # NOTE: make sure the function "addStationMeadata" is up to date with info
    # MON survey needs to use upcast
    # ØKOKYST should use downcast

    CTDConfig = CTDConfig.CTDConfig(createStationPlot=False,
                                    createTSPlot=False,
                                    createContourPlot=True,
                                    createTimeseriesPlot=False,
                                    binDataWriteToNetCDF=False,
                                    describeStation=False,
                                    createHistoricalTimeseries=False,
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
                                    debug=True)

    kw = dict(compression=None)
    kw.update(below_water=True)

    main(surveys, months, CTDConfig)
