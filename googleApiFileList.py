#!/usr/bin/python3

"""
  To authenticate in Google follow the instructions at

  https://developers.google.com/drive/v3/web/quickstart/python

  A credentials.json file needs to placed in the same directory

  with this script. The link above contains the instruction on

  how to obtain this file.

"""

import httplib2

import os

import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import pandas as pd


# If modifying these scopes, delete your previously saved credentials

# at ~/.credentials/drive-python-quickstart.json

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

CLIENT_SECRET_FILE = 'credentials.json'

APPLICATION_NAME = 'Drive API Python Quickstart'

folder_id = 'ADD FOLDER ID HERE' #Set to id of the parent folder you want to list (should be content folder)
folder_list = []
all_folders = []
file_list = []



def get_credentials():
    """Gets valid user credentials from storage.



    If nothing has been stored, or if the stored credentials are invalid,

    the OAuth2 flow is completed to obtain the new credentials.



    Returns:

        Credentials, the obtained credential.

    """

    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return creds



def get_root_folder(): # get's folder list from original root folder

    service = build('drive', 'v3', credentials = creds)

    page_token = None
    while True:
        results = service.files().list(q="mimeType = 'application/vnd.google-apps.folder' and '"+folder_id+"' in parents",
        pageSize=1000, fields="nextPageToken, files(id, mimeType)",pageToken=page_token, supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
        folders = results.get('files', [])

        if not folders:
             print('No folders found.')

        else:

            for folder in folders:
                id = folder.get('id')
                folder_list.append(id)
        page_token = results.get('nextPageToken', None)
        if page_token is None:
            break

def get_all_folders(folder_list): #creates list of all sub folder under root, keeps going until no folders underneath

    for folder in folder_list:
        page_token = None
        while True:
            additional_folders = []
            service = build('drive', 'v3', credentials=creds)
            results = service.files().list(
                q="mimeType = 'application/vnd.google-apps.folder' and '" +folder+ "' in parents",

                pageSize=1000, fields="nextPageToken, files(id, mimeType)", pageToken=page_token,supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
            items = results.get('files', [])

            for item in items:
                id = item.get('id')
                additional_folders.append(id)
            if not additional_folders:
                pass
            else:
               all_folders.extend(additional_folders)
               folder_list = additional_folders
               get_all_folders(folder_list)
            page_token = results.get('nextPageToken', None)
            if page_token is None:
                break

def merge(): #merges sub folder list with full list
    global full_list
    full_list = all_folders + folder_list
    full_list.append(folder_id)


def get_file_list(): #runs over each folder generating file list, for files over 1000 uses nextpagetoken to run additional requests, picks up metadata included in the request


    for folder in full_list:
        service = build('drive', 'v3', credentials=creds)

        page_token = None
        while True:
            results = service.files().list(
                q="'" + folder + "' in parents",

                pageSize=1000, fields="nextPageToken, files(name, md5Checksum, mimeType, size, createdTime, modifiedTime, id, parents, trashed, copyRequiresWriterPermission, shortcutDetails, exportLinks)", pageToken=page_token, supportsAllDrives=True, includeItemsFromAllDrives=True).execute()

            items = results.get('files', [])
            for item in items:
                name = item['name']

                checksum = item.get('md5Checksum')

                size = item.get('size', '-')

                id = item.get('id')

                mimeType = item.get('mimeType', '-')

                createdTime = item.get('createdTime', 'No date')

                modifiedTime = item.get('modifiedTime', 'No date')

                parents = item.get('parents')

                trashed = item.get('trashed')

                copyRequiresWriterPermission = item.get('copyRequiresWriterPermission')

                exportLinks = item.get('exportLinks')

                if mimeType == 'application/vnd.google-apps.document' and exportLinks != None:
                    standardDownloadLink = exportLinks['application/vnd.openxmlformats-officedocument.wordprocessingml.document']
                    PDFDownloadLink = exportLinks['application/pdf']
                elif mimeType == 'application/vnd.google-apps.spreadsheet' and exportLinks != None:
                    standardDownloadLink = exportLinks['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']
                    PDFDownloadLink = exportLinks['application/pdf']
                elif mimeType == 'application/vnd.google-apps.presentation' and exportLinks != None:
                    standardDownloadLink = exportLinks['application/vnd.openxmlformats-officedocument.presentationml.presentation']
                    PDFDownloadLink = exportLinks['application/pdf']
                elif mimeType == 'application/vnd.google-apps.jam' and exportLinks != None:
                    standardDownloadLink = exportLinks['application/pdf']
                    PDFDownloadLink = ''
                elif mimeType == 'application/vnd.google-apps.drawing' and exportLinks != None:
                    standardDownloadLink = exportLinks['image/png']
                    PDFDownloadLink = ''
                else:
                    standardDownloadLink = ''
                    PDFDownloadLink = ''

                ShortcutDetails = item.get('shortcutDetails')

                if ShortcutDetails != None:
                        ShortcutID = ShortcutDetails['targetId']

                        ShortcutMimeType = ShortcutDetails['targetMimeType']

                        Shortcuts = service.files().get(fileId=ShortcutID,
                                                     fields = "copyRequiresWriterPermission, exportLinks, createdTime, modifiedTime", supportsAllDrives=True).execute()
                        ShortcutCopyRequiresWritersPermissions = Shortcuts['copyRequiresWriterPermission']

                        ShortcutCreatedTime = Shortcuts['createdTime']

                        ShortcutModifiedTime = Shortcuts['modifiedTime']

                        try:
                            exportLinks = Shortcuts['exportLinks']
                        except:
                            pass

                        if ShortcutMimeType == 'application/vnd.google-apps.document' and exportLinks != None:
                            standardDownloadLink = exportLinks[
                                'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
                            PDFDownloadLink = exportLinks['application/pdf']
                        elif ShortcutMimeType == 'application/vnd.google-apps.spreadsheet' and exportLinks != None:
                            standardDownloadLink = exportLinks[
                                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']
                            PDFDownloadLink = exportLinks['application/pdf']
                        elif ShortcutMimeType == 'application/vnd.google-apps.presentation' and exportLinks != None:
                            standardDownloadLink = exportLinks[
                                'application/vnd.openxmlformats-officedocument.presentationml.presentation']
                            PDFDownloadLink = exportLinks['application/pdf']
                        elif ShortcutMimeType == 'application/vnd.google-apps.jam' and exportLinks != None:
                            standardDownloadLink = exportLinks['application/pdf']
                            PDFDownloadLink = ''
                        elif ShortcutMimeType == 'application/vnd.google-apps.drawing' and exportLinks != None:
                             standardDownloadLink = exportLinks['image/png']
                             PDFDownloadLink = ''
                        else:
                            pass

                else:
                        ShortcutID = None
                        ShortcutMimeType = None
                        ShortcutCopyRequiresWritersPermissions = None
                        ShortcutCreatedTime = None
                        ShortcutModifiedTime = None


                file_list.append([name, checksum, mimeType, size, createdTime, modifiedTime, id, parents, trashed, copyRequiresWriterPermission, ShortcutID, ShortcutMimeType, ShortcutCreatedTime,ShortcutModifiedTime, ShortcutCopyRequiresWritersPermissions, standardDownloadLink, PDFDownloadLink])

            page_token = results.get('nextPageToken', None)
            if page_token is None:
                break
    files = pd.DataFrame(file_list,columns=['file_name','checksum_md5','mimeType','size', 'date_created', 'date_last_modified','google_id','google_parent_id', 'trashed', 'download_require_permission', 'ShortcutID', 'ShortcutMimeType','shortcutCreatedTime', 'shortcutModifiedTime', 'ShortcutCopyRequiresWritersPermissions','standardDownloadLink','PDFDownloadLink'])
    files.drop(files[files['trashed'] == True].index, inplace=True) #removes files which have True listed in trashed, these are files which had been moved to the recycle bin
    foldernumbers = files['mimeType'].str.contains('application/vnd.google-apps.folder').sum()
    filenumbers = (~files['mimeType'].str.contains('application/vnd.google-apps.folder')).sum()
    print('Number of folders is: ', foldernumbers)
    print('Number of files is: ', filenumbers)
    files.to_csv('GoogleAPIMetadata.csv', index=False)


if __name__ == '__main__':
    creds = get_credentials()
    print('Collecting folder id list')
    get_root_folder()
    get_all_folders(folder_list)
    merge()
    print('Generating file metadata list')
    get_file_list()
