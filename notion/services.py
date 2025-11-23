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
) -> bool:
    """
    Creare a notion task given a Notion Client and task details.
    """
    data = {
        "parent": {"database_id": client.database_id},
        "properties": {
            "Nombre": {"title": [{"text": {"content": nombre}}]},
            "Materia": {"select": {"name": materia}},
            "Descripción": {"rich_text": [{"text": {"content": descripcion}}]},
            "Estado": {"status": {"name": "Not started"}},
            "Fecha de Entrega": {"date": {"start": fecha_entrega}},
            "Prioridad": {"select": {"name": prioridad}},
            "Nivel de Esfuerzo": {"select": {"name": nivel_esfuerzo}}
        }
    }

    try:
        client.create_page(data)
        return True
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
        return True
    except Exception as e:
        print(f"Error updating task: {e}")
        return False


def archive_task(client: NotionClient, page_id: str) -> bool:
    """
    Archive a Notion task by its page ID.
    """
    response = client.archive_page(page_id)
    return response.status_code == 200

def get_tasks(client: NotionClient) -> dict:
    filter = {
        "property": "Estado",
        "status": {"equals": "Not started"}
    }

    sorts = [
        {"property": "Prioridad", "direction": "ascending"},
        {"property": "Nivel de Esfuerzo", "direction": "descending"},
        {"property": "Fecha de Entrega", "direction": "ascending"}
    ]

    return client.query_datasource(filter, sorts)


