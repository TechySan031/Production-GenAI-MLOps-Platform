# ─────────────────────────────────────────────────────────────────────────────
# Outputs
#
# These values are consumed by the CI/CD pipeline and by operators.
# Sensitive outputs are marked to prevent accidental exposure in logs.
# ─────────────────────────────────────────────────────────────────────────────

output "resource_group_name" {
  description = "Name of the Azure Resource Group"
  value       = azurerm_resource_group.genai.name
}

output "acr_login_server" {
  description = "Azure Container Registry login server URL"
  value       = azurerm_container_registry.acr.login_server
}

output "acr_name" {
  description = "Azure Container Registry name"
  value       = azurerm_container_registry.acr.name
}

output "container_app_name" {
  description = "Container App name"
  value       = azurerm_container_app.app.name
}

output "container_app_fqdn" {
  description = "Container App fully qualified domain name"
  value       = azurerm_container_app.app.ingress[0].fqdn
}

output "container_app_url" {
  description = "Container App HTTPS URL"
  value       = "https://${azurerm_container_app.app.ingress[0].fqdn}"
}

output "container_app_environment_name" {
  description = "Container App Environment name"
  value       = azurerm_container_app_environment.env.name
}

output "managed_identity_client_id" {
  description = "Client ID of the user-assigned managed identity"
  value       = azurerm_user_assigned_identity.genai.client_id
}

output "managed_identity_principal_id" {
  description = "Principal ID of the user-assigned managed identity"
  value       = azurerm_user_assigned_identity.genai.principal_id
}

output "log_analytics_workspace_id" {
  description = "Log Analytics Workspace ID"
  value       = azurerm_log_analytics_workspace.logs.id
}

output "application_insights_connection_string" {
  description = "Application Insights connection string for SDK configuration"
  value       = azurerm_application_insights.appinsights.connection_string
  sensitive   = true
}

output "application_insights_instrumentation_key" {
  description = "Application Insights instrumentation key"
  value       = azurerm_application_insights.appinsights.instrumentation_key
  sensitive   = true
}
