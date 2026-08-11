# api.py
import requests
import time

def clickup_get(endpoint, headers, params=None, delay=0.3):
    url = f"https://api.clickup.com/api/v2/{endpoint}"
    res = requests.get(url, headers=headers, params=params)
    if res.status_code != 200:
        raise Exception(f"ClickUp API error: {res.status_code} - {res.text}")
    time.sleep(delay)  # avoid rate limit
    return res.json()

