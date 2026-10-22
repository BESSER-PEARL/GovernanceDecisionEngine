"""Translates between the AISP wire format (docs/aisp-interface.md) and the
engine's existing runtime objects (governance.engine.semantics.runtime_metamodel).

Deliberately a thin, direct mapping: no new domain concepts are introduced on
top of what governance.engine.events.CollaborationProposalEvent/VoteEvent and
governancedsl.utils.chp_extension already model for the GitHub integration.
"""

from dataclasses import dataclass, field

from governancedsl.metamodel import Activity, StatusEnum
from governancedsl.utils.chp_extension import Issue, Label, Patch, PatchAction, PullRequest, Repository

from governance.engine.semantics.runtime_metamodel import Decision


@dataclass
class ParticipantVote:
    """A vote/opinion for one participant.

    Note: agent vote-weighting (confidence/autonomy_level/explainability) is not
    carried here -- it is resolved by Collaboration.vote() from the (Agent)
    participant already declared in the loaded governance policy, matched by
    `id` against the policy's Individuals/Roles section.
    """
    id: str
    agreement: bool
    role: str | None = None
    rationale: str | None = None


@dataclass
class ScopeRequest:
    project: str
    task: str
    activity: str | None = None
    action: str | None = None
    labels: list[str] = field(default_factory=list)


@dataclass
class EvaluateCollaborationRequest:
    collaboration_id: str
    scope: ScopeRequest
    proposed_by: str
    participants: list[ParticipantVote]
    policy: str | None = None
    rationale: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> 'EvaluateCollaborationRequest':
        scope_data = data['scope']
        scope = ScopeRequest(
            project=scope_data['project'],
            task=scope_data['task'],
            activity=scope_data.get('activity'),
            action=scope_data.get('action'),
            labels=list(scope_data.get('labels', [])),
        )
        participants = [
            ParticipantVote(
                id=p['id'],
                agreement=p['agreement'],
                role=p.get('role'),
                rationale=p.get('rationale'),
            )
            for p in data['participants']
        ]
        return cls(
            collaboration_id=data['collaborationId'],
            scope=scope,
            proposed_by=data['proposedBy'],
            participants=participants,
            policy=data.get('policy'),
            rationale=data.get('rationale'),
        )


_TASK_TYPES = {
    'pull request': PullRequest,
    'pullrequest': PullRequest,
    'issue': Issue,
}

_PATCH_ACTIONS = {
    'merge': PatchAction.MERGE,
    'review': PatchAction.REVIEW,
}


def build_scope(request: EvaluateCollaborationRequest) -> Patch:
    """Build an ephemeral Patch/Activity/Repository scope tree from an AISP
    request, mirroring what CollaborationProposalEvent.from_github_event builds
    from a webhook payload. It is matched by value (repo id, action, element
    type, labels) against a loaded policy's declared scope -- see
    governance/engine/semantics/scope_comparator.py -- not by object identity.
    """
    element_type = _TASK_TYPES.get(request.scope.task.strip().lower(), PullRequest)
    labels = {Label(name) for name in request.scope.labels}
    element = element_type(request.scope.task, labels)

    action = _PATCH_ACTIONS.get((request.scope.action or '').strip().lower(), PatchAction.ALL)

    title = f"{request.scope.task} {request.collaboration_id} of {request.scope.project}"
    scope = Patch(title, StatusEnum.ACCEPTED, action, element)
    scope.activity = Activity(request.scope.activity or '', StatusEnum.ACCEPTED)
    scope.activity.tasks = {scope}
    scope.activity.project = Repository(
        "Repository " + request.scope.project, StatusEnum.ACCEPTED, request.scope.project
    )
    scope.activity.project.activities = {scope.activity}
    return scope


def decision_result(decision: Decision) -> dict:
    """Shapes a Decision into the AISP `decision` artifact's data part,
    reusing the same `Evaluation`-like shape already defined for Supervision
    Agents in mosaico-demonstrator/docs/agent-requirements.md.
    """
    return {
        'accepted': bool(decision._accepted),
        'rule': decision._rule.name,
        'votes': [
            {
                'id': vote.voted_by.name,
                'agreement': vote._agreement,
                'voteValue': vote._vote_value,
            }
            for vote in decision._votes
        ],
    }


def decision_explanation(decision: Decision) -> str:
    """Natural-language rationale for the `explanation` artifact. Deterministic,
    no LLM involved for T4.3 (the Consensus Agent, T4.4, may replace/augment
    this later for escalated cases).
    """
    outcome = 'accepted' if decision._accepted else 'rejected'
    votes_summary = ', '.join(
        f"{vote.voted_by.name} ({'for' if vote._agreement else 'against'}, weight {vote._vote_value:.2f})"
        for vote in decision._votes
    ) or 'no votes were counted'
    return (
        f"Collaboration '{decision._decides._id}' was {outcome} under policy "
        f"'{decision._rule.name}'. Votes counted: {votes_summary}."
    )
