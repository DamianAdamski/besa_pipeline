# config.py
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()  # Load environment variables from .env file

CLICKUP_TOKEN = os.getenv("CLICKUP_TOKEN")

if not CLICKUP_TOKEN:
    raise ValueError("CLICKUP_TOKEN was not found in .env")

HEADERS = {"Authorization": CLICKUP_TOKEN}

# IDs - keep them in one place for easy changes
TEAM_ID = "9012223014"
BESA_SPACE_ID = "90121722741"
OPERATIONS_FOLDER_ID = "90123018368"
BESA_CLIENTS_LIST_ID = "901205091637"

# Define the base directory for the project
BASE_DIR = Path(__file__).resolve().parent

# Raw export + incremental-sync state, shared between main.py and export.py
RAW_DATA_FILE = BASE_DIR / "data" / "raw" / "raw_data.xlsx"
LAST_SYNC_FILE = BASE_DIR / "data" / "raw" / "last_sync.json"

# Log file accumulating history across runs
LOG_FILE = BASE_DIR / "logs" / "pipeline.log"