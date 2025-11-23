# bot/commands.py

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
