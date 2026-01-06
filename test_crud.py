#!/usr/bin/env python3
"""Test script for all CRUD operations on Notion database."""

import os
from dotenv import load_dotenv
load_dotenv()

from notion.client import NotionClient
from notion.services import create_task, get_tasks, update_task, archive_task
from config.config import check_notion_credentials

def test_crud_operations():
    if not check_notion_credentials():
        print("Credenciales de Notion no configuradas.")
        return

    client = NotionClient()

    print("=== TEST CRUD OPERATIONS ===\n")

    # CREATE
    print("1. Creando tarea de prueba...")
    task_data = {
        "nombre": "Tarea de prueba CRUD",
        "descripcion": "Esta es una tarea para probar las operaciones CRUD",
        "materia": "Prueba",
        "fecha_entrega": "2026-01-15",
        "prioridad": "Media",
        "nivel_esfuerzo": "Medio"
    }
    create_response = create_task(client, **task_data)
    if create_response:
        task_id = create_response["id"]
        print(f"✓ Tarea creada con ID: {task_id}")
    else:
        print("✗ Error creando tarea")
        return

    # READ
    print("\n2. Leyendo tareas...")
    tasks = get_tasks(client)
    results = tasks.get("results", [])
    print(f"✓ Encontradas {len(results)} tareas")

    # Encontrar la tarea creada
    test_task = None
    for task in results:
        if task["id"] == task_id:
            test_task = task
            break

    if test_task:
        print("✓ Tarea de prueba encontrada en la lista")
        props = test_task.get("properties", {})
        nombre = props.get("Nombre", {}).get("title", [{}])[0].get("plain_text", "")
        print(f"  Nombre: {nombre}")
    else:
        print("✗ Tarea de prueba no encontrada")

    # UPDATE
    print("\n3. Actualizando tarea...")
    update_props = {
        "Nombre": {"title": [{"text": {"content": "Tarea de prueba CRUD - Actualizada"}}]},
        "Prioridad": {"select": {"name": "Alta"}},
        "Descripción": {"rich_text": [{"text": {"content": "Descripción actualizada"}}]}
    }
    update_response = update_task(client, task_id, update_props)
    if update_response:
        print("✓ Tarea actualizada")
    else:
        print("✗ Error actualizando tarea")

    # READ again to verify update
    print("\n4. Verificando actualización...")
    tasks = get_tasks(client)
    results = tasks.get("results", [])
    updated_task = None
    for task in results:
        if task["id"] == task_id:
            updated_task = task
            break

    if updated_task:
        props = updated_task.get("properties", {})
        nombre = props.get("Nombre", {}).get("title", [{}])[0].get("plain_text", "")
        prioridad = props.get("Prioridad", {}).get("select", {}).get("name", "Sin prioridad") if props.get("Prioridad", {}).get("select") else "Sin prioridad"
        descripcion = props.get("Descripción", {}).get("rich_text", [])
        desc_text = "".join([t.get("plain_text", "") for t in descripcion]) if descripcion else "Sin descripción"
        print(f"✓ Tarea actualizada:")
        print(f"  Nombre: {nombre}")
        print(f"  Prioridad: {prioridad}")
        print(f"  Descripción: {desc_text}")
    else:
        print("✗ Tarea no encontrada después de actualización")

    # DELETE
    print("\n5. Eliminando tarea...")
    delete_response = archive_task(client, task_id)
    if delete_response:
        print("✓ Tarea eliminada (archivada)")
    else:
        print("✗ Error eliminando tarea")

    # READ final to verify deletion
    print("\n6. Verificando eliminación...")
    tasks = get_tasks(client)
    results = tasks.get("results", [])
    deleted_task = None
    for task in results:
        if task["id"] == task_id:
            deleted_task = task
            break

    if deleted_task:
        archived = deleted_task.get("archived", False)
        if archived:
            print("✓ Tarea correctamente archivada")
        else:
            print("✗ Tarea no archivada")
    else:
        print("✓ Tarea no encontrada en lista activa (posiblemente archivada)")

    print("\n=== TEST COMPLETADO ===")

if __name__ == "__main__":
    test_crud_operations()