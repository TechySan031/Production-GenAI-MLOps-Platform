# ─────────────────────────────────────────────────────────────────────────────
# Remote state backend — Azure Blob Storage
#
# The state file is stored in a dedicated storage account. The backend config
# values are provided via -backend-config flags in CI/CD to avoid hardcoding
# environment-specific values.
#
# CI usage:
#   terraform init \
#     -backend-config="resource_group_name=genai-gateway-rg" \
#     -backend-config="storage_account_name=tfstategenaigateway" \
#     -backend-config="container_name=tfstate" \
#     -backend-config="key=staging.tfstate"
# ─────────────────────────────────────────────────────────────────────────────

terraform {
  backend "azurerm" {}
}