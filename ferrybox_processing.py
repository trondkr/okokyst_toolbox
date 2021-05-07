import os
import sys
from datetime import datetime
from netCDF4 import date2num
from pyniva import Vessel, TimeSeries, token2header
import pandas as pd
from ferrybox import ferryBoxStationClass as fb
import csv

__author__ = 'Trond Kristiansen'
__email__ = 'trond.kristiansen@niva.no'
__created__ = datetime(2019, 1, 22)
__modified__ = datetime(2020, 3, 6)
__version__ = "1.0"
__status__ = "Development"


def setup_connection_to_nivadb():
    token = '../FBdata/NIVA_TOKEN/nivatestdev-7dee310e019d.json'
    return token2header(token)


def get_list_of_available_timeseries_for_vessel(vessel_name, vessel_abbreviation, start_date, end_date, variable,
                                                use_raw=False):
    header = setup_connection_to_nivadb()
    meta_host = "https://api-test.niva.no/v1/metaflow/"
    tsb_host = "https://api-test.niva.no/v1/tsb/"

    vessel_list = [v for v in Vessel.list(meta_host, header=header) if hasattr(v, "imo")]

    for v in vessel_list:
        if v.name == vessel_name:
            print("Fetching data for vessel {} ({})".format(v.name, vessel_abbreviation))

            # Get signals the vessel
            signals = v.get_all_tseries(meta_host, header=header)

            if variable == 'temperature':
                db_path = "{}/ferrybox/INLET/TEMPERATURE".format(vessel_abbreviation)
            elif variable == 'salinity':
                db_path = "{}/ferrybox/CTD/SALINITY".format(vessel_abbreviation)
            elif variable == 'chla_fluorescence':
                if not use_raw:
                    db_path = "{}/ferrybox/CHLA_FLUORESCENCE/BIOF_CORR_AND_CALIB".format(vessel_abbreviation)
                else:
                    db_path = "{}/ferrybox/CHLA_FLUORESCENCE/RAW".format(vessel_abbreviation)
            elif variable == 'cdom_fluorescence':
                db_path = "{}/ferrybox/CDOM_FLUORESCENCE/ADJUSTED".format(vessel_abbreviation)
            elif variable == 'turbidity':
                db_path = "{}/ferrybox/TURBIDITY".format(vessel_abbreviation)
            else:
                db_path = "{}/ferrybox/CHLA_FLUORESCENCE/BIOF_CORR_AND_CALIB".format(vessel_abbreviation)

            interesting_signals = [db_path, "{}/gpstrack".format(vessel_abbreviation)]

            int_ts = [ts for sn in interesting_signals
                      for ts in signals if sn in ts.path]
            for ts in int_ts:
                print(" Paths found => ", ts.path)

            if len(int_ts) > 0:
                data = TimeSeries.get_timeseries_list(tsb_host, int_ts,
                                                      start_time=start_date,  # datetime.utcnow() - timedelta(260),
                                                      end_time=end_date,  # datetime.utcnow()- timedelta(90),
                                                      name_headers=True,
                                                      header=header,
                                                      noffill=True,
                                                      dt=0)

                data.to_csv('FA.csv')
    return data


def get_data_around_station(df, st_lon, st_lat, dist):
    # https://stackoverflow.com/questions/21415661/logical-operators-for-boolean-indexing-in-pandas
    # Filter out the longitude and latitudes surrounding the station lat/lon
    print(df['latitude'])
    return df[
        (st_lat - dist < df['latitude']) & (df['latitude'] < st_lat + dist) & (st_lon - 2 * dist < df['longitude']) & (
                df['longitude'] < st_lon + 2 * dist)]


def get_data_at_station_and_timestamp(df, st_lon, st_lat, timestamp):
    # https://stackoverflow.com/questions/21415661/logical-operators-for-boolean-indexing-in-pandas
    # Filter out the nearest observations in time from water sample
    ind = df.index.get_loc(timestamp, method='nearest')

    return df.index[ind], df.iloc[ind]


def create_station(stationid, df, varname):
    metadata = ferrybox_metadata(stationid)
    # Get the data for the station

    if not metadata["plot_along_latitude"]:
        df_st = get_data_around_station(df, metadata['longitude'], metadata['latitude'], 0.2)
    else:
        df_st = get_data_around_station(df, metadata['longitude'], metadata['latitude'], 0.2)

    # Create the station
    return fb.FerryBoxStation(stationid, metadata, df_st, varname)


def ferrybox_metadata(stationid):
    return \
        {'VT4': {'name': 'Hvitsten', 'latitude': 59.59, 'longitude': 10.64,
                 'vessel': 'FA', 'vessel_name': 'MS Color Fantasy',
                 'plot_along_latitude': True,
                 'dist': 0.1, 'ybin_dist': 0.01},
         'VT12': {'name': 'Sognesjøen', 'latitude': 60.9804, 'longitude': 4.7568,
                  'vessel': 'TF',
                  'vessel_name': 'MS Trollfjord',
                  'plot_along_latitude': True,
                  'dist': 0.1, 'ybin_dist': 0.01},
         'VT72': {'name': 'Herøyfjorden og VT71:Skinnbrokleia', 'latitude': 62.3066, 'longitude': 5.5877,
                  'vessel': 'TF',
                  'vessel_name': 'MS Trollfjord',
                  'plot_along_latitude': True,
                  'dist': 0.1, 'ybin_dist': 0.01},
         'VT80': {'name': 'Djupfest', 'latitude': 63.76542, 'longitude': 9.52296,
                  'vessel': 'TF',
                  'vessel_name': 'MS Trollfjord',
                  'plot_along_latitude': True, 'dist': 0.15, 'ybin_dist': 0.1},
         'VT45': {'name': 'Valset',
                  'latitude': 63.65006, 'longitude': 9.77012,
                  'vessel': 'TF',
                  'vessel_name': 'MS Trollfjord',
                  'plot_along_latitude': False,
                  'dist': 0.15,
                  'ybin_dist': 0.1},
         'VT22': {'name': 'Biologisk Stasjon', 'latitude': 63.36, 'longitude': 10.2,
                  'vessel': 'TF',
                  'vessel_name': 'MS Trollfjord',
                  'plot_along_latitude': False,
                  'dist': 0.13, 'ybin_dist': 0.01},
         'Trondheimsfjorden': {'name': 'Trondheimsfjorden', 'latitude': 63.46, 'longitude': 10.05,
                               'vessel': 'TF',
                               'vessel_name': 'MS Trollfjord',
                               'plot_along_latitude': False,
                               'dist': 0.05, 'ybin_dist': 0.01},
         'VT23': {'name': 'Trondheimsleia', 'latitude': 63.45737, 'longitude': 8.85324,
                  'vessel': 'TF',
                  'vessel_name': 'MS Trollfjord',
                  'plot_along_latitude': True,
                  'dist': 0.2, 'ybin_dist': 0.01},
         'VT76': {'name': 'Oksebåsneset', 'latitude': 69.82562, 'longitude': 30.11961,
                  'vessel': 'TF',
                  'vessel_name': 'MS Trollfjord',
                  'plot_along_latitude': True,
                  'dist': 0.1, 'ybin_dist': 0.01},
         'VR23': {'name': 'Blodskytodden', 'latitude': 70.4503, 'longitude': 31.0031,
                  'vessel': 'TF',
                  'vessel_name': 'MS Trollfjord',
                  'plot_along_latitude': False,
                  'dist': 0.2, 'ybin_dist': 0.05},
         'VR25': {'name': 'Tanafjorden ytre', 'latitude': 70.98425, 'longitude': 28.78323,
                  'vessel': 'TF',
                  'vessel_name': 'MS Trollfjord',
                  'plot_along_latitude': False,
                  'dist': 0.2, 'ybin_dist': 0.01},
         'VR51': {'name': 'Korsen', 'latitude': 62.0944, 'longitude': 7.0061,
                  'vessel': 'TF',
                  'vessel_name': 'MS Trollfjord',
                  'plot_along_latitude': True,
                  'dist': 0.1, 'ybin_dist': 0.01},
         'VR31': {'name': 'Tilremsfjorden', 'latitude': 65.6009, 'longitude': 12.2354,
                  'vessel': 'TF',
                  'vessel_name': 'MS Trollfjord',
                  'plot_along_latitude': True,
                  'dist': 0.1, 'ybin_dist': 0.01},
         'VT3': {'name': 'Torbjørnskjær', 'latitude': 59.0407, 'longitude': 10.7608,
                 'vessel': 'FA',
                 'vessel_name': 'MS Color Fantasy',
                 'plot_along_latitude': True,
                 'dist': 0.1, 'ybin_dist': 0.01},
         'VT71': {'name': 'Skinnbrokleia', 'latitude': 62.32841, 'longitude': 5.75517,
                  'vessel': 'TF',
                  'vessel_name': 'MS Trollfjord',
                  'plot_along_latitude': True,
                  'dist': 0.1, 'ybin_dist': 0.01},
         'VR54': {'name': 'Straumsfjorden', 'latitude': 69.502, 'longitude': 18.338,
                  'vessel': 'TF',
                  'vessel_name': 'MS Trollfjord',
                  'plot_along_latitude': True,
                  'dist': 0.2, 'ybin_dist': 0.01},
         'Dk1': {'name': 'Steilene', 'latitude': 59.814999, 'longitude': 10.569384,
                 'vessel': 'FA',
                 'vessel_name': 'MS Color Fantasy',
                 'plot_along_latitude': True,
                 'dist': 0.1, 'ybin_dist': 0.01},
         'Im2': {'name': 'Elle', 'latitude': 59.620367, 'longitude': 10.628200,
                 'vessel': 'FA',
                 'vessel_name': 'MS Color Fantasy',
                 'plot_along_latitude': True,
                 'dist': 0.1, 'ybin_dist': 0.01},
         'Oslofjorden': {'name': 'Skagerrak', 'latitude': 59.207, 'longitude': 10.7608,
                         'vessel': 'FA',
                         'vessel_name': 'MS Color Fantasy',
                         'plot_along_latitude': True,
                         'dist': 0.35, 'ybin_dist': 0.05},
         'YO1': {'name': 'Skagerrak', 'latitude': 59.35, 'longitude': 10.7608,
                 'vessel': 'FA',
                 'vessel_name': 'MS Color Fantasy',
                 'plot_along_latitude': True,
                 'dist': 0.35, 'ybin_dist': 0.01},
         'VR4': {'name': 'Kvænangen', 'latitude': 70.1161, 'longitude': 21.0725,
                 'vessel': 'TF',
                 'vessel_name': 'MS Trollfjord',
                 'plot_along_latitude': True,
                 'dist': 0.1, 'ybin_dist': 0.01},
         'VR55': {'name': 'Spilderbukta', 'latitude': 69.9664, 'longitude': 21.6887,
                  'vessel': 'TF',
                  'vessel_name': 'MS Trollfjord',
                  'plot_along_latitude': True,
                  'dist': 0.1, 'ybin_dist': 0.01},
         'VR56': {'name': 'Reisafjorden', 'latitude': 69.9068, 'longitude': 21.0927,
                  'vessel': 'TF',
                  'vessel_name': 'MS Trollfjord',
                  'plot_along_latitude': True,
                  'dist': 0.1, 'ybin_dist': 0.01},
         'VR58': {'name': 'Ullsfjorden', 'latitude': 69.7544, 'longitude': 19.7701,
                  'vessel': 'TF',
                  'vessel_name': 'MS Trollfjord',
                  'plot_along_latitude': True,
                  'dist': 0.2, 'ybin_dist': 0.01},
         'VR59': {'name': 'Sørfjorden', 'latitude': 69.5711, 'longitude': 19.7185,
                  'vessel': 'TF',
                  'vessel_name': 'MS Trollfjord',
                  'plot_along_latitude': True,
                  'dist': 0.1, 'ybin_dist': 0.01},
         'VR7': {'name': 'Langfjordnes', 'latitude': 70.6915, 'longitude': 28.0860,
                 'vessel': 'TF',
                 'vessel_name': 'MS Trollfjord',
                 'plot_along_latitude': True,
                 'dist': 0.1, 'ybin_dist': 0.01},
         'VR21': {'name': 'Bugøynes', 'latitude': 69.9584, 'longitude': 29.8804,
                  'vessel': 'TF',
                  'vessel_name': 'MS Trollfjord',
                  'plot_along_latitude': True,
                  'dist': 0.2, 'ybin_dist': 0.01},
         'VR24': {'name': 'Tanafjorden', 'latitude': 70.7500, 'longitude': 28.3468,
                  'vessel': 'TF',
                  'vessel_name': 'MS Trollfjord',
                  'plot_along_latitude': True,
                  'dist': 0.1, 'ybin_dist': 0.01},
         'VR52': {'name': 'Broemsneset', 'latitude': 64.47, 'longitude': 11.31,
                  'vessel': 'TF',
                  'vessel_name': 'MS Trollfjord',
                  'plot_along_latitude': True,
                  'dist': 0.1, 'ybin_dist': 0.01},
         'VT42': {'name': 'Korsfjorden', 'latitude': 63.4061, 'longitude': 10.041,
                  'vessel': 'TF',
                  'vessel_name': 'MS Trollfjord',
                  'plot_along_latitude': True,
                  'dist': 0.2, 'ybin_dist': 0.01},
         'VR7-VR21-VR24': {'name': 'Barentshavet', 'latitude': 70.0, 'longitude': 30.0,
                           'vessel': 'TF',
                           'vessel_name': 'MS Trollfjord',
                           'plot_along_latitude': False,
                           'dist': 1.8, 'ybin_dist': 0.3},
         }[stationid]


def get_water_sample_data(stationid, df_fb, writer):
    file = "2020/Oekokyst_FB_AQM_extract_2020.xlsx"
    df = pd.read_excel(file, sheet_name="WaterChemistry")
    df_id = df[df["StationCode"] == stationid]

    metadata = ferrybox_metadata(stationid)
    st_lon = metadata['longitude']
    st_lat = metadata['latitude']

    for sample_time, sample_klfa in zip(df_id["SampleDate"], df_id["KlfA µg/l"]):
        sample_time = pd.to_datetime(sample_time)

        fb_time, fb_df = get_data_at_station_and_timestamp(df_fb, st_lon, st_lat, sample_time)
        line = stationid, st_lon, st_lat, sample_time, sample_klfa, fb_time, fb_df["raw_chla_fluorescence"], fb_df[
            "longitude"], fb_df["latitude"]
        writer.writerow(line)


# MAIN
def main():
    substations = ['Dk1', 'Im2', 'YO1',
                   'VT4', 'Oslofjorden', 'VT4',
                   'VT12', 'VT80',
                   'VT45', 'VT22', 'VT23',
                   'VT76', 'VR23', 'VR25',
                   'VR51', 'VR31', 'VT3',
                   'VT71', 'VR54', 'VR4',
                   'VR58',
                   'VR21', 'VT42', 'VR7-VR21-VR24', 'VT72']
    #  'VR55', 'VR59', 'VR7', 'VR24', 'VR52' 'VT72']
    # removed 'VR56' VR55, VR59, VR7, VR24, VR52 'VT72',
    #  substations = ['VT80'] #, 'VT76', 'VR23', 'VR25', 'VT80', 'VT45', 'VT22', 'VT23', 'VT72',
    #                'VT12']  # ,'VT22','VT22 ytre']

    substations = ['Trondheimsfjorden']  # ,'Dk1', 'Im2', 'YO1','VT4']
    substations = ['Dk1', 'Im2', 'YO1', 'VT4', 'Oslofjorden']

    varnames = ['chla_fluorescence','salinity', 'turbidity', 'temperature']
    # varnames = ['chla_fluorescence'] #,'salinity', 'temperature']

    start_date = datetime(2020, 1, 1)
    end_date = datetime(2020, 12, 31)
    first = True
    use_preprocessed_data = True
    ferrybox_calibration = False

    print("Starting contour plot creation for {} stations".format(len(substations)))
    for varname in varnames:
        for stationid in substations:
            metadata = ferrybox_metadata(stationid)
            print('Creating station for {} using vessel {} and variable {}'.format(stationid, metadata['vessel_name'],
                                                                                   varname))

            if not use_preprocessed_data and not ferrybox_calibration:
                tsbdata = get_list_of_available_timeseries_for_vessel(metadata['vessel_name'],
                                                                      metadata['vessel'],
                                                                      start_date,
                                                                      end_date,
                                                                      varname,
                                                                      use_raw=ferrybox_calibration)
            elif use_preprocessed_data and not ferrybox_calibration:
                if metadata['vessel'] == "FA":
                    tsbdata = pd.read_csv("../FBdata/Final_data_2020/FA_corrected.dat", usecols=["time",
                                                                                                 "salinity",
                                                                                                 "inlet_temperature",
                                                                                                 "turbidity_adj",
                                                                                                 "longitude",
                                                                                                 "latitude",
                                                                                                 "chla_fluorescence_c3_adj_corr"])

                    tsbdata.columns = ["time", "salinity", "temperature","turbidity", "longitude", "latitude","chla_fluorescence"]

                elif metadata['vessel'] == "TF":

                    tsbdata = pd.read_csv("../FBdata/Final_data_2020/TF_corrected_v2_05022021.dat", usecols=["time",
                                                                                                             "salinity",
                                                                                                             "inlet_temperature",
                                                                                                             "turbidity_adj",
                                                                                                             "longitude",
                                                                                                             "latitude",

                                                                                                             "raw_chla_fluorescence_c3_adj_corr"])

                    tsbdata.columns = ["time", "salinity", "temperature", "turbidity","longitude", "latitude",
                                       "chla_fluorescence"]

                else:
                    raise Exception("Unable to read data")

            if not ferrybox_calibration:
                station = create_station(stationid, tsbdata, varname)
                station.start_date_jd = date2num(start_date, units=station.refdate, calendar="standard")
                station.end_date_jd = date2num(end_date, units=station.refdate, calendar="standard")

                #  station.extract_calibration_data(varname)
                print('Creating contour plot for {}'.format(stationid))
                station.create_station_contour_plot()
            else:
                if first is True:
                    import csv
                    infile = "ferrybox_calibration_{}{}_to_{}{}.csv".format(start_date.year,
                                                                            start_date.month,
                                                                            end_date.year,
                                                                            end_date.month)
                    if os.path.exists(infile):
                        os.remove(infile)

                    csv_file = open(infile, "a", newline="")

                    writer = csv.writer(csv_file, delimiter=',')
                    header = "StationID", "OBS_LON", "OBS_LAT", "OBS_TIME", \
                             "OBS_KLFA", "FB_TIME", "FB_KLFA", "FB_LON", "FB_LAT"
                    writer.writerow(header)
                    first = False

                get_water_sample_data(stationid, tsbdata, writer)


if __name__ == '__main__':
    main()
