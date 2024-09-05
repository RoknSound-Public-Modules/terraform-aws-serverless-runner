resource "aws_cloudwatch_log_group" "function_log_group" {
  name              = "/aws/lambda/${var.namespace}"
  retention_in_days = 90
}

resource "aws_cloudwatch_log_group" "log_group" {
  name              = "${var.namespace}-service"
  retention_in_days = 7
}

resource "aws_cloudwatch_log_group" "access_log_group" {
  name              = "/${var.namespace}/access-logs"
  retention_in_days = 7
}

output "log_group" {
  value = aws_cloudwatch_log_group.log_group.name
}

output "function_log_group" {
  value = aws_cloudwatch_log_group.function_log_group.name
}

output "access_log_group_arn" {
  value = aws_cloudwatch_log_group.access_log_group.arn
}
