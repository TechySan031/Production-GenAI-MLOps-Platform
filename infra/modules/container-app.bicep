/*
  Azure Container App — reusable for both staging and production.

  Managed identity is used for ACR pull — no registry passwords stored.
  The initial image is a public placeholder (no ACR auth needed on first
  deploy). The CD pipeline updates it to the real image from ACR.

  Role assignment: AcrPull is scoped to the resource group.
  Trade-off: this grants AcrPull on all ACRs in the RG, not just ours.
  For a single-ACR project this is acceptable; tighten to ACR scope
  in multi-ACR environments.
*/

@description('Container App name.')
param appName string

@description('Azure region.')
param location string

@description('Container Apps environment resource ID.')
param containerAppsEnvironmentId string

@description('ACR login server (e.g. myacr.azurecr.io).')
param containerRegistryServer string

@description('Initial Docker image — public placeholder for first deploy.')
param initialImage string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'

@allowed(['staging', 'production'])
param environment string

@secure()
param groqApiKey string

param groqModel string = 'llama-3.1-8b-instant'

@secure()
param appInsightsConnectionString string

@secure()
param langfuseSecretKey string = ''

param langfusePublicKey string = ''
param langfuseEnabled bool = false
param langfuseHost string = 'https://cloud.langfuse.com'

@minValue(0)
param minReplicas int = 0

@maxValue(30)
param maxReplicas int = 5

// ── Container App ─────────────────────────────────────────────────────────────

resource containerApp 'Microsoft.App/containerApps@2023-11-02-preview' = {
  name: appName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    environmentId: containerAppsEnvironmentId
    workloadProfileName: 'Consumption'
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
        allowInsecure: false
      }
      
      secrets: [
  {
    name: 'groq-api-key'
    value: groqApiKey
  }
  {
    name: 'appinsights-connection-string'
    value: appInsightsConnectionString
  }
]
    }
    template: {
      containers: [
        {
          name: 'gateway'
          image: initialImage
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: [
            { name: 'ENVIRONMENT', value: environment }
            { name: 'PORT', value: '8000' }
            { name: 'LOG_FORMAT', value: 'json' }
            { name: 'LLM_PROVIDER', value: 'groq' }
            { name: 'GROQ_MODEL', value: groqModel }
            { name: 'GROQ_API_KEY', secretRef: 'groq-api-key' }
            { name: 'LANGFUSE_ENABLED', value: string(langfuseEnabled) }
            { name: 'LANGFUSE_HOST', value: langfuseHost }
            { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', secretRef: 'appinsights-connection-string' }
          ]
        }
      ]

      scale: {
        minReplicas: minReplicas
        maxReplicas: maxReplicas
        rules: [
          {
            name: 'http-scale'
            http: {
              metadata: { concurrentRequests: '20' }
            }
          }
        ]
      }
    }
  }
}

// ── AcrPull role assignment ───────────────────────────────────────────────────

var acrPullRoleDefinitionId = '7f951dda-4ed3-4680-a7ca-43fe172d538d'

resource acrPullAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  // guid() is deterministic — same inputs always produce the same GUID,
  // so re-running Bicep does not create duplicate role assignments.
  name: guid(containerApp.id, acrPullRoleDefinitionId, resourceGroup().id)
  scope: resourceGroup()
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      acrPullRoleDefinitionId
    )
    principalId: containerApp.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

// ── Outputs ───────────────────────────────────────────────────────────────────

output fqdn string = containerApp.properties.configuration.ingress.fqdn
output appName string = containerApp.name
output appId string = containerApp.id
output managedIdentityPrincipalId string = containerApp.identity.principalId