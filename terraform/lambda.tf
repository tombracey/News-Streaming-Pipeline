resource "aws_iam_role_policy_attachment" "lambda_sqs_attach" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.lambda_sqs_policy.arn
}

resource "aws_lambda_function" "streaming_lambda" {
  filename         = "../src/lambda.zip"
  function_name    = "streaming-lambda"
  role             = aws_iam_role.lambda_role.arn
  handler          = "handler.lambda_handler"

  source_code_hash = filebase64sha256("../src/lambda.zip")

  runtime          = "python3.12"

  timeout = 30 # default is just 3

  environment {
    variables = {
        QUEUE_URL = aws_sqs_queue.terraform_queue.url
        QUEUE_NAME = aws_sqs_queue.terraform_queue.name
        GUARDIAN_API_KEY = var.guardian_api_key
    }
  }
}