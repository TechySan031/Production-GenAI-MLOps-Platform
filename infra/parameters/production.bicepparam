using '../main.bicep'

param environment = 'production'
param location = 'eastus'
param projectName = 'genai-gateway'
param groqModel = 'llama-3.1-8b-instant'
param langfuseEnabled = true