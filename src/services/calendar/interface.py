from abc import abstractmethod, ABC


class CalendarService(ABC):
    @abstractmethod
    def some_abstract_method(self):
        raise NotImplementedError
