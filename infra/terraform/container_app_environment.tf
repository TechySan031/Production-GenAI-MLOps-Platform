resource "azurerm_container_app_environment" "env" {
  name                = "genai-gateway-env-staging"
  location            = azurerm_resource_group.genai.location
  resource_group_name = azurerm_resource_group.genai.name

  log_analytics_workspace_id = azurerm_log_analytics_workspace.logs.id

  mutual_tls_enabled = false

  workload_profile {
    name                  = "Consumption"
    workload_profile_type = "Consumption"
    minimum_count         = 0
    maximum_count         = 0
  }

  tags = {
    Project     = "Production-GenAI-MLops-Platform"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}