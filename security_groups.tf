
resource "aws_security_group" "container_security_group" {
  name_prefix = "${var.namespace}-ecs-sg"
  description = "${var.namespace} ECS SecurityGroup"
  vpc_id      = var.vpc_id
}

resource "aws_security_group_rule" "container_security_group_egress" {
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
  description       = "Allows Egress to the world"
  security_group_id = aws_security_group.container_security_group.id
}

resource "aws_security_group" "serverless_security_group" {
  name_prefix = "${var.namespace}-lambda-sg"
  description = "Security group for lambda"
  vpc_id      = var.vpc_id
}

resource "aws_security_group_rule" "serverless_security_group_egress" {
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
  description       = "Allows Egress to the world"
  security_group_id = aws_security_group.serverless_security_group.id
}

resource "aws_security_group" "vpce_security_group" {
  name_prefix = "${var.namespace}-vpce-sg"
  description = "Security group for vpc endpoint"
  vpc_id      = var.vpc_id
}

resource "aws_security_group_rule" "vpce_security_group_ingress" {
  type              = "ingress"
  from_port         = 443
  to_port           = 443
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
  description       = "Allow ingress on 443"
  security_group_id = aws_security_group.vpce_security_group.id
}

resource "aws_security_group_rule" "vpce_security_group_egress" {
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
  description       = "Allows Egress to the world"
  security_group_id = aws_security_group.vpce_security_group.id
}

output "container_security_group" {
  value = aws_security_group.container_security_group.id
}

output "serverless_security_group" {
  value = aws_security_group.serverless_security_group.id
}

output "vpce_security_group" {
  value = aws_security_group.vpce_security_group.id
}
