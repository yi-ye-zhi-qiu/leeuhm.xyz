locals {
  app = var.append_workspace ? "${var.app}${title(terraform.workspace)}" : var.app
}


# create the NAT gateway
resource "azurerm_nat_gateway" "nat" {
  name                    = "${local.app}NatGateway"
  location                = var.resource_group_location
  resource_group_name     = var.resource_group_name
  sku_name                = "Standard"
  idle_timeout_in_minutes = 10
  zones                   = var.nat_gateway_zones
}

# static IP address for outbound traffic
resource "azurerm_public_ip" "pip" {
  name                = "${local.app}Pip"
  location            = var.resource_group_location
  resource_group_name = var.resource_group_name
  allocation_method   = "Static"
  sku                 = "Standard"
  zones               = var.nat_gateway_zones
}

# association between a NAT gateway and a public IP
resource "azurerm_nat_gateway_public_ip_association" "nat_public_ip_association" {
  nat_gateway_id       = azurerm_nat_gateway.nat.id
  public_ip_address_id = azurerm_public_ip.pip.id
}

# route traffic in private subnets to NAT gateway

resource "azurerm_subnet_security_group_association" "sg-association" {
  subnet_id                 = private_subnet.id
  network_security_group_id = sg.id
}

# create virtual network
resource "azurerm_virtual_network" "vnet" {
  name                = "${local.app}Vnet"
  address_space       = ["10.0.0.0/16"]
  location            = var.resource_group_location
  resource_group_name = var.resource_group_name
}

# create subnet
resource "azurerm_subnet" "private_subnet" {
  name                 = "${local.app}PrivateSubnet"
  resource_group_name  = var.resource_group_name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = ["10.0.1.0/24"]

  delegation {
    name = "delegation"

    service_delegation {
      name = "Microsoft.ContainerInstance/containerGroups"
      actions = [
        "Microsoft.Network/virtualNetworks/subnets/join/action",
        "Microsoft.Network/virtualNetworks/subnets/prepareNetworkPolicies/action"
      ]
    }
  }
}

# associate NAT gateway with subnet
resource "azurerm_subnet_nat_gateway_association" "main" {
  nat_gateway_id = azurerm_nat_gateway.nat.id
  subnet_id      = azurerm_subnet.private_subnet.id
}

# this is the network profile used by containers
resource "azurerm_network_profile" "network_profile" {
  name                = "${local.app}NetworkProfile"
  location            = var.resource_group_location
  resource_group_name = var.resource_group_name

  container_network_interface {
    name = "${local.app}NetworkInterface"

    ip_configuration {
      name      = "${local.app}IpConfig"
      subnet_id = azurerm_subnet.private_subnet.id
    }
  }
}

# this is the security group that 
resource "azurerm_network_security_group" "sg" {
  name                = "sg"
  resource_group_name = var.resource_group_name
  location            = var.resource_group_location

  security_rule {
    name              = "from-gateway-subnet"
    priority          = 100
    direction         = "Inbound"
    access            = "Allow"
    protocol          = "Tcp"
    source_port_range = "*"

    destination_port_ranges    = [22, 443, 445, 8000]
    source_address_prefix      = []
    destination_address_prefix = azurerm_subnet.private_subnet.address_prefix
  }

  security_rule {
    name                       = "DenyAllInbound-Override"
    priority                   = 900
    direction                  = "Inbound"
    access                     = "Deny"
    protocol                   = "*"
    source_port_range          = "*"
    destination_port_range     = "*"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  security_rule {
    name              = "to-internet"
    priority          = 100
    direction         = "Outbound"
    access            = "Allow"
    protocol          = "Tcp"
    source_port_range = "*"

    destination_port_ranges    = [80, 443, 445]
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "DenyAllOutbound-Override"
    priority                   = 900
    direction                  = "Outnound"
    access                     = "Deny"
    protocol                   = "*"
    source_port_range          = "*"
    destination_port_range     = "*"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
}
