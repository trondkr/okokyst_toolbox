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
 
__author__ = 'Trond Kristiansen'
__email__ = 'trond.kristiansen@niva.no'
__created__ = datetime.datetime(2019, 12, 4)
__modified__ = datetime.datetime(2020, 1, 29)
__version__ = "1.0"
__status__ = "Development"

  
"""
Script that converts the output from convert_format_of_old_files_to_modern.py into standard SAIV files
that can be read using python ctd scripts.

RUN convert_format_of_old_txt_files_to_modern.py FIRST!

Trond Kristiansen, 4.12.2019
"""
def create_directory_structure(dateobject,output_basedir,filename_base):
    date_formatted='{}-{:02d}-{:02d}'.format(dateobject.year,dateobject.month,dateobject.day)
    new_directory_name=date_formatted
    if not os.path.exists(output_basedir+new_directory_name):
        print("Creating folder: {}".format(output_basedir+new_directory_name))
        os.mkdir(output_basedir+new_directory_name)
        
    new_subdirectory_name=new_directory_name+' CTD data'
    if not os.path.exists(output_basedir+new_directory_name+'/'+new_subdirectory_name):
        print("Creating folder: {}".format(output_basedir+new_directory_name+'/'+new_subdirectory_name))
        os.mkdir(output_basedir+new_directory_name+'/'+new_subdirectory_name)
    return output_basedir+new_directory_name+'/'+new_subdirectory_name+'/'+filename_base+'.txt'
    
def date_from_string(current_date):
    return datetime.datetime(int(current_date[6:10]),int(current_date[3:5]),int(current_date[0:2]))
    
def convert_file_into_files(filename,output_basedir,filename_base):
    
    first=True; counter=0
    with open(filename, encoding="utf8", errors='ignore') as infile:
        lines=infile.readlines()
    
        print("Reading input file {}".format(f))
        outfile='temp.txt'
        if os.path.exists(outfile): os.remove(outfile)
        out=open(outfile,'a')
        remove_last_line=False
        remove_first_line=False
        separator=';' # Could also be ";" as in OKS2_2018_september.txt
        
        for line in lines:
            l = line.split(separator)
        
            if len(l)==1:
                # Occassionally return causes
                break
           
            if counter==0:
                first=False
                header=line
                out.writelines(header)
            elif counter==1:
                current_date=l[9]
                first_dateobject=date_from_string(current_date)
                fullpath = create_directory_structure(first_dateobject,output_basedir,filename_base)
                out.writelines(line)
            else:
                current_date=l[9]
                dateobject=date_from_string(current_date)
                
                if dateobject.day != first_dateobject.day:
                    print("Moving file to {}".format(fullpath))
                    out.close()
                    if os.path.exists(fullpath):os.remove(fullpath)
                    
                    if separator=='\t':
                        reader = csv.reader(open('temp.txt', "rU"), delimiter=separator)
                        writer = csv.writer(open(fullpath, 'w'), delimiter=';')
                        writer.writerows(reader)
                    else:
                        os.rename('temp.txt',fullpath)  
            
                    outfile='temp.txt'
                    out=open(outfile,'a')
                    out.writelines(header)
                    
                    # compare the next few lines to see if pressure is wrong.
                    line1=lines[counter].split(separator)
                    line2=lines[counter+1].split(separator)
                    line3=lines[counter+2].split(separator)
                    
                    linelast1=lines[-1].split(separator)
                    linelast2=lines[-2].split(separator)
            
                    if line1[8] < line2[8] > line3[8]:
                        remove_first_line=True
                    else:
                        remove_first_line=False
            
                    if(len(linelast1) > 2):
                        if abs(float(linelast1[8]))-abs(float(linelast2[8])) > 10:
                            remove_last_line=True
                        else:
                            remove_last_line=False
                            
                    # Create new folder for the next file
                    fullpath = create_directory_structure(dateobject,output_basedir,filename_base)
                    print("Found new cast {}".format(dateobject))
                
                if (remove_last_line and counter==len(lines)-1):
                    continue
                else:
                    if remove_first_line is False:
                        out.writelines(line)
                    remove_first_line=False
                        
            if counter>1:   
                first_dateobject=dateobject
            
                
            counter+=1    
        out.close()
        if os.path.exists(fullpath):os.remove(fullpath)
        
        if separator=='\t':
            reader = csv.reader(open('temp.txt', "rU"), delimiter=separator)
            writer = csv.writer(open(fullpath, 'w'), delimiter=';')
            writer.writerows(reader)
        else:
            os.rename('temp.txt',fullpath)  
    

output_basedir='/Users/trondkr/Dropbox/MON-data/CONVERTED/'
#output_basedir='/Users/trondkr/Dropbox/NIVA/OKOKYST/OKS1-2_create_new_data/TEST2/'
input_basedir='/Users/trondkr/Dropbox/NIVA/OKOKYST/OKS1-2_create_new_data/TEST/'
files = [f for f in glob.glob(input_basedir+ "OKS2*.txt", recursive=False)]
files.sort()
ignore_stations=[]

print("Conversion starting\n")
for f in files:
   
    filename_base=Path(f).resolve().stem
    if not filename_base in ignore_stations:
        station_name=filename_base.split('_')
        convert_file_into_files(f,output_basedir,station_name[0])