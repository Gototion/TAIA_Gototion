# bot/client.py

from telegram import Bot
from telegram.ext import Application
from config.config import config


class TelegramBotClient:
    """
    Wrapper class responsible for initializing and configuring the Telegram bot.
    Supports both local polling mode and AWS Lambda webhook mode.
    """

    def __init__(self):
        self._token = config["BOT_TK"]

        if not self._token:
            raise ValueError("BOT_TK not found in environment variables.")

        # Raw Bot instance (used for parsing updates in webhook)
        self._bot = Bot(token=self._token)

        # Unified Application (works for both webhook and polling)
        self._app = (
            Application.builder()
            .token(self._token)
            .concurrent_updates(False)
            .build()
        )

    @property
    def bot(self):
        """Return raw Bot instance (used to deserialize webhook updates)."""
        return self._bot

    @property
    def application(self):
        """Return the Application instance (for polling OR webhook)."""
        return self._app
