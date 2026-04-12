import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load .env file
env_path = os.path.join(os.path.dirname(__file__), '../../../env/.env')
load_dotenv(dotenv_path=env_path)

class Settings(BaseSettings):
    app_name: str = "PersonaXR API"
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    class Config:
        env_file = ".env"

# Instantiate the settings once to be used across the app
settings = Settings()