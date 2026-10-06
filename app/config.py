import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "Tutor Socrático IA"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "chave_secreta_dev_12345")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./tutor_socratico.db")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

settings = Settings()