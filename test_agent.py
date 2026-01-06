#!/usr/bin/env python3
"""Test script for the agent to create a task."""

import os
from dotenv import load_dotenv
load_dotenv()

from bot.agent import run_agent_execute

def test_create_task():
    text = "Crear una tarea para estudiar matemáticas para mañana con prioridad alta"
    try:
        result = run_agent_execute(text, debug=True)
        print("Result:", result)
        # Simular el procesamiento de results como en handlers.py
        lines = []
        for r in result.get("results", []):
            act = r.get("action")
            ok = r.get("ok")
            if ok:
                res = r.get("result")
                if act == "create_task" and isinstance(res, dict):
                    from bot.handlers import format_task_details
                    lines.append(format_task_details(res))
                elif isinstance(res, dict):
                    page_id = res.get("id") or (res.get("page") or {}).get("id") if isinstance(res.get("page"), dict) else None
                    if page_id:
                        lines.append(f"Acción: {act} — OK — page_id: {page_id}")
                    else:
                        lines.append(f"Acción: {act} — OK — respuesta: {str(res)[:120]}")
                else:
                    lines.append(f"Acción: {act} — OK")
            else:
                err = r.get("error") or r.get("reason") or str(r.get("result"))
                lines.append(f"Acción: {act} — FALLÓ — {err}")

        print("Response lines:", lines)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test_create_task()