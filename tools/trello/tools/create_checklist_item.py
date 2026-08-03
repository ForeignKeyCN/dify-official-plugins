from typing import Generator, Union
import requests
from dify_plugin.entities.tool import ToolInvokeMessage
from dify_plugin import Tool


class CreateChecklistItemTool(Tool):
    """
    Tool for creating an item within a Trello checklist.
    """

    def _invoke(
        self, tool_parameters: dict[str, Union[str, int, bool, None]]
    ) -> Generator[ToolInvokeMessage, None, None]:
        """
        Invoke the tool to create an item within a Trello checklist.

        Args:
            tool_parameters (dict[str, Union[str, int, bool, None]]): The parameters for the tool invocation,
             including the checklist ID, item name, and optional checked and position values.

        Returns:
            ToolInvokeMessage: The result of the tool invocation.
        """
        api_key = self.runtime.credentials.get("trello_api_key")
        token = self.runtime.credentials.get("trello_api_token")
        checklist_id = tool_parameters.get("id")
        name = tool_parameters.get("name")
        if not (api_key and token and checklist_id and name):
            yield self.create_text_message(
                "Missing required parameters: API key, token, checklist ID, or item name."
            )
            return
        url = f"https://api.trello.com/1/checklists/{checklist_id}/checkItems"
        params = {"name": name, "key": api_key, "token": token}
        checked = tool_parameters.get("checked")
        if checked is not None:
            params["checked"] = checked
        pos = tool_parameters.get("pos")
        if pos:
            params["pos"] = pos
        try:
            response = requests.post(url, params=params)
            response.raise_for_status()
            item = response.json()
        except requests.exceptions.RequestException:
            yield self.create_text_message("Failed to create checklist item")
            return
        yield self.create_text_message(
            text=f"Checklist item '{item.get('name')}' created successfully with ID {item.get('id')}."
        )
