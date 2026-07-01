resource "azurerm_container_app" "staging" {
  name                         = "genai-gateway-staging"
  resource_group_name          = azurerm_resource_group.genai.name
  container_app_environment_id = azurerm_container_app_environment.env.id

  revision_mode = "Single"

  template {
    container {
      name   = "genai-gateway-staging"
      image  = "genaigatewayacrstaging54tk6e.azurecr.io/genai-gateway:latest"
      cpu    = 0.5
      memory = "1Gi"
    }
  }

  ingress {
    external_enabled = true
    target_port      = 8000

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  tags = {
    Project     = "Production-GenAI-MLops-Platform"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}