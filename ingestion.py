import requests
import os
from dotenv import load_dotenv
import json

def get_guardian_articles(query, date_from=None, num_results=10):
    load_dotenv()
    api_key = os.getenv("GUARDIAN_API_KEY")

    url = f"https://content.guardianapis.com/search?q=debate&api-key={api_key}"

    params = {
        "q": query,
        "page-size": num_results, # in case the default changes
        "order-by": "newest",
        "show-fields": "trailText,body",
    }

    if date_from:
        params["from-date"] = date_from

    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()["response"]["results"]
        articles = []
        for article in data:
            articles.append({
            "webPublicationDate": article["webPublicationDate"],
            "webTitle": article["webTitle"],
            "webUrl": article["webUrl"],
        })
        return articles
    else:
        return f'Error: {response.status_code}'

print(get_guardian_articles("machine learning"))