# config.py
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

CLICKUP_TOKEN = os.getenv("CLICKUP_TOKEN")
HEADERS = {"Authorization": CLICKUP_TOKEN}

# IDs - keep them in one place for easy changes
TEAM_ID = "9012223014"
BESA_SPACE_ID = "90121722741"
OPERATIONS_FOLDER_ID = "90123018368"
BESA_CLIENTS_LIST_ID = "901205091637"