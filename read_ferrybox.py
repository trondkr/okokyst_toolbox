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
import ferryBoxStationClass as fb

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
                                                    start_time=datetime.utcnow() - timedelta(120),
                                                    end_time=datetime.utcnow(),
                                                    name_headers=True,
                                                    header=header,
                                                    noffill=True,dt=0)
  
    return data

def get_data_around_station(df,st_lon,st_lat,dist):
    # https://stackoverflow.com/questions/21415661/logical-operators-for-boolean-indexing-in-pandas
    # Filter out the longitude and latitudes surrounding the station lat/lon
    return df[(st_lat-dist < df['latitude']) & (df['latitude']< st_lat+dist) & (st_lon-dist < df['longitude']) & (df['longitude']< st_lon+dist)]
     
def create_station(stationid,df):

    metadata=ferrybox_metadata(stationid)
    dist=0.1
    
    # Get the data for the station
    df_st=get_data_around_station(df,metadata['longitude'],metadata['latitude'],dist)
    
    # Create the station 
    station=fb.FerryBoxStation(metadata,df_st)
         
def ferrybox_metadata(staionid):
    return {'VT4':{'name':'Hurum', 'latitude':59.59,'longitude':10.64,'vessel':'FA'},
            'VT12':{'name':'Sognesjøen', 'latitude':60.9804,'longitude':4.7568,'vessel':'TF'},
            'VT72':{'name':'Herøyfjorden/Røyrasundet', 'latitude':62.3066,'longitude':5.5877,'vessel':'TF'},
            'VT80':{'name':'Frohavet', 'latitude':63.76542,'longitude':9.52296,'vessel':'TF'},
            'VT45':{'name':'Trondheimsfjorden - Agdenes', 'latitude':63.65006,'longitude':9.77012,'vessel':'TF'},
            'VT22':{'name':'Trondheimsfjorden', 'latitude':63.46,'longitude':10.3,'vessel':'TF'},
            'VT23':{'name':'Trondheimsleia - Hemneskjela', 'latitude':63.45737,'longitude':8.85324,'vessel':'TF'},
            'VT76':{'name':'Bøkfjorden-ytre', 'latitude':69.82562,'longitude':30.11961,'vessel':'TF'},
            'VR23':{'name':'Blodskytodden - Vardø fyr', 'latitude':70.4503,'longitude':31.0031,'vessel':'TF'},
            'VR25':{'name':'Vardnesodden - Kjølnes', 'latitude':70.98425,'longitude':28.78323,'vessel':'TF'}}[stationid]   
                 
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
    

substations=['VT12','VT72','VT80','VT45','VT22','VT23','VT76','VR23','VR25']
tsbdata = get_list_of_available_timeseries_for_vessel('MS Trollfjord','TF')

for stationid in substations:
    print('Creating station for {}'.format(stationid))
    create_station(stationid,tsbdata)
