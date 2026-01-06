# notion/services.py
from notion.client import NotionClient

def create_task(
    client: NotionClient,
    nombre: str,
    descripcion: str,
    materia: str,
    fecha_entrega: str,
    prioridad: str,
    nivel_esfuerzo: str
) -> dict:
    """
    Create a task in the Notion database, only using existing properties and validating options.
    """
    # Sanitize inputs
    nombre = nombre.strip() if nombre else "Tarea sin título"
    descripcion = descripcion.strip() if descripcion else ""
    materia = materia.strip() if materia else ""
    fecha_entrega = fecha_entrega.strip() if fecha_entrega else ""
    prioridad = prioridad.strip() if prioridad else "Media"
    nivel_esfuerzo = nivel_esfuerzo.strip() if nivel_esfuerzo else "Medio"
    
    # Get schema
    schema = client.get_database_schema()
    
    properties = {}
    
    # Map and validate properties
    if "Nombre" in schema and nombre:
        properties["Nombre"] = {"title": [{"text": {"content": nombre}}]}
    
    if "Descripción" in schema and descripcion:
        properties["Descripción"] = {"rich_text": [{"text": {"content": descripcion}}]}
    
    if "Materia" in schema and materia:
        options = schema["Materia"].get("options", [])
        # Find case-insensitive match
        matching_option = next((opt for opt in options if opt.lower() == materia.lower()), None)
        if matching_option:
            properties["Materia"] = {"select": {"name": matching_option}}
        elif not options:  # If no options, allow free text
            properties["Materia"] = {"select": {"name": materia}}
    
    if "Fecha de entrega" in schema and fecha_entrega:
        properties["Fecha de entrega"] = {"date": {"start": fecha_entrega}}
    
    if "Prioridad" in schema and prioridad:
        options = schema["Prioridad"].get("options", [])
        if prioridad in options or not options:
            properties["Prioridad"] = {"select": {"name": prioridad}}
    
    if "Nivel de Esfuerzo" in schema and nivel_esfuerzo:
        options = schema["Nivel de Esfuerzo"].get("options", [])
        if nivel_esfuerzo in options or not options:
            properties["Nivel de Esfuerzo"] = {"select": {"name": nivel_esfuerzo}}
    
    if "Estado" in schema:
        properties["Estado"] = {"status": {"name": "Sin empezar"}}
    
    data = {
        "parent": {"data_source_id": client._NotionClient__datasource_id},
        "properties": properties
    }

    try:
        response = client.create_page(data)
        return response
    except Exception as e:
        print(f"Error creating task: {e}")
        return False

def get_task(client: NotionClient, page_id: str) -> dict:
    """
    Retrieve a Notion task by its page ID.
    """
    return client.get_page(page_id)

def update_task(client: NotionClient, page_id: str, properties: dict) -> bool:
    """
    Update a Notion task with given updates.
    """
    try:
        response = client.update_page(page_id, {"properties": properties})
        # Return response dict for reporting
        return response
    except Exception as e:
        print(f"Error updating task: {e}")
        return False


def archive_task(client: NotionClient, page_id: str) -> bool:
    """
    Archive a Notion task by its page ID.
    """
    try:
        response = client.archive_page(page_id)
        # Return the response dict for reporting purposes
        return response
    except Exception as e:
        print(f"Error archiving task: {e}")
        return False

def get_tasks(client: NotionClient) -> dict:
    filter = {
        "property": "Estado",
        "status": {"equals": "Sin empezar"}
    }

    sorts = [
        {"property": "Prioridad", "direction": "ascending"},
        {"property": "Nivel de Esfuerzo", "direction": "descending"},
        {"property": "Fecha de entrega", "direction": "ascending"}
    ]

    return client.query_datasource(filter, sorts)


