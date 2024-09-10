import os, json
import xarray as xr
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import timedelta, datetime
import cftime
import geopandas as gpd
import rasterio
from shapely.geometry import mapping
import matplotlib.dates as mdates

class Tools():

    def plot_nc_file(self, file_path, variable_name, save_path, lon_dim='lon', lat_dim='lat', time_dim='time', region_dim='region'):
        """
        Función para graficar el promedio diario y la desviación estándar de una variable en un archivo NetCDF y guardar la figura por región.

        Parámetros:
        - file_path: Ruta al archivo NetCDF.
        - variable_name: Nombre de la variable a graficar.
        - save_path: Ruta donde se guardarán las figuras.
        - lon_dim: Nombre de la dimensión de longitud (por defecto 'lon').
        - lat_dim: Nombre de la dimensión de latitud (por defecto 'lat').
        - time_dim: Nombre de la dimensión de tiempo (por defecto 'time').
        - region_dim: Nombre de la dimensión de región (por defecto 'region').
        """
        # Abrir el archivo NetCDF
        dataset = xr.open_dataset(file_path)

        # Verificar si la variable existe en el conjunto de datos
        if variable_name not in dataset:
            raise ValueError(f"La variable '{variable_name}' no se encuentra en el archivo.")

        # Iterar sobre cada región
        for region in dataset[region_dim].values:
            # Filtrar los datos por la región actual
            region_data = dataset.sel({region_dim: region})

            # Calcular el promedio diario y la desviación estándar para la región actual
            daily_mean = region_data[variable_name].mean(dim=[lon_dim, lat_dim])
            daily_std = region_data[variable_name].std(dim=[lon_dim, lat_dim])

            # Extraer los datos de tiempo
            time = dataset[time_dim].values

            # Convertir el tiempo de cftime.DatetimeGregorian a pandas datetime si es necesario
            if isinstance(time[0], cftime.DatetimeGregorian):
                time = np.array([np.datetime64(date.strftime('%Y-%m-%d')) for date in time])

            # Obtener las unidades de la variable
            units = dataset[variable_name].attrs.get('units', 'unidades')

            # Nombres en español
            dict = {
                "air_temperature": "temperatura del aire",
                "precipitation": "precipitación",
                "mm/day": "mm/día",
            }
            nombre_variable_final = dict[variable_name] if variable_name in dict else variable_name
            nombre_unidades_final = dict[units] if units in dict else units

            # Si la variable es 'precipitation', se grafica un gráfico de barras
            if variable_name == "precipitation":
                # Graficar para la región actual
                plt.figure(figsize=(10, 6))
                plt.bar(time, daily_mean, yerr=daily_std, capsize=5, color='skyblue', label=f'{nombre_variable_final} promedio')
                plt.xlabel('Días')
                plt.ylabel(f'{nombre_variable_final} ({nombre_unidades_final})')
                plt.title(f'Promedio diario de {nombre_variable_final} con desviación estándar en la región {region}')
            else:
                # Graficar para la región actual con rango de incertidumbre
                upper_bound = daily_mean + daily_std
                lower_bound = np.where((daily_mean - daily_std < 0) & (variable_name == 'precipitation'), 0, daily_mean - daily_std)
                
                plt.figure(figsize=(10, 6))
                plt.plot(time, daily_mean, label=f'{nombre_variable_final} promedio', color='green')
                plt.fill_between(time, lower_bound, upper_bound, color='green', alpha=0.3, label='Rango de incertidumbre')
                plt.xlabel('Días')
                plt.ylabel(f'{nombre_variable_final} ({nombre_unidades_final})')
                plt.title(f'Promedio diario de {nombre_variable_final} con rango de incertidumbre en la región {region}')

            # Ajustar las etiquetas de fechas
            plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=1))
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            plt.gcf().autofmt_xdate()  # Rotar las etiquetas de fecha para mayor claridad

            plt.legend()
            plt.grid(True)

            # Guardar la figura
            plt.savefig(f"{save_path}{variable_name}_{region}.png")
            plt.close()


    def country_crop(self, file_to_be_cropped, mask_file, output_file):
        
        file_to_be_cropped = xr.open_dataset(file_to_be_cropped)
        mask_file = mask_file
        ds_mask = xr.open_dataset(mask_file)

        # Aplicar la máscara a los datos globales
        ds_global_honduras = file_to_be_cropped.where(ds_mask['mask'] == 1, drop=True)
        ds_global_honduras.to_netcdf(output_file)

        ds_mask.close()

    
    def regions_crop(self, file_to_be_cropped, shapefile, output_file, name_column):
        # Abre el archivo netCDF
        ds = xr.open_dataset(file_to_be_cropped, decode_times=False)

        # Asegúrate de que el dataset tenga las coordenadas necesarias para rioxarray
        if 'crs' not in ds.attrs:
            ds.rio.write_crs("EPSG:4326", inplace=True)  # Ajusta el EPSG según sea necesario

        # Obtener las dimensiones del archivo NetCDF
        lon_dim = 'lon' if 'lon' in ds.dims else 'x'
        lat_dim = 'lat' if 'lat' in ds.dims else 'y'
        time_dim = 'time' if 'time' in ds.dims else None

        # Configura las dimensiones espaciales
        ds = ds.rio.set_spatial_dims(x_dim=lon_dim, y_dim=lat_dim, inplace=True)

        # Abre el shapefile usando geopandas
        regions = gpd.read_file(shapefile)

        # Asegúrate de que el shapefile y el netCDF tengan el mismo sistema de coordenadas
        if ds.rio.crs != regions.crs:
            regions = regions.to_crs(ds.rio.crs)

        # Obtener la primera variable de datos del dataset
        data_var = list(ds.data_vars.keys())[0]

        # Crear una lista para almacenar los datasets recortados
        clipped_datasets = []
        # Crear una lista para almacenar los nombres de las regiones
        region_names = []

        # Obtener las unidades de la variable original
        units = ds[data_var].attrs.get('units', 'unidades no definidas')

        # Iterar sobre cada región y recortar el dataset
        for idx, region in regions.iterrows():
            geometry = [mapping(region.geometry)]

            # Crear la máscara de la región
            mask = ds.rio.clip(geometry, drop=False)

            # Asegurarse de que la máscara tenga las mismas dimensiones que el dataset original
            mask = mask[data_var].notnull().astype(int)

            # Crear una variable para la región con un nombre único basado en el nombre de la columna
            region_name = region[name_column]
            region_masked = xr.where(mask, ds[data_var], float('nan'))

            # Añadir el atributo de unidades al dataset recortado
            region_masked.attrs['units'] = units

            # Añadir el dataset recortado a la lista
            clipped_datasets.append(region_masked)
            region_names.append(region_name)

        # Combinar todos los datasets recortados en uno solo
        combined_ds = xr.concat(clipped_datasets, dim='region')
        combined_ds = combined_ds.assign_coords(region=region_names)

        # Asignar las coordenadas de tiempo si existen en el dataset original
        if time_dim:
            combined_ds = combined_ds.assign_coords({time_dim: ds[time_dim].values})
            combined_ds[time_dim].attrs.update(ds[time_dim].attrs)  # Preservar los atributos de tiempo

        # Mantener los atributos del archivo original
        combined_ds.attrs.update(ds.attrs)

        # Guardar el resultado en un nuevo archivo netCDF
        combined_ds.to_netcdf(output_file)

        return output_file

    def merge_files(self, start_date, end_date, data_folder, output_folder, file_type, units, variable_name='data'):
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
                        latitudes = src.transform[5] + src.transform[4] * np.arange(src.height)
                        longitudes = src.transform[2] + src.transform[0] * np.arange(src.width)
                        ds = xr.DataArray(
                            data,
                            dims=('lat', 'lon'),
                            coords={
                                'lat': latitudes,
                                'lon': longitudes
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
        combined_ds[variable_name].attrs['units'] = units
        
        # Guardar el dataset combinado a un archivo .nc
        combined_ds.to_netcdf(output_folder, mode='w', format='NETCDF4')

        # Cerrar los datasets
        for ds in datasets:
            ds.close()


        
    def translate_julian_dates(self, directorio):
        # Obtener una lista de los archivos en el directorio
        archivos = os.listdir(directorio)
        
        # Crear una lista para almacenar los nuevos nombres de archivos
        nuevos_nombres = []
        
        # Iterar sobre los archivos
        for archivo in archivos:
            # Asumimos que los nombres de los archivos tienen el formato '2024099.ext'
            nombre, extension = os.path.splitext(archivo)
            
            if len(nombre) == 7 and nombre.isdigit():
                año = int(nombre[:4])
                dia_juliano = int(nombre[4:])
                
                # Convertir el día juliano a una fecha
                fecha = datetime.strptime(f'{año}{dia_juliano:03}', '%Y%j').strftime('%Y-%m-%d')
                
                # Crear el nuevo nombre de archivo
                nuevo_nombre = f'{fecha}{extension}'
                
                # Añadir el nuevo nombre a la lista
                nuevos_nombres.append(nuevo_nombre)
                
                # Renombrar el archivo en el sistema de archivos
                os.rename(os.path.join(directorio, archivo), os.path.join(directorio, nuevo_nombre))
            else:
                nuevos_nombres.append(archivo)
        
        return nuevos_nombres

    def calculate_daily_mean_per_municipality(self, shapefile_path, netcdf_file, variable_name, region_column, municipality_column, units, column_name):
        """
        Función para calcular el promedio diario de una variable por municipio y escribir los resultados en un archivo CSV.

        Parámetros:
        - shapefile_path: Ruta al shapefile de municipios.
        - netcdf_file: Ruta al archivo NetCDF.
        - variable_name: Nombre de la variable en el archivo NetCDF.
        - output_csv: Ruta donde se guardará el archivo CSV de salida.
        - region_column: Nombre de la columna en el shapefile que contiene la región.
        - municipality_column: Nombre de la columna en el shapefile que contiene el nombre del municipio.
        - units: Unidades de la variable.
        """
        # Cargar el shapefile de municipios
        municipalities = gpd.read_file(shapefile_path)

        # Abrir el archivo NetCDF
        dataset = xr.open_dataset(netcdf_file)

        # Verificar si la variable existe en el conjunto de datos
        if variable_name not in dataset:
            raise ValueError(f"La variable '{variable_name}' no se encuentra en el archivo NetCDF.")

        # Inicializar una lista para almacenar los resultados
        results = []

        # Obtener las dimensiones del archivo NetCDF
        lon_dim = 'lon' if 'lon' in dataset.dims else 'x'
        lat_dim = 'lat' if 'lat' in dataset.dims else 'y'

        # Iterar sobre cada municipio y calcular el promedio diario
        for index, municipality in municipalities.iterrows():
            # Obtener el polígono del municipio
            municipality_polygon = municipality['geometry']

            # Extraer los datos de la variable para el polígono del municipio
            variable_data = dataset[variable_name].sel({lon_dim: municipality_polygon.centroid.x, lat_dim: municipality_polygon.centroid.y}, method='nearest')

            string_to_append = "avg"

           # Verificar si la variable es 'precipitation'
            if variable_name == "precipitation" or variable_name == "precipitationCal":
                # Calcular el acumulado diario
                daily_value = variable_data.sum(dim='time').values
                string_to_append = "acc"
            else:
                # Calcular el promedio diario
                daily_value = variable_data.mean(dim='time').values

            # Agregar los resultados a la lista
            results.append({
                'region': municipality[region_column],
                'municipio': municipality[municipality_column],
                f'{column_name}_{units}_{string_to_append}': daily_value
            })

        # Crear un DataFrame con los resultados y escribirlo en un archivo CSV
        df = pd.DataFrame(results)
        #df.to_csv(output_csv, index=False)
        return df


    def create_gcc_json(self, file_path):
        """
        Función para crear el archivo credentials.json usando las variables de entorno. Este archivo es necesario para el proceso
        de MSWX.
        Parámetros:
        - file_path: Ruta donde se escribirá el archivo json.
        """
        gcc_variables = [
            "GCC_TYPE",
            "GCC_PROJECT_ID",
            "GCC_PRIVATE_KEY_ID",
            "GCC_PRIVATE_KEY",
            "GCC_CLIENT_EMAIL",
            "GCC_CLIENT_ID",
            "GCC_AUTH_URI",
            "GCC_TOKEN_URI",
            "GCC_AUTH_PROVIDER_X509_CERT_URL",
            "GCC_CLIENT_X509_CERT_URL",
            "GCC_UNIVERSE_DOMAIN"
        ]
        
        gcc_data = {}
        
        try:
            for var in gcc_variables:
                value = os.getenv(var)
                if value is None:
                    raise ValueError(f"La variable de entorno {var} no está definida.")
                gcc_data[var.lower()] = value
                
            # Renaming keys to match the required JSON structure
            gcc_data = {
                "type": gcc_data["gcc_type"],
                "project_id": gcc_data["gcc_project_id"],
                "private_key_id": gcc_data["gcc_private_key_id"],
                "private_key": gcc_data["gcc_private_key"],
                "client_email": gcc_data["gcc_client_email"],
                "client_id": gcc_data["gcc_client_id"],
                "auth_uri": gcc_data["gcc_auth_uri"],
                "token_uri": gcc_data["gcc_token_uri"],
                "auth_provider_x509_cert_url": gcc_data["gcc_auth_provider_x509_cert_url"],
                "client_x509_cert_url": gcc_data["gcc_client_x509_cert_url"],
                "universe_domain": gcc_data["gcc_universe_domain"]
            }
            # Write JSON data to file with correct newline handling
            json_str = json.dumps(gcc_data, indent=4, ensure_ascii=False)
            json_str = json_str.replace('\\\\n', '\\n')  # Correct newline characters

            with open(file_path, 'w') as json_file:
                json_file.write(json_str)
        
            print(f"Archivo credentials.json creado con éxito: {file_path}")
        
        except ValueError as e:
            print(e)
            print("Debe declarar todas las variables de entorno.")
