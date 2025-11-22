import os
from dotenv import load_dotenv
from typing import Final
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from notion import create_task as notion_create_task

# Credentials
load_dotenv()
TELEGRAM_TK : Final = os.getenv('TELEGRAM_TK')
BOT_USERNAME : Final = os.getenv('BOT_USERNAME')


# Comands 
async def start_command(update : Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = "Bienvenido!"
    await update.message.reply_text(msg)

async def create_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = """
    Para crear una nueva tarea, usa el siguiente formato:
    Nombre de la tarea, descripción de la tarea, materia, fecha de vencimiento (YYYY-MM-DD), prioridad (alta, media, baja), esfuerzo (alto, medio, bajo)

    Ejemplo:
    Investigar IA en AWS, Revisar documentación y tutoriales sobre LLMs en AWS, Inteligencia Artificial, 2025-11-25, alta, medio    
    """

    context.user_data['last_command'] = 'create_task'
    
    await update.message.reply_text(msg)

# Reponses    
def handle_response(update : Update, context : ContextTypes.DEFAULT_TYPE) -> str:
    last_cmd : str = context.user_data.get('last_command', '')
    text : str = update.message.text

    if last_cmd == 'create_task':
        task_columns = ['nombre', 'materia', 'descripcion', 'fecha_entrega', 'prioridad', 'nivel_esfuerzo']
        task_details = [detail.strip() for detail in text.split(',')]

        if len(task_details) != len(task_columns):
            return "Error: Por favor, proporciona todos los detalles de la tarea en el formato correcto."

        task = {column : detail for column, detail in zip(task_columns, task_details)}

        if notion_create_task(**task):
            context.user_data['last_command'] = ''
            return "Tarea creada exitosamente en Notion."
        else:
            return "Error al crear la tarea en Notion. Por favor, intenta de nuevo."
    else:
        return "Comando no reconocido. Por favor, usa /crear_tarea para crear una nueva tarea."
        
        

# Messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type : str = update.message.chat.type # Public chat or Private chat
    text : str = update.message.text
    user : int = update.message.chat.id

    print(f'Usuario {user} en {message_type}: "{text}"')

    if message_type == 'group':
        if not BOT_USERNAME in text: return 
        new_text : str = text.replace(BOT_USERNAME, '').strip()
        response : str = handle_response(update, context)
    else:
        response : str = handle_response(update, context)
        print('Bot:', response)
        await update.message.reply_text(response)

# Errors        
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} causo el siguiente error: {context.error}')
            

# Main Program
if __name__ == '__main__':
    print("Iniciando Gototion...\n")
    app = Application.builder().token(TELEGRAM_TK).build()

    # Comands
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('crear_tarea', create_task))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Errors
    app.add_error_handler(error)

    print("Esperando respuestas...\n")
    app.run_polling(poll_interval=3)
