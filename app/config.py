import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/db/rental.db")
BACKUP_DIR: str = os.getenv("BACKUP_DIR", "./data/backups")
SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")
API_KEY: str = os.getenv("API_KEY", "dev-key-123")
