"""
Store class for Redux-like state management.

The Store manages application state, dispatches actions, and notifies subscribers.
"""

from typing import Any, Callable, Dict, List

from .state import AppState
from .reducers import reducer


class Store:
    """Simple Redux-like store for state management."""

    def __init__(self, initial_state: AppState = None):
        self._state = initial_state or AppState()
        self._listeners: List[Callable] = []

    def get_state(self) -> AppState:
        """Get current state (read-only)."""
        return self._state

    def dispatch(self, action: Dict[str, Any]) -> None:
        """Dispatch an action to update state."""
        self._state = reducer(self._state, action)
        self._notify_listeners()

    def subscribe(self, listener: Callable) -> Callable:
        """Subscribe to state changes. Returns unsubscribe function."""
        self._listeners.append(listener)
        return lambda: self._listeners.remove(listener)

    def _notify_listeners(self) -> None:
        """Notify all listeners of state change."""
        for listener in self._listeners:
            listener()
