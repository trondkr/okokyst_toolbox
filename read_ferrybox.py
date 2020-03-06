from datetime import datetime
from netCDF4 import date2num
from pyniva import Vessel, TimeSeries, token2header

import ferryBoxStationClass as fb

__author__ = 'Trond Kristiansen'
__email__ = 'trond.kristiansen@niva.no'
__created__ = datetime(2019, 1, 22)
__modified__ = datetime(2020, 3, 6)
__version__ = "1.0"
__status__ = "Development"


def setup_connection_to_nivadb():
    token = '../FBdata/NIVA_TOKEN/nivatestdev-7dee310e019d.json'
    return token2header(token)


def get_list_of_available_timeseries_for_vessel(vessel_name, vessel_abbreviation, start_date, end_date, variable):
    header = setup_connection_to_nivadb()
    meta_host = "https://api-test.niva.no/v1/metaflow/"
    tsb_host = "https://api-test.niva.no/v1/tsb/"

    vessel_list = [v for v in Vessel.list(meta_host, header=header) if hasattr(v, "imo")]

    for v in vessel_list:
        if v.name == vessel_name:
            print("Fetching data for vessel {} ({})".format(v.name, vessel_abbreviation))

            # Get signals the vessel
            signals = v.get_all_tseries(meta_host, header=header)
          #  for s in signals:
          #      print(s.path)

            if variable == 'temperature':
                db_path = "{}/ferrybox/CTD/TEMPERATURE".format(vessel_abbreviation)
            elif variable == 'salinity':
                db_path = "{}/ferrybox/CTD/SALINITY".format(vessel_abbreviation)
            elif variable == 'chla_fluorescence':
                db_path = "{}/ferrybox/CHLA_FLUORESCENCE/BIOF_CORR_AND_CALIB".format(vessel_abbreviation)
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
                                                      noffill=True)
    return data


def get_data_around_station(df, st_lon, st_lat, dist):
    # https://stackoverflow.com/questions/21415661/logical-operators-for-boolean-indexing-in-pandas
    # Filter out the longitude and latitudes surrounding the station lat/lon

    return df[
        (st_lat - dist < df['latitude']) & (df['latitude'] < st_lat + dist) & (st_lon - 2 * dist < df['longitude']) & (
                df['longitude'] < st_lon + 2 * dist)]


def create_station(stationid, df, varname, dist):
    metadata = ferrybox_metadata(stationid)

    # Get the data for the station
    df_st = get_data_around_station(df, metadata['longitude'], metadata['latitude'], dist)

    # Create the station 
    return fb.FerryBoxStation(stationid, metadata, df_st, varname)


def ferrybox_metadata(staionid):
    return \
        {'VT4': {'name': 'Hvitsten', 'latitude': 59.59, 'longitude': 10.64,
                 'vessel': 'FA', 'vessel_name': 'MS Color Fantasy'},
         'VT12': {'name': 'Sognesjøen', 'latitude': 60.9804, 'longitude': 4.7568,
                  'vessel': 'TF',
                  'vessel_name': 'MS Trollfjord'},
         'VT72': {'name': 'Herøyfjorden og VT71:Skinnbrokleia', 'latitude': 62.3066, 'longitude': 5.5877,
                  'vessel': 'TF',
                  'vessel_name': 'MS Trollfjord'},
         'VT80': {'name': 'Djupfest', 'latitude': 63.76542, 'longitude': 9.52296,
                  'vessel': 'TF',
                  'vessel_name': 'MS Trollfjord'},
         'VT45': {'name': 'Valset', 'latitude': 63.65006, 'longitude': 9.77012,
                  'vessel': 'TF',
                  'vessel_name': 'MS Trollfjord'},
         'VT22': {'name': 'Biologisk Stasjon', 'latitude': 63.46, 'longitude': 10.3,
                  'vessel': 'TF',
                  'vessel_name': 'MS Trollfjord'},
         'VT23': {'name': 'Trondheimsleia', 'latitude': 63.45737, 'longitude': 8.85324,
                  'vessel': 'TF',
                  'vessel_name': 'MS Trollfjord'},
         'VT76': {'name': 'Oksebåsneset', 'latitude': 69.82562, 'longitude': 30.11961,
                  'vessel': 'TF',
                  'vessel_name': 'MS Trollfjord'},
         'VR23': {'name': 'Blodskytodden', 'latitude': 70.4503, 'longitude': 31.0031,
                  'vessel': 'TF',
                  'vessel_name': 'MS Trollfjord'},
         'VR25': {'name': 'Tanafjorden ytre', 'latitude': 70.98425, 'longitude': 28.78323,
                  'vessel': 'TF',
                  'vessel_name': 'MS Trollfjord'},
         'VR51': {'name': 'Korsen', 'latitude': 62.0944, 'longitude': 7.0061,
                  'vessel': 'TF',
                  'vessel_name': 'MS Trollfjord'},
         'VR31': {'name': 'Tilremsfjorden', 'latitude': 65.6009, 'longitude': 12.2354,
                  'vessel': 'TF',
                  'vessel_name': 'MS Trollfjord'},
         'VT3': {'name': 'Torbjørnskjær', 'latitude': 59.0407, 'longitude': 10.7608,
                 'vessel': 'FA',
                 'vessel_name': 'MS Color Fantasy'},
         'VT71': {'name': 'Skinnbrokleia', 'latitude': 62.32841, 'longitude': 5.75517,
                  'vessel': 'TF',
                  'vessel_name': 'MS Trollfjord'},
         'VR54': {'name': 'Straumsfjorden', 'latitude': 69.502, 'longitude': 18.338,
                  'vessel': 'TF',
                  'vessel_name': 'MS Trollfjord'},
         'Dk1': {'name': 'Steilene', 'latitude': 59.814999, 'longitude': 10.569384,
                 'vessel': 'FA',
                 'vessel_name': 'MS Color Fantasy'},
         'Im2': {'name': 'Elle', 'latitude': 59.620367, 'longitude': 10.628200,
                 'vessel': 'FA',
                 'vessel_name': 'MS Color Fantasy'},
         'VT81': {'name': 'Alvenes', 'latitude': 67.2743, 'longitude': 14.9770,
                  'vessel': 'TF',
                  'vessel_name': 'MS Trollfjord'},
         'VT82': {'name': 'Setså', 'latitude': 67.1709, 'longitude': 15.4461,
                  'vessel': 'TF',
                  'vessel_name': 'MS Trollfjord'},
         'VT3X': {'name': 'Skagerrak', 'latitude': 59.0407, 'longitude': 10.7608,
                  'vessel': 'FA',
                  'vessel_name': 'MS Color Fantasy'}
         }[stationid]


# MAIN 

substations = ['VT4', 'VT12', 'VT72', 'VT80', 'VT45', 'VT22', 'VT23', 'VT76', 'VR23', 'VR25', 'VR51', 'VR31', 'VT3',
               'VT71', 'VR54','VT81','VT82','VR54']
substations = ['Dk1','Im2']

varnames = ['temperature', 'salinity', 'cdom_fluorescence', 'turbidity', 'chla_fluorescence']
varnames = ['temperature']
dist = 0.1

start_date = datetime(2013, 1, 1)
end_date = datetime(2013, 12, 31)
# start_date=datetime(2018,1,1)
# end_date=datetime(2018,12,31)

# NO EDIT

for varname in varnames:
    for stationid in substations:
        if stationid in ['VT3X']:
            dist = 0.5
            print("WARNING: Extending the search area to cover much of Skagerrak. dist={}".format(dist))

        metadata = ferrybox_metadata(stationid)
        print('Creating station for {} using vessel {} and variable {}'.format(stationid, metadata['vessel_name'],
                                                                               varname))
        tsbdata = get_list_of_available_timeseries_for_vessel(metadata['vessel_name'],
                                                              metadata['vessel'],
                                                              start_date,
                                                              end_date,
                                                              varname)

        station = create_station(stationid, tsbdata, varname, dist)
        station.start_date_jd = date2num(start_date, units=station.refdate, calendar="standard")
        station.end_date_jd = date2num(end_date, units=station.refdate, calendar="standard")

        print('Creating contour plot for {}'.format(stationid))
        station.create_station_contour_plot()
