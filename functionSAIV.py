import bz2
import gzip
import linecache
import re
import warnings
import zipfile
from datetime import datetime
from io import StringIO
from pathlib import Path
import dateutil.parser

import numpy as np
import pandas as pd
from netCDF4 import date2num, num2date
import string

def _basename(fname):
    """Return file name without path."""
    if not isinstance(fname, Path):
        fname = Path(fname)
    path, name, ext = fname.parent, fname.stem, fname.suffix
    return path, name, ext


def _normalize_names(name):
    name = name.strip()
    name = name.strip("*")
    return name


def _open_compressed(fname):
    extension = fname.suffix.lower()
    if extension in [".gzip", ".gz"]:
        cfile = gzip.open(str(fname))
    elif extension == ".bz2":
        cfile = bz2.BZ2File(str(fname))
    elif extension == ".zip":
        # NOTE: Zip format may contain more than one file in the archive
        # (similar to tar), here we assume that there is just one file per
        # zipfile!  Also, we ask for the name because it can be different from
        # the zipfile file!!
        zfile = zipfile.ZipFile(str(fname))
        name = zfile.namelist()[0]
        cfile = zfile.open(name)
    else:
        raise ValueError(
            "Unrecognized file extension. Expected .gzip, .bz2, or .zip, got {}".format(
                extension
            )
        )
    contents = cfile.read()
    cfile.close()
    return contents


def _read_file(fname):
    if not isinstance(fname, Path):
        fname = Path(fname).resolve()

    extension = fname.suffix.lower()
    if extension in [".gzip", ".gz", ".bz2", ".zip"]:
        contents = _open_compressed(fname)
    elif extension in [".cnv", ".edf", ".txt", ".ros", ".btl"]:
        contents = fname.read_bytes()
    else:
        raise ValueError(
            f"Unrecognized file extension. Expected .cnv, .edf, .txt, .ros, or .btl got {extension}"
        )
    # Read as bytes but we need to return strings for the parsers.
    text = contents.decode(encoding="utf-8", errors="replace")
    return StringIO(text)


def _parse_seabird(lines, ftype="cnv"):
    # Initialize variables.
    lon = lat = time = None, None, None
    skiprows = 0

    metadata = {}
    header, config, names = [], [], []
    for k, line in enumerate(lines):
        line = line.strip()

        # Only cnv has columns names, for bottle files we will use the variable row.
        if ftype == "cnv":
            if "# name" in line:
                name, unit = line.split("=")[1].split(":")
                name, unit = list(map(_normalize_names, (name, unit)))
                names.append(name)

        # Seabird headers starts with *.
        if line.startswith("*"):
            header.append(line)

        # Seabird configuration starts with #.
        if line.startswith("#"):
            config.append(line)

        # NMEA position and time.
        if "NMEA Latitude" in line:
            hemisphere = line[-1]
            lat = line.strip(hemisphere).split("=")[1].strip()
            lat = np.float_(lat.split())
            if hemisphere == "S":
                lat = -(lat[0] + lat[1] / 60.0)
            elif hemisphere == "N":
                lat = lat[0] + lat[1] / 60.0
            else:
                raise ValueError("Latitude not recognized.")
        if "NMEA Longitude" in line:
            hemisphere = line[-1]
            lon = line.strip(hemisphere).split("=")[1].strip()
            lon = np.float_(lon.split())
            if hemisphere == "W":
                lon = -(lon[0] + lon[1] / 60.0)
            elif hemisphere == "E":
                lon = lon[0] + lon[1] / 60.0
            else:
                raise ValueError("Latitude not recognized.")
        if "NMEA UTC (Time)" in line:
            time = line.split("=")[-1].strip()
            # Should use some fuzzy datetime parser to make this more robust.
            time = datetime.strptime(time, "%b %d %Y %H:%M:%S")

        # cnv file header ends with *END* while
        if ftype == "cnv":
            if line == "*END*":
                skiprows = k + 1
                break
        else:  # btl.
            # There is no *END* like in a .cnv file, skip two after header info.
            if not (line.startswith("*") | line.startswith("#")):
                # Fix commonly occurring problem when Sbeox.* exists in the file
                # the name is concatenated to previous parameter
                # example:
                #   CStarAt0Sbeox0Mm/Kg to CStarAt0 Sbeox0Mm/Kg (really two different params)
                line = re.sub(r"(\S)Sbeox", "\\1 Sbeox", line)

                names = line.split()
                skiprows = k + 2
                break
    if ftype == "btl":
        # Capture stat names column.
        names.append("Statistic")
    metadata.update(
        {
            "header": "\n".join(header),
            "config": "\n".join(config),
            "names": names,
            "skiprows": skiprows,
            "time": time,
            "lon": lon,
            "lat": lat,
        }
    )
    return metadata


def from_bl(fname):
    """Read Seabird bottle-trip (bl) file

    Example
    -------
    >>> from pathlib import Path
    >>> import ctd
    >>> data_path = Path(__file__).parents[1].joinpath("tests", "data")
    >>> df = ctd.from_bl(str(data_path.joinpath('bl', 'bottletest.bl')))
    >>> df._metadata["time_of_reset"]
    datetime.datetime(2018, 6, 25, 20, 8, 55)

    """
    df = pd.read_csv(
        fname,
        skiprows=2,
        parse_dates=[1],
        index_col=0,
        names=["bottle_number", "time", "startscan", "endscan"],
    )
    df._metadata = {
        "time_of_reset": pd.to_datetime(
            linecache.getline(str(fname), 2)[6:-1]
        ).to_pydatetime()
    }
    return df


def from_btl(fname):
    """
    DataFrame constructor to open Seabird CTD BTL-ASCII format.

    Examples
    --------
    >>> from pathlib import Path
    >>> import ctd
    >>> data_path = Path(__file__).parents[1].joinpath("tests", "data")
    >>> bottles = ctd.from_btl(data_path.joinpath('btl', 'bottletest.btl'))

    """
    f = _read_file(fname)
    metadata = _parse_seabird(f.readlines(), ftype="btl")

    f.seek(0)

    df = pd.read_fwf(
        f,
        header=None,
        index_col=False,
        names=metadata["names"],
        parse_dates=False,
        skiprows=metadata["skiprows"],
    )
    f.close()

    # At this point the data frame is not correctly lined up (multiple rows
    # for avg, std, min, max or just avg, std, etc).
    # Also needs date,time,and bottle number to be converted to one per line.

    # Get row types, see what you have: avg, std, min, max or just avg, std.
    rowtypes = df[df.columns[-1]].unique()
    # Get times and dates which occur on second line of each bottle.
    dates = df.iloc[:: len(rowtypes), 1].reset_index(drop=True)
    times = df.iloc[1:: len(rowtypes), 1].reset_index(drop=True)
    datetimes = dates + " " + times

    # Fill the Date column with datetimes.
    df.loc[:: len(rowtypes), "Date"] = datetimes.values
    df.loc[1:: len(rowtypes), "Date"] = datetimes.values

    # Fill missing rows.
    df["Bottle"] = df["Bottle"].fillna(method="ffill")
    df["Date"] = df["Date"].fillna(method="ffill")

    df["Statistic"] = df["Statistic"].str.replace(r"\(|\)", "")  # (avg) to avg

    name = _basename(fname)[1]

    dtypes = {
        "bpos": int,
        "pumps": bool,
        "flag": bool,
        "Bottle": int,
        "Scan": int,
        "Statistic": str,
        "Date": str,
    }
    for column in df.columns:
        if column in dtypes:
            df[column] = df[column].astype(dtypes[column])
        else:
            try:
                df[column] = df[column].astype(float)
            except ValueError:
                warnings.warn("Could not convert %s to float." % column)

    df["Date"] = pd.to_datetime(df["Date"])
    metadata["name"] = str(name)
    setattr(df, "_metadata", metadata)
    return df

def try_parsing_date(stringtime):
    for fmt in ('%d.%m.%Y %H:%M:%S','%Y-%m-%d %H.%M.%S', '%d.%m.%Y %H.%M.%S', '%d/%m/%Y %H.%M.%S',\
                '%Y-%m-%d %H:%M:%S', '%d/%m/%Y %H:%M:%S'):
        try:
            return datetime.strptime(stringtime, fmt)
        except ValueError:
            pass
    raise ValueError('no valid date format found')

def _parse_saiv(lines, sep=";", ftype="saiv"):
    metadata = {}
    header, config, names = [], [], []
    counter = 0
    separator = ';'

    for k, line in enumerate(lines):
        line = line.strip()

        if counter == 0:
            lat = line.split(separator)[3].strip()
            lon = line.split(separator)[4].strip()
            station = line.split(separator)[1]
            serial = line.split(separator)[0]

        if counter == 1:
            header.append(line)
            col = line.split(separator)
            names = col
            for i,name in enumerate(names):
                if name=="Time":
                    time_index=i
                if name=="Date":
                    date_index=i
            if time_index is None and date_index is None:
                print("ERROR - unable to find time and date columns in header")
                break
        if counter == 2:
            l = line.split(separator)
            time = l[date_index] + ' ' + l[time_index].strip().replace(".",":")
            try:
                self.try_parsing_date(time)
            except:
                print(f"Could not find proper time format for {time}")
            skiprows = counter

        if counter > 2:
            break
        counter += 1
    config = "SAIV"
    metadata.update(
        {
            "header": "\n".join(header),
            "config": "\n".join(config),
            "names": names,
            "skiprows": skiprows,
            "time": time,
            "lon": lon,
            "lat": lat,
        })
    return metadata


def calculate_julianday(d):
    # Calculate the julian date from the current datetime format (Norwegian time and date format)
    return date2num(d, units="days since 1948-01-01 00:00:00", calendar="standard")

def pressure_to_depth(P, lat):
    """Compute depth from pressure and latitude
    Usage: depth(P, lat)
    Input:
        P = Pressure,     [dbar]
        lat = Latitude    [deg]
    Output:
        Depth             [m]
    Algorithm: UNESCO 1983
    """

    # Use numpy for trigonometry if present
    from numpy import sin, pi

    a1 =  9.72659
    a2 = -2.2512e-5
    a3 =  2.279e-10
    a4 = -1.82e-15

    b  =  1.092e-6

    g0 =  9.780318
    g1 =  5.2788e-3
    g2 =  2.36e-5

    rad = pi / 180.

    X = sin(lat*rad)
    X = X*X
    grav = g0 * (1.0 + (g1 + g2*X)*X) + b*P
    nom = (a1 + (a2 + (a3 + a4*P)*P)*P)*P

    return nom / grav

def from_saiv(fname):
    """
    DataFrame constructor to open SAIV ASCII format. This file is modified by adding the
    header containing longitude and latitude. E.g.

    STATION;VT52;Kvinnherad;60.0096;5.954
    Ser;Meas;Sal.;Temp;T (FTU);Opt;Density;Depth(u);Date;Time;;

    Examples
    --------
    >>> from ctd import DataFrame
    >>> cast = DataFrame.from_saiv("/Users/trondkr/Dropbox/NIVA/OKOKYST_2017/OKOKYST_NS_Nord_Leon/t01_saiv_leon/SAIV_208_SN1380_VT79.txt")
    >>> fig, ax = cast['Temp'].plot()
    >>> _ = ax.axis([20, 24, 19, 0])
    >>> ax.grid(True)
    """
    separator = ';'
    f = _read_file(fname)
    metadata = _parse_saiv(f.readlines(), sep=separator, ftype="saiv")

    f.seek(0)
    skiprows = 2

    df = pd.read_table(f, header=None, index_col=False, names=metadata["names"],
                       skiprows=metadata["skiprows"], sep=separator)

    f.close()

    # Get row types, see what you have: avg, std, min, max or just avg, std.
    rowtypes = df[df.columns[-1]].unique()
    datetimes = df["Date"].str.strip() + " " + df["Time"].str.replace(".",":", regex=True)
    df["Date"] = pd.to_datetime(datetimes)

    df['Depth2'] = df['Depth']

    # Fill the Date column with datetimes.
    df.set_index("Depth", drop=True, inplace=True)
    df.index.name = "Depth [m]"
    name = _basename(fname)[1]

    setattr(df, "_metadata", metadata)

    df['JD'] = df.apply(lambda row: calculate_julianday(row['Date']), axis=1)
    df['dz/dtM'] = abs(df['Depth2'].astype('float64') - df.shift()['Depth2'].astype('float64')) / (abs(
        df['JD'].astype('float64') - df.shift()['JD'].astype(
            'float64')) * 3600 * 24.)  # cast.apply(lambda row: calculate_sinking_velocity(row,cast), axis=1)

    return df, metadata


def from_edf(fname):
    """
    DataFrame constructor to open XBT EDF ASCII format.

    Examples
    --------
    >>> from pathlib import Path
    >>> import ctd
    >>> data_path = Path(__file__).parents[1].joinpath("tests", "data")
    >>> cast = ctd.from_edf(data_path.joinpath('XBT.EDF.gz'))
    >>> ax = cast['temperature'].plot_cast()

    """
    f = _read_file(fname)
    header, names = [], []
    for k, line in enumerate(f.readlines()):
        line = line.strip()
        if line.startswith("Serial Number"):
            serial = line.strip().split(":")[1].strip()
        elif line.startswith("Latitude"):
            try:
                hemisphere = line[-1]
                lat = line.strip(hemisphere).split(":")[1].strip()
                lat = np.float_(lat.split())
                if hemisphere == "S":
                    lat = -(lat[0] + lat[1] / 60.0)
                elif hemisphere == "N":
                    lat = lat[0] + lat[1] / 60.0
            except (IndexError, ValueError):
                lat = None
        elif line.startswith("Longitude"):
            try:
                hemisphere = line[-1]
                lon = line.strip(hemisphere).split(":")[1].strip()
                lon = np.float_(lon.split())
                if hemisphere == "W":
                    lon = -(lon[0] + lon[1] / 60.0)
                elif hemisphere == "E":
                    lon = lon[0] + lon[1] / 60.0
            except (IndexError, ValueError):
                lon = None
        else:
            header.append(line)
            if line.startswith("Field"):
                col, unit = [l.strip().lower() for l in line.split(":")]
                names.append(unit.split()[0])
        if line == "// Data":
            skiprows = k + 1
            break

    f.seek(0)
    df = pd.read_csv(
        f,
        header=None,
        index_col=None,
        names=names,
        skiprows=skiprows,
        delim_whitespace=True,
    )
    f.close()

    df.set_index("depth", drop=True, inplace=True)
    df.index.name = "Depth [m]"
    name = _basename(fname)[1]

    metadata = {
        "lon": lon,
        "lat": lat,
        "name": str(name),
        "header": "\n".join(header),
        "serial": serial,
    }
    setattr(df, "_metadata", metadata)
    return df


def from_cnv(fname):
    """
    DataFrame constructor to open Seabird CTD CNV-ASCII format.

    Examples
    --------
    >>> from pathlib import Path
    >>> import ctd
    >>> data_path = Path(__file__).parents[1].joinpath("tests", "data")
    >>> cast = ctd.from_cnv(data_path.joinpath('CTD_big.cnv.bz2'))
    >>> downcast, upcast = cast.split()
    >>> ax = downcast['t090C'].plot_cast()

    """
    f = _read_file(fname)
    metadata = _parse_seabird(f.readlines(), ftype="cnv")

    f.seek(0)
    df = pd.read_fwf(
        f,
        header=None,
        index_col=None,
        names=metadata["names"],
        skiprows=metadata["skiprows"],
        delim_whitespace=True,
        widths=[11] * len(metadata["names"]),
    )
    f.close()

    key_set = False
    prkeys = ["prDM", "prdM", "pr"]
    for prkey in prkeys:
        try:
            df.set_index(prkey, drop=True, inplace=True)
            key_set = True
        except KeyError:
            continue
    if not key_set:
        raise KeyError(
            f"Could not find pressure field (supported names are {prkeys})."
        )
    df.index.name = "Pressure [dbar]"

    name = _basename(fname)[1]

    dtypes = {"bpos": int, "pumps": bool, "flag": bool}
    for column in df.columns:
        if column in dtypes:
            df[column] = df[column].astype(dtypes[column])
        else:
            try:
                df[column] = df[column].astype(float)
            except ValueError:
                warnings.warn("Could not convert %s to float." % column)

    metadata["name"] = str(name)
    setattr(df, "_metadata", metadata)
    return df


def from_fsi(fname, skiprows=9):
    """
    DataFrame constructor to open Falmouth Scientific, Inc. (FSI) CTD
    ASCII format.

    Examples
    --------
    >>> from pathlib import Path
    >>> import ctd
    >>> data_path = Path(__file__).parents[1].joinpath("tests", "data")
    >>> cast = ctd.from_fsi(data_path.joinpath('FSI.txt.gz'))
    >>> downcast, upcast = cast.split()
    >>> ax = downcast['TEMP'].plot_cast()

    """
    f = _read_file(fname)
    df = pd.read_csv(
        f,
        header="infer",
        index_col=None,
        skiprows=skiprows,
        dtype=float,
        delim_whitespace=True,
    )
    f.close()

    df.set_index("PRES", drop=True, inplace=True)
    df.index.name = "Pressure [dbar]"
    metadata = {"name": str(fname)}
    setattr(df, "_metadata", metadata)
    return df


def rosette_summary(fname):
    """
    Make a BTL (bottle) file from a ROS (bottle log) file.

    More control for the averaging process and at which step we want to
    perform this averaging eliminating the need to read the data into SBE
    Software again after pre-processing.
    NOTE: Do not run LoopEdit on the upcast!

    Examples
    --------
    >>> from pathlib import Path
    >>> import ctd
    >>> data_path = Path(__file__).parents[1].joinpath("tests", "data")
    >>> fname = data_path.joinpath('CTD/g01l01s01.ros')
    >>> ros = ctd.rosette_summary(fname)
    >>> ros = ros.groupby(ros.index).mean()
    >>> ros.pressure.values.astype(int)
    array([835, 806, 705, 604, 503, 404, 303, 201, 151, 100,  51,   1])

    """
    ros = from_cnv(fname)
    ros["pressure"] = ros.index.values.astype(float)
    ros["nbf"] = ros["nbf"].astype(int)
    ros.set_index("nbf", drop=True, inplace=True, verify_integrity=False)
    return ros
