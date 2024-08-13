# ETL Agroclimatic Bulletins
This repository contains all related to ETL Agroclimatic Bulletins

## Features

- Generates a NetCDF file with the calculation of evo-transpiration (ET0) using NRT data from MSWX (Tmax, Tmin, Relhum, Wind, SWd) for Honduras and its regions
- Generates a NetCDF precipitation file (IMERG data) for Honduras and its regions
- Generates a NetCDF file temperature (Temp) from the MSWX file for Honduras and its regions
- Generates a NetCDF file with the calculation of evo-transpiration (ET0) predicted using the WRF model (Weather Research and Forecasting model) for Honduras and its regions
- Generates a NetCDF file of forecasted precipitation using the WRF (Weather Research and Forecasting model) for Honduras and its regions
- Generates a NetCDF file of forecasted temperature (Temp) using the WRF (Weather Research and Forecasting model) for Honduras and its regions
- Generates daily average graphs with uncertainty range for all variables (Observed ET0, Forecast ET0, Observed Temperature, Forecast Temperature, Observed Precipitation, Predicted Precipitation)
- Generates a CSV file with a daily average of all variables (Observed ET0, Forecast ET0, Observed Temperature, Forecast Temperature, Observed Precipitation, Predicted Precipitation) for the municipalities of Honduras

## Prerequisites

- Python 3.x
- You need an account to download IMERG data. You can create one here https://urs.earthdata.nasa.gov/
- Clone this repository.

## Project Structure

- `workspace/`: It is the main directory where the input, output, and configuration files will be.
- `workspace/config/mask_honduras/`: This folder contains a Honduras NetCDF file that will be used to cut out the shape of the country. You must provide such a file in the folder with the name "mask_mswx_hnd.nc4" for the process to work correctly.
- `workspace/config/mask_honduras/municipalities_shapefile/`: This folder contains a municipalities shapefile for Honduras. You must provide such files in the folder with the name "Municipios_reg_prod_HN.shp" for the process to work correctly.
- `workspace/config/mask_honduras/regions_shapefile/`: This folder contains a region shapefile for Honduras. You must provide such files in the folder with the name "Regiones_productoras_HN.shp" for the process to work correctly.
- `workspace/outputs/`: Folder where all outputs will be saved
- `workspace/outputs/YYYYMMDD/MSWX/`: Folder where all MSWX outputs will be saved
- `workspace/outputs/YYYYMMDD/IMERG/`: Folder where all IMERG outputs will be saved, 
- `workspace/outputs/YYYYMMDD/forecast/`: Folder where all forecast outputs will be saved, 
- `workspace/outputs/YYYYMMDD/figures/`: Folder where all graphs will be saved, 
- `workspace/inputs/`: Folder where all inputs will be saved, 
- `workspace/inputs/downloaded_data/`: Folder where all data downloaded will be saved, 
- `workspace/inputs/forecast_data/ET0/`: This folder contains ET0 forecast .tif files for Honduras from the WRF. You must provide these files in "ET0_YYYY_MM_DD.tif" format and the dates must correspond to the start and end dates of the process.
- `workspace/inputs/forecast_data/RAIN/`: This folder contains precipitation forecast .tif files for Honduras from the WRF. You must provide these files in "RAIN_YYYY_MM_DD.tif" format and the dates must correspond to the start and end dates of the process.
- `workspace/inputs/forecast_data/T2/`: This folder contains temperature forecast .tif files for Honduras from the WRF. You must provide these files in "T2_YYYY_MM_DD.tif" format and the dates must correspond to the start and end dates of the process.
- `src/`: Folder to store the source code of the project.

## Configure DEV Environment

You should create an environment to run the code and install the requirements. Run the following commands in the prompt

````bash
pip install virtualenv
venv env
pip install -r requirements.txt
````
## Environment vars
The system requires set environment vars. 
For setting env vars in **Windows** you use:

```
set SECRET_KEY=Loc@lS3cr3t

```
For setting env vars in **Linux** you use:

```
export SECRET_KEY=Loc@lS3cr3t

```
GCC stands for Google Cloud Credentials. The variables **GCC_** reference attributes in Google's credentials.json file.
The variables environments required are the following:

* IMERG_USERNAME: IMERG user
* IMERG_PWD: IMERG password
* GCC_TYPE: Google Cloud Credentials type.
* GCC_PROJECT_ID: Google Cloud Credentials project id.
* GCC_PRIVATE_KEY_ID: Google Cloud Credentials private key id.
* GCC_PRIVATE_KEY: Google Cloud Credentials private key.
* GCC_CLIENT_EMAIL: Google Cloud Credentials client email.
* GCC_CLIENT_id: Google Cloud Credentials client id.
* GCC_AUTH_URI: Google Cloud Credentials auth uri.
* GCC_TOKEN_URI: Google Cloud Credentials token uri.
* GCC_AUTH_PROVIDER_X509_CERT_URL: Google Cloud Credentials auth provider x509 cert url.
* GCC_CLIENT_X509_CERT_URL: Google Cloud Credentials client x509 cert url.
* GCC_UNIVERSE_DOMAIN: Google Cloud Credentials universe domain


## Run

You can run the module using the command python master.py at src/ level followed by the following parameters:

````bash
python master.py end_date workspace_path path_shp_crop_honduras path_shp_crop_honduras_regions path_shp_crop_honduras_municipalities path_forecast_files
````

### Params
- end_date: date in YYYY-MM-DD format. The day before this date will be the final day of the ten-day range. This is the only **mandatory** parameter.
- workspace_path: the path set as workspace 
- path_shp_crop_honduras: Corresponds to the path `workspace/config/mask_honduras/` indicated in the Project Structure section
- path_shp_crop_honduras_regions: Corresponds to the path `workspace/config/mask_honduras/regions_shapefile/` indicated in the Project Structure section
- path_shp_crop_honduras_municipalities: Corresponds to the path `workspace/config/mask_honduras/municipalities_shapefile/` indicated in the Project Structure section
- path_forecast_files: Corresponds to the path `workspace/input/forecast_data/` indicated in the Project Structure section
  
### Example
````bash
python master.py 2024-05-30
````
