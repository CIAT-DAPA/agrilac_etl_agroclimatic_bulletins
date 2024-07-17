# ETL Agrilac CENAOS Infoagro

This repository contains all related to ETL Agrilac CENAOS Infoagro.

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

## Project Structure

- `workspace/`: It is the main directory where the input, output, and configuration files will be. (it is not necessary to create it, it is created automatically).
- `workspace/config/`: This folder contains the shapefile files used for the data process.
- `workspace/outputs/`: Folder where all outputs will be saved, (it is not necessary to create it, it is created automatically).
- `workspace/outputs/YYYYMMDD/MSWX/`: Folder where all MSWX outputs will be saved, (it is not necessary to create it, it is created automatically).
- `workspace/outputs/YYYYMMDD/IMERG/`: Folder where all IMERG outputs will be saved, (it is not necessary to create it, it is created automatically).
- `workspace/outputs/YYYYMMDD/forecast/`: Folder where all forecast outputs will be saved, (it is not necessary to create it, it is created automatically).
- `workspace/outputs/YYYYMMDD/figures/`: Folder where all graphs will be saved, (it is not necessary to create it, it is created automatically).
- `workspace/inputs/`: Folder where all inputs will be saved, (it is not necessary to create it, it is created automatically).
-`workspace/inputs/downloaded_data/`: Folder where all data downloaded will be saved, (it is not necessary to create it, it is created automatically).
- `workspace/inputs/forecast_data/`: Folder where all forecast data for temperature, precipitation and ET0  will be saved, (it is not necessary to create it, it is created automatically).
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
GDC stands for Google Drive Credentials. The variables **GDC_** reference attributes in Google's credentials.json file.
The variables environments required are the following:

* IMERG_USERNAME: IMERG user
* IMERG_PWD: IMERG password
* GDC_TYPE: Google Drive Credentials type.
* GDC_PROJECT_ID: Google Drive Credentials project id.
* GDC_PRIVATE_KEY_ID: Google Drive Credentials private key id.
* GDC_PRIVATE_KEY: Google Drive Credentials private key.
* GDC_CLIENT_EMAIL: Google Drive Credentials client email.
* GDC_CLIENT_id: Google Drive Credentials client id.
* GDC_AUTH_URI: Google Drive Credentials auth uri.
* GDC_TOKEN_URI: Google Drive Credentials token uri.
* GDC_AUTH_PROVIDER_X509_CERT_URL: Google Drive Credentials auth provider x509 cert url.
* GDC_CLIENT_X509_CERT_URL: Google Drive Credentials client x509 cert url.
* GDC_UNIVERSE_DOMAIN: Google Drive Credentials universe domain


## Run

You can run the module using the command python master.py at src/ level followed by the following parameters:

````bash
python master.py end_date workspace_path path_shp_crop_honduras path_shp_crop_honduras_regions path_shp_crop_honduras_municipalities path_forecast_files
````

### Params
- end_date: date in YYYY-MM-DD format. This will be the last day of a 10-day range. This is the only **mandatory** parameter.
- workspace_path: the path set as workspace 
- path_shp_crop_honduras: path where is the mask for Honduras
- path_shp_crop_honduras_regions: path where is the shapefile for Honduras regions
- path_shp_crop_honduras_municipalities: path where is the shapefile for Honduras municipalities
- path_forecast_files: path where the WRF .nc files (Temperature, Rain and ET0)
  
### Example
````bash
python master.py 2024-06-30
````
