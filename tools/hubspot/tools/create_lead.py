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

        # A lead should be associated with a contact and/or company.
        linked = []
        contact_id = (tool_parameters.get("associated_contact_id") or "").strip()
        company_id = (tool_parameters.get("associated_company_id") or "").strip()
        try:
            if contact_id:
                client.associate_default("leads", lead_id, "contacts", contact_id)
                linked.append(f"contact {contact_id}")
            if company_id:
                client.associate_default("leads", lead_id, "companies", company_id)
                linked.append(f"company {company_id}")
        except HubSpotError as e:
            yield self.create_text_message(
                f"Lead created (id: {lead_id}) but association failed: {e.message}"
            )
            yield self.create_json_message(result)
            return

        suffix = f", linked to {', '.join(linked)}" if linked else ""
        yield self.create_text_message(f"Lead created (id: {lead_id}){suffix}.")
        yield self.create_json_message(result)
