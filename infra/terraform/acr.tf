# ─────────────────────────────────────────────────────────────────────────────
# Azure Container Registry
#
# ACR stores Docker images built by the CI/CD pipeline. The Container App
# pulls images using Managed Identity (AcrPull role), not admin credentials.
# ─────────────────────────────────────────────────────────────────────────────

resource "azurerm_container_registry" "acr" {
  name                = local.acr_name
  resource_group_name = azurerm_resource_group.genai.name
  location            = azurerm_resource_group.genai.location

  sku           = var.acr_sku
  admin_enabled = false

  public_network_access_enabled = true

  tags = local.common_tags
}