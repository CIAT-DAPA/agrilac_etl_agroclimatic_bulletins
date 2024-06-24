import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from datetime import datetime, timedelta

class GoogleDriveManager:
    def __init__(self, credentials_file):
        self.drive = self.authenticate_drive(credentials_file)
        
    def authenticate_drive(self, credentials_file):
        SCOPES = ['https://www.googleapis.com/auth/drive']
        credentials = service_account.Credentials.from_service_account_file(
            credentials_file, scopes=SCOPES)
        return build('drive', 'v3', credentials=credentials)
    
    def list_folders_in_folder(self, folder_id, var_mswx):
        query = f"'{folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed=false"
        results = self.drive.files().list(q=query, supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
        file_list = results.get('files', [])
        
        folders = []
        for file in file_list:
            title = file['name']
            if title in var_mswx.keys():
                folders.append({'title': title, 'id': file['id']})
        
        return folders
    
    def list_files_in_daily_folder(self, folder_id, ini_date, fin_date, var_mswx, folder_title):
        query = f"'{folder_id}' in parents and name = 'Daily' and trashed=false"
        results = self.drive.files().list(q=query, supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
        daily_folder = results.get('files', [])
        
        if len(daily_folder) == 1:
            daily_folder_id = daily_folder[0]['id']
            print(f"Archivos y carpetas dentro de la carpeta 'Daily' (ID: {daily_folder_id}):")
            
            daily_files = self.drive.files().list(
                q=f"'{daily_folder_id}' in parents and trashed=false",
                supportsAllDrives=True, includeItemsFromAllDrives=True).execute().get('files', [])
            
            base_download_dir = os.path.join(os.getcwd(), 'MSWX')
            if not os.path.exists(base_download_dir):
                os.makedirs(base_download_dir)
            
            date_range = [(ini_date + timedelta(days=i)).strftime('%Y%j') for i in range((fin_date - ini_date).days + 1)]
            
            for file in daily_files:
                file_date_str = file['name'][:7]
                if file_date_str in date_range and file['name'].endswith('.nc'):
                    variable_name = file['name'].split('_')[0]
                    variable_download_dir = os.path.join(base_download_dir, folder_title)
                    if not os.path.exists(variable_download_dir):
                        os.makedirs(variable_download_dir)
                    
                    self.download_file(file['id'], file['name'], variable_download_dir)
        else:
            print(f"No se encontró la carpeta 'Daily' dentro de la carpeta con ID: {folder_id}")

    def download_file(self, file_id, file_name, download_folder_path):
        request = self.drive.files().get_media(fileId=file_id)
        file_path = os.path.join(download_folder_path, file_name)
        with open(file_path, 'wb') as file:
            downloader = MediaIoBaseDownload(file, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    print(f"Descargado {int(status.progress() * 100)}%.")
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
    credentials_file = './credentials.json'  # Reemplazar por la ruta
    drive_manager = GoogleDriveManager(credentials_file)
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
