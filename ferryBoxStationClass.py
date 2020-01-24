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
#import tables

__author__ = 'Trond Kristiansen'
__email__ = 'trond.kristiansen@niva.no'
__created__ = datetime(2019, 1, 18)
__modified__ = datetime(2019, 1, 18)
__version__ = "1.0"
__status__ = "Development"
    

class FerryBoxStation:

    def __init__(self,metadata,df_st):
        self.lon=metadata['longitude']
        self.lat=metadata['latitude']
        self.name=metadata['name']
        self.df_st=df_st
        self.description()
        
    def description(self):
        print('=> Station {} created at (lat,lon) ({},{})'.format(self.name,self.lon,self.lat))
        