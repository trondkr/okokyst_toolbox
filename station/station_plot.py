import datetime
import locale
import os
import matplotlib
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from netCDF4 import num2date

__author__ = 'Trond Kristiansen'
__email__ = 'trond.kristiansen@niva.no'
__created__ = datetime.datetime(2017, 2, 24)
__modified__ = datetime.datetime(2019, 1, 21)
__version__ = "1.0"
__status__ = "Development"

matplotlib.rcParams.update({'font.size': 14})


class FormatScalarFormatter(matplotlib.ticker.ScalarFormatter):
    def __init__(self, fformat="%1.1f", offset=True, mathText=True):
        self.fformat = fformat
        matplotlib.ticker.ScalarFormatter.__init__(self, useOffset=offset,
                                                   useMathText=mathText)

    def _set_format(self):
        self.format = self.fformat
        if self._useMathText:
            self.format = '$%s$' % matplotlib.ticker._mathdefault(self.format)


class StationPlot:
    # Used for contour plots
    def define_variable_specifics(self, varname):
        return {"temp": {"vmin": 4, "vmax": 17, "title": "{}: Temperatur ($^o$C)".format(self.name)},
                "salt": {"vmin": 10, "vmax": 35, "title": "{}: Saltholdighet".format(self.name)},
                "ox": {"vmin": 0, "vmax": 12, "title": "{}: Oksygenkons.(mlO$_2$/L)".format(self.name)},
                "oxsat": {"vmin": 0, "vmax": 120, "title": "{}: Oksygenmetning ($\%$)".format(self.name)},
                "ftu": {"vmin": 0, "vmax": 5, "title": "{}: Fluorescence".format(self.name)}}[varname]

    # Used for variability over time at fixed depths
    def define_variable_specifics_3m(self, varname):
        return {"temp": {"vmin": 2, "vmax": 19, "ylabel": "Temperatur ($^o$C)", "title": "{}".format(self.name)},
                "salt": {"vmin": 25, "vmax": 35.5, "ylabel": "Saltholdighet", "title": "{}".format(self.name)},
                "ox": {"vmin": 2, "vmax": 12, "ylabel": "Oksygenkons.(mlO$_2$/L)", "title": "{}".format(self.name)},
                "oxsat": {"vmin": 0, "vmax": 120, "ylabel": "Oksygenmetning ($\%$)", "title": "{}".format(self.name)},
                "ftu": {"vmin": 0, "vmax": 5, "ylabel": "Fluorescence", "title": "{}".format(self.name)}}[varname]

    # Used for variability over time at fixed depths  
    def define_variable_specifics_100_200m(self, varname):
        return {"temp": {"vmin": 5, "vmax": 12, "ylabel": "Temperatur ($^o$C)", "title": "{}".format(self.name)},
                "salt": {"vmin": 33, "vmax": 35.5, "ylabel": "Saltholdighet", "title": "{}".format(self.name)},
                "ox": {"vmin": 2, "vmax": 8, "ylabel": "Oksygenkons.(mlO$_2$/L)", "title": "{}".format(self.name)},
                "oxsat": {"vmin": 0, "vmax": 120, "ylabel": "Oksygenmetning ($\%$)", "title": "{}".format(self.name)},
                "ftu": {"vmin": 0, "vmax": 5, "ylabel": "Fluorescence", "title": "{}".format(self.name)}}[varname]

    def define_array_for_variable(self, varname):
        return {"temp": self.sectionTE,
                "salt": self.sectionSA,
                "ox": self.sectionOX,
                "ftu": self.sectionFTU,
                "oxsat": self.sectionOXS}[varname]

    # Save figures to file depending on what sort of plot (plot_type)   
    def save_to_file(self, CTDConfig, var_name, plot_type, work_dir, selected_depth=None, dateObjectStart=None,
                     dateObjectEnd=None):
        figures_path = os.path.join(work_dir,'figures', CTDConfig.survey)
        if not os.path.isdir(figures_path):
            os.makedirs(figures_path)

        if plot_type == "timeseries":

            start = dateObjectStart.strftime("%Y%m%d")
            stop = dateObjectEnd.strftime("%Y%m%d")
            filename = f"timeseries-{self.name}-{var_name}-{start}-to-{stop}.png"


        else:
            filename = f"{plot_type}-{self.name}-{var_name}-{selected_depth}.png"

        plotfileName = os.path.join(figures_path, filename)


        if os.path.exists(plotfileName): os.remove(plotfileName)
        print("Saving time series to file {}".format(plotfileName))
        plt.savefig(plotfileName, dpi=300, bbox_inches='tight')
        plt.close()

    def get_depthindex(self, Y, max_depth, ax, varname):
        if float(max_depth) > 250:
            ax.set_ylim(-250, 0)
            depthindex = np.where(Y == 250)[0][0]
        elif 100 < float(max_depth) < 190:
            ax.set_ylim(-150, 0)
            depthindex = np.where(Y == 150)[0][0]
        else:
            depthindex = -1

        if self.name in ["S16", "S10", "SOE72", "Lind1"]:
            ax.set_ylim(-40, 0)
            depthindex = np.where(Y == 40)[0][0]
        if self.name in ["S22"]:
            ax.set_ylim(-25, 0)
            depthindex = np.where(Y == 25)[0][0]
        if self.name == "OKS1" or self.name == "OFOT1":
            ax.set_ylim(-150, 0)
            depthindex = np.where(Y == 150)[0][0]
        if self.name == "NORD2":
            ax.set_ylim(-225, 0)
            depthindex = np.where(Y == 225)[0][0]
        if self.name in ["VT79"]:
            ax.set_ylim(-500, 0)
            depthindex = np.where(Y == 450)[0][0]
        if self.name in ["VT69"]:
            ax.set_ylim(-20, 0)
            depthindex = np.where(Y == 20)[0][0]
        if self.name in ["VT70"]:
            ax.set_ylim(-590, 0)
            depthindex = np.where(Y == 590)[0][0]
        if self.name in ["VT75"]:
            ax.set_ylim(-180, 0)
            depthindex = np.where(Y == 180)[0][0]
        if self.name in ["VT52"]:
            ax.set_ylim(-370, 0)
            depthindex = np.where(Y == 370)[0][0]
        if self.name in ["VT74"]:
            ax.set_ylim(-230, 0)
            depthindex = np.where(Y == 230)[0][0]
        if self.name in ["VT53"]:
            ax.set_ylim(-850, 0)
            depthindex = np.where(Y == 850)[0][0]
        if self.name in ["VT16"] and varname in ["oxsat", "ox"]:
            ax.set_ylim(-1250, 0)
            depthindex = np.where(Y == 1250)[0][0]
        if self.name in ["VT16"] and varname in ["temp", "salt"]:
            ax.set_ylim(-300, 0)
            depthindex = np.where(Y == 300)[0][0]
        if varname in ["ftu"]:
            print("ylim", ax.get_ylim())
            if ax.get_ylim()[0] < -100:
                ax.set_ylim(-100, 0)
                depthindex = np.where(Y == 100)[0][0]
        return depthindex

    def createHistoricalTimeseries(self, CTDConfig):
        dates = [num2date(jd, units=CTDConfig.refdate, calendar="standard") for jd in self.julianDay]

        # Either we plot all the years or a selection (e.g. years=[2017,2018])
        startdate = dates[0]
        enddate = dates[-1]
        steps = (enddate.year - startdate.year) + 1
        years = [int(startdate.year) + i for i in range(steps)]
        n_months = 12
        smooth = False
        print("Using smoothing for timeseries: {}".format(smooth))
        CTDConfig.selected_depths = [200]
        for var_name in ["temp", "salt"]:  # ,"salt","ox"]:
            fig, ax = plt.subplots(nrows=1)
            colormap = plt.cm.plasma
            colors = [colormap(i) for i in np.linspace(0, 0.9, len(years))]

            for sub_index, selected_depth in enumerate(CTDConfig.selected_depths):
                # Size of data is number of years for data storage
                all_data = np.empty((len(years), n_months))
                Z = self.define_array_for_variable(var_name)

                depthindex = np.where(self.Y == selected_depth)[0][0]
                all_dates = np.zeros((len(years), 12))

                # Extract only data for each individual year and save by month
                for ind, d in enumerate(dates):
                    year_index = years.index(d.year)
                    all_data[year_index, int(d.month - 1)] = Z[ind, depthindex]
                    all_dates[year_index, d.month - 1] = self.julianDay[ind]
                # Mask the data to remove months where observations may not exist
                all_data = np.ma.masked_where(all_data < 0.1, all_data)
                if var_name in ["salt"]:
                    all_data = np.ma.masked_where(all_data < 28, all_data)
                if var_name in ["salt", "temp"]:
                    all_data = np.ma.masked_where(all_data > 50, all_data)
                all_data = np.ma.masked_invalid(all_data)
                legendlist = []

                # Create the smoothed series of data and plot
                for ind in range(len(years)):
                    changed_dates = []
                    legendlist.append("{}".format(years[ind]))
                    alld = num2date(all_dates[ind, :], units=CTDConfig.refdate, calendar="standard")
                    # Mock the year in dates so all plots from different years can be using the same
                    # x-axis and be overlaid on top of eachother
                    for d in alld:
                        changed_dates.append(datetime.datetime(years[0], d.month, d.day, d.hour))

                    # Smooth the data by creating a pandas Series object which is resampled at high frequency
                    ser = pd.Series(all_data[ind, :], index=pd.to_datetime(changed_dates))
                    ser = ser.dropna()
                    if smooth:
                        smoothed = ser.resample("60T").apply(['median'])
                        tsint = smoothed.interpolate(method='cubic')

                    # Get the vmin and vmax limits for the specific plot
                    if selected_depth < 10:
                        specs = self.define_variable_specifics_3m(var_name)
                    else:
                        specs = self.define_variable_specifics_100_200m(var_name)
                    # ser=ser.mask(ser>36)

                    ax.set_ylim(float(specs["vmin"]), float(specs["vmax"]))
                    if not smooth:
                        ax = ser.loc['2013-01-01':'2030-01-01'].plot(color=colors[ind], lw=2.2, ax=ax,
                                                                     label=str(years[ind]))
                    # SMOOTHED version uncomment next line
                    if smooth:
                        ax = tsint.loc['2013-01-01':'2020-01-01'].plot(color=colors[ind], ax=ax, lw=2.2,
                                                                       label=str(years[ind]), x_compat=True)
                    # SHOW DOTS FOR original positions uncomment next line
                    #   ax[ind] = ser.loc['2017-01-01':'2030-01-01'].plot(style="o",ms=5,ax=ax) #,label=str(years[ind]))
                    ax.xaxis.set_tick_params(reset=True)
                    ax.xaxis.set_major_locator(mdates.MonthLocator())
                    ax.xaxis.set_major_formatter(mdates.DateFormatter(''))

            # Make sure the month names are in Norwegian
            locale.setlocale(locale.LC_ALL, "no_NO")
            leg = ax.legend(legendlist, loc=1, prop={'size': 10})
            for j, selected_depth in enumerate(CTDConfig.selected_depths):
                label = " {}m".format(selected_depth)
                ax.text(0.1, 0.1,
                        label,
                        size=12,
                        horizontalalignment='right',
                        verticalalignment='bottom',
                        transform=ax.transAxes)

            ax.xaxis.set_tick_params(reset=True)
            ax.xaxis.set_major_locator(mdates.MonthLocator())
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
            ax.set_xlabel("Dato")
            ax.set_ylabel(specs["ylabel"], multialignment='center')
            ax.set_title(specs["title"])

            plt.tight_layout()
            if not smooth:
                self.save_to_file(CTDConfig, var_name, 'annual_variability_historical',
                                  selected_depth=str(selected_depth))
            else:
                self.save_to_file(CTDConfig, var_name, 'annual_variability_historical_smoothed',
                                  selected_depth=str(selected_depth))
            plt.clf()

    def createTimeseriesPlot(self, CTDConfig, work_dir):

        dates = [num2date(jd, units=CTDConfig.refdate, calendar="standard") for jd in self.julianDay]
        if len(dates)> 0:
            # Either we plot all the years or a selection (e.g. years=[2017,2018])
            startdate = dates[0]
            enddate = dates[-1]
            steps = (enddate.year - startdate.year) + 1
            years = [int(startdate.year) + i for i in range(steps)]
            n_months = 12

            if self.get_max_depth() < 100:
                CTDConfig.selected_depths = [3]
            elif self.get_max_depth() < 200:
                CTDConfig.selected_depths = [3, 100]
            elif self.get_max_depth() < 300:
                CTDConfig.selected_depths = [3, 100, 200]
            for var_name in ["temp"]:  # ,"salt","ox"]:
                fig, ax = plt.subplots(nrows=3)
                if self.name in ["VT75"]:
                    fig, ax = plt.subplots(nrows=2)
                colormap = plt.cm.plasma
                colors = [colormap(i) for i in np.linspace(0, 0.9, len(years))]
                legendlist = []

                # Loop over all depths to be plotted as individual figures
                for sub_index, selected_depth in enumerate(CTDConfig.selected_depths):
                    # Size of data is number of years for data storage
                    all_data = np.empty((len(years), n_months))
                    Z = self.define_array_for_variable(var_name)

                    depthindex = np.where(self.Y == selected_depth)[0][0]
                    all_dates = np.zeros((len(years), 12))

                    # Extract only data for each individual year and save by month
                    for ind, d in enumerate(dates):
                        year_index = years.index(d.year)
                        all_data[year_index, int(d.month - 1)] = Z[ind, depthindex]
                        all_dates[year_index, d.month - 1] = self.julianDay[ind]
                    # Mask the data to remove months where observations may not exist
                    all_data = np.ma.masked_where(all_data < 0.1, all_data)
                    all_data = np.ma.masked_where(all_data > 150, all_data)

                    # Create the smoothed series of data and plot
                    for ind in range(len(years)):
                        changed_dates = []
                        legendlist.append("{}".format(years[ind]))
                        alld = num2date(all_dates[ind, :], units=CTDConfig.refdate, calendar="standard")
                        # Mock the year in dates so all plots from different years can be using the same
                        # x-axis and be overlaid on top of eachother
                        for d in alld:
                            changed_dates.append(datetime.datetime(years[0], d.month, d.day, d.hour))

                        # Smooth the data by creating a pandas Series object which is resampled at high frequency
                        ser = pd.Series(all_data[ind, :], index=pd.to_datetime(changed_dates))
                        #   smoothed = ser.resample("60T").apply(['median'])
                        #   tsint = smoothed.interpolate(method='cubic')

                        # Get the vmin and vmax limits for the specific plot
                        if selected_depth < 10:
                            specs = self.define_variable_specifics_3m(var_name)
                        else:
                            specs = self.define_variable_specifics_100_200m(var_name)
                        # ser=ser.mask(ser>36)

                        ax[sub_index].set_ylim(float(specs["vmin"]), float(specs["vmax"]))
                        ax[sub_index] = ser.loc['2013-01-01':'2030-01-01'].plot(color=colors[ind], lw=1.5, ax=ax[sub_index],
                                                                                label=str(years[ind]))
                        # SMOOTHED version uncomment next line
                        #  ax[ind] = tsint.loc['2017-01-01':'2030-01-01'].plot(color=colors[ind],ax=ax,lw=2,label=str(years[ind]),x_compat=True)
                        # SHOW DOTS FOR original positions uncomment next line
                        #   ax[ind] = ser.loc['2017-01-01':'2030-01-01'].plot(style="o",ms=5,ax=ax) #,label=str(years[ind]))
                        ax[sub_index].xaxis.set_tick_params(reset=True)
                        ax[sub_index].xaxis.set_major_locator(mdates.MonthLocator())
                        ax[sub_index].xaxis.set_major_formatter(mdates.DateFormatter(''))

                # Make sure the month names are in Norwegian
                locale.setlocale(locale.LC_ALL, "no_NO")

                if self.name in ["VT75"]:
                    leg = ax[1].legend(legendlist, loc=1, prop={'size': 10})
                else:
                    leg = ax[2].legend(legendlist, loc=1, prop={'size': 10})
                for j, selected_depth in enumerate(CTDConfig.selected_depths):
                    label = " {}m".format(selected_depth)
                    if self.name in ["VT75"]:
                        yy=1.15
                    else:
                        yy=1.5
                    ax[j].text(0.1, yy,
                               label,
                               size=12,
                               horizontalalignment='right',
                               verticalalignment='top',
                               transform=ax[j].transAxes)

                if self.name in ["VT75"]:
                    ax[1].xaxis.set_tick_params(reset=True)
                    ax[1].xaxis.set_major_locator(mdates.MonthLocator())
                    ax[1].xaxis.set_major_formatter(mdates.DateFormatter('%b'))
                    ax[1].set_xlabel("Dato")
                else:
                    ax[2].xaxis.set_tick_params(reset=True)
                    ax[2].xaxis.set_major_locator(mdates.MonthLocator())
                    ax[2].xaxis.set_major_formatter(mdates.DateFormatter('%b'))
                    ax[2].set_xlabel("Dato")
                ax[1].set_ylabel(specs["ylabel"], multialignment='center')
                if self.survey not in ['Soerfjorden']:
                    ax[0].set_title(specs["title"])

                plt.tight_layout()
                self.save_to_file(CTDConfig, var_name, 'annual_variability', work_dir, selected_depth=str(selected_depth))
        else:
            print('Empty dates', CTDConfig)


    def createContourPlots(self, CTDConfig):
        xticklabels = []
        yticklabels = []
        for d, dd in enumerate(self.julianDay):
            dateObject = num2date(self.julianDay[d], units=CTDConfig.refdate, calendar="standard")
            self.X[d] = self.julianDay[d]
            xticklabels.append(str(dateObject.year) + "-" + str(dateObject.month))

        for yy in self.Y: yticklabels.append(str(-(np.max(self.Y) - yy)))
        plt.set_cmap('RdYlBu_r')

        varNames = ["temp", "salt", "ox", "ftu", "oxsat"]
        if self.name in ['SJON1', 'SJON2']:
            varNames = ["temp", "salt", "ox", "oxsat"]
        for i in range(len(varNames)):
            plt.clf()
            fig, ax = plt.subplots()

            # Get data and settings for station
            specs = self.define_variable_specifics(varNames[i])
            Z = self.define_array_for_variable(varNames[i])
            Z = np.ma.masked_where(Z < 0, Z)
            if varNames[i] == "ftu":
                Z = np.ma.masked_where(Z > 20, Z)
            delta = (specs["vmax"] - specs["vmin"]) / 15
            levels = np.arange(specs["vmin"], specs["vmax"], delta)
            XX, YY = np.meshgrid(self.X, self.Y)

            CS = ax.contourf(XX, -YY, np.fliplr(np.rot90(Z, 3)), levels, vmin=specs["vmin"], vmax=specs["vmax"],
                             extend="both")
            #  CS2 = ax.contour(XX,-YY,np.fliplr(np.rot90(Z, 3)), levels, linewidths=0.05, colors='w')
            max_depth = self.get_max_depth()
            depthindex = self.get_depthindex(self.Y, max_depth, ax, varNames[i])

            fmt = FormatScalarFormatter("%.1f")
            plt.colorbar(CS, format=fmt)
            xsteps = 5
            if len(xticklabels) < 10:
                xsteps = 1
            if len(xticklabels) < 20:
                xsteps = 2

            ax.set_xlim(np.min(self.X), np.max(self.X))
            ax.set_xticks(self.X[::xsteps])
            ax.set_xticklabels(xticklabels[::xsteps], rotation="vertical")

            # Plot the position of the CTD stations at the deepest depths + 10 m
            new_y = np.zeros(np.shape(self.X)) - self.Y[depthindex] + 5
            ax.scatter(self.X, new_y, s=6, facecolors='none', edgecolors='k', marker='o')

            if CTDConfig.survey not in ['Soerfjorden']:
                ax.set_title(specs["title"])
                ax.set_ylabel("Dyp (m)")
                ax.set_xlabel("Dato")

            dateObjectStart, dateObjectEnd = self.getTimeRangeForStation(CTDConfig)
            self.save_to_file(CTDConfig,
                              varNames[i],
                              'timeseries',
                              selected_depth='alldepths',
                              dateObjectStart=dateObjectStart,
                              dateObjectEnd=dateObjectEnd)

    def plotStationTS(self, survey):
        sa = np.asarray([item for sublist in self.salinity for item in sublist])
        te = np.asarray([item for sublist in self.temperature for item in sublist])
        de = np.asarray([item for sublist in self.depth for item in sublist])

        sa = np.ma.masked_where(sa < 0, sa)
        te = np.ma.masked_where(te < -1.7, te)

        self.createTS(sa, te, de, self.name, survey)
