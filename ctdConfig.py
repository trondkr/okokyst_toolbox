class CTDConfig(object):

    def __init__(self, createStationPlot, createTSPlot,createContourPlot, binDataWriteToNetCDF, showStats, plotStationMap, useDowncast, tempName, saltName,
                 oxName, ftuName, oxsatName, refdate, year, conductivity_to_salinity=False,calculate_depth_from_pressure=False):
        self.createStationPlot = createStationPlot
        self.createTSPlot = createTSPlot
        self.createContourPlot = createContourPlot
        self.binDataWriteToNetCDF = binDataWriteToNetCDF
        self.showStats = showStats
        self.plotStationMap = plotStationMap
        self.useDowncast = useDowncast
        self.tempName = tempName
        self.saltName = saltName
        self.oxName = oxName
        self.ftuName = ftuName
        self.oxsatName = oxsatName
        self.refdate = refdate
        self.year = year
        self.calculate_depth_from_pressure = calculate_depth_from_pressure
        self.conductivity_to_salinity = conductivity_to_salinity
