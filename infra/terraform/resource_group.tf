resource "azurerm_resource_group" "genai" {
  name     = var.resource_group_name
  location = var.location

  tags = {
    Project     = "Production-GenAI-MLops-Platform"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}