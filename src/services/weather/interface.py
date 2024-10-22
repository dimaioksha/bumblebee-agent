from abc import abstractmethod, ABC


class WeatherService(ABC):
    @abstractmethod
    def some_abstract_method(self):
        raise NotImplementedError
