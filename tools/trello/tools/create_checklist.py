from typing import Generator, Union
import requests
from dify_plugin.entities.tool import ToolInvokeMessage
from dify_plugin import Tool


class CreateChecklistTool(Tool):
    """
    Tool for creating a checklist on a Trello card.
    """

    def _invoke(
        self, tool_parameters: dict[str, Union[str, int, bool, None]]
    ) -> Generator[ToolInvokeMessage, None, None]:
        """
        Invoke the tool to create a checklist on a Trello card.

        Args:
            tool_parameters (dict[str, Union[str, int, bool, None]]): The parameters for the tool invocation,
             including the card ID and checklist name.

        Returns:
            ToolInvokeMessage: The result of the tool invocation.
        """
        api_key = self.runtime.credentials.get("trello_api_key")
        token = self.runtime.credentials.get("trello_api_token")
        card_id = tool_parameters.get("id")
        name = tool_parameters.get("name")
        if not (api_key and token and card_id and name):
            yield self.create_text_message(
                "Missing required parameters: API key, token, card ID, or checklist name."
            )
            return
        url = f"https://api.trello.com/1/cards/{card_id}/checklists"
        params = {"name": name, "key": api_key, "token": token}
        try:
            response = requests.post(url, params=params)
            response.raise_for_status()
            checklist = response.json()
        except requests.exceptions.RequestException:
            yield self.create_text_message("Failed to create checklist")
            return
        yield self.create_text_message(
            text=f"Checklist '{checklist.get('name')}' created successfully with ID {checklist.get('id')}."
        )
