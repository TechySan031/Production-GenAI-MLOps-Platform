# ─────────────────────────────────────────────────────────────────────────────
# Container App
#
# The primary compute resource running the FastAPI LLM gateway. Uses Managed
# Identity for ACR image pulls (no admin credentials). Resource limits are
# configurable via variables for environment-appropriate sizing.
# ─────────────────────────────────────────────────────────────────────────────

resource "azurerm_container_app" "app" {
  name                         = "${local.name_prefix}-app"
  resource_group_name          = azurerm_resource_group.genai.name
  container_app_environment_id = azurerm_container_app_environment.env.id

  revision_mode = "Single"

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.genai.id]
  }

  registry {
    server   = azurerm_container_registry.acr.login_server
    identity = azurerm_user_assigned_identity.genai.id
  }

  template {
    min_replicas = var.environment == "production" ? 1 : 0
    max_replicas = var.environment == "production" ? 3 : 1

    container {
      name   = var.project_name
      image  = var.container_image != "" ? var.container_image : "${azurerm_container_registry.acr.login_server}/${var.project_name}:latest"
      cpu    = var.container_cpu
      memory = var.container_memory

      # Liveness probe — restart if the process is unresponsive
      liveness_probe {
        transport = "HTTP"
        port      = 8000
        path      = "/health"

        initial_delay    = 10
        interval_seconds = 30
        timeout          = 5
        failure_count_threshold = 3
      }

      # Readiness probe — stop routing traffic if dependencies are unhealthy
      readiness_probe {
        transport = "HTTP"
        port      = 8000
        path      = "/health/ready"

        interval_seconds = 15
        timeout          = 5
        failure_count_threshold = 3
      }
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

  tags = local.common_tags
}