import matplotlib
from pathlib import Path

# matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
import numpy as np
import string

from netCDF4 import date2num, num2date
import pandas as pd
from datetime import datetime, timedelta
import glob
import progressbar
import matplotlib.tri as tri
import matplotlib.dates as mdates


class FerryBoxCalibration:

    def get_observation_times_2019(self):
        # Email fra Kai:
        # # Prøvene tas på norgående dvs før lokal tid 1000, du kan jo sette f.eks 12 da den går igjen kl 1400 lokal tid
        #
        df = pd.read_excel('/Users/trondkr/Dropbox/NIVA/OKOKYST/FBdata/14411_IO19.xlsx', columns=['Proevedato'])
        return [d + timedelta(hours=7) for d in df['Proevedato']]

    def get_data_for_specific_time(self, dates, df, varname):
        df = df.dropna()
        for calibration_date in dates:
            index=df.index.get_loc(calibration_date, method='nearest')
            if varname == 'temperature':
                idx = df.temperature[index]
            if varname == 'salinity':
                idx = df.salinity[index]
            time_idx = df.index[index]
          #  print("Extracting data for comparison with calibration for {} at index {} for {} on {}".format(calibration_date,
          #                                                                                           idx, varname,time_idx))

            print(idx)

    def extract_calibration_data(self, df, varname):
        dates = self.get_observation_times_2019()
        self.get_data_for_specific_time(dates, df, varname)
