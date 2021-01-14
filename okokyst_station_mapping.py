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

    try:
        df['Date'] = pd.to_datetime(df['Date'], format='%d.%m.%Y').dt.strftime('%d.%m.%Y')
    except Exception as e:
        print (e)
    try:
        df['Time'] = pd.to_datetime(df['Time'], format='%H:%M:%S').dt.strftime('%H.%M.%S')
    except Exception as e:
        print (e)

    df = df.astype(convert_dict)
    df = df.dropna(how='all', axis=1)
    df = df.round(4)
    return df


class processStation(object):
    def __init__(self, inputpath):

        self.input_path = inputpath
        self.base_path = os.path.split(self.input_path)[0]
        name = os.path.split(self.input_path)[1]
        import re
        x = re.findall("[0-9]{8}", name)
        self.correct_survey_date = pd.to_datetime(x, format='%Y%m%d').strftime('%d.%m.%Y').values[0]
        self.non_assigned = []
        self.assigned = []
        self.servey = self.get_region_from_path()

        self.stations_list = list(serveys_lookup_table[self.servey].keys())
        self.stations_depths = np.array([serveys_lookup_table[self.servey][st]['depth'] for st in self.stations_list])

        self.df_all = self.read_convert_df()
        self.calc_depth()
        print('\nDate', self.correct_survey_date)
        try:
            self.df_all = modify_df(self.df_all)

            grouped = self.df_all.groupby('Ser')
            for name, group_df in grouped:

                self.match_stations_by_depth(group_df)
            #groups = [unused_df for name, unused_df in grouped]
            #print (groups)
            #grouped.apply(self.match_stations_by_depth)
        except:
            print('Error in reading the dataframe')

    def calc_depth(self):
        first_st = list(serveys_lookup_table[self.servey].keys())[0]

        latitude = serveys_lookup_table[self.servey][first_st]["station.latitude"]
        depths = []
        for p in self.df_all['Press'].values:
            d = pressure_to_depth(float(p), latitude)
            depths.append(d)
        self.df_all['Depth'] = depths



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
                        #df_all.head()
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
        print('\n***********************************')
        # Get number of the cast
        Ser = group['Ser'].values[0]
        print('Cast', Ser)

        self.servey_date = group.Date.values[0]

        if self.servey_date == self.correct_survey_date:


            # Find the max depth of the group (this cast)
            #print (group['Depth'].values)
            max_depth = np.max(group['Depth'].max())

            # find the closest depth in the arr with all stations for this region
            difs = self.stations_depths - max_depth
            sqr_difs = np.sqrt(difs**2)
            min_dif = np.min(sqr_difs)

            print('max depth', max_depth)
            print('min difference', min_dif)

            self.make_new_base_path()

            print('Time', group.Time.values[0])

            if 'Salinity' not in group.columns:
                group = self.calc_salinity(group)
            if self.servey == 'Hardangerfjorden':
                dif_threshold = 50
            else:
                dif_threshold = 50

            group=group.drop(columns=['Press'])
            columnOrder=['Ser','Meas','Salinity','Conductivity', 'Temp', 'FTU',
                           'OptOx', 'OxMgL', 'Density', 'Depth', 'Date', 'Time']
            group=group.reindex(columns=columnOrder)

            if min_dif < dif_threshold:
                nearest_depth_id = np.where(sqr_difs == min_dif)[0][0]
                self.station_name = self.stations_list[nearest_depth_id]
                self.station_metadata = serveys_lookup_table[self.servey][self.station_name]

                #l = [os.path.split(f)[-1][:-4] for f in self.assigned]

                print (self.station_name, 'already assigned stations:', self.assigned)
                if self.station_name in self.assigned:
                    print ("duplicate")
                    self.station_name = self.station_name + "_duplicate"

                print(self.station_name)


                # Save df matched by station
                self.filename = os.path.join(self.base_path, self.station_name + '.txt')
                group.to_csv(self.filename, index=False, sep=';')

                #Add header and save update file in the new location
                self.assigned.append(self.station_name)
                self.add_metadata_header()
            else:

                print('Was not able to find a matching station name')

                if max_depth < 10:
                    print("Probably it is a cleaning station ")

                    filename = os.path.join(self.base_path, 'Cleaning_station', str(Ser), '.txt')
                    new_filename = os.path.join(self.new_base_path, 'Cleaning_station' + str(Ser) + '.txt')
                else:
                    print('available station depths', self.stations_depths)

                    #filename = self.base_path + r'\\Unknown_station' + str(Ser) + '.txt'
                    new_filename = self.new_base_path + r'\\Unknown_station' + str(Ser) + '.txt'

                self.non_assigned.append(new_filename)
                #group.to_csv(filename, index=False, sep=';')
                group.to_csv(new_filename, index=False, sep=';')
        else:
            print ('Date of measurement does not match date in a filename')
            print(self.servey_date, self.correct_survey_date, self.servey_date == self.correct_survey_date)
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
        self.new_base_path = os.path.join(onedrive, self.servey, date_folder, date_folder + " CTD data")

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

    '''newfile = base_path +f'\\to_{station_name}.txt'
    try:
        os.rename(filepath, newfile)
    except WindowsError:
        os.remove(newfile)
        os.rename(filepath, newfile)'''
    try:
        os.remove(filepath)
    except Exception as e:
        print (e)
    #os.rename(filepath, base_path +f'to_{station_name}.txt')

def process_all_2020(task):
    if task == "sognefjorden":
        main_folder = os.path.join(k_work_dir, 'OKOKYST_NS_Nord_Leon')
        files = [f for f in os.listdir(main_folder) if re.search('2019_saiv_leon', f, re.IGNORECASE)]

    elif task == "hardangerfjorden":
        main_folder = os.path.join(k_work_dir, "OKOKYST_NS_Nord_Kvitsoy")
        files = [f for f in os.listdir(main_folder) if re.search('_2019', f, re.IGNORECASE)]


    non_assigned = []
    for file in files:
        file_path = os.path.join(main_folder, file)

        if task == "sognefjorden":
            subfiles = glob.glob(file_path + '/**/*.txt', recursive=True)
            txtfiles = [f for f in subfiles if (re.search('.txt', f, re.IGNORECASE) and not re.search('VT', f))]

        elif task == "hardangerfjorden":
            subfiles = glob.glob(file_path + '/**/*.txt', recursive=True)
            txtfiles = [f for f in subfiles if (re.search('txt', f, re.IGNORECASE) and not re.search('VT', f))]


        if len(txtfiles) > 0:
            input_path = txtfiles[0]
            d = processStation(input_path)
            if set(d.assigned) != len(d.assigned):
                print ('some stations got the same name ')
            if len(d.non_assigned) > 0:
                l = [os.path.split(f)[-1] for f in d.assigned]
                if task == 'hardangerfjorden':
                    if len(l) == 3 and 'VT69' not in l:
                        for file in d.non_assigned:
                            if re.search('station1', file):
                                #newfile = os.path.split(file)[0] + '\\VT69.txt'
                                manual_add_metadata_header(file, 'VT69')
                            else:
                                newfile = os.path.split(file)[0]+'_probably_VT69.txt'
                                d.non_assigned.append(newfile)
                                try:
                                    os.rename(file, newfile)
                                except WindowsError:
                                    os.remove(newfile)
                                    os.rename(file, newfile)
                            d.non_assigned.remove(file)
                else:
                    print (l)
                    print (d.non_assigned)
                non_assigned.append(d.non_assigned)

    print("\nCould not assign names for:")
    for n in non_assigned:
        print (n)

if __name__ == "__main__":

    k_work_dir = r'K:/Avdeling/214-Oseanografi/DATABASER/OKOKYST_2017/'
    onedrive = r'C:\Users\ELP\OneDrive - NIVA\Documents\Projects\\OKOKYST\ØKOKYST_NORDSJØENNORD_CTD'
    task = "sognefjorden"
    #task = "hardangerfjorden"

    #process_all_2020(task)


    #processStation(r'K:\Avdeling\214-Oseanografi\DATABASER\OKOKYST_2017\OKOKYST_NS_Nord_Leon\t36_Des2019_Saiv_Leon\O-19075_20191215_Leon.txt')
    #manual_add_metadata_header(r'C:\Users\ELP\OneDrive - NIVA\Documents\Projects\OKOKYST\ØKOKYST_NORDSJØENNORD_CTD\Sognefjorden\2019-12-15\2019-12-15 CTD data\Unknown_station4.txt', 'VT16')

    #processStation(r'K:\Avdeling\214-Oseanografi\DATABASER\OKOKYST_2017\OKOKYST_NS_Nord_Leon\t37_Janv2020_Saiv_Leon\O-19075_20200119_Leon_sal.txt')

    #processStation(r'K:\Avdeling\214-Oseanografi\DATABASER\OKOKYST_2017\OKOKYST_NS_Nord_Leon\t38_Feb2020_Saiv_Leon\O-20075_20200219.txt')
    #manual_add_metadata_header(r'C:\Users\ELP\OneDrive - NIVA\Documents\Projects\OKOKYST\ØKOKYST_NORDSJØENNORD_CTD\Sognefjorden\2020-02-19\2020-02-19 CTD data\Unknown_station4.txt',
    #                           "VT16")

    #processStation(r'K:\Avdeling\214-Oseanografi\DATABASER\OKOKYST_2017\OKOKYST_NS_Nord_Leon\t39_Mar2020_Saiv_Leon\O-20075_20200312.txt')
    #processStation(r'K:\Avdeling\214-Oseanografi\DATABASER\OKOKYST_2017\OKOKYST_NS_Nord_Leon\t45_aug2020_SAIV_Leon\O-200075-20200816_SAIV_Leon.txt')
    # okt processStation(r'K:\Avdeling\214-Oseanografi\DATABASER\OKOKYST_2017\OKOKYST_NS_Nord_Leon\t47_Okt2020_SAIV_Leon\O-200075_20201018_SAIV_LEON.txt')
    #processStation(r'K:\Avdeling\214-Oseanografi\DATABASER\OKOKYST_2017\OKOKYST_NS_Nord_Leon\t48_Nov2020_SAIV_Leon\O-200075_20201110_SAIV_Leon.txt')
    #processStation(os.path.join(k_work_dir, r"OKOKYST_NS_Nord_Kvitsoy\t46_2020_09_21\Kvitsøy_2020-09-21 og 22.txt"))


    #fpath = os.path.join(onedrive, r'Hardangerfjorden\2020-09-21\2020-09-21 CTD data\Unknown_station1.txt')
    #name = 'VT69'
    #manual_add_metadata_header("C:\\Users\\ELP\\OneDrive - NIVA\\Documents\\Projects\\\\OKOKYST\\ØKOKYST_NORDSJØENNORD_CTD\\Sognefjorden\\2019-12-15\\2019-12-15 CTD data\\\\Unknown_station4.txt",
    #                           "VT16")
    #manual_add_metadata_header("C:\\Users\\ELP\\OneDrive - NIVA\\Documents\\Projects\\\\OKOKYST\\ØKOKYST_NORDSJØENNORD_CTD\\Sognefjorden\\2019-12-15\\2019-12-15 CTD data\\\\Unknown_station1.txt",
    #                           "VT16")