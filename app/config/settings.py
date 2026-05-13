import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-fallback'
    DEBUG = os.environ.get('DEBUG', 'False').lower() in ['true', '1', 't']
