from datetime import datetime, timedelta
from imerg_data import IMERGData
from mswx_data import MSWXData
from tools import Tools
import os, sys

class Master:
    #Today date for use in folders
    TODAY = datetime.now().date().strftime('%Y%m%d')
    # WORSKPACE = sys.argv[4]
    # CONFIG_FOLDER = os.path.join(WORSKPACE, "/config/")
    # INPUTS_FOLDER = os.path.join(WORSKPACE, "/inputs/")
    # OUTPUTS_FOLDER = os.path.join(WORSKPACE, "/outputs/")


    """
    MSXW data process
    """
    def run_mswx_data_proccess(self, ini_date, fin_date):
        credentials_file = os.path.join("./workspace/config/credentials.json")
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
            google_drive_mswx.list_files_in_daily_folder(folder['id'], ini_date, fin_date, os.path.join(f"./workspace/inputs/downloaded_data/{self.TODAY}"), folder['title'])

        google_drive_mswx.calculate_et0(ini_date, fin_date, inputdatapath=os.path.join(f"./workspace/inputs/downloaded_data/{self.TODAY}/MSWX/"), outputpath=os.path.join(f"./workspace/outputs/{self.TODAY}/MSWX/"), mask_file_path='./workspace/config/mask_honduras/mask_mswx_hnd.nc4')

    """
    IMERG data process
    """  
    def run_imerg_data_process(self, ini_date, fin_date):
        imerg_process = IMERGData()
        imerg_process.imerg(ini_date, fin_date, os.path.join(f"./workspace/inputs/downloaded_data/{self.TODAY}/IMERG/"), os.path.join(f"./workspace/outputs/{self.TODAY}/IMERG/"), mask_file_path='./workspace/config/mask_honduras/mask_mswx_hnd.nc4')
        

    """
    Post data process
    """
    def post_data_process(self, ini_date, fin_date):
        tools = Tools()

        print("Merging forecast files...")
        tools.merge_files(ini_date, fin_date, "./workspace/inputs/forecast_data/RAINNC/RAINNC_", "./workspace/outputs/forecast/RAINNC_forecast_Honduras.nc", "tif", variable_name='precipitation')
        tools.merge_files(ini_date, fin_date, "./workspace/inputs/forecast_data/ET0/ET0_", "./workspace/outputs/forecast/ET0_forecast_Honduras.nc", "tif", variable_name='ET0')
        tools.merge_files(ini_date, fin_date, "./workspace/inputs/downloaded_data/20240705/MSWX/Temp/", "./workspace/outputs/20240705/MSWX/Temp.nc", "nc", variable_name='air_temperature')
        print("Merging forecast files end.")

        print("Cropping Temp for Honduras...")
        tools.country_crop("./workspace/outputs/20240705/MSWX/Temp.nc", "./workspace/config/mask_honduras/mask_mswx_hnd.nc4", "./workspace/outputs/20240705/MSWX/Temp_Honduras.nc")
        print("Cropping Temp for Honduras end.")


        print("Cropping regions...")
        #tools.regions_crop("./outputs/MSWX/2024jun28/ET0_Honduras.nc", "./mask_honduras/regions_shapefile/hnd_admbnda_adm1_sinit_20161005.shp", "./outputs/MSWX/ET0_Honduras_regions.nc")
        #tools.regions_crop("./outputs/IMERG/IMERG_Honduras.nc", "./mask_honduras/regions_shapefile/hnd_admbnda_adm1_sinit_20161005.shp", "./outputs/IMERG/IMERG_Honduras_regions.nc")
        #tools.regions_crop("./outputs/forecast/ET0_forecast_Honduras.nc", "./mask_honduras/regions_shapefile/hnd_admbnda_adm1_sinit_20161005.shp", "./outputs/forecast/ET0_forecast_Honduras_regions.nc")
        #tools.regions_crop("./outputs/forecast/RAINNC_forecast_Honduras.nc", "./mask_honduras/regions_shapefile/hnd_admbnda_adm1_sinit_20161005.shp", "./outputs/forecast/RAINNC_forecast_Honduras_regions.nc")

        tools.regions_crop("./workspace/outputs/20240705/MSWX/Temp_Honduras.nc", "./workspace/config/mask_honduras/mask_mswx_hnd.nc4", "./workspace/outputs/20240705/MSWX/Temp_Honduras_regions.nc")


        print("Cropping regions end.")

        print("Plotting files...")
        tools.plot_nc_file(f"./workspace/outputs/{self.TODAY}/IMERG/IMERG_Honduras.nc", "precipitationCal")
        tools.plot_nc_file(f"./workspace/outputs/{self.TODAY}/MSWX/2024jul04/ET0_Honduras.nc", "ET0")
        tools.plot_nc_file("./workspace/outputs/forecast/ET0_forecast_Honduras.nc", "ET0", lon_dim='x', lat_dim='y', time_dim='time')
        tools.plot_nc_file("./workspace/outputs/forecast/RAINNC_forecast_Honduras.nc", "precipitation", lon_dim='x', lat_dim='y', time_dim='time')
        print("Plotting files end.")

        print("Writting CSV file for daily mean for municipalities...")
        tools.calculate_daily_mean_per_municipality("./workspace/config/mask_honduras/municipalities_shapefile/Municipios_reg_prod_HN.shp", f"./workspace/outputs/{self.TODAY}/MSWX/Temp_Honduras.nc", "air_temperature", f"./workspace/outputs/{self.TODAY}/MSWX/Temp_Honduras_municipios.csv", "NAME_1", "NAME_2", "grados celcius")
        tools.calculate_daily_mean_per_municipality("./workspace/config/mask_honduras/municipalities_shapefile/Municipios_reg_prod_HN.shp", f"./workspace/outputs/{self.TODAY}/MSWX/ET0_Honduras.nc", "ET0", f"./workspace/outputs/{self.TODAY}/MSWX/ET0_Honduras_municipios.csv", "NAME_1", "NAME_2", "mm/day")
        tools.calculate_daily_mean_per_municipality("./workspace/config/mask_honduras/municipalities_shapefile/Municipios_reg_prod_HN.shp", f"./workspace/outputs/{self.TODAY}/IMERG/IMERG_Honduras.nc", "precipitationCal", f"./workspace/outputs/{self.TODAY}/IMERG/IMERG_Honduras_municipios.csv", "NAME_1", "NAME_2", "mm/day")
        tools.calculate_daily_mean_per_municipality("./workspace/config/mask_honduras/municipalities_shapefile/Municipios_reg_prod_HN.shp", "./workspace/outputs/forecast/ET0_forecast_Honduras.nc", "ET0", "./workspace/outputs/forecast/ET0_forecast_Honduras_municipios.csv", "NAME_1", "NAME_2", "mm/day")
        tools.calculate_daily_mean_per_municipality("./workspace/config/mask_honduras/municipalities_shapefile/Municipios_reg_prod_HN.shp", "./workspace/outputs/forecast/RAINNC_forecast_Honduras.nc", "precipitation", "./workspace/outputs/forecast/RAINNC_forecast_Honduras_municipios.csv", "NAME_1", "NAME_2", "mm/day")
        print("Writting CSV file for daily mean for municipalities end.")


if __name__ == "__main__":
    #YYYYMMDD
    # central_date = sys.argv[1]
    # path_shp_crop_honduras = sys.argv[2]
    # path_shp_crop_honduras_regions = sys.argv[3]
    # path_forecast_files = sys.argv[3]
    # workspace_path = sys.argv[4]


    #Dates for last ten days, taking yesterday as last day
    #fin_date = datetime.now().date() - timedelta(days=1)
    #ini_date = fin_date - timedelta(days=9)
    ini_date = datetime(2024, 4, 8).date()
    fin_date = datetime(2024, 4, 18).date() 
    #ini_date = datetime(2017, 8, 15).date()
    #fin_date = datetime(2017, 8, 24).date() 
    main = Master()

    print("MSWX data process begin...")
    main.run_mswx_data_proccess(ini_date, fin_date)
    print("MSWX data process end.")

    print("IMERG data process begin...")
    #main.run_imerg_data_process(ini_date, fin_date)
    print("IMERG data process end.")

    #main.post_data_process(ini_date, fin_date)