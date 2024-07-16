# ETL Agrilac CENAOS Infoagro

This repository contains all related to ETL Agrilac CENAOS Infoagro.

## Features

- Generates a NetCDF file with the calculation of evo-transpiration (ET0) using NRT data from MSWX (Tmax, Tmin, Relhum, Wind, SWd) for Honduras and its regions
- Generates a NetCDF precipitation file (IMERG data) for Honduras and its regions
- Generates a NetCDF file temperature (Temp) from MSWX file for Honduras and its regions
- Generates a NetCDF file with the calculation of evo-transpiration (ET0) predicted using the WRF model (Weather Research and Forecasting model) for Honduras and its regions
- Generates a NetCDF file of forecasted precipitation using the WRF (Weather Research and Forecasting model) for Honduras and its regions
- Generates a NetCDF file of forecasted temperature (Temp) using the WRF (Weather Research and Forecasting model) for Honduras and its regions
- Generates daily average graphs with uncertainty range for all variables (Observed ET0, Forecast ET0, Observed Temperature, Forecast Temperature, Observed Precipitation, Predicted Precipitation)
- Generates a CSV file with daily average of all variables (Observed ET0, Forecast ET0, Observed Temperature, Forecast Temperature, Observed Precipitation, Predicted Precipitation) for the municipalities of Honduras

## Prerequisites

- Python 3.x
- You need an account to download IMERG data. You can create one here https://urs.earthdata.nasa.gov/

## Configure DEV Environment

You should create an env to run the code and install the requirements. Run the following commands in the prompt

````bash
pip install virtualenv
venv env
pip install -r requirements.txt
````


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
