MODEL_PATH = "/home/tumbadoboy/UNIVERSIDAD/Topicos/llm-test/Meta-Llama-3.1-8B-Instruct-Q4_K_L.gguf"

# Carga perezosa del modelo para que el módulo pueda importarse sin inicializar
# el LLM en el momento de la importación (evita errores si el modelo no existe
# o si se desea inicializar bajo demanda).
_llm = None
def get_llm():
    global _llm
    if _llm is None:
        from llama_cpp import Llama
        _llm = Llama(
            model_path=MODEL_PATH,
            n_gpu_layers=0,
            n_ctx=4096,
            verbose=False
        )
        print("Modelo cargado correctamente.")
    return _llm


import json
import re
import spacy
from datetime import datetime, timedelta
import dateparser

DEBUG_TODAY = datetime(2025, 11, 23)

# ======== Cargar spaCy ========
nlp = spacy.load("es_core_news_md")


# ---------------------------------------
# Detectar categoría automática con spaCy
# ---------------------------------------
def detect_category_spacy(text, categories):
    """
    Recibe texto y lista de categorías del usuario.
    Devuelve la categoría más parecida según similitud semántica.
    """
    if not categories:
        return None

    doc = nlp(text)
    best_cat = None
    best_score = 0.0

    for cat in categories:
        cat_doc = nlp(cat)
        sim = doc.similarity(cat_doc)
        if sim > best_score:
            best_score = sim
            best_cat = cat

    # Umbral mínimo para considerar que realmente coincide
    return best_cat if best_score > 0.55 else None



# ----------------------------
#  Detectar días tipo "el siguiente martes"
# ----------------------------
WEEKDAYS = {
    "lunes": 0,
    "martes": 1,
    "miércoles": 2,
    "miercoles": 2,
    "jueves": 3,
    "viernes": 4,
    "sábado": 5,
    "sabado": 5,
    "domingo": 6,
}



def detect_relative_weekday(text, base):
    pattern = r"(el|para|este|siguiente|pr[oó]ximo)\s+(lunes|martes|mi[eé]rcoles|jueves|viernes|s[aá]bado|domingo)"
    match = re.search(pattern, text, re.I)
    if not match:
        return None

    _, weekday = match.groups()
    weekday = weekday.lower()
    target = WEEKDAYS[weekday]

    today_idx = base.weekday()

    days_ahead = (target - today_idx) % 7
    if days_ahead == 0:
        days_ahead = 7

    return base + timedelta(days=days_ahead)



# ---------------------------------------
#  Parser de fechas
# ---------------------------------------
def normalize_dates(task_text):
    base = DEBUG_TODAY

    weekday_date = detect_relative_weekday(task_text, base)
    if weekday_date:
        return weekday_date, weekday_date

    week_next = re.search(r"(la\s+)?(siguiente|pr[oó]xima)\s+semana", task_text, re.I)
    if week_next:
        start = base + timedelta(days=7 - base.weekday())
        end = start + timedelta(days=6)
        return start, end

    month_next = re.search(r"(el\s+)?pr[oó]ximo\s+mes", task_text, re.I)
    if month_next:
        next_month = (base.replace(day=1) + timedelta(days=32)).replace(day=1)
        end_month = (next_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        return next_month, end_month

    parsed = dateparser.parse(task_text, settings={"RELATIVE_BASE": base})
    if parsed:
        return parsed.date(), None

    return None, None



# ---------------------------------------
# Extraer JSON
# ---------------------------------------
def extract_first_json(text):
    matches = re.findall(r"\{.*?\}", text, flags=re.DOTALL)
    for m in matches:
        try:
            return json.loads(m)
        except:
            pass
    raise ValueError("No se encontró JSON válido.")



# ---------------------------------------
# parser principal
# ---------------------------------------
def parse_task(task_text, user_categories=None, debug=False):
    if user_categories is None:
        user_categories = []

    # 1. FECHAS
    start_date_obj, end_date_obj = normalize_dates(task_text)

    start_pre = start_date_obj.strftime("%Y-%m-%d") if start_date_obj else None
    end_pre = end_date_obj.strftime("%Y-%m-%d") if end_date_obj else None

    # 2. CATEGORÍA spaCy
    spacy_detected = detect_category_spacy(task_text, user_categories)

    # 3. SYSTEM PROMPT
    allowed_materias = ", ".join([f'"{c}"' for c in user_categories]) if user_categories else ""

    system_prompt = f"""
RESPONDE EXCLUSIVAMENTE con un objeto JSON válido.
NO incluyas explicaciones, texto adicional, ni código.
NO uses bloques de código (```).
Solo devuelve JSON.
Eres un sistema de clasificación. Tu única salida debe ser un JSON válido que cumpla exactamente con este esquema.

Reglas:
- La fecha será la ya detectada.
- La materia permitida: [{allowed_materias}]
- NO generes texto fuera del JSON.
-Si el usuario menciona varias tareas, devuelve un JSON por cada una,
pero cada JSON debe estar en una única línea,
sin texto entre ellos, sin barras "|" ni opciones alternativas.


Fechas detectadas:
start_date_pre = {start_pre}
end_date_pre   = {end_pre}

Materia detectada por spaCy: {spacy_detected}

Descripción del usuario: "{task_text}"
FORMATO DE SALIDA OBLIGATORIO:
{{
    "Titulo": "string",
    "descripcion": "string",
    "materia": "string",
    "fecha_entrega": "YYYY-MM-DD",
    "prioridad": "Alta" | "Media" | "Baja",
    "nivel_esfuerzo": "Alto" | "Medio" | "Bajo"
}}
"""

    llm_instance = get_llm()
    result = llm_instance(system_prompt, max_tokens=256, temperature=0)
    raw = result["choices"][0]["text"].strip()

    if debug:
        print(raw)

    data = extract_first_json(raw)

    # Forzar fecha correcta
    if start_pre:
        fecha_final = start_pre
    elif end_pre:
        fecha_final = end_pre
    else:
        fecha_final = DEBUG_TODAY.strftime("%Y-%m-%d")

    data["fecha_entrega"] = fecha_final

    # Forzar categoría final fusionando spaCy con LLM
    if spacy_detected:
        data["materia"] = spacy_detected
    
    return data




# # ------------ PRUEBA ---------------

# parse_task(
#      "Tengo que hacer una tarea de descenso de gradiente para IA para el siguiente martes, no es muy importante, pero requiere de mucha investigación y tambien debo hacer una tarea de calculo para el miercoles de la siguiente semana",
#       user_categories=["Inteligencia Artificial", "Cálculo", "Redes", "Matemáticas"],
#       debug=False
# )

def parse_multiple_tasks_container(task_text, user_categories=None, debug=False):
    # Dividir el texto en posibles tareas
    fragments = re.split(r",\s*pero|y también debo|;|\.", task_text)
    fragments = [f.strip() for f in fragments if f.strip()]

    results = []
    for frag in fragments:
        try:
            res = parse_task(frag, user_categories=user_categories, debug=debug)
            results.append(res)
        except Exception as e:
            if debug:
                print(f"Error con fragmento: {frag}\n{e}")
    
    # Envolver en un JSON contenedor
    container = {"tareas": results}
    json_text = json.dumps(container, ensure_ascii=False)
    print(json_text)
    return container


# ------------ PRUEBA ---------------
if __name__ == "__main__":
    parse_multiple_tasks_container(
        "Tengo que hacer una tarea de descenso de gradiente para IA para el siguiente martes, no es muy importante, pero requiere de mucha investigación y tambien debo hacer una tarea de calculo para el miercoles de la siguiente semana",
        user_categories=["Inteligencia Artificial", "Cálculo", "Redes", "Matemáticas"],
        debug=False
    )

