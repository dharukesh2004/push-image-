from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
import os

# Define the scopes and credentials
SCOPES = ['https://www.googleapis.com/auth/drive']

def auth_g_drive():
    """Authenticates and returns a Google Drive service instance."""
    creds = None
    # The file token.json stores the user's access and refresh tokens.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            print("Authentication error. Please check credentials.")
    try:
        # Build the service
        service = build('drive', 'v3', credentials=creds)
        return service
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None

def create_root_folder(service, folder_name):
    """Create a folder on Google Drive and return its ID."""
    folder_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    try:
        folder = service.files().create(body=folder_metadata, fields='id').execute()
        print(f'Folder "{folder_name}" created with ID: {folder.get("id")}')
        return folder.get('id')  # Return the folder ID
    except HttpError as error:
        print(f'An error occurred while creating the folder: {error}')

def main():
    # Authenticate and build the Drive service
    service = auth_g_drive()

    if service:
        # Create a root folder in your Google Drive
        root_folder_id = create_root_folder(service, 'MyRootFolder')  # Specify your root folder name
        print(f"Root folder created with ID: {root_folder_id}")

if __name__ == '__main__':
    main()
