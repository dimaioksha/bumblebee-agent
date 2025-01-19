import os
from os_envs import *

from google.oauth2 import service_account
from googleapiclient.discovery import build
from langchain.tools import tool
from datetime import datetime, timedelta

def authenticate():
        credentials = service_account.Credentials.from_service_account_file(
            os.environ['KEYFILE'],
            scopes=['https://www.googleapis.com/auth/calendar', 'https://www.googleapis.com/auth/calendar.events']
        )
        return credentials

class Calendar:
    def __init__(self):
        self.auth = service_account.Credentials.from_service_account_file(
            os.environ['KEYFILE'],
            scopes=['https://www.googleapis.com/auth/calendar', 'https://www.googleapis.com/auth/calendar.events']
        )

    def delete_google_calendar_event(self, event_id: str):
        service = build('calendar', 'v3', credentials=self.auth)
        try:
            service.events().delete(calendarId=os.environ['CALENDAR_ID'], eventId=event_id).execute()
            return(f'Событие с ID "{event_id}" успешно удалено.')
        except Exception as e:
            return(f'Произошла ошибка при удалении события: {e}')


    def calendar_get_task(self) -> None:
        now = datetime.utcnow().isoformat() + "Z"
        service = build('calendar', 'v3', credentials=self.auth)
        
        # Fetch events from the calendar
        events_result = service.events().list(
            calendarId=os.environ['CALENDAR_ID'],
            timeMin=now,
            maxResults=30,
            singleEvents=True,
            orderBy="startTime",
        ).execute()
        
        events = events_result.get("items", [])
        #print('Fetched events:')
        
        result = []
        for event in events:
            #print(event)
            summary = event.get("summary", "No Title")
            description = event.get("description", "No Description")
            start = event["start"].get("dateTime", event["start"].get("date"))
            end = event["end"].get("dateTime", event["end"].get("date"))
            reminders = event.get("reminders", {})
            google_calendar_id = event.get("id")
            notification_times = []
            use_default = reminders.get('useDefault', False)
            
            if True:
                overrides = reminders.get('overrides', [])
                for override in overrides:
                    method = override.get('method')
                    minutes = override.get('minutes')
                    notification_times.append(f"{minutes} minutes before via {method}")
                if not overrides:
                    notification_times.append("No reminders set for this event")
            
            # Print the event information
            # print(f"Title: {summary}")
            # print(f"Description: {description}")
            # print(f"Start Time: {start}")
            # print(f"End Time: {end}")
            # print(f"Notification Times: {notification_times}")
            # print('-' * 40)
            result.append({'summary': summary, 'description': description, 'start': start, 'end': end, 'google_calendar_id': google_calendar_id, 'notification_times': notification_times})
        return result


    def add_google_calendar_event(self, context_variables):
        summary = context_variables['summary']
        description = context_variables['description']
        dateTime_start = context_variables['dateTime_start']
        dateTime_end = context_variables['dateTime_end']
        service = build('calendar', 'v3', credentials=self.auth)
        event = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': dateTime_start,
                'timeZone': 'Europe/Riga',
            },
            'end': {
                'dateTime': dateTime_end,
                'timeZone': 'Europe/Riga',
            }
        }

        event_result = service.events().insert(calendarId=os.environ['CALENDAR_ID'], body=event).execute()
        #print("Событие создано: %s" % (event_result.get('htmlLink')))
        return "Событие успешно создано."
