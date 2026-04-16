import os
import time
import requests
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional

load_dotenv()

# keep sending requests to the endpoint untill they tell me it's ready,
# Function to keep checking if the data is ready (The "Are we there yet?" function)
def poll_snapshot_status(
        snapshot_id: str, max_attempts: int = 60, delay: int = 5
) -> bool:
    # INPUT: Takes a unique ID for the job, how many times to check, and how long to wait between checks
    api_key = os.getenv("BRIGHTDATA_API_KEY")
    progress_url = f"https://api.brightdata.com/datasets/v3/progress/{snapshot_id}"
    headers = {"Authorization": f"Bearer {api_key}"}

    # LOOP: Repeat the check up to 60 times
    for attempt in range(max_attempts):
        try:
            print(f"⏳ Checking progress... ({attempt + 1}/{max_attempts})")
            response = requests.get(progress_url, headers=headers)
            response.raise_for_status()

            progress_data = response.json()
            status = progress_data.get("status")

            # LOGIC: Decisions based on the server's answer
            if status == "ready":
                return True  # Success! Stop waiting.
            elif status == "failed":
                return False  # Something broke on the server. Stop.

            # If still "running", wait for a few seconds (delay) before trying again
            time.sleep(delay)

        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(delay)

    # OUTPUT: Returns False if the time runs out before the data is ready
    return False

# we call it once the snapshot is ready
# Function to grab the data once it's finished (The "Delivery" function)
def download_snapshot(
        snapshot_id: str, format: str = "json"
) -> Optional[List[Dict[Any, Any]]]:
    # INPUT: The unique ID of the finished job
    api_key = os.getenv("BRIGHTDATA_API_KEY")
    download_url = f"https://api.brightdata.com/datasets/v3/snapshot/{snapshot_id}?format={format}"
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        # ACTION: Send a final request to download the actual results
        response = requests.get(download_url, headers=headers)
        response.raise_for_status()

        # OUTPUT: Return the data as a Python list/dictionary
        data = response.json()
        return data

    except Exception as e:
        # SAFETY: Returns None if the download fails
        print(f"❌ Error: {e}")
        return None