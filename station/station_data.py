import numpy as np
import matplotlib.pyplot as plt
import cmocean
from netCDF4 import date2num, num2date, Dataset
import os, sys
import matplotlib.cm as cmx
import scipy.interpolate
from shutil import copyfile
import datetime
import pandas as pd
import locale
import matplotlib.dates as mdates

__author__ = 'Trond Kristiansen'
__email__ = 'trond.kristiansen@niva.no'
__created__ = datetime.datetime(2017, 2, 24)
__modified__ = datetime.datetime(2019, 1, 13)
__version__ = "1.0"
__status__ = "Development"


class StationData:
    def addData(self, salt, temp, oxy, oxsat, ftu, depth, julianDay):
        self.salinity.append(salt)
        self.temperature.append(temp)
        self.oxygen.append(oxy)
        self.oxsat.append(oxsat)
        self.depth.append(depth)
        self.ftu.append(ftu)
        self.julianDay.append(julianDay)

    def getTimeRangeForStation(self, CTDConfig):
        dateObjectStart = num2date(self.julianDay[0], units=CTDConfig.refdate, calendar="standard")
        dateObjectEnd = num2date(self.julianDay[-1], units=CTDConfig.refdate, calendar="standard")

        return dateObjectStart, dateObjectEnd

    def findStartAndEndIndexToInsetData(self, depthInFile, Y):
        startIndexFound = False
        endIndexFound = False
        for d, de in enumerate(depthInFile):
            if (float(de) == float(min(Y))) and startIndexFound is False:
                startIndex = d
                startIndexFound = True

            if (float(de) == float(max(Y))) and endIndexFound is False:
                endIndex = d
                endIndexFound = True
        if endIndexFound is False or startIndexFound is False:
            print("FAILED: to find start index %s and end index %s" % (startIndex, endIndex))
            sys.exit()
        return startIndex, endIndex + 1

    def get_max_depth(self):
        max_depth = 0
        for de in self.depth:
            m = max(de)
            if m > max_depth:
                max_depth = m
        return max_depth

    def special_MON_cases_where_oxygen_already_in_mlOL(self, CTDConfig, current_date, d):
        # Special cases first
        if current_date.year in [2018] and current_date.month in [9] and self.name in ['OKS2']:
            return np.asarray(self.oxygen[d].values)

        if current_date.year in [2018] and self.name in ['SJON1', 'SJON2', 'OKS1', 'OKS2', 'NORD1', 'NORD2',
                                                         'OFOT1', 'OFOT2', 'SAG1', 'SAG2', 'TYS1', 'TYS2']:
            return np.asarray(self.oxygen[d].values) * CTDConfig.mgperliter_to_mlperliter

        if current_date.year in [2013, 2014, 2015, 2018, 2019]:
            return np.asarray(self.oxygen[d].values)
        # The ones that needs to be converted to mlO/L
        if current_date.year in [2016, 2017]:
            return np.asarray(self.oxygen[d].values) * CTDConfig.mgperliter_to_mlperliter

    def createTimeSection(self, CTDConfig):
        max_depth = self.get_max_depth()

        self.Y = np.arange(0, max_depth, 1)
        self.X = np.arange(0, len(self.julianDay), 1)
        stDates = num2date(self.julianDay[:], units=CTDConfig.refdate, calendar="standard")

        self.sectionTE = np.ma.masked_all((len(self.X), len(self.Y)))
        self.sectionSA = np.ma.masked_all((len(self.X), len(self.Y)))
        self.sectionOX = np.ma.masked_all((len(self.X), len(self.Y)))
        self.sectionOXS = np.ma.masked_all((len(self.X), len(self.Y)))
        self.sectionFTU = np.ma.masked_all((len(self.X), len(self.Y)))

        for d, de in enumerate(self.depth):
            current_date = stDates[d]

            sa = np.asarray(self.salinity[d].values)
            te = np.asarray(self.temperature[d].values)

            # Convert from mgO/L to mlO/L for reporting
            if self.survey == "MON":
                ox = self.special_MON_cases_where_oxygen_already_in_mlOL(CTDConfig, current_date, d)
            else:
                ox = np.asarray(self.oxygen[d].values) * CTDConfig.mgperliter_to_mlperliter  # mg/L to ml/L

            oxsat = np.asarray(self.oxsat[d].values)
            if self.name not in ['SJON1', 'SJON2']:
                ftu = np.asarray(self.ftu[d].values)

            interpolation_method = "linear"  # "cubic"
            fill_value = np.nan  # "extrapolate"
            te_interp = scipy.interpolate.interp1d(de.values, te,
                                                   fill_value=fill_value,
                                                   bounds_error=False,
                                                   kind=interpolation_method)

            sa_interp = scipy.interpolate.interp1d(de.values, sa,
                                                   fill_value=fill_value,
                                                   bounds_error=False,
                                                   kind=interpolation_method)
            if self.name not in ['SJON1', 'SJON2']:
                ftu_interp = scipy.interpolate.interp1d(de.values, ftu,
                                                        fill_value=fill_value,
                                                        bounds_error=False,
                                                        kind=interpolation_method)
            if len(ox) > len(de.values):
                ox_interp = scipy.interpolate.interp1d(de.values, ox[0:len(de)],
                                                       fill_value=fill_value,
                                                       bounds_error=False,
                                                       kind=interpolation_method)
            else:
                ox_interp = scipy.interpolate.interp1d(de.values[0:len(ox)], ox,
                                                       fill_value=fill_value,
                                                       bounds_error=False,
                                                       kind=interpolation_method)

            if len(oxsat) > len(de.values):
                oxsat_interp = scipy.interpolate.interp1d(de.values, oxsat[0:len(de)],
                                                          fill_value=fill_value,
                                                          bounds_error=False,
                                                          kind=interpolation_method)
            else:
                oxsat_interp = scipy.interpolate.interp1d(de.values[0:len(oxsat)], oxsat,
                                                          fill_value=fill_value,
                                                          bounds_error=False,
                                                          kind=interpolation_method)
            self.sectionTE[d, :] = te_interp(self.Y)
            self.sectionSA[d, :] = sa_interp(self.Y)
            self.sectionOX[d, :] = ox_interp(self.Y)
            self.sectionOXS[d, :] = oxsat_interp(self.Y)
            if self.name not in ['SJON1', 'SJON2']:
                self.sectionFTU[d, :] = ftu_interp(self.Y)

    def describeStation(self, CTDConfig):
        print("-------------------------------------")
        print("Station: %s" % (self.name))
        print("-------------------------------------")

        #  print("Depths: %s" % len(self.depth))
        print("Julian dates: %s" % len(self.julianDay))

        stDates = num2date(self.julianDay[:], units=CTDConfig.refdate, calendar="standard")

        # Need to find the start and end for May-Sept and June - Aug

        periods = [[5, 9], [6, 8]]
        foundStart = False
        foundEnd = False
        year = 2019
        foundStartFullYear = False
        foundEndFullYear = False
        for period in periods:
            for d, dd in enumerate(stDates):
                if dd.year == year and dd.month == period[0] and foundStart is False:
                    indStart = d
                    foundStart = True
                if dd.year == year and dd.month == period[1] and foundEnd is False:
                    indEnd = d
                    foundEnd = True

                if dd.year == year and foundStartFullYear is False:
                    indStartFullYear = d
                    foundStartFullYear = True
                if dd.year == year:
                    indEndFullYear = d
                    foundEndFullYear = True

            sa = np.asarray([item for sublist in self.salinity[indStart:indEnd] for item in sublist])
            te = np.asarray([item for sublist in self.temperature[indStart:indEnd] for item in sublist])
            de = np.asarray([item for sublist in self.depth[indStart:indEnd] for item in sublist])
            ox = np.asarray([item for sublist in self.oxygen[indStart:indEnd] for item in sublist])
            foundEnd = False
            foundStart = False

            sa = np.ma.masked_where(de > 10, sa)
            te = np.ma.masked_where(de > 10, te)
            sa = np.ma.masked_invalid(sa)
            ox = np.ma.masked_invalid(ox)
            te = np.ma.masked_invalid(te)

            print("Period: %s to %s" % (stDates[indStart], stDates[indEnd]))
            print("Mean salt:  %3.2f " % (np.ma.mean(sa)))
            print("Mean temp:  %3.2f " % (np.ma.mean(te)))
            print("Mean oxygen:  %3.2f " % (np.ma.mean(ox)))

        print("Overall through the year {}".format(year))
        ox = np.asarray([item for sublist in self.oxygen[indStartFullYear:indEndFullYear] for item in sublist])
        ftu = np.asarray([item for sublist in self.ftu[indStartFullYear:indEndFullYear] for item in sublist])
        sa = np.asarray([item for sublist in self.salinity[indStartFullYear:indEndFullYear] for item in sublist])
        te = np.asarray([item for sublist in self.temperature[indStartFullYear:indEndFullYear] for item in sublist])
        de = np.asarray([item for sublist in self.depth[indStartFullYear:indEndFullYear] for item in sublist])

        sa = np.ma.masked_where(sa < 1, sa)
        te = np.ma.masked_where(te < 1, te)
        sa = np.ma.masked_invalid(sa)
        ox = np.ma.masked_invalid(ox)
        te = np.ma.masked_invalid(te)

        minimumBottomOxygen = np.nanmin(ox)
        minimumBottomDepthIndex = np.where(ox == np.nanmin(ox))[0]
        print(minimumBottomDepthIndex)
        if (minimumBottomDepthIndex > len(de)):
            minimumBottomDepthIndex = len(de)

        print("Minimum oxygen %3.2f at depth: %3.2f" % (minimumBottomOxygen, de[minimumBottomDepthIndex]))

        minimumTemp = np.nanmin(te)
        minimumTempDepthIndex = np.where(te == np.nanmin(te))[0]
        if len(minimumTempDepthIndex) > 1:
            minimumTempDepthIndex = minimumTempDepthIndex[0]

        print("Minimum temperature %3.2f at depth: %3.2f" % (minimumTemp, de[minimumTempDepthIndex]))

        maximumTemp = np.nanmax(te)
        maximumTempDepthIndex = np.where(te == np.nanmax(te))[0]
        if len(maximumTempDepthIndex) > 1:
            maximumTempDepthIndex = maximumTempDepthIndex[0]
        print("Maximum temperature %3.2f at depth: %3.2f" % (maximumTemp, de[maximumTempDepthIndex]))
