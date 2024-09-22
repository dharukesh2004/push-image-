import os
import datetime
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from apiclient.http import MediaFileUpload
import cv2
import time
import uuid
import requests

SCOPES = ["https://www.googleapis.com/auth/drive"]
ROOT_FOLDER = '13c2mGLOAwdYJg2420n-eKgh069dQhA-V'  # Parent folder ID
CONFIG_URL = 'http://localhost:8080/public/config'

# Global variable to track the current folder ID
current_folder_id = None

def auth_g_drive():
    """Authenticates and returns a Google Drive service instance."""
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    try:
        service = build("drive", "v3", credentials=creds)
        return service
    except HttpError as error:
        print(f"An error occurred: {error}")

def create_folder(folder_name, parent_id):
    """Create a folder on Google Drive, returns the new folder's ID."""
    service = auth_g_drive()
    body = {
        'name': folder_name,
        'mimeType': "application/vnd.google-apps.folder",
        'parents': [parent_id]
    }
    root_folder = service.files().create(body=body).execute()
    return root_folder['id']

def check_if_folder_exists(folder_name, parent_id):
    """Check if a folder exists on Google Drive."""
    service = auth_g_drive()
    results = service.files().list(
        q=f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and '{parent_id}' in parents",
        pageSize=10, fields="nextPageToken, files(id, name)").execute()
    items = results.get("files", [])
    if items:
        return items[0]['id']  # Return the folder ID if exists
    return None

def write_file(file_name):
    """Upload the image file to Google Drive."""
    try:
        service = auth_g_drive()
        global current_folder_id

        # Ensure folder ID is set
        if not current_folder_id:
            raise ValueError("Current folder ID is not set.")

        file_metadata = {
            'name': f"{file_name}.jpg",
            'parents': [current_folder_id]  # Use the correct folder ID
        }
        file_path = f'./{current_folder_id}/{file_name}.jpg'

        # Correct MIME type for an image
        media = MediaFileUpload(file_path, mimetype='image/jpeg')

        # Check if the file actually exists before uploading
        if not os.path.exists(file_path):
            print(f"Error: {file_path} does not exist. Skipping upload.")
            return

        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        print(f"Uploaded file with ID: {file.get('id')}")
    except HttpError as error:
        print(f"An error occurred: {error}")

def capture_image():
    """Capture an image using the webcam and save it locally and on Google Drive."""
    video = cv2.VideoCapture(0)

    # Ensure the local folder exists
    if current_folder_id and not os.path.exists(current_folder_id):
        os.makedirs(current_folder_id)

    a = 0
    while True:
        a += 1
        check, frame = video.read()
        if not check:
            print("Failed to capture image.")
            break

        # Use a timestamp and count for the filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"{timestamp}_{a}_{str(uuid.uuid4())}"  # Unique filename with timestamp and count
        local_file_path = f"./{current_folder_id}/{file_name}.jpg"

        # Save the captured image locally
        success = cv2.imwrite(local_file_path, frame)
        if success:
            print(f"Image saved locally: {local_file_path}")
        else:
            print(f"Failed to save image: {local_file_path}")
            break

        # Check if image exists and is valid
        if os.path.exists(local_file_path) and os.path.getsize(local_file_path) > 0:
            # Upload the image to Google Drive
            write_file(file_name)
        else:
            print(f"Image file is invalid: {local_file_path}")

        time.sleep(10)

        key = cv2.waitKey(1)
        if key == ord('q'):
            break

    video.release()
    cv2.destroyAllWindows()

def get_current_folder_id_mock():
    return "4f5d0742-b145-4667-9f27-22b3bb5bcc20"

def get_current_folder_id():
  # Make a GET request to the API endpoint using requests.get()
  response = requests.get(CONFIG_URL)

  # Check if the request was successful (status code 200)
  if response.status_code == 200:
      print("Response: " + str(response.json()))
      config = response.json()
      return config["uuid"]
  else:
      print('Error:', response.status_code)
      return None

def start_new_command():
    """Start a new command with a new folder name based on the API command."""
    global current_folder_id

    # Fetch folder ID from the API command
    folder_id = get_current_folder_id_mock()
    if folder_id is None:
        print("Error: Could not fetch folder ID.")
        return
    else:
        print("Folder Id: " + folder_id)

    # Set the folder ID as the current folder
    current_folder_id = folder_id

    # Ensure the new folder is created locally
    if not os.path.exists(current_folder_id):
        os.makedirs(current_folder_id)

    # Ensure the folder is created on Google Drive
    drive_folder_id = check_if_folder_exists(folder_id, ROOT_FOLDER)
    if not drive_folder_id:
        drive_folder_id = create_folder(folder_id, ROOT_FOLDER)
    current_folder_id = drive_folder_id

def main():
    # Start with the folder name from the API command
    start_new_command()
    capture_image()

if __name__ == "__main__":
    main()



