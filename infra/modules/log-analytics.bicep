@description('Log Analytics workspace name.')
param workspaceName string

@description('Azure region.')
param location string

@minValue(30)
@maxValue(730)
param retentionInDays int = 30

resource workspace 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: workspaceName
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: retentionInDays
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
  }
}

output workspaceId string = workspace.id
output customerId string = workspace.properties.customerId

// @secure() prevents this value appearing in Azure deployment history logs.
@secure()
output sharedKey string = workspace.listKeys().primarySharedKey