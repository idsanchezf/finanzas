"""Router de Autenticacion — OAuth2 (Google/Microsoft) + JWT."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, status

from src.api.dependencies import get_current_user_id, get_usuario_repo

router = APIRouter()


@router.post("/login")
async def login(body: dict = Body(...)):
    """Inicia sesion con OAuth2 (Google/Microsoft).

    Intercambia token del proveedor por JWT propio.
    """
    provider = body.get("provider")
    id_token = body.get("id_token")

    if not provider or not id_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="provider e id_token son requeridos",
        )

    # TODO: Validar id_token con el proveedor OAuth2
    # TODO: Buscar/crear usuario en BD
    # TODO: Generar JWT propio

    return {
        "access_token": "placeholder-jwt-token",
        "refresh_token": "placeholder-refresh-token",
        "expires_in": 1800,
        "user": {
            "id": "user-id",
            "nombre": "Usuario",
            "email": "usuario@email.com",
        },
    }


@router.post("/refresh")
async def refresh_token(body: dict = Body(...)):
    """Renueva access token usando refresh token."""
    return {
        "access_token": "placeholder-new-jwt",
        "expires_in": 1800,
    }


@router.get("/me")
async def get_me(
    user_id: str = Depends(get_current_user_id),
    usuario_repo: Any = Depends(get_usuario_repo),
):
    """Datos del usuario autenticado."""
    usuario = await usuario_repo.get_by_id(uuid.UUID(user_id))
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    return {
        "id": str(usuario.id),
        "nombre": usuario.nombre,
        "email": usuario.email,
        "avatar_url": usuario.avatar_url,
        "tarjetas": [],  # TODO: Incluir tarjetas del usuario
    }


@router.post("/2fa/enable")
async def enable_2fa(user_id: str = Depends(get_current_user_id)):
    """Habilita 2FA TOTP. Retorna QR code."""
    return {
        "secret": "placeholder-totp-secret",
        "qr_code_url": "otpauth://totp/FinanceReport:user?secret=XXX",
    }


@router.post("/2fa/verify")
async def verify_2fa(body: dict = Body(...)):
    """Verifica y activa 2FA."""
    return {"status": "verified"}
