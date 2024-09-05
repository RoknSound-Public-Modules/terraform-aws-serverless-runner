#!/bin/bash -m
export PATH="$PATH:/actions-runner"
RUNNER_NAME_FULL="$NAMESPACE-$HOSTNAME"

# Cut the name if it is more than 64 characters
RUNNER_NAME=${RUNNER_NAME_FULL:0:64}

# Support for setup-python
AGENT_TOOLSDIRECTORY=/opt/hostedtoolscache

./config.sh \
    --unattended \
    --url "${REPO_URL}" \
    --token "${ACCESS_TOKEN}" \
    --name "${RUNNER_NAME}" \
    --runnergroup "${RUNNER_GROUP}" \
    --labels "${RUNNER_LABELS}" \
    --disableupdate \
    --replace \
    --ephemeral

echo "github runner config with token complete."

env -u ACCESS_TOKEN ./run.sh
