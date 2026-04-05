output "api_base_url" {
  description = "Base URL for the /events endpoint"
  value       = "${aws_api_gateway_stage.event_relay.invoke_url}/events"
}

output "ushahidi_api_key_id" {
  description = "API key ID for Ushahidi (use AWS CLI to retrieve the actual key value)"
  value       = aws_api_gateway_api_key.ushahidi.id
}

output "xmpro_api_key_id" {
  description = "API key ID for XMPro (use AWS CLI to retrieve the actual key value)"
  value       = aws_api_gateway_api_key.xmpro.id
}

output "lambda_function_name" {
  description = "Lambda function name"
  value       = aws_lambda_function.event_relay.function_name
}

output "dynamodb_table_name" {
  description = "DynamoDB table name"
  value       = aws_dynamodb_table.events.name
}
