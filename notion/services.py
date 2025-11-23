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

    response = client.post(data)
    return response.status_code == 200
