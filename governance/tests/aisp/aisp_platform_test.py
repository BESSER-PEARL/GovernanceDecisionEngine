"""Integration tests for MOSAICOPlatform (the AISP/A2A interface), exercised
against a real A2A client (the a2a-sdk itself) -- see docs/aisp-interface.md.

Like governance/tests/kubernetes/kubernetes_merge_policy.py, this assumes the
engine is already running in a separate process, pointed at
governance/tests/policy_examples/majority_policy.txt:

    cd GovernanceDecisionEngine
    PYTHONPATH=<path-to>/GovernanceDSL python governance/engine/decision_engine.py \
        -p -P governance/tests/policy_examples/majority_policy.txt

Then, from a second terminal:

    cd GovernanceDecisionEngine/governance/tests/aisp
    pytest aisp_platform_test.py -v

`majority_policy.txt` declares `TestPolicy` (MajorityPolicy, ratio 0.5) over
scope `owner/repo` / `myActivity` / `Pull request` (action `review`), with
`reviewer` participants `adem` and `gwendal` (and `Mike`, excluded).
"""

import asyncio
import uuid

import httpx
from a2a.client import ClientConfig, ClientFactory
from a2a.helpers import get_data_parts, new_data_message
from a2a.types import Role, SendMessageRequest, TaskState

AISP_URL = 'http://localhost:8910'

# The "unresolvable scope" test deliberately waits out the server-side
# DECISION_TIMEOUT_SECONDS (agent_executor.py), so the client timeout must be
# longer than that.
CLIENT_TIMEOUT_SECONDS = 20


def _evaluate(collaboration_id: str, participants: list[dict], action: str = 'review'):
    payload = {
        'collaborationId': collaboration_id,
        'scope': {
            'project': 'owner/repo',
            'activity': 'myActivity',
            'task': 'Pull request',
            'action': action,
        },
        'proposedBy': 'joe',
        'participants': participants,
    }

    async def send():
        config = ClientConfig(httpx_client=httpx.AsyncClient(timeout=CLIENT_TIMEOUT_SECONDS))
        client = await ClientFactory(config).create_from_url(AISP_URL)
        try:
            message = new_data_message(payload, role=Role.ROLE_USER)
            request = SendMessageRequest(message=message)
            task = None
            async for response in client.send_message(request):
                if response.HasField('task'):
                    task = response.task
            return task
        finally:
            await client.close()

    return asyncio.run(send())


def _artifact_data(task, name: str):
    for artifact in task.artifacts:
        if artifact.name == name:
            return get_data_parts(artifact.parts)[0]
    return None


def _artifact_text(task, name: str):
    for artifact in task.artifacts:
        if artifact.name == name:
            return artifact.parts[0].text
    return None


def test_evaluate_collaboration_accepted():
    task = _evaluate(
        f'aisp-test-{uuid.uuid4()}',
        [
            {'id': 'adem', 'agreement': True, 'rationale': 'LGTM'},
            {'id': 'gwendal', 'agreement': True, 'rationale': 'Looks fine'},
        ],
    )

    assert task.status.state == TaskState.TASK_STATE_COMPLETED
    decision = _artifact_data(task, 'decision')
    assert decision['accepted'] is True
    assert decision['rule'] == 'TestPolicy'
    assert _artifact_text(task, 'explanation')


def test_evaluate_collaboration_rejected():
    task = _evaluate(
        f'aisp-test-{uuid.uuid4()}',
        [
            {'id': 'adem', 'agreement': False, 'rationale': 'needs work'},
            {'id': 'gwendal', 'agreement': False, 'rationale': 'disagree'},
        ],
    )

    assert task.status.state == TaskState.TASK_STATE_COMPLETED
    decision = _artifact_data(task, 'decision')
    assert decision['accepted'] is False
    assert decision['rule'] == 'TestPolicy'


def test_evaluate_collaboration_unresolvable_scope_fails():
    # No policy is declared for this scope/project, so the request can never
    # become decidable -- the executor should fail the task rather than hang
    # (see agent_executor.py's DECISION_TIMEOUT_SECONDS).
    task = _evaluate(
        f'aisp-test-{uuid.uuid4()}',
        [{'id': 'adem', 'agreement': True}],
        action='merge',  # majority_policy.txt only covers action "review"
    )

    assert task.status.state == TaskState.TASK_STATE_FAILED
