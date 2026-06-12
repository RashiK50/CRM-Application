import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Pydantic will automatically look for GEMINI_API_KEY in the environment or .env file
    GEMINI_API_KEY: str = "MOCK_KEY"
    GROQ_API_KEY: str = "your_default_key_or_none"

    # Configuration to find the .env file one level up from the backend directory
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()