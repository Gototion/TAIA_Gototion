"""Integración con la API de Google Gemini para parsear tareas en lenguaje natural.

Usa la variable de entorno GEMINI_API_KEY para autenticar.
"""

import os
import json
import re
from typing import List, Dict, Optional
from datetime import datetime

try:
    import google.generativeai as genai
except ImportError:
    genai = None


def _initialize_gemini():
    """Inicializa el cliente de Gemini con la API key del entorno."""
    if genai is None:
        raise RuntimeError(
            "google.generativeai no está instalado. Instálalo con: pip install google-generativeai"
        )

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY no encontrada en variables de entorno")

    genai.configure(api_key=api_key)


def parse_tasks_gemini(text: str, user_categories: Optional[List[str]] = None, debug: bool = False, debug_today: Optional[datetime] = None) -> List[Dict]:
    """Parsea `text` usando la API de Gemini.

    Envía un prompt a Gemini pidiendo que devuelva JSON con las tareas detectadas.
    Devuelve una lista de diccionarios con las claves esperadas por `create_task`.

    Args:
        text: Texto en lenguaje natural con una o más tareas.
        user_categories: Lista opcional de categorías/materias del usuario.
        debug: Si True, imprime la salida cruda del modelo.
        debug_today: datetime actual para cálculo de fechas relativas. Si es None, usa hoy.

    Returns:
        Lista de diccionarios con estructura:
        {"Titulo": str, "descripcion": str, "materia": str, "fecha_entrega": str (YYYY-MM-DD),
         "prioridad": str (Alta/Media/Baja), "nivel_esfuerzo": str (Alto/Medio/Bajo)}

    Raises:
        RuntimeError si google.generativeai no está disponible o GEMINI_API_KEY falta.
    """
    if debug_today is None:
        debug_today = datetime.now()
    
    try:
        _initialize_gemini()
    except (RuntimeError, ValueError) as e:
        raise RuntimeError(f"Error inicializando Gemini: {e}")

    # Preparar categorías permitidas para el prompt
    allowed_materias = ", ".join([f'"{c}"' for c in user_categories]) if user_categories else ""
    today_str = debug_today.strftime("%Y-%m-%d")

    system_prompt = f"""Eres un sistema experto en clasificación de tareas académicas.
Tu tarea es parsear texto en lenguaje natural y extraer tareas académicas.

INSTRUCCIONES CRÍTICAS:
1. Responde EXCLUSIVAMENTE con un JSON válido.
2. NO incluyas explicaciones, texto adicional ni código.
3. NO uses bloques de código (```).
4. Si el usuario menciona múltiples tareas, devuelve un array JSON.
5. Cada campo debe contener valores válidos según el esquema.

Categorías/Materias permitidas (si se mencionan): [{allowed_materias}]
Si no se menciona explícitamente una materia, déjala vacía.

FECHA ACTUAL DE REFERENCIA: {today_str}
Usa esta fecha como base para calcular fechas relativas (ej: "el próximo martes", "la siguiente semana", etc).

FORMATO DE SALIDA OBLIGATORIO:
{{
  "tareas": [
    {{
      "Titulo": "Título corto de la tarea",
      "descripcion": "Descripción detallada",
      "materia": "Materia o categoría",
      "fecha_entrega": "YYYY-MM-DD",
      "prioridad": "Alta", "Media" o "Baja"
      "nivel_esfuerzo": "Medio", "Alto" o "Bajo"
    }}
  ]
}}

Valores válidos:
- prioridad: "Alta", "Media", "Baja"
- nivel_esfuerzo: "Alto", "Medio", "Bajo"
- fecha_entrega: formato ISO 8601 (YYYY-MM-DD). Si el usuario menciona una fecha relativa, calcúlala basándote en {today_str}. En caso de que el usuario no especifique una fecha, asume que es {today_str}.

Entrada del usuario:
"{text}"

Devuelve SOLO JSON válido."""

    try:
        print("[GEMINI PARSER] 📤 Enviando prompt a Gemini API...")
        model = genai.GenerativeModel("gemini-2.0-flash-lite")
        response = model.generate_content(system_prompt)
        raw_response = response.text.strip()
        print("[GEMINI PARSER] 📥 Respuesta recibida de Gemini")

        if True:
            print(f"[GEMINI PARSER] Raw Response:\n{raw_response}\n")

        # Extraer JSON de la respuesta
        json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
        if not json_match:
            print("[GEMINI PARSER] ❌ No se encontró JSON en la respuesta")
            raise ValueError("No se encontró JSON en la respuesta de Gemini")

        parsed_json = json.loads(json_match.group(0))
        tareas = parsed_json.get("tareas", [])
        print(f"[GEMINI PARSER] ✅ JSON parseado correctamente: {len(tareas)} tarea(s)")

        return tareas if isinstance(tareas, list) else [tareas]

    except Exception as e:
        print(f"[GEMINI PARSER] ❌ Error: {type(e).__name__}: {str(e)[:100]}")
        if debug:
            print(f"[GEMINI PARSER] Detalles completos: {e}")
        raise RuntimeError(f"Error al procesar con Gemini: {e}")
