# bot/config.py
import os
from dotenv import load_dotenv
from notion.client import NotionClient
from typing import Final


load_dotenv()
BOT_USERNAME: Final = os.getenv('BOT_USERNAME')
