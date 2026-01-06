# bot/polling_bot.py

from telegram.ext import CommandHandler, MessageHandler, filters

from bot.client import TelegramBotClient
from bot.commands import (
    start_command,
    create_task_command,
    get_tasks_command,
    update_task_command,
    delete_task_command,
    tutorial_command,
    set_database_command,
    schema_command
)
from bot.handlers import handle_message, error_handler


def pooling_bot():
    """
    Local entrypoint for running the bot in polling mode.
    Useful for development and debugging on your machine.
    """

    # Create client and retrieve Application() instance
    client = TelegramBotClient()
    app = client.application

    # Register handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("crear_tarea", create_task_command))
    app.add_handler(CommandHandler("lista_tareas", get_tasks_command))
    app.add_handler(CommandHandler("borrar_tarea", delete_task_command))
    app.add_handler(CommandHandler("actualizar_tarea", update_task_command))
    app.add_handler(CommandHandler("tutorial", tutorial_command))
    app.add_handler(CommandHandler("set_database", set_database_command))
    app.add_handler(CommandHandler("schema", schema_command))

    # Messages that are not commands
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Errors
    app.add_error_handler(error_handler)

    return app

