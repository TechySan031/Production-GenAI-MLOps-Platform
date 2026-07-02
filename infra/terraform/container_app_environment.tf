# ─────────────────────────────────────────────────────────────────────────────
# Container App Environment
#
# Shared hosting environment for Container Apps. Connected to Log Analytics
# for centralized logging. Uses Consumption workload profile (serverless).
# ─────────────────────────────────────────────────────────────────────────────

resource "azurerm_container_app_environment" "env" {
  name                = "${local.name_prefix}-env"
  location            = azurerm_resource_group.genai.location
  resource_group_name = azurerm_resource_group.genai.name

  log_analytics_workspace_id = azurerm_log_analytics_workspace.logs.id

  workload_profile {
    name                  = "Consumption"
    workload_profile_type = "Consumption"
    minimum_count         = 0
    maximum_count         = 0
  }

  tags = local.common_tags
}