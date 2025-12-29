# infra/main.tf

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
  name     = "pipeline-x-resources"
  location = "Sweden Central"
}

# 2. Networking (Security Rule to allow access)
# Note: For production, we would use VNETs. For this demo, we allow public access.
resource "azurerm_postgresql_flexible_server" "postgres" {
  name                   = "pipeline-x-db-${random_id.server_id.hex}"
  resource_group_name    = azurerm_resource_group.rg.name
  location               = azurerm_resource_group.rg.location
  version                = "13"
  administrator_login    = "airflow_admin"
  administrator_password = "SecurePassword123!" # Change this!
  storage_mb             = 32768
  sku_name               = "B_Standard_B1ms" # Burstable (Cheapest)
  zone                   = "1"
}

# 3. Firewall Rule (Allow All IPs for Demo Simplicity)
resource "azurerm_postgresql_flexible_server_firewall_rule" "allow_all" {
  name             = "allow-all"
  server_id        = azurerm_postgresql_flexible_server.postgres.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "255.255.255.255"
}

# 4. Create the Database inside the Server
resource "azurerm_postgresql_flexible_server_database" "airflow_db" {
  name      = "airflow"
  server_id = azurerm_postgresql_flexible_server.postgres.id
  collation = "en_US.utf8"
  charset   = "utf8"
}

# Utility to generate unique name
resource "random_id" "server_id" {
  byte_length = 4
}

# Output the connection info (So we can put it in our .env)
output "db_host" {
  value = azurerm_postgresql_flexible_server.postgres.fqdn
}