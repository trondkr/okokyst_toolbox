# The addStationMetadata function needs to be modified if new areas are to be
# plotted using this package
def addStationMeadata(station, CTDConfig, options = None):

    if CTDConfig.conductivityMissing is False and CTDConfig.conductivity_to_salinity is False:
        station.mainHeader = "Ser;Meas;Salinity;Conductivity;Temp;FTU;OptOx;OxMgL;Density;Depth;Date;Time\n"
    elif CTDConfig.conductivityMissing is True and CTDConfig.conductivity_to_salinity is False:
        station.mainHeader = "Ser;Meas;Salinity;Temp;FTU;OptOx;OxMgL;Density;Depth;Date;Time\n"
    else:
        station.mainHeader = "Ser;Meas;Salinity;Temp;FTU;OptOx;OxMgL;Density;Depth;Date;Time\n"

    if options:
        station.mainHeader = "Ser;Meas;Salinity;Conductivity;Temp;FTU;OptOx;OxMgL;Density;S.vel;Depth;Date;Time\n"
    
    if station.survey == "MON":
        if station.name == "NORD1":
            station.header = "STATION;NORD1;MON;67.7638;15.3131\n"
            station.longitude = 15.3131
            station.latitude = 67.76380
        if station.name == "NORD2":
            station.header = "STATION;NORD2;MON;67.6899;15.1517\n"
            station.longitude = 15.1517
            station.latitude = 67.6899
        if station.name == "OFOT1":
            station.header = "STATION;OFOT1;MON;68.4552;17.336\n"
            station.longitude = 17.336
            station.latitude = 68.4552
        if station.name == "OFOT2":
            station.header = "STATION;OFOT2;MON;68.4022;16.9707\n"
            station.longitude = 16.9707
            station.latitude = 68.4022
        if station.name == "OKS1":
            station.header = "STATION;OKS1;MON;68.3951;15.3617\n"
            station.longitude = 15.3617
            station.latitude = 68.3951
        if station.name == "OKS2":
            station.header = "STATION;OKS2;MON;68.340;15.2699\n"
            station.longitude = 15.2699
            station.latitude = 68.340
        if station.name == "SAG1":
            station.header = "STATION;SAG1;MON;67.9538;15.3528\n"
            station.longitude = 15.3528
            station.latitude = 67.9538
        if station.name == "SAG2":
            station.header = "STATION;SAG2;MON;67.97869;15.71398\n"
            station.longitude = 15.71398
            station.latitude = 67.97869
        if station.name == "SJON1":
            station.header = "STATION;SJON1;MON;66.305;12.965\n"
            station.longitude = 12.965
            station.latitude = 66.305
        if station.name == "SJON2":
            station.header = "STATION;SJON2;MON;66.300;13.250\n"
            station.longitude = 13.250
            station.latitude = 66.300
        if station.name == "TYS1":
            station.header = "STATION;TYS1;MON;68.2023;16.1664\n"
            station.longitude = 16.1664
            station.latitude = 68.2023
        if station.name == "TYS2":
            station.header = "STATION;TYS2;MON;68.0898;16.184\n"
            station.longitude = 16.184
            station.latitude = 68.0898
        if station.name == "GLOM1":
            station.header = "STATION;GLOM1;MON;66.8242;13.6244\n"
            station.longitude = 13.6244
            station.latitude = 66.8242
        if station.name == "GLOM2":
            station.header = "STATION;GLOM2;MON;66.8066;13.7995\n"
            station.longitude = 13.7995
            station.latitude = 66.8066
          
    if station.survey == "Hardangerfjorden":
        if station.name == "VT52":
            station.header = "STATION;VT52;Kvinnherad;60.0096;5.954\n"
            station.longitude = 5.954
            station.latitude = 60.0096
        if station.name == "VT53":
            station.header = "STATION;VT53;Tveitneset;60.4014;6.4398\n"
            station.longitude = 6.4398
            station.latitude = 60.4014
        if station.name == "VT74":
            station.header = "STATION;VT74;Maurangsfjorden;60.1061;6.168\n"
            station.longitude = 6.168
            station.latitude = 60.1061
        if station.name == "VT75":
            station.header = "STATION;VT75;Fusafjorden;60.1595;5.5424\n"
            station.longitude = 5.5424
            station.latitude = 60.1595
        if station.name == "VT69":
            station.header = "STATION;VT169;Korsfjorden;60.1788;5.2393\n"
            station.longitude = 5.2393
            station.latitude = 60.1788
        if station.name == "VT70":
            station.header = "STATION;VT170;Bjornafjorden;60.1043;5.4742\n"
            station.longitude = 5.4742
            station.latitude = 60.1043

    if station.survey == "Sognefjorden":
        if station.name == "VT16":
            station.header = "STATION;VT16;Kyrkjeboe;61.14600;5.9527\n"
            station.longitude = 5.9527
            station.latitude = 61.14600
        if station.name == "VT179":
            station.header = "STATION;VT179;Naersnes;60.9963;7.0556\n"
            station.longitude = 7.0556
            station.latitude = 60.9963

    if station.survey == "Soerfjorden":
        if station.name == "SOE72":
            station.header = "STATION;SOE22;SOE22;60.08138;6.538253\n"
            station.longitude = 6.538253
            station.latitude = 60.08138
        if station.name == "Lind1":
            station.header = "STATION;Lind1;Lind1;60.09583;6.541883\n"
            station.longitude = 6.541883
            station.latitude = 60.09583
        if station.name == "S22":
            station.header = "STATION;S22;S22;60.113483;6.553533\n"
            station.longitude = 6.553533
            station.latitude = 60.113483
        if station.name == "S16":
            station.header = "STATION;S16;S16;60.404001;6.435502\n"
            station.longitude = 6.435502
            station.latitude = 60.404001
        if station.name == "SOE10":
            station.header = "STATION;SOE10;SOE10;60.08855;6.543167\n"
            station.longitude = 6.543167
            station.latitude = 60.08855


