# notion/client.py
import os
import requests
from dotenv import load_dotenv

class NotionClient:
    """
    A lightweight client for interacting with the Notion API.

    This class handles:
    - Loading credentials from environment variables
    - Managing authentication headers
    - Sending POST requests to create new pages in a Notion database
    """

    def __init__(self):
        """
        Initialize the Notion client by loading environment variables
        and setting up authentication headers.
        """
        load_dotenv()

        # Private credentials (should not be accessed outside this class)
        self.__token = os.getenv("NOTION_TK")
        self.__database_id = os.getenv("NOTION_DB_ID")

        # Notion API version
        self.notion_version = "2022-06-28"

        # HTTP headers required by Notion API
        self.__headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.__token}",
            "Notion-Version": self.notion_version,
        }

        # Base URL for creating pages in Notion
        self.url = "https://api.notion.com/v1/pages"
        
    @property
    def database_id(self) -> str:
        """Return the Notion database ID."""
        return self.__database_id

    def post(self, data: dict) -> requests.Response:
        """
        Send a POST request to the Notion API.

        Args:
            data (dict): Structured JSON payload representing the Notion page.

        Returns:
            requests.Response: The HTTP response object from Notion.
        """
        return requests.post(self.url, headers=self.__headers, json=data)
