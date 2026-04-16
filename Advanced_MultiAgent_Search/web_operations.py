# all operations related to web scrapping and using brightdata sevice

from dotenv import load_dotenv # import our env variables
import os
import requests
from urllib.parse import quote_plus # allow us to turn normal string to query parameter in out url
from  snapshot_operations import download_snapshot, poll_snapshot_status

load_dotenv()

dataset_id = "gd_lvz8ah06191smkebj4"

# make the req and check the responses
def _make_api_request(url, **kwargs):# reusable function so we can use it anytime we want to send  api request to bright data
    api_key = os.getenv("BRIGHTDATA_API_KEY")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        # INPUT: Send request to URL with headers and extra settings like post in social media so post the request
        response = requests.post(url, headers=headers, **kwargs)

        # VALIDATION: Check response if it success or not- if not raise the flag and jump to exception
        response.raise_for_status()

        # OUTPUT: Convert the raw website data into a Python dictionary
        return response.json()

    except requests.exceptions.RequestException as e:
        # SAFETY: Catch internet issues (like bad URLs or timeouts)
        print(f"API request failed: {e}")
        return None

    except Exception as e:
        # BACKUP: Catch random glitches you didn't expect
        print(f"Unknown error: {e}")
        return None

def serp_search(query, engine="google"):
    # INPUT: The 'query' is your question; 'engine' is the tool you choose.

    # LOGIC: Picking the right destination based on your choice.
    if engine == "google":
        base_url = "https://www.google.com/search"
    elif engine == "bing":
        base_url = "https://www.bing.com/search"
    else:
        # SAFETY: Stop everything if an unknown engine is requested.
        raise ValueError(f"Unknown Search engine {engine}")
    # then we write the url request to know you should use this website api
    url = "https://api.brightdata.com/request"
    payload = {
        # THE TOOL: Tells the API which specific "Zone" or account to use
        "zone": "serp_api",
        # THE MISSION: Combines the search engine (Google/Bing) with your question
        # quote_plus() makes sure spaces and symbols don't break the web link
        # parse the result and get it in json
        #ex. query = AI+trend+2026 (Notice how quote_plus turned spaces into +)
        "url": f"{base_url}?q={quote_plus(query)}&brd_json=1",
        "format": "raw"
    }
    full_response = _make_api_request(url, json=payload) # send the request and make sure to apply the instruction in the payload

    # If the came back empty-handed, stop to avoid a crash
    if not full_response:
        return None
    # THE FILTER: Only grab the specific "content" (knowledge boxes and web links)
    extracted_data = {
        # .get ensures that if the data is missing, the code doesn't break
        "knowledge": full_response.get("knowledge", {}),
        "organic": full_response.get("organic", []), # learn this from the youtuber experience in the video
    }
    # THE OUTPUT: Return the clean, tiny package of useful info
    return extracted_data

# function to download the snapshot - Starts a long-running task.  Monitors progress until finished.
def _trigger_and_download_snapshot(trigger_url, params, data, operation_name="operation"):
    # 1. THE ORDER: Tell the API to start "getting" the data (the snapshot)
    trigger_result = _make_api_request(trigger_url, params=params, json=data)
    if not trigger_result:
        return None

    # 2. THE TICKET: Get the unique ID of the data store (snap-shot)
    snapshot_id = trigger_result.get("snapshot_id") # we use snapshot id to know if it's ready or not
    if not snapshot_id:
        return None

    # 3. THE WAIT: Keep checking until the API says "It's ready!"
    if not poll_snapshot_status(snapshot_id):
        return None

    # 4. THE DELIVERY: Finally download the finished data to your computer
    raw_data = download_snapshot(snapshot_id)
    return raw_data


def reddit_search_api(keyword, date="All time", sort_by="Hot", num_of_posts=75):
    trigger_url = "https://api.brightdata.com/datasets/v3/trigger"

    params = {
        "dataset_id":  "gd_lvz8ah06191smkebj4",
        "include_errors": "true",
        "type": "discover_new",
        "discover_by": "keyword"
    }

    data = [
        {
            "keyword": keyword,
            "date": date,
            "sort_by": sort_by,
            "num_of_posts": num_of_posts,
        }
    ]
    raw_data = _trigger_and_download_snapshot(
        trigger_url, params, data, operation_name="reddit"
    )

    if not raw_data:
        return None

    parsed_data = []
    for post in raw_data:
        parsed_post = {
            "title":  post.get("title"),
            "url": post.get("url")
        }
        parsed_data.append(parsed_post)
    return {"parsed_post": parsed_data, "total_found": len(parsed_data)}

def reddit_post_retrieval(urls, days_back=10, load_all_replies=False, comment_limit=""):
    # SAFETY: If no links were provided, don't waste time/money
    if not urls:
        return None

    # THE FACTORY: The Bright Data address for triggering a scrape
    trigger_url = "https://api.brightdata.com/datasets/v3/trigger"

    # THE TOOLS: Telling the API exactly which scraper "machine" to turn on
    params = {
        "dataset_id": "gd_lvzdpsdlw09j6t702",
        "include_errors": "true"
    }

    # THE BLUEPRINT: Creating a list of instructions for every URL provided
    data = [
        {
            "url": url,
            "days_back": days_back,
            "load_all_replies": load_all_replies,
            "comment_limit": comment_limit
        }
        for url in urls
    ]

    # THE ACTION: Start the process, wait for the download, and get the raw JSON
    raw_data = _trigger_and_download_snapshot(
        trigger_url, params, data, operation_name="reddit comments"
    )
    if not raw_data:
        return None

    # THE CLEANUP: Sifting through the raw data to keep only the "good stuff"
    parsed_comments = []
    for comment in raw_data:
        parsed_comment = {
            "comment_id": comment.get("comment_id"),
            "content": comment.get("comment"),
            "date": comment.get("date_posted"),
        }
        parsed_comments.append(parsed_comment)

    # OUTPUT: Return a tidy package of comments and a count
    return {"comments": parsed_comments, "total_retrieved": len(parsed_comments)}