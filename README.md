# Gototion — Telegram → Notion task helper

Breve guía para configurar y ejecutar el bot que transforma mensajes en tareas y las guarda en Notion. Incluye soporte por lenguaje natural usando Gemini (API) o un parser local (llama.cpp), y un fallback heurístico.

**Requisitos**
- Python 3.11+ (se recomendó 3.12 en el entorno conda).
- Conda (opcional) o pip en un virtualenv.

**Archivos importantes**
- `main.py`: arranca el bot.
- `bot/`: código del bot (handlers, client, parsers).
- `notion/`: cliente y servicios para la integración con Notion.
- `llm_test.py`: parser local basado en `llama-cpp-python` y spaCy.
- `env.yaml`: archivo de entorno (conda) sugerido para reproducir dependencias.

**Variables de entorno (archivo `.env`)**
Coloca un archivo `.env` en la raíz del proyecto con al menos las variables:

```
BOT_TK=<tu_token_telegram>
BOT_USERNAME=@TuBotUsername
NOTION_API_KEY=<tu_notion_integration_token>
NOTION_DATABASE_ID=<tu_database_id>
# Opcional: si usas Gemini
GEMINI_API_KEY=<tu_gemini_api_key>
```

**Instalación rápida (recomendada con conda)**

1) Crear el entorno desde `env.yaml` (si usas conda):

```bash
conda env create -f env.yaml
conda activate gototion312
```


Nota: `llama-cpp-python` requiere que tengas un runtime compatible (libllama/ggml/gguf). Si vas a usar un modelo local, coloca el archivo `.gguf` y ajusta `MODEL_PATH` en `llm_test.py`.

**Run (modo desarrollo)**

1) Asegúrate de que `.env` está presente y correcto.
2) Ejecuta:

```bash
python main.py
```

El bot usará polling (según `main.py`) y registrará mensajes de debug en la terminal indicando qué backend de parsing usó: Gemini, LLM local o fallback heurístico.

**Probar el flujo**
- Envía `/crear_tarea` en Telegram. A continuación puedes enviar:
  - Formato por comas (6 campos): `Titulo, Descripción, Materia, 2025-12-01, alta, medio`
  - Lenguaje natural: `Tengo que preparar la presentación sobre redes neuronales para el siguiente martes; prioridad alta.`
