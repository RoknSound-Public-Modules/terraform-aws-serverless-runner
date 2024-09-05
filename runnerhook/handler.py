''' The lambda handler for workflow_job payload events '''
# noqa: E501
# pylint: disable=W0511,W0703,W0212,R0911

import hmac
import hashlib
from os import environ
import logging
import json
import boto3
from github import Github

logger = logging.getLogger('runner-hook')
logger.setLevel(logging.INFO)

def handler(event: dict, _context):
    '''
    Handle the lambda event that contains the github workflow_job payload
    and launches a github runner via ecs fargate task

    :param event: The lambda event
    :param _context: The lambda context
    '''
    logger.info("event: %s", event)
    try:
        verify_environment()
    except Exception:
        logger.error('Missing expected environment config')
        return {
            'statusCode': 500,
            'body': 'Internal Error'
        }

    session = boto3.session.Session()

    try:
        verify_github_hook(event, session)
    except Exception:
        logger.error('Unable to verify webhook payload')
        return {
            'statusCode': 403,
            'body': 'Bad Signature'
        }

    if event.get('headers', {}).get('X-GitHub-Event') == 'ping':
        return {
            'statusCode': 200,
            'body': 'Ack'
        }

    webhook_payload = json.loads(event.get('body','{}'))
    if event.get('headers', {}).get('X-GitHub-Event') == 'workflow_job' and webhook_payload.get('action') == 'queued' and webhook_payload.get('workflow_job') and webhook_payload.get('repository'):
        job = webhook_payload['workflow_job']
        repo = webhook_payload['repository']
        job_id = job.get('id')
        labels = job.get('labels', [])
        repo_name = repo['full_name']
        repo_url = repo['html_url']

        runner_labels = environ.get('RUNNER_LABELS', '').split(',')
        missing_labels = [label for label in labels if label not in runner_labels]
        if len(missing_labels) > 0:
            return {
                'statusCode': 400,
                'body': 'Unsupported labels'
            }

        try:
            registration_token = generate_runner_token(repo_name, session)
            launch_ecs_runner(repo_name, repo_url, job_id, registration_token, session)
            return {
                'statusCode': 200,
                'body': 'Runner launched'
            }
        except Exception:
            return {
                'statusCode': 500,
                'body': 'Internal Error'
            }
    else:
        return {
            'statusCode': 400,
            'body': 'Unsupported'
        }

def verify_github_hook(event: dict, boto_session: boto3.Session):
    '''
    Verify the github webhook by comparing locally hashed body with provided header.
    See https://docs.github.com/en/enterprise-server@3.5/developers/webhooks-and-events/webhooks/securing-your-webhooks

    :param event: The lambda event containing the webhook request
    :param boto_session: the AWS boto3 session
    '''
    try:
        session_manager = boto_session.client('secretsmanager')
        hook_secret = session_manager.get_secret_value(SecretId=environ.get('GITHUB_HOOK_SECRET'))['SecretString']

        gh_sig_digest = event['headers']['X-Hub-Signature-256'].replace('sha256=', '')
        computed_digest = hmac.new(hook_secret.encode('utf-8'), event['body'].encode('utf-8'), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(gh_sig_digest, computed_digest):
            logger.warning("Invalid signature - %s", computed_digest)
            raise Exception('Body Signature is invalid')
        logger.info("Valid signature detected")
        return True
    except Exception as error:
        logger.exception('Unable to validate github signature')
        raise error

def verify_environment():
    '''
    Verify all required environment variables exist

    :raise Exception: if a environment variable is missing
    '''
    expected_keys = [
        'GITHUB_SECRET_ARN',
        'GITHUB_API_URL',
        'GITHUB_HOOK_SECRET',
        'ECS_CLUSTER',
        'TASK_DEFINITION_ARN',
        'CONTAINER_NAME',
        'CONTAINER_SECURITY_GROUP',
        'SUBNET_A',
        'SUBNET_B',
        'RUNNER_LABELS'
    ]

    for key in expected_keys:
        if not environ.get(key):
            raise Exception(f"Missing environment variable {key}")

def generate_runner_token(repo_name: str, boto_session: boto3.Session) -> str:
    '''
    Generate a github actions runner registration token
    See https://docs.github.com/en/rest/actions/self-hosted-runners#create-a-registration-token-for-a-repository

    :param repo_name: the repo to generate the token for
    :param boto_session: the AWS boto3 session for getting the github token to make the api call
    :return token: the runner registration token
    '''
    try:
        session_manager = boto_session.client('secretsmanager')
        git_secret = session_manager.get_secret_value(SecretId=environ.get('GITHUB_SECRET_ARN'))['SecretString']
        git_token = json.loads(git_secret)["token"]
    except Exception as error:
        logger.exception('Unable to retrieve git secret')
        raise error

    try:
        gh_client = Github(base_url=environ.get('GITHUB_API_URL'), login_or_token=git_token)
        repo = gh_client.get_repo(repo_name)

        # Using this internal API isn't great, but the github library doesn't natively support this API method yet
        status, _response_headers, output = repo._requester.requestJson("POST", f"{repo.url}/actions/runners/registration-token")
        if status == 201:
            response = json.loads(output)
            logger.info('Runner registration token for %s expires %s', repo_name, response.get('expires_at'))
            return response.get('token')
        logger.error('Error requesting registration token - response: %s, %s', status, output)
        raise Exception('Unable to generate runner registration')
    except Exception as error:
        logger.exception('Error requesting registration token')
        raise error

def launch_ecs_runner(repo_name: str, repo_url: str, job_id: str, registration_token: str, boto_session: boto3.Session) -> str:
    '''
    Launch an ECS task to create a github runner for the repo

    :param repo_name: the full name of the repo
    :param repo_url: the full html url of the repo
    :param job_id: the id of the workflow run/job
    :param registration_token: the github runner registration token
    :param boto_session: the AWS boto3 session for interacting with ECS

    :return task_arn: the arn of the launched task
    '''
    try:
        ecs_client = boto_session.client('ecs')
        response = ecs_client.run_task(
            cluster=environ.get('ECS_CLUSTER'),
            count=1,
            enableECSManagedTags=True,
            enableExecuteCommand=False,
            launchType='FARGATE',
            networkConfiguration={
                'awsvpcConfiguration': {
                    'subnets': [ environ.get('SUBNET_A'), environ.get('SUBNET_B') ],
                    'securityGroups': [ environ.get('CONTAINER_SECURITY_GROUP') ],
                    'assignPublicIp': 'DISABLED'
                }
            },
            overrides={
                'containerOverrides': [
                    {
                        'name': environ.get('CONTAINER_NAME'),
                        'environment': [
                            { 'name': 'REPO_URL', 'value': repo_url },
                            { 'name': 'ACCESS_TOKEN', 'value': registration_token }
                        ]
                    }
                ]
            },
            propagateTags='TASK_DEFINITION',
            startedBy=f"{repo_name}/runs/{job_id}",
            taskDefinition=environ.get('TASK_DEFINITION_ARN')
        )

        if 'tasks' in response:
            logger.info('Launched task %s', response.get('tasks')[0].get('taskArn'))
            return response.get('tasks')[0].get('taskArn')
        logger.error('Failed to launch task %s', response.get('failures')[0].get('reason'))
        raise Exception('Unable to launch runner')
    except Exception as error:
        logger.exception('Error launching runner task')
        raise error
