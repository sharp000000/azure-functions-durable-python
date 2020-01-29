import json
from ..models.history import HistoryEventType


def should_suspend(partial_result) -> bool:
    """Check the state of the result to determine if the orchestration should suspend."""
    return bool(partial_result is not None
                and hasattr(partial_result, "is_completed")
                and not partial_result.is_completed)


def parse_history_event(directive_result):
    """Based on the type of event, parse the JSON.serializable portion of the event."""
    event_type = directive_result.event_type
    if event_type is None:
        raise ValueError("EventType is not found in task object")

    if event_type == HistoryEventType.EVENT_RAISED:
        return json.loads(directive_result.Input)
    if event_type == HistoryEventType.SUB_ORCHESTRATION_INSTANCE_CREATED:
        return json.loads(directive_result.Result)
    if event_type == HistoryEventType.TASK_COMPLETED:
        return json.loads(directive_result.Result)
    return None


def find_task_scheduled(state, name):
    """Locate the Scheduled Task.

    Within the state passed, search for an event that has hasn't been processed
    and has the the name provided.
    """
    if not name:
        raise ValueError("Name cannot be empty")

    tasks = list(
        filter(lambda e:
               e.event_type == HistoryEventType.TASK_SCHEDULED and e.Name == name
               and not e.is_processed,
               state))

    if len(tasks) == 0:
        return None

    return tasks[0]


def find_task_completed(state, scheduled_task):
    """Locate the Completed Task.

    Within the state passed, search for an event that has hasn't been processed,
    is a completed task type,
    and has the a scheduled id that equals the EventId of the provided scheduled task.
    """
    if scheduled_task is None:
        return None

    tasks = list(
        filter(lambda e:
               (e.event_type == HistoryEventType.TASK_COMPLETED)
               and (e.TaskScheduledId == scheduled_task.event_id),
               state))

    if len(tasks) == 0:
        return None

    return tasks[0]


def find_task_failed(state, scheduled_task):
    """Locate the Failed Task.

    Within the state passed, search for an event that has hasn't been processed,
    is a failed task type,
    and has the a scheduled id that equals the EventId of the provided scheduled task.
    """
    if scheduled_task is None:
        return None

    tasks = list(
        filter(lambda e:
               e.event_type == HistoryEventType.TASK_FAILED
               and e.TaskScheduledId == scheduled_task.event_id, state))

    if len(tasks) == 0:
        return None

    return tasks[0]


def find_task_retry_timer_created(state, failed_task):
    """Locate the Timer Created Task.

    Within the state passed, search for an event that has hasn't been processed,
    is a timer created task type,
    and has the an event id that is one higher then Scheduled Id of the provided
    failed task provided.
    """
    if failed_task is None:
        return None

    tasks = list(
        filter(lambda e:
               e.event_type == HistoryEventType.TIMER_CREATED
               and e.event_id == failed_task.TaskScheduledId + 1,
               state))

    if len(tasks) == 0:
        return None

    return tasks[0]


def find_task_retry_timer_fired(state, retry_timer_created):
    """Locate the Timer Fired Task.

    Within the state passed, search for an event that has hasn't been processed,
    is a timer fired task type,
    and has the an timer id that is equal to the EventId of the provided
    timer created task provided.
    """
    if retry_timer_created is None:
        return None

    tasks = list(
        filter(lambda e: e.event_type == HistoryEventType.TIMER_FIRED
                         and e.TimerId == retry_timer_created.event_id,
               state))

    if len(tasks) == 0:
        return None

    return tasks[0]


def set_processed(tasks):
    """Set the isProcessed attribute of all of the tasks to true.

    This provides the ability to not look at events that have already been processed within
    searching the history of events.
    """
    for task in tasks:
        if task is not None:
            task.is_processed = True
