# terraform-aws-serverless-runner
Terraform Module

<!-- BEGIN_TF_DOCS -->
## Requirements

No requirements.

## Providers

| Name | Version |
|------|---------|
| <a name="provider_archive"></a> [archive](#provider\_archive) | 2.5.0 |
| <a name="provider_aws"></a> [aws](#provider\_aws) | 5.65.0 |
| <a name="provider_github"></a> [github](#provider\_github) | 6.2.3 |
| <a name="provider_random"></a> [random](#provider\_random) | 3.6.2 |

## Modules

| Name | Source | Version |
|------|--------|---------|
| <a name="module_files"></a> [files](#module\_files) | HappyPathway/files/ls | n/a |

## Resources

| Name | Type |
|------|------|
| [aws_apigatewayv2_api.hook_api](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/apigatewayv2_api) | resource |
| [aws_cloudwatch_log_group.access_log_group](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_group) | resource |
| [aws_cloudwatch_log_group.function_log_group](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_group) | resource |
| [aws_cloudwatch_log_group.log_group](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudwatch_log_group) | resource |
| [aws_ecs_task_definition.runner_task_definition](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ecs_task_definition) | resource |
| [aws_iam_role.ecs_task_execution_role](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role) | resource |
| [aws_iam_role.ecs_task_role](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role) | resource |
| [aws_iam_role.runner_hook_role](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role) | resource |
| [aws_lambda_function.function](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function) | resource |
| [aws_secretsmanager_secret.git_access_token](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/secretsmanager_secret) | resource |
| [aws_secretsmanager_secret.git_hook_secret](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/secretsmanager_secret) | resource |
| [aws_secretsmanager_secret_version.git_access_token_version](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/secretsmanager_secret_version) | resource |
| [aws_secretsmanager_secret_version.git_hook_secret_version](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/secretsmanager_secret_version) | resource |
| [aws_security_group.container_security_group](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/security_group) | resource |
| [aws_security_group.serverless_security_group](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/security_group) | resource |
| [aws_security_group.vpce_security_group](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/security_group) | resource |
| [aws_security_group_rule.container_security_group_egress](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/security_group_rule) | resource |
| [aws_security_group_rule.serverless_security_group_egress](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/security_group_rule) | resource |
| [aws_security_group_rule.vpce_security_group_egress](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/security_group_rule) | resource |
| [aws_security_group_rule.vpce_security_group_ingress](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/security_group_rule) | resource |
| [aws_ssm_parameter.hook_url_ssm_parameter](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ssm_parameter) | resource |
| [aws_vpc_endpoint.vpc_endpoint](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc_endpoint) | resource |
| [github_repository_webhook.foo](https://registry.terraform.io/providers/hashicorp/github/latest/docs/resources/repository_webhook) | resource |
| [random_password.git_hook_secret_password](https://registry.terraform.io/providers/hashicorp/random/latest/docs/resources/password) | resource |
| [archive_file.runnerhook](https://registry.terraform.io/providers/hashicorp/archive/latest/docs/data-sources/file) | data source |
| [aws_partition.current](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/partition) | data source |
| [aws_region.current](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/region) | data source |
| [github_repository.repo](https://registry.terraform.io/providers/hashicorp/github/latest/docs/data-sources/repository) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_ecs_cluster"></a> [ecs\_cluster](#input\_ecs\_cluster) | Cluster used to create and execute tasks | `string` | n/a | yes |
| <a name="input_environment"></a> [environment](#input\_environment) | Name of the AWS deployment environment | `string` | n/a | yes |
| <a name="input_github_org"></a> [github\_org](#input\_github\_org) | github organization | `string` | n/a | yes |
| <a name="input_github_pat"></a> [github\_pat](#input\_github\_pat) | github personal access token | `string` | n/a | yes |
| <a name="input_github_repo"></a> [github\_repo](#input\_github\_repo) | github repository | `string` | n/a | yes |
| <a name="input_github_url"></a> [github\_url](#input\_github\_url) | github url | `string` | `"https://github.com/api/v3"` | no |
| <a name="input_image"></a> [image](#input\_image) | The container to run tasks in | `string` | n/a | yes |
| <a name="input_island_subnet_a"></a> [island\_subnet\_a](#input\_island\_subnet\_a) | Subnets used for Service Template | `string` | n/a | yes |
| <a name="input_island_subnet_b"></a> [island\_subnet\_b](#input\_island\_subnet\_b) | Subnets used for Service Template | `string` | n/a | yes |
| <a name="input_namespace"></a> [namespace](#input\_namespace) | Prefix for all resources generated by the pipeline | `string` | n/a | yes |
| <a name="input_routable_subnet_a"></a> [routable\_subnet\_a](#input\_routable\_subnet\_a) | Subnets used for Service Template | `string` | n/a | yes |
| <a name="input_routable_subnet_b"></a> [routable\_subnet\_b](#input\_routable\_subnet\_b) | Subnets used for Service Template | `string` | n/a | yes |
| <a name="input_runner_group"></a> [runner\_group](#input\_runner\_group) | Name of the runner group | `string` | `null` | no |
| <a name="input_runner_labels"></a> [runner\_labels](#input\_runner\_labels) | Comma-separated list of runner labels | `string` | `null` | no |
| <a name="input_tag"></a> [tag](#input\_tag) | Used as the aws log stream prefix | `string` | n/a | yes |
| <a name="input_vpc_id"></a> [vpc\_id](#input\_vpc\_id) | VPC ID to build in | `string` | n/a | yes |
| <a name="input_webhook_events"></a> [webhook\_events](#input\_webhook\_events) | github webhook events | `list(string)` | n/a | yes |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_access_log_group_arn"></a> [access\_log\_group\_arn](#output\_access\_log\_group\_arn) | n/a |
| <a name="output_container_security_group"></a> [container\_security\_group](#output\_container\_security\_group) | n/a |
| <a name="output_ecs_task_execution_role_arn"></a> [ecs\_task\_execution\_role\_arn](#output\_ecs\_task\_execution\_role\_arn) | n/a |
| <a name="output_ecs_task_role_arn"></a> [ecs\_task\_role\_arn](#output\_ecs\_task\_role\_arn) | n/a |
| <a name="output_function_log_group"></a> [function\_log\_group](#output\_function\_log\_group) | n/a |
| <a name="output_function_name"></a> [function\_name](#output\_function\_name) | n/a |
| <a name="output_git_access_token"></a> [git\_access\_token](#output\_git\_access\_token) | n/a |
| <a name="output_git_hook_secret"></a> [git\_hook\_secret](#output\_git\_hook\_secret) | n/a |
| <a name="output_log_group"></a> [log\_group](#output\_log\_group) | n/a |
| <a name="output_runner_hook_role_arn"></a> [runner\_hook\_role\_arn](#output\_runner\_hook\_role\_arn) | n/a |
| <a name="output_serverless_security_group"></a> [serverless\_security\_group](#output\_serverless\_security\_group) | n/a |
| <a name="output_vpce_security_group"></a> [vpce\_security\_group](#output\_vpce\_security\_group) | n/a |
| <a name="output_web_hook_url"></a> [web\_hook\_url](#output\_web\_hook\_url) | n/a |
<!-- END_TF_DOCS -->