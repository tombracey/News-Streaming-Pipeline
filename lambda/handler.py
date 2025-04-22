import requests
import os
from dotenv import load_dotenv
import json
import boto3

def get_guardian_articles(query, date_from=None, num_results=10):
    load_dotenv()
    api_key = os.getenv("GUARDIAN_API_KEY")

    url = f"https://content.guardianapis.com/search?q=debate&api-key={api_key}"

    params = {
        "q": query,
        "page-size": num_results, # 10 is the default anyway, but coded in case that changes
        "order-by": "newest",
        "show-fields": "trailText,body",
    }

    if date_from:
        params["from-date"] = date_from # date_from input is optional

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
        return f'{response.status_code} error'

def send_to_sqs(articles):
    boto3_client = boto3.client('sqs', region_name="eu-west-2")
    queue_url = os.getenv("QUEUE_URL")
    for article in articles:
        boto3_client.send_message(QueueUrl=queue_url, MessageBody=json.dumps(article))

def lambda_handler(event, context):
    query = event.get("query")
    articles = get_guardian_articles(query)
    send_to_sqs(articles)