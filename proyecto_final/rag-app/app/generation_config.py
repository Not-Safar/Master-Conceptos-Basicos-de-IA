from google.genai import types

from app.config import Settings


def generation_config(settings: Settings, system: str, schema) -> types.GenerateContentConfig:
    options = {"system_instruction": system, "response_mime_type": "application/json",
               "response_schema": schema}
    if settings.generation_model == "gemini-3.8-flash":
        # Gemini 3.8 retira temperature/top_p/top_k. Low reduce latencia sin
        # truncar el JSON mediante un limite pequeno de tokens de salida.
        options["thinking_config"] = types.ThinkingConfig(thinking_level=settings.generation_thinking_level)
    else:
        options["temperature"] = 0
    return types.GenerateContentConfig(**options)
