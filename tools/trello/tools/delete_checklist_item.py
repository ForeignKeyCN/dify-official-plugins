from typing import Generator, Union
import requests
from dify_plugin.entities.tool import ToolInvokeMessage
from dify_plugin import Tool


class DeleteChecklistItemTool(Tool):
    """
    Tool for deleting an item from a Trello checklist.
    """

    def _invoke(
        self, tool_parameters: dict[str, Union[str, int, bool, None]]
    ) -> Generator[ToolInvokeMessage, None, None]:
        """
        Invoke the tool to delete an item from a Trello checklist.

        Args:
            tool_parameters (dict[str, Union[str, int, bool, None]]): The parameters for the tool invocation,
             including the checklist ID and check item ID.

        Returns:
            ToolInvokeMessage: The result of the tool invocation.
        """
        api_key = self.runtime.credentials.get("trello_api_key")
        token = self.runtime.credentials.get("trello_api_token")
        checklist_id = tool_parameters.get("idChecklist")
        check_item_id = tool_parameters.get("idCheckItem")
        if not (api_key and token and checklist_id and check_item_id):
            yield self.create_text_message(
                "Missing required parameters: API key, token, checklist ID, or check item ID."
            )
            return
        url = f"https://api.trello.com/1/checklists/{checklist_id}/checkItems/{check_item_id}"
        params = {"key": api_key, "token": token}
        try:
            response = requests.delete(url, params=params)
            response.raise_for_status()
        except requests.exceptions.RequestException:
            yield self.create_text_message("Failed to delete checklist item")
            return
        yield self.create_text_message(
            text=f"Checklist item with ID {check_item_id} has been successfully deleted."
        )
