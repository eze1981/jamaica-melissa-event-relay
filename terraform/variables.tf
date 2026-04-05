variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-east-1"
}

variable "stage_name" {
  description = "API Gateway deployment stage name"
  type        = string
  default     = "v1"
}

variable "table_name" {
  description = "DynamoDB table name for events"
  type        = string
  default     = "melissa-events"
}

variable "ushahidi_shared_secret" {
  description = "Shared secret for validating X-Ushahidi-Signature webhook headers"
  type        = string
  sensitive   = true
}
