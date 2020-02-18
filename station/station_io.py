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
__created__ = datetime.datetime(2019, 1, 17)
__modified__ = datetime.datetime(2019, 1, 17)
__version__ = "1.0"
__status__ = "Development"

class StationIO:
    def binDataWriteToNetCDF(self, CTDConfig, basepathToNetCDF):

        # Template to write to:
        # K:\Avdeling\214-Oseanografi\DATABASER\OKOKYST_2017\OKOKYST_NS_Nord_Kvitsoy\ncbase
        # K:\Avdeling\214-Oseanografi\DATABASER\OKOKYST_2017\OKOKYST_NS_Nord_Leon\ncbase
        # Copy the original files received from Andre
        source = "/Users/trondkr/Dropbox/NIVA/OKOKYST_2017/NCFILES" + str("/{}.nc".format(self.name))
        destination = basepathToNetCDF + str("/{}.nc".format(self.name))
        print("source {} dest {}".format(source, destination))

        copyfile(source, destination)

        outfilename = basepathToNetCDF + "/%s.nc" % self.name
        cdf = Dataset(outfilename, "a")
        depthInfile = np.arange(0, len(cdf.variables["depth"][:]),1)
        attributes = cdf.__getattribute__("history")
        cdf.history=attributes + "\ntrk@niva.no : added data for OEKOKYST Nordsjoen Nord %s" % datetime.now()

        cruiseNumber=0

        for stationIndex, de in enumerate(self.depth):
            maxDepth = int(max(de))
            minDepth = int(min(de))
            dateObject = num2date(self.julianDay[stationIndex], units=CTDConfig.refdate, calendar="standard")

            print("\n=> %s: depth range for %s at : %s - %s m" % (self.name, dateObject, minDepth, maxDepth))

            # Setup the grid to interpolate to
            Y = np.arange(minDepth, maxDepth, 1)

            sa = np.asarray(self.salinity[stationIndex].values)
            te = np.asarray(self.temperature[stationIndex].values)
            ox = np.asarray(self.oxygen[stationIndex].values)
            oxsat = np.asarray(self.oxsat[stationIndex].values)
            sa=np.ma.masked_where(sa<=0,sa)
            te=np.ma.masked_where(te<-1.7,te)
            
            te_interp = scipy.interpolate.interp1d(de.values[0:len(te)], te, 
                                                        fill_value=np.nan,
                                                        bounds_error=False,
                                                        kind="cubic")
            sa_interp = scipy.interpolate.interp1d(de.values[0:len(sa)], sa, 
                                                        fill_value=np.nan,
                                                        bounds_error=False,
                                                        kind="cubic")

            if (len(ox) > len(de.values)):
                ox_interp = scipy.interpolate.interp1d(de.values[0:len(de)], ox[0:len(de)], 
                                                        fill_value=np.nan,
                                                        bounds_error=False,
                                                        kind="cubic")
            else:
                ox_interp = scipy.interpolate.interp1d(de.values[0:len(ox)], ox[0:len(ox)], 
                                                        fill_value=np.nan,
                                                        bounds_error=False,
                                                        kind="cubic")
            if (len(oxsat) > len(de.values)):
                oxsat_interp = scipy.interpolate.interp1d(de.values[0:len(de)], oxsat[0:len(de)], 
                                                            fill_value=np.nan,
                                                            bounds_error=False,
                                                            kind="cubic")
            else:
                oxsat_interp = scipy.interpolate.interp1d(de.values[0:len(oxsat)], oxsat[0:len(oxsat)], 
                                                            fill_value=np.nan,
                                                            bounds_error=False,
                                                            kind="cubic")
            startIndex, endIndex = self.findStartAndEndIndexToInsetData(depthInfile, Y)

            cdf.variables["depth"][:] = 1e20
            cdf.variables["depth1"][:] = 1e20
            cdf.variables["depth2"][:] = 1e20
            cdf.variables["salt"][cruiseNumber, :] = 1e20
            cdf.variables["ftu"][cruiseNumber, :] = 1e20
            cdf.variables["temp"][cruiseNumber, :] = 1e20
            cdf.variables["O2mg"][cruiseNumber, :] = 1e20
            cdf.variables["O2sat"][cruiseNumber, :] = 1e20

            # No VT52 and VT75 in February 2017
            if (self.name in ["VT52","VT75"] and int(dateObject.year)==2017 and int(dateObject.month)==2):
                print("EMPTY DATA ADDED FOR STATION {}".format(self.name))

            else:
                cdf.variables["depth"][:] = depthInfile
                cdf.variables["depth1"][:] = depthInfile-0.5
                cdf.variables["depth2"][:] = depthInfile+0.5

                print("=> cruisenumber {}".format(cruiseNumber))
                cdf.variables["salt"][cruiseNumber, startIndex:endIndex] = sa_interp(Y)
                cdf.variables["temp"][cruiseNumber, startIndex:endIndex] = te_interp(Y)
                cdf.variables["ftu"][cruiseNumber, startIndex:endIndex] = ftu_interp(Y)
                cdf.variables["O2mg"][cruiseNumber, startIndex:endIndex] = ox_interp(Y)
                cdf.variables["O2sat"][cruiseNumber, startIndex:endIndex] = oxsat_interp(Y)
                print("Temp range {} to {}".format(np.min(cdf.variables["temp"][:]), np.max(cdf.variables["temp"][:])))
                print("Salt range {} to {}".format(np.min(cdf.variables["salt"][:]), np.max(cdf.variables["salt"][:])))
                print("FTU range {} to {}".format(np.min(cdf.variables["ftu"][:]), np.max(cdf.variables["ftu"][:])))

            cruiseNumber += 1

        print("Will write to file %s"%(outfilename))
        cdf.close()