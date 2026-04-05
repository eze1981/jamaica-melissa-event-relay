import base64
import hashlib
import hmac
import json
import os
import uuid
from datetime import datetime, timezone

import boto3
from boto3.dynamodb.conditions import Attr

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])
USHAHIDI_SHARED_SECRET = os.environ.get("USHAHIDI_SHARED_SECRET", "")


def lambda_handler(event, context):
    method = event.get("httpMethod", "")
    if method == "POST":
        return handle_post(event)
    elif method == "GET":
        return handle_get(event)
    else:
        return _response(405, {"error": "Method not allowed"})


def handle_post(event):
    try:
        body_str = event.get("body") or ""
        if not body_str:
            return _response(400, {"error": "Request body is required"})

        headers = event.get("headers") or {}
        sig = headers.get("X-Ushahidi-Signature", "")
        host = headers.get("Host", "")
        path = event.get("path", "/v1/events")
        url = f"https://{host}{path}"

        if not sig or not _verify_signature(url, body_str, sig):
            return _response(401, {"error": "Invalid signature"})

        try:
            payload = json.loads(body_str)
        except json.JSONDecodeError:
            return _response(400, {"error": "Request body must be valid JSON"})

        event_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        item = {**payload, "event_id": event_id, "timestamp": timestamp, "received_at": timestamp}
        table.put_item(Item=item)

        return _response(201, {"event_id": event_id, "timestamp": timestamp})
    except Exception as e:
        return _response(500, {"error": str(e)})


def handle_get(event):
    try:
        params = event.get("queryStringParameters") or {}

        # Parse limit
        try:
            limit = int(params.get("limit", 100))
            limit = min(limit, 1000)
        except ValueError:
            return _response(400, {"error": "limit must be an integer"})

        # Parse since
        since = params.get("since")
        if since is not None:
            try:
                datetime.fromisoformat(since)
            except ValueError:
                return _response(400, {"error": "since must be a valid ISO 8601 timestamp"})

        # Build scan kwargs
        scan_kwargs = {}
        if since:
            scan_kwargs["FilterExpression"] = Attr("timestamp").gte(since)

        # Paginate through results
        items = []
        while True:
            resp = table.scan(**scan_kwargs)
            items.extend(resp.get("Items", []))
            last_key = resp.get("LastEvaluatedKey")
            if not last_key:
                break
            scan_kwargs["ExclusiveStartKey"] = last_key

        # Sort ascending by timestamp and apply limit
        items.sort(key=lambda x: x.get("timestamp", ""))
        items = items[:limit]

        return _response(200, items)
    except Exception as e:
        return _response(500, {"error": str(e)})


def _verify_signature(url: str, body_str: str, signature: str) -> bool:
    message = (url + body_str).encode("utf-8")
    expected = base64.b64encode(
        hmac.new(USHAHIDI_SHARED_SECRET.encode("utf-8"), message, hashlib.sha256).digest()
    ).decode("utf-8")
    return hmac.compare_digest(expected, signature)


def _response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, default=str),
    }
