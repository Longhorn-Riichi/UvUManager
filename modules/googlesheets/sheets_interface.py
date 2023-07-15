from __future__ import print_function

import os
from os.path import join, dirname

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class Sheets_Interface:
    def __init__(self, spreadsheet_id=None):
        # If modifying these scopes, delete the file token.json.
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
        
        current_path = os.path.dirname(__file__)
        credentials_json_path = join(current_path, 'credentials.json')
        token_json_path = join(current_path, 'token.json')

        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.

        if os.path.exists(token_json_path):
            creds = Credentials.from_authorized_user_file(token_json_path, SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_json_path, SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(token_json_path, 'w') as token:
                token.write(creds.to_json())

        # Calling the Sheets API
        self.creds = creds
        self.spreadsheet_id = spreadsheet_id
        self.service = build('sheets', 'v4', credentials=self.creds)

    def read_xl(self, sheet_range):
        try:
            sheet = self.service.spreadsheets()
            result = sheet.values().get(spreadsheetId=self.spreadsheet_id, range=sheet_range).execute()

            # result is type dict with range, majorDimension, and values as keys
            # values is of type list, returns empty list if values key not found
            values = result.get('values', [])

            if not values:
                print('No data found.')
                return

            return values
        
        except HttpError as err:
            print(err)

    def update_xl(self, sheet_range, values_list,):
        value_input_option = "USER_ENTERED"
        value_range_body = {
            'values': values_list
        }

        try:
            request = self.service.spreadsheets().values().update(spreadsheetId=self.spreadsheet_id, range=sheet_range, valueInputOption=value_input_option, body=value_range_body)
            request.execute()

        except HttpError as err:
            print(err)

    def append_xl(self, sheet_range, values_list):
        value_input_option = "USER_ENTERED"
        value_range_body = {
            'values': values_list
        }

        try:
            request = self.service.spreadsheets().values().append(spreadsheetId=self.spreadsheet_id, range=sheet_range, valueInputOption=value_input_option, body=value_range_body)
            request.execute()

        except HttpError as err:
            print(err)

if __name__ == "__main__":
    value = [['test workzz']]
    sheet = Sheets_Interface(spreadsheet_id="1e4pHYPRkOhgAd0N9q2bImpr7c1oe9IilIPWS70JNgk4")
    sheet.append_xl("Test 2", value)