# bot/client.py

import os
from dotenv import load_dotenv
from telegram.ext import Application

load_dotenv()

class TelegramBotClient:
    """
    Wrapper class responsible for initializing and configuring
    the Telegram bot application. Keeps credentials isolated.
    """

    def __init__(self):
        self.__token = os.getenv("BOT_TK")
        
        if not self.__token:
            raise ValueError("BOT not found in environment variables")

        self.__app = Application.builder().token(self.__token).build()

    def get_app(self):
        """Return the Telegram Application instance."""
        return self.__app
