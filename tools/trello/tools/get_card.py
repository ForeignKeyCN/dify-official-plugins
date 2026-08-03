from typing import Generator, Union
import requests
from dify_plugin.entities.tool import ToolInvokeMessage
from dify_plugin import Tool


class GetCardTool(Tool):
    """
    Tool for retrieving a Trello card by its ID.
    """

    def _invoke(
        self, tool_parameters: dict[str, Union[str, int, bool, None]]
    ) -> Generator[ToolInvokeMessage, None, None]:
        """
        Invoke the tool to retrieve a Trello card by its ID.

        Args:
            tool_parameters (dict[str, Union[str, int, bool, None]]): The parameters for the tool invocation,
             including the card ID.

        Returns:
            ToolInvokeMessage: The result of the tool invocation.
        """
        api_key = self.runtime.credentials.get("trello_api_key")
        token = self.runtime.credentials.get("trello_api_token")
        card_id = tool_parameters.get("id")
        if not (api_key and token and card_id):
            yield self.create_text_message(
                "Missing required parameters: API key, token, or card ID."
            )
            return
        url = f"https://api.trello.com/1/cards/{card_id}"
        params = {"key": api_key, "token": token}
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            card = response.json()
        except requests.exceptions.RequestException:
            yield self.create_text_message("Failed to retrieve card")
            return
        yield self.create_text_message(
            text=f"Card '{card.get('name')}' (ID: {card.get('id')}) retrieved successfully."
        )
        yield self.create_json_message(card)
