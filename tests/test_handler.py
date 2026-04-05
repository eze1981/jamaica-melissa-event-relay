import json
import os

import boto3
import pytest
from moto import mock_aws

os.environ["TABLE_NAME"] = "melissa-events"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
os.environ["AWS_ACCESS_KEY_ID"] = "testing"
os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
os.environ["AWS_SECURITY_TOKEN"] = "testing"
os.environ["AWS_SESSION_TOKEN"] = "testing"

from handler import lambda_handler  # noqa: E402


TABLE_NAME = "melissa-events"
KEY_SCHEMA = [
    {"AttributeName": "event_id", "KeyType": "HASH"},
    {"AttributeName": "timestamp", "KeyType": "RANGE"},
]
ATTR_DEFS = [
    {"AttributeName": "event_id", "AttributeType": "S"},
    {"AttributeName": "timestamp", "AttributeType": "S"},
]


def _make_table(dynamodb_client):
    dynamodb_client.create_table(
        TableName=TABLE_NAME,
        KeySchema=KEY_SCHEMA,
        AttributeDefinitions=ATTR_DEFS,
        BillingMode="PAY_PER_REQUEST",
    )


def _post_event(body):
    return {"httpMethod": "POST", "body": json.dumps(body), "queryStringParameters": None}


def _get_event(params=None):
    return {"httpMethod": "GET", "body": None, "queryStringParameters": params}


def _seed_item(table, event_id, timestamp, **extra):
    table.put_item(Item={"event_id": event_id, "timestamp": timestamp, **extra})


@mock_aws
def test_post_stores_item_returns_201():
    client = boto3.client("dynamodb", region_name="us-east-1")
    _make_table(client)

    payload = {"title": "Flood", "location": "Kingston", "severity": "high"}
    resp = lambda_handler(_post_event(payload), {})

    assert resp["statusCode"] == 201
    body = json.loads(resp["body"])
    assert "event_id" in body
    assert "timestamp" in body

    # Verify item is actually in DynamoDB
    resource = boto3.resource("dynamodb", region_name="us-east-1")
    table = resource.Table(TABLE_NAME)
    scan = table.scan()
    assert len(scan["Items"]) == 1
    item = scan["Items"][0]
    assert item["title"] == "Flood"
    assert item["location"] == "Kingston"
    assert "received_at" in item


@mock_aws
def test_post_missing_body_returns_400():
    client = boto3.client("dynamodb", region_name="us-east-1")
    _make_table(client)

    resp = lambda_handler({"httpMethod": "POST", "body": None, "queryStringParameters": None}, {})

    assert resp["statusCode"] == 400
    body = json.loads(resp["body"])
    assert "error" in body


@mock_aws
def test_post_invalid_json_returns_400():
    client = boto3.client("dynamodb", region_name="us-east-1")
    _make_table(client)

    resp = lambda_handler({"httpMethod": "POST", "body": "not-json", "queryStringParameters": None}, {})

    assert resp["statusCode"] == 400


@mock_aws
def test_get_returns_all_items():
    client = boto3.client("dynamodb", region_name="us-east-1")
    _make_table(client)
    resource = boto3.resource("dynamodb", region_name="us-east-1")
    table = resource.Table(TABLE_NAME)
    _seed_item(table, "id-1", "2025-01-01T00:00:00+00:00", title="Event 1")
    _seed_item(table, "id-2", "2025-02-01T00:00:00+00:00", title="Event 2")

    resp = lambda_handler(_get_event(), {})

    assert resp["statusCode"] == 200
    items = json.loads(resp["body"])
    assert isinstance(items, list)
    assert len(items) == 2


@mock_aws
def test_get_with_limit():
    client = boto3.client("dynamodb", region_name="us-east-1")
    _make_table(client)
    resource = boto3.resource("dynamodb", region_name="us-east-1")
    table = resource.Table(TABLE_NAME)
    for i in range(5):
        _seed_item(table, f"id-{i}", f"2025-0{i+1}-01T00:00:00+00:00", title=f"Event {i}")

    resp = lambda_handler(_get_event({"limit": "3"}), {})

    assert resp["statusCode"] == 200
    items = json.loads(resp["body"])
    assert len(items) == 3


@mock_aws
def test_get_with_since_filter():
    client = boto3.client("dynamodb", region_name="us-east-1")
    _make_table(client)
    resource = boto3.resource("dynamodb", region_name="us-east-1")
    table = resource.Table(TABLE_NAME)
    _seed_item(table, "id-jan", "2025-01-01T00:00:00+00:00", title="January event")
    _seed_item(table, "id-jun", "2025-06-01T00:00:00+00:00", title="June event")

    resp = lambda_handler(_get_event({"since": "2025-03-01T00:00:00+00:00"}), {})

    assert resp["statusCode"] == 200
    items = json.loads(resp["body"])
    assert len(items) == 1
    assert items[0]["title"] == "June event"


@mock_aws
def test_get_no_items_returns_empty_array():
    client = boto3.client("dynamodb", region_name="us-east-1")
    _make_table(client)

    resp = lambda_handler(_get_event(), {})

    assert resp["statusCode"] == 200
    items = json.loads(resp["body"])
    assert items == []


@mock_aws
def test_get_invalid_limit_returns_400():
    client = boto3.client("dynamodb", region_name="us-east-1")
    _make_table(client)

    resp = lambda_handler(_get_event({"limit": "banana"}), {})

    assert resp["statusCode"] == 400


@mock_aws
def test_get_invalid_since_returns_400():
    client = boto3.client("dynamodb", region_name="us-east-1")
    _make_table(client)

    resp = lambda_handler(_get_event({"since": "not-a-date"}), {})

    assert resp["statusCode"] == 400


@mock_aws
def test_invalid_method_returns_405():
    client = boto3.client("dynamodb", region_name="us-east-1")
    _make_table(client)

    resp = lambda_handler({"httpMethod": "DELETE", "body": None, "queryStringParameters": None}, {})

    assert resp["statusCode"] == 405


@mock_aws
def test_response_is_sorted_ascending():
    client = boto3.client("dynamodb", region_name="us-east-1")
    _make_table(client)
    resource = boto3.resource("dynamodb", region_name="us-east-1")
    table = resource.Table(TABLE_NAME)
    _seed_item(table, "id-c", "2025-03-01T00:00:00+00:00", title="March")
    _seed_item(table, "id-a", "2025-01-01T00:00:00+00:00", title="January")
    _seed_item(table, "id-b", "2025-02-01T00:00:00+00:00", title="February")

    resp = lambda_handler(_get_event(), {})

    items = json.loads(resp["body"])
    titles = [i["title"] for i in items]
    assert titles == ["January", "February", "March"]
