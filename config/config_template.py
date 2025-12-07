"""
Configuration Template
Copy this to config.py and add your credentials
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent

# Google Calendar API settings
SCOPES = ['https://www.googleapis.com/auth/calendar']
CREDENTIALS_FILE = PROJECT_ROOT / 'config' / 'credentials.json'
TOKEN_FILE = PROJECT_ROOT / 'config' / 'token.json'

# Default timezone
DEFAULT_TIMEZONE = 'Europe/Brussels'  # Change to your timezone

# Conflict detection settings
MINIMUM_GAP_MINUTES = 15

# Azure OpenAI settings - REPLACE WITH YOUR CREDENTIALS
AZURE_OPENAI_ENDPOINT = "YOUR_AZURE_ENDPOINT_HERE"  # e.g., https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY = "YOUR_API_KEY_HERE"
AZURE_OPENAI_DEPLOYMENT = "gpt-4o"  # Your deployment name
AZURE_API_VERSION = "2024-08-01-preview"

MAX_TOKENS = 4000
TEMPERATURE = 0.2
