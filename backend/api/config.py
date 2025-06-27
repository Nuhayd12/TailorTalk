import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Google Calendar API
    google_credentials_file: str = "credentials.json"
    google_token_file: str = "token.pickle"
    
    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True
    
    # Calendar Settings
    default_meeting_duration: int = 60
    business_start_hour: int = 9
    business_end_hour: int = 17
    timezone: str = "UTC"
    
    # LLM Settings
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    class Config:
        env_file = ".env"

settings = Settings()