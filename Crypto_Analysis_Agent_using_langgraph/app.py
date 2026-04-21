import os, json, requests, typing
from dotenv import load_dotenv
from langchain_core.messages.tool import tool_call
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langsmith import expect
from newsapi.const import languages

load_dotenv()
from newsapi import NewsApiClient
from langchain.chat_models import init_chat_model

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
FREECRYPTO_TOKEN = os.getenv("FREECRYPTO_TOKEN")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")

llm = init_chat_model("gemini-3.1-flash-lite-preview", model_provider="google_genai")


@tool
def crypto_list_tool(limit: int = 25) -> str:
    """
        Fetches a list of available cryptocurrencies (symbol + name) from FreeCryptoAPI.
        Args:
            limit (int): Max number of coins to return (to keep responses compact).
        Returns:
            str: JSON string with a condensed list: [{"symbol": "...", "name": "..."}, ...]
        """

    # define the endpoint we going to send the request to
    url = "https://api.freecryptoapi.com/v1/getCryptoList"
    headers = {"Authorization": f"Bearer {os.getenv('FREECRYPTO_TOKEN')}"}


    try:
        response = requests.get(url, headers=headers, timeout=25)
        response.raise_for_status()
        data = response.json()
        #print(data)
        coin_list = data.get("result")
        #print(coin_list)
    except Exception:
        return json.dumps({"status": False,"error": "Could not retrieve coins"}, indent=2)

    info = []
    if isinstance(coin_list, list):
        for item in coin_list[ :max(1, limit)]:
            symbol = item.get("symbol")
            name = item.get("name")


            if symbol or name:
                info.append({"symbol": symbol, "name" : name})
        return json.dumps({"status": True, "coins": info}, indent=2)
    # else, fallback to returning the whole response
    return json.dumps(data, indent=2)

# result = crypto_list_tool.func(2)
# print(result)


@tool
def crypto_data_tool(symbol: str) -> str:
    # ValueError: Function must have a docstring if description not provided.
    """
        Fetches detailed data for a given crypto symbol (e.g., BTC) from FreeCryptoAPI.
        Args:
            symbol (str): Symbol like 'BTC', 'ETH', etc.
        Returns:
            str: JSON string of the API response.
        """

    url = "https://api.freecryptoapi.com/v1/getData"
    headers = {"Authorization": f"Bearer {os.getenv('FREECRYPTO_TOKEN')}"}
    params = {"symbol": symbol.upper()}
    try:
        response = requests.get(url, headers=headers, params=params, timeout=25)
        response.raise_for_status()
        data = response.json()
    except Exception:
        return json.dumps({"status": False, "error": "Invalid JSON from API"})
    return json.dumps(data, indent=2)

@tool
def crypto_news_tool(query: str = "crypto", max_items: int = 5) -> str:
    """
        Fetches recent news using NewsAPI and returns a condensed list.
        Args:
            query (str): Search query, e.g., 'bitcoin', 'ethereum'
            max_items (int): Number of articles to return
        Returns:
            str: JSON string of the results.
        """
    newsapi = NewsApiClient(api_key= os.getenv("NEWSAPI_KEY"))

    try:
        response = newsapi.get_everything(
            q=query,
            language="en",
            sort_by="publishedAt",
            page=1
        )
        articles = response.get("articles", [])

    except Exception as e:
        return json.dumps({"status": False, "error": str(e)})

    slim = []
    for a in articles[:max(1, max_items)]:
        slim.append({
            "title": a.get("title"),
            "source": a.get("source"),
            "url": a.get("url"),
            "content": a.get("content"),
            "publishedAt": a.get("publishedAt"),
            "description": a.get("description")
        })

    return json.dumps({
        "status": True,
        "totalResults": len(articles),
        "returned": len(slim),
        "articles": slim,
    }, indent=2)


    #print(response)
    #print(articles)

# if __name__ == "__main__":
    # Call the function for testing
    # print(crypto_list_tool.func(5))
    # print(crypto_data_tool.func("BTC"))
    # print(crypto_news_tool.func("bitcoin", 3))

