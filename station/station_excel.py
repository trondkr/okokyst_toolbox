import os
import datetime
from pathlib import Path
from netCDF4 import date2num, num2date
import progressbar
import pandas as pd
import cftime

# Local files
import ctdConfig as CTDConfig

__author__ = 'Trond Kristiansen'
__email__ = 'trond.kristiansen@niva.no'
__created__ = datetime.datetime(2017, 2, 24)
__modified__ = datetime.datetime(2020, 1, 15)
__version__ = "2.0"
__status__ = "Development" 
__history__ = "Converted from version by Anna Birgitta Ledang, NIVA; Changed 15.01.2020 Trond Kristiansen"

class StationExcel:
    def open_excel_file(self, filename, sheet_name):
      
        if os.path.exists(filename): 
            os.remove(filename)
        writer = pd.ExcelWriter(filename, engine='openpyxl')

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
            print("Date", d_num, dateObject)
            date_num = d_num - (excl-2)

            projname = []; statcode = []; mtd = []; dat = []
            for i in self.Y:
                projname.append(self.projectname)
                statcode.append(self.stationid)
                mtd.append(self.method)
                dat.append(date_num)
            depth1 = self.Y - 0.5
            depth2 = self.Y + 0.5

            # No VT52 and VT75 in February 2017
            if (self.name in ["VT52","VT75"] and int(dateObject.year)==2017 and int(dateObject.month)==2):
                print("EMPTY DATA ADDED FOR STATION {}".format(self.name))
            else:
               # print("Writing data to file {}".format(dat[0]))
                df = pd.DataFrame({'ProjectName': projname,
                                    'StationCode': statcode,
                                    'Date': dat,
                                    'Depth1': depth1,
                                    'Depth2': depth2,
                                    'Saltholdighet': self.sectionSA[station_index,:],
                                    'Temperatur': self.sectionTE[station_index,:],
                                    'Oksygen': self.sectionOX[station_index,:],
                                    'Oksygenmetning': self.sectionOXS[station_index,:],
                                    'Metode': mtd})
                
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
