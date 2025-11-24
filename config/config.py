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

    return {
        "BOT_TK": os.getenv("BOT_TK"),
        "BOT_USERNAME": os.getenv("BOT_USERNAME"),
        "NOTION_TK": os.getenv("NOTION_TK"),
        "NOTION_PAGE_ID": os.getenv("NOTION_PAGE_ID"),
        "NOTION_DB_ID": os.getenv("NOTION_DB_ID"),
        "NOTION_DATA_SOURCE_ID": os.getenv("NOTION_DATA_SOURCE_ID"),
    }

config = load_env()
