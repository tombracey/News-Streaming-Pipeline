resource "aws_iam_policy" "sqs_send_message_policy" {
  name        = "sqs-send-message-policy"
  description = "Allow sending messages to the SQS queue"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Statement1"
        Effect = "Allow"
        Action = [
          "sqs:SendMessage"
        ]
        Resource = [
          aws_sqs_queue.terraform_queue.arn
        ]
      }
    ]
  })
}
