
import os
import re
import glob

encoding = "ISO-8859-1"
#main_folder = r'C:\Users\ELP\OneDrive - NIVA\Documents\Projects\OKOKYST\ØKOKYST_NORDSJØENNORD_CTD\Sognefjorden'
main_folder = r'C:\Users\ELP\OneDrive - NIVA\Documents\Projects\OKOKYST\ØKOKYST_NORDSJØENNORD_CTD\Hardangerfjorden'
folders = os.listdir(main_folder)
all_files = glob.glob(main_folder + '/**/*.txt', recursive=True)
for file in all_files:
    if bool(re.search('2020', file)):
        with open(file, 'r') as f:
            # read a list of lines into data
            data = f.readlines()

        print (file)
        data[1] = 'Ser;Meas;Salinity;Conductivity;Temp;FTU;OptOx;OxMlL;Density;Depth;Date;Time\n'

        with open(file, 'w') as file:
            file.writelines(data)


