# NOTES for Økokyst 2019

# Update
SJON1 - remove oxygen last part of 2019 with white fields? New sensor as 2019 very different from previous years
SJON1 - remove/add white box during summer of 2018 when we have little data 

SJON2 - remove/add white box during summer of 2018 when we have little data 

OKS2 - big difference in oxygen between 2013-2015 compared to 2016-2018
OKS1 - add white bar to hide oxygen and oxygen saturation for may/june 2019
OKS1 - Also big difference in oxygen between 2013-2015 and 2019 comopared to 2017-2018. Sensor change - what to do?

TYS2 - add white bar to hide oxygen and oxygen saturation for may/june 2019
TYS1 - add white bar to hide oxygen and oxygen saturation for may/june 2019
SAG2 - add white bar to hide oxygen and oxygen saturation for may/june 2019. Weird values stuck sensor?
SAG1 - add white bar to hide oxygen and oxygen saturation for may/june 2019. Weird values stuck sensor?
NORD2 - add white bar to hide oxygen and oxygen saturation for may/june 2019. Weird values stuck sensor?
NORD1 - add white bar to hide oxygen and oxygen saturation for may/june 2019. Weird values stuck sensor?

OFOT2 and NORD2 very similar are they close in location?

### Sognefjorden
Error in files April 2019 (29.04.2019) for VT16 and VT179 where oygen and oxygen saturation both fixed for long periods 
at constant values. Set to -999 to mask out.

Error in file June 16 2019 (16.06.2019) for VT179 where oygen and oxygen saturation both fixed for long periods 
at constant values. Set to -999 to mask out.

VT69 deepest depth varies from 42 to 75 m

VT74 december 2018 has weird pattern below 100 m  - repeating / osciallting
5;1899;36.803;8.347;0.12;48.53;4.51;27.963;123.3400;17.12.2018;15.26.56
5;1900;36.797;8.330;0.12;39.19;3.64;27.980;124.8000;17.12.2018;15.26.58
5;1901;36.789;8.315;0.13;36.65;3.41;27.993;126.2400;17.12.2018;15.27.00
5;1902;36.788;8.310;0.13;44.53;4.14;28.003;127.7100;17.12.2018;15.27.02
5;1903;36.786;8.304;0.29;54.53;5.07;28.013;129.1800;17.12.2018;15.27.04
5;1904;36.784;8.297;0.14;55.74;5.18;28.024;130.5900;17.12.2018;15.27.06
5;1905;36.770;8.277;0.13;47.90;4.45;28.037;131.9200;17.12.2018;15.27.08
5;1906;36.760;8.252;0.13;38.84;3.61;28.058;133.3100;17.12.2018;15.27.10
5;1907;36.752;8.237;0.15;36.96;3.44;28.071;134.6000;17.12.2018;15.27.12
5;1908;36.742;8.222;0.15;44.25;4.12;28.083;136.1000;17.12.2018;15.27.14
5;1909;36.744;8.219;0.14;53.01;4.93;28.093;137.5900;17.12.2018;15.27.16
5;1910;36.743;8.216;0.14;56.60;5.27;28.101;139.0000;17.12.2018;15.27.18



### MON
#### SJON2 oxygen and FTU wrong (constant) for 31.5.2019

Removed and replaced with -999
Ser	Meas	Sal.	Temp	FTU	OptOx	OxMgL	Density	Depth	Date	Time
SJON2	1891	34.9	6.899	0	0.32	0.021	30.231	623.8077266512032	31.05.2019	9.2.0
SJON2	1892	34.9	6.898	0	0.33	0.021	30.228	622.820619400996	31.05.2019	9.2.0
SJON2	1893	34.9	6.898	0	0.33	0.021	30.224	621.8335074353057	31.05.2019	9.2.0
SJON2	1894	34.9	6.897	0	0.32	0.021	30.22	620.8463907539945	31.05.2019	9.2.0
SJON2	1895	34.9	6.897	0	0.33	0.021	30.215	619.8592693569238	31.05.2019	9.2.0
SJON2	1896	34.9	6.897	0	0.33	0.021	30.208	618.8721432439564	31.05.2019	9.2.0
SJON2	1897	34.9	6.896	0	0.32	0.021	30.203	617.885012414954	31.05.2019	9.2.0
SJON2	1898	34.9	6.896	0	0.32	0.021	30.202	616.8978768697787	31.05.2019	9.2.0
SJON2	1899	34.9	6.896	0	0.32	0.021	30.2	615.9107366082922	31.05.2019	9.2.0
SJON2	1900	34.9	6.895	0	0.33	0.021	30.193	614.9235916303569	31.05.2019	9.2.0
 
SJON1 for May and June seems weird. Almost constant values or decreasing from bottom to surface. Wrong with sensor?

Ser	Meas	Sal.	Temp	FTU	OptOx	OxMgL	Density	Depth	Date	Time
SJON1	1132	35.17	6.759	-999	76.04	6.153	29.31	372.93047197336233	28.06.2019	9.26.46
SJON1	1133	35.13	6.755	-999	75.74	5.999	29.275	371.94216288167036	28.06.2019	9.26.46
SJON1	1134	35.15	6.755	-999	76	6.083	29.286	370.953849039311	28.06.2019	9.26.46
SJON1	1135	35.15	6.755	-999	76.31	6.125	29.282	369.96553044614524	28.06.2019	9.26.46
SJON1	1136	35.15	6.755	-999	76.53	6.188	29.277	368.9772071020339	28.06.2019	9.26.46
SJON1	1137	35.14	6.754	-999	76.67	6.216	29.265	367.9888790068379	28.06.2019	9.26.46
SJON1	1138	35.14	6.753	-999	76.84	6.23	29.261	367.00054616041825	28.06.2019	9.26.46
SJON1	1139	35.14	6.753	-999	76.91	6.244	29.257	366.01220856263564	28.06.2019	9.26.46
SJON1	1140	35.13	6.752	-999	77.04	6.349	29.244	365.0238662133509	28.06.2019	9.26.46
SJON1	1141	35.13	6.753	-999	77.2	6.405	29.24	364.0355191124252	28.06.2019	9.26.46
SJON1	1142	35.14	6.752	-999	77.31	6.489	29.243	363.04716725971906	28.06.2019	9.26.46
SJON1	1143	35.13	6.751	-999	77.44	6.524	29.231	362.05881065509357	28.06.2019	9.26.46
SJON1	1144	35.13	6.751	-999	77.51	6.405	29.226	361.07044929840947	28.06.2019	9.26.46
SJON1	1145	35.14	6.751	-999	77.61	6.426	29.23	360.08208318952774	28.06.2019	9.26.46
SJON1	1146	35.14	6.751	-999	77.69	6.426	29.226	359.09371232830915	28.06.2019	9.26.46

#### Same goes for SAG2 and SAG1 and TYS2 and NORD2

Wrong with FTU and oxygen in OFOT2
Ser	Meas	Sal.	Temp	FTU	OptOx	OxMgL	Density	Depth	Date	Time
OFOT2	1123	35.04	7.262	0	0.33	0.021	29.446	441.05159292730826	29.05.2019	8.49.39
OFOT2	1124	35.03	7.261	0	0.33	0.021	29.434	440.06374733497057	29.05.2019	8.49.39
OFOT2	1125	35.04	7.261	0	0.33	0.021	29.434	439.0758970022359	29.05.2019	8.49.39
OFOT2	1126	35.03	7.26	0	0.33	0.021	29.427	438.08804192896514	29.05.2019	8.49.39
OFOT2	1127	35.03	7.26	0	0.33	0.021	29.422	437.10018211501983	29.05.2019	8.49.39
OFOT2	1128	35.03	7.259	0	0.32	0.021	29.417	436.112317560261	29.05.2019	8.49.39
OFOT2	1129	35.03	7.259	0	0.33	0.021	29.413	435.12444826455	29.05.2019	8.49.39
OFOT2	1130	35.03	7.259	0	0.33	0.021	29.408	434.13657422774793	29.05.2019	8.49.39
OFOT2	1131	35.03	7.259	0	0.32	0.021	29.401	433.14869544971606	29.05.2019	8.49.39
OFOT2	1132	35.03	7.26	0	0.32	0.021	29.399	432.16081193031573	29.05.2019	8.49.39
OFOT2	1133	35.03	7.26	0	0.32	0.021	29.396	431.1729236694079	29.05.2019	8.49.39
OFOT2	1134	35.03	7.259	0	0.33	0.021	29.393	430.18503066685383	29.05.2019	8.49.39
OFOT2	1135	35.03	7.259	0	0.32	0.021	29.385	429.1971329225147	29.05.2019	8.49.39
OFOT2	1136	35.03	7.259	0	0.32	0.021	29.378	428.20923043625174	29.05.2019	8.49.39
OFOT2	1137	35.03	7.26	0	0.33	0.021	29.372	427.2213232079261	29.05.2019	8.49.39
OFOT2	1138	35.03	7.26	0	0.33	0.021	29.371	426.23341123739897	29.05.2019	8.49.39
OFOT2	1139	35.03	7.259	0	0.33	0.021	29.371	425.2454945245316	29.05.2019	8.49.39
OFOT2	1140	35.03	7.259	0	0.33	0.021	29.36	424.257573069185	29.05.2019	8.49.39
OFOT2	1141	35.03	7.258	0	0.33	0.021	29.359	423.2696468712205	29.05.2019	8.49.39
OFOT2	1142	35.03	7.259	0	0.33	0.021	29.351	422.28171593049905	29.05.2019	8.49.39

Fixed by removing and setting to -999

### SØRFJORDEN
Weird value in oxygen for 2018.7 S22 