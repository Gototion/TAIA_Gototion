# notion/client.py

import requests
import os
from config.config import config

class NotionClient:
    def __init__(self):
        self.__token = os.environ.get("NOTION_TK")
        # Clean up database ID: remove any URL parameters like ?v=...
        db_id = os.environ.get("NOTION_DB_ID")
        if db_id and "?" in db_id:
            db_id = db_id.split("?")[0]
        self.__database_id = db_id
        
        # Use Notion API version 2025-09-03 (supports multi-source databases)
        self.notion_version = "2025-09-03"
        self.__headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.__token}",
            "Notion-Version": self.notion_version,
        }
        self.base_url = "https://api.notion.com/v1"
        
        # Try to get data_source_id from config; if not set, discover it from database
        configured_ds_id = os.environ.get("NOTION_DATA_SOURCE_ID")
        self.__datasource_id = configured_ds_id if configured_ds_id else self._discover_data_source_id()



    def _discover_data_source_id(self) -> str:
        """
        Discover the data_source_id by calling GET /v1/databases/{database_id}.
        This endpoint returns a list of data sources under the database.
        """
        if not self.__database_id:
            raise RuntimeError("NOTION_DB_ID not configured. Cannot discover data source.")
        
        try:
            url = f"{self.base_url}/databases/{self.__database_id}"
            response = requests.get(url, headers=self.__headers)
            response.raise_for_status()
            data = response.json()
            
            # Extract the first data source from the list
            data_sources = data.get("data_sources", [])
            if not data_sources:
                raise RuntimeError(f"No data sources found in database {self.__database_id}")
            
            ds_id = data_sources[0].get("id")
            print(f"✓ Discovered data_source_id: {ds_id}")
            return ds_id
        except Exception as e:
            print(f"✗ Error discovering data_source_id: {e}")
            raise RuntimeError(f"Failed to discover data_source_id: {e}")

    @property
    def database_id(self) -> str:
        return self.__database_id

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

        # If Notion returns an error (status >= 400), capture and raise a clearer exception
        if not response.ok:
            try:
                body = response.json()
            except Exception:
                body = response.text

            # Print debug information to help diagnose issues (token/ids/payload)
            print(f"Notion API error: {response.status_code} {response.reason} for URL: {url}")
            print(f"Request headers: {self.__headers}")
            if 'json' in kwargs:
                print(f"Request JSON payload: {kwargs.get('json')}")
            print(f"Response body: {body}")

            raise RuntimeError(f"Notion API error {response.status_code}: {body}")

        # Successful response
        return response.json()

    def get_database(self, database_id: str = None) -> dict:
        if database_id is None:
            database_id = self.__database_id
        return self._request("GET", f"/databases/{database_id}")

    def get_database_properties(self, database_id: str = None) -> dict:
        db = self.get_database(database_id)
        return db.get("properties", {})

    def get_database_schema(self, database_id: str = None) -> dict:
        """Obtiene el esquema del data source, incluyendo propiedades y opciones de selects."""
        ds_id = self.__datasource_id  # Usa el data_source_id descubierto
        response = self._request('GET', f'/data_sources/{ds_id}')
        properties = response.get('properties', {})
        schema = {}
        for prop_name, prop_data in properties.items():
            prop_type = prop_data.get('type')
            schema[prop_name] = {
                'type': prop_type,
                'options': []
            }
            if prop_type in ['select', 'multi_select', 'status']:
                options = prop_data.get(prop_type, {}).get('options', [])
                schema[prop_name]['options'] = [opt['name'] for opt in options]
        return schema

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

        # If a data source id is configured, use the newer data_sources endpoint.
        if self.__datasource_id:
            endpoint = f"/data_sources/{self.__datasource_id}/query"
            print(f"Querying Notion data source {self.__datasource_id} with payload: {payload}")
            return self._request("POST", endpoint, json=payload)

        # Fallback: if no data source id is available, try querying the database directly
        if self.__database_id:
            endpoint = f"/databases/{self.__database_id}/query"
            print(f"Querying Notion database {self.__database_id} with payload: {payload}")
            return self._request("POST", endpoint, json=payload)

        # If neither is available, raise a clearer error
        raise RuntimeError("Notion data source id and database id are not configured. Set NOTION_DATA_SOURCE_ID or NOTION_DB_ID in your environment.")
