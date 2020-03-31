import matplotlib.pyplot as plt
from matplotlib.transforms import offset_copy

import cartopy.crs as ccrs
import cartopy.io.img_tiles as cimgt
import read_ferrybox
from datetime import datetime


def get_gps_data():
    varnames = ['temperature']

    start_date = datetime(2019, 3, 1)
    end_date = datetime(2019, 6, 29)
    stationid = 'VT3'

    for varname in varnames:
        metadata = read_ferrybox.ferrybox_metadata(stationid)
        print('Creating station for {} using vessel {} and variable {}'.format(stationid, metadata['vessel_name'],
                                                                               varname))
        tsbdata = read_ferrybox.get_list_of_available_timeseries_for_vessel(metadata['vessel_name'],
                                                                            metadata['vessel'],
                                                                            start_date,
                                                                            end_date,
                                                                            varname)

        return tsbdata


def create_map(ds):

    fig = plt.figure()

    # Create a GeoAxes in the tile's projection.
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.Mercator())

    # Limit the extent of the map to a small longitude/latitude range.
    ax.set_extent([9.8, 11.5, 58.7, 60], crs=ccrs.Geodetic())

    # Add the Stamen data at zoom level 8.
  #  ax.add_image(stamen_terrain, 20)
    ax.stock_img()
    ax.coastlines(resolution='50m')
    # Add a marker for the Eyjafjallajökull volcano.
    ax.plot(ds.longitude, ds.latitude, marker='o', color='red', markersize=2,
            alpha=0.7, transform=ccrs.Geodetic())

    # Use the cartopy interface to create a matplotlib transform object
    # for the Geodetic coordinate system. We will use this along with
    # matplotlib's offset_copy function to define a coordinate system which
    # translates the text by 25 pixels to the left.
    geodetic_transform = ccrs.Geodetic()._as_mpl_transform(ax)
    text_transform = offset_copy(geodetic_transform, units='dots', x=-25)

    # Add text 25 pixels to the left of the volcano.
  #  ax.text(-19.613333, 63.62, u'Eyjafjallajökull',
  #          verticalalignment='center', horizontalalignment='right',
  #          transform=text_transform,
  #          bbox=dict(facecolor='sandybrown', alpha=0.5, boxstyle='round'))
    plt.show()


if __name__ == '__main__':
    tsbdata = get_gps_data()
    create_map(tsbdata)
