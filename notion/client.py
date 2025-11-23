# notion/client.py

import requests
import os
from dotenv import load_dotenv

class NotionClient:
    def __init__(self):
        load_dotenv()
        self.__token = os.getenv("NOTION_TK")
        self.__datasource_id = os.getenv("NOTION_DATA_SOURCE_ID")
        self.notion_version = "2025-09-03"
        self.__headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.__token}",
            "Notion-Version": self.notion_version,
        }
        self.base_url = "https://api.notion.com/v1"

    def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        """
        Internal method to make calls to the Notion API.

        Args:
            method (str): "GET", "POST", "PATCH", "DELETE"
            endpoint (str): relative endpoint (e.g., "/pages")
            kwargs: parameters for the request (json, params, etc.)

        Returns:
            dict: response in JSON format
        """

        url = f"{self.base_url}{endpoint}"
        response = requests.request(method, url, headers=self.__headers, **kwargs)
        response.raise_for_status()  # Lanza error si status >= 400
        return response.json()

    def create_page(self, data: dict) -> dict:
        return self._request("POST", "/pages", json=data)

    def get_page(self, page_id: str) -> dict:
        return self._request("GET", f"/pages/{page_id}")

    def update_page(self, page_id: str, data: dict) -> dict:
        return self._request("PATCH", f"/pages/{page_id}", json=data)

    def archive_page(self, page_id: str) -> dict:
        data = {"archived": True}
        return self.update_page(page_id, data)

    def query_datasource(self, filter: dict = None, sorts: list = None) -> dict:
        """
        Query a Notion data source using the new 2025-09-03 API.
        """
        payload = {}
        if filter:
            payload["filter"] = filter
        if sorts:
            payload["sorts"] = sorts

        return self._request("POST", f"/data_sources/{self.__datasource_id}/query", json=payload)
