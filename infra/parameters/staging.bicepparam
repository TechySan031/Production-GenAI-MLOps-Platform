using '../main.bicep'

// Non-secret values only — safe to commit.
// Secrets are injected at deploy time via CLI:
//   --parameters groqApiKey=$GROQ_API_KEY
// Never put secret values in this file.

param environment = 'staging'
param location = 'eastus'
param projectName = 'genai-gateway'
param groqModel = 'llama-3.1-8b-instant'
param langfuseEnabled = false
param langfusePublicKey = ''