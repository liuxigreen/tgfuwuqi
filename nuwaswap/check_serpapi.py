import os
from serpapi import GoogleSearch

api_key = os.getenv("SERPAPI_API_KEY")
params = {
    "engine": "google",
    "q": "site:twitter.com/CryptoRover",
    "api_key": api_key,
    "num": 2
}
try:
    res = GoogleSearch(params).get_dict()
    if "error" in res:
        print("Error from SerpApi:", res["error"])
    elif "organic_results" in res:
        print("Success! Got results.")
    else:
        print("No organic results, but no error. Keys:", res.keys())
except Exception as e:
    print("Exception:", e)
