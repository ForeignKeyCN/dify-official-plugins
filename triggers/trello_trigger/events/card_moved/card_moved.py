from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from werkzeug import Request

from dify_plugin.entities.trigger import Variables
from dify_plugin.errors.trigger import EventIgnoreError
from dify_plugin.interfaces.trigger import Event


class CardMovedEvent(Event):
    """Fires when a card is moved from one list to another."""

    def _on_event(
        self,
        request: Request,
        parameters: Mapping[str, Any],
        payload: Mapping[str, Any],
    ) -> Variables:
        payload = payload or request.get_json(silent=True) or {}
        if not payload:
            raise ValueError("No payload received")
        data = (payload.get("action") or {}).get("data") or {}
        if not (data.get("listBefore") and data.get("listAfter")):
            raise EventIgnoreError()
        return Variables(variables={**payload})
