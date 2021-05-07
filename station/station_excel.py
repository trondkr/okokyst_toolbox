import os
import datetime
from pathlib import Path
from netCDF4 import date2num, num2date
import progressbar
import pandas as pd
import cftime
import xlsxwriter
import numpy as np

# Local files
import ctdConfig as CTDConfig

__author__ = 'Trond Kristiansen'
__email__ = 'trond.kristiansen@niva.no'
__created__ = datetime.datetime(2017, 2, 24)
__modified__ = datetime.datetime(2021, 5, 7)
__version__ = "2.0"
__status__ = "Development" 
__history__ = "Converted from version by Anna Birgitta Ledang, NIVA; Changed 15.01.2020, " \
              "New template 07.05.2021 Trond Kristiansen"

class StationExcel:
    def open_excel_file(self, filename, sheet_name):
      
        if os.path.exists(filename): 
            os.remove(filename)
        options = {'strings_to_formulas': False, 'strings_to_urls': False}
        writer = pd.ExcelWriter(filename, engine='openpyxl', options=options)

        return writer

    def get_excel_filename(self,CTDConfig):
        if not os.path.exists('xlsfiles/{}'.format(CTDConfig.survey)):
            Path('xlsfiles/{}'.format(CTDConfig.survey)).mkdir(parents=True, exist_ok=True)

        return "xlsfiles/{}/{}_CTD.xlsx".format(CTDConfig.survey, self.name)
                    
    def write_station_to_excel(self, CTDConfig):
        filename = self.get_excel_filename(CTDConfig)
        sheet_name = 'Rådata'
        pbar = progressbar.ProgressBar(max_value=len(self.depth), redirect_stdout=True).start()
        
        # Load the data
        self.createTimeSection(CTDConfig)
        first=True
        startrow=0
        header=True
        missing_value=-999
        
        for station_index, de in enumerate(self.depth):
            pbar.update(station_index+1)
            d = num2date(self.julianDay[station_index], units=CTDConfig.refdate, calendar="standard")
            excl = datetime.datetime.strptime('1900-01-01','%Y-%M-%d').toordinal()

            if isinstance(d, cftime.DatetimeGregorian):
                dateObject = datetime.datetime(d.year, d.month, d.day, d.hour, d.minute, d.second)

            d_num = dateObject.toordinal()
            date_num = d_num - (excl-2)

            if dateObject.year == 2019 and dateObject.month == 12 or dateObject.year == 2020:
                projname = []; statcode = []; mtd = []; dat = []
                for i in self.Y:
                    projname.append(self.projectname)
                    statcode.append(self.stationid)
                    mtd.append(self.method)
                    dat.append(date_num)
                depth1 = self.Y
                depth2 = self.Y + 1.0

                # No VT52 and VT75 in February 2017
                if (self.name in ["VT52","VT75"] and int(dateObject.year)==2017 and int(dateObject.month)==2):
                    print("EMPTY DATA ADDED FOR STATION {}".format(self.name))
                else:
                    print("Writing data to file {} {}".format(dateObject,dateObject.strftime("%d-%m-%Y %H:%M:%S")))
                    df = pd.DataFrame({'PROJECT_NAME': str(self.projectname),
                                        'STATION_CODE': str(self.stationid),
                                        'STATION_NAME': str(self.name),
                                        'DATASOURCE_NAME': 'NIVA',
                                        'INSTRUMENT_REF': mtd,
                                        'Date': dateObject.strftime("%d-%m-%Y %H:%M:%S"), #date_num,
                                        'DEPTH1': depth1,
                                        'DEPTH2': depth2,
                                        'REMARK':"",
                                        'Saltholdighet PSU': self.sectionSA[station_index,:],
                                        'Temperatur C': self.sectionTE[station_index,:],
                                        'Oksygen ml O2/L': self.sectionOX[station_index,:],
                                        'Oksygenmetning %': self.sectionOXS[station_index,:]})

                    # Replace nans with missing value
                    df=df.fillna(missing_value)

                    if first:
                        print("Writing data to file {}".format(filename))
                        writer = self.open_excel_file(filename,sheet_name)
                        first = False

                    # write out the data to file

                    df.to_excel(writer, sheet_name, startrow=startrow, header=header)
                    startrow = writer.book[sheet_name].max_row
                    header=False

                    # save the workbook
                writer.save()
