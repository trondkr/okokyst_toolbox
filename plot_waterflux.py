
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Data downloaded from sildre.nve.no using the Beta service
# https://beta-sildre.nve.no/station/72.77.0?1001v1=1440&1000v1=1440&1003v1=1440&17v1=1440
# Values are daily averaged for flux of water (Vannføring m3/s)
#
# Plots used in Økokyst Nordsjøen Nord reporting for NIVA#
# Trond Kristiansen, 23.02.2021

col_name1="Tidspunkt"
col_name2="Vannføring (m³/s)"

rivers=["Flaam bru (72.77.0)", "Holen (50.1.0)", "Seimsfoss (45.4.0)"]
river_plotname=["Flaam_bru_2017_2020.png", "Holen_2017_2020.png", "Seimsfoss_2017_2020.png"]
river_files=["72.77.0-Vannføring-dogn-v1.csv", "50.1.0-Vannføring-dogn-v1.csv", "45.4.0-Vannføring-dogn-v1.csv"]

for river, plotname , file in zip(rivers, river_plotname, river_files):
    df = pd.read_csv('../Vannfoering/{}'.format(file), sep=';', skiprows=1)

    df["Date"] = pd.to_datetime(df[col_name1], format='%Y-%m-%d %H:%M:%S')
    df = df.sort_values("Date")

    df = df.set_index(pd.DatetimeIndex(df["Date"]))
    fig, ax = plt.subplots(1, 1, figsize = (14, 6))

    ax.title.set_text(river)

    df2 = pd.DataFrame({'Vannfoering_m3_s': df[col_name2]}, index=pd.DatetimeIndex(df['Date']), dtype=float)

    df2=df2.resample("1D").mean()
    ax.title.set_text(river)
    sns.lineplot(data=df2,x="Date",y="Vannfoering_m3_s")
    ax.set_xlabel('Dato')
    ax.set_ylabel('Vannføring (m$^3$/s)')

    plt.savefig(plotname, dpi=300)
    plt.show()