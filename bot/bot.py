# bot.py

import os
from dotenv import load_dotenv
from typing import Final
from telegram import Update
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)

from bot.client import TelegramBotClient

from notion.client import NotionClient
from notion.services import create_task as notion_create_task

# ==============================
#         CONFIG
# ==============================
load_dotenv()
BOT_USERNAME: Final = os.getenv('BOT_USERNAME')
notion_client = NotionClient()


# ==============================
#         COMMANDS
# ==============================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("¡Bienvenido!")


async def create_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = """
Para crear una nueva tarea, usa este formato:

nombre, descripción, materia, fecha (YYYY-MM-DD), prioridad (alta/media/baja), esfuerzo (alto/medio/bajo)

Ejemplo:
Investigar IA en AWS, Revisar documentación y tutoriales sobre LLMs, Inteligencia Artificial, 2025-11-25, alta, medio
    """

    context.user_data['last_command'] = 'create_task'
    await update.message.reply_text(msg)


# ==============================
#       CORE RESPONSE LOGIC
# ==============================

def handle_response(update : Update, context : ContextTypes.DEFAULT_TYPE) -> str:
    last_cmd : str = context.user_data.get('last_command', '')
    text : str = update.message.text

    if last_cmd == 'create_task':
        task_columns = ['nombre', 'materia', 'descripcion', 'fecha_entrega', 'prioridad', 'nivel_esfuerzo']
        task_details = [detail.strip() for detail in text.split(',')]

        if len(task_details) != len(task_columns):
            return "Error: Por favor, proporciona todos los detalles de la tarea en el formato correcto."

        task = {column : detail for column, detail in zip(task_columns, task_details)}

        if notion_create_task(notion_client, **task):
            context.user_data['last_command'] = ''
            return "Tarea creada exitosamente en Notion."
        else:
            return "Error al crear la tarea en Notion. Por favor, intenta de nuevo."
    else:
        return "Comando no reconocido. Por favor, usa /crear_tarea para crear una nueva tarea."
        

# ==============================
#          MESSAGES
# ==============================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    chat_type = update.message.chat.type
    user_id = update.message.chat.id

    print(f'Usuario {user_id} en {chat_type}: "{text}"')

    if chat_type == 'group' and BOT_USERNAME not in text:
        return

    if chat_type == 'group':
        update.message.text = text.replace(BOT_USERNAME, '').strip()

    response = handle_response(update, context)
    print('Bot:', response)

    await update.message.reply_text(response)


# ==============================
#           ERRORS
# ==============================

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} causó error: {context.error}')


def create_bot():
    """
    Creates and returns a configured Telegram bot Application.
    """
    
    # Create Telegram bot client
    telegram_bot_client = TelegramBotClient()

    # Create Application
    app = telegram_bot_client.get_app()

    # Bind the commands and handlers to the application
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('crear_tarea', create_task))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    app.add_error_handler(error_handler)

    return app
