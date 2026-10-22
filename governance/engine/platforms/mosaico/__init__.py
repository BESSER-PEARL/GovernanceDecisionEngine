"""Agent properties for the MOSAICOPlatform, following the same convention as
``baf.platforms.github``/``baf.platforms.gitlab``.
"""

from baf.core.property import Property

MOSAICO_HOST = Property('platforms.mosaico.host', str, '0.0.0.0')
"""Host the AISP/A2A server should bind to.

name: ``platforms.mosaico.host``

type: ``str``

default value: ``0.0.0.0``
"""

MOSAICO_PORT = Property('platforms.mosaico.port', int, 8910)
"""Port the AISP/A2A server should listen on.

name: ``platforms.mosaico.port``

type: ``int``

default value: ``8910``
"""

MOSAICO_AGENT_CARD_URL = Property('platforms.mosaico.agent_card_url', str, None)
"""URL advertised in the agent card's endpoint, e.g. ``http://governance-engine:8910``.

If unset, falls back to ``http://<host>:<port>`` (with ``host`` resolved to ``localhost``
when bound to ``0.0.0.0``), per the MOSAICO packaging conventions in
``mosaico-demonstrator/docs/agent-requirements.md``.

name: ``platforms.mosaico.agent_card_url``

type: ``str``

default value: ``None``
"""
