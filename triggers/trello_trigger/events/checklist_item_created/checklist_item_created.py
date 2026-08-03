from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from werkzeug import Request

from dify_plugin.entities.trigger import Variables
from dify_plugin.interfaces.trigger import Event


class ChecklistItemCreatedEvent(Event):
    """Fires when a checklist item is created on a card."""

    def _on_event(
        self,
        request: Request,
        parameters: Mapping[str, Any],
        payload: Mapping[str, Any],
    ) -> Variables:
        payload = payload or request.get_json(silent=True) or {}
        if not payload:
            raise ValueError("No payload received")
        return Variables(variables={**payload})
