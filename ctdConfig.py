class CTDConfig(object):

    def __init__(self, createStationPlot, 
                 createTSPlot,
                 createContourPlot, 
                 createTimeseriesPlot, 
                 binDataWriteToNetCDF, 
                 describeStation,
                 createHistoricalTimeseries,
                 showStats, 
                 plotStationMap, 
                 tempName, 
                 saltName,
                 oxName, 
                 ftuName, 
                 oxsatName, 
                 refdate, 
                 selected_depths,
                 write_to_excel, 
                 survey=None, 
                 conductivity_to_salinity=False,
                 calculate_depth_from_pressure=False,
                 debug=False):
        
        self.createStationPlot = createStationPlot
        self.createTSPlot = createTSPlot
        self.createContourPlot = createContourPlot
        self.createTimeseriesPlot = createTimeseriesPlot
        self.binDataWriteToNetCDF = binDataWriteToNetCDF
        self.describeStation = describeStation
        self.showStats = showStats
        self.plotStationMap = plotStationMap
        self.useDowncast = None
        self.tempName = tempName
        self.saltName = saltName
        self.oxName = oxName
        self.ftuName = ftuName
        self.oxsatName = oxsatName
        self.refdate = refdate
        self.calculate_depth_from_pressure = calculate_depth_from_pressure
        self.conductivity_to_salinity = conductivity_to_salinity
        self.debug=debug
        self.survey=survey
        self.write_to_excel=write_to_excel
        self.projectname=None
        self.selected_depths=selected_depths
        self.mgperliter_to_mlperliter=0.7
        self.createHistoricalTimeseries=createHistoricalTimeseries
