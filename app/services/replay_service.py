
"""
MANTIQ historical replay controller.

Replay is based on the NASA IMS dataset.
It is not a live sensor feed.
"""

import streamlit as st

from app.services import condition_service as cs
from app.services.alert_monitor import process_replay_transitions

KEY_INDEX = "replay_index"
KEY_STATUS = "replay_status"
KEY_SPEED = "replay_speed"

STATUS_IDLE = "idle"
STATUS_RUNNING = "running"
STATUS_PAUSED = "paused"
STATUS_FINISHED = "finished"

_LABELS = {
    STATUS_IDLE: "Not started",
    STATUS_RUNNING: "Running",
    STATUS_PAUSED: "Paused",
    STATUS_FINISHED: "Finished",
}


def status() -> str:
    return st.session_state.get(KEY_STATUS, STATUS_IDLE)


def status_label() -> str:
    return _LABELS.get(status(), "Not started")


def is_replaying() -> bool:
    return status() != STATUS_IDLE


def position():
    return st.session_state.get(KEY_INDEX)


def speed() -> int:
    return int(st.session_state.get(KEY_SPEED, 1))


def set_speed(value: int) -> None:
    st.session_state[KEY_SPEED] = max(1, min(int(value), 20))


def view_index(pipeline) -> int:
    last = len(pipeline.conditions) - 1
    index = position()

    if index is None:
        return last

    return max(0, min(int(index), last))


def start(pipeline) -> None:
    """Start replay from the first historical recording."""
    if len(pipeline.conditions) == 0:
        return

    st.session_state[KEY_INDEX] = 0
    st.session_state[KEY_STATUS] = STATUS_RUNNING


def pause() -> None:
    if status() == STATUS_RUNNING:
        st.session_state[KEY_STATUS] = STATUS_PAUSED


def resume() -> None:
    if status() == STATUS_PAUSED:
        st.session_state[KEY_STATUS] = STATUS_RUNNING


def reset() -> None:
    """Return to the initial state without deleting saved alerts."""
    st.session_state[KEY_INDEX] = None
    st.session_state[KEY_STATUS] = STATUS_IDLE


def advance(pipeline, steps: int = 1) -> int:
    """
    Advance historical recordings and process each transition once.

    Alert deduplication is enforced by the database service.
    """
    total = len(pipeline.conditions)

    if total == 0:
        return 0

    if status() != STATUS_RUNNING:
        return view_index(pipeline)

    current = position()

    if current is None:
        current = 0

    for _ in range(max(1, int(steps))):
        if current >= total - 1:
            st.session_state[KEY_STATUS] = STATUS_FINISHED
            break

        previous_index = current
        current += 1

        transitions = cs.transitions_between(
            pipeline.conditions,
            previous_index,
            current,
        )

        if transitions is not None and not transitions.empty:
            process_replay_transitions(
                transitions=transitions,
                scored=pipeline.scored,
            )

        st.session_state[KEY_INDEX] = current

    if current >= total - 1:
        st.session_state[KEY_STATUS] = STATUS_FINISHED

    return current
