variable "subscription_id" {
  description = "Azure Subscription ID"
  type        = string
  default     = "fffbeb3f-c296-4399-b05d-dd812838c8cf"
}

variable "resource_group_name" {
  description = "Resource Group Name"
  type        = string
  default     = "genai-gateway-rg"
}

variable "location" {
  description = "Azure Region"
  type        = string
  default     = "eastus"
}

variable "environment" {
  description = "Deployment Environment"
  type        = string
  default     = "staging"
}