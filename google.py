#pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client

import os
import google.auth
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

def download_files_from_drive(client_id, client_secret, refresh_token, folder_id, download_path='./downloads'):
    # Crear el diccionario de credenciales
    credentials_info = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        }
    }

    # Crear credenciales usando el refresh token
    creds = Credentials.from_authorized_user_info(credentials_info)
    creds.refresh(Request())

    # Construir el servicio de Google Drive
    service = build('drive', 'v3', credentials=creds)

    # Crear el directorio de descargas si no existe
    if not os.path.exists(download_path):
        os.makedirs(download_path)

    # Obtener la lista de archivos en la carpeta especificada
    query = f"'{folder_id}' in parents and trashed=false"
    results = service.files().list(q=query, pageSize=1000, fields="files(id, name)").execute()
    items = results.get('files', [])

    # Descargar cada archivo
    for item in items:
        file_id = item['id']
        file_name = item['name']
        request = service.files().get_media(fileId=file_id)
        file_path = os.path.join(download_path, file_name)
        with open(file_path, 'wb') as f:
            downloader = googleapiclient.http.MediaIoBaseDownload(f, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                print(f"Descargando {file_name} ({int(status.progress() * 100)}%)")

    print('Todos los archivos han sido descargados.')

# Ejemplo de uso de la función
client_id = 'TU_CLIENT_ID_AQUI'
client_secret = 'TU_CLIENT_SECRET_AQUI'
refresh_token = 'TU_REFRESH_TOKEN_AQUI'
folder_id = 'TU_FOLDER_ID_AQUI'

download_files_from_drive(client_id, client_secret, refresh_token, folder_id)