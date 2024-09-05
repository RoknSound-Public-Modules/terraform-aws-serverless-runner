resource "aws_ecs_task_definition" "runner_task_definition" {
  family                   = var.namespace
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "2048"
  memory                   = "4096"
  task_role_arn            = var.ecs_task_role_arn
  execution_role_arn       = var.ecs_task_execution_role_arn

  container_definitions = jsonencode([
    {
      name      = var.namespace
      image     = var.image
      essential = true
      cpu       = 2048
      memory    = 4096
      environment = [
        {
          name  = "NAMESPACE"
          value = var.namespace
        },
        {
          name  = "RUNNER_GROUP"
          value = var.runner_group
        },
        {
          name  = "RUNNER_LABELS"
          value = var.runner_labels
        }
      ]
      command = ["./entrypoint_token.sh"]
      log_configuration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = var.log_group
          awslogs-region        = "us-west-2"
          awslogs-stream-prefix = var.tag
        }
      }
    }
  ])
}

resource "aws_vpc_endpoint" "vpc_endpoint" {
  vpc_id             = var.vpc_id
  service_name       = "com.amazonaws.${data.aws_region.current.name}.execute-api"
  vpc_endpoint_type  = "Interface"
  security_group_ids = [var.vpce_security_group]
  subnet_ids         = [var.routable_subnet_a, var.routable_subnet_b]
}

resource "aws_apigatewayv2_api" "hook_api" {
  name          = "${var.namespace}-github-workflow_job hook"
  protocol_type = "HTTP"

  target = aws_lambda_function.function.arn
}

resource "aws_lambda_function" "function" {
  function_name = var.namespace
  handler       = "handler.handler"
  runtime       = "python3.9"
  role          = var.serverless_role_arn
  filename      = "../runnerhook.zip"
  memory_size   = 128
  timeout       = 30

  environment {
    variables = {
      AWS_ENV                  = var.environment
      GITHUB_SECRET_ARN        = var.github_secret_arn
      GITHUB_API_URL           = "https://github.mmm.com/api/v3"
      GITHUB_HOOK_SECRET       = var.git_hook_secret
      ECS_CLUSTER              = var.ecs_cluster
      TASK_DEFINITION_ARN      = aws_ecs_task_definition.runner_task_definition.arn
      CONTAINER_NAME           = var.namespace
      CONTAINER_SECURITY_GROUP = var.container_security_group
      SUBNET_A                 = var.island_subnet_a
      SUBNET_B                 = var.island_subnet_b
      RUNNER_LABELS            = var.runner_labels
    }
  }

  vpc_config {
    security_group_ids = [var.serverless_security_group]
    subnet_ids         = [var.island_subnet_a, var.island_subnet_b]
  }
}

resource "aws_ssm_parameter" "hook_url_ssm_parameter" {
  name        = "${var.namespace}HookUrl"
  description = "The API endpoint for runner github webhook"
  type        = "String"
  value       = "https://${aws_apigatewayv2_api.hook_api.id}.execute-api.${data.aws_region.current.name}.amazonaws.com/prod/workflow/run"
}

output "function_name" {
  value = aws_lambda_function.function.function_name
}

output "web_hook_url" {
  value = aws_ssm_parameter.hook_url_ssm_parameter.value
}
