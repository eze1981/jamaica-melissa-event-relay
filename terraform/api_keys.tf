resource "aws_api_gateway_api_key" "ushahidi" {
  name    = "melissa-ushahidi-key"
  enabled = true
}

resource "aws_api_gateway_api_key" "xmpro" {
  name    = "melissa-xmpro-key"
  enabled = true
}

resource "aws_api_gateway_usage_plan" "event_relay" {
  name        = "melissa-event-relay-usage-plan"
  description = "Usage plan for Ushahidi and XMPro API access"

  api_stages {
    api_id = aws_api_gateway_rest_api.event_relay.id
    stage  = aws_api_gateway_stage.event_relay.stage_name
  }

  throttle_settings {
    rate_limit  = 100
    burst_limit = 50
  }
}

resource "aws_api_gateway_usage_plan_key" "ushahidi" {
  key_id        = aws_api_gateway_api_key.ushahidi.id
  key_type      = "API_KEY"
  usage_plan_id = aws_api_gateway_usage_plan.event_relay.id
}

resource "aws_api_gateway_usage_plan_key" "xmpro" {
  key_id        = aws_api_gateway_api_key.xmpro.id
  key_type      = "API_KEY"
  usage_plan_id = aws_api_gateway_usage_plan.event_relay.id
}
