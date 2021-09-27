
import os
import re
import glob
import matplotlib.pyplot as plt
import pandas as pd

encoding = "ISO-8859-1"
main_folder = r'C:\Users\ELP\OneDrive - NIVA\Documents\Projects\OKOKYST\ØKOKYST_NORDSJØENNORD_CTD\Sognefjorden'
#main_folder = r'C:\Users\ELP\OneDrive - NIVA\Documents\Projects\OKOKYST\ØKOKYST_NORDSJØENNORD_CTD\Hardangerfjorden'
folders = os.listdir(main_folder)
all_files = glob.glob(main_folder + '/**/*.txt', recursive=True)

#fig, axs = plt.subplots(30)
n = 0
for file in all_files[:35]:
    if bool(re.search('2020', file)):
        df = pd.read_csv(file,sep = ';', skiprows=1)
        plt.plot(df.OxMlL,df.Depth*-1)
        n = n + 1
        '''with open(file, 'r') as f:
            # read a list of lines into data
            data = f.readlines()

        print (file)
        data[1] = 'Ser;Meas;Salinity;Conductivity;Temp;FTU;OptOx;OxMgL;Density;Depth;Date;Time\n'

        with open(file, 'w') as file:
            file.writelines(data)'''
plt.show()






