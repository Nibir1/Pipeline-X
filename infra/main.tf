terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

# 1. Resource Group
resource "azurerm_resource_group" "rg" {
  name     = "pipeline-x-production-rg"
  location = "Sweden Central"  # Good for Student subscriptions
}

# 2. Azure Database for PostgreSQL (Flexible Server)
resource "azurerm_postgresql_flexible_server" "postgres" {
  name                   = "pipeline-x-db-${random_string.suffix.result}"
  resource_group_name    = azurerm_resource_group.rg.name
  location               = azurerm_resource_group.rg.location
  version                = "13"
  administrator_login    = "airflow_admin"
  administrator_password = "SecurePassword123!" # In real life, use variables
  storage_mb             = 32768
  sku_name               = "B_Standard_B1ms"    # Cheapest burstable tier
  zone                   = "1"
}

# Allow access from all IPs (For Student/Demo ease - In Prod use VNET)
resource "azurerm_postgresql_flexible_server_firewall_rule" "all" {
  name             = "allow-all-ips"
  server_id        = azurerm_postgresql_flexible_server.postgres.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "255.255.255.255"
}

resource "azurerm_postgresql_flexible_server_database" "airflow" {
  name      = "airflow"
  server_id = azurerm_postgresql_flexible_server.postgres.id
  collation = "en_US.utf8"
  charset   = "utf8"
}

# 3. Azure Data Lake Storage Gen2 (The "Big Data" Home)
resource "azurerm_storage_account" "datalake" {
  name                     = "pipelinex${random_string.suffix.result}"
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"
  is_hns_enabled           = "true" # IMPORTANT: Enables Data Lake (Hierarchical Namespace)
}

resource "azurerm_storage_data_lake_gen2_filesystem" "fs" {
  name               = "datalake"
  storage_account_id = azurerm_storage_account.datalake.id
}

# Random suffix for unique naming
resource "random_string" "suffix" {
  length  = 4
  special = false
  upper   = false
}

# 4. Outputs (Copy these to your .env)
output "postgres_host" {
  value = azurerm_postgresql_flexible_server.postgres.fqdn
}

output "storage_account_name" {
  value = azurerm_storage_account.datalake.name
}

output "storage_account_key" {
  value     = azurerm_storage_account.datalake.primary_access_key
  sensitive = true
}