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


def modify_df(df,onedrive,filename):
    print ("modify_df")
    '''
    Convert columns name to the format used further in the processing steps
    '''
    # df = to_rename_columns(df, 'Press', "Depth")
    #print (df.columns)
    df = to_rename_columns(df, 'Depth(u)', "Depth")
    df = to_rename_columns(df, 'Sal.', 'Salinity')
    df = to_rename_columns(df, 'T(FTU)', 'FTU')
    df = to_rename_columns(df, 'T (FTU)', 'FTU')
    df = to_rename_columns(df, 'OpOx %', 'OptOx')
    df = to_rename_columns(df, 'Ox %', 'OptOx')
    df = to_rename_columns(df, 'mg/l', 'OxMgL')
    df = to_rename_columns(df, 'Opt', 'OptOx')

    df = to_rename_columns(df, 'Opmg/l', 'OxMgL')
    df = to_rename_columns(df, 'Opml/l', 'OxMlL')

    # recalculate Oxygen into Ml/l

    convert_dict = {
        'Press': float
    }

    df = df.astype(convert_dict)
    print ("press to float")
    if 'OxMgL' in df.columns:
        print ('recalculate to ml/l')
        df = df.astype({'OxMgL': float})
        df['OxMgL'] = df.OxMgL.values / 1.42905
        df = to_rename_columns(df,  'OxMgL', 'OxMlL')

    try:
        df['Date'] = pd.to_datetime(df['Date'], format='%d.%m.%Y').dt.strftime('%d.%m.%Y')
    except Exception as e:
        print ('date',e)
    try:
        df['Time'] = pd.to_datetime(df['Time'], format='%H:%M:%S').dt.strftime('%H.%M.%S')
    except Exception as e:
        print ('time', e)

    try:
        df = df.astype({'OxMlL': float})
    except Exception as e:
        print ('float', e)
        try:
            df = df.astype({'OxMgL': float})
        except:
            print ('Probably Oxygen is missing')

    df = df.dropna(how='all', axis=1)
    df = df.round(4)
    if len(set(df['OptOx'].values)) < 5:

        er=open(f"{onedrive}\\Errors\\NoOxygenData.txt","w+")
        er.write(filename)
        er.close()
    return df


class processStation(object):
    def __init__(self, inputpath,onedrive):

        self.input_path = inputpath
        self.base_path = os.path.split(self.input_path)[0]
        name = os.path.split(self.input_path)[1]
        self.onedrive = onedrive


        #try:
        #    y = re.findall("[0-9]", str(name))
        #    x = ''.join(y)
        #    print (name,x)
        #    self.correct_survey_date = pd.to_datetime(x, format='%Y%m%d').strftime('%d.%m.%Y')
        #    print ('correct_survey_date', self.correct_survey_date)#.values
        #except:
        #    y = re.findall("[0-9]{8}", str(name))
        #    x = ''.join(y)
        #    print(name, x)
        #    self.correct_survey_date = pd.to_datetime(x, format='%Y%m%d').strftime('%d.%m.%Y')
        #    print('correct_survey_date', self.correct_survey_date)  # .values

        self.non_assigned = []
        self.assigned = []
        self.servey = self.get_region_from_path()

        self.stations_list = list(serveys_lookup_table[self.servey].keys())
        self.stations_depths = np.array([serveys_lookup_table[self.servey][st]['depth'] for st in self.stations_list])

        self.df_all = self.read_convert_df()
        try:
            self.calc_depth()
        except Exception as e:
            print('Error in reading the dataframe', e)

        try:
            self.df_all = modify_df(self.df_all, self.onedrive,name)

            grouped = self.df_all.groupby('Ser')

            for name, group_df in grouped:
                self.match_stations_by_depth(group_df)

        except Exception as e:
            print('Error in reading the dataframe',e)

    def calc_depth(self):
        first_st = list(serveys_lookup_table[self.servey].keys())[0]
        print ('calc depth')
        latitude = serveys_lookup_table[self.servey][first_st]["station.latitude"]
        depths = []

        for p in self.df_all['Press'].values:
            d = pressure_to_depth(float(p), latitude)
            depths.append(d)
        self.df_all['Depth'] = depths



    def get_region_from_path(self):

        regions = {'Leon': 'Sognefjorden', 'Kvitsoy': 'Hardangerfjorden',
                   'Hardangerfjorden': 'Hardangerfjorden', 'Sognefjorden': 'Sognefjorden', 'RMS': 'RMS',
                   'Aquakompetens': 'Aqua kompetanse'}

        for r in regions:
            name_to_check = re.compile(r, re.IGNORECASE)
            find_match = name_to_check.search(self.input_path)
            if find_match:
                return regions[r]

    def read_convert_df(self):
        print ('\n****** Reading', self.input_path)
        # read the document and skip undefined number of unneeded rows

        for n in range(1, 16):
            print('Attempt N', n)
            try:

                df_all = pd.read_csv(self.input_path, skiprows=n, header=n-1,
                                     sep=';', decimal=',', encoding=encoding)

                #print (df_all.head())
                if len(df_all.columns) < 10:
                    print('short', df_all.columns)
                    try:
                        df_all = pd.read_csv(self.input_path, skiprows=n, header=n,
                                             sep=';', decimal=',', encoding=encoding)
                        #print(df_all.columns)
                        break
                    except Exception as e:
                        print('Exception 2')
                        pass

                else:
                    break
            except Exception as e:
                print('Exception 1')
                df_all = None

            try:
                df_all = pd.read_csv(self.input_path, skiprows=n, header=n-1,
                                     sep=';', decimal='.')
                if len(df_all.columns) < 10:
                    print('short', df_all.columns)
                    try:
                        df_all = pd.read_csv(self.input_path, skiprows=n, header=n,
                                             sep=';', decimal=',')
                        #print(df_all.columns)
                        df_all.head()
                        break
                    except Exception as e:
                        print('Exception 4', e)
                        pass
            except Exception as e:
                print('Exception 3', e)
                df_all = None
        try:
            print ('***',df_all.columns)
        except Exception as e:
            print (e)

        return df_all

    def match_stations_by_depth(self, group):
        print('\n***********************************')
        # Get number of the cast
        Ser = group['Ser'].values[0]
        print('Cast', Ser)

        self.servey_date = group.Date.values[0]

        max_depth = np.max(group['Depth'].max())

        # find the closest depth in the arr with all stations for this region
        difs =  self.stations_depths - max_depth
        #print ('difs',difs)
        difs_pos  = list(filter(lambda x : x > -10, difs))
        #print (difs_pos,'filtered difs')
        #sqr_difs = np.sqrt(difs**2)
        min_dif = np.min(difs_pos)

        print('max depth', max_depth,'min difference', min_dif, 'Time', group.Time.values[0])

        self.make_new_base_path()

        if 'Salinity' not in group.columns:
            group = self.calc_salinity(group)
        if self.servey == 'Hardangerfjorden':
            dif_threshold = 50
        else:
            dif_threshold = 50

        group=group.drop(columns=['Press'])
        columns = group.columns

        if 'OxMgL' in columns:
            columnOrder=['Ser','Meas','Salinity','Conductivity', 'Temp', 'FTU',
                           'OptOx', 'OxMgL', 'Density', 'Depth', 'Date', 'Time']
            #print('max OxMlL') #, group['OxMgL'].max(), group.columns)
        else:
            print ('O2 in Ml/l')
            columnOrder=['Ser','Meas','Salinity','Conductivity', 'Temp', 'FTU',
                           'OptOx', 'OxMlL', 'Density', 'Depth', 'Date', 'Time']
            #print('max OxMlL') #, group['OxMlL'].max(), group.columns)
        group=group.reindex(columns=columnOrder)
        #print ('min dif', min_dif)
        if min_dif < dif_threshold:
            # double check the sign of the difference (if cast went deeper than the station, do no assign)
            nearest_depth_id = np.where(difs == min_dif)[0][0]
            #print ('nearest_depth_id', np.where(difs == min_dif)[0][0])
            #print ('stations list', self.stations_list)
            self.station_name = self.stations_list[nearest_depth_id]
            self.station_metadata = serveys_lookup_table[self.servey][self.station_name]

            #l = [os.path.split(f)[-1][:-4] for f in self.assigned]

            if self.station_name in self.assigned:
                print(self.station_name, 'already assigned stations:', self.assigned)
                print ("duplicate")
                self.station_name = self.station_name + "_duplicate"


            # Save df matched by station
            #self.filename = os.path.join(self.base_path, self.station_name + '.txt')
            self.filename = os.path.join(self.new_base_path, self.station_name + '_temp.txt')

            print('station_name', self.station_name)
            print('save data to file with ', self.filename, Ser)

            group.to_csv(self.filename,  sep=';')

            #Add header and save update file in the new location
            self.assigned.append(self.station_name)
            self.add_metadata_header()

        else:
            print('Was not able to find a matching station name')

            if max_depth < 10:
                print("Probably it is a cleaning station ")
                new_filename = os.path.join(self.new_base_path, 'Cleaning_station' + str(Ser) + '.txt')
            else:
                print('available station depths', self.stations_depths)

                #filename = self.base_path + r'\\Unknown_station' + str(Ser) + '.txt'
                print('Cast Unknown_station', Ser)
                print (max_depth,'max depth')
                new_filename = self.new_base_path + r'\\Unknown_station' + str(Ser) + '.txt'

            self.non_assigned.append(new_filename)
            #group.to_csv(filename, index=False, sep=';')
            #print (group['OxMlL'].values.max())
            group.to_csv(new_filename, index=False, sep=';')
        #else:
        #    print ('Date of measurement does not match date in a filename')
        #    print(self.servey_date, self.correct_survey_date, self.servey_date == self.correct_survey_date)
        return


    def calc_salinity(self,group):
        ''' If salinity is not in the list
            calculate if from TSP
        '''
        print( 'calculating_salinity')
        salinity = []
        for n in range(len(group['Cond.'])):
            s = gsw.SP_from_C(group['Cond.'].values[n], group['Temp'].values[n], group['Press'].values[n])
            salinity.append(s)

        group['Salinity'] = salinity

        return group


    def make_new_base_path(self):
        # datetime.datetime.strptime(
        date_folder = pd.to_datetime(str(self.servey_date), format='%d.%m.%Y').strftime('%Y-%m-%d')
        ##self.new_base_path = os.path.join(onedrive, self.servey, date_folder, date_folder + " CTD data")
        self.new_base_path = os.path.join(self.onedrive, date_folder + " CTD data")
        if not os.path.exists(self.new_base_path):
            os.makedirs(self.new_base_path)


    def add_metadata_header(self):
        header = self.station_metadata['station.header']
        #print ('adding metadata header to ', self.station_name,'.txt')
        new_filename = os.path.join(self.new_base_path, self.station_name + '.txt')
        print (new_filename)
        # Open initial file, update header, save the new file in One_Drive
        with open(self.filename, 'r') as read_obj, open(new_filename, 'w') as write_obj:
            write_obj.write(header)
            for line in read_obj:
                write_obj.write(line)
        try:
            os.remove(self.filename)
        except Exception as e:
            print (e)

def manual_add_metadata_header(filepath, station_name):
    t = serveys_lookup_table
    base_path = os.path.split(filepath)[0]

    serveys = t.keys()
    for key in serveys:
        if station_name in t[key]:
            header = t[key][station_name]['station.header']
            break

    new_filename = os.path.join(base_path, station_name + '.txt')

    # Open initial file, update header, save the new file in One_Drive
    with open(filepath, 'r') as read_obj, open(new_filename, 'w') as write_obj:
        write_obj.write(header)
        for line in read_obj:
            write_obj.write(line)

    try:
        os.remove(filepath)
    except Exception as e:
        print (e)
    #os.rename(filepath, base_path +f'to_{station_name}.txt')


if __name__ == "__main__":

    #k_work_dir = r'K:/Avdeling/214-Oseanografi/DATABASER/OKOKYST_2017/'

    #task = "sognefjorden"
    #leon = r"K:\Avdeling\214-Oseanografi\DATABASER\OKOKYST_2017\OKOKYST_NS_Nord_Leon\\"





    def call_process(main_path, foldername):
        path = os.path.join(main_path, foldername)
        onedrive = path

        files = glob.glob(path + '\*txt')
        for f in files:
            if 'OBS' not in f:
                processStation(f,onedrive)


    user = 'TEG'
    main_path_RMS = fr"C:\Users\{user}\OneDrive - NIVA\Okokyst_CTD\Norskehavet_Sor\RMS"
    main_path_aqua = fr"C:\Users\{user}\OneDrive - NIVA\Okokyst_CTD\Norskehavet_Sor\Aquakompetens"
    #foldernames = [f for f in os.listdir(main_path) if re.match(r'2021', f)]

    #RMS
    #call_process(main_path_RMS,'06_2021')
    #call_process('04-2021')
    #call_process('06-2021')
    #call_process('07-2021')
    #call_process('08-2021')

    #Aqua kompetanse
    call_process(main_path_aqua,'2021-03')


    # Sognefjorden 2021
    main_path_sognefjorden = fr"C:\Users\{user}\OneDrive - NIVA\Okokyst_CTD\Nordsjoen_Nord\Sognefjorden"

    #foldername = "2021-01-25"

    # Here the automatic assignment did not work, due to bad weather the CTD did not reach the bottom
    #call_process(main_path_sognefjorden, "2021-02-17")
    #manual_add_metadata_header(r"C:\Users\ELP\OneDrive - NIVA\Okokyst_CTD\Nordsjoen_Nord\Sognefjorden\2021-02-17\2021-02-17 CTD data\Unknown_station2.txt", 'VT16')

    #call_process(main_path_sognefjorden, '2021-03-14')
    #call_process(main_path_sognefjorden, '2021-04-18')
    #call_process(main_path_sognefjorden, '2021-05-19')
    #call_process(main_path_sognefjorden, '2021-06-17')
    #call_process(main_path_sognefjorden, '2021-07-14')
    #call_process(main_path_sognefjorden, '2021-08-18')

    main_path_hardangerfjorden = r'C:\Users\ELP\OneDrive - NIVA\Okokyst_CTD\Nordsjoen_Nord\Hardangerfjorden'
    #call_process(main_path_hardangerfjorden, "2021-04-20-21")

    #Has to be checked, no oxygen! did not work
    ###call_process(main_path_hardangerfjorden, "2021-05-18-20")

    #call_process(main_path_hardangerfjorden, "2021-07")
    ##for f in foldernames:
    ##    call_process(f)



