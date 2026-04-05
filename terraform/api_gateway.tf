resource "aws_api_gateway_rest_api" "event_relay" {
  name        = "melissa-event-relay-api"
  description = "Event relay between Ushahidi and XMPro for Hurricane Melissa response"

  endpoint_configuration {
    types = ["REGIONAL"]
  }
}

resource "aws_api_gateway_resource" "events" {
  rest_api_id = aws_api_gateway_rest_api.event_relay.id
  parent_id   = aws_api_gateway_rest_api.event_relay.root_resource_id
  path_part   = "events"
}

# POST /events
resource "aws_api_gateway_method" "post_events" {
  rest_api_id      = aws_api_gateway_rest_api.event_relay.id
  resource_id      = aws_api_gateway_resource.events.id
  http_method      = "POST"
  authorization    = "NONE"
  api_key_required = true
}

resource "aws_api_gateway_integration" "post_events" {
  rest_api_id             = aws_api_gateway_rest_api.event_relay.id
  resource_id             = aws_api_gateway_resource.events.id
  http_method             = aws_api_gateway_method.post_events.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.event_relay.invoke_arn
}

# GET /events
resource "aws_api_gateway_method" "get_events" {
  rest_api_id      = aws_api_gateway_rest_api.event_relay.id
  resource_id      = aws_api_gateway_resource.events.id
  http_method      = "GET"
  authorization    = "NONE"
  api_key_required = true
}

resource "aws_api_gateway_integration" "get_events" {
  rest_api_id             = aws_api_gateway_rest_api.event_relay.id
  resource_id             = aws_api_gateway_resource.events.id
  http_method             = aws_api_gateway_method.get_events.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.event_relay.invoke_arn
}

resource "aws_api_gateway_deployment" "event_relay" {
  rest_api_id = aws_api_gateway_rest_api.event_relay.id

  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.events,
      aws_api_gateway_method.post_events,
      aws_api_gateway_method.get_events,
      aws_api_gateway_integration.post_events,
      aws_api_gateway_integration.get_events,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }

  depends_on = [
    aws_api_gateway_integration.post_events,
    aws_api_gateway_integration.get_events,
  ]
}

resource "aws_api_gateway_stage" "event_relay" {
  deployment_id = aws_api_gateway_deployment.event_relay.id
  rest_api_id   = aws_api_gateway_rest_api.event_relay.id
  stage_name    = var.stage_name
}
