resource "azurerm_storage_account" "this" {
  name                     = var.storage_account_name
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = "Standard" # can be variablised but i dont think i have access beyond standard tier
  account_replication_type = "LRS"      # again sets hardcode it to basic tiers
  min_tls_version          = "TLS1_2"   # it's default but lets make sure it's visible in code

  tags = {
    environment = terraform.workspace
  }
}