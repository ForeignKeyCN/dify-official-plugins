from typing import Generator, Union
import requests
from dify_plugin.entities.tool import ToolInvokeMessage
from dify_plugin import Tool


class AddCommentToCardTool(Tool):
    """
    Tool for adding a comment to a Trello card.
    """

    def _invoke(
        self, tool_parameters: dict[str, Union[str, int, bool, None]]
    ) -> Generator[ToolInvokeMessage, None, None]:
        """
        Invoke the tool to add a comment to a Trello card.

        Args:
            tool_parameters (dict[str, Union[str, int, bool, None]]): The parameters for the tool invocation,
             including the card ID and comment text.

        Returns:
            ToolInvokeMessage: The result of the tool invocation.
        """
        api_key = self.runtime.credentials.get("trello_api_key")
        token = self.runtime.credentials.get("trello_api_token")
        card_id = tool_parameters.get("id")
        text = tool_parameters.get("text")
        if not (api_key and token and card_id and text):
            yield self.create_text_message(
                "Missing required parameters: API key, token, card ID, or comment text."
            )
            return
        url = f"https://api.trello.com/1/cards/{card_id}/actions/comments"
        params = {"text": text, "key": api_key, "token": token}
        try:
            response = requests.post(url, params=params)
            response.raise_for_status()
        except requests.exceptions.RequestException:
            yield self.create_text_message("Failed to add comment to card")
            return
        yield self.create_text_message(
            text=f"Comment added successfully to card with ID {card_id}."
        )
