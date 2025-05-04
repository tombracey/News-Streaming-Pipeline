import requests
import os
from dotenv import load_dotenv
import json
import boto3
import logging

logger = logging.getLogger('handler')
logger.setLevel(logging.INFO)

def get_guardian_articles(query, date_from=None, num_results=10):
    load_dotenv()
    api_key = os.getenv("GUARDIAN_API_KEY")

    if not api_key:
        err_message = "Guardian API key not found"
        logger.error(err_message)
        raise ValueError(err_message)

    url = f"https://content.guardianapis.com/search"

    params = {
        "api-key": api_key,
        "q": query,
        "page-size": num_results, # 10 is the default anyway, but coded in case that changes
        "order-by": "newest",
        "show-fields": "trailText,body",
    }

    if date_from:
        params["from-date"] = date_from # date_from input is optional

    try:
        logger.info(f"Calling Guardian API\nQuery: {query}\nFrom date: {date_from}")
        response = requests.get(url, params=params)

        if response.status_code == 200:
            data = response.json()["response"]["results"]
            articles = []
            for article in data:
                article_obj = {
                    "webPublicationDate": article["webPublicationDate"],
                    "webTitle": article["webTitle"],
                    "webUrl": article["webUrl"],
                }
                
                # Adds content preview if one can be provided
                if "fields" in article and "trailText" in article["fields"]:
                    article_obj["content_preview"] = article["fields"]["trailText"][:1000]
                
                articles.append(article_obj)
            return articles
        else:
            return f'{response.status_code} error'
    except Exception as e:
        logger.error(f"Error returning articles: {str(e)}")

def get_queue_url(queue_name):
    try:
        queue_url = os.getenv("QUEUE_URL")
        if queue_url:
            return queue_url # gets QUEUE_URL if it exists as an env variable...
        else:
            sqs_client = boto3.client('sqs', region_name="eu-west-2")
            response = sqs_client.get_queue_url(QueueName=queue_name)
            return response['QueueUrl'] # ...if not, gets it from AWS
    except Exception as e:
        logger.error(f"Error finding queue URL: {str(e)}")

def send_to_sqs(articles, queue_name):
    try:
        boto3_client = boto3.client('sqs', region_name="eu-west-2")
        queue_url = get_queue_url(queue_name)
        for article in articles:
            boto3_client.send_message(QueueUrl=queue_url, MessageBody=json.dumps(article))
    except Exception as e:
        logger.error(f"Error sending to SQS: {str(e)}")

def lambda_handler(event, context):
    query = event.get("query")
    date_from = event.get("date_from")
    
    articles = get_guardian_articles(query, date_from)

    queue_name = os.getenv("QUEUE_NAME", "terraform-queue")
    send_to_sqs(articles, queue_name)

    return {
        "statusCode": 200,
        "body": json.dumps({"message": "Articles successfully sent to SQS"})
    }