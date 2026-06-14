/*
  Azure Key Vault

  Used for two purposes:
    1. Storing application secrets (Groq key, App Insights connection string)
    2. Storing the previous production image tag so the rollback workflow
       can retrieve it without needing to query Azure deployment history.

  Uses RBAC authorization (modern) rather than legacy access policies.
*/

@description('Key Vault name — 3–24 chars, globally unique.')
param vaultName string

@description('Azure region.')
param location string

@description('Groq API key.')
@secure()
param groqApiKey string

@description('Application Insights connection string.')
@secure()
param appInsightsConnectionString string

@description('Langfuse secret key (optional).')
@secure()
param langfuseSecretKey string = ''

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: vaultName
  location: location
  properties: {
    sku: {
      family: 'A'
      name: 'Premium'
    }
    tenantId: subscription().tenantId
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
    enablePurgeProtection: true 
  }
}

resource secretGroq 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'groq-api-key'
  properties: {
    value: groqApiKey
    attributes: { enabled: true }
  }
}

resource secretAppInsights 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'appinsights-connection-string'
  properties: {
    value: appInsightsConnectionString
    attributes: { enabled: true }
  }
}

// Populated at first deployment; updated by the CD pipeline before each
// production promotion so the rollback workflow can revert.
resource secretPreviousImage 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'prod-previous-image'
  properties: {
    value: 'none'
    attributes: { 
        enabled: true
    }
  }
}

resource secretLangfuse 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = if (!empty(langfuseSecretKey)) {
  parent: keyVault
  name: 'langfuse-secret-key'
  properties: {
    value: langfuseSecretKey
    attributes: { enabled: true }
  }
}

output vaultName string = keyVault.name
output vaultUri string = keyVault.properties.vaultUri
output vaultId string = keyVault.id