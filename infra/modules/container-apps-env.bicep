@description('Container Apps managed environment name.')
param environmentName string

@description('Azure region.')
param location string

@description('Log Analytics workspace resource ID.')
param logAnalyticsWorkspaceId string

@description('Log Analytics primary shared key.')
@secure()
param logAnalyticsSharedKey string

@description('Log Analytics customer ID (workspace GUID).')
param logAnalyticsCustomerId string

resource containerAppsEnv 'Microsoft.App/managedEnvironments@2023-11-02-preview' = {
  name: environmentName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalyticsCustomerId
        sharedKey: logAnalyticsSharedKey
      }
    }
    workloadProfiles: [
      {
        name: 'Consumption'
        workloadProfileType: 'Consumption'
      }
    ]
  }
}

output environmentId string = containerAppsEnv.id
output environmentName string = containerAppsEnv.name