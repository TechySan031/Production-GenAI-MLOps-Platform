# ─────────────────────────────────────────────────────────────────────────────
# Application Insights
#
# Connected to the Log Analytics workspace for unified monitoring.
# Provides request tracing, dependency tracking, and performance metrics
# for the FastAPI application via Azure Monitor.
# ─────────────────────────────────────────────────────────────────────────────

resource "azurerm_application_insights" "appinsights" {
  name                = "${local.name_prefix}-insights"
  location            = azurerm_resource_group.genai.location
  resource_group_name = azurerm_resource_group.genai.name

  workspace_id     = azurerm_log_analytics_workspace.logs.id
  application_type = "web"

  # Sample 100% in staging for debugging, 50% in production for cost control
  sampling_percentage = var.environment == "production" ? 50 : 100

  tags = local.common_tags
}