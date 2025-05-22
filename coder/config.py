# config.py – Teil des Otto KI-Systems
# © Christian Angermeier 2025

from dotenv import load_dotenv
import os
from pathlib import Path

load_dotenv()

# System
BASE_DIR = Path("/opt/otto")
API_KEY = os.getenv("API_KEY")
