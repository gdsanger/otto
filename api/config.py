# config.py – Teil des Otto KI-Systems
# © Christian Angermeier 2025

from dotenv import load_dotenv
import os
from pathlib import Path

load_dotenv()

# System
BASE_DIR = Path("/home/anger")
API_KEY = os.getenv("API_KEY")

# Azure / GarphAPI
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TENANT_ID = "240f487f-9038-4806-bfda-6a617ee5da14"
MAIL_FROM = "Christian.Angermeier@isartec.de"
MAIL_TO = os.getenv("MAIL_TO")
SITE_ID = "6de60bff-46b2-4c09-b690-651e0d0ab8f3"
DRIVE_ID = "b!_wvmbbJGCUy2kGUeDQq48wGoU_ggXVtOoCg4ZWpY2DYICqDfnPOvSrDLdC6yvpNC"
FOLDER = "Otto/Projekte/"
GRAPH_URL = "https://graph.microsoft.com/v1.0"
