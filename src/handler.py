import requests
import os
from dotenv import load_dotenv
import json
import boto3
import logging
import argparse

logger = logging.getLogger('handler')
logger.setLevel(logging.INFO)

load_dotenv()

def get_guardian_articles(query, date_from=None, num_results=10):
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
        api_call_log_string = f"Calling Guardian API\nQuery: {query}"
        if date_from:
            api_call_log_string += f"\nFrom date: {date_from}"
        logger.info(api_call_log_string)
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
    queue_url = os.getenv("QUEUE_URL") # gets QUEUE_URL if it exists as an env variable...
    if queue_url:
        logger.info(f"Using QUEUE_URL from environment: {queue_url}")
        return queue_url
    
    try:
        sqs_client = boto3.client("sqs", region_name="eu-west-2") # ...if not, gets it from AWS
        response = sqs_client.get_queue_url(QueueName=queue_name)
        queue_url = response["QueueUrl"]
        logger.info(f"Using queue URL from AWS: {queue_url}")
        return queue_url
    except Exception as e:
        logger.error(f"Error retrieving queue URL: {e}")
        raise

def send_to_sqs(articles, queue_name):
    try:
        session = boto3.Session(region_name="eu-west-2")
        boto3_client = session.client('sqs')
        
        queue_url = get_queue_url(queue_name)
        for article in articles:
            boto3_client.send_message(QueueUrl=queue_url, MessageBody=json.dumps(article, indent=2))
    except Exception as e:
        logger.error(f"Error sending to SQS: {str(e)}")
        raise

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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch articles and send to SQS")
    parser.add_argument("query", help="Query string for Guardian API")
    parser.add_argument("--date_from", help="Filter by date from, YYYY-MM-DD (optional)", default=None)
    parser.add_argument("--queue_name", help="SQS queue name (optional)", default="guardian_content")
    args = parser.parse_args()

    query = args.query
    if " " in query and not (query[0] == '"' and query[-1] == '"'):
        query = f'"{query}"' # Wraps the queries (e.g. 'machine learning' treated as a phrase) to improve relevance of articles

    try:
        articles = get_guardian_articles(query, args.date_from)
        print(f"Using queue: {args.queue_name}")
        send_to_sqs(articles, args.queue_name)
        print(f"{len(articles)} articles successfully sent to SQS")
    except Exception as e:
        logger.error(f"Error sending to SQS: {str(e)}")
        raise