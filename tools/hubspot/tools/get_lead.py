from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from hubspot_client import HubSpotClient, HubSpotError


class GetLeadTool(Tool):
    """Get a lead from HubSpot by id."""

    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        token = self.runtime.credentials.get("access_token")
        if not token:
            yield self.create_text_message("HubSpot access token is required.")
            return

        lead_id = tool_parameters.get("lead_id")
        if not lead_id:
            yield self.create_text_message("'lead_id' is required.")
            return

        properties = tool_parameters.get("properties")
        prop_list = [p.strip() for p in properties.split(",") if p.strip()] if properties else None

        try:
            result = HubSpotClient(token).get("leads", lead_id, properties=prop_list)
        except HubSpotError as e:
            yield self.create_text_message(f"HubSpot error: {e.message}")
            return

        yield self.create_text_message(f"Lead retrieved (id: {result.get('id')}).")
        yield self.create_json_message(result)
