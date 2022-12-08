from datetime import datetime
from os import path
import gspread
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class Scheduler:
    ''' 
        Scheduler object for extracting workshifts from Google Sheets shift plan and creating corresponding events in Google Calendar.\n
        It use `OAuth Client ID` credentials to authenticate action in particular scopes. To make it works correctly you have to grant access 
        to your sheets, drive and calendar data. 

        Scheduler logic was implemented in two ways: 
        - sensitive for letters with accents (`'v2'`) and 
        - insensitive ('`v1`').

        (Warning) In case of use scheduler version 2 user must enter full name with attention to special characters.

        Args:
        sheet_name: string
            The title of Google Sheet to work with.
        worker: string
            The full name of worker whose workshifts to extract.
        version: string, (Optional) 
            Version of the Scheduler to use; default: `v1`.
    '''
    def __init__(self, sheet_name: str, worker: str, version='v1'):
        self.version = version
        self.sheet_name = sheet_name
        self.worker = self.to_short(worker)
        self.days_mapper = {
            0: ['A', 'B'], 
            1: ['C', 'D'], 
            2: ['E', 'F'], 
            3: ['G', 'H'], 
            4: ['I', 'J'], 
            5: ['K', 'L'], 
            6: ['M', 'N']}
    
    @staticmethod
    def remove_accents(text: str):
        '''  Replace latin polish letters including accents with common ones'''
        letter_mapper = {'ś': 's', 'ą': 'a', 'ć': 'c', 'ę': 'e', 'ó': 'o', 'ł': 'l', 'ń': 'n', 'ź': 'z', 'ż': 'z'}
        text = text.lower()
        for letter in letter_mapper.keys():
            if letter in text:
                text = text.replace(letter, letter_mapper[letter])
        return text

    @staticmethod
    def to_short(full_name: str):
        ''' Return person name in J. Doe format '''
        f_name, l_name = full_name.split(' ')[0][0], full_name.split(' ')[1]
        short = '. '.join([f_name, l_name])
        return short

    def clean_record(self, value: str):
        ''' Clean values to extract first and last name in specific format '''
        value = value.replace(' ', '').replace('PLAKATY', '')
        if len(value) > 1:
            if '/' in value:
                value = value.split('/')[1]
            return self.remove_accents(value)
        return value

    def load_sheet(self):
        ''' Authorize user to Google Sheets API using credential from JSON file and open spredsheet of given title '''
        print(f'Loading "{self.sheet_name}" from Google Sheets...')
        credentials = self.get_cred()
        file = gspread.authorize(credentials)
        sheet = file.open(self.sheet_name)
        return sheet

    @staticmethod
    def get_cred():
        ''' Get credentials to Google Sheets & Google Calendar APIs from JSON file. If doesn't exists open a console with link to user consent screen. '''
        credentials = None
        scopes = [
                "https://www.googleapis.com/auth/calendar",
                "https://www.googleapis.com/auth/calendar.events",
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
                ]
        if path.exists('token.json'):
            credentials = Credentials.from_authorized_user_file('token.json', scopes)
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "client_secret.json", scopes)

                credentials = flow.run_console()

                with open('token.json', 'w') as token:
                    token.write(credentials.to_json())

        return credentials

    def api_build(self):
        ''' Build a Google Calendar API Resource to interact with '''
        print('Building Google Calendar API Resource...')
        credentials = self.get_cred()
        service = build('calendar', 'v3', credentials=credentials)
        self.GOOGLE_CALENDAR_API = service
 
    @staticmethod
    def create_event(
            title: str,
            location: str,
            startDate: str,
            endDate: str):
        ''' Return dictionary representing Google Calendar Event object'''
        return {
            'summary': title, 
            'location': location, 
            'start': {
                'dateTime': startDate, 
                "timeZone": "Europe/Warsaw",
                }, 
            'end': {
                'dateTime': endDate, 
                "timeZone": "Europe/Warsaw",
                }, 
            'reminders': {
                'useDefault': False, 
                'overrides': [
                    {"method": "popup", 'minutes': 15}
                    ], 
                }
            }

# First version of helper functions (special chars insensitive)
    def get_dates(self):
        ''' Return list of dates from the worksheet converted to "YYYY-mm-dd" format '''
        print('Extracting dates...')
        ws = self.sheet.worksheet('PT-CZW')
        raw_dates = ws.row_values(5)
        raw_dates = list(filter(lambda date: len(date) > 0, raw_dates))
        dates = []
        for date in raw_dates:
            date = date.split(' ')
            date.append(str(datetime.now().date().year))
            date = '-'.join(date)
            date = datetime.strptime(date, "%d-%b-%Y").date().strftime("%Y-%m-%d")
            dates.append(date)
        return dates

    def get_hours(self):
        ''' Return list of lists including start and end hours from worksheet '''
        print('Extracting hours...')
        hours = []
        ws = self.sheet.worksheet('PT-CZW')
        for values in self.days_mapper.values():
            range1 = values[0] + '7:' + values[0] + '15'
            range2 = values[0] + '24:' + values[0] + '31'
            customer_service = ws.get(range1, major_dimension='COLUMNS')[0]
            ticket_agent = ws.get(range2, major_dimension='COLUMNS')[0]
            hours.append(customer_service + ticket_agent)
        hours = [[list(map(lambda hour: hour + ':00', hour[:11].replace(' ', '').replace('.', ':').replace('24', '00').split('-'))) for hour in sublist] for sublist in hours]
        return hours

    def get_workshifts(self):
        ''' Return list of lists representing particular workshift including date and hours '''
        print(f'Extracting "{self.worker}" workshifts...')
        workshifts = []
        worker = self.remove_accents(self.worker).replace(' ', '')
        ws = self.sheet.worksheet('PT-CZW')
        for key, value in self.days_mapper.items():
            range1 = value[-1] + '7:' + value[-1] + '15'
            range2 = value[-1] + '24:' + value[-1] + '31'
            customer_service = [self.clean_record(name) for sublist in ws.get(range1) for name in sublist]  # flatten the list of names
            ticket_agent = [self.clean_record(name) for sublist in ws.get(range2) for name in sublist] # flatten the list of names
            employees = customer_service + ticket_agent
            if worker in employees:
                shift = [self.dates[key], self.hours[key][employees.index(worker)]]
                workshifts.append(shift)
        return workshifts

    def add_event(self, shift: list):
        ''' Insert event to the calendar with use of Google Calendar API '''
        print('Adding event...')
        title = '<YOUR TITLE>'
        location = '<YOUR LOCATION>'
        
        start = shift[0] + 'T' + shift[1][0]
        if shift[1][1][:2] == '00':
            shift[0] = shift[0][:-2] + str(int(shift[0][-2:]) + 1)

        end = shift[0] + 'T' + shift[1][1]
        event = self.create_event(title, location, start, end)
        try:
            self.GOOGLE_CALENDAR_API.events().insert(calendarId='primary', body=event).execute()
        except HttpError as error:
            print('An error occurred: ', error)
  
# Second version of helper functions (special chars sensitive)
    def get_workshifts_v2(self):
        ''' Return list of cell objects matching given value including row number and column number '''
        print('Extracting workshifts...')
        normal = self.sheet.findall(self.worker)
        outlier = self.sheet.find(self.worker + ' PLAKATY')
        workshifts = [outlier] + normal if outlier else normal 
        return workshifts

    def get_hours_v2(self):
        ''' Return list of hours corresponding to cells representing workshifts'''
        print('Extracting hours...')
        hours = []
        for cell in self.workshifts:
            hours.append(self.sheet.cell(cell.row, cell.col-1).value[:11].replace(' ', '').replace('.',':').replace('24', '00'))
        hours = [hour.split('-') for hour in hours]
        hours = [[datetime.strptime(item+':00', '%H:%M:%S').time().strftime('%H:%M:%S') for item in hour] for hour in hours]
        return hours

    def get_dates_v2(self):
        ''' Return list of dates corresponding to cells representing workshifts'''
        print('Extracting dates...')
        days = []
        for cell in self.workshifts:
            days.append(self.sheet.cell(5, cell.col-1).value)
        days = [day + ' ' + str(datetime.now().date().year) for day in days]
        days = [datetime.strptime(day, '%d %b %Y').date().strftime('%Y-%m-%d') for day in days]
        return days

    def add_event_v2(self, date: str, hours: list):
        ''' Insert event to the calendar with use of Google Calendar API '''
        print('Adding event...')
        title = '<YOUR TITLE>'
        location = '<YOUR LOCATION>'

        start = date + 'T' + hours[0]
        if hours[1][:2] == '00':
            date = date[:-2] + str(int(date[-2:]) + 1)    
        end = date + 'T' + hours[1]
        event = self.create_event(title, location, start, end)
        try:
            self.GOOGLE_CALENDAR_API.events().insert(calendarId='primary', body=event).execute()
        except HttpError as error:
            print('An error occurred: ', error)

    def execute(self):
        ''' Execute Scheduler logic depending on version declared. '''
        self.api_build()    
        if self.version == 'v2':
            self.sheet = self.load_sheet().worksheet('PT-CZW')
            self.workshifts = self.get_workshifts_v2()
            self.hours = self.get_hours_v2()
            self.dates = self.get_dates_v2()
            for i in range(len(self.workshifts)):
                self.add_event_v2(self.dates[i], self.hours[i])
        else:
            self.sheet = self.load_sheet()
            self.dates = self.get_dates()
            self.hours = self.get_hours()
            self.workshifts = self.get_workshifts()
            for event in self.workshifts:
                self.add_event(event)
        
        print('Events successfuly added!')
    
