/*
  GenAI Gateway — Infrastructure Entry Point

  Deploys the full stack for one environment (staging or production).
  Run via Makefile targets or GitHub Actions CD pipeline.

  Usage (manual):
    az deployment group create \
      --resource-group <rg> \
      --template-file infra/main.bicep \
      --parameters infra/parameters/staging.bicepparam \
      --parameters groqApiKey=$GROQ_API_KEY \
                   appInsightsConnectionString=""
      # appInsightsConnectionString is bootstrapped — see below.

  Bootstrap order:
    1. Deploy with appInsightsConnectionString="" to create App Insights.
    2. Read the generated connection string from the output.
    3. Re-deploy with the real connection string to inject it into the app.
    The Makefile 'infra-bootstrap' target handles this automatically.
*/

@allowed(['staging', 'production'])
param environment string

param location string = resourceGroup().location

param projectName string = 'genai-gateway'

@secure()
param groqApiKey string

@description('App Insights connection string. Empty on first deploy; bootstrapped on second.')
@secure()
param appInsightsConnectionString string = ''

@secure()
param langfuseSecretKey string = ''

param langfusePublicKey string = ''
param langfuseEnabled bool = false
param langfuseHost string = 'https://cloud.langfuse.com'
param groqModel string = 'llama-3.1-8b-instant'
param initialImage string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'

// ── Resource naming ───────────────────────────────────────────────────────────

var suffix = uniqueString(resourceGroup().id)
var acrName = replace('${projectName}acr${environment}${take(suffix, 6)}', '-', '')
var kvName = 'gkv${take(environment,4)}${take(suffix,8)}'
// ── Modules ───────────────────────────────────────────────────────────────────

module logAnalytics 'modules/log-analytics.bicep' = {
  name: 'log-analytics'
  params: {
    workspaceName: '${projectName}-logs-${environment}'
    location: location
    retentionInDays: environment == 'production' ? 90 : 30
  }
}

module appInsights 'modules/app-insights.bicep' = {
  name: 'app-insights'
  params: {
    appInsightsName: '${projectName}-insights-${environment}'
    location: location
    logAnalyticsWorkspaceId: logAnalytics.outputs.workspaceId
  }
}

module acr 'modules/acr.bicep' = {
  name: 'acr'
  params: {
    registryName: acrName
    location: location
    sku: 'Premium'
  }
}

module keyVault 'modules/key-vault.bicep' = {
  name: 'key-vault'
  params: {
    vaultName: kvName
    location: location
    groqApiKey: groqApiKey
    appInsightsConnectionString: empty(appInsightsConnectionString)
      ? appInsights.outputs.connectionString
      : appInsightsConnectionString
    langfuseSecretKey: langfuseSecretKey
  }
}

module containerAppsEnv 'modules/container-apps-env.bicep' = {
  name: 'container-apps-env'
  params: {
    environmentName: '${projectName}-env-${environment}'
    location: location
    logAnalyticsWorkspaceId: logAnalytics.outputs.workspaceId
    logAnalyticsSharedKey: logAnalytics.outputs.sharedKey
    logAnalyticsCustomerId: logAnalytics.outputs.customerId
  }
}

// Staging environment — scale to zero, basic SKU
module stagingApp 'modules/container-app.bicep' = {
  name: 'staging-app'
  params: {
    appName: '${projectName}-staging'
    location: location
    containerAppsEnvironmentId: containerAppsEnv.outputs.environmentId
    containerRegistryServer: acr.outputs.loginServer
    initialImage: initialImage
    environment: 'staging'
    groqApiKey: groqApiKey
    groqModel: groqModel
    appInsightsConnectionString: empty(appInsightsConnectionString)
      ? appInsights.outputs.connectionString
      : appInsightsConnectionString
    langfuseSecretKey: langfuseSecretKey
    langfusePublicKey: langfusePublicKey
    langfuseEnabled: langfuseEnabled
    langfuseHost: langfuseHost
    minReplicas: 0
    maxReplicas: 3
  }
}

// Production environment — always-on, higher ceiling
module productionApp 'modules/container-app.bicep' = {
  name: 'production-app'
  params: {
    appName: '${projectName}-production'
    location: location
    containerAppsEnvironmentId: containerAppsEnv.outputs.environmentId
    containerRegistryServer: acr.outputs.loginServer
    initialImage: initialImage
    environment: 'production'
    groqApiKey: groqApiKey
    groqModel: groqModel
    appInsightsConnectionString: empty(appInsightsConnectionString)
      ? appInsights.outputs.connectionString
      : appInsightsConnectionString
    langfuseSecretKey: langfuseSecretKey
    langfusePublicKey: langfusePublicKey
    langfuseEnabled: langfuseEnabled
    langfuseHost: langfuseHost
    minReplicas: 1
    maxReplicas: 10
  }
}

// ── Outputs ───────────────────────────────────────────────────────────────────

output acrLoginServer string = acr.outputs.loginServer
output acrName string = acr.outputs.registryName
output stagingFqdn string = stagingApp.outputs.fqdn
output productionFqdn string = productionApp.outputs.fqdn
output stagingAppName string = stagingApp.outputs.appName
output productionAppName string = productionApp.outputs.appName
output keyVaultName string = keyVault.outputs.vaultName
output appInsightsConnectionString string = appInsights.outputs.connectionString