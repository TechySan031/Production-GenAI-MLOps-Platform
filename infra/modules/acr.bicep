/*
  Azure Container Registry

  Stores Docker images tagged by Git SHA.
  admin_enabled = false: images are pulled via managed identity, not passwords.
  Retention policy: auto-delete untagged manifests after 30 days.
*/

@description('Registry name — globally unique, alphanumeric only, 5–50 chars.')
param registryName string

@description('Azure region.')
param location string

@allowed(['Basic', 'Standard', 'Premium'])
param sku string = 'Standard'

resource acr 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: registryName
  location: location
  sku: {
    name: sku
  }
  properties: {
    adminUserEnabled: false
    publicNetworkAccess: 'Enabled'
    zoneRedundancy: 'Disabled'
    policies: {
      retentionPolicy: {
        status: 'enabled'
        days: 30
      }
    }
  }
}

output loginServer string = acr.properties.loginServer
output registryName string = acr.name
output registryId string = acr.id