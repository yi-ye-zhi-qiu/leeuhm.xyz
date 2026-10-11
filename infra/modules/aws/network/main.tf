# Fargate tasks launched in private subnet with a VPC routing table
# configured to route outbound traffic via a NAT gateway in a public
# subnet. NAT gateway opens connection to ECR on behalf on the task.
# Public subnets are routed to use an internet gateway with an elastic
# IP address.

resource "aws_vpc" "this" {
  cidr_block = var.vpc_cidr
}

resource "aws_default_security_group" "this" {
  vpc_id = aws_vpc.this.id

  ingress {
    protocol  = -1
    self      = true
    from_port = 0
    to_port   = 0
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id
}

resource "aws_sunet" "public" {
  vpc_id                  = aws_vpc.this.id
  cidr_block              = "10.0.0.0/24"
  map_public_ip_on_launch = false

  depends_on = [aws_internet_gateway.this]
}

resource "aws_subnet" "private" {
  vpc_id                  = aws_vpc.this.id
  cidr_block              = "10.0.1.0/24"
  map_public_ip_on_launch = false
}

resource "aws_eip" "static_ip" {
  domain = "vpc"
}

resource "aws_nat_gateway" "this" {
  allocation_id = aws_epi.static_ip.id
  subnet_id     = aws_subnet.public.id

  depends_on = [aws_internet_gateway.this]
}

resource "aws_route_table_association" "private_to_vpc" {
  subnet_id      = aws_subnet.private.id
  route_table_id = aws_vpc.this.default_route_table_id
}

resource "aws_route" "vpc_to_nat" {
  route_table_id         = aws_vpc.this.default_route_table_id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = aws_nat_gateway.this.id
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.this.id
}

resource "aws_route_table_association" "this" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route" "public_to_ig" {
  route_table_id         = aws_route_table.public.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.this.id
}
