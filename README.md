# BESA Data Pipeline

This project is a Python-based tool that collects project data from **ClickUp** and converts it into clean, structured tables for reporting and analysis. It handles projects, materials, and services, and exports them to Excel and CSV files. It runs automatically every day, uploads the results to Dropbox, and syncs current projects into the Mapogos Pricing app's database — so reports stay up to date and the pricing app always has a real, current list of projects to price against, without anyone needing to run anything by hand.

---

## Key Benefits

- Automatically fetches project data from ClickUp
- Only re-fetches what's changed since the last run, so daily runs stay fast
- Organizes and cleans data for easier analysis
- Generates ready-to-use Excel and CSV reports
- Runs on a daily schedule in the cloud and uploads results to Dropbox automatically
- Saves time and reduces manual data entry errors

---

## How It Works

1. **Extract:** Gets all tasks and subtasks from ClickUp, including custom fields. Only tasks changed since the last run are fetched, and the results are merged into the existing dataset.
2. **Transform:** Cleans and organizes the data into structured tables:
   - Projects
   - Materials
   - Services
3. **Load / Export:** Saves the cleaned data into Excel and CSV files.
4. **Upload:** Sends the finished reports (and the log of the run itself) to Dropbox, and upserts current projects (name, client, status, dates, accepted price) into the `besa_projects` table in the Mapogos Pricing app's Supabase database.

---

## Output Files

**Raw Data (Excel):** `data/raw/raw_data.xlsx`

| Sheet     | Description |
|-----------|-------------|
| Projects  | Basic project details (client, status, dates, etc.) |
| Materials | Materials used with costs and quantities |
| Services  | Services performed with prices and descriptions |

**Cleaned Data (Excel & CSV):** `data/clean/besaconstruction_clean_data.xlsx`

| Table       | Description |
|-------------|-------------|
| ClientDim   | Clean client information |
| ProjectDim  | Project details linked to clients |
| ProjectFact | Project metrics including total cost |
| ExpenseFact | Material and service costs |

**Where to actually check your reports:** the Dropbox app folder the pipeline uploads to (`Apps/<app name>` in your Dropbox) always has the latest version of every file above, plus `pipeline.log` — the full history of every run, useful for checking a scheduled run actually happened or diagnosing a failure without needing to open this repo at all.

---

## How to Use (running it yourself, locally)

1. Clone the repository:

```bash
git clone https://github.com/yourusername/besa_pipeline.git
cd besa_pipeline
```

2. Install Python dependencies:
```pip install -r requirements.txt```

3. Create a file in the project folder called `.env` with the following:

```
CLICKUP_TOKEN = YOUR_CLICKUP_TOKEN
DROPBOX_APP_KEY = YOUR_DROPBOX_APP_KEY
DROPBOX_APP_SECRET = YOUR_DROPBOX_APP_SECRET
DROPBOX_REFRESH_TOKEN = YOUR_DROPBOX_REFRESH_TOKEN
SUPABASE_URL = YOUR_SUPABASE_PROJECT_URL
SUPABASE_SERVICE_ROLE_KEY = YOUR_SUPABASE_SERVICE_ROLE_KEY
```

`CLICKUP_TOKEN` comes from your ClickUp account settings. The three Dropbox values come from a Dropbox app (Scoped access, **App folder** type) created at [dropbox.com/developers/apps](https://www.dropbox.com/developers/apps), with `files.content.read`/`files.content.write` permissions enabled and a one-time OAuth authorization completed to obtain the refresh token — this is already set up for the current Dropbox app folder; you'd only need to redo it if that app's access is ever revoked.

`SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` come from the Mapogos Pricing app's Supabase project (Settings → API). This deliberately uses the **service_role** key, not the anon/publishable one — that key is only ever used by this trusted backend job, and it must never be put in the pricing app itself or shared anywhere client-facing, since it bypasses all database security rules.

4. Run the pipeline in your terminal: `python main.py`

5. Check the output:
   - Raw Excel: `data/raw/raw_data.xlsx`
   - Cleaned Excel: `data/clean/besaconstruction_clean_data.xlsx`
   - Cleaned CSV: `data/clean/*.csv`
   - Run log: `logs/pipeline.log`
   - All of the above are also uploaded to the shared Dropbox folder after a successful run

---

## Automatic Daily Runs (GitHub Actions)

The pipeline also runs on its own every day via [`.github/workflows/daily-pipeline.yml`](.github/workflows/daily-pipeline.yml) (06:00 UTC), with no machine needing to be left on. Since each run happens on a fresh, empty cloud runner, `main.py` restores its previous state (the merge baseline and sync timestamp) from Dropbox at startup if it isn't found locally, then uploads everything — including an updated `pipeline.log` — back to Dropbox once the run finishes.

To set this up on a new copy of this repo, add these as repository secrets (Settings → Secrets and variables → Actions): `CLICKUP_TOKEN`, `DROPBOX_APP_KEY`, `DROPBOX_APP_SECRET`, `DROPBOX_REFRESH_TOKEN`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`. You can also trigger a run manually any time from the **Actions** tab → **Daily BESA Pipeline** → **Run workflow**, without waiting for the schedule.

---

## PROJECT STRUCTURE
```text
besa_pipeline/
├─ .github/
│  └─ workflows/
│     └─ daily-pipeline.yml  # Runs the pipeline automatically every day
├─ data/
│  ├─ raw/       # Raw Excel exports + last_sync.json (incremental-sync state)
│  └─ clean/     # Cleaned Excel and CSV exports
├─ logs/
│  └─ pipeline.log      # Accumulated log of every run
├─ extract.py            # Fetch tasks and subtasks from ClickUp
├─ transform.py          # Clean, organize, and merge the data
├─ export.py             # Save data to Excel/CSV
├─ api.py                # ClickUp API helper (with retry on failure)
├─ config.py             # API keys, list IDs, and file paths
├─ sync_state.py         # Tracks the timestamp of the last successful run
├─ dropbox_upload.py     # Uploads results to (and restores state from) Dropbox
├─ supabase_upload.py    # Syncs current projects into the pricing app's database
├─ main.py               # Runs the full pipeline
└─ README.md             # This file
```