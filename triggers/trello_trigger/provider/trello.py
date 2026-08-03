from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import requests
from werkzeug import Request, Response

from dify_plugin.entities import I18nObject, ParameterOption
from dify_plugin.entities.provider_config import CredentialType
from dify_plugin.entities.trigger import EventDispatch, Subscription, UnsubscribeResult
from dify_plugin.errors.trigger import SubscriptionError
from dify_plugin.interfaces.trigger import Trigger, TriggerSubscriptionConstructor

TRELLO_API = "https://api.trello.com/1"

# Maps a Trello action.type to the Event name(s) that should be invoked.
# A single Trello action can fan out to multiple Events; each Event applies its
# own filtering in `_on_event` (e.g. card_moved ignores non-move updates).
ACTION_EVENT_MAP: dict[str, list[str]] = {
    "createCard": ["card_created"],
    "updateCard": ["card_updated", "card_moved"],
    "deleteCard": ["card_deleted"],
    "commentCard": ["comment_added"],
    "addAttachmentToCard": ["attachment_added"],
    "createCheckItem": ["checklist_item_created"],
    "updateCheckItemStateOnCard": ["checklist_item_updated"],
}


class TrelloTrigger(Trigger):
    """Receives Trello webhook deliveries and routes them to Events."""

    def _dispatch_event(
        self, subscription: Subscription, request: Request
    ) -> EventDispatch:
        # When a webhook is created, Trello verifies the callback URL with a HEAD
        # request and expects a 200 response.
        if request.method == "HEAD":
            return EventDispatch(events=[], response=Response("", status=200))

        payload = request.get_json(silent=True) or {}
        action = payload.get("action") or {}
        action_type = action.get("type")
        events = ACTION_EVENT_MAP.get(action_type, [])
        user_id = str(action.get("idMemberCreator") or "")

        return EventDispatch(
            user_id=user_id,
            events=events,
            response=Response("OK", status=200),
            payload=payload,
        )


class TrelloSubscriptionConstructor(TriggerSubscriptionConstructor):
    """Manages the lifecycle of Trello webhooks (create/delete/refresh)."""

    @staticmethod
    def _creds(credentials: Mapping[str, Any]) -> tuple[str, str]:
        return (
            str(credentials.get("trello_api_key") or ""),
            str(credentials.get("trello_api_token") or ""),
        )

    def _validate_api_key(self, credentials: Mapping[str, Any]) -> None:
        key, token = self._creds(credentials)
        if not key or not token:
            raise SubscriptionError("Trello API key and token are required.")
        try:
            resp = requests.get(
                f"{TRELLO_API}/members/me",
                params={"key": key, "token": token},
                timeout=10,
            )
        except requests.RequestException as exc:
            raise SubscriptionError(f"Failed to reach Trello: {exc}")
        if resp.status_code == 401:
            raise SubscriptionError("Invalid Trello credentials: unauthorized.")
        if not resp.ok:
            raise SubscriptionError(
                f"Trello credential validation failed: HTTP {resp.status_code}"
            )

    def _create_subscription(
        self,
        endpoint: str,
        parameters: Mapping[str, Any],
        credentials: Mapping[str, Any],
        credential_type: CredentialType,
    ) -> Subscription:
        key, token = self._creds(credentials)
        board_id = parameters.get("board")
        if not board_id:
            raise SubscriptionError("A Trello board must be selected.")
        try:
            resp = requests.post(
                f"{TRELLO_API}/webhooks",
                params={"key": key, "token": token},
                json={
                    "callbackURL": endpoint,
                    "idModel": board_id,
                    "description": "Dify Trello Trigger",
                },
                timeout=10,
            )
        except requests.RequestException as exc:
            raise SubscriptionError(f"Failed to create Trello webhook: {exc}")
        if not resp.ok:
            raise SubscriptionError(
                f"Failed to create Trello webhook: HTTP {resp.status_code} {resp.text[:300]}"
            )
        webhook = resp.json()
        return Subscription(
            expires_at=-1,  # Trello webhooks do not expire.
            endpoint=endpoint,
            parameters=parameters,
            properties={"external_id": str(webhook.get("id")), "board_id": board_id},
        )

    def _delete_subscription(
        self,
        subscription: Subscription,
        credentials: Mapping[str, Any],
        credential_type: CredentialType,
    ) -> UnsubscribeResult:
        key, token = self._creds(credentials)
        external_id = subscription.properties.get("external_id")
        if not external_id:
            return UnsubscribeResult(
                success=True, message="No webhook id stored; nothing to delete."
            )
        try:
            resp = requests.delete(
                f"{TRELLO_API}/webhooks/{external_id}",
                params={"key": key, "token": token},
                timeout=10,
            )
        except requests.RequestException as exc:
            return UnsubscribeResult(
                success=False, message=f"Failed to delete webhook {external_id}: {exc}"
            )
        if resp.ok or resp.status_code == 404:
            return UnsubscribeResult(
                success=True, message=f"Removed Trello webhook {external_id}."
            )
        return UnsubscribeResult(
            success=False,
            message=f"Failed to delete webhook {external_id}: HTTP {resp.status_code}",
        )

    def _refresh_subscription(
        self,
        subscription: Subscription,
        credentials: Mapping[str, Any],
        credential_type: CredentialType,
    ) -> Subscription:
        # Trello webhooks never expire; keep everything as-is.
        return Subscription(
            expires_at=-1,
            endpoint=subscription.endpoint,
            parameters=subscription.parameters,
            properties=subscription.properties,
        )

    def _fetch_parameter_options(
        self,
        parameter: str,
        credentials: Mapping[str, Any],
        credential_type: CredentialType,
    ) -> list[ParameterOption]:
        if parameter != "board":
            return []
        key, token = self._creds(credentials)
        try:
            resp = requests.get(
                f"{TRELLO_API}/members/me/boards",
                params={
                    "key": key,
                    "token": token,
                    "fields": "name,url",
                    "filter": "open",
                },
                timeout=10,
            )
        except requests.RequestException:
            return []
        if not resp.ok:
            return []
        options: list[ParameterOption] = []
        for board in resp.json():
            board_id = board.get("id")
            if not board_id:
                continue
            name = board.get("name") or board_id
            options.append(
                ParameterOption(value=board_id, label=I18nObject(en_us=name))
            )
        return options
