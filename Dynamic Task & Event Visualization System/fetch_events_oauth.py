import datetime
import os
import pytz
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import pickle

SCOPES = [
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/tasks.readonly'
]
CLIENT_SECRET_FILE = 'credentials.json'

def get_calendar_service():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return build('calendar', 'v3', credentials=creds), build('tasks', 'v1', credentials=creds)

def fetch_events_and_tasks():
    try:
        calendar_service, tasks_service = get_calendar_service()
        tz = pytz.timezone('Asia/Kolkata')
        now_ist = datetime.datetime.now(tz)
        now_utc = now_ist.astimezone(pytz.utc)
        now = now_utc.isoformat()
        later_utc = (now_ist + datetime.timedelta(days=1)).astimezone(pytz.utc)
        later = later_utc.isoformat()

        events_result = calendar_service.events().list(
            calendarId='primary', timeMin=now, timeMax=later, singleEvents=True, orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])
        
        tasks_result = tasks_service.tasks().list(
            tasklist='@default', dueMin=now, dueMax=later, showCompleted=False
        ).execute()
        tasks = tasks_result.get('items', [])

        combined = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            combined.append({
                'summary': event.get('summary', 'No Title'),
                'start': start,
                'end': end
            })

        for task in tasks:
            due = task.get('due')
            combined.append({
                'title': task.get('title', 'No Title'),
                'due': due
            })

        return combined

    except Exception as e:
        print(f"Error fetching events and tasks: {e}")
        return []
