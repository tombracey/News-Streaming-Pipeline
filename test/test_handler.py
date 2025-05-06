import pytest
from unittest.mock import patch, MagicMock
from src.handler import get_guardian_articles, get_queue_url, lambda_handler


@patch('src.handler.requests.get')
def test_get_guardian_articles(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "response": {
            "results": [
                {
                    "webPublicationDate": "2025-01-01T11:11:31Z",
                    "webTitle": "Test Article",
                    "webUrl": "https://www.theguardian.co.uk/article",
                    "fields": {"trailText": "this is a preview of the content"}
                }
            ]
        }
    }
    mock_get.return_value = mock_response

    articles = get_guardian_articles('test', date_from='2024-01-01')

    assert len(articles) == 1
    assert articles[0]['webTitle'] == "Test Article"
    assert articles[0]['webUrl'] == "https://www.theguardian.co.uk/article"
    assert articles[0]['content_preview'] == "this is a preview of the content"


@patch('src.handler.os.getenv')
def test_get_guardian_articles_with_no_api_key(mock_getenv):
    mock_getenv.return_value = None

    with pytest.raises(ValueError, match="Guardian API key not found"):
        get_guardian_articles("test query")


@patch('src.handler.os.getenv')
def test_get_queue_url_from_env(mock_getenv):
    mock_getenv.return_value = (
        "https://sqs.eu-west-2.amazonaws.com/12345/test_queue"
    )
    result = get_queue_url("test_queue")

    assert result == "https://sqs.eu-west-2.amazonaws.com/12345/test_queue"


@patch('src.handler.boto3.client')
@patch('src.handler.os.getenv')
def test_get_queue_url_from_aws(mock_getenv, mock_boto3_client):
    mock_getenv.return_value = None

    mock_sqs = MagicMock()
    mock_sqs.get_queue_url.return_value = {
        "QueueUrl": "https://sqs.eu-west-2.amazonaws.com/12345/test_queue"
    }
    mock_boto3_client.return_value = mock_sqs

    result = get_queue_url("test_queue")

    assert result == "https://sqs.eu-west-2.amazonaws.com/12345/test_queue"


@patch("src.handler.send_to_sqs")
@patch("src.handler.get_guardian_articles")
def test_send_to_sqs_and_lambda_handler(mock_get_articles, mock_send_to_sqs):
    mock_get_articles.return_value = [
        {
            "webTitle": "Lambda Test",
            "webUrl": "https://example.com",
            "webPublicationDate": "2025-01-01T00:00:00Z"}
    ]

    event = {"query": "test", "date_from": "2024-01-01"}
    context = None

    response = lambda_handler(event, context)

    mock_get_articles.assert_called_once_with("test", "2024-01-01")
    mock_send_to_sqs.assert_called_once()
    assert "Articles successfully sent to SQS" in response["body"]


if __name__ == "__main__":
    pytest.main()
