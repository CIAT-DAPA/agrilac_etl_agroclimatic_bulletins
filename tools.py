import os
import xarray as xr
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import timedelta, datetime
import cftime
import geopandas as gpd
import rasterio
from shapely.geometry import mapping
import cartopy.crs as ccrs
import cartopy.feature as cfeature

class Tools():

    def plot_nc_file(file_path, variable_name, lon_dim='lon', lat_dim='lat', time_dim='time'):
        """
        Función para graficar el promedio diario y la desviación estándar de una variable en un archivo NetCDF.
        
        Parámetros:
        - file_path: Ruta al archivo NetCDF.
        - variable_name: Nombre de la variable a graficar.
        - lon_dim: Nombre de la dimensión de longitud (por defecto 'lon').
        - lat_dim: Nombre de la dimensión de latitud (por defecto 'lat').
        - time_dim: Nombre de la dimensión de tiempo (por defecto 'time').
        """
        # Abrir el archivo NetCDF
        dataset = xr.open_dataset(file_path)
        
        # Verificar si la variable existe en el conjunto de datos
        if variable_name not in dataset:
            raise ValueError(f"La variable '{variable_name}' no se encuentra en el archivo.")
        
        # Calcular el promedio diario y la desviación estándar
        daily_mean = dataset[variable_name].mean(dim=[lon_dim, lat_dim])
        daily_std = dataset[variable_name].std(dim=[lon_dim, lat_dim])
        
        # Extraer los datos de tiempo
        time = dataset[time_dim].values
        
        # Convertir el tiempo de cftime.DatetimeGregorian a pandas datetime
        if isinstance(time[0], cftime.DatetimeGregorian):
            time = np.array([np.datetime64(date.strftime('%Y-%m-%d')) for date in time])
        
        # Calcular los rangos de incertidumbre
        upper_bound = daily_mean + daily_std
        lower_bound = daily_mean - daily_std
        
        # Obtener las unidades de la variable
        units = dataset[variable_name].attrs.get('units', 'unidades')
        
        # Graficar
        plt.figure(figsize=(10, 6))
        plt.plot(time, daily_mean, label=f'{variable_name} promedio', color='green')
        plt.fill_between(time, lower_bound, upper_bound, color='green', alpha=0.3, label='Rango de incertidumbre')
        plt.xlabel('Días')
        plt.ylabel(f'{variable_name} ({units})')
        plt.title(f'Promedio diario de {variable_name} con rango de incertidumbre')
        plt.legend()
        plt.grid(True)
        plt.show()

    def regions_crop(file_to_be_cropped, shapefile, output_file):
        # Abre el archivo netCDF
        ds = xr.open_dataset(file_to_be_cropped)

        # Asegúrate de que el dataset tenga las coordenadas necesarias para rioxarray
        if 'crs' not in ds.attrs:
            ds.rio.write_crs("EPSG:4326", inplace=True)  # Ajusta el EPSG según sea necesario

        # Configura las dimensiones espaciales
        ds = ds.rio.set_spatial_dims(x_dim='lon', y_dim='lat', inplace=True)

        # Abre el shapefile usando geopandas
        regions = gpd.read_file(shapefile)

        # Asegúrate de que el shapefile y el netCDF tengan el mismo sistema de coordenadas
        if ds.rio.crs != regions.crs:
            regions = regions.to_crs(ds.rio.crs)

        # Recorta el dataset usando las geometrías del shapefile
        geometries = [mapping(geom) for geom in regions.geometry]
        clipped_ds = ds.rio.clip(geometries, regions.crs, drop=True)

        # Guardar el resultado en un nuevo archivo netCDF
        clipped_ds.to_netcdf(output_file)

        return output_file

    def merge_files(start_date, end_date, data_folder, output_folder, file_type, variable_name='data'):
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
            filename = f'{data_folder}{year}-{month}-{day}.{file_type}'

            # Verificar si el archivo existe
            if os.path.exists(filename):
                if file_type == 'nc':
                    # Abrir el archivo .nc y agregarlo a la lista de datasets
                    ds = xr.open_dataset(filename)
                    datasets.append(ds)
                    times.append(date)
                elif file_type == 'tif':
                    # Abrir el archivo .tif y agregarlo a la lista de datasets
                    with rasterio.open(filename) as src:
                        data = src.read(1)  # Leer la primera banda
                        ds = xr.DataArray(
                            data,
                            dims=('y', 'x'),
                            coords={
                                'y': src.transform[5] + src.transform[4] * np.arange(src.height),
                                'x': src.transform[2] + src.transform[0] * np.arange(src.width)
                            },
                            name=variable_name
                        ).to_dataset(name=variable_name)  # Convertir DataArray a Dataset
                        datasets.append(ds)
                        times.append(date)
                else:
                    print(f'Unsupported file type: {file_type}')
                    return
            else:
                print(f'File not found: {filename}')

        # Combinar todos los datasets en uno solo a lo largo de la dimensión 'time'
        combined_ds = xr.concat(datasets, dim='time')
        combined_ds['time'] = times  # Asignar la coordenada de tiempo

        # Asignar las unidades a la variable
        combined_ds[variable_name].attrs['units'] = 'mm/day'
        combined_ds.attrs['units'] = 'mm/day'

        # Guardar el dataset combinado a un archivo .nc
        combined_ds.to_netcdf(output_folder, mode='w', format='NETCDF4')

        # Cerrar los datasets
        for ds in datasets:
            ds.close()


#regions_crop("./outputs/MSWX/2024jun28/ET0.nc", "./mask_honduras/regions_shapefile/hnd_admbnda_adm1_sinit_20161005.shp", "./outputs/MSWX/ET0_Honduras_regions.nc")
# ini_date = datetime(2017, 8, 15).date()
# fin_date = datetime(2017, 8, 25).date()
# #merge_files(ini_date, fin_date, "./forecast_data/RAINNC/RAINNC_", "./outputs/forecast/RAINNC_forecast_Honduras.nc", "tif", variable_name='precipitation')
# #merge_files(ini_date, fin_date, "./forecast_data/ET0/ET0_", "./outputs/forecast/ET0_forecast_Honduras.nc", "tif", variable_name='ET0')
# # Ejemplo de uso
# plot_nc_file("./outputs/IMERG/IMERG_Honduras.nc", "precipitationCal")
# plot_nc_file("./outputs/MSWX/2024jun28/ET0_Honduras.nc", "ET0")
#plot_nc_file("./outputs/forecast/ET0_forecast_Honduras.nc", "ET0", lon_dim='x', lat_dim='y', time_dim='time')
#plot_nc_file("./outputs/forecast/RAINNC_forecast_Honduras.nc", "precipitation", lon_dim='x', lat_dim='y', time_dim='time')
