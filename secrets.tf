
resource "random_password" "git_hook_secret_password" {
  length           = 64
  special          = true
  override_special = "_%@"
}

resource "aws_secretsmanager_secret" "git_hook_secret" {
  description = "Webhook secret for github integration"
  name        = "${var.namespace}HookSecret"
  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_secretsmanager_secret_version" "git_hook_secret_version" {
  secret_id     = aws_secretsmanager_secret.git_hook_secret.id
  secret_string = random_password.git_hook_secret_password.result
}


resource "aws_secretsmanager_secret" "git_access_token" {
  description = "GitHub access token for registering runners in the organization or repo"

  name = "${var.namespace}GitToken"

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_secretsmanager_secret_version" "git_access_token_version" {
  secret_id     = aws_secretsmanager_secret.git_access_token.id
  secret_string = var.github_pat
}

output "git_hook_secret" {
  value = aws_secretsmanager_secret.git_hook_secret.id
}

output "git_access_token" {
  value = aws_secretsmanager_secret.git_access_token.id
}
