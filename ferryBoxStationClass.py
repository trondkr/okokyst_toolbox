import matplotlib
from pathlib import Path

# matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
import numpy as np
import string

from netCDF4 import date2num, num2date
import pandas as pd
from datetime import datetime
import glob
import progressbar
import matplotlib.tri as tri
import matplotlib.dates as mdates

__author__ = 'Trond Kristiansen'
__email__ = 'trond.kristiansen@niva.no'
__created__ = datetime(2019, 1, 18)
__modified__ = datetime(2019, 2, 11)
__version__ = "1.0"
__status__ = "Development"


class FerryBoxStation:

    def __init__(self, stationid, metadata, df_st, varname):
        self.lon = metadata['longitude']
        self.lat = metadata['latitude']
        self.name = metadata['name']
        self.varname = varname
        self.df_st = df_st
        self.df_st_grouped = None
        self.refdate = "days since 1970-01-01:00:00:00"
        self.bin_days = 20
        self.stationid = stationid
        self.basedir = '../FBdata/'
        self.start_date_jd = None
        self.end_date_jd = None

        self.description()
        self.calculate_julianday()
        self.create_grouped_dataframe()

    def calculate_julianday(self):
        df2 = self.df_st.copy()
        print(self.df_st)
        df2['julianday'] = date2num(self.df_st.index.to_pydatetime(), units=self.refdate, calendar="standard")
        self.df_st = df2

    def bin_dataframe(self):
        x_bins = pd.cut(self.df_st_grouped.julianday, np.arange(self.start_date_jd + self.bin_days,
                                                                self.end_date_jd - self.bin_days,
                                                                self.bin_days))
        y_bins = pd.cut(self.df_st_grouped.latitude, np.arange(self.df_st_grouped.latitude.min(),
                                                               self.df_st_grouped.latitude.max(),
                                                               0.01))

        binned = self.df_st_grouped.groupby([x_bins, y_bins])[self.varname].mean().reset_index()

        binned.julianday = binned.julianday.apply(lambda x: x.mid)
        binned.latitude = binned.latitude.apply(lambda y: y.mid)

        return binned

    def create_grouped_dataframe(self):
        self.df_st_grouped = self.df_st.groupby(['julianday']).mean()
        self.df_st_grouped = self.df_st_grouped.reset_index()
        print("{}=>\n {}".format(self.name, self.df_st_grouped.head()))

    def description(self):
        print(
            '=> Station {} created at (lat,lon) ({},{}) for var {}'.format(self.name, self.lon, self.lat, self.varname))

    # Method for interpolating and binning the irregular data into a 
    # fine structured grid
    def interpolate_irregular_data_to_grid(self):
        # https://matplotlib.org/gallery/images_contours_and_fields/irregulardatagrid.html
        binned = self.bin_dataframe()
        xi = np.arange(self.start_date_jd, self.end_date_jd, 1)
        yi = np.arange(np.min(binned.latitude), np.max(binned.latitude), 0.01)
        triang = tri.Triangulation(binned.julianday, binned.latitude)
        interpolator = tri.LinearTriInterpolator(triang, getattr(binned, self.varname))
        Xi, Yi = np.meshgrid(xi, yi)

        return xi, yi, interpolator(Xi, Yi), binned

    def get_varname_label(self):
        return {'temperature': 'Temperatur (\$^{o}$C)',
                'salinity': 'Saltholdighet',
                'cdom_fluorescence': 'Rel. verdier',
                'turbidity': 'FTU',
                'chla_fluorescence': 'Klorofyll a fluorescens (\u03bcg/L)'}[self.varname]

    def get_varname_maxrange(self):
        return {'temperature': 20,
                'salinity': 35.5,
                'cdom_fluorescence': 5.0,
                'turbidity': 5.0,
                'chla_fluorescence': 5.0}[self.varname]

    def get_varname_minrange(self):
        return {'temperature': 0,
                'salinity': 10,
                'cdom_fluorescence': 0.0,
                'turbidity': 0.0,
                'chla_fluorescence': 0.0}[self.varname]

    def get_varname_delta(self):
        return {'temperature': 1.0,
                'salinity': 1.0,
                'cdom_fluorescence': 0.5,
                'turbidity': 0.5,
                'chla_fluorescence': 0.5}[self.varname]

    def create_station_contour_plot(self):

        xi, yi, zi, binned = self.interpolate_irregular_data_to_grid()

        fig, (ax1) = plt.subplots(nrows=1)
        levels = np.arange(self.get_varname_minrange(), self.get_varname_maxrange(), self.get_varname_delta())
        cntr1 = ax1.contourf(xi, yi, zi, levels=levels, cmap="RdBu_r", extend='max')

        cbar = plt.colorbar(cntr1, ax=ax1)
        cbar.set_label(self.get_varname_label(), rotation=90)
        cbar.ax.yaxis.set_label_position('left')

        locs, labels = plt.xticks()
        xlabels = num2date(locs, units=self.refdate, calendar="standard")
        xlabels_edited = ["{}-{:02d}-{:02d}".format(o.year, o.month, o.day) for o in xlabels]
        print("=> data period from {} to {}".format(xlabels_edited[0], xlabels_edited[-1]))
        ax1.set_xticklabels(xlabels_edited, rotation=-90)
        ax1.set_title("{}:{}".format(self.stationid, self.name))
        ax1.set_ylabel("Breddegrad")
        ax1.set_xlabel("Dato")

        fig.tight_layout()
        self.save_to_file(xlabels[0], xlabels[-1])

    #   plt.show()

    def save_to_file(self, date_start, date_end):
        if not os.path.exists('{}Figures/'.format(self.basedir)):
            os.mkdir('{}Figures'.format(self.basedir))
        if not os.path.exists('{}Figures/{}'.format(self.basedir, self.varname)):
            os.mkdir('{}Figures/{}'.format(self.basedir, self.varname))

        plotfileName = "{}Figures/{}/{}-{}-{}-to-{}.png".format(self.basedir,
                                                                self.varname,
                                                                self.name,
                                                                self.varname,
                                                                date_start,
                                                                date_end)
        if os.path.exists(plotfileName): os.remove(plotfileName)
        print("=> Saving station to file {}".format(plotfileName))
        plt.savefig(plotfileName, dpi=300, bbox_inches='tight')
        plt.close()
