import matplotlib
try:
    from mpl_toolkits.basemap import Basemap
except:
    pass
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from matplotlib.patches import Polygon
import os
import numpy as np
import datetime

__author__ = 'Trond Kristiansen'
__email__ = 'trond.kristiansen@niva.no'
__created__ = datetime.datetime(2017, 2, 24)
__modified__ = datetime.datetime(2019, 1, 8)
__version__ = "1.0"
__status__ = "Development"

def map_limits(m):
    llcrnrlon = min(m.boundarylons)
    urcrnrlon = max(m.boundarylons)
    llcrnrlat = min(m.boundarylats)
    urcrnrlat = max(m.boundarylats)
    return llcrnrlon, urcrnrlon, llcrnrlat, urcrnrlat


def make_map(survey, llcrnrlon=12.8, urcrnrlon=17.5, llcrnrlat=66.2, urcrnrlat=69,
             projection='merc', resolution='f', figsize=(6, 6), inset=True):
    if survey == "Soerfjorden":
        mmap = Basemap(llcrnrlon=6.4, urcrnrlon=6.85, llcrnrlat=60, urcrnrlat=60.2, projection=projection,
                       resolution=resolution)
        meridians = np.arange(6.3, 6.7, 0.1)
        parallels = np.arange(60.1, 60.5, 0.1)
    elif survey == "Hardangerfjorden":
        mmap = Basemap(llcrnrlon=5.0, urcrnrlon=6.2, llcrnrlat=60.5, urcrnrlat=61.5, projection=projection,
                       resolution=resolution)
        meridians = np.arange(5.0, 6.7, 0.1)
        parallels = np.arange(60.1, 61.5, 0.1)
    elif survey == "Sognefjorden":
        mmap = Basemap(llcrnrlon=6.0, urcrnrlon=6.85, llcrnrlat=59.7, urcrnrlat=60.2, projection=projection,
                       resolution=resolution)
        meridians = np.arange(6.0, 6.7, 0.1)
        parallels = np.arange(60.1, 60.5, 0.1)
    else:
        mmap = Basemap(llcrnrlon=llcrnrlon, urcrnrlon=urcrnrlon,
                       llcrnrlat=llcrnrlat, urcrnrlat=urcrnrlat,
                       projection=projection, resolution=resolution)
        meridians = np.arange(llcrnrlon, urcrnrlon + 0.5, 0.5)
        parallels = np.arange(llcrnrlat, urcrnrlat + 0.5, 0.5)

    fig, ax = plt.subplots(figsize=figsize)
    mmap.drawstates()
    mmap.drawcoastlines()
    mmap.fillcontinents(color='0.85')

    mmap.drawparallels(parallels, linewidth=0, labels=[1, 0, 0, 0],fontsize=9)
    mmap.drawmeridians(meridians, linewidth=0, labels=[0, 0, 0, 1],fontsize=9, rotation=45)
    mmap.ax = ax

    if inset:
        axins = inset_axes(mmap.ax, width="40%", height="40%", loc=4)
      #  axins.set_xlim(-40, 60) # longitude boundaries of inset map
      #  axins.set_ylim(30, 85) #
        
        # Global inset map.
        if survey == "Soerfjorden":
            inmap = Basemap(llcrnrlon=4.0, urcrnrlon=8, llcrnrlat=59, urcrnrlat=62, projection=projection,
                           resolution=resolution, ax=axins, anchor='NE')
        elif survey == "MON":
            inmap = Basemap(llcrnrlon=4, urcrnrlon=30,
                       llcrnrlat=60, urcrnrlat=72,
                       projection=projection, ax=axins, resolution='i')
        else:
            inmap = Basemap(lon_0=np.mean(mmap.boundarylons),
                        lat_0=np.mean(mmap.boundarylats),
                        projection='ortho', ax=axins, anchor='NE')
      
        inmap.drawcountries(color='white')
        inmap.fillcontinents(color='gray')
        bx, by = inmap(mmap.boundarylons, mmap.boundarylats)
        xy = list(zip(bx, by))
        mapboundary = Polygon(xy, edgecolor='r', linewidth=1, fill=False)
        inmap.ax.add_patch(mapboundary)
    return fig, mmap


def createMap(stationsList):
    lons = []
    lats = []
    names = []
    for station in stationsList:
        lons.append(station.longitude)
        lats.append(station.latitude)
        names.append(station.name)

    print("=> Creating station map")
    # Stations map.
    if not os.path.exists('figures/{}'.format(stationsList[0].survey)):
        os.mkdir('figures/{}'.format(stationsList[0].survey))
    fig, mmap = make_map(stationsList[0].survey, figsize=(6, 6))
    mmap.plot(lons, lats, marker='o', markersize=10, edgecolor='k', c='r', lw=0.1, linestyle="None", latlon=True)

    x, y = mmap(lons, lats)
    for i in range(len(names)):
        print("Adding name for station {}".format(names[i]))
        bbox_props = dict(boxstyle="round,pad=0.1", fc="w", ec="r", lw=1)
        mmap.ax.annotate(names[i], xy=(x[i], y[i]), va="top", fontsize=8, bbox=bbox_props)

    plotfileName = "figures/{}/{}-stations.png".format(stationsList[0].survey,stationsList[0].survey)

    if os.path.exists(plotfileName): os.remove(plotfileName)
    plt.savefig(plotfileName, dpi=300)
    print('=> Saved station map to file: %s\n' % (plotfileName))

