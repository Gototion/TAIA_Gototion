"""Agent wrapper that asks Gemini for a plan of actions and executes Notion tools.

The agent expects Gemini to return a JSON array of actions, e.g.:
[
  {"action": "create_task", "args": {"nombre": "T1", "descripcion": "...", "materia":"Math", "fecha_entrega":"2025-12-31", "prioridad":"Media", "nivel_esfuerzo":"Medio"}},
  {"action": "archive_task", "args": {"page_id": "..."}}
]

If GEMINI is not available or the model doesn't return valid JSON, the function
raises a RuntimeError so callers can fallback to other parsers.
"""
from datetime import datetime
from typing import List, Dict, Optional
import os
import re
import json

import ast
try:
    import google.generativeai as genai
except Exception:
    genai = None

from notion.client import NotionClient
from notion.services import (
    create_task as notion_create_task,
    update_task as notion_update_task,
    archive_task as notion_archive_task,
)


def _initialize_gemini():
    if genai is None:
        raise RuntimeError("google.generativeai no está instalado.")
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY no encontrada.")
    genai.configure(api_key=api_key)


def _extract_json_segment(text: str) -> str:
    """Encuentra el primer array JSON o el primer objeto JSON en la respuesta."""
    # Buscar array primero
    m = re.search(r"\[\s*\{.*\}\s*\]", text, re.DOTALL)
    if m:
        return m.group(0)
    # Buscar objeto
    m2 = re.search(r"\{.*\}", text, re.DOTALL)
    if m2:
        # envolver en array para unificar
        return f"[{m2.group(0)}]"
    raise ValueError("No se encontró JSON (array/objeto) en la respuesta del modelo.")


def _parse_tool_calls_from_text(text: str) -> List[Dict]:
    """Busca llamadas marcadas con @tool en el texto y las parsea a acciones.

    Soporta sintaxis en una línea del tipo:
      @tool create_task(nombre=Avanzar con la presentación, fecha_entrega=2026-01-09)

    Devuelve una lista de objetos: {"action": <name>, "args": {..}}
    """
    actions: List[Dict] = []
    # Usar regex para extraer tool y params
    import re
    for match in re.finditer(r"@tool\s+(\w+)\((.*?)\)", text):
        tool_name = match.group(1)
        params_str = match.group(2)
        args = {}
        # Extraer key=value pairs
        for param_match in re.finditer(r'(\w+)=([^,]+)', params_str):
            key = param_match.group(1)
            value = param_match.group(2).strip().strip('"').strip("'")  # Remover quotes si hay
            args[key] = value
        actions.append({"action": tool_name, "args": args})
    return actions


def run_agent_execute(text: str, debug: bool = False, client: Optional[NotionClient] = None) -> Dict:
    """Preguntar a Gemini por un plan de acciones y ejecutar las herramientas.

    Devuelve un dict con la salida cruda del modelo y una lista de resultados por acción.
    """
    if client is None:
        from config.config import check_notion_credentials
        if not check_notion_credentials():
            raise RuntimeError("Credenciales de Notion no configuradas. Usa /tutorial y /set_database.")
        client = NotionClient()

    if os.getenv("GEMINI_API_KEY") is None:
        raise RuntimeError("GEMINI_API_KEY no configurada")

    _initialize_gemini()

    # Obtener schema de la DB para incluir opciones válidas
    schema = client.get_database_schema()
    materia_options = []
    if "Materia" in schema and schema["Materia"]["options"]:
        materia_options = schema["Materia"]["options"]

    # Escape braces in the prompt (use double braces for literal braces in f-strings)
    # El prompt permite al modelo devolver EITHER: (A) un JSON array como antes,
    # o (B) llamadas a herramientas en líneas utilizando la etiqueta @tool.
    # Ejemplos aceptables de salida del modelo:
    # 1) JSON: [{"action":"create_task","args":{...}}]
    # 2) @tool create_task(nombre="T1", fecha_entrega="2025-12-31")
    prompt = (
        "Eres un agente que debe decidir qué herramienta usar para atender la petición.\n"
        "RESPONDE SOLO con EITHER (A) JSON válido que sea un array de acciones, o (B) una o varias líneas que comiencen con '@tool' seguidas de la llamada con los argumentos.\n"
        "No incluyas texto adicional fuera del JSON o de las líneas @tool.\n"
        "\nHerramientas disponibles (firma):\n"
        "- create_task(titulo, descripcion, materia, fecha_entrega (YYYY-MM-DD), prioridad, nivel_esfuerzo)\n"
        "- update_task(page_id, properties)  # properties en formato Notion\n"
        "- archive_task(page_id)\n"
        "\nSi la petición no requiere ninguna acción, devuelve [{\"action\":\"noop\",\"args\":{}}] o una línea '@tool noop()'.\n"
        "Valores válidos:"
        "- prioridad: \"Alta\", \"Media\", \"Baja\""
        "- nivel_esfuerzo: \"Alto\", \"Medio\", \"Bajo\""
        f"{'- materia: ' + ', '.join(f'\"{opt}\"' for opt in materia_options) + '\n' if materia_options else ''}"
        "- fecha_entrega: formato ISO 8601 (YYYY-MM-DD). Si el usuario menciona una fecha relativa, calcúlala basándote en {today_str}. En caso de que el usuario no especifique una fecha, asume que es {today_str}.\n"
        f"Fecha actual de referencia: {datetime.now().strftime('%Y-%m-%d')}.\n"
        "\nEntrada del usuario:\n"
        "----------------------------------------\n"
        f"{text}\n"
        "----------------------------------------\n"
        "\nRecuerda: si usas @tool, cada línea debe tener la forma: @tool <tool_name>(key=value, ...)."
   
    )

    model = genai.GenerativeModel("gemini-2.5-flash-lite")
    resp = model.generate_content(prompt)
    raw = resp.text.strip()
    # Mostrar la respuesta cruda de Gemini siempre en la terminal, para auditoría
    try:
        print("[AGENT] Gemini raw output:\n" + raw)
    except Exception:
        # En entornos donde print podría fallar por encoding, salir silenciosamente
        pass

    # Intentar parsear en este orden:
    # 1) líneas @tool (más explícitas)
    # 2) JSON array u objeto incrustado
    actions = []
    try:
        actions = _parse_tool_calls_from_text(raw)
        if not actions:
            seg = _extract_json_segment(raw)
            actions = json.loads(seg)
    except ValueError as e:
        if "No se encontró JSON" in str(e):
            actions = []  # No hay acciones válidas
        else:
            # Mostrar la respuesta cruda también en caso de error de parseo
            try:
                print("[AGENT] Gemini raw (on parse error):\n" + raw)
            except Exception:
                pass
            raise RuntimeError(f"Error extrayendo acciones del modelo: {e}")
    except Exception as e:
        # Mostrar la respuesta cruda también en caso de error de parseo
        try:
            print("[AGENT] Gemini raw (on parse error):\n" + raw)
        except Exception:
            pass
        raise RuntimeError(f"Error extrayendo acciones del modelo: {e}")

    results = []
    for act in actions:
        name = act.get("action")
        args = act.get("args", {}) or {}
        try:
            if name == "create_task":
                resp = notion_create_task(
                    client,
                    nombre=args.get("titulo") or args.get("nombre") or "Tarea",
                    descripcion=args.get("descripcion", ""),
                    materia=args.get("materia", ""),
                    fecha_entrega=args.get("fecha_entrega", ""),
                    prioridad=args.get("prioridad", "Media"),
                    nivel_esfuerzo=args.get("nivel_esfuerzo", "Medio"),
                )
                if resp and isinstance(resp, dict):
                    results.append({"action": name, "ok": True, "result": resp})
                else:
                    results.append({"action": name, "ok": False, "result": resp})
            elif name == "update_task":
                page_id = args.get("page_id")
                props = args.get("properties", {})
                resp = notion_update_task(client, page_id, props)
                if resp and isinstance(resp, dict):
                    results.append({"action": name, "ok": True, "result": resp})
                else:
                    results.append({"action": name, "ok": False, "result": resp})
            elif name == "archive_task":
                page_id = args.get("page_id")
                resp = notion_archive_task(client, page_id)
                if resp and isinstance(resp, dict):
                    results.append({"action": name, "ok": True, "result": resp})
                else:
                    results.append({"action": name, "ok": False, "result": resp})
            elif name == "noop":
                results.append({"action": name, "ok": True})
            else:
                results.append({"action": name, "ok": False, "reason": "unknown action"})
        except Exception as e:
            results.append({"action": name, "ok": False, "error": str(e)[:200]})

    return {"raw": raw, "results": results}
