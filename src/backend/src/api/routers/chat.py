"""Router de Chat IA — Asistente financiero con Gemini (SSE streaming)."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from src.api.dependencies import get_current_user_id, get_gemini

router = APIRouter()


@router.post("")
async def chat(
    body: dict = Body(...),
    user_id: str = Depends(get_current_user_id),
    gemini: Any = Depends(get_gemini),
):
    """Consulta en lenguaje natural con streaming SSE.

    El frontend consume el stream via EventSource.
    Cada chunk contiene: {token, tipo: "text"|"chart"|"suggestion", chart_data?}
    """
    mensaje = body.get("mensaje", "")
    session_id = body.get("session_id")

    if not mensaje:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="mensaje es requerido",
        )

    async def event_stream():
        """Genera el stream SSE para el frontend."""
        try:
            async for chunk in gemini.chat_stream(
                mensaje=mensaje,
                user_context={"user_id": user_id},
            ):
                # Formato SSE: "data: {json}\\n\\n"
                import json
                yield f"data: {json.dumps(chunk)}\\n\\n"
        except Exception as e:
            import json
            yield f"data: {json.dumps({'token': f'Error: {str(e)}', 'tipo': 'error'})}\\n\\n"

        # Senal de fin de stream
        yield "data: [DONE]\\n\\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/sessions")
async def list_chat_sessions(user_id: str = Depends(get_current_user_id)):
    """Historial de sesiones de chat del usuario."""
    return {
        "items": [],
        "message": "Historial de chat — proximamente",
    }


@router.get("/sessions/{session_id}")
async def get_chat_session(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Mensajes de una sesion de chat."""
    return {"items": []}


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_session(session_id: str):
    """Elimina una sesion de chat."""
    pass
