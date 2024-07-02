from urllib import request
from netCDF4 import Dataset
import pandas as pd
from datetime import datetime, timedelta
import os
import xarray as xr

class IMERGData:

    def generate_month_year_range(self,initial_date, final_date):
        result = []
        current_date = initial_date
        while current_date <= final_date:
            result.append(current_date.strftime("%m-%Y"))
            current_date += timedelta(days=32)
            current_date = current_date.replace(day=1)
        return result


    def imerg(self, ini_date, fin_date):
        username = "deguzman"
        password = "Daniqwert54321."
        redirectHandler = request.HTTPRedirectHandler()
        cookieProcessor = request.HTTPCookieProcessor()
        passwordManager = request.HTTPPasswordMgrWithDefaultRealm()
        passwordManager.add_password(
            None, "https://urs.earthdata.nasa.gov", username, password)
        authHandler = request.HTTPBasicAuthHandler(passwordManager)
        opener = request.build_opener(
            redirectHandler, cookieProcessor, authHandler)
        request.install_opener(opener)

        month_year_range = self.generate_month_year_range(ini_date, fin_date)
    
        days_array = [str(day).zfill(2) for day in range(1, 32)]

        for i, month_year in enumerate(month_year_range):

            [month, year] = month_year.split('-')

            if i == 0:
                days = [str(day).zfill(2)
                        for day in range(ini_date.day, fin_date.day)]
            elif i == len(month_year_range) - 1:
                days = [str(day).zfill(2) for day in range(1, fin_date.day + 1)]
            else:
                days = days_array

            for day in days:
                try:
                    url = f'https://gpm1.gesdisc.eosdis.nasa.gov/opendap/hyrax/GPM_L3/GPM_3IMERGDL.06/{year}/{month}/3B-DAY-L.MS.MRG.3IMERG.{year}{month}{day}-S000000-E235959.V06.nc4.nc4?precipitationCal[0:1:0][0:1:3599][0:1:1799]'
                    filename = f'./imerg_data/IMERG_LATE{year}{month}{day}.nc'
                    request.urlretrieve(url, filename)

                    imerg_nc = Dataset(filename)

                    if 'lat' not in imerg_nc.dimensions or 'lon' not in imerg_nc.dimensions:
                        print(f'lat/lon not found in {filename}')
                        imerg_nc.close()
                        os.remove(filename)
                        continue

                    if 'precipitationCal' not in imerg_nc.variables:
                        print(f'precipitationCal not found in {filename}')
                        imerg_nc.close()
                        os.remove(filename)
                        continue

                except Exception as e:
                    print(e)
        
        #Merging, cropping and writting file
        self.merge_nc_files(ini_date, fin_date)

    def merge_nc_files(self, start_date, end_date):
        # Generar la lista de fechas
        date_range = pd.date_range(start=start_date, end=end_date - timedelta(days=1))

        # Crear una lista para almacenar los datasets
        datasets = []
        times = []

        for date in date_range:
            year = date.year
            month = str(date.month).zfill(2)
            day = str(date.day).zfill(2)

            # Construir el nombre del archivo
            filename = f'./imerg_data/IMERG_LATE{year}{month}{day}.nc'

            # Verificar si el archivo existe
            if os.path.exists(filename):
                # Abrir el archivo y agregarlo a la lista de datasets
                ds = xr.open_dataset(filename)
                datasets.append(ds)
                times.append(date)
            else:
                print(f'File not found: {filename}')

        # Combinar todos los datasets en uno solo a lo largo de la dimensión 'time'
        combined_ds = xr.concat(datasets, dim='time')
        combined_ds['time'] = times  # Asignar la coordenada de tiempo

        # Asignar las unidades a la variable
        combined_ds['precipitationCal'].attrs['units'] = 'mm/day'
        combined_ds.attrs['units'] = 'mm/day'

        mask_file = './mask_honduras/mask_mswx_hnd.nc4'
        ds_mask = xr.open_dataset(mask_file)

        # Aplicar la máscara a los datos globales
        ds_global_honduras = combined_ds.where(ds_mask['mask'] == 1, drop=True)
        ds_global_honduras.to_netcdf('./imerg_data/IMERG_Honduras.nc')

        # Cerrar los datasets
        for ds in datasets:
            ds.close()
        ds_mask.close()



