import os
import math
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from datetime import datetime, timedelta
import netCDF4 as nc
import numpy as np
from tqdm import tqdm
import pandas as pd
import xarray as xr

"""
Clase que usa Google Drive para la descarga de datos NRT de MSWX
"""


class MSWXData:
    def __init__(self, credentials_file):
        """
        Inicializa la clase con las credenciales para Google Drive.
        """
        self.drive = self.authenticate_drive(credentials_file)

    def authenticate_drive(self, credentials_file):
        """
        Autentica y construye el servicio de Google Drive.
        """
        SCOPES = ['https://www.googleapis.com/auth/drive']
        credentials = service_account.Credentials.from_service_account_file(
            credentials_file, scopes=SCOPES)
        return build('drive', 'v3', credentials=credentials)

    def list_folders_in_folder(self, folder_id, var_mswx):
        """
        Lista las carpetas dentro de una carpeta específica en Google Drive.
        """
        query = f"'{folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed=false"
        results = self.drive.files().list(q=query, supportsAllDrives=True,
                                   includeItemsFromAllDrives=True).execute()
        file_list = results.get('files', [])

        folders = []
        for file in file_list:
            title = file['name']
            if title in var_mswx.keys():
                folders.append({'title': title, 'id': file['id']})

        return folders

    def list_files_in_daily_folder(self, folder_id, ini_date, fin_date, download_folder, folder_title):
        """
        Lista los archivos dentro de la carpeta 'Daily' y los descarga si están dentro del rango de fechas.
        """
        query = f"'{folder_id}' in parents and name = 'Daily' and trashed=false"
        results = self.drive.files().list(q=query, supportsAllDrives=True,
                                   includeItemsFromAllDrives=True).execute()
        daily_folder = results.get('files', [])

        if len(daily_folder) == 1:
            daily_folder_id = daily_folder[0]['id']
            print(
                f"Archivos y carpetas dentro de la carpeta 'Daily' (ID: {daily_folder_id}):")

            daily_files = self.drive.files().list(
                q=f"'{daily_folder_id}' in parents and trashed=false",
                supportsAllDrives=True, includeItemsFromAllDrives=True).execute().get('files', [])

            base_download_dir = os.path.join(download_folder, 'MSWX')
            if not os.path.exists(base_download_dir):
                os.makedirs(base_download_dir)

            date_range = [(ini_date + timedelta(days=i)).strftime('%Y%j')
                           for i in range((fin_date - ini_date).days + 1)]
            date_range.pop()

            total_iterations = len(date_range)
            bar_format = '{l_bar}{bar}| {n:.0f}/{total:.0f} [{elapsed}<{remaining}, {rate_fmt}]'

            with tqdm(total=total_iterations, desc=f"Descargando datos de {folder_title} NRT de MSWX", bar_format=bar_format) as pbar:
                for file in daily_files:
                    file_date_str = file['name'][:7]
                    if file_date_str in date_range and file['name'].endswith('.nc'):
                        variable_name = file['name'].split('_')[0]
                        variable_download_dir = os.path.join(
                            base_download_dir, folder_title)
                        if not os.path.exists(variable_download_dir):
                            os.makedirs(variable_download_dir)

                        self.download_file(
                            file['id'], file['name'], variable_download_dir)
                        pbar.update(1)
        else:
            print(
                f"No se encontró la carpeta 'Daily' dentro de la carpeta con ID: {folder_id}")

    def download_file(self, file_id, file_name, download_folder_path):
        """
        Descarga un archivo de Google Drive.
        """
        request = self.drive.files().get_media(fileId=file_id)
        file_path = os.path.join(download_folder_path, file_name)
        with open(file_path, 'wb') as file:
            downloader = MediaIoBaseDownload(file, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                # if status:
                   # print(f"Descargado {int(status.progress() * 100)}%.")
        # print(f"Descargado archivo: {file_name}")

    def calculate_et0(self, ini_date, fin_date, inputdatapath, outputpath, mask_file_path, pressure=101.325):
        """
        Calcula la evapotranspiración (ET0) utilizando el método de Penman-Monteith para los últimos 10 días.
        """
        date_range = pd.date_range(start=ini_date, end=fin_date - timedelta(days=1))
        dates_list = [date.strftime('%Y%j') for date in date_range]
        doy_list = [int(date.strftime('%j')) for date in date_range]

        os.makedirs(outputpath, exist_ok=True)

        # Archivo de máscara de Honduras
        mask_file = mask_file_path
        nc_file = nc.Dataset(mask_file)
        lat = nc_file.variables["lat"][:]
        lon = nc_file.variables["lon"][:]
        mask = nc_file.variables["mask"][:]

        # Inicializa una lista para almacenar los datos de ET0 con dimensión temporal
        ET0_list = []

        print('Leyendo datos de entrada para cálculo de ET0...')
        total_iterations = len(dates_list) * len(lat)
        bar_format = '{l_bar}{bar}| {n:.0f}/{total:.0f} [{elapsed}<{remaining}, {rate_fmt}]'
        with tqdm(total=total_iterations, desc=f"Calculando ET0", bar_format=bar_format) as pbar:
            for t in dates_list:
                try:
                    tmax_file = nc.Dataset(inputdatapath + "Tmax/" + str(int(t)) + ".nc")
                    tmax = tmax_file.variables["air_temperature"][:]
                    tmax = tmax[0, :, :]

                    tmin_file = nc.Dataset(inputdatapath + "Tmin/" + str(int(t)) + ".nc")
                    tmin = tmin_file.variables["air_temperature"][:]
                    tmin = tmin[0, :, :]

                    temperature = (tmax + tmin) / 2

                    rh_file = nc.Dataset(inputdatapath + "RelHum/" + str(int(t)) + ".nc")
                    humidity = rh_file.variables["relative_humidity"][:]
                    humidity = humidity[0, :, :]

                    wind_file = nc.Dataset(inputdatapath + "Wind/" + str(int(t)) + ".nc")
                    wind_speed = wind_file.variables["wind_speed"][:]
                    wind_speed = wind_speed[0, :, :]

                    swd_file = nc.Dataset(inputdatapath + "SWd/" + str(int(t)) + ".nc")
                    solar_radiation = swd_file.variables["downward_shortwave_radiation"][:]
                    solar_radiation = solar_radiation[0, :, :]
                except FileNotFoundError as e:
                    print(f"Error: No se encontró el archivo {e.filename}. No se podrá calcular para {t}")
                    print(f"Consulte https://www.gloh2o.org/mswx/ para validar los datos")
                    continue


                rows = np.size(lat)
                cols = np.size(lon)
                myET0 = np.empty((rows, cols))
                myET0[:] = np.nan

                doy = doy_list.pop(0)

                for i in range(len(lat)):
                    for j in range(len(lon)):
                        if mask[i, j] == 1:
                            mytas = temperature[i, j]
                            myrh = humidity[i, j]
                            myws = wind_speed[i, j]
                            mysr = solar_radiation[i, j] * 0.0864

                            es = 0.6108 * math.exp(17.27 * mytas / (mytas + 237.3))
                            ea = (myrh / 100) * es

                            delta = 4098 * es / (mytas + 237.3) ** 2
                            gamma = 0.665 * 10 ** (-3) * pressure / 0.622

                            latitude = lat[i]

                            dr = 1 + 0.033 * math.cos(2 * math.pi / 365 * doy)
                            delta_s = 0.409 * math.sin(2 * math.pi / 365 * doy - 1.39)
                            omega_s = math.acos(-math.tan(latitude * math.pi / 180) * math.tan(delta_s))
                            Ra = (24 * 60 / math.pi) * 0.082 * dr * (omega_s * math.sin(latitude * math.pi / 180) * math.sin(
                                delta_s) + math.cos(latitude * math.pi / 180) * math.cos(delta_s) * math.sin(omega_s))

                            Rns = 0.77 * mysr
                            Rnl = 4.903 * 10 ** (-9) * ((mytas + 273.16) ** 4) * (
                                0.34 - 0.14 * math.sqrt(ea)) * (1.35 * (mysr / Ra) - 0.35)

                            Rn = Rns - Rnl
                            G = 0

                            ET0 = (0.408 * delta * (Rn - G) + gamma * (900 / (mytas + 273))
                                * myws * (es - ea)) / (delta + gamma * (1 + 0.34 * myws))

                            myET0[i][j] = ET0
                    pbar.update(1)

                lat_min = 12.5
                lat_max = 16.5
                lon_min = -90
                lon_max = -83

                lon_indices = np.nonzero((lon >= lon_min) & (lon <= lon_max))[0]
                lat_indices = np.nonzero((lat >= lat_min) & (lat <= lat_max))[0]
                myET0 = np.array(myET0)
                region_data = myET0[np.ix_(lat_indices, lon_indices)]
                ET0_list.append(region_data)

        # Convertir la lista de ET0 a un array numpy con una dimensión de tiempo
        ET0_array = np.array(ET0_list)

        # Ajustar date_range para que coincida con los datos disponibles
        valid_date_range = date_range[:len(ET0_array)]

        # Crear un DataArray de xarray
        ET0_da = xr.DataArray(
            ET0_array,
            dims=['time', 'lat', 'lon'],
            coords={
                'time': valid_date_range,
                'lat': lat[lat_indices],
                'lon': lon[lon_indices]
            },
            name='ET0'
        )

        # Sumar los valores a lo largo de la dimensión temporal
        ET0_sum = ET0_da.sum(dim='time')

        # Crear un Dataset de xarray
        ds = xr.Dataset({'ET0': ET0_da, 'ET0_sum': ET0_sum})

        # Asignar atributos
        ds['ET0'].attrs['units'] = 'mm/day'
        ds['ET0'].attrs['long_name'] = 'FAO-56 Penman-Monteith reference evapotranspiration'
        ds['ET0_sum'].attrs['units'] = 'mm/day'
        ds['ET0_sum'].attrs['long_name'] = 'Sum of FAO-56 Penman-Monteith reference evapotranspiration over time'
        ds.attrs['author'] = 'CGIAR-AgriLAC, CENAOS-COPECO'
        ds.attrs['originaldata'] = 'MSWX Near Real Time'
        ds.attrs['created'] = datetime.now().strftime('%Y-%m-%d')

        # Guardar el Dataset a un archivo .nc
        output_file = os.path.join(outputpath, "ET0_Honduras.nc")
        ds.to_netcdf(output_file, mode='w', format='NETCDF4')
        print("ETC save on: ", outputpath)
        

