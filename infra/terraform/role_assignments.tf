# ─────────────────────────────────────────────────────────────────────────────
# RBAC Role Assignments — Least-Privilege Access
#
# Each assignment grants the minimum permissions needed:
#   - AcrPull: Container App can pull images from ACR (read-only, no push)
#   - Monitoring Metrics Publisher: App can emit custom metrics to Azure Monitor
# ─────────────────────────────────────────────────────────────────────────────

# Allow the Container App's managed identity to pull images from ACR
resource "azurerm_role_assignment" "acr_pull" {
  scope                = azurerm_container_registry.acr.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_user_assigned_identity.genai.principal_id
}

# Allow the Container App's managed identity to publish monitoring metrics
resource "azurerm_role_assignment" "monitoring_publisher" {
  scope                = azurerm_application_insights.appinsights.id
  role_definition_name = "Monitoring Metrics Publisher"
  principal_id         = azurerm_user_assigned_identity.genai.principal_id
}
