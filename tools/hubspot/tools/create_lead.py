from collections.abc import Generator
from typing import Any
import json

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from hubspot_client import HubSpotClient, HubSpotError


class CreateLeadTool(Tool):
    """Create a lead in HubSpot, optionally linked to a contact or company."""

    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        token = self.runtime.credentials.get("access_token")
        if not token:
            yield self.create_text_message("HubSpot access token is required.")
            return

        properties: dict[str, Any] = {}
        name = tool_parameters.get("lead_name")
        if name:
            properties["hs_lead_name"] = name

        extra = tool_parameters.get("properties")
        if extra:
            try:
                properties.update(json.loads(extra) if isinstance(extra, str) else extra)
            except Exception:
                yield self.create_text_message("'properties' must be a valid JSON object.")
                return

        if not properties:
            yield self.create_text_message("Provide at least a lead name or a property.")
            return

        client = HubSpotClient(token)
        try:
            result = client.create("leads", properties)
        except HubSpotError as e:
            yield self.create_text_message(f"HubSpot error: {e.message}")
            return

        lead_id = result.get("id")
        if not lead_id:
            # Creation succeeded (no HubSpotError) but we can't associate without an id.
            yield self.create_text_message(
                "Lead created, but HubSpot returned no id so associations were skipped."
            )
            yield self.create_json_message(result)
            return

        # A lead should be associated with a contact and/or company. Each link is
        # attempted independently so one failure never hides the other's outcome.
        # The lead already exists at this point, so we never re-create it - we just
        # report which links succeeded and which failed, with HubSpot's reason.
        linked: list[str] = []
        failed: list[str] = []
        targets = [
            ("contacts", (tool_parameters.get("associated_contact_id") or "").strip(), "contact"),
            ("companies", (tool_parameters.get("associated_company_id") or "").strip(), "company"),
        ]
        for to_obj, to_id, noun in targets:
            if not to_id:
                continue
            try:
                client.associate_default("leads", lead_id, to_obj, to_id)
                linked.append(f"{noun} {to_id}")
            except HubSpotError as e:
                failed.append(f"{noun} {to_id} ({e.message})")

        parts = [f"Lead created (id: {lead_id})"]
        if linked:
            parts.append(f"linked to {', '.join(linked)}")
        if failed:
            parts.append(f"but failed to link {', '.join(failed)} - link it manually or retry the association")
        yield self.create_text_message(". ".join(parts) + ".")
        yield self.create_json_message(result)
