"""In-process tests for tools/list_events.py.

``requests.get`` is patched, so no network and no real token are needed.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest
import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT))

from tools.list_events import ListEventsTool  # noqa: E402


class _Response:
    def __init__(self, status_code: int = 200, payload: dict | None = None) -> None:
        self.status_code = status_code
        self._payload = payload if payload is not None else {"value": []}
        self.text = "error"

    def json(self) -> dict:
        return self._payload


def _tool() -> ListEventsTool:
    tool = ListEventsTool.__new__(ListEventsTool)
    tool.runtime = SimpleNamespace(credentials={"access_token": "token"})
    tool.create_text_message = lambda text: ("text", text)
    tool.create_json_message = lambda data: ("json", data)
    return tool


def _invoke(params: dict, response: _Response | None = None):
    with mock.patch("tools.list_events.requests.get", return_value=response or _Response()) as get:
        messages = list(_tool()._invoke(params))
    return messages, get


def test_limit_is_sent_as_top_with_fixed_descending_order():
    _, get = _invoke({"limit": 7})
    params = get.call_args.kwargs["params"]
    assert params["$top"] == 7
    assert params["$orderby"] == "start/dateTime desc"


def test_default_limit_is_ten():
    _, get = _invoke({})
    assert get.call_args.kwargs["params"]["$top"] == 10


def test_legacy_top_parameter_still_works():
    _, get = _invoke({"top": 25})
    assert get.call_args.kwargs["params"]["$top"] == 25


@pytest.mark.parametrize("limit", [0, 101, "abc"])
def test_out_of_range_limit_is_rejected_before_calling_graph(limit):
    messages, get = _invoke({"limit": limit})
    assert not get.called
    assert messages[0][0] == "text"
    assert "Limit must be" in messages[0][1]


def test_calendar_id_selects_calendar_endpoint():
    _, get = _invoke({"calendar_id": "abc"})
    assert get.call_args.args[0] == "https://graph.microsoft.com/v1.0/me/calendars/abc/events"


def test_yaml_declares_limit_and_not_the_old_parameters():
    spec = yaml.safe_load((PLUGIN_ROOT / "tools" / "list_events.yaml").read_text(encoding="utf-8"))
    names = [p["name"] for p in spec["parameters"]]
    assert names == ["limit", "calendar_id"]
    limit = spec["parameters"][0]
    assert limit["type"] == "number" and limit["default"] == 10 and limit["min"] == 1 and limit["max"] == 100
    for key in ("label", "human_description"):
        for locale in ("en_US", "zh_Hans", "ja_JP", "ko_KR", "pt_BR"):
            assert limit[key].get(locale), f"{key}.{locale} missing"
