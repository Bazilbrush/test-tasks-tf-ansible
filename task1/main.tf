terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~>4.32.0"
    }
  }
  backend "azurerm" {
      resource_group_name  = "tfbackend"
      storage_account_name = "tfbackendjack"
      container_name       = "backend"
      key                  = "code-test/test/module-validation.tfstate"
  }
}

provider "azurerm" {
  use_oidc = false  #change to false
  features {}
}

resource "azurerm_resource_group" "module-test" {
  name     = "module-${terraform.workspace}"
  location = "UK South"
}


module "queues" {
  source = "./test-module"
  resource_group_name = azurerm_resource_group.module-test.name
  storage_account_name = "queues"
  queue_names = ["one", "two"]
}