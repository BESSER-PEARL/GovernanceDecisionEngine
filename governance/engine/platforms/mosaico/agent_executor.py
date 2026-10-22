"""AgentExecutor for the `evaluate-collaboration` AISP skill.

See docs/aisp-interface.md for the request/response contract this implements.
"""

import asyncio
from concurrent.futures import TimeoutError as FutureTimeoutError

from a2a.helpers import get_data_parts, new_data_part, new_task_from_user_message, new_text_message, new_text_part
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import TaskState

from baf.exceptions.logger import logger

from governance.engine.platforms.mosaico import correlation
from governance.engine.platforms.mosaico.mapping import (
    EvaluateCollaborationRequest,
    decision_explanation,
    decision_result,
)

DECISION_TIMEOUT_SECONDS = 15

# asyncio.run_in_executor converts a worker's concurrent.futures.TimeoutError into
# asyncio.TimeoutError when it propagates back to the awaiting coroutine (see
# asyncio.futures._convert_future_exc), and the two are distinct classes before
# Python 3.11 -- catch both so the timeout path below actually triggers.
_TIMEOUT_ERRORS = (FutureTimeoutError, asyncio.TimeoutError)


class GovernanceAgentExecutor(AgentExecutor):
    """Bridges AISP `evaluate-collaboration` requests into the engine's FSM.

    Args:
        platform: the owning MOSAICOPlatform, used to fire engine events and
            await the resulting Decision (see platforms/mosaico/mosaico_platform.py).
    """

    def __init__(self, platform) -> None:
        self._platform = platform

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        task = context.current_task or new_task_from_user_message(context.message)
        if context.current_task is None:
            await event_queue.enqueue_event(task)

        task_updater = TaskUpdater(event_queue=event_queue, task_id=task.id, context_id=task.context_id)
        await task_updater.update_status(
            state=TaskState.TASK_STATE_WORKING,
            message=new_text_message('Evaluating collaboration...'),
        )

        data_parts = get_data_parts(context.message.parts)
        if not data_parts:
            await task_updater.failed(new_text_message('No data part found in the request message.'))
            return

        try:
            request = EvaluateCollaborationRequest.from_dict(data_parts[0])
        except (KeyError, TypeError) as exc:
            await task_updater.failed(new_text_message(f'Malformed evaluate-collaboration request: {exc}'))
            return

        try:
            pending = self._platform.evaluate_collaboration(request)
            decision = await asyncio.get_running_loop().run_in_executor(
                None, pending.result, DECISION_TIMEOUT_SECONDS
            )
        except _TIMEOUT_ERRORS:
            correlation.cancel(request.collaboration_id)
            logger.warning(f"AISP evaluate-collaboration timed out for collaboration '{request.collaboration_id}'")
            await task_updater.failed(new_text_message(
                'No decision could be reached: the policy could not be resolved or conditions were not met '
                '(e.g. missing required participants) within the expected time.'
            ))
            return
        except Exception as exc:  # noqa: BLE001 - surface any engine-side error to the caller
            correlation.cancel(request.collaboration_id)
            logger.exception('AISP evaluate-collaboration failed')
            await task_updater.failed(new_text_message(f'Decision engine error: {exc}'))
            return

        await task_updater.add_artifact(parts=[new_data_part(decision_result(decision))], name='decision')
        await task_updater.add_artifact(parts=[new_text_part(decision_explanation(decision))], name='explanation')
        await task_updater.complete(new_text_message('Decision reached.'))

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError('Cancel is not supported: decisions are rule-based and complete quickly.')
