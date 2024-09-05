data "github_repository" "repo" {
  full_name = "${var.github_org}/${var.github_repo}"
}

resource "github_repository_webhook" "foo" {
  repository = data.github_repository.repo.name

  configuration {
    url          = aws_apigatewayv2_api.hook_api.api_endpoint
    content_type = "form"
    insecure_ssl = false
  }

  active = false

  events = var.webhook_events
}
