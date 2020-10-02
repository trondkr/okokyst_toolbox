import numpy as np
import pandas as pd
import datetime
from okokyst_metadata import serveys_lookup_table
import os
import re
import glob
import gsw
from okokyst_tools import  pressure_to_depth
encoding = "ISO-8859-1"

__author__   = 'Elizaveta Protsenko'
__email__    = 'Elizaveta.Protsenko@niva.no'
__created__  = datetime.datetime(2020, 9, 23)
__version__  = "1.0"
__status__   = "Development"


def to_rename_columns(df,old_name, new_name):
    if old_name in df.columns:
        df = df.rename(columns={old_name : new_name})
    return df


def modify_df(df):
    '''
    Convert columns name to the format used further in the processing steps
    '''
    # df = to_rename_columns(df, 'Press', "Depth")
    df = to_rename_columns(df, 'Depth(u)', "Depth")
    df = to_rename_columns(df, 'Sal.', 'Salinity')
    df = to_rename_columns(df, 'T(FTU)', 'FTU')
    df = to_rename_columns(df, 'T (FTU)', 'FTU')
    df = to_rename_columns(df, 'OpOx %', 'OptOx')
    df = to_rename_columns(df, 'Opmg/l', 'OxMgL')

    convert_dict = {
        'Press': float
    }


    df['Date'] = pd.to_datetime(df['Date'], format='%d.%m.%Y').dt.strftime('%d.%m.%Y')
    df['Time'] = pd.to_datetime(df['Time'], format='%H:%M:%S').dt.strftime('%H.%M.%S')

    df = df.astype(convert_dict)
    df = df.dropna(how='all', axis=1)
    df = df.round(4)
    return df


class processStation(object):
    def __init__(self, inputpath):

        self.input_path = inputpath
        self.base_path = os.path.split(self.input_path)[0]

        self.non_assigned = []
        self.servey = self.get_region_from_path()

        self.stations_list = list(serveys_lookup_table[self.servey].keys())
        self.stations_depths = np.array([serveys_lookup_table[self.servey][st]['depth'] for st in self.stations_list])

        self.df_all = self.read_convert_df()
        self.calc_depth()

        if self.df_all is not None:
            self.df_all = modify_df(self.df_all)
            self.df_all.groupby('Ser').apply(self.match_stations_by_depth)
        else:
            print('Error in reading the dataframe')

    def calc_depth(self):
        first_st = list(serveys_lookup_table[self.servey].keys())[0]
        print (first_st)
        latitude = serveys_lookup_table[self.servey][first_st]["station.latitude"]
        depths = []
        for p in self.df_all['Press'].values:
            d = pressure_to_depth(float(p), latitude)
            depths.append(d)
        self.df_all['Depth'] = depths
        print (self.df_all)


    def get_region_from_path(self):

        regions = {'Leon': 'Sognefjorden', 'Kvitsoy': 'Hardangerfjorden'}
        for r in regions:
            name_to_check = re.compile(r, re.IGNORECASE)
            find_match = name_to_check.search(self.input_path)
            if find_match:
                return regions[r]

    def read_convert_df(self):
        print ('\n****** Reading', self.input_path)
        # read the document and skip undefined number of unneeded rows

        for n in range(1, 10):
            print('Attempt N', n)
            try:

                df_all = pd.read_csv(self.input_path, skiprows=n, header=n-1,
                                     sep=';', decimal=',', encoding=encoding)
                if len(df_all.columns) < 10:
                    print('short', df_all.columns)
                    try:
                        df_all = pd.read_csv(self.input_path, skiprows=n, header=n,
                                             sep=';', decimal=',', encoding=encoding)
                        print(df_all.columns)
                        df_all.head()
                        break
                    except Exception as e:
                        print('Exception 2', e)
                        pass

                else:
                    break
            except Exception as e:
                print('Exception 1', e)
                df_all = None

            try:
                df_all = pd.read_csv(self.input_path, skiprows=n, header=n-1,
                                     sep=';', decimal='.')
                if len(df_all.columns) < 10:
                    print('short', df_all.columns)
                    try:
                        df_all = pd.read_csv(self.input_path, skiprows=n, header=n,
                                             sep=';', decimal=',')
                        print(df_all.columns)
                        df_all.head()
                        break
                    except Exception as e:
                        print('Exception 4', e)
                        pass
            except Exception as e:
                print('Exception 3', e)
                df_all = None

        return df_all

    def match_stations_by_depth(self, group):
        print(' ')

        # Get number of the cast
        Ser = group['Ser'].values[0]

        # Find the max depth of the group (this cast)
        max_depth = np.max(group['Depth'])

        # find the closest depth in the arr with all stations for this region
        difs = self.stations_depths - max_depth
        sqr_difs = np.sqrt(difs**2)
        min_dif = np.min(sqr_difs)

        print('max depth', max_depth)
        print('min difference', min_dif)

        self.servey_date = group.Date.values[0]
        self.make_new_base_path()

        print('Time', group.Time.values[0])

        if 'Salinity' not in group.columns:
            group = self.calc_salinity(group)
        if self.servey == 'Hardangerfjorden':
            dif_threshold = 25
        else:
            dif_threshold = 50
        if min_dif < dif_threshold:
            nearest_depth_id = np.where(sqr_difs == min_dif)[0][0]
            self.station_name = self.stations_list[nearest_depth_id]

            self.station_metadata = serveys_lookup_table[self.servey][self.station_name]

            print(self.station_name)
            print('Date', self.servey_date)

            # Save df matched by station
            self.filename = os.path.join(self.base_path, self.station_name + '.txt')



            group=group.drop(columns=['Press'])

            columnOrder=['Ser','Meas','Salinity','Conductivity', 'Temp', 'FTU',
                           'OptOx', 'OxMgL', 'Density', 'Depth', 'Date', 'Time']
            group=group.reindex(columns=columnOrder)
            group.to_csv(self.filename, index=False, sep=';')

            #Add header and save update file in the new location

            self.add_metadata_header()
        else:

            print('Was not able to find a matching station name')

            if max_depth < 10:
                print("Probably it is a cleaning station ")

                filename = os.path.join(self.base_path, 'Cleaning_station', str(Ser), '.txt')
                new_filename = os.path.join(self.new_base_path, 'Cleaning_station' + str(Ser) + '.txt')
            else:
                print('available station depths', self.stations_depths)

                filename = self.base_path + r'\\Unknown_station' + str(Ser) + '.txt'
                new_filename = self.new_base_path + r'\\Unknown_station' + str(Ser) + '.txt'
            self.non_assigned.append(filename)
            group.to_csv(filename, index=False, sep=';')
            group.to_csv(new_filename, index=False, sep=';')

        return




    def calc_salinity(self,group):
        ''' If salinity is not in the list
            calculate if from TSP
        '''
        print(group.head(), 'GROUP')
        salinity = []
        for n in range(len(group['Cond.'])):
            s = gsw.SP_from_C(group['Cond.'].values[n], group['Temp'].values[n], group['Press'].values[n])
            salinity.append(s)

        group['Salinity'] = salinity

        print ('****Salinity***', group)

        return group



    def make_new_base_path(self):
        # datetime.datetime.strptime(

        date_folder = pd.to_datetime(str(self.servey_date)).strftime('%Y-%m-%d')

        user = r'C:\Users\ELP\OneDrive - NIVA\Documents\Projects\\'

        self.new_base_path = os.path.join(user, "OKOKYST\ØKOKYST_NORDSJØENNORD_CTD", self.servey, date_folder, date_folder + " CTD data")

        if not os.path.exists(self.new_base_path):
            os.makedirs(self.new_base_path)

    def add_metadata_header(self):
        header = self.station_metadata['station.header']
        new_filename = os.path.join(self.new_base_path, self.station_name + '.txt')

        # Open initial file, update header, save the new file in One_Drive
        with open(self.filename, 'r') as read_obj, open(new_filename, 'w') as write_obj:
            write_obj.write(header)
            for line in read_obj:
                write_obj.write(line)

        # os.remove(filename)
        # os.rename(dummy_file, filename)


if __name__ == "__main__":

    #k_work_dir = r'K:/Avdeling/214-Oseanografi/DATABASER/OKOKYST_2017/OKOKYST_NS_Nord_Leon/t46_Sept2020_Saiv_Leon'
    main_folder = 'K:/Avdeling/214-Oseanografi/DATABASER/OKOKYST_2017/OKOKYST_NS_Nord_Leon'


    files2020 = [f for f in os.listdir(main_folder) if re.search('2020_saiv_leon', f, re.IGNORECASE)]
    files = files2020

    print (files2020)


    for file in files:

        file_path = os.path.join(main_folder, file)

        subfiles = glob.glob(file_path + '/**/*.txt', recursive=True)
        txtfiles = [f for f in subfiles if re.search('saiv_leon.txt', f, re.IGNORECASE)]
        non_assigned = []
        if len(txtfiles) > 0:
            input_path = txtfiles[0]
            d = processStation(input_path)
            non_assigned.append(d.non_assigned)
        print ('non_assigned paths', non_assigned)

    #file_path = "K:/Avdeling/214-Oseanografi/DATABASER/OKOKYST_2017/OKOKYST_NS_Nord_Leon/t46_Sept2020_Saiv_Leon/O-200075_20200913_SAIV_LEON.txt"
    #input_path =  k_work_dir + file_path # r'K:/Avdeling/214-Oseanografi/DATABASER/OKOKYST_2017/OKOKYST_NS_Nord_Leon/t46_Sept2020_Saiv_Leon'

