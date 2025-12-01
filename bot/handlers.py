# bot/handlers.py

from telegram import Update
from telegram.ext import ContextTypes
from bot.llm_parser import parse_tasks_natural
from config.config import config
from notion.services import create_task, get_tasks, update_task
from notion.client import NotionClient

notion_client = NotionClient()

# ==============================
#         AUXILIARY
# ============================== 
def _handle_create_task(update : Update, context : ContextTypes.DEFAULT_TYPE) -> str:
    text : str = update.message.text
    task_columns = ['nombre', 'descripcion', 'materia', 'fecha_entrega', 'prioridad', 'nivel_esfuerzo']
    task_details = [detail.strip() for detail in text.split(',')]
    # Si el usuario dio exactamente 6 campos separados por comas, usar el parser simple
    if len(task_details) == len(task_columns):
        task = {column: detail for column, detail in zip(task_columns, task_details)}

        if create_task(notion_client, **task):
            context.user_data['last_command'] = ''
            return "Tarea creada exitosamente en Notion."
        else:
            return "Error al crear la tarea en Notion. Por favor, intenta de nuevo."

    # Si no coincide con el formato exacto, intentar parsear lenguaje natural con LLM
    try:
        user_categories = None
        # Si tienes categorías de usuario disponibles, pásalas aquí
        parsed_tasks = parse_tasks_natural(text, user_categories=user_categories, debug=False)
    except Exception as e:
        # En caso de fallo del LLM, devolver error de formato
        print(f'LLM parser error: {e}')
        return "Error: no pude entender la tarea. Usa el formato: nombre, descripción, materia, fecha (YYYY-MM-DD), prioridad, esfuerzo"

    if not parsed_tasks:
        return "No pude extraer tareas del texto. Intenta ser más concreto o usa el formato por comas."

    created = 0
    failed = 0
    for t in parsed_tasks:
        # Normalizar keys para create_task (espera nombres en español exactos)
        normalized = {
            'nombre': t.get('Titulo') or t.get('titulo') or t.get('Titulo', ''),
            'descripcion': t.get('descripcion', ''),
            'materia': t.get('materia', ''),
            'fecha_entrega': t.get('fecha_entrega', ''),
            'prioridad': t.get('prioridad', ''),
            'nivel_esfuerzo': t.get('nivel_esfuerzo', ''),
        }
        try:
            ok = create_task(notion_client, **normalized)
            if ok:
                created += 1
            else:
                failed += 1
        except Exception as e:
            print(f'Error creando tarea en Notion: {e}')
            failed += 1

    context.user_data['last_command'] = ''
    return f"Tareas creadas: {created}. Fallidas: {failed}."

def _handle_update_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    text: str = update.message.text

    try:
        task_num_str, props_str = text.split(',', 1)
        task_num = task_num_str.strip()
        props_list = [p.strip() for p in props_str.split(',')]
    except ValueError:
        return "Formato inválido. Usa: número de tarea, campo1: valor1, campo2: valor2"

    tasks = get_tasks(notion_client).get("results", [])
    if not tasks:
        return "No tienes tareas pendientes para actualizar."

    # Buscar el page_id de la tarea correspondiente
    page_id = None
    for i, task in enumerate(tasks, start=1):
        if str(i) == task_num:
            page_id = task.get("id")
            break
    if not page_id:
        return f"No se encontró la tarea número {task_num}"

    # Convertir propiedades a formato Notion
    properties = {}
    for prop in props_list:
        if ':' not in prop:
            continue
        key, value = [x.strip() for x in prop.split(':', 1)]
        if key.lower() == "estado":
            properties["Estado"] = {"status": {"name": value}}
        elif key.lower() == "prioridad":
            properties["Prioridad"] = {"select": {"name": value}}
        elif key.lower() == "nivel de esfuerzo":
            properties["Nivel de Esfuerzo"] = {"select": {"name": value}}
        elif key.lower() == "fecha de entrega":
            properties["Fecha de Entrega"] = {"date": {"start": value}}
        elif key.lower() == "nombre":
            properties["Nombre"] = {"title": [{"text": {"content": value}}]}
        elif key.lower() == "descripcion":
            properties["Descripción"] = {"rich_text": [{"text": {"content": value}}]}

    print(f'Actualizando tarea {page_id} con propiedades: {properties}')

    # Actualizar la tarea en Notion
    if update_task(notion_client, page_id, properties):
        return "Tarea actualizada exitosamente."
    else:
        return "Ocurrió un error al actualizar la tarea."


def _handle_delete_tasks(update : Update, context : ContextTypes.DEFAULT_TYPE) -> str:
    pass

def handle_get_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    tasks_data = get_tasks(notion_client)
    results = tasks_data.get("results", [])
    context.user_data['last_command'] = ''
    
    if not results:
        return "No tienes tareas pendientes."

    response_lines = [
        "Aquí está la lista de tus tareas pendientes ordenadas por prioridad, esfuerzo y fecha de entrega:\n"
    ]

    for i, task in enumerate(results, start=1):
        props = task.get("properties", {})

        # Extraer propiedades específicas, con seguridad si no existen
        nombre = props.get("Nombre", {}).get("title", [])
        nombre_text = nombre[0]["text"]["content"] if nombre else "Sin título"

        descripcion = props.get("Descripción", {}).get("rich_text", [])
        descripcion_text = descripcion[0]["text"]["content"] if descripcion else "Sin descripción"

        materia = props.get("Materia", {}).get("select", {}).get("name", "Sin materia")
        fecha_entrega = props.get("Fecha de Entrega", {}).get("date", {}).get("start", "Sin fecha")
        prioridad = props.get("Prioridad", {}).get("select", {}).get("name", "Sin prioridad")
        nivel_esfuerzo = props.get("Nivel de Esfuerzo", {}).get("select", {}).get("name", "Sin nivel")

        # Formatear cada tarea en una línea
        response_lines.append(
            f"{i}. {nombre_text} ({materia})\n"
            f"   Descripción: {descripcion_text}\n"
            f"   Fecha de entrega: {fecha_entrega}\n"
            f"   Prioridad: {prioridad}, Nivel de esfuerzo: {nivel_esfuerzo}\n"
        )

    # Unir todas las líneas en un solo string para Telegram
    return "\n".join(response_lines)


# ==============================
#         RESPONSES
# ==============================    
def handle_response(update : Update, context : ContextTypes.DEFAULT_TYPE) -> str:
    last_cmd : str = context.user_data.get('last_command', '')
    text : str = update.message.text

    print(f'Último comando del usuario: {last_cmd}')
    # --- Create Task ---
    if last_cmd == 'create_task':
        return _handle_create_task(update, context)
        
    elif last_cmd == 'update_task':
        return _handle_update_task(update, context)

    elif last_cmd == 'delete_tasks':
        # Future implementation for updating tasks
        return "Funcionalidad de actualización de tareas no implementada aún."

    elif last_cmd == 'get_tasks':
        return _handle_get_tasks(update, context)

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

    if chat_type == 'group' and config["BOT_USERNAME"] not in text:
        return

    if chat_type == 'group':
        update.message.text = text.replace(config["BOT_USERNAME"], '').strip()

    response = handle_response(update, context)
    print('Bot:', response)

    await update.message.reply_text(response)


# ==============================
#           ERRORS
# ==============================

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} causó error: {context.error}')
