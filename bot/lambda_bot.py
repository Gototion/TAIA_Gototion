# bot/lambda_bot.py

import json
from telegram.ext import CommandHandler, MessageHandler, filters
from telegram import Update

from bot.client import TelegramBotClient
from bot.commands import (
    start_command, 
    create_task_command,
    get_tasks_command, 
    update_task_command
)
from bot.handlers import handle_message, error_handler


# Create a single TelegramBotClient instance
client = TelegramBotClient()

# Application used for webhook updates in AWS Lambda
app = client.application
bot = client.bot  # Bot instance for Update.de_json()


# Register handlers (same as before)
app.add_handler(CommandHandler("start", start_command))
app.add_handler(CommandHandler("crear_tarea", create_task_command))
app.add_handler(CommandHandler("lista_tareas", get_tasks_command))
app.add_handler(CommandHandler("actualizar_tarea", update_task_command))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_error_handler(error_handler)

def lambda_handler(event, context):
    print("🔹 EVENTO RECIBIDO:", event)

    if "body" in event:
        body = json.loads(event["body"])
        print("🔹 BODY RECIBIDO:", body)

        # Convertimos a Update
        from telegram import Update
        update = Update.de_json(body, app.bot)

        print("🔹 UPDATE PARSEADO:", update)

        # Procesamos update (IMPORTANTE: initialize + process)
        async def process():
            await app.initialize()
            await app.process_update(update)
            await app.shutdown()

        import asyncio
        asyncio.run(process())

    return {"statusCode": 200}
