from datetime import datetime, timedelta
from imerg_data import IMERGData
from mswx_data import MSWXData
from tools import Tools

class Master:
    TODAY = datetime.now().date().strftime('%Y%m%d')
    """
    MSXW data process
    """
    def run_mswx_data_proccess(self, ini_date, fin_date):
        credentials_file = "./credentials.json"
        folder_id = "14no0Wkoat3guyvVnv-LccXOEoxQqDRy7"
        
        var_mswx = {
            "Tmax": "Tmax_variable_id",
            "Tmin": "Tmin_variable_id",
            "RelHum": "RelHum_variable_id",
            "Wind": "Wind_variable_id",
            "SWd": "SWd_variable_id"
        }

        google_drive_mswx = MSWXData(credentials_file)
        folders = google_drive_mswx.list_folders_in_folder(folder_id, var_mswx)
        for folder in folders:
            google_drive_mswx.list_files_in_daily_folder(folder['id'], ini_date, fin_date, f"./downloaded_data/{self.TODAY}", folder['title'])

        google_drive_mswx.calculate_et0(ini_date, fin_date, inputdatapath=f"./downloaded_data/{self.TODAY}/MSWX/", outputpath=f"./outputs/{self.TODAY}/MSWX/")

    """
    IMERG data process
    """  
    def run_imerg_data_process(self, ini_date, fin_date):
        imerg_process = IMERGData()
        imerg_process.imerg(ini_date, fin_date)
        imerg_process.merge_nc_files(ini_date, fin_date)

    """
    Post data process
    """
    def post_data_process(self, ini_date, fin_date):
        tools = Tools()

        print("Merging forecast files...")
        tools.merge_files(ini_date, fin_date, "./forecast_data/RAINNC/RAINNC_", "./outputs/forecast/RAINNC_forecast_Honduras.nc", "tif", variable_name='precipitation')
        tools.merge_files(ini_date, fin_date, "./forecast_data/ET0/ET0_", "./outputs/forecast/ET0_forecast_Honduras.nc", "tif", variable_name='ET0')
        print("Merging forecast files end.")

        print("Cropping regions...")
        tools.regions_crop("./outputs/MSWX/2024jun28/ET0_Honduras.nc", "./mask_honduras/regions_shapefile/hnd_admbnda_adm1_sinit_20161005.shp", "./outputs/MSWX/ET0_Honduras_regions.nc")
        tools.regions_crop("./outputs/IMERG/IMERG_Honduras.nc", "./mask_honduras/regions_shapefile/hnd_admbnda_adm1_sinit_20161005.shp", "./outputs/IMERG/IMERG_Honduras_regions.nc")
        tools.regions_crop("./outputs/forecast/ET0_forecast_Honduras.nc", "./mask_honduras/regions_shapefile/hnd_admbnda_adm1_sinit_20161005.shp", "./outputs/forecast/ET0_forecast_Honduras_regions.nc")
        tools.regions_crop("./outputs/forecast/RAINNC_forecast_Honduras.nc", "./mask_honduras/regions_shapefile/hnd_admbnda_adm1_sinit_20161005.shp", "./outputs/forecast/RAINNC_forecast_Honduras_regions.nc")
        print("Cropping regions end.")

        print("Plotting files...")
        tools.plot_nc_file("./outputs/IMERG/IMERG_Honduras.nc", "precipitationCal")
        tools.plot_nc_file("./outputs/MSWX/2024jun28/ET0_Honduras.nc", "ET0")
        tools.plot_nc_file("./outputs/forecast/ET0_forecast_Honduras.nc", "ET0", lon_dim='x', lat_dim='y', time_dim='time')
        tools.plot_nc_file("./outputs/forecast/RAINNC_forecast_Honduras.nc", "precipitation", lon_dim='x', lat_dim='y', time_dim='time')
        print("Plotting files end.")


if __name__ == "__main__":
    #Dates for last ten days, taking yesterday as last day
    fin_date = datetime.now().date() - timedelta(days=1)
    ini_date = fin_date - timedelta(days=9)
    main = Master()

    print("MSWX data process begin...")
    #main.run_mswx_data_proccess(ini_date, fin_date)
    print("MSWX data process end.")

    print("IMERG data process begin...")
    main.run_imerg_data_process(ini_date, fin_date)
    print("IMERG data process end.")

   #main.post_data_process(ini_date, fin_date)