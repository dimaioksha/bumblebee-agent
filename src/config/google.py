from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class GoogleConfig(BaseSettings):

    """Class for loading the necessary env variables."""

    API_KEY: str
    EXAMPLE_ENV: str = Field(default="some-default")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


google_config = GoogleConfig()
