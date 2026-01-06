# config.py
import os

def load_env():
    """
    Load enviroment variables.
    - On AWS Lambda: use os.getenv()
    - On local: try to load .env if exists
    """

    if os.path.exists(".env"):
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass

    # Support multiple common env var names for compatibility
    notion_db_id = os.getenv("NOTION_DB_ID") or os.getenv("NOTION_DATABASE_ID")
    notion_token = os.getenv("NOTION_TK") or os.getenv("NOTION_API_KEY") or os.getenv("NOTION_TOKEN")
    notion_data_source = os.getenv("NOTION_DATA_SOURCE_ID") or os.getenv("NOTION_DATA_SOURCE")

    return {
        "BOT_TK": os.getenv("BOT_TK"),
        "BOT_USERNAME": os.getenv("BOT_USERNAME"),
        "NOTION_TK": notion_token,
        "NOTION_PAGE_ID": os.getenv("NOTION_PAGE_ID"),
        "NOTION_DB_ID": notion_db_id,
        "NOTION_DATA_SOURCE_ID": notion_data_source,
    }

def check_notion_credentials():
    """Verifica si las credenciales de Notion están configuradas."""
    return all([
        config.get("NOTION_TK"),
        config.get("NOTION_PAGE_ID"),
        config.get("NOTION_DB_ID")
    ])

def test_notion_connection():
    """Realiza una request de prueba a Notion para verificar la conexión."""
    try:
        from notion.client import NotionClient
        client = NotionClient()
        # Intentar una consulta simple a la DB
        client.query_datasource()
        return True
    except Exception as e:
        print(f"Error en verificación de Notion: {e}")
        return False

config = load_env()
