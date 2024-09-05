from unittest import mock
import pytest
import boto3
import json
import os
from moto import mock_secretsmanager, mock_ecs
from handler import handler, verify_environment, generate_runner_token, launch_ecs_runner, verify_github_hook

@pytest.fixture
def queued_payload():
    event_path = os.path.join(os.path.dirname(__file__), 'mocks/webhook_job_payload.json')
    return open(event_path).read()

@pytest.fixture
def in_progress_payload():
    event_path = os.path.join(os.path.dirname(__file__), 'mocks/webhook_job_payload.json')
    payload = json.load(open(event_path))
    payload['action'] = 'in_progress'

    return json.dumps(payload)

@pytest.fixture
def preset_environment():
    return {
        'GITHUB_SECRET_ARN': 'somevalue',
        'GITHUB_API_URL': 'https://git.mmm.com/api/v3',
        'GITHUB_HOOK_SECRET': 'thesecrethooksettings',
        'ECS_CLUSTER': 'mytestcluster',
        'TASK_DEFINITION_ARN': 'arn:example',
        'CONTAINER_NAME': 'fastimage',
        'CONTAINER_SECURITY_GROUP': 'sg-123',
        'SUBNET_A': 'subnet-01234567890abcdef',
        'SUBNET_B': 'subnet-01234567890abcdeg',
        'AWS_DEFAULT_REGION': 'us-east-1',
        'RUNNER_LABELS': 'hello,test'
    }

def test_verify_environment_invalid():
    with pytest.raises(Exception) as excinfo:
        verify_environment()
    assert 'Missing environment variable' in str(excinfo.value)

def test_verify_environment(preset_environment):
    with mock.patch.dict(os.environ, preset_environment):
        verify_environment()

@mock.patch('handler.verify_environment')
def test_handler_wrong_environment(verify_env_mock):
    verify_env_mock.side_effect = Exception("Missing environment variable bob")

    result = handler({}, None)
    assert result['statusCode'] == 500

@mock.patch('handler.verify_environment')
@mock.patch('handler.boto3')
@mock.patch('handler.verify_github_hook')
def test_handler_invalid_hook(mock_verify_hook, mock_boto3, mock_verify_env, preset_environment):
    mock_verify_hook.side_effect = Exception("Invalid webhook signature")

    with mock.patch.dict(os.environ, preset_environment):
        result = handler({}, None)
    assert result['statusCode'] == 403

@mock.patch('handler.verify_environment')
@mock.patch('handler.boto3')
@mock.patch('handler.verify_github_hook')
def test_handler_ping_event(mock_verify_hook, mock_boto3, mock_verify_env, preset_environment):
    hook = {
        'headers': {
            'X-GitHub-Event': 'ping'
        }
    }

    with mock.patch.dict(os.environ, preset_environment):
        result = handler(hook, None)
    assert result['statusCode'] == 200

@mock.patch('handler.verify_environment')
@mock.patch('handler.boto3')
@mock.patch('handler.verify_github_hook')
def test_handler_wrong_hook(mock_verify_hook, mock_boto3, mock_verify_env, preset_environment):
    hook = {
        'headers': {
            'X-GitHub-Event': 'push'
        },
        'body': '{}'
    }

    with mock.patch.dict(os.environ, preset_environment):
        result = handler(hook, None)
    assert result['statusCode'] == 400

@mock.patch('handler.verify_environment')
@mock.patch('handler.boto3')
@mock.patch('handler.verify_github_hook')
def test_handler_wrong_hook_action(mock_verify_hook, mock_boto3, mock_verify_env, preset_environment, in_progress_payload):
    hook = {
        'headers': {
            'X-GitHub-Event': 'workflow_job'
        },
        'body': in_progress_payload
    }

    with mock.patch.dict(os.environ, preset_environment):
        result = handler(hook, None)
    assert result['statusCode'] == 400

@mock.patch('handler.verify_environment')
@mock.patch('handler.boto3')
@mock.patch('handler.verify_github_hook')
def test_handler_label_mismatch(mock_verify_hook, mock_boto3, mock_verify_env, preset_environment, queued_payload):
    hook = {
        'headers': {
            'X-GitHub-Event': 'workflow_job'
        },
        'body': queued_payload
    }

    preset_environment['RUNNER_LABELS'] = 'wrong,test'

    with mock.patch.dict(os.environ, preset_environment):
        result = handler(hook, None)
    assert result['statusCode'] == 400
    assert 'Unsupported labels' in result['body']

@mock.patch('handler.verify_environment')
@mock.patch('handler.boto3')
@mock.patch('handler.verify_github_hook')
@mock.patch('handler.generate_runner_token')
def test_handler_failure(mock_runner_token, mock_verify_hook, mock_boto3, mock_verify_env, preset_environment, queued_payload):
    hook = {
        'headers': {
            'X-GitHub-Event': 'workflow_job'
        },
        'body': queued_payload
    }

    mock_runner_token.side_effect = Exception("Unable to get registration token")

    with mock.patch.dict(os.environ, preset_environment):
        result = handler(hook, None)
    assert result['statusCode'] == 500
    mock_runner_token.assert_called_once_with('octo-org/example-workflow', mock.ANY)

@mock.patch('handler.verify_environment')
@mock.patch('handler.boto3')
@mock.patch('handler.verify_github_hook')
@mock.patch('handler.generate_runner_token')
@mock.patch('handler.launch_ecs_runner')
def test_handler(mock_ecs_runner, mock_runner_token, mock_verify_hook, mock_boto3, mock_verify_env, preset_environment, queued_payload):
    hook = {
        'headers': {
            'X-GitHub-Event': 'workflow_job'
        },
        'body': queued_payload
    }

    mock_ecs_runner.return_value = 'arn:sometask'
    mock_runner_token.return_value = 'secretregistrationtoken'

    with mock.patch.dict(os.environ, preset_environment):
        result = handler(hook, None)
    assert result['statusCode'] == 200
    mock_runner_token.assert_called_once_with('octo-org/example-workflow', mock.ANY)
    mock_ecs_runner.assert_called_once_with('octo-org/example-workflow', 'https://github.com/octo-org/example-workflow', 2832853555, 'secretregistrationtoken', mock.ANY)

@mock_secretsmanager
def test_generate_runner_token_missing_secret(preset_environment):
    session = boto3.session.Session(region_name='us-east-1')
    with mock.patch.dict(os.environ, preset_environment):
        with pytest.raises(Exception) as excinfo:
            generate_runner_token('my-cool-org/builder', session)
        assert 'ResourceNotFoundException' in str(excinfo.value)

@mock_secretsmanager
@mock.patch('handler.Github')
def test_generate_runner_token_api_failure(mock_github, preset_environment):
    session = boto3.session.Session(region_name='us-east-1')
    sm = session.client('secretsmanager')
    fake_secret = sm.create_secret(
        Name='testingsecret',
        Description='string',
        SecretString='{"token": "supersecretoken"}'
    )
    preset_environment['GITHUB_SECRET_ARN'] = fake_secret['ARN']

    mock_repo = mock.MagicMock()
    mock_repo._requester.requestJson.return_value = 401, [], 'bad auth'
    mock_github().get_repo.return_value = mock_repo

    with mock.patch.dict(os.environ, preset_environment):
        with pytest.raises(Exception) as excinfo:
            generate_runner_token('my-cool-org/builder', session)
        assert 'Unable to generate runner registration' in str(excinfo.value)

@mock_secretsmanager
@mock.patch('handler.Github')
def test_generate_runner_token(mock_github, preset_environment):
    session = boto3.session.Session(region_name='us-east-1')
    sm = session.client('secretsmanager')
    fake_secret = sm.create_secret(
        Name='testingsecret',
        Description='string',
        SecretString='{"token": "supersecretoken"}'
    )
    preset_environment['GITHUB_SECRET_ARN'] = fake_secret['ARN']

    mock_repo = mock.MagicMock()
    mock_repo._requester.requestJson.return_value = 201, [], '{"token": "supersecrettoken", "expires_at": "tomorrow" }'
    mock_github().get_repo.return_value = mock_repo

    with mock.patch.dict(os.environ, preset_environment):
        token = generate_runner_token('my-cool-org/builder', session)
        assert token == 'supersecrettoken'

@mock_ecs
def test_launch_ecs_runner_invalid_cluster(preset_environment):
    session = boto3.session.Session(region_name='us-east-1')
    with mock.patch.dict(os.environ, preset_environment):
        with pytest.raises(Exception) as excinfo:
            launch_ecs_runner('my-cool-org/builder', 'https://example.com/my-cool-org/builder', 12334, 'supercooltoken', session)
        assert 'ClusterNotFoundException' in str(excinfo.value)

def test_launch_ecs_runner_failed_task(preset_environment):
    session = mock.MagicMock()

    session.client().run_task.return_value = {
        'failures': [ { 'reason': 'Task failed to start' } ]
    }

    with mock.patch.dict(os.environ, preset_environment):
        with pytest.raises(Exception) as excinfo:
            launch_ecs_runner('my-cool-org/builder', 'https://example.com/my-cool-org/builder', 12334, 'supercooltoken', session)
        assert 'Unable to launch runner' in str(excinfo.value)

def test_launch_ecs_runner(preset_environment):
    session = mock.MagicMock()

    session.client().run_task.return_value = {
        'tasks': [ { 'taskArn': 'arn:mycooltask' } ]
    }

    with mock.patch.dict(os.environ, preset_environment):
        task_arn = launch_ecs_runner('my-cool-org/builder', 'https://example.com/my-cool-org/builder', 12334, 'supercooltoken', session)
        assert task_arn == 'arn:mycooltask'

@mock_secretsmanager
def test_verify_github_hook_missing_secret(preset_environment, queued_payload):
    session = boto3.session.Session(region_name='us-east-1')

    hook = {
        'headers': {
            'X-GitHub-Event': 'workflow_job',
            'X-Hub-Signature-256': 'testsignature'
        },
        'body': queued_payload
    }

    with mock.patch.dict(os.environ, preset_environment):
        with pytest.raises(Exception) as excinfo:
            verify_github_hook(hook, session)
        assert 'ResourceNotFoundException' in str(excinfo.value)

@mock_secretsmanager
def test_verify_github_hook_invalid_signature(preset_environment, queued_payload):
    session = boto3.session.Session(region_name='us-east-1')
    sm = session.client('secretsmanager')
    fake_secret = sm.create_secret(
        Name='testingsecret',
        Description='string',
        SecretString='superimportanthookvalue'
    )
    preset_environment['GITHUB_HOOK_SECRET'] = fake_secret['ARN']

    hook = {
        'headers': {
            'X-GitHub-Event': 'workflow_job',
            'X-Hub-Signature-256': 'testsignature'
        },
        'body': queued_payload
    }

    with mock.patch.dict(os.environ, preset_environment):
        with pytest.raises(Exception) as excinfo:
            verify_github_hook(hook, session)
        assert 'Body Signature is invalid' in str(excinfo.value)

@mock_secretsmanager
def test_verify_github_hook(preset_environment, queued_payload):
    session = boto3.session.Session(region_name='us-east-1')
    sm = session.client('secretsmanager')
    fake_secret = sm.create_secret(
        Name='testingsecret',
        Description='string',
        SecretString='superimportanthookvalue'
    )
    preset_environment['GITHUB_HOOK_SECRET'] = fake_secret['ARN']

    hook = {
        'headers': {
            'X-GitHub-Event': 'workflow_job',
            'X-Hub-Signature-256': 'sha256=3ac747f4e0aa84941bd6d5de659be91f98eb57515df41295389b2d879523c00b'
        },
        'body': queued_payload
    }

    with mock.patch.dict(os.environ, preset_environment):
        token = verify_github_hook(hook, session)
        assert token == True