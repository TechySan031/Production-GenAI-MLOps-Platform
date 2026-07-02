# ─────────────────────────────────────────────────────────────────────────────
# Input Variables
#
# All values with security implications (subscription_id) are marked sensitive
# and have no default — they must be provided via terraform.tfvars, environment
# variables, or CI/CD pipeline secrets.
# ─────────────────────────────────────────────────────────────────────────────

variable "subscription_id" {
  description = "Azure Subscription ID"
  type        = string
  sensitive   = true

  validation {
    condition     = can(regex("^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", var.subscription_id))
    error_message = "subscription_id must be a valid UUID."
  }
}

variable "resource_group_name" {
  description = "Name of the Azure Resource Group"
  type        = string
  default     = "genai-gateway-rg"
}

variable "location" {
  description = "Azure region for all resources"
  type        = string
  default     = "eastus"

  validation {
    condition     = contains(["eastus", "eastus2", "westus2", "westeurope", "northeurope", "centralus"], var.location)
    error_message = "Location must be one of: eastus, eastus2, westus2, westeurope, northeurope, centralus."
  }
}

variable "environment" {
  description = "Deployment environment (staging or production)"
  type        = string
  default     = "staging"

  validation {
    condition     = contains(["staging", "production"], var.environment)
    error_message = "Environment must be either 'staging' or 'production'."
  }
}

variable "project_name" {
  description = "Project identifier used in resource naming and tagging"
  type        = string
  default     = "genai-gateway"
}

variable "container_image" {
  description = "Full container image reference (registry/repo:tag)"
  type        = string
  default     = ""
}

variable "container_cpu" {
  description = "CPU cores allocated to the container app"
  type        = number
  default     = 0.5

  validation {
    condition     = contains([0.25, 0.5, 1.0, 2.0, 4.0], var.container_cpu)
    error_message = "container_cpu must be one of: 0.25, 0.5, 1.0, 2.0, 4.0."
  }
}

variable "container_memory" {
  description = "Memory allocated to the container app (e.g., '1Gi')"
  type        = string
  default     = "1Gi"

  validation {
    condition     = can(regex("^[0-9]+(\\.[0-9]+)?Gi$", var.container_memory))
    error_message = "container_memory must be in the format '<number>Gi' (e.g., '1Gi', '2Gi')."
  }
}

variable "log_retention_days" {
  description = "Log Analytics workspace retention in days"
  type        = number
  default     = 30

  validation {
    condition     = var.log_retention_days >= 7 && var.log_retention_days <= 730
    error_message = "log_retention_days must be between 7 and 730."
  }
}

variable "acr_sku" {
  description = "SKU tier for Azure Container Registry"
  type        = string
  default     = "Basic"

  validation {
    condition     = contains(["Basic", "Standard", "Premium"], var.acr_sku)
    error_message = "acr_sku must be one of: Basic, Standard, Premium."
  }
}