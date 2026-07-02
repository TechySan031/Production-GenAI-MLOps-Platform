# ─────────────────────────────────────────────────────────────────────────────
# User-Assigned Managed Identity
#
# Used by the Container App to authenticate to Azure services (ACR, Key Vault)
# without storing credentials. This is the zero-secret access pattern:
# the identity is assigned RBAC roles, and the container inherits it at runtime.
# ─────────────────────────────────────────────────────────────────────────────

resource "azurerm_user_assigned_identity" "genai" {
  name                = "${local.name_prefix}-identity"
  location            = azurerm_resource_group.genai.location
  resource_group_name = azurerm_resource_group.genai.name
  tags                = local.common_tags
}
