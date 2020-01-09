import numpy as np
import matplotlib.pyplot as plt
import cmocean
from netCDF4 import date2num, num2date, Dataset
import os, sys
import matplotlib.cm as cmx
import scipy.interpolate
from shutil import copyfile
import datetime

# Local files
import okokyst_ts_plot

__author__ = 'Trond Kristiansen'
__email__ = 'trond.kristiansen@niva.no'
__created__ = datetime.datetime(2017, 2, 24)
__modified__ = datetime.datetime(2019, 1, 8)
__version__ = "1.0"
__status__ = "Development"

class Station(object):

    def __init__(self, name, survey):
        self.name = name
        self.survey = survey
        self.header = None
        self.mainHeader = None

        self.salinity = []
        self.temperature = []
        self.oxygen = []
        self.oxsat = []
        self.ftu = []
        self.julianDay = []
        self.depth = []

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
        return startIndex, endIndex+1

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

    def createTimeSection(self, CTDConfig, survey):

        maxDepth = 0
        
        for de in self.depth:
            
            m = max(de)
            if m > maxDepth:
                maxDepth = m
     
        xticklabels = []
        yticklabels = []
        # Setup the grid to interpolate to
        Y = np.arange(0, maxDepth, 1)
        X = np.arange(0, len(self.julianDay), 1)

        sectionTE = np.ma.masked_all((len(X), len(Y)))
        sectionSA = np.ma.masked_all((len(X), len(Y)))
        sectionOX = np.ma.masked_all((len(X), len(Y)))
        sectionFTU = np.ma.masked_all((len(X), len(Y)))
        all_x=[]
        all_y=[]
        all_te=[]
        for d, de in enumerate(self.depth):
            sa = np.asarray(self.salinity[d].values)
            te = np.asarray(self.temperature[d].values)
            ox = np.asarray(self.oxygen[d].values)
            ftu = np.asarray(self.ftu[d].values)
          #  all_y.append(de.values)
          #  all_x.append(np.ones((len(de.values)))*self.julianDay[d])
          #  all_te.append(te)
        
            te_interp = scipy.interpolate.interp1d(de.values, te, 
                                                    fill_value=np.nan,
                                                    bounds_error=False,
                                                    kind="cubic")
          
            sa_interp = scipy.interpolate.interp1d(de.values, sa,
                                                    fill_value=np.nan,
                                                    bounds_error=False,
                                                    kind="cubic")
            
            ftu_interp = scipy.interpolate.interp1d(de.values, ftu,
                                                    fill_value=np.nan,
                                                    bounds_error=False,
                                                    kind="cubic")
            if len(ox) > len(de.values):
                ox_interp = scipy.interpolate.interp1d(de.values, ox[0:len(de)], 
                                                    fill_value=np.nan,
                                                    bounds_error=False,
                                                    kind="cubic")
            else:
                ox_interp = scipy.interpolate.interp1d(de.values[0:len(ox)], ox, 
                                                    fill_value=np.nan,
                                                    bounds_error=False,
                                                    kind="cubic")
            
            sectionTE[d, :] = te_interp(Y)
            sectionSA[d, :] = sa_interp(Y)
            sectionOX[d, :] = ox_interp(Y)
            sectionFTU[d, :] = ftu_interp(Y)
            
            dateObject = num2date(self.julianDay[d], units=CTDConfig.refdate, calendar="standard")
            X[d] = self.julianDay[d]

            xticklabels.append(str(dateObject.year) + "-" + str(dateObject.month))
       
        if (30< np.max(Y) < 50):
            depths = np.arange(0, np.max(Y), 4)
        if (0< np.max(Y) < 200):
            depths = np.arange(0, np.max(Y), 20)
        if (0< np.max(Y) < 500):
            depths = np.arange(0, np.max(Y), 50)
        if (np.max(Y) > 500):
            depths = np.arange(0, np.max(Y), 200)
            
        for yy in Y:
            yticklabels.append(str(-(np.max(Y) - yy)))
       
        plt.set_cmap('RdYlBu_r')
              
        varNames = ["temp","salt","oxy","ftu"]
        for i in range(4):
            plt.clf()
            if varNames[i] == "temp":
                vmin = 0
                vmax = 17
                Z = sectionTE
                Z=np.ma.masked_where(Z<-1.7,Z)
                
            if varNames[i] == "salt":
                vmin = 5
                vmax = 35
                Z = sectionSA
                Z=np.ma.masked_where(Z<0,Z)
                
            if varNames[i] == "ftu":
                vmin = 0
                vmax = 2
                Z = sectionFTU
                Z=np.ma.masked_where(Z>4,Z)
                
            if varNames[i] == "oxy":
                vmin = 0
                vmax = 18
                Z = sectionOX
                Z=np.ma.masked_where(sectionOX>17,Z)
                Z=np.ma.masked_where(sectionOX<0,Z)
            
            delta = (vmax - vmin) / 15
            levels = np.arange(vmin, vmax, delta)
            XX, YY = np.meshgrid(X,Y)
            
           # from scipy.interpolate import griddata
           # new_x=np.concatenate(all_x, axis=None)
           # new_y=np.concatenate(all_y, axis=None)
           # new_z=np.concatenate(all_te, axis=None)
            
           # zi = griddata((new_x,new_y),new_z,(XX, YY), method='cubic')
           
            fig, ax = plt.subplots()
            CS = ax.contourf(XX,-YY,np.fliplr(np.rot90(Z, 3)), levels, vmin=vmin, vmax=vmax, extend="both")
          #  CS2 = ax.contour(XX,-YY,np.fliplr(np.rot90(Z, 3)), levels, linewidths=0.05, colors='w')
            if float(maxDepth)>250:
                ax.set_ylim(-250,0)
                depthindex=np.where(Y==250)[0][0]
            elif 100<float(maxDepth)<190:
                ax.set_ylim(-150,0)
                depthindex=np.where(Y==150)[0][0]
            else:
                depthindex=-1
                
            if self.name in ["S16","S10","SOE72","Lind1"]:
                ax.set_ylim(-40,0)
                depthindex=np.where(Y==40)[0][0]
            if self.name in ["S22"]:
                ax.set_ylim(-25,0)
                depthindex=np.where(Y==25)[0][0]
            if self.name=="OKS1" or self.name=="OFOT1":
                ax.set_ylim(-150,0)
                depthindex=np.where(Y==150)[0][0]
            if self.name=="NORD2":
                ax.set_ylim(-225,0)
                depthindex=np.where(Y==225)[0][0]
            plt.colorbar(CS)
            xsteps=5
            if len(xticklabels)<10:
                xsteps=1
            if len(xticklabels)<20:
                xsteps=2
           
            ax.set_xlim(np.min(X),np.max(X))
            ax.set_xticks(X[::xsteps])
            ax.set_xticklabels(xticklabels[::xsteps], rotation="vertical")

            # Plot the position of the CTD stations at the deepest depths + 10 m
            new_y=np.zeros(np.shape(X))-Y[depthindex]+5
            ax.scatter(X, new_y, s=6, facecolors='none', edgecolors='k', marker='o')
       
            if maxDepth<50:
                steps=5
            elif 50<=maxDepth<250:
                steps=10
            elif 250<=maxDepth<1000:
                steps=50

            dateObjectStart, dateObjectEnd = self.getTimeRangeForStation(CTDConfig)
            if not os.path.exists('figures/{}'.format(survey)):
                os.mkdir('figures/{}'.format(survey))
            plotfileName = "figures/{}/timeseries-{}-{}-{}-to-{}.png".format(survey,
                                                                             self.name, 
                                                                             varNames[i], 
                                                                             dateObjectStart.strftime("%Y%m%d"), 
                                                                             dateObjectEnd.strftime("%Y%m%d"))

            if os.path.exists(plotfileName): os.remove(plotfileName)
            print("Saving time series to file {}".format(plotfileName))
            plt.savefig(plotfileName, dpi=300, bbox_inches='tight')
            plt.close()
            
    #  plt.show()

    def plotStationTS(self, survey):
        sa = np.asarray([item for sublist in self.salinity for item in sublist])
        te = np.asarray([item for sublist in self.temperature for item in sublist])
        de = np.asarray([item for sublist in self.depth for item in sublist])
        
        sa=np.ma.masked_where(sa<0,sa)
        te=np.ma.masked_where(te<-1.7,te)
        
        okokyst_ts_plot.createTS(sa, te, de, self.name, survey)

    def describeStation(self, CTDConfig):
        print("-------------------------------------")
        print("Station: %s" % (self.name))
        print("-------------------------------------")

        print("Depths: %s" % len(self.depth))
        print("Julian dates: %s" % len(self.julianDay))

        stDates = num2date(self.julianDay[:], units=CTDConfig.refdate, calendar="standard")

        # Need to find the start and end for May-Sept and June - Aug
     
        periods = [[5, 9], [6, 8]]
        foundStart = False
        foundEnd = False
        for period in periods:
            for d, dd in enumerate(stDates):
                if dd.month == period[0] and foundStart is False:
                    indStart = d
                    foundStart = True
                if dd.month == period[1] and foundEnd is False:
                    indEnd = d
                    foundEnd = True
            sa = np.asarray([item for sublist in self.salinity[indStart:indEnd] for item in sublist])
            te = np.asarray([item for sublist in self.temperature[indStart:indEnd] for item in sublist])
            de = np.asarray([item for sublist in self.depth[indStart:indEnd] for item in sublist])
            foundEnd = False
            foundStart = False

            sa = np.ma.masked_where(de > 10, sa)
            te = np.ma.masked_where(de > 10, te)


            print("Period: %s to %s" % (stDates[indStart], stDates[indEnd]))
            print("Mean salt:  %3.2f " % (np.ma.mean(sa)))
            print("Mean temp:  %3.2f " % (np.ma.mean(te)))

        ox = np.asarray([item for sublist in self.oxygen for item in sublist])
        ftu = np.asarray([item for sublist in self.ftu for item in sublist])
        sa = np.asarray([item for sublist in self.temperature for item in sublist])
        te = np.asarray([item for sublist in self.salinity for item in sublist])
        de = np.asarray([item for sublist in self.depth for item in sublist])

        sa = np.ma.masked_where(sa < 1, sa)
        te = np.ma.masked_where(te < 1, te)

        minimumBottomOxygen = np.min(ox)
        minimumBottomDepthIndex = np.where(ox == np.min(ox))
        if (minimumBottomDepthIndex>len(de)):
            minimumBottomDepthIndex=len(de)

        print("Minimum oxygen at bottom: %3.2f" % ( minimumBottomOxygen ))
        print("Depth at oxygen minimum : %3.2f" % ( de[minimumBottomDepthIndex] ))

        minimumTemp = np.min(te)
        minimumTempDepthIndex = np.where(te == np.min(te))

        print("Minimum temperature at bottom: %3.2f" % (minimumTemp))
        print("Depth at temperature minimum : %3.2f" % (de[minimumTempDepthIndex]))

        maximumTemp = np.max(te)
        maximumTempDepthIndex = np.where(te == np.max(te))

        print("Maximum temperature at bottom: %3.2f" % (maximumTemp))
        print("Depth at temperature maximum : %3.2f" % (de[maximumTempDepthIndex]))

        minimumSalt = np.min(sa)
        minimumSaltDepthIndex = np.where(sa == np.min(sa))

        print("Minimum salt at bottom: %3.2f" % (minimumSalt))
        print("Depth at salt minimum : %3.2f" % (de[minimumSaltDepthIndex]))

        maximumSalt = np.max(sa)
        maximumSaltDepthIndex = np.where(sa == np.max(sa))

        print("Maximum salt at bottom: %3.2f" % (maximumSalt))
        print("Depth at salt maximum : %3.2f" % (de[maximumSaltDepthIndex]))