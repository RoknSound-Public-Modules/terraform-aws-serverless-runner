# GitHub Enterprise Actions Runners

## Overview

This repository will create a pipeline to launch [self-hosted Github Action Runners](https://docs.github.com/en/actions/hosting-your-own-runners/about-self-hosted-runners) for 3M's [Github Enterprise](https://github.mmm.com).

This runner DOES NOT enable docker tasks. That would require docker-in-docker functionality which is not enabled on Fargate.
See: aws-containers-roadmap <https://github.com/aws/containers-roadmap/issues/1356>

Below is a description of notable resources deployed by the pipeline:

| Resource   | Description          | Stack     |
| ---------- | -------------------- | ----------|
| API Gateway | Accepts the webhook from GitHub enterprise and triggers the lambda. | Serverless.yml |
| VPC Endpoint| Endpoint for the API Gateway | Serverless.yml |
| ECS runner task definition | Contains the configuration for the ECS Fargate runner | Serverless.yml |
| Lambda  | Starts the runner using the task definition. | Serverless.yml |
| `namespace`GitToken secret | Secrets manager secret to store the access token used for registering the webhook to the repo | Secrets.yml |
| `namespace`HookSecret secret | Secrets manager secret to store the random string used to secure the webhook communication. This is generated for you. | Secrets.yml |

## Configuration

This pipeline requires configuration in the account where you will be deploying the runners.

1) ### Networking Connectivity
    The networking team needs to enable connectivity from GitHub enterprise to the account and VPC where the API gateway endpoint will be deployed. By default, the API gateway endpoint is deployed to the routable subnets.
    To request this access, open an HISHOST `task` Jira ticket and provide the routable VPC and subnet IDs in the ticket.
1)  ### Runner target
    The runners can respond to jobs from a specific repository or all repositories in a given organization. Set the `runner_target` value for the environment in [blackbird_config.yml](blackbird_config.yml) to the organization name or the specific repository (e.g `myorg\testteam-pipeline`). The pipeline automatically registers a webhook in the target
    when the environment is deployed using the `worflow_job` trigger (https://docs.github.com/en/developers/webhooks-and-events/webhooks/webhook-events-and-payloads#workflow_job). By default, this is set to the pipeline repo for this pipeline.
1) ### Runner labels
    The runners will respond to jobs when the labels on the job match the runner's  labels (See [Using Labels](https://docs.github.com/en/actions/hosting-your-own-runners/using-labels-with-self-hosted-runners)). Runner labels can be configured using `runner_labels` list in [blackbird_config.yml](blackbird_config.yml) for each environment. By default, the labels applied are `self-hosted,linux`.
1) ### Github Access Token
    The solution requires a Github API token to communicate with the API to register the runners and configure the webhook. For organization targets, the token will need organization admin (`admin:org` scope) and repo admin permissions (`repo` scope). For repo targets, the token will need repo admin permissions (`repo` scope). To create the token, see [Create a PAT](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token).

    Update the Secrets Manager secret with the created token. The secret name is `'namespace'GitToken`. Note that you must run the pipeline through the environment FoundationalStacks step before the secret is created. When updating the secret, be sure you set it using the key/value configuration with 'token' as the secret key and the GitHub access token as the secret value.
1) ### Github Webhook Secret
    When the pipeline is deployed, it generates a random secret which is used to [secure the Github Webhook](https://docs.github.com/en/developers/webhooks-and-events/webhooks/securing-your-webhooks). This is stored in AWS Secrets Manager in the deployment account under the name `'namespace'HookSecret`. You can rotate the token as needed by updating the secret in secrets manager and executing the pipeline to sync the webhook configuration.

## Architecture

![Runner Scaling Diagram](actions_runner_scaling.png)

Action runners are launched by integrating with Github's [workflow_job webhook](https://docs.github.com/en/developers/webhooks-and-events/webhooks/webhook-events-and-payloads#workflow_job). When a new job is queued, Github invokes a API Gateway in the deployment account and passes the request the [runnerhook](runnerhook/handler.py) lambda function. The lambda function generates a [runner registration token](https://docs.github.com/en/rest/actions/self-hosted-runners#create-a-registration-token-for-a-repository) and launches an ECS fargate task. The task registers with Github and executes the Actions job. When the job is finished, the runner deregisters.

The webhook configuration is automatically created and updated with the pipeline.


## Runner Environment

The runners execute within ECS Fargate as docker containers. This *DOES NOT* enable docker tasks. That would require docker-in-docker functionality which is not enabled on [Fargate](https://github.com/aws/containers-roadmap/issues/1356).

### OS
The OS and related packages are controlled by the [Dockerfile](app/Dockerfile.ubuntu) which is used to build the runner image. By default, this image is based on Ubuntu 22.04 LTS. Minimal packages are installed by default, but sudo permissions are available which mirrors the standard Github Virtual Environments.

Use official actions to configure required runtimes (e.g [setup-python](https://github.com/actions/setup-python)) where possible. This increases the portability of your runner image across multiple repos and mirrors how commercial Github Runners would be used.

### Security
The runners have minimal AWS permissions that are controlled by the IAM role assigned to the ECS task. You can view and configure the `EcsTaskRole` in the [Roles template](CloudFormation/Roles.jinja.yml).
It is recommended that you regularly change the access token that is used for registering the webhook. You should also regularly deploy the pipeline to update the docker image with the latest security patches.

## Setting up workflows

The Blackbird team has created workflows for various tasks that can be used in a Blackbird pipeline that can be accessed here: https://github.mmm.com/blackbird/blackbird-actions-workflow. This repo will be updated regularly and we welcome contributers.
<!-- BEGIN_TF_DOCS -->
## Requirements

No requirements.

## Providers

No providers.

## Modules

No modules.

## Resources

No resources.

## Inputs

No inputs.

## Outputs

No outputs.
<!-- END_TF_DOCS -->