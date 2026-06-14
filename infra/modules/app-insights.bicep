@description('Application Insights resource name.')
param appInsightsName string

@description('Azure region.')
param location string

@description('Log Analytics workspace resource ID (workspace-based, not classic).')
param logAnalyticsWorkspaceId string

// Workspace-based Application Insights — classic mode is deprecated.
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalyticsWorkspaceId
    RetentionInDays: 90
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

output connectionString string = appInsights.properties.ConnectionString
output instrumentationKey string = appInsights.properties.InstrumentationKey
output appInsightsId string = appInsights.id