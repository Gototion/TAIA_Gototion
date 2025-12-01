"""Parser de tareas en lenguaje natural con múltiples backends.

Intenta usar en orden:
1. API de Gemini (si GEMINI_API_KEY está disponible)
2. LLM local (si llm_test.py funciona)
3. Fallback heurístico (siempre disponible)
"""

from typing import List, Dict, Optional
import re
from datetime import datetime
import os

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


def parse_tasks_natural(text: str, user_categories: Optional[List[str]] = None, debug: bool = False) -> List[Dict]:
    """Parsea `text` en una lista de tareas usando múltiples backends en orden de preferencia.

    Intenta (en orden):
    1. Gemini API (si GEMINI_API_KEY disponible)
    2. LLM local (llm_test.py)
    3. Fallback heurístico (siempre funciona)

    Args:
        text: Texto en lenguaje natural
        user_categories: Lista opcional de categorías/materias del usuario
        debug: Si True, imprime logs de debugging

    Returns:
        Lista de diccionarios con estructura esperada por create_task
    """
    print(f"\n[LLM PARSER] Iniciando parsing de: '{text[:80]}...'")
    
    # 1. Intentar Gemini API primero
    has_gemini_key = os.getenv("GEMINI_API_KEY") is not None
    print(f"[LLM PARSER] ¿GEMINI_API_KEY disponible? {has_gemini_key}")
    
    if has_gemini_key:
        print("[LLM PARSER] 🔄 Intentando Gemini API...")
        try:
            from bot.gemini_parser import parse_tasks_gemini
            tareas = parse_tasks_gemini(text, user_categories=user_categories, debug=debug, debug_today=datetime.now())
            if tareas:
                print(f"[LLM PARSER] ✅ GEMINI API: Extraídas {len(tareas)} tarea(s)")
                return tareas
            else:
                print("[LLM PARSER] ⚠️  Gemini devolvió lista vacía")
        except Exception as e:
            print(f"[LLM PARSER] ❌ Gemini error: {type(e).__name__}: {str(e)[:100]}")

    # 2. Intentar LLM local (llm_test.py)
    print("[LLM PARSER] 🔄 Intentando LLM local...")
    try:
        from importlib import import_module
        mod = import_module('llm_test')
        print("[LLM PARSER]   ✓ llm_test.py importado")
        parse_multiple_tasks_container = getattr(mod, 'parse_multiple_tasks_container', None)
        
        if parse_multiple_tasks_container:
            print("[LLM PARSER]   ✓ parse_multiple_tasks_container encontrada")
            container = parse_multiple_tasks_container(text, user_categories=user_categories, debug=debug)
            tareas = container.get("tareas", []) if isinstance(container, dict) else []
            if tareas:
                print(f"[LLM PARSER] ✅ LLM LOCAL: Extraídas {len(tareas)} tarea(s)")
                return tareas
            else:
                print("[LLM PARSER] ⚠️  LLM local devolvió lista vacía")
    except Exception as e:
        print(f"[LLM PARSER] ❌ LLM local error: {type(e).__name__}: {str(e)[:100]}")

    # 3. Fallback heurístico
    print("[LLM PARSER] 🔄 Usando fallback heurístico...")
    result = _fallback_parse(text)
    print(f"[LLM PARSER] ✅ FALLBACK: Extraídas {len(result)} tarea(s)")
    return result
