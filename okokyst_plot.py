import matplotlib
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

def plotStation(station, dateObject):
    # Plotting
    kw_temp = dict(linestyle='-', color='#6699cc', linewidth=4, label=r"Temperature [$^\circ$C]")
    kw_salt = dict(linestyle='-', color='#ffcc33', alpha=0.8, linewidth=4, label=r"Salinity [psu]")
    kw_oxy = dict(linestyle='-', color='#339933', alpha=0.9, linewidth=4, label=r"Oxygen [mg/L]")
    kw_ftu = dict(linestyle='-', color='#669933', alpha=0.9, linewidth=4, label=r"FTU")
    
    fig, ax = plt.subplots() #station.temperature.plot(**kw_temp)
   # ax.plot(station.temperature, station.depth, **kw_oxy)
    ax.plot(station.oxygen, station.depth, **kw_oxy)
    ax.grid(True)

    ax2 = ax.twiny()
    ax2.plot(station.salinity, station.depth, **kw_salt)
    ax.set_xlabel("Temp[$^\circ$C] & Oxygen [$mg/L$]")
    ax2.set_xlabel("Salinity [psu]")
    ax.set_ylabel("Depth [m]")
    ax.legend(loc="lower left", prop={'size': 6})
    ax2.legend(loc="lower right", prop={'size': 6})

    figurepath = "figures/%s" % (station.survey)
    if not os.path.exists(figurepath):
        os.makedirs(figurepath)

    plotfileName = "%s/CTD_%s_%s.png" % (figurepath, station.name, dateObject)
    if os.path.exists(plotfileName): os.remove(plotfileName)
    plt.savefig(plotfileName, dpi=300)