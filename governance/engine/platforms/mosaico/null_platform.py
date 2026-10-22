"""No-op stand-in for ``collab._platform`` on AISP-originated collaborations.

``governance/engine/semantics/actions.py`` (``merge_PR``/``close_PR``/``close_issue``)
calls ``.put(...)``/``.patch(...)`` on the collaboration's platform to apply a
decision (e.g. merging a GitHub PR). An AISP-originated collaboration has no
such hosting-platform side effect to apply here: per the AISP contract
(docs/aisp-interface.md), it is the Collaboration Agent's job to act on the
``decision`` artifact the engine returns. This stub just absorbs those calls
so the existing decide/close logic in state_bodies.py doesn't need special
casing for the AISP origin.
"""


class NullPlatform:
    def put(self, url, data=None):
        pass

    def patch(self, url, data=None):
        pass

    def getitem(self, url):
        return {}
