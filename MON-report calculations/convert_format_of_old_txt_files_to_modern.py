import os, sys, datetime, string
import numpy as np
import pandas as pd
import csv
import glob
from pathlib import Path
import string
from ttictoc import TicToc
from dateutil.parser import parse
from netCDF4 import date2num, num2date

__author__   = 'Trond Kristiansen'
__email__    = 'trond.kristiansen@niva.no'
__created__  = datetime.datetime(2019, 11, 25)
__modified__ = datetime.datetime(2019, 11, 25)
__version__  = "1.1"
__status__   = "Development, 25.11.2019"


"""
Script to process the txt files for 2013-2019 to convert to joint format with regards to 
datetime format and some other tweaks. The conversion will result in fileds compatible with using python-ctd 
package for reading the files.

After this script run 
python convert_txt_dataframe.py

"""

station_lats={"NORD1": 67.76380, "NORD2": 67.6899,
              "OFOT1": 68.4552,"OFOT2": 68.4022,
              "OKS1":68.3951, "OKS2": 68.340,
              "SAG1": 67.9538,"SAG2": 67.97869,
              "SJON1": 66.305,"SJON2": 66.300,
              "TYS1": 68.2023,"TYS2": 68.0898,
              "GLOM1":66.8242, "GLOM2":66.8066}

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

def is_date(string, fuzzy=False):
    """
    Return whether the string can be interpreted as a date.

    :param string: str, string to check for date
    :param fuzzy: bool, ignore unknown tokens in string if True
    """
    try: 
        parse(string, fuzzy=fuzzy)
        return True

    except ValueError:
        return False

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False
     
pathin='/Users/trondkr/Dropbox/MON-data/'
pathin='/Users/trondkr/Dropbox/NIVA/OKOKYST/OKS1-2_create_new_data/'

pathout='/Users/trondkr/Dropbox/MON-data/CONVERTED/'
pathout='/Users/trondkr/Dropbox/NIVA/OKOKYST/OKS1-2_create_new_data/TEST/'

if not os.path.exists(pathout):
    os.mkdir(pathout)
    
files = [f for f in glob.glob(pathin+ "OKS2*.txt", recursive=False)]
totalfiles=len(files)
currentfile=0
print(files)

t = TicToc()
t.tic();
wrong_final_dates=[]
# stations where time column is sometimes missing
problem_stations=["TYS2","TYS1","NORD1","NORD2","SAG1","SAG2","OFOT1","OFOT2","OKS1","OKS2"]
ignore_stations=[]

print("Conversion starting\n")
for f in files:
    currentfile+=1
    
    filename_base=Path(f).resolve().stem
    if not filename_base in ignore_stations:
        print(filename_base)
        if filename_base in ['OKS2_2018_september','OFOT1_2018']:
            separator=';'
        else:
            separator='\t'
        
        newfile='{}.txt'.format(pathout+filename_base)
        if "_edited" in newfile:
            newfile=newfile.replace('_edited','')
        if os.path.exists(newfile):
            #print("Will remove file {}".format(newfile))
            os.remove(newfile)
        out=open(newfile,'a')
        progress=(currentfile/totalfiles*1.0)*100.
        print("==> New file will be written to {} ({:3.2f}% done)".format(newfile,progress))
        with open(f, encoding="utf8", errors='ignore') as infile:
            lines=infile.readlines()
            first=True
            
            print("Reading input file {}".format(f))
            listofdates=[]
           
            for line in lines:
                if first:
                    first=False
                    data="Ser;Meas;Sal.;Temp;FTU;OptOx;OxMgL;Density;Depth;Date;Time\n" #"Ser;Meas;Sal.;Temp;FTU;Opt;Opml;Density;Press;Date;Time;Lat;Lon;Depth\n"
                    out.writelines(data)
                else:
                    l = line.split(separator)
                    data=""
                    timeextra=False
                    for count,item in enumerate(l):
                     
                        item=item.replace(',','.')
                        if count==8:
                            depth=pressure_to_depth(float(l[8].replace(',','.')),station_lats[l[0]])
                            data+="{};".format(depth) 
                        elif (count==10):
                            
                            if (item=='00:00:00'):
                                timeextra=True
                                continue
                            elif (":" in item and not item=='00:00:00'):
                                data+="{};".format(item.replace(':','.'))
                                print("Found actual time {}".format(item))
                            else:
                                td=datetime.timedelta(float(item.replace(',','.')))
                                hours, remainder = divmod(td.seconds, 3600)
                                minutes, seconds = divmod(remainder, 60)
                                print("Time {} => {} {} {} {}".format(item,td,hours,minutes,seconds))
                                data+="{}.{}.{};".format(hours,minutes,seconds)
                        elif count==11 and timeextra is True:
                            # Some files have additional column with '00:00:00'
                            timeetra=False
                            td=datetime.timedelta(float(item.replace(',','.')))
                            hours, remainder = divmod(td.seconds, 3600)
                            minutes, seconds = divmod(remainder, 60)
                            data+="{}.{}.{};".format(hours,minutes,seconds)
                         #   print("Time {} => {} {} {} {}".format(item,td,hours,minutes,seconds))
                        elif count>10:
                            continue
                        elif count==9:
                            item.strip()
                            item=item.replace('\x00','')
                            if is_date(item):
                               
                                if '/' in item:
                                    newdate=item.replace('/','.')
                                    newdate=newdate.replace('\x00','')
                                    data+="{};".format(newdate)
                                    if not is_date(newdate):
                                        if not newdate in wrong_final_dates:
                                            wrong_final_dates.append(newdate)
                                            print("2 Converting date for {} went WRONG {} from {}".format(l[0],newdate,item))
                                elif '-' in item:
                                    # Date format yyyy-mm-dd converted to dd/mm/yyyy
                                    newdate=item.replace('-','.')
                                    newdate=newdate.replace('\x00','')
                                    ndate='{}.{}.{}'.format(newdate[8:11],newdate[5:7],newdate[0:4])
                                    # This is mostly SJON1
                                    data+="{};".format(ndate)
                                
                                    if not is_date(newdate):
                                        if not newdate in wrong_final_dates:
                                            wrong_final_dates.append(newdate)
                                            print("2 Converting date for {} went WRONG {} from {}".format(l[0],newdate,item))
                                else:
                                    data+="{};".format(item)
                                    if not is_date(item):
                                        if not item in wrong_final_dates:
                                            wrong_final_dates.append(newdate)
                                            print("3 Converting date for {} went WRONG {} from {}".format(l[0],newdate,item))
                        
                            else:
                                currentdate = num2date(int(item), units="days since 1899-07-01 00:00 ", calendar="standard")
                                if currentdate not in listofdates:
                                    listofdates.append(currentdate)
                                data+="{};".format(currentdate)
                        else:  
                            data+="{};".format(item.replace(',','.'))   
                    data=data[:-1]+"\n"
                    #print(data)
                    out.writelines(data)
            
            out.close()
            infile.close()
            first=True
t.toc();
print("\nFINISHED\n=> It took {} seconds to do the conversions".format(t.elapsed))
  