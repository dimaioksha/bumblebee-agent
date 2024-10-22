from src.services.weather.interface import WeatherService


class SomeWeatherService(WeatherService):
    def some_abstract_method(self):
        raise NotImplementedError
