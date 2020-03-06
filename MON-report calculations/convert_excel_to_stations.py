import os, sys, datetime, string
import numpy as np
import pandas as pd
import csv
import glob
from pathlib import Path
import string
from ttictoc import TicToc

__author__   = 'Trond Kristiansen'
__email__    = 'trond.kristiansen@niva.no'
__created__  = datetime.datetime(2019, 11, 22)
__modified__ = datetime.datetime(2019, 11, 22)
__version__  = "1.1"
__status__   = "Development, 22.11.2019"

"""
Script to process the output for 2018 and 2019 of CTD observations exported from Excel spreadsheet. For 2018 
depth is calculated from pressure and replaces the current values in the depth column. Also, all commas are converted 
to dots to use with pandas.

After this script run 
python convert_format_of_old_files_to_modern.py
python convert_txt_to_dataframe.py

"""

def pressure_to_depth(P, lat):
    """Compute depth from pressure and latitude
    Usage: depth(P, lat)
    Input:
        P = Pressure,     [dbar]
        lat = Latitude    [deg]
    Output:
        Depth             [m]
    Algorithm: UNESCO 1983
    """

    # Use numpy for trigonometry if present
    from numpy import sin, pi

    a1 =  9.72659
    a2 = -2.2512e-5
    a3 =  2.279e-10
    a4 = -1.82e-15

    b  =  1.092e-6

    g0 =  9.780318
    g1 =  5.2788e-3
    g2 =  2.36e-5

    rad = pi / 180.

    X = sin(lat*rad)
    X = X*X
    grav = g0 * (1.0 + (g1 + g2*X)*X) + b*P
    nom = (a1 + (a2 + (a3 + a4*P)*P)*P)*P

    return nom / grav

path='/Users/trondkr/Dropbox/MON-data/'
files = [f for f in glob.glob(path + "EXPORTED/*.txt", recursive=False)]
totalfiles=len(files)
currentfile=0

nocounter=['NORD1_2019','NORD2_2019','OFOT1_2019','OFOT2_2019','OKS1_2019','OKS2_2019',
           'SAG1_2019','SAG2_2019','SJON1_2019','SJON2_2019','TYS1_2019','TYS2_2019']
withcounter=[]

# Originally from Excel spreadsheet these files did not have Serial counter
withcounter=['OKS2_2018','NORD1_2018','NORD2_2018','OFOT1_2018','OFOT2_2018','OKS1_2018',
         'OKS2_2018','SAG1_2018','SAG2_2018','SJON1_2018','SJON2_2018','TYS1_2018', 'TYS2_2018']

header="Ser	Meas	Salinity	Temp	F	Opt	Opml	Density	Press	Date	Time	Lat	Lon	Depth\n"
t = TicToc()
t.tic();
print("Conversion starting\n")
for f in files:
    currentfile+=1
    filename_base=Path(f).resolve().stem
    newfile='{}_edited.txt'.format(path+filename_base)
    if os.path.exists(newfile):
        os.remove(newfile)
    out=open(newfile,'a')
    progress=(currentfile/totalfiles*1.0)*100.
    print("==> New file will be written to {} ({:3.2f}% done)".format(newfile,progress))
    infile=open(f,'r')
    lines=infile.readlines()
    counter=0
    first=True
    
    for line in lines:
        offset=0
        latindex=10
        pressindex=7
        if filename_base in withcounter:
            offset=1
    
        l = line.split()
      
        lat=float(l[latindex+offset].replace(',','.'))
        press=float(l[pressindex+offset].replace(',','.'))
        depth=pressure_to_depth(press, lat)
        
        if first:
            out.writelines(header)
            first=False
        if filename_base in nocounter:
            data = "{}	{}  {}	".format(l[0].replace(',','.'),counter,l[1].replace(',','.'))
        else:
            data = "{}	{}	".format(l[0].replace(',','.'),l[1].replace(',','.'))
        
        for item in l[2:-1]:
            data+="{} ".format(item.replace(',','.'))
        
        # 2018 data have to convert press to depth
        if filename_base in withcounter:
            data+="{}\n".format(str(depth).replace(',','.'))
        else:
            data+="{}\n".format(str(press).replace(',','.'))
       
        out.writelines(data)
        counter+=1
    counter=0 
    out.close()
    infile.close()
    first=True
t.toc();
print("\nFINISHED\n=> It took {} seconds to do the conversions".format(t.elapsed))
  