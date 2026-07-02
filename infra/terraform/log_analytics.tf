# ─────────────────────────────────────────────────────────────────────────────
# Log Analytics Workspace
#
# Central log sink for Container App environment, Application Insights,
# and Azure Monitor. Retention is configurable via var.log_retention_days.
# ─────────────────────────────────────────────────────────────────────────────

resource "azurerm_log_analytics_workspace" "logs" {
  name                = "${local.name_prefix}-logs"
  location            = azurerm_resource_group.genai.location
  resource_group_name = azurerm_resource_group.genai.name

  sku               = "PerGB2018"
  retention_in_days = var.log_retention_days

  # Disable local authentication in production for security — forces AAD auth
  local_authentication_disabled = var.environment == "production" ? true : false

  tags = local.common_tags
}