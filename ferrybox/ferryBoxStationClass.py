import os
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.tri as tri
import numpy as np
import pandas as pd
from matplotlib.collections import PatchCollection
from matplotlib.colors import ListedColormap
from matplotlib.patches import Rectangle
from netCDF4 import date2num, num2date

from .ferrybox_calibration import FerryBoxCalibration

__author__ = 'Trond Kristiansen'
__email__ = 'trond.kristiansen@niva.no'
__created__ = datetime(2019, 1, 18)
__modified__ = datetime(2020, 3, 9)
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
        self.bin_days = 50
        self.stationid = stationid
        self.basedir = '../FBdata/'
        self.start_date_jd = None
        self.end_date_jd = None
        # The distance to extract data in decomal degrees surrouding the station
        self.dist = metadata['dist']
        if metadata["vessel"] == "FA":
            self.ybin_dist = 0.05
            if stationid in ["VT3"]:
                self.ybin_dist = 0.05
                self.bin_days = 20
            #self.ybin_dist = metadata['ybin_dist']

        if metadata["vessel"] == "TF":
            if metadata["name"] in ["Barentshavet"]:
                self.ybin_dist = 0.13
            else:
                self.ybin_dist = 0.035
                if stationid in ["VR25", "VR23", "VT45", "VT22", "VT76"]:
                    self.ybin_dist=0.05
                    self.bin_days=23

        # Defines whether y-axis is longitude or latitude
        self.plot_along_latitude = metadata['plot_along_latitude']

        self.description()
        self.calculate_julianday()
        self.create_grouped_dataframe()

    def description(self):
        print(
            '=> Station {} created at (lat,lon) ({},{}) for var {}'.format(self.name, self.lon, self.lat,
                                                                           self.varname))

    def calculate_julianday(self):
        df2 = self.df_st.copy()

        if isinstance(self.df_st.index, pd.Int64Index):
            df2['julianday'] = date2num(pd.DatetimeIndex(self.df_st.time).to_pydatetime(), units=self.refdate,
                                        calendar="standard")
        else:
            df2['julianday'] = date2num(self.df_st.index.to_pydatetime(), units=self.refdate, calendar="standard")
        self.df_st = df2

    def bin_dataframe2(self):
        numcols, numrows = 100, 10

        xi = np.linspace(self.df_st_grouped.longitude.min(), self.df_st_grouped.longitude.max(), numcols)
        yi = np.linspace(self.df_st_grouped.latitude.min(), self.df_st_grouped.latitude.max(), numrows)
        xi, yi = np.meshgrid(xi, yi)
        from scipy.interpolate import griddata
        x, y, z = self.df_st_grouped.longitude.values, self.df_st_grouped.latitude.values, self.df_st_grouped.chla_fluorescence.values

        binned = griddata((x, y), z, (xi, yi), method='linear', fill_value=np.nan, rescale=False)

        julianday = xi
        latitude = yi

        return binned, julianday, latitude

    def create_warming_strips_plot(df):
        FIRST = 2020
        LAST = 2021  # inclusive

        # Reference period for the center of the color scale
        FIRST_REFERENCE = 1971
        LAST_REFERENCE = 2000
        LIM = 0.7  # degrees


        # the colors in this colormap come from http://colorbrewer2.org
        # the 8 more saturated colors from the 9 blues / 9 reds

        cmap = ListedColormap([
            '#08306b', '#08519c', '#2171b5', '#4292c6',
            '#6baed6', '#9ecae1', '#c6dbef', '#deebf7',
            '#fee0d2', '#fcbba1', '#fc9272', '#fb6a4a',
            '#ef3b2c', '#cb181d', '#a50f15', '#67000d',
        ])

        fig = plt.figure(figsize=(10, 1))

        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_axis_off()

        # create a collection with a rectangle for each year

        col = PatchCollection([
            Rectangle((y, 0), 1, 1)
            for y in range(FIRST, LAST + 1)
        ])

        # set data, colormap and color limits

        col.set_array(anomaly)
        col.set_cmap(cmap)
        col.set_clim(reference - LIM, reference + LIM)
        ax.add_collection(col)
        ax.set_ylim(0, 1)
        ax.set_xlim(FIRST, LAST + 1)

        fig.savefig('{}_warming_stripes.png'.format(CMIP6_name))

    def bin_dataframe(self):

        x_bins = pd.cut(self.df_st_grouped.julianday, np.arange(self.start_date_jd,
                                                                self.end_date_jd,
                                                                self.bin_days),
                        right=True, include_lowest=True)

        if not self.plot_along_latitude:
            y_bins = pd.cut(self.df_st_grouped.longitude, np.arange(self.df_st_grouped.longitude.min(),
                                                                    self.df_st_grouped.longitude.max(),
                                                                    self.ybin_dist))
        else:
            y_bins = pd.cut(self.df_st_grouped.latitude, np.arange(self.df_st_grouped.latitude.min(),
                                                                   self.df_st_grouped.latitude.max(),
                                                                   self.ybin_dist))

        binned = self.df_st_grouped.groupby([x_bins, y_bins])[self.varname].mean().reset_index()
        binned.julianday = binned.julianday.apply(lambda x: x.mid)
        if not self.plot_along_latitude:
            binned.longitude = binned.longitude.apply(lambda y: y.mid)
        else:
            binned.latitude = binned.latitude.apply(lambda y: y.mid)

        return binned

    def create_grouped_dataframe(self):
        self.df_st_grouped = self.df_st.groupby(['julianday']).mean()
        self.df_st_grouped = self.df_st_grouped.reset_index()
        print("{}=>\n {}".format(self.name, self.df_st_grouped.head()))

    # Method for interpolating and binning the irregular data into a
    # fine structured grid
    def interpolate_irregular_data_to_grid(self):
        # https://matplotlib.org/gallery/images_contours_and_fields/irregulardatagrid.html
        binned = self.bin_dataframe()

        xi = np.arange(self.start_date_jd, self.end_date_jd, 1)

        if not self.plot_along_latitude:
            yi = np.arange(np.nanmin(binned.longitude), np.nanmax(binned.longitude), 0.1)
            triang = tri.Triangulation(binned.julianday, binned.longitude)
        else:

            yi = np.arange(np.nanmin(binned.latitude), np.nanmax(binned.latitude), 0.1)
            triang = tri.Triangulation(binned.julianday, binned.latitude)
        interpolator = tri.LinearTriInterpolator(triang, getattr(binned, self.varname))
        Xi, Yi = np.meshgrid(xi, yi)

        return xi, yi, interpolator(Xi, Yi), binned

    def get_varname_label(self):
        return {'temperature': 'Temperatur ($^\circ$C)',
                'salinity': 'Saltholdighet',
                'cdom_fluorescence': 'Rel. verdier',
                'turbidity': 'FTU',
                'chla_fluorescence': 'Klorofyll a fluorescens (\u03bcg/L)'}[self.varname]

    def get_varname_maxrange(self):
        return {'temperature': 22,
                'salinity': 36,
                'cdom_fluorescence': 3.0,
                'turbidity': 50.0,
                'chla_fluorescence': 3.5}[self.varname]

    def get_varname_minrange(self):
        return {'temperature': 0,
                'salinity': 20,
                'cdom_fluorescence': 0.0,
                'turbidity': 0.0,
                'chla_fluorescence': 0.0}[self.varname]

    def get_varname_delta(self):
        return {'temperature': 0.5,
                'salinity': 0.25,
                'cdom_fluorescence': 0.1,
                'turbidity': 0.5,
                'chla_fluorescence': 0.2}[self.varname]

    def create_station_contour_plot(self):
        xi, yi, zi, binned = self.interpolate_irregular_data_to_grid()

        fig, (ax1) = plt.subplots(nrows=1)

        cmap = "RdBu_r"

        levels = np.arange(self.get_varname_minrange(), self.get_varname_maxrange(), self.get_varname_delta())
        cntr1 = ax1.contourf(xi, yi, zi, levels=levels, cmap=cmap, extend='max')

        cbar = plt.colorbar(cntr1, ax=ax1)
        cbar.set_label(self.get_varname_label(), rotation=90)
        cbar.ax.yaxis.set_label_position('left')

        locs, labels = plt.xticks()
        xlabels = num2date(locs, units=self.refdate, calendar="standard")
        xlabels_edited = ["{}-{:02d}-{:02d}".format(o.year, o.month, o.day) for o in xlabels]
        print("=> data period from {} to {}".format(xlabels_edited[0], xlabels_edited[-1]))
        ax1.set_xticklabels(xlabels_edited, rotation=-90)
        ax1.set_title("{}:{}".format(self.stationid, self.name))
        if self.stationid in ['Trondheimsfjorden']:
            ax1.set_title("Trondheimsfjorden")
        if self.stationid in ['VR7-VR21-VR24']:
            ax1.set_title("Barentshavet")
        if not self.plot_along_latitude:
            ax1.set_ylabel("Lengdegrad")
        else:
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

        plotfileName = "{}Figures/{}/{}-{}-{}-to-{}".format(self.basedir,
                                                            self.varname,
                                                            self.name,
                                                            self.varname,
                                                            date_start.year,
                                                            date_end.year)
        if date_start.year < date_end.year:
            plotfileName += '_multiyear'
        plotfileName += '.png'

        if os.path.exists(plotfileName): os.remove(plotfileName)
        print("=> Saving station to file {}".format(plotfileName))
        plt.savefig(plotfileName, dpi=300, bbox_inches='tight')
        plt.close()

    def extract_calibration_data(self, varname):
        fbc = FerryBoxCalibration()
        fbc.extract_calibration_data(self.df_st, varname)
