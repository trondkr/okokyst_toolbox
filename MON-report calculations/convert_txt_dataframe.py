import os, sys, datetime, string
import numpy as np
import pandas as pd
import csv
import glob
from pathlib import Path
import string
from ttictoc import TicToc
import pandas as pd
import seaborn as sns
from pylab import *
import matplotlib.ticker as ticker
import cmocean
from scipy.interpolate import griddata
from matplotlib.tri import Triangulation, TriAnalyzer, UniformTriRefiner

__author__   = 'Trond Kristiansen'
__email__    = 'trond.kristiansen@niva.no'
__created__  = datetime.datetime(2019, 11, 22)
__modified__ = datetime.datetime(2019, 11, 22)
__version__  = "1.1"
__status__   = "Development, 22.11.2019"

station_names=['NORD1',
               'NORD2',
               'OFOT1',
               'OFOT2',
               'OKS1',
            #   'OKS2',
               'SAG1',
               'SAG2',
               'SJON1',
               'SJON2',
               'TYS1',
               'TYS2']

station_names=['SJON1']

path='/Users/trondkr/Dropbox/MON-data/CONVERTED/'
t = TicToc()
t.tic();
    
maxdepths=-9
# Loop over stations to concatenate the data as dataframe
for station in station_names:
    pattern="{}*txt".format(station)
    files = [f for f in glob.glob(path + pattern, recursive=False)]
    files=sorted(files,reverse=False)
    totalfiles=len(files)
    currentfile=0

    dataframes=[]
    for f in files:
        print("=> Working on file {}".format(f))
        df=pd.read_csv(f,delim_whitespace=True)
        
        if (maxdepths < len(df.Depth)):
            maxdepths=len(df.Depth)
      
        if (df.index[0] > df.index[-1]):
            df=df[::-1]
        df=df.dropna()

        df['Date'] = pd.to_datetime(df.Date)
        df.set_index('Date',inplace=True)
        dataframes.append(df)
        print(df)
    # Concatenate the dataframes into one big dataframe
    dfnew=pd.concat(dataframes, axis=0)
    dfnew= dfnew.loc['2013-1-1 01:00:00':'2020-8-1 04:00:00']
    dfnew = dfnew.sort_values(by=['Date', 'Depth'])
    
    dateindex=0; depthindex=0; current_depth=-9; 
    current_variable="Salinity"
    first=True
    dates=[]
    print(dfnew.info())
    
    all_variables=["Temp","Salinity","Density"]
    #4all_variables=["Opt"]
    minimum_depth_levels=[-100,None]
    
    for current_var in all_variables:
        if current_var=="Temp":
            vmin=0; vmax=18
            cmap="RdBu_r"
        if current_var=="Salinity":
            vmin=28; vmax=35
            cmap=cmocean.cm.haline
        if current_var=="Opt":
            vmin=50; vmax=100
            cmap=cmocean.cm.oxy
        if current_var=="Density":
            vmin=25; vmax=29
            cmap=cmocean.cm.dense
            
        title='{} - {}'.format(station, current_var)
            
        x=dfnew.index.to_julian_date()
        z=dfnew[current_var].values
        y=-dfnew.Depth.values
        JD=dfnew.index.to_julian_date()

        print(dfnew)
        xi = np.linspace(np.min(x.values), np.max(x.values), 100, endpoint=True)
        yi = np.linspace(np.max(y), np.min(y),100, endpoint=True)
      #  zi = griddata((x.values, y), z, (xi[None,:], yi[:,None]), method='cubic')
       # if current_var=="Salinity":
       #     z = np.ma.array(z, mask=z >35.5)
        print(z, current_var)
        print("Values in dataset {} from {} to {}".format(current_var,np.min(z),np.max(z)))
       
        alldates=[]; items=[]; counter=0
        previous_cast_month=-9;previous_cast_year=-9

        # Find unique CTD dates for casts - one per year
        for d in dfnew.index[::1]:
            
            if  (d.month != previous_cast_month and d.year != previous_cast_year):
                items.append(counter)
    
            alldates.append(d)
            previous_cast_month=d.month
            previous_cast_year=d.year
            counter+=1
         
        # Create various figures showing more details at teh surface and the full water column
        for minimum_depth_level in minimum_depth_levels:
            
            # Setup the figure
            fig, ax1 = plt.subplots()
         #   fig.clf()
            plot_val = np.linspace(vmin, vmax, 15, endpoint=True)
            CS = ax1.tricontourf(x, y, z, plot_val, cmap=cmap, vmin=vmin,vmax=vmax,extend='both')
           # CS=ax1.contourf(xi,yi,zi, 15, vmin=vmin,vmax=vmax, cmap=cmap)
          
            ticks_to_use = x[items]
            ticklabels = [alldates[i].strftime('%d-%m-%Y') for i in items]
            ax1.set_xticks(ticks_to_use)
            ax1.set_xticklabels(ticklabels)
            plt.xticks(rotation=45, ha='right')
            plt.ylabel("Depth (m)")
            ax1.xaxis.set_major_formatter(ticker.FixedFormatter(ticklabels))
           # plt.gcf().autofmt_xdate()
            
            cbar = fig.colorbar(CS,ax=ax1)
            # plot data points.
            if minimum_depth_level is not None:
                plt.ylim(minimum_depth_level,0)
                plt.scatter(x.ravel(),y.ravel(),marker='o',c='k',s=0.02)
                plotfile='Figures/{}_{}_shallow.png'.format(station,current_var)
            else:
                plt.ylim(minimum_depth_level,0)
                plt.scatter(x.ravel(),0.0*y.ravel(),marker='o',c='r',s=8)
                plotfile='Figures/{}_{}_alldepths.png'.format(station,current_var)
            plt.title(title)
            
            if not os.path.exists('Figures'):
                os.mkdir('Figures')
            plt.savefig(plotfile,dpi=150)
            print('=> Creating figure {}'.format(plotfile))
           # plt.show()
            

    
    
t.toc();
print("\nFINISHED\n=> It took {} seconds to do the conversions".format(t.elapsed))
        