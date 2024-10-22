from src.services.calendar.interface import CalendarService


class GoogleCalendar(CalendarService):
    def __init__(self, google_integration):
        self.google_integration = google_integration
    def some_abstract_method(self):
        raise NotImplementedError
