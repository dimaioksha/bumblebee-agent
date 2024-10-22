from dataclasses import dataclass

from src.infrastructure.integrations.google_calendar import get_google_calendar
from src.services.calendar.interface import CalendarService
from src.services.mail.interface import MailService
from src.services.weather.interface import WeatherService

from src.services.calendar.google import GoogleCalendar
from src.services.mail.some_mail_service import SomeMailService
from src.services.weather.some_weather_service import SomeWeatherService


@dataclass
class Bootstrap:
    calendar_service: CalendarService
    mail_service: MailService
    weather_service: WeatherService


def get_prod_bootstrap() -> Bootstrap:
    google_integration = get_google_calendar()
    return Bootstrap(
        calendar_service=GoogleCalendar(google_integration),
        mail_service=SomeMailService(),
        weather_service=SomeWeatherService()
    )
