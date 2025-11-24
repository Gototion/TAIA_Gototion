# bot/commands.py

from bot.handlers import handle_get_tasks
from telegram import Update
from telegram.ext import ContextTypes

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("¡Bienvenido!")


async def create_task_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = """
Para crear una nueva tarea, usa este formato:

nombre, descripción, materia, fecha (YYYY-MM-DD), prioridad (alta/media/baja), esfuerzo (alto/medio/bajo)

Ejemplo:
Investigar IA en AWS, Revisar documentación y tutoriales sobre LLMs, Inteligencia Artificial, 2025-11-25, alta, medio
    """

    context.user_data['last_command'] = 'create_task'
    await update.message.reply_text(msg)

async def get_tasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    response = handle_get_tasks(update, context)

    await update.message.reply_text(response)

# Comando que inicia la actualización
async def update_task_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = """
Para actualizar una tarea, proporciona el número de la tarea y los campos a actualizar en el siguiente formato:

número de tarea, campo1: nuevo valor1, campo2: nuevo valor2
    """
    
    context.user_data['last_command'] = 'update_task'
    
    await update.message.reply_text(msg)


