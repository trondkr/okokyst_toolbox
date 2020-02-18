import os, sys
import datetime

from .station_data import StationData
from .station_excel import StationExcel
from .station_io import StationIO
from .station_plot import StationPlot

__author__ = 'Trond Kristiansen'
__email__ = 'trond.kristiansen@niva.no'
__created__ = datetime.datetime(2017, 2, 24)
__modified__ = datetime.datetime(2019, 1, 13)
__version__ = "1.0"
__status__ = "Development"


class Station(StationData, StationExcel, StationIO, StationPlot):

    def __init__(self, name, survey, projectname):
        self.name = name
        self.survey = survey
        self.projectname = projectname
        self.header = None
        self.mainHeader = None
        self.stationid = None
        self.salinity = []
        self.temperature = []
        self.oxygen = []
        self.oxsat = []
        self.ftu = []
        self.julianDay = []
        self.depth = []
        self.X = []
        self.Y = []
