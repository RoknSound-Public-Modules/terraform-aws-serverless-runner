resource "aws_ecs_task_definition" "runner_task_definition" {
  family                   = var.namespace
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "2048"
  memory                   = "4096"
  task_role_arn            = aws_iam_role.ecs_task_role.arn
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn

  container_definitions = jsonencode([
    {
      name      = var.namespace
      image     = var.image
      essential = true
      cpu       = 2048
      memory    = 4096
      environment = concat([
        {
          name  = "NAMESPACE"
          value = var.namespace
        }
        ],
        var.runner_group != null ? [
          {
            name  = "RUNNER_GROUP"
            value = var.runner_group
          }
        ] : [],
        var.runner_labels != null ? [
          {
            name  = "RUNNER_LABELS"
            value = var.runner_labels
          }
        ] : []
      )
      command = ["./entrypoint_token.sh"]
      log_configuration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.function_log_group.name
          awslogs-region        = data.aws_region.current.name
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
  security_group_ids = [aws_security_group.vpce_security_group.id]
  subnet_ids         = [var.routable_subnet_a, var.routable_subnet_b]
}

resource "aws_apigatewayv2_api" "hook_api" {
  name          = "${var.namespace}-github-workflow_job hook"
  protocol_type = "HTTP"

  target = aws_lambda_function.function.arn
}

module "files" {
  source  = "HappyPathway/files/ls"
  pattern = "./runnerhoook/*"
}

data "archive_file" "runnerhook" {
  type        = "zip"
  output_path = "runnerhook.zip"

  dynamic "source" {
    for_each = module.files.files
    content {
      content  = file(source.value)
      filename = split("/", source.value)[length(split("/", source.value)) - 1]
    }
  }
  depends_on = [module.files]
}

resource "aws_lambda_function" "function" {
  function_name = var.namespace
  handler       = "handler.handler"
  runtime       = "python3.9"
  role          = aws_iam_role.runner_hook_role.arn
  filename      = "runnerhook.zip"
  memory_size   = 128
  timeout       = 30

  environment {
    variables = {
      AWS_ENV                  = var.environment
      GITHUB_PAT_TOKEN_ARN     = aws_secretsmanager_secret.git_access_token.arn
      GITHUB_API_URL           = var.github_url
      GITHUB_HOOK_SECRET       = random_password.git_hook_secret_password.result
      ECS_CLUSTER              = var.ecs_cluster
      TASK_DEFINITION_ARN      = aws_ecs_task_definition.runner_task_definition.arn
      CONTAINER_NAME           = var.namespace
      CONTAINER_SECURITY_GROUP = aws_security_group.container_security_group.id
      SUBNET_A                 = var.island_subnet_a
      SUBNET_B                 = var.island_subnet_b
      RUNNER_LABELS            = var.runner_labels
    }
  }

  vpc_config {
    security_group_ids = [aws_security_group.serverless_security_group.id]
    subnet_ids         = [var.island_subnet_a, var.island_subnet_b]
  }
}

resource "aws_ssm_parameter" "hook_url_ssm_parameter" {
  name        = "${var.namespace}HookUrl"
  description = "The API endpoint for runner github webhook"
  type        = "String"
  # Value: !Sub "https://${HookApi}-${VpcEndpoint}.execute-api.${AWS::Region}.${AWS::URLSuffix}/prod/workflow/run"
  value = "${aws_apigatewayv2_api.hook_api.api_endpoint}.execute-api.${data.aws_region.current.name}.amazonaws.com/prod/workflow/run"
}

output "function_name" {
  value = aws_lambda_function.function.function_name
}

output "web_hook_url" {
  value = aws_ssm_parameter.hook_url_ssm_parameter.value
}
