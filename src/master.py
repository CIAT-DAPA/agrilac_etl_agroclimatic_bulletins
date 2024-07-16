from datetime import datetime, timedelta
from imerg_data import IMERGData
from mswx_data import MSWXData
from tools import Tools
import os, sys

class Master:
    #Today date for use in folders
    TODAY = datetime.now().date().strftime('%Y%m%d')
    INI_DATE = ""
    FIN_DATE = ""
    WORSKPACE = ""
    CONFIG_FOLDER = ""
    INPUTS_FOLDER = ""
    OUTPUTS_FOLDER = ""
    INPUTS_DOWNLOADED_DATA=""
    INPUTS_FORECAST_DATA=""
    HONDURAS_SHP_PATH=""
    HONDURAS_REGIONS_PATH=""
    HONDURAS_MUNICIPALITIES_PATH=""


    def __init__(self, central_date, workspace_path=None, path_shp_crop_honduras=None, 
                 path_shp_crop_honduras_regions=None, path_shp_crop_honduras_municipalities=None, path_forecast_files=None):
        """
        Inicializa la clase con los parametros del usuario, así como también la construcción de los diferentes directorios.
        """
        self.WORKSPACE = workspace_path if workspace_path is not None else "../workspace/"
        self.CONFIG_FOLDER = os.path.join(self.WORKSPACE, "config/")
        self.INPUTS_FOLDER = os.path.join(self.WORKSPACE, "inputs/")
        self.OUTPUTS_FOLDER = os.path.join(self.WORKSPACE, "outputs/")
        self.INPUTS_DOWNLOADED_DATA = os.path.join(self.INPUTS_FOLDER, "downloaded_data/")
        self.INPUTS_FORECAST_DATA = path_forecast_files if path_forecast_files is not None else os.path.join(self.INPUTS_FOLDER, "forecast_data/")
        self.HONDURAS_SHP_PATH = path_shp_crop_honduras if path_shp_crop_honduras is not None else os.path.join(self.CONFIG_FOLDER, "mask_honduras/")
        self.HONDURAS_REGIONS_PATH = path_shp_crop_honduras_regions if path_shp_crop_honduras_regions is not None else os.path.join(self.HONDURAS_SHP_PATH, "regions_shapefile/")
        self.HONDURAS_MUNICIPALITIES_PATH = path_shp_crop_honduras_municipalities if path_shp_crop_honduras_municipalities is not None else os.path.join(self.HONDURAS_SHP_PATH, "municipalities_shapefile/")

        self.FIN_DATE = datetime.strptime(central_date, "%Y-%m-%d").date()
        self.INI_DATE = self.FIN_DATE - timedelta(days=10)

        print("fecha de inicio: ", self.INI_DATE)
        print("fecha de fin: ",self.FIN_DATE)
    

    """
    MSXW data process
    """
    def run_mswx_data_proccess(self, ini_date, fin_date):
        credentials_file = os.path.join(f"{self.CONFIG_FOLDER}credentials.json")
        folder_id = "14no0Wkoat3guyvVnv-LccXOEoxQqDRy7"  
        
        var_mswx = {
            "Tmax": "Tmax_variable_id",
            "Tmin": "Tmin_variable_id",
            "RelHum": "RelHum_variable_id",
            "Wind": "Wind_variable_id",
            "SWd": "SWd_variable_id",
            "Temp": "Temp_variable_id"
        }

        google_drive_mswx = MSWXData(credentials_file)
        folders = google_drive_mswx.list_folders_in_folder(folder_id, var_mswx)

        for folder in folders:
            google_drive_mswx.list_files_in_daily_folder(folder['id'], ini_date, fin_date, os.path.join(f"{self.INPUTS_DOWNLOADED_DATA}{self.TODAY}"), folder['title'])

        google_drive_mswx.calculate_et0(ini_date, fin_date, inputdatapath=os.path.join(f"{self.INPUTS_DOWNLOADED_DATA}{self.TODAY}/MSWX/"), outputpath=os.path.join(f"{self.OUTPUTS_FOLDER}{self.TODAY}/MSWX/"), mask_file_path=f'{self.HONDURAS_SHP_PATH}mask_mswx_hnd.nc4')

    """
    IMERG data process
    """  
    def run_imerg_data_process(self, ini_date, fin_date):
        imerg_process = IMERGData()
        imerg_process.imerg(ini_date, fin_date, os.path.join(f"{self.INPUTS_DOWNLOADED_DATA}{self.TODAY}/IMERG/"), os.path.join(f"{self.OUTPUTS_FOLDER}{self.TODAY}/IMERG/"), mask_file_path=f'{self.HONDURAS_SHP_PATH}mask_mswx_hnd.nc4')
        

    """
    Post data process
    """
    def post_data_process(self, ini_date, fin_date):
        tools = Tools()
        
        tools.translate_julian_dates(f"{self.INPUTS_DOWNLOADED_DATA}{self.TODAY}/MSWX/Temp/")

        print("Merging forecast and observed temperature files...")
        #tools.merge_files(datetime(2024, 7, 5).date(), datetime(2024, 7, 14).date(), f"{self.INPUTS_FORECAST_DATA}RAIN/RAIN_", f"{self.OUTPUTS_FOLDER}{self.TODAY}/forecast/RAIN_forecast_Honduras.nc", "tif", "mm/day",variable_name='precipitation')
        #tools.merge_files(datetime(2024, 7, 5).date(), datetime(2024, 7, 14).date(), f"{self.INPUTS_FORECAST_DATA}ET0/ET0_", f"{self.OUTPUTS_FOLDER}{self.TODAY}/forecast/ET0_forecast_Honduras.nc", "tif", "mm/day", variable_name='ET0')
        #tools.merge_files(datetime(2024, 7, 5).date(), datetime(2024, 7, 14).date(), f"{self.INPUTS_FORECAST_DATA}T2/T2_", f"{self.OUTPUTS_FOLDER}{self.TODAY}/forecast/Temperature_forecast_Honduras.nc", "tif", "grados celcius", variable_name='air_temperature')
        tools.merge_files(ini_date, fin_date, f"{self.INPUTS_FORECAST_DATA}RAIN/RAIN_", f"{self.OUTPUTS_FOLDER}{self.TODAY}/forecast/RAIN_forecast_Honduras.nc", "tif", "mm/day",variable_name='precipitation')
        tools.merge_files(ini_date, fin_date, f"{self.INPUTS_FORECAST_DATA}ET0/ET0_", f"{self.OUTPUTS_FOLDER}{self.TODAY}/forecast/ET0_forecast_Honduras.nc", "tif", "mm/day", variable_name='ET0')
        tools.merge_files(ini_date, fin_date, f"{self.INPUTS_FORECAST_DATA}T2/T2_", f"{self.OUTPUTS_FOLDER}{self.TODAY}/forecast/Temperature_forecast_Honduras.nc", "tif", "grados celcius", variable_name='air_temperature')
        tools.merge_files(ini_date, fin_date, f"{self.INPUTS_DOWNLOADED_DATA}{self.TODAY}/MSWX/Temp/", f"{self.OUTPUTS_FOLDER}{self.TODAY}/MSWX/Temp.nc", "nc", "grados celcius", variable_name='air_temperature')
        print("Merging forecast and observed temperature files end.")

        print("Cropping observed Temp for Honduras...")
        tools.country_crop(f"{self.OUTPUTS_FOLDER}{self.TODAY}/MSWX/Temp.nc", f"{self.HONDURAS_SHP_PATH}mask_mswx_hnd.nc4", f"{self.OUTPUTS_FOLDER}{self.TODAY}/MSWX/Temp_Honduras.nc")
        print("Cropping observed Temp for Honduras end.")

        print("Cropping regions...")
        tools.regions_crop(f"{self.OUTPUTS_FOLDER}{self.TODAY}/MSWX/ET0_Honduras.nc", f"{self.HONDURAS_REGIONS_PATH}Regiones_productoras_HN.shp", f"{self.OUTPUTS_FOLDER}{self.TODAY}/MSWX/ET0_Honduras_regions.nc", "Nombre")
        tools.regions_crop(f"{self.OUTPUTS_FOLDER}{self.TODAY}/IMERG/IMERG_Honduras.nc", f"{self.HONDURAS_REGIONS_PATH}Regiones_productoras_HN.shp", f"{self.OUTPUTS_FOLDER}{self.TODAY}/IMERG/IMERG_Honduras_regions.nc", "Nombre")
        tools.regions_crop(f"{self.OUTPUTS_FOLDER}{self.TODAY}/forecast/ET0_forecast_Honduras.nc", f"{self.HONDURAS_REGIONS_PATH}Regiones_productoras_HN.shp", f"{self.OUTPUTS_FOLDER}{self.TODAY}/forecast/ET0_forecast_Honduras_regions.nc", "Nombre")
        tools.regions_crop(f"{self.OUTPUTS_FOLDER}{self.TODAY}/forecast/RAIN_forecast_Honduras.nc", f"{self.HONDURAS_REGIONS_PATH}Regiones_productoras_HN.shp", f"{self.OUTPUTS_FOLDER}{self.TODAY}/forecast/RAIN_forecast_Honduras_regions.nc", "Nombre")
        tools.regions_crop(f"{self.OUTPUTS_FOLDER}{self.TODAY}/MSWX/Temp_Honduras.nc", f"{self.HONDURAS_REGIONS_PATH}Regiones_productoras_HN.shp", f"{self.OUTPUTS_FOLDER}{self.TODAY}/MSWX/Temp_Honduras_regions.nc", "Nombre")
        tools.regions_crop(f"{self.OUTPUTS_FOLDER}{self.TODAY}/forecast/Temperature_forecast_Honduras.nc", f"{self.HONDURAS_REGIONS_PATH}Regiones_productoras_HN.shp", f"{self.OUTPUTS_FOLDER}{self.TODAY}/forecast/Temperature_forecast_Honduras_regions.nc", "Nombre")
        print("Cropping regions end.")

        print("Plotting files...")
        tools.plot_nc_file(f"{self.OUTPUTS_FOLDER}{self.TODAY}/MSWX/Temp_Honduras.nc", "air_temperature", save_path=f"{self.OUTPUTS_FOLDER}{self.TODAY}/figures/temperature_honduras_observado_")
        tools.plot_nc_file(f"{self.OUTPUTS_FOLDER}{self.TODAY}/IMERG/IMERG_Honduras.nc", "precipitationCal", save_path=f"{self.OUTPUTS_FOLDER}{self.TODAY}/figures/precipitation_honduras_observado_")
        tools.plot_nc_file(f"{self.OUTPUTS_FOLDER}{self.TODAY}/MSWX/ET0_Honduras.nc", "ET0", save_path=f"{self.OUTPUTS_FOLDER}{self.TODAY}/figures/et0_honduras_observado_")
        tools.plot_nc_file(f"{self.OUTPUTS_FOLDER}{self.TODAY}/forecast/Temperature_forecast_Honduras.nc", "air_temperature", save_path=f"{self.OUTPUTS_FOLDER}{self.TODAY}/figures/temperature_honduras_forecast_")
        tools.plot_nc_file(f"{self.OUTPUTS_FOLDER}{self.TODAY}/forecast/ET0_forecast_Honduras.nc", "ET0", save_path=f"{self.OUTPUTS_FOLDER}{self.TODAY}/figures/et0_honduras_forecast_")
        tools.plot_nc_file(f"{self.OUTPUTS_FOLDER}{self.TODAY}/forecast/RAIN_forecast_Honduras.nc", "precipitation", save_path=f"{self.OUTPUTS_FOLDER}{self.TODAY}/figures/precipitation_honduras_forecast_")
        print("Plotting files end.")

        print("Writting CSV file for daily mean for municipalities...")
        temp = tools.calculate_daily_mean_per_municipality(f"{self.HONDURAS_MUNICIPALITIES_PATH}/Municipios_reg_prod_HN.shp", f"{self.OUTPUTS_FOLDER}{self.TODAY}/MSWX/Temp_Honduras.nc", "air_temperature", "NAME_1", "NAME_2", "c", "air-temperature_obs")
        temp_forecast = tools.calculate_daily_mean_per_municipality(f"{self.HONDURAS_MUNICIPALITIES_PATH}/Municipios_reg_prod_HN.shp", f"{self.OUTPUTS_FOLDER}{self.TODAY}/MSWX/Temp_Honduras.nc", "air_temperature", "NAME_1", "NAME_2", "c","air-temperature_for")
        et0_mswx = tools.calculate_daily_mean_per_municipality(f"{self.HONDURAS_MUNICIPALITIES_PATH}/Municipios_reg_prod_HN.shp", f"{self.OUTPUTS_FOLDER}{self.TODAY}/MSWX/ET0_Honduras.nc", "ET0", "NAME_1", "NAME_2", "mm-day", "et0_obs")
        et0_forecast = tools.calculate_daily_mean_per_municipality(f"{self.HONDURAS_MUNICIPALITIES_PATH}/Municipios_reg_prod_HN.shp", f"{self.OUTPUTS_FOLDER}{self.TODAY}/forecast/ET0_forecast_Honduras.nc", "ET0", "NAME_1", "NAME_2", "mm-day","et0_for")
        prep_imerg = tools.calculate_daily_mean_per_municipality(f"{self.HONDURAS_MUNICIPALITIES_PATH}/Municipios_reg_prod_HN.shp", f"{self.OUTPUTS_FOLDER}{self.TODAY}/IMERG/IMERG_Honduras.nc", "precipitationCal", "NAME_1", "NAME_2", "mm-day", "precipitation-cal_obs")
        prep_forecast = tools.calculate_daily_mean_per_municipality(f"{self.HONDURAS_MUNICIPALITIES_PATH}/Municipios_reg_prod_HN.shp", f"{self.OUTPUTS_FOLDER}{self.TODAY}/forecast/RAIN_forecast_Honduras.nc", "precipitation", "NAME_1", "NAME_2", "mm-day", "precipitation-cal_for")

        merged_df = temp.merge(temp_forecast, on=["region", "municipio"])
        merged_df = merged_df.merge(et0_mswx, on=["region", "municipio"])
        merged_df = merged_df.merge(et0_forecast, on=["region", "municipio"])
        merged_df = merged_df.merge(prep_imerg, on=["region", "municipio"])
        merged_df = merged_df.merge(prep_forecast, on=["region", "municipio"])
        merged_df.to_csv(f"{self.OUTPUTS_FOLDER}{self.TODAY}/daily_mean_municipalities.csv", index=False, encoding='utf-8-sig')
        print("Writting CSV file for daily mean for municipalities end.")


if __name__ == "__main__":
    #YYYY-MM-DD
    central_date = sys.argv[1]
    workspace_path =  sys.argv[2] if len(sys.argv) > 2 else None
    path_shp_crop_honduras = sys.argv[3] if len(sys.argv) > 3 else None
    path_shp_crop_honduras_regions = sys.argv[4] if len(sys.argv) > 4 else None
    path_shp_crop_honduras_municipalities = sys.argv[5] if len(sys.argv) > 5 else None
    path_forecast_files = sys.argv[6] if len(sys.argv) > 6 else None

    main = Master(central_date, workspace_path, path_shp_crop_honduras, path_shp_crop_honduras_regions, path_shp_crop_honduras_municipalities, path_forecast_files)

    print("MSWX data process begin...")
    main.run_mswx_data_proccess(main.INI_DATE, main.FIN_DATE)
    print("MSWX data process end.")

    print("IMERG data process begin...")
    main.run_imerg_data_process(main.INI_DATE, main.FIN_DATE)
    print("IMERG data process end.")

    main.post_data_process(main.INI_DATE, main.FIN_DATE)