# bot/commands.py

from bot.handlers import handle_get_tasks
from telegram import Update
from telegram.ext import ContextTypes
from notion.client import NotionClient
from notion.services import get_tasks

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


async def delete_task_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Inicia el flujo para borrar una tarea: muestra la lista y espera la selección."""
    client = NotionClient()
    tasks_data = get_tasks(client)
    results = tasks_data.get("results", [])

    if not results:
        await update.message.reply_text("No tienes tareas pendientes para borrar.")
        return

    response_lines = ["Selecciona la tarea a borrar respondiendo con su número o nombre exacto:\n"]

    num_map = {}
    name_map = {}
    for i, task in enumerate(results, start=1):
        props = task.get("properties", {})
        nombre = props.get("Nombre", {}).get("title", [])
        nombre_text = nombre[0]["text"]["content"] if nombre else "Sin título"
        response_lines.append(f"{i}. {nombre_text}")
        num_map[str(i)] = task.get("id")
        name_map[nombre_text] = task.get("id")

    # Guardar mapas en user_data para la siguiente interacción
    context.user_data['delete_map_by_num'] = num_map
    context.user_data['delete_map_by_name'] = name_map
    context.user_data['last_command'] = 'delete_tasks'

    await update.message.reply_text("\n".join(response_lines))


