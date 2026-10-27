"""MOSAICOPlatform: the AISP/A2A-compliant BAF Platform for the Governance
Decision Engine.

Unlike baf.platforms.a2a.A2APlatform (a bespoke, non-A2A-spec JSON-RPC/task
scheme shipped with BAF), this platform wraps the official `a2a-sdk` so the
engine is wire-compatible with the rest of MOSAICO's agents (which all speak
real A2A v1.0.0). See docs/aisp-interface.md for the contract.
"""

from __future__ import annotations

from concurrent.futures import Future
from typing import TYPE_CHECKING

import uvicorn
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes
from a2a.server.tasks import InMemoryTaskStore
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route

from baf.exceptions.logger import logger
from baf.platforms.platform import Platform

from governance.engine.platforms.mosaico import MOSAICO_AGENT_CARD_URL, MOSAICO_HOST, MOSAICO_PORT
from governance.engine.platforms.mosaico import correlation
from governance.engine.platforms.mosaico.agent_card import build_agent_card
from governance.engine.platforms.mosaico.agent_executor import GovernanceAgentExecutor
from governance.engine.events import AISPEvaluateEvent
from governance.engine.platforms.mosaico.mapping import EvaluateCollaborationRequest

if TYPE_CHECKING:
    from baf.core.agent import Agent
    from baf.core.session import Session
    from baf.platforms.payload import Payload


class MOSAICOPlatform(Platform):
    """Exposes the engine as a genuine A2A v1.0.0 agent (the `evaluate-collaboration`
    skill), bridging requests into the existing FSM via `agent.receive_event(...)`,
    exactly as GitHubPlatform/gh_webhooks_bodybuilder does for webhooks.
    """

    def __init__(self, agent: 'Agent'):
        super().__init__()
        self._agent: 'Agent' = agent
        self._host: str = agent.get_property(MOSAICO_HOST)
        self._port: int = agent.get_property(MOSAICO_PORT)

        agent_card_url = agent.get_property(MOSAICO_AGENT_CARD_URL)
        if agent_card_url is None:
            display_host = 'localhost' if self._host == '0.0.0.0' else self._host
            agent_card_url = f'http://{display_host}:{self._port}'

        self.agent_card = build_agent_card(agent_card_url)
        self._executor = GovernanceAgentExecutor(self)
        self._request_handler = DefaultRequestHandler(
            agent_executor=self._executor,
            task_store=InMemoryTaskStore(),
            agent_card=self.agent_card,
        )
        self._server: uvicorn.Server | None = None

    def _build_app(self) -> Starlette:
        async def health(request):
            return PlainTextResponse('OK', status_code=200)

        routes = [Route('/health', health, methods=['GET'])]
        routes.extend(create_agent_card_routes(self.agent_card))
        routes.extend(create_jsonrpc_routes(self._request_handler, '/'))
        return Starlette(routes=routes)

    def initialize(self) -> None:
        self._app = self._build_app()

    def start(self) -> None:
        logger.info(f"{self._agent.name}'s MOSAICOPlatform starting on {self._host}:{self._port}")
        self.running = True
        config = uvicorn.Config(self._app, host=self._host, port=self._port, log_level='info')
        self._server = uvicorn.Server(config)
        self._server.run()

    def stop(self) -> None:
        self.running = False
        if self._server is not None:
            self._server.should_exit = True
        logger.info(f"{self._agent.name}'s MOSAICOPlatform stopped")

    def _send(self, session_id: str, payload: 'Payload') -> None:
        # All output for this platform goes through A2A Task artifacts
        # (see agent_executor.py), not through BAF's generic reply mechanism.
        logger.warning('MOSAICOPlatform._send is not used; responses are sent as A2A artifacts.')

    def reply(self, session: 'Session', message: str) -> None:
        logger.warning('MOSAICOPlatform.reply is not used; responses are sent as A2A artifacts.')

    def evaluate_collaboration(self, request: EvaluateCollaborationRequest) -> Future:
        """Fires a single AISPEvaluateEvent carrying the whole request (see
        events.AISPEvaluateEvent for why this is one atomic event rather than
        a proposal followed by separate per-participant vote events), and
        returns a Future resolved with the resulting Decision once the
        engine's existing vote-decidability logic (Collaboration.vote /
        decide_bodybuilder) reaches one -- see correlation.py.
        """
        logger.info(f"MOSAICOPlatform: firing AISPEvaluateEvent for collaboration '{request.collaboration_id}'")
        future = correlation.register(request.collaboration_id)
        self._agent.receive_event(AISPEvaluateEvent(request))
        return future
