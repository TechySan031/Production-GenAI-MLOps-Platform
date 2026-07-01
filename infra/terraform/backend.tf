terraform {
  backend "azurerm" {
    resource_group_name  = "genai-gateway-rg"
    storage_account_name = "tfstategenaigateway"
    container_name       = "tfstate"
    key                  = "staging.tfstate"
  }
}