from dotenv import load_dotenv
import os
from pathlib import Path

load_dotenv()

# Main settings
API_KEY = os.getenv("API_KEY")

# Graph Api Settings
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TENANT_ID = os.getenv("TENANT_ID")
MAIL_FROM = "Christian.Angermeier@isartec.de"
MAIL_TO = os.getenv("MAIL_TO")
MAIL_INBOX = "otto.pa@isartec.de"
SITE_ID = "6de60bff-46b2-4c09-b690-651e0d0ab8f3"
DRIVE_ID = "b!_wvmbbJGCUy2kGUeDQq48wGoU_ggXVtOoCg4ZWpY2DYICqDfnPOvSrDLdC6yvpNC"
FOLDER = "Otto/Projekte/"
GRAPH_URL = "https://graph.microsoft.com/v1.0"