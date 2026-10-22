# Governance Decision Engine — AISP interface

This describes what the MOSAICO Governance Decision Engine (T4.3/T4.4, LIST) expects
in its initial A2A Message request, and what artifacts it produces, per the
[MOSAICO AISP profile](../../mosaico-demonstrator/docs/agent-requirements.md) of
[A2A v1.0.0](https://a2a-protocol.org/v1.0.0/specification/).

It is implemented by `MOSAICOPlatform`
(`governance/engine/platforms/mosaico/`), a BAF `Platform` built directly on
the official `a2a-sdk` (not BAF's own bundled `A2APlatform`, which does not
implement the real A2A wire format — see the implementation notes at the
bottom of this document).

## Integration model

Per agreement with WP3 (see `emails/Re_ WP3-WP4 Coordination.eml` and
`emails/Re_ Questions about Decision engine.eml`): the Collaboration Agent
collects votes/opinions from Supervision Agents itself, then calls the
governance agent **on demand**, once, with everything needed to decide —
rather than the engine listening for individual votes over time (as it does
today for GitHub webhooks). This keeps the AISP interface to a single
synchronous skill.

```
Collaboration Agent                    Governance Decision Engine
        │                                          │
        │  SendMessage(evaluate-collaboration)     │
        ├─────────────────────────────────────────►│
        │                                          │  propose collaboration
        │                                          │  record every vote
        │                                          │  evaluate governance policy
        │  Task { decision, explanation }          │
        │◄─────────────────────────────────────────┤
        │                                          │
```

## Agent Card

Served at `GET /.well-known/agent-card.json`. One skill:

| Field | Value |
|---|---|
| `name` | MOSAICO Governance Decision Engine |
| `skills[0].id` | `evaluate-collaboration` |
| `capabilities.extensions` | `https://mosaico-project.eu/extensions/mosaico-observability` (optional) |

`GET /health` returns `200` if the engine is reachable, per the MOSAICO
packaging conventions.

## Request: `evaluate-collaboration`

A `SendMessage` request (`A2A-Version: 1.0`) whose `Message` carries exactly
one `data` part, shaped as:

```typescript
interface EvaluateCollaborationRequest {
  collaborationId: string;    // stable id for the PR/Issue/Task being decided
  scope: {
    project: string;          // matches the Repository/Project id declared in the loaded policy's Scopes section
    activity?: string;
    task: string;             // task type, e.g. "Pull request" or "Issue"
    action?: string;          // e.g. "merge", "review" -- must match the policy's declared Action, if any
    labels?: string[];
  };
  proposedBy: string;         // login/id of the proposer
  rationale?: string;
  policy?: string;            // reserved; currently unused -- the policy is resolved from `scope`
  participants: ParticipantVote[];
}

interface ParticipantVote {
  id: string;        // login/id, resolved against the loaded policy's Individuals/Roles
  agreement: boolean; // the vote cast
  role?: string;
  rationale?: string; // free-text opinion from the Supervision Agent
}
```

Notes:

- The governance policy (govdsl) must already be loaded (via the engine's
  existing file-upload/playground mechanisms) before this request is sent —
  there is no AISP endpoint to upload a policy document yet. `scope` is
  matched by value against the loaded policy's declared `Scopes:` section
  (see `governance/engine/semantics/scope_comparator.py`), the same way a
  GitHub PR's repo/action is matched today.
- Agent vote-weighting (`confidence`/`autonomy_level`/`explainability`) is
  **not** part of `ParticipantVote` — it is resolved from the `(Agent)`
  participant already declared in the loaded policy (matched by `id`), per
  the existing `vote_value = 0.5*confidence + 0.3*autonomy_level + 0.2*explainability`
  formula.

## Response: a `Task` with two artifacts

Mirrors the Supervision Agent pattern already defined for MOSAICO (one
machine-friendly artifact, one natural-language one):

- **`decision`** — one `data` part:

  ```typescript
  interface DecisionResult {
    accepted: boolean;  // the governance policy's outcome
    rule: string;        // name of the policy that decided it
    votes: { id: string; agreement: boolean; voteValue: number }[];
  }
  ```

- **`explanation`** — one `text` part: a natural-language rationale (which
  policy/votes decided the outcome). Deterministic for T4.3 — no LLM
  involved; a future Consensus Agent (T4.4) may enrich this for escalated,
  non-decidable cases without changing the wire contract.

`Task.status.state` is `TASK_STATE_COMPLETED` when a decision was reached, or
`TASK_STATE_FAILED` if the request was malformed, no policy matched the given
scope, or the policy's conditions (e.g. `MinParticipants`) could not be
satisfied within a bounded wait (currently 15s — see
`agent_executor.DECISION_TIMEOUT_SECONDS`).

### Example

Request (`data` part):

```json
{
  "collaborationId": "pr-42",
  "scope": { "project": "owner/repo", "activity": "myActivity", "task": "Pull request", "action": "review" },
  "proposedBy": "joe",
  "participants": [
    { "id": "adem", "agreement": true, "rationale": "LGTM" },
    { "id": "gwendal", "agreement": true, "rationale": "Looks fine" }
  ]
}
```

Response (`decision` artifact's `data` part):

```json
{
  "accepted": true,
  "rule": "TestPolicy",
  "votes": [
    { "id": "adem", "agreement": true, "voteValue": 1.0 },
    { "id": "gwendal", "agreement": true, "voteValue": 1.0 }
  ]
}
```

## Implementation notes

- `besser-agentic-framework` (BAF) already ships a platform called
  `A2APlatform` (`baf.platforms.a2a`). It is **not** used here: it implements
  a bespoke, non-standard JSON-RPC/task scheme (`task_id`/`method`/`params`,
  `PENDING/RUNNING/DONE/ERROR` states) with no `Message`/`Part`/`Task`/`AgentCard`
  objects matching the real A2A spec and no `/.well-known/agent-card.json`.
  Since the rest of MOSAICO speaks genuine A2A v1.0.0 via the official SDKs,
  `MOSAICOPlatform` wraps `a2a-sdk` directly instead.
- The engine processes a request as a single new FSM event
  (`events.AISPEvaluateEvent`) handled by one state body
  (`state_bodies.aisp_evaluate_bodybuilder`), which proposes the collaboration
  and records every vote in one synchronous pass, rather than replaying it as
  a proposal event followed by separate vote events (BAF's per-session event
  queue does not guarantee FIFO ordering across back-to-back
  `receive_event()` calls, which made that initial approach race).
- Out of scope for this interface (tracked separately, see
  `MOSAICO_T43_Onboarding_Report.md`): writing collaboration history to
  INTRA, and the T4.4 Consensus Agent extension. The `Task`-based response
  shape (rather than a bare `Message`) is chosen so a future Consensus Agent
  can extend it with `input-required` rounds without changing this contract.

## Open items for WP3/WP1

- Confirm reusing the Supervision Agent's `Evaluation` type shape for the
  `decision` artifact (rather than inventing a new one) is acceptable, so
  WP3's parsing code stays uniform across agent types.
- Policy upload over AISP is not yet defined; for now the policy must already
  be loaded on the engine side.
