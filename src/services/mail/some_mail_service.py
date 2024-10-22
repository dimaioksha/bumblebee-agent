from src.services.mail.interface import MailService


class SomeMailService(MailService):
    def some_abstract_method(self):
        raise NotImplementedError
