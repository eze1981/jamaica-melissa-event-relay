#!/usr/bin/env bash
set -euo pipefail

TERRAFORM_VERSION="1.9.8"
WORKDIR="/workspaces/jamaica-melissa-event-relay"

echo "==> Detecting architecture..."
ARCH=$(uname -m)
if [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then
  TF_ARCH="arm64"
  AWS_ARCH="aarch64"
else
  TF_ARCH="amd64"
  AWS_ARCH="x86_64"
fi
echo "    Architecture: $ARCH (Terraform: $TF_ARCH, AWS CLI: $AWS_ARCH)"

# ── Terraform ─────────────────────────────────────────────────────────────────
if command -v terraform &>/dev/null; then
  echo "==> Terraform already installed: $(terraform version -json | python3 -c 'import sys,json; print(json.load(sys.stdin)["terraform_version"])')"
else
  echo "==> Installing Terraform $TERRAFORM_VERSION ($TF_ARCH)..."
  TF_ZIP="terraform_${TERRAFORM_VERSION}_linux_${TF_ARCH}.zip"
  curl -fsSL "https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/${TF_ZIP}" -o /tmp/terraform.zip
  unzip -o /tmp/terraform.zip -d /usr/local/bin
  chmod +x /usr/local/bin/terraform
  rm /tmp/terraform.zip
  echo "    Terraform $(terraform version -json | python3 -c 'import sys,json; print(json.load(sys.stdin)["terraform_version"])') installed."
fi

# ── AWS CLI v2 ────────────────────────────────────────────────────────────────
if command -v aws &>/dev/null; then
  echo "==> AWS CLI already installed: $(aws --version)"
else
  echo "==> Installing AWS CLI v2 ($AWS_ARCH)..."
  curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-${AWS_ARCH}.zip" -o /tmp/awscliv2.zip
  unzip -o /tmp/awscliv2.zip -d /tmp/awscli
  /tmp/awscli/aws/install --update
  rm -rf /tmp/awscliv2.zip /tmp/awscli
  echo "    $(aws --version) installed."
fi

# ── Python test dependencies ───────────────────────────────────────────────────
echo "==> Installing Python test dependencies..."
pip install --quiet -r "${WORKDIR}/tests/requirements-test.txt"

echo ""
echo "==> Setup complete!"
echo "    Terraform: $(terraform version -json | python3 -c 'import sys,json; print(json.load(sys.stdin)["terraform_version"])')"
echo "    AWS CLI:   $(aws --version)"
echo "    Python:    $(python3 --version)"
