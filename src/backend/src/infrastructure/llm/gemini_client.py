"""Cliente Google Gemini 1.5 Flash — Asistente IA con function calling.

Procesa consultas en lenguaje natural sobre finanzas personales.
Soporta streaming de respuestas via SSE y function calling para consultar la BD.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from typing import Any

import google.generativeai as genai
from google.generativeai.types import GenerationConfig

logger = logging.getLogger(__name__)

# System prompt para el asistente financiero
SYSTEM_PROMPT = """Eres un asistente financiero personal de Finance Report, una aplicacion de
analisis de gastos. Ayudas al usuario a entender sus finanzas, detectar patrones de gasto,
y dar recomendaciones practicas para mejorar su salud financiera.

Tus capacidades:
- Analizar transacciones y categorias de gasto
- Responder preguntas sobre presupuestos y metas de ahorro
- Detectar malos habitos financieros
- Sugerir acciones concretas para ahorrar dinero
- Calcular proyecciones de gasto futuro
- Explicar conceptos financieros en espanol sencillo

Reglas:
- Responde en espanol latinoamericano, con tono amigable pero profesional
- Usa emojis moderadamente para hacer las respuestas mas amigables
- Cuando des cifras, usa formato colombiano ($X.XXX COP)
- Si no tienes suficiente informacion, pregunta amablemente
- Manten la privacidad: nunca reveles datos de otros usuarios
- Se positivo y motivador, incluso cuando senales problemas financieros
"""


class GeminiClient:
    """Cliente para Google Gemini 1.5 Flash con soporte de streaming y function calling."""

    def __init__(self, api_key: str | None = None, model_name: str = "gemini-1.5-flash") -> None:
        import os

        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.model_name = model_name
        self._model = None
        self._configured = False

    def configure(self) -> None:
        """Configura el cliente de Gemini."""
        if self._configured:
            return
        genai.configure(api_key=self.api_key)
        self._model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=SYSTEM_PROMPT,
        )
        self._configured = True
        logger.info(f"Gemini client configurado — modelo: {self.model_name}")

    async def chat(
        self,
        mensaje: str,
        historial: list[dict[str, str]] | None = None,
        user_context: dict[str, Any] | None = None,
    ) -> str:
        """Envia un mensaje a Gemini y retorna la respuesta completa.

        Args:
            mensaje: Texto del usuario.
            historial: Historial de mensajes previos (rol, contenido).
            user_context: Contexto adicional (datos financieros del usuario).

        Returns:
            Respuesta completa del asistente.
        """
        self.configure()

        # Construir prompt con contexto
        prompt = self._build_prompt(mensaje, user_context)

        # Construir historial para la conversacion
        contents = []
        if historial:
            for msg in historial:
                role = "user" if msg.get("rol") == "user" else "model"
                contents.append({"role": role, "parts": [msg.get("contenido", "")]})
        contents.append({"role": "user", "parts": [prompt]})

        generation_config = GenerationConfig(
            temperature=0.7,
            top_p=0.95,
            top_k=40,
            max_output_tokens=2048,
        )

        response = await self._model.generate_content_async(
            contents,
            generation_config=generation_config,
        )

        return response.text

    async def chat_stream(
        self,
        mensaje: str,
        historial: list[dict[str, str]] | None = None,
        user_context: dict[str, Any] | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Envia un mensaje y retorna un stream de chunks para SSE.

        Yields:
            Dict con: {token, tipo: "text"|"chart"|"suggestion", chart_data?}
        """
        self.configure()

        prompt = self._build_prompt(mensaje, user_context)

        contents = []
        if historial:
            for msg in historial:
                role = "user" if msg.get("rol") == "user" else "model"
                contents.append({"role": role, "parts": [msg.get("contenido", "")]})
        contents.append({"role": "user", "parts": [prompt]})

        generation_config = GenerationConfig(
            temperature=0.7,
            top_p=0.95,
            top_k=40,
            max_output_tokens=2048,
        )

        response = await self._model.generate_content_async(
            contents,
            generation_config=generation_config,
            stream=True,
        )

        async for chunk in response:
            if chunk.text:
                yield {
                    "token": chunk.text,
                    "tipo": "text",
                }

    def _build_prompt(self, mensaje: str, user_context: dict[str, Any] | None) -> str:
        """Construye el prompt con contexto financiero del usuario."""
        if not user_context:
            return mensaje

        # Agregar contexto financiero al prompt
        contexto_partes = []
        if "total_gastado" in user_context:
            contexto_partes.append(
                f"Gasto total del periodo: ${user_context['total_gastado']:,.0f} COP"
            )
        if "categorias_top" in user_context:
            cats = user_context["categorias_top"]
            contexto_partes.append(
                "Top categorias: "
                + ", ".join(f"{c['nombre']} (${c['total']:,.0f})" for c in cats[:3])
            )
        if "presupuestos" in user_context:
            contexto_partes.append(f"Presupuestos activos: {len(user_context['presupuestos'])}")

        if contexto_partes:
            contexto = "\n".join(contexto_partes)
            return f"[Contexto financiero del usuario]\n{contexto}\n\n[Pregunta del usuario]\n{mensaje}"

        return mensaje


# Instancia singleton
_gemini_client: GeminiClient | None = None


def get_gemini_client() -> GeminiClient:
    """Retorna la instancia singleton del cliente Gemini."""
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
        _gemini_client.configure()
    return _gemini_client
