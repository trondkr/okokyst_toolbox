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


class FerryBoxPlot:
    def get_varname_label(self):
        return {'temperature': 'Temperatur ($^\circ$C)',
                'salinity': 'Saltholdighet',
                'cdom_fluorescence': 'Rel. verdier',
                'turbidity': 'FTU',
                'chla_fluorescence': 'Klorofyll a fluorescens (\u03bcg/L)'}[self.varname]


    def get_varname_maxrange(self):
        return {'temperature': 20,
                'salinity': 35.5,
                'cdom_fluorescence': 20.0,
                'turbidity': 25.0,
                'chla_fluorescence': 5.0}[self.varname]


    def get_varname_minrange(self):
        return {'temperature': 0,
                'salinity': 10,
                'cdom_fluorescence': 0.0,
                'turbidity': 0.0,
                'chla_fluorescence': 0.0}[self.varname]


    def get_varname_delta(self):
        return {'temperature': 0.5,
                'salinity': 1.0,
                'cdom_fluorescence': 1,
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
        if self.stationid in ['VT22']:
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
                                                            date_start,
                                                            date_end)
        if date_start.year < date_end.year:
            plotfileName += '_multiyear'
        plotfileName += '.png'

        if os.path.exists(plotfileName): os.remove(plotfileName)
        print("=> Saving station to file {}".format(plotfileName))
        plt.savefig(plotfileName, dpi=300, bbox_inches='tight')
        plt.close()
