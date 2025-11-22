import requests
import os
from dotenv import load_dotenv
from typing import Final

# Credentials
load_dotenv()
NOTION_TK: Final = os.getenv('NOTION_TK')
NOTION_DB_ID: Final = os.getenv('NOTION_DB_ID')

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {NOTION_TK}",
    "Notion-Version": "2025-09-03",
}

url = "https://api.notion.com/v1/pages/"

def create_task(
    nombre: str,
    materia: str,
    descripcion: str,
    fecha_entrega: str,
    prioridad: str,
    nivel_esfuerzo: str
) -> bool:
    """
    Crea una tarea en la base de datos de Notion usando la API.
    
    Parámetros:
        nombre (str): Título de la tarea
        materia (str): Valor del select "Materia"
        descripcion (str): Texto de la descripción
        fecha_entrega (str): Fecha en formato ISO YYYY-MM-DD
        prioridad (str): Valor del select "Prioridad"
        nivel_esfuerzo (str): Valor del select "Nivel de Esfuerzo"
    
    Retorna:
        bool: True si la tarea fue creada exitosamente, False en caso contrario.
    """

      # Mostrar los argumentos
    print("=== Datos que se enviarán a Notion ===")
    print("Nombre:", nombre)
    print("Materia:", materia)
    print("Descripción:", descripcion)
    print("Fecha de Entrega:", fecha_entrega)
    print("Prioridad:", prioridad)
    print("Nivel de Esfuerzo:", nivel_esfuerzo)
    print("=====================================")
    
    data = {
        "parent": {"database_id": NOTION_DB_ID},
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

    response = requests.post(url=url, headers=headers, json=data)

    return response.status_code == 200


