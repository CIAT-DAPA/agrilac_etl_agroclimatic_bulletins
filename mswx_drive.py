import os
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from datetime import datetime, timedelta

class GoogleDriveManager:
    def __init__(self):
        self.drive = self.authenticate_drive()
        
    def authenticate_drive(self):
        gauth = GoogleAuth()
        gauth.LocalWebserverAuth()  # Autenticar y crear credenciales
        return GoogleDrive(gauth)
    
    def list_folders_in_folder(self, folder_id, var_mswx):
        query = f"'{folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed=false"
        file_list = self.drive.ListFile({
            'q': query,
            'supportsAllDrives': True,
            'includeItemsFromAllDrives': True
        }).GetList()
        
        folders = []
        for file in file_list:
            title = file['title']
            if title in var_mswx.keys():
                folders.append({'title': title, 'id': file['id']})
        
        return folders
    
    def list_files_in_daily_folder(self, folder_id, ini_date, fin_date, var_mswx, folder_title):
        query = f"'{folder_id}' in parents and title = 'Daily' and trashed=false"
        daily_folder = self.drive.ListFile({
            'q': query,
            'supportsAllDrives': True,
            'includeItemsFromAllDrives': True
        }).GetList()
        
        if len(daily_folder) == 1:
            daily_folder_id = daily_folder[0]['id']
            print(f"Archivos y carpetas dentro de la carpeta 'Daily' (ID: {daily_folder_id}):")
            
            daily_files = self.drive.ListFile({
                'q': f"'{daily_folder_id}' in parents and trashed=false",
                'supportsAllDrives': True,
                'includeItemsFromAllDrives': True
            }).GetList()
            
            base_download_dir = os.path.join(os.getcwd(), 'MSWX')
            if not os.path.exists(base_download_dir):
                os.makedirs(base_download_dir)
            
            date_range = [(ini_date + timedelta(days=i)).strftime('%Y%j') for i in range((fin_date - ini_date).days + 1)]
            
            for file in daily_files:
                file_date_str = file['title'][:7]
                if file_date_str in date_range and file['title'].endswith('.nc'):
                    variable_name = file['title'].split('_')[0]
                    variable_download_dir = os.path.join(base_download_dir, folder_title)
                    if not os.path.exists(variable_download_dir):
                        os.makedirs(variable_download_dir)
                    
                    self.download_file(file['id'], file['title'], variable_download_dir)
        else:
            print(f"No se encontró la carpeta 'Daily' dentro de la carpeta con ID: {folder_id}")

    def download_file(self, file_id, file_name, download_folder_path):
        file = self.drive.CreateFile({'id': file_id})
        file.GetContentFile(os.path.join(download_folder_path, file_name))
        print(f"Descargado archivo: {file_name}")

class FolderManager:
    def __init__(self, google_drive_manager, folder_id, var_mswx, ini_date, fin_date):
        self.drive_manager = google_drive_manager
        self.folder_id = folder_id
        self.var_mswx = var_mswx
        self.ini_date = ini_date
        self.fin_date = fin_date
        
    def process_folders(self):
        folders = self.drive_manager.list_folders_in_folder(self.folder_id, self.var_mswx)
        for folder in folders:
            print(f"\nAccediendo a la carpeta '{folder['title']}' (ID: {folder['id']})")
            self.drive_manager.list_files_in_daily_folder(folder['id'], self.ini_date, self.fin_date, self.var_mswx, folder['title'])

if __name__ == "__main__":
    drive_manager = GoogleDriveManager()
    folder_id = "14no0Wkoat3guyvVnv-LccXOEoxQqDRy7"
    ini_date = datetime(2024, 4, 8).date()
    fin_date = datetime(2024, 4, 18).date()
    var_mswx = {
        'SWd': 'downward_shortwave_radiation',
        'RelHum': 'relative_humidity',
        'Tmax': 'air_temperature',
        'Tmin': 'air_temperature',
        'Wind': 'wind_speed'
    }
    
    folder_manager = FolderManager(drive_manager, folder_id, var_mswx, ini_date, fin_date)
    folder_manager.process_folders()
