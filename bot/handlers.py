# bot/handlers.py

from telegram import Update
from telegram.ext import ContextTypes
from bot.config import BOT_USERNAME
from notion.services import create_task
from notion.client import NotionClient

notion_client = NotionClient()

# ==============================
#         AUXILIARY
# ============================== 
def _handle_create_task(update : Update, context : ContextTypes.DEFAULT_TYPE) -> str:
    text : str = update.message.text
    task_columns = ['nombre', 'materia', 'descripcion', 'fecha_entrega', 'prioridad', 'nivel_esfuerzo']
    task_details = [detail.strip() for detail in text.split(',')]

    if len(task_details) != len(task_columns):
        return "Error: Por favor, proporciona todos los detalles de la tarea en el formato correcto."

    task = {column : detail for column, detail in zip(task_columns, task_details)}

    if create_task(notion_client, **task):
        context.user_data['last_command'] = ''
        return "Tarea creada exitosamente en Notion."
    else:
        return "Error al crear la tarea en Notion. Por favor, intenta de nuevo."

def _handle_update_task(update : Update, context : ContextTypes.DEFAULT_TYPE) -> str:
    pass  

def _handle_delete_tasks(update : Update, context : ContextTypes.DEFAULT_TYPE) -> str:
    pass

def _handle_get_tasks(update : Update, context : ContextTypes.DEFAULT_TYPE) -> str:
    pass

# ==============================
#         RESPONSES
# ==============================    
def handle_response(update : Update, context : ContextTypes.DEFAULT_TYPE) -> str:
    last_cmd : str = context.user_data.get('last_command', '')
    text : str = update.message.text

    # --- Create Task ---
    if last_cmd == 'create_task':
        return _handle_create_task(update, context)
        
    elif last_cmd == 'update_task':
        # Future implementation for updating tasks
        return "Funcionalidad de actualización de tareas no implementada aún."

    elif last_cmd == 'delete_tasks':
        # Future implementation for updating tasks
        return "Funcionalidad de actualización de tareas no implementada aún."

    elif last_cmd == 'get_tasks':
        # Future implementation for updating tasks
        return "Funcionalidad de actualización de tareas no implementada aún."

    else:
        return "No entendí tu mensaje. Usa /crear_tarea para iniciar la creación de una tarea."
        

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
