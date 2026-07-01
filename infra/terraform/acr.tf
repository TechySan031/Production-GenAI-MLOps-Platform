resource "azurerm_container_registry" "acr" {
  name                = "genaigatewayacrstaging54tk6e"
  resource_group_name = azurerm_resource_group.genai.name
  location            = azurerm_resource_group.genai.location

  sku           = "Premium"
  admin_enabled = false

  public_network_access_enabled = true

  retention_policy_in_days = 30

  tags = {
    Project     = "Production-GenAI-MLops-Platform"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}