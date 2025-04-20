resource "aws_sqs_queue" "terraform_queue" {
  name                      = "terraform-queue"
  max_message_size          = 2048
  message_retention_seconds = 259200

  tags = {
    Environment = "production"
  }
}

