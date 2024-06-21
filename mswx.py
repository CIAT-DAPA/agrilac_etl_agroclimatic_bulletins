from netCDF4 import Dataset
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import shutil
import os
from rclone_python import rclone


def generate_day_of_year_range(initial_date, final_date):
    result = []
    current_date = initial_date
    
    while current_date <= final_date:
        result.append(current_date.strftime("%j-%Y"))
        current_date += timedelta(days=1)
    
    return result


var_mswx = {'SWd':'downward_shortwave_radiation',
            'RelHum':'relative_humidity',
            'Tmax':'air_temperature',
            'Tmin':'air_temperature',
            'Wind':'wind_speed'}

def mswx(ini_date, fin_date):
    
    doy_year_range = generate_day_of_year_range(ini_date, fin_date)  
    for doy_year in doy_year_range:
        [doy, year] = doy_year.split('-')
        doy = doy.zfill(3)

        for var in var_mswx.keys():
            folder_name = f'MSWX/{var}'
            if os.path.exists(folder_name):
                shutil.rmtree(folder_name)
            os.mkdir(folder_name)
    
            try:
                rclone.copy(f'GoogleDrive:/MSWX_V100/NRT/{var}/Daily/{year}{doy}.nc', folder_name, ignore_existing=True, args=['--drive-shared-with-me'])
            except:
                rclone.copy(f'GoogleDrive:/MSWX_V100/NRT/{var}/Daily/{year}{doy}.nc', folder_name, ignore_existing=True, args=['--drive-shared-with-me'])



    return True

ini_date = datetime(2024, 4, 8).date()
fin_date = datetime(2024, 4, 18).date()

mswx(ini_date, fin_date)

