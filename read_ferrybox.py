#flu
#flu bcor final
#flu fcal corrected
import matplotlib
from pathlib import Path

#matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
import numpy as np
import string

from netCDF4 import date2num, num2date
import pandas as pd
from datetime import datetime
import glob
import progressbar
import ferryBoxStationClass

from datetime import datetime, timedelta
from pyniva import Vessel, TimeSeries, token2header
from pyniva import PUB_META, PUB_TSB # Meta data and time-series data endpoints
from pyniva import META_HOST, TSB_HOST
    
#import tables

__author__ = 'Trond Kristiansen'
__email__ = 'trond.kristiansen@niva.no'
__created__ = datetime(2019, 1, 22)
__modified__ = datetime(2019, 1, 22)
__version__ = "1.0"
__status__ = "Development"
 
   
    
def setup_connection_to_nivadb():
    token='../FBdata/NIVA_TOKEN/nivatestdev-7dee310e019d.json'
    return token2header(token)
    
def get_list_of_available_timeseries_for_vessel(vessel_name,vessel_abbreviation):

    header = setup_connection_to_nivadb()
    meta_host = "https://api-test.niva.no/v1/metaflow/"
    tsb_host = "https://api-test.niva.no/v1/tsb/"

    vessel_list = [v for v in Vessel.list(meta_host, header=header) if hasattr(v, "imo")]
    for v in vessel_list:
        if v.name==vessel_name:
            print("Fetching data for vessel {} ({})".format(v.name,vessel_abbreviation))
        
            # Get signals the vessel
            signals = v.get_all_tseries(meta_host, header=header)
           # for s in signals:
           #     print(s.path)
            vessel_abbreviation='TF'
            interesting_signals =["{}/ferrybox/CHLA_FLUORESCENCE/BIOF_CORR".format(vessel_abbreviation),
                         #   "{}/ferrybox/CHLA_FLUORESCENCE/RAW".format(vessel_abbreviation),
                         #   "{}/ferrybox/CHLA_FLUORESCENCE".format(vessel_abbreviation),
                            "{}/gpstrack".format(vessel_abbreviation)]
            int_ts = [ts for sn in interesting_signals 
                        for ts in signals if sn in ts.path]
            for ts in int_ts:
                print(" Paths found => ", ts.path)

            if len(int_ts) > 0:
                data = TimeSeries.get_timeseries_list(tsb_host, int_ts,
                                                    start_time=datetime.utcnow() - timedelta(380),
                                                    end_time=datetime.utcnow(),
                                                    name_headers=True,
                                                    header=header,
                                                    noffill=True,dt=0)
                print(data, "\n")

def get_data_around_station(df,st_lon,st_lat,dist):
    # Filter out the longitude and latitudes surrounding the station lat/lon
    return df.sel((st_lat-dist < df.lat < st_lat+dist) and (st_lon-dist < df.lon < st_lon+dist))
     
def create_stations(df):
    
    station_lons=[12.3]
    station_lats=[67.6]
    station_names=['test']
    dist=0.1
    
    for st_lon,st_lat,st_name in enumerate(station_lons,station_lats,station_names):
        # Get the data for the station
        df_st=get_data_around_station(df,st_lon,st_lat,dist)
        # Create the station 
        station=FerryBoxStation(st_name,st_lon,st_lat,df_st)
         

def create_contour_station(station):
    xticklabels = []
    yticklabels = []
    refdate="seconds since 1970-01-01:00:00:00"
    
    dateObject = num2date(station.julianDay[d], units=refdate, calendar="standard")
    self.X[d] = self.julianDay[d]
    xticklabels.append(str(dateObject.year) + "-" + str(dateObject.month))
    for yy in self.Y: yticklabels.append(str(-(np.max(Y) - yy)))
    plt.set_cmap('RdYlBu_r')
            
    varNames = ["temp","salt","ox","ftu","oxsat"]
    if self.name in ['SJON1','SJON2']:
        varNames = ["temp","salt","ox", "oxsat"]
    for i in range(len(varNames)):
        plt.clf()
        fig, ax = plt.subplots()
        
        # Get data and settings for station
        specs = self.define_variable_specifics(varNames[i])
        Z = self.define_array_for_variable(varNames[i])
        Z=np.ma.masked_where(Z<0,Z)
        if varNames[i]=="ftu":
            Z=np.ma.masked_where(Z>20,Z)
        delta = (specs["vmax"] - specs["vmin"]) / 15
        levels = np.arange(specs["vmin"], specs["vmax"], delta)
        XX, YY = np.meshgrid(self.X,self.Y)
        
        CS = ax.contourf(XX,-YY,np.fliplr(np.rot90(Z, 3)), levels, vmin=specs["vmin"], vmax=specs["vmax"], extend="both")
        #  CS2 = ax.contour(XX,-YY,np.fliplr(np.rot90(Z, 3)), levels, linewidths=0.05, colors='w')
        
        depthindex=self.get_depthindex(self.Y,max_depth,ax,varNames[i])
            
        plt.colorbar(CS)
        xsteps=5
        if len(xticklabels)<10:
            xsteps=1
        if len(xticklabels)<20:
            xsteps=2
        
        ax.set_xlim(np.min(self.X),np.max(self.X))
        ax.set_xticks(self.X[::xsteps])
        ax.set_xticklabels(xticklabels[::xsteps], rotation="vertical")

        # Plot the position of the CTD stations at the deepest depths + 10 m
        new_y=np.zeros(np.shape(X))-self.Y[depthindex]+5
        ax.scatter(self.X, new_y, s=6, facecolors='none', edgecolors='k', marker='o')
        ax.set_ylabel("Dyp (m)")
        ax.set_xlabel("Dato")
        ax.set_title(specs["title"])

        dateObjectStart, dateObjectEnd = self.getTimeRangeForStation(CTDConfig)
        self.save_to_file(CTDConfig,
                            varNames[i],
                            'timeseries',
                            selected_depth='alldepths',
                            dateObjectStart=dateObjectStart,
                            dateObjectEnd=dateObjectEnd)
    
def open_mat_file(filename):

    from scipy.io import loadmat
    x = loadmat(filename)
    print(x)
    lon = x['lon']
    lat = x['lat']
   

filename='../FBdata/TF2018.mat'
#open_mat_file(filename)

get_list_of_available_timeseries_for_vessel('MS Trollfjord','TF')