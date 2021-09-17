# coding=utf-8
import numpy as np
import matplotlib.pyplot as plt
import seawater as sw
import cmocean
import datetime
from netCDF4 import Dataset
import matplotlib.cm as cm
import calendar
import os, string
import numpy as np

__author__ = 'Trond Kristiansen'
__email__ = 'trond.kristiansen@niva.no'
__created__ = datetime.datetime(2017, 2, 24)
__modified__ = datetime.datetime(2019, 1, 8)
__version__ = "1.0"
__status__ = "Development"

def help():
    """ This script creates a TS plot of temperature and salinity data. Colored with
    depth location. Also, draws density lines in the background. Requires the CSIRO
    seawater python package """


def createTS(salt, temp, depth, stationName, survey):
    fig = plt.figure()
    smin, smax, tmin, tmax = salt.min() - 0.2, salt.max() + 0.2, temp.min() - 0.2, temp.max() + 0.2
    #smin, smax, tmin, tmax = 29.5, 37, 5, 10
    """ Fake temperature and salinity for density contours in out T-S """
    T = np.linspace(tmin, tmax, 15)
    S = np.linspace(smin, smax, 15)
    print("Salinity range: %s to %s" % (smin, smax))
    print("Temperature range: %s to %s" % (tmin, tmax))
    print("Observations Salinity range: %s to %s" % (np.min(salt), np.max(salt)))
    print("Observations Temperature range: %s to %s" % (np.min(temp), np.max(temp)))

    """ Potential density"""
    Sg, Tg = np.meshgrid(S, T)
    sigma_theta = sw.eos80.pden(Sg, Tg, 0, pr=0) - 1000
    dmin, dmax = sigma_theta.min(), sigma_theta.max()
    d = np.linspace(dmin, dmax, 10)

    ax = fig.add_subplot(111)
    cntr = ax.contour(S, T, sigma_theta, d, colors='k')  # density contours
    clbl = ax.clabel(cntr, fmt=r"%2.1f kg m$^{-3}$", fontsize=12, use_clabeltext=True, inline=1)

    """ Theta-S """
    CS = ax.scatter(salt, temp, marker='o', c=depth, s=50, edgecolor='None', linewidth=0.2,
                    cmap='RdYlBu', zorder=10)
    plt.colorbar(CS)

   # if (smin!=np.nan and smax!=np.nan):
   #     ax.set_xlim(smin, smax)

    ax.set_title(r"$\theta$-S - %s" % (stationName))
    if not os.path.exists('figures/{}'.format(survey)):
        os.mkdir('figures/{}'.format(survey))
    plotfile = 'figures/{}/TS_{}.png'.format(survey,stationName)
    plt.savefig(plotfile, dpi=300, bbox_inches='tight')
    print("Saving to file: %s" % (plotfile))
    #plt.show()

def test():
    choice = "Leon"  # "Bjarte"
    # choice="Bjarte"

    if choice == "Leon":
        infile = "/Users/trondkr/Dropbox/NIVA/OKOKYST_2017/OKOKYST_NS_Nord_Leon/t01_saiv_leon/SAIV_208_SN1380.txt"
        separator = "\t"
        headers = 7
    if choice == "Bjarte":
        infile = "/Users/trondkr/Dropbox/NIVA/OKOKYST_2017/OKOKYST_NS_Nord_Kvitsoy/t01_saiv_kvitsøy/2017-02-20 CTD data/2017-02-20 hardanger_salt.txt"
        separator = ";"
        headers = 8

    filetype = "txt"

    myfile = open(infile, 'r')

    if not os.path.exists('figures'):
        os.makedirs('figures')

    if filetype == "avg":
        timeR = np.asarray(myCDF.variables["ocean_time"][:])
        refDateR = datetime.datetime(1948, 1, 1, 0, 0, 0)

    if filetype == "txt":
        lines = myfile.readlines()
        counter = 0;
        temp = [];
        salt = [];
        depth = []

        for line in lines:
            if counter < headers:
                test = "ss"
            else:
                l = string.split(line, separator)
                temp.append(float(l[3]))
                salt.append(float(l[2]))
                depth.append(float(l[7]))
            counter += 1

        myfile.close()
        salt = np.asarray(salt)
        temp = np.asarray(temp)
        depth = np.asarray(depth)
        current = "februar 2017"

        createTS(salt, temp, depth, current)

    myfile.close()



if __name__ == "__main__":
    test()
