# jamaica-melissa-event-relay

Serverless event relay for **Hurricane Melissa** humanitarian logistics — receives Ushahidi crowdsource reports via webhook and exposes them for XMPro digital twin ingestion.

## Architecture

```
Ushahidi  ──POST /events──▶  API Gateway  ──▶  Lambda (Python 3.12)  ──▶  DynamoDB
                                                                              │
XMPro     ◀─GET /events ──  API Gateway  ◀──  Lambda (Python 3.12)  ◀──────┘
```

- **POST /events** — authenticated with Ushahidi API key; stores full webhook JSON payload + `received_at` timestamp
- **GET /events** — authenticated with XMPro API key; returns stored events, supports `?limit=N` and `?since=<ISO timestamp>` query params

All infrastructure is managed via Terraform. No manual AWS console setup required.

---

## Prerequisites

| Tool | Minimum version | Install |
|------|----------------|---------|
| AWS CLI | v2 | https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html |
| Terraform | 1.14.8 | https://developer.hashicorp.com/terraform/install |
| Python | 3.12 | https://www.python.org/downloads/ |

Configure AWS credentials before deploying:

```bash
aws configure
# or
export AWS_PROFILE=your-profile
```

---

## Development Container (VS Code + Podman on macOS M1)

A devcontainer is provided for local development on macOS M1 (Apple Silicon) using Podman.

### One-time Podman setup

```bash
# Install Podman Desktop or Podman CLI via Homebrew
brew install podman
podman machine init
podman machine start

# Point VS Code Dev Containers at the Podman socket
# Option A — environment variable (add to ~/.zshrc):
export DOCKER_HOST=unix://${HOME}/.local/share/containers/podman/machine/qemu/podman.sock

# Option B — VS Code setting (in settings.json):
# "dev.containers.dockerPath": "podman"
```

### Open in devcontainer

1. Install the **Dev Containers** extension in VS Code.
2. Open the repo folder in VS Code.
3. When prompted, click **Reopen in Container** (or run `Dev Containers: Reopen in Container` from the command palette).
4. The `setup.sh` script runs automatically and installs Terraform, AWS CLI v2, and Python test dependencies.

AWS credentials from `~/.aws` on your Mac are bind-mounted into the container automatically.

---

## Deployment

### 1. Deploy infrastructure

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

Terraform will zip the `lambda/` directory automatically via the `archive_file` data source — no manual packaging step needed.

### 2. Retrieve API key values

Terraform outputs the key **IDs**. Retrieve the actual secret key **values** via the AWS CLI:

```bash
cd terraform

# Ushahidi key (use this in Ushahidi webhook config)
aws apigateway get-api-key \
  --api-key $(terraform output -raw ushahidi_api_key_id) \
  --include-value \
  --query 'value' \
  --output text

# XMPro key (use this in XMPro polling config)
aws apigateway get-api-key \
  --api-key $(terraform output -raw xmpro_api_key_id) \
  --include-value \
  --query 'value' \
  --output text
```

Get the API endpoint URL:

```bash
terraform output api_base_url
# e.g. https://abc123.execute-api.us-east-1.amazonaws.com/v1/events
```

---

## Configure Ushahidi

In the Ushahidi admin panel go to **Settings → Webhooks** and create a new webhook:

| Field | Value |
|-------|-------|
| URL | `<api_base_url>` from `terraform output api_base_url` |
| Method | POST |
| Header name | `x-api-key` |
| Header value | Ushahidi key value from step 2 |

---

## Configure XMPro

In XMPro Data Stream Designer, add an **HTTP Polling** data stream agent:

| Field | Value |
|-------|-------|
| URL | `<api_base_url>?limit=100&since=<last_poll_timestamp>` |
| Method | GET |
| Header | `x-api-key: <xmpro_key_value>` |
| Polling interval | 60 seconds (adjust as needed) |

Use `?since=` with the ISO 8601 timestamp of your last successful poll to retrieve only new events.

---

## API Reference

### POST /events

Stores an Ushahidi webhook payload.

**Request headers:**
```
x-api-key: <ushahidi_key>
Content-Type: application/json
```

**Request body:** Any valid JSON object (the full Ushahidi webhook payload is stored as-is).

**Response `201`:**
```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-06-15T14:30:00.123456+00:00"
}
```

---

### GET /events

Returns stored events as a JSON array, sorted ascending by timestamp.

**Request headers:**
```
x-api-key: <xmpro_key>
```

**Query parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 100 | Maximum number of events to return (max 1000) |
| `since` | ISO 8601 string | — | Only return events with `timestamp >= since` |

**Response `200`:**
```json
[
  {
    "event_id": "550e8400-...",
    "timestamp": "2025-06-15T14:30:00.123456+00:00",
    "received_at": "2025-06-15T14:30:00.123456+00:00",
    "title": "Road blocked - Spanish Town Road",
    "location": "Kingston"
  }
]
```

---

## Running Tests

```bash
pip install -r tests/requirements-test.txt
pytest
```

Tests use [moto](https://github.com/getmoto/moto) to mock DynamoDB locally — no AWS credentials or live resources required.

---

## Project Structure

```
.
├── .devcontainer/
│   ├── devcontainer.json   # VS Code devcontainer config (M1/Podman)
│   ├── Dockerfile          # ARM64-compatible Python 3.12 base image
│   └── setup.sh            # Installs Terraform, AWS CLI, test deps
├── lambda/
│   ├── handler.py          # Lambda function (POST + GET routing)
│   └── requirements.txt
├── terraform/
│   ├── main.tf             # AWS provider + DynamoDB table
│   ├── lambda.tf           # Lambda function, IAM role/policy
│   ├── api_gateway.tf      # REST API, resources, methods, integrations
│   ├── api_keys.tf         # API keys + usage plan
│   ├── variables.tf
│   └── outputs.tf
├── tests/
│   ├── test_handler.py     # Unit tests (pytest + moto)
│   └── requirements-test.txt
├── pytest.ini
└── README.md
```

---

## Teardown

```bash
cd terraform
terraform destroy
```

This removes all AWS resources: Lambda, API Gateway, DynamoDB table, IAM role, and API keys.
