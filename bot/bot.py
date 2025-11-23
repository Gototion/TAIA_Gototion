# bot.py

from telegram.ext import CommandHandler, MessageHandler, filters
from bot.client import TelegramBotClient
from bot.commands import start_command, create_task_command, get_tasks_command, update_task_command
from bot.handlers import handle_message, error_handler
from bot.config import BOT_USERNAME

def create_bot():
    telegram_bot_client = TelegramBotClient()
    app = telegram_bot_client.get_app()

    # Command handlers
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('crear_tarea', create_task_command))
    app.add_handler(CommandHandler('lista_tareas', get_tasks_command))
    app.add_handler(CommandHandler('actualizar_tarea', update_task_command))

    # Message handler
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Error handler
    app.add_error_handler(error_handler)

    return app
