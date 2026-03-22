from agents.models.models import SharedAgentState


class InMemoryStateService:
    """
    Simple in-memory state store for each chat session.

    This lets your orchestrator and agents share data across steps.
    """

    def __init__(self) -> None:
        self._store: dict[str, SharedAgentState] = {}

    def set_state(self, chat_session_id: str, state: SharedAgentState) -> None:
        """Save or update state"""
        self._store[chat_session_id] = state

    def get_state(self, chat_session_id: str) -> SharedAgentState | None:
        """Retrieve state"""
        return self._store.get(chat_session_id)

    def delete_state(self, chat_session_id: str) -> None:
        """Delete a session"""
        if chat_session_id in self._store:
            del self._store[chat_session_id]

state_service = InMemoryStateService()