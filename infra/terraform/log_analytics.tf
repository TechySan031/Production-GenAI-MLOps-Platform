resource "azurerm_log_analytics_workspace" "logs" {
  name                = "genai-gateway-logs-staging"
  location            = azurerm_resource_group.genai.location
  resource_group_name = azurerm_resource_group.genai.name

  sku               = "PerGB2018"
  retention_in_days = 30

  local_authentication_enabled = true

  tags = {
    Project     = "Production-GenAI-MLops-Platform"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}