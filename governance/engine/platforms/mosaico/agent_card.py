"""Builds the AgentCard for the Governance Decision Engine, per the AISP
contract in docs/aisp-interface.md and the packaging conventions in
mosaico-demonstrator/docs/agent-requirements.md.
"""

from a2a.types import AgentCapabilities, AgentCard, AgentExtension, AgentInterface, AgentSkill

OBSERVABILITY_EXTENSION_URI = 'https://mosaico-project.eu/extensions/mosaico-observability'


def build_agent_card(agent_card_url: str) -> AgentCard:
    skill = AgentSkill(
        id='evaluate-collaboration',
        name='Evaluate Collaboration',
        description=(
            'Applies the loaded governance policy to a collaboration (e.g. a pull request) given '
            'the votes/opinions already collected from Supervision Agents, and returns the decision.'
        ),
        input_modes=['application/json'],
        output_modes=['application/json', 'text/plain'],
        tags=['governance', 'decision-engine', 'voting'],
        examples=[],
    )

    return AgentCard(
        name='MOSAICO Governance Decision Engine',
        description=(
            'Collects Supervision Agents\' votes/opinions for a collaboration and, according to the '
            'loaded governance policy (govdsl), outputs the final decision and its rationale.'
        ),
        version='0.1.0',
        default_input_modes=['application/json'],
        default_output_modes=['application/json', 'text/plain'],
        capabilities=AgentCapabilities(
            streaming=False,
            extended_agent_card=False,
            extensions=[
                AgentExtension(
                    uri=OBSERVABILITY_EXTENSION_URI,
                    description='Links traces of hierarchically decomposed tasks across MOSAICO agents.',
                    required=False,
                ),
            ],
        ),
        supported_interfaces=[
            AgentInterface(protocol_binding='JSONRPC', url=agent_card_url, protocol_version='1.0'),
        ],
        skills=[skill],
    )
