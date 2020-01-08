
from numpy import sin, pi
import os

# Local files
import stationClass
import ctdConfig as CTDConfig
import okokyst_metadata

__author__ = 'Trond Kristiansen'
__email__ = 'trond.kristiansen@niva.no'
__created__ = datetime(2017, 2, 24)
__modified__ = datetime(2019, 1, 8)
__version__ = "1.0"
__status__ = "Development"

def createNewFile(filename, station, CTDConfig):
    infile = open(filename, 'r')
    lines = infile.readlines()
    l = lines[0].split(";")
    options = None

    if l[2] == "Cond." and len(l)==13:
        CTDConfig.conductivity_to_salinity = True
        CTDConfig.conductivityMissing = False

    elif l[2] == "Sal." and 'Cond.' not in l:
        CTDConfig.conductivity_to_salinity=False
        CTDConfig.conductivityMissing = True

    elif l[2] == "Sal." and 'Cond.' in l:
        CTDConfig.conductivity_to_salinity=False
        CTDConfig.conductivityMissing = False

    if ('S. vel.' in l and 'Cond.' in l):
        CTDConfig.conductivityMissing = False
        CTDConfig.conductivity_to_salinity = False
        l[-4] = l[-3]
        l[-3] = l[-2]
        l[-2] = l[-1]
        options = ['S. vel.']
        
    if l[8] == "Press":
        CTDConfig.calculate_depth_from_pressure=True

    okokyst_metadata.addStationMeadata(station, CTDConfig, options)

    # Create a new file by adding a header to the existing CTD file.
    newfilename = filename[0:-4] + "_edited.txt"

    if os.path.exists(newfilename):
        os.remove(newfilename)
    print("=> Creating new output file: %s" % newfilename)
    outfile = open(newfilename, 'a')

    outfile.writelines(station.header + station.mainHeader)

    counter = 0
    for line in lines[1:]:
        l = line.split(";")
        #  Calculate salinity from conductivty and replace with conductivity in data array
        if CTDConfig.conductivity_to_salinity and counter > 0:
            C = float(l[2])
            T = float(l[3])
            P = float(l[8])
            salinity = gsw.SP_from_C(C, T, P)
            l[2] = salinity
            
        # If only pressure is given, convert to depth in meters
        if CTDConfig.calculate_depth_from_pressure:
            P = float(l[8])
            l[8]=okokyst_tools.pressure_to_depth(P,station.latitude)
           
        line = ';'.join(map(str, l))
    
        if counter > 0:
            outfile.writelines(line)
        counter += 1

    outfile.close()
    infile.close()
    return newfilename

def pressure_to_depth(P, lat):
    """Compute depth from pressure and latitude
    Usage: depth(P, lat)
    Input:
        P = Pressure,     [dbar]
        lat = Latitude    [deg]
    Output:
        Depth             [m]
    Algorithm: UNESCO 1983
    """
    a1 =  9.72659
    a2 = -2.2512e-5
    a3 =  2.279e-10
    a4 = -1.82e-15

    b  =  1.092e-6

    g0 =  9.780318
    g1 =  5.2788e-3
    g2 =  2.36e-5

    rad = pi / 180.

    X = sin(lat*rad)
    X = X*X
    grav = g0 * (1.0 + (g1 + g2*X)*X) + b*P
    nom = (a1 + (a2 + (a3 + a4*P)*P)*P)*P

    return nom / grav

# After identifying correct folder, find the txt file
def locateFile(basepath, subStation):
    filename = "%s/%s.txt" % (basepath, subStation)
    if os.path.isfile(filename):
        return filename

def findMaximumWindow(cast, tempName):

    maxDepth = np.max(cast[tempName].index.values)
    window = 1

    if maxDepth > 400:
        window = 21
    if 400 > maxDepth > 100:
        window = 11
    if 50 > maxDepth > 0:
        window = 5

    return 1 #window #window