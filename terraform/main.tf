resource "aws_sqs_queue" "terraform_queue" {
  name                      = "guardian_content"
  max_message_size          = 2048
  message_retention_seconds = 259200 # 3 days

  tags = {
    Environment = "production"
  }
}

