import os
import requests
import json
from dotenv import load_dotenv
load_dotenv()
from newsapi import NewsApiClient

FREECRYPTO_TOKEN = os.getenv("FREECRYPTO_TOKEN")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")

# API setup
headers = {
    "Authorization": f"Bearer {FREECRYPTO_TOKEN}"
    }
# define the endpoint we going to send the request to
url = "https://api.freecryptoapi.com/v1/getData"
# to see the available coins
params = {"symbol": "BTC"}

# send the HTTP request to the API through the url
response = requests.get(url, headers=headers, params=params)
data = response.json()
#print(f"this is Crypto {json.dumps(data, indent=4)}")

# NewsAPI setup
newsapi = NewsApiClient(api_key=NEWSAPI_KEY)
all_articles = newsapi.get_everything(q='bitcoin', language='en', sort_by='relevancy', page=1)
#print(f"This is NewsAPI {json.dumps(all_articles, indent=2)}")



