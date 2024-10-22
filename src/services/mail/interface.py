from abc import abstractmethod, ABC


class MailService(ABC):
    @abstractmethod
    def some_abstract_method(self):
        raise NotImplementedError
