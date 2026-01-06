# bot/commands.py

from bot.handlers import handle_get_tasks, get_notion_client
from telegram import Update
from telegram.ext import ContextTypes
from notion.client import NotionClient
from notion.services import get_tasks
from config.config import check_notion_credentials

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
    if not check_notion_credentials():
        await update.message.reply_text("Credenciales de Notion no configuradas. Ejecuta /tutorial para instrucciones y /set_database para configurar.")
        return
    
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


async def tutorial_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = """
Para configurar Notion:
1. Ve a https://www.notion.so/ y crea una cuenta si no tienes.
2. Crea una nueva página o base de datos.
3. Obtén tu Integration Token: Ve a https://www.notion.so/my-integrations, crea una nueva integración y copia el token.
4. Obtén el ID de la página: En la URL de tu página, copia el ID (después de la última /).
5. Obtén el ID de la base de datos: En la URL de la DB, copia el ID.
6. Usa /set_database para ingresar estos valores.
    """
    await update.message.reply_text(msg)


async def set_database_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = """
Envía los valores en el siguiente formato:
NOTION_TK: tu_token
NOTION_PAGE_ID: tu_page_id
NOTION_DB_ID: tu_db_id

Ejemplo:
NOTION_TK: secret_abc123
NOTION_PAGE_ID: 12345678-1234-1234-1234-123456789abc
NOTION_DB_ID: abcdef12-3456-7890-abcd-ef1234567890
    """
    context.user_data['last_command'] = 'set_database'
    await update.message.reply_text(msg)


async def schema_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Muestra el esquema de la base de datos de Notion."""
    try:
        notion_client = get_notion_client()
        schema = notion_client.get_database_schema()
        response = "Esquema de la DB de Notion:\n"
        for prop, data in schema.items():
            response += f"- {prop} ({data['type']}): {', '.join(data['options']) if data['options'] else 'Sin opciones'}\n"
        await update.message.reply_text(response)
    except RuntimeError as e:
        await update.message.reply_text(str(e))

