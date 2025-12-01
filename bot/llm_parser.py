"""Envoltorio ligero para usar el parser LLM definido en `llm_test.py`.

Intenta importar la función `parse_multiple_tasks_container` desde el módulo raíz
`llm_test`. Si no está disponible, lanza un error claro en tiempo de ejecución.
"""
from typing import List, Dict, Optional

def parse_tasks_natural(text: str, user_categories: Optional[List[str]] = None, debug: bool = False) -> List[Dict]:
    """Parsea `text` en una lista de tareas usando el parser LLM.

    Intenta importar `parse_multiple_tasks_container` desde `llm_test` en tiempo de ejecución.
    Devuelve una lista de diccionarios con las keys esperadas por `create_task`.
    """
    import re
    from datetime import datetime

    try:
        import dateparser
    except Exception:
        dateparser = None

    def _fallback_parse(text: str) -> List[Dict]:
        """Heurística simple para extraer una tarea desde texto en NL.

        Devuelve una lista con al menos una tarea si detecta algo razonable.
        Campos de salida coinciden con lo que espera `create_task` a nivel de llaves.
        """
        t = text.strip()
        # Extraer prioridad
        prio_match = re.search(r"prioridad\s*[:]?\s*(alta|media|baja)", t, re.I)
        prioridad = prio_match.group(1).capitalize() if prio_match else "Media"

        # Extraer nivel de esfuerzo
        esfor_match = re.search(r"esfuerzo\s*[:]?\s*(alto|medio|bajo)", t, re.I)
        nivel_esfuerzo = esfor_match.group(1).capitalize() if esfor_match else "Medio"

        # Intentar extraer fecha con dateparser si está disponible
        fecha_entrega = None
        if dateparser:
            parsed = dateparser.parse(t, settings={"PREFER_DATES_FROM": "future"})
            if parsed:
                fecha_entrega = parsed.date().isoformat()

        # Extraer título: heurística simple
        title = None
        m = re.search(r"(tengo que|necesito|debo)?\s*(.+?)\s+para\b", t, re.I)
        if m:
            title = m.group(2).strip()
        else:
            m2 = re.search(r"(?:sobre|de)\s+([\w\s]+?)(?:\s+para|;|$)", t, re.I)
            if m2:
                title = m2.group(0).strip()
        if not title:
            parts = re.split(r"[.;]", t)
            title = parts[0].strip()

        # Normalizar campos a la forma esperada
        tarea = {
            "Titulo": title or "Tarea",
            "descripcion": "",
            "materia": "",
            "fecha_entrega": fecha_entrega or datetime.now().date().isoformat(),
            "prioridad": prioridad,
            "nivel_esfuerzo": nivel_esfuerzo,
        }

        return [tarea]

    # Intentar import dinámico del parser LLM
    parse_multiple_tasks_container = None
    try:
        from importlib import import_module
        mod = import_module('llm_test')
        parse_multiple_tasks_container = getattr(mod, 'parse_multiple_tasks_container', None)
    except Exception as e:
        parse_multiple_tasks_container = None

    if parse_multiple_tasks_container:
        try:
            container = parse_multiple_tasks_container(text, user_categories=user_categories, debug=debug)
            tareas = container.get("tareas", []) if isinstance(container, dict) else []
            if tareas:
                return tareas
        except Exception as e:
            if debug:
                print(f"LLM parser runtime error: {e}")

    # Fallback heurístico
    return _fallback_parse(text)
