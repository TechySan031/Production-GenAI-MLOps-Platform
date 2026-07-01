resource "azurerm_application_insights" "appinsights" {
  name                = "genai-gateway-insights-staging"
  location            = azurerm_resource_group.genai.location
  resource_group_name = azurerm_resource_group.genai.name

  workspace_id         = azurerm_log_analytics_workspace.logs.id
  application_type     = "web"
  sampling_percentage  = 100

  tags = {
    Project     = "Production-GenAI-MLops-Platform"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}