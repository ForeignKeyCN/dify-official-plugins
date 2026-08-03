from typing import Generator, Union
import requests
from dify_plugin.entities.tool import ToolInvokeMessage
from dify_plugin import Tool


class AddAttachmentToCardTool(Tool):
    """
    Tool for adding an attachment to a Trello card.
    """

    def _invoke(
        self, tool_parameters: dict[str, Union[str, int, bool, None]]
    ) -> Generator[ToolInvokeMessage, None, None]:
        """
        Invoke the tool to add an attachment to a Trello card.

        Args:
            tool_parameters (dict[str, Union[str, int, bool, None]]): The parameters for the tool invocation,
             including the card ID, attachment URL, and optional name.

        Returns:
            ToolInvokeMessage: The result of the tool invocation.
        """
        api_key = self.runtime.credentials.get("trello_api_key")
        token = self.runtime.credentials.get("trello_api_token")
        card_id = tool_parameters.get("id")
        url_param = tool_parameters.get("url")
        if not (api_key and token and card_id and url_param):
            yield self.create_text_message(
                "Missing required parameters: API key, token, card ID, or attachment URL."
            )
            return
        url = f"https://api.trello.com/1/cards/{card_id}/attachments"
        params = {"url": url_param, "key": api_key, "token": token}
        name = tool_parameters.get("name")
        if name:
            params["name"] = name
        try:
            response = requests.post(url, params=params)
            response.raise_for_status()
        except requests.exceptions.RequestException:
            yield self.create_text_message("Failed to add attachment to card")
            return
        yield self.create_text_message(
            text=f"Attachment added successfully to card with ID {card_id}."
        )
