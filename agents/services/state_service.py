from agents.models.models import SharedAgentState


class InMemoryStateService:
    def __init__(self) -> None:
        self._store: dict[str, SharedAgentState] = {}

    def set_state(self, chat_session_id: str, state: SharedAgentState) -> None:
        self._store[chat_session_id] = state

    def get_state(self, chat_session_id: str) -> SharedAgentState | None:
        return self._store.get(chat_session_id)

    def delete_state(self, chat_session_id: str) -> None:
        if chat_session_id in self._store:
            del self._store[chat_session_id]


state_service = InMemoryStateService()
