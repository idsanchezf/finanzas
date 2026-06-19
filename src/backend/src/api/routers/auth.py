"""Router de Autenticacion — OAuth2 (Google) + JWT."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, status

from src.api.dependencies import (
    get_current_user_id,
    get_google_oauth_service,
    get_jwt_service,
    get_refresh_token_repo,
    get_usuario_repo,
)

router = APIRouter()


@router.post("/login")
async def login(
    body: dict = Body(...),
    jwt_svc: Any = Depends(get_jwt_service),
    google_svc: Any = Depends(get_google_oauth_service),
    usuario_repo: Any = Depends(get_usuario_repo),
    refresh_token_repo: Any = Depends(get_refresh_token_repo),
):
    """Inicia sesion con OAuth2 (Google).

    Recibe un id_token de Google, lo valida, busca/crea el usuario
    en la base de datos, y retorna access + refresh tokens JWT.

    Body esperado:
    ```json
    {
        "provider": "google",
        "id_token": "eyJ..."
    }
    ```

    En modo desarrollo (ENVIRONMENT=development), acepta id_token="dev-token"
    sin validar contra Google.
    """
    provider = body.get("provider", "").lower()
    id_token = body.get("id_token", "")

    if not provider or not id_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="provider e id_token son requeridos",
        )

    if provider != "google":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Proveedor no soportado: {provider}. Solo 'google' esta disponible.",
        )

    # 1. Validar id_token con Google OAuth2
    google_result = await google_svc.validate_id_token(id_token)

    if not google_result.get("valid"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token de Google invalido: {google_result.get('error', 'desconocido')}",
        )

    email = google_result["email"]
    nombre = google_result["nombre"]
    avatar_url = google_result.get("avatar_url")
    provider_id = google_result["provider_id"]

    # 2. Buscar o crear usuario en BD
    usuario = await usuario_repo.get_by_email(email)

    if not usuario:
        # Crear nuevo usuario
        from src.domain.entities.usuario import AuthProvider, Usuario

        nuevo_usuario = Usuario(
            email=email,
            nombre=nombre,
            avatar_url=avatar_url,
            auth_provider=AuthProvider.GOOGLE,
            auth_provider_id=provider_id,
        )
        usuario = await usuario_repo.save(nuevo_usuario)

    # 3. Generar tokens JWT
    user_id_str = str(usuario.id if hasattr(usuario, "id") else usuario["id"])
    user_email = usuario.email if hasattr(usuario, "email") else usuario.get("email", email)
    user_nombre = usuario.nombre if hasattr(usuario, "nombre") else usuario.get("nombre", nombre)
    user_avatar = (
        usuario.avatar_url
        if hasattr(usuario, "avatar_url")
        else usuario.get("avatar_url", avatar_url)
    )

    access_token = jwt_svc.generate_access_token(
        user_id=user_id_str,
        email=user_email,
        nombre=user_nombre,
    )

    # Decodificar refresh token para obtener su JTI y exp
    refresh_token = jwt_svc.generate_refresh_token(user_id=user_id_str)
    from jose import jwt

    refresh_payload = jwt.decode(
        refresh_token, jwt_svc.secret, algorithms=[jwt_svc.algorithm],
        options={"verify_exp": False},  # Permitimos decodificar sin validar exp
    )
    refresh_jti = refresh_payload["jti"]
    refresh_exp = datetime.fromtimestamp(refresh_payload["exp"], tz=UTC)

    # 4. Persistir refresh token para poder revocarlo
    await refresh_token_repo.save(
        usuario_id=uuid.UUID(user_id_str),
        token_jti=refresh_jti,
        expires_at=refresh_exp,
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": jwt_svc.access_token_ttl,
        "user": {
            "id": user_id_str,
            "nombre": user_nombre,
            "email": user_email,
            "avatar_url": user_avatar,
        },
    }


@router.post("/refresh")
async def refresh_token(
    body: dict = Body(...),
    jwt_svc: Any = Depends(get_jwt_service),
    refresh_token_repo: Any = Depends(get_refresh_token_repo),
    usuario_repo: Any = Depends(get_usuario_repo),
):
    """Renueva access token usando refresh token.

    Body esperado:
    ```json
    {
        "refresh_token": "eyJ..."
    }
    ```

    El refresh token debe ser valido (no expirado, no revocado en BD).
    Retorna un nuevo access token.
    """
    token_str = body.get("refresh_token", "")

    if not token_str:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="refresh_token es requerido",
        )

    # 1. Validar refresh token JWT
    try:
        payload = jwt_svc.validate_refresh_token(token_str)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Refresh token invalido o expirado: {str(e)}",
        ) from e

    token_jti = payload.get("jti", "")
    user_id = payload.get("sub", "")

    # 2. Verificar que el refresh token no fue revocado en BD
    stored = await refresh_token_repo.find_valid_by_jti(token_jti)
    if not stored:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token revocado o no encontrado",
        )

    # 3. Buscar usuario para obtener email y nombre
    usuario = await usuario_repo.get_by_id(uuid.UUID(user_id))
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
        )

    user_email = usuario.email if hasattr(usuario, "email") else usuario.get("email", "")
    user_nombre = usuario.nombre if hasattr(usuario, "nombre") else usuario.get("nombre", "")

    # 4. Rotacion de refresh token: revocar el viejo, generar uno nuevo
    await refresh_token_repo.revoke(token_jti)

    new_access = jwt_svc.generate_access_token(
        user_id=user_id, email=user_email, nombre=user_nombre
    )
    new_refresh = jwt_svc.generate_refresh_token(user_id=user_id)

    # Decodificar el nuevo refresh para obtener JTI y persistirlo
    from jose import jwt

    new_payload = jwt.decode(
        new_refresh, jwt_svc.secret, algorithms=[jwt_svc.algorithm],
        options={"verify_exp": False},
    )
    new_jti = new_payload["jti"]
    new_exp = datetime.fromtimestamp(new_payload["exp"], tz=UTC)

    await refresh_token_repo.save(
        usuario_id=uuid.UUID(user_id),
        token_jti=new_jti,
        expires_at=new_exp,
    )

    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
        "expires_in": jwt_svc.access_token_ttl,
    }


@router.post("/logout")
async def logout(
    body: dict = Body(...),
    jwt_svc: Any = Depends(get_jwt_service),
    refresh_token_repo: Any = Depends(get_refresh_token_repo),
):
    """Cierra sesion revocando el refresh token.

    Body esperado:
    ```json
    {
        "refresh_token": "eyJ..."
    }
    ```

    El refresh token se invalida en BD para que no pueda ser reutilizado.
    """
    token_str = body.get("refresh_token", "")

    if not token_str:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="refresh_token es requerido",
        )

    # Intentar extraer JTI sin validar expiracion para poder revocar siempre
    try:
        from jose import jwt as jose_jwt

        payload = jose_jwt.decode(
            token_str, jwt_svc.secret, algorithms=[jwt_svc.algorithm],
            options={"verify_exp": False},
        )
        token_jti = payload.get("jti", "")
        if token_jti:
            await refresh_token_repo.revoke(token_jti)
        # Si ademas se proporciono user_id, revocar TODOS los tokens del user
        user_id = body.get("user_id")
        if user_id:
            await refresh_token_repo.revoke_all_for_user(uuid.UUID(user_id))
    except Exception:
        # Si el token es invalido, igual decimos que el logout fue exitoso
        pass

    return {"status": "logged_out"}


@router.get("/me")
async def get_me(
    user_id: str = Depends(get_current_user_id),
    usuario_repo: Any = Depends(get_usuario_repo),
):
    """Datos del usuario autenticado."""
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        # En desarrollo, user_id puede no ser UUID
        return {
            "id": user_id,
            "nombre": "Dev User",
            "email": "dev@financereport.local",
            "avatar_url": None,
            "tarjetas": [],
        }

    usuario = await usuario_repo.get_by_id(uid)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    # Extraer atributos (maneja tanto ORM como domain entity)
    def _attr(obj, name, default=None):
        if hasattr(obj, name):
            return getattr(obj, name)
        if isinstance(obj, dict):
            return obj.get(name, default)
        return default

    return {
        "id": str(_attr(usuario, "id", uid)),
        "nombre": _attr(usuario, "nombre", "Usuario"),
        "email": _attr(usuario, "email", ""),
        "avatar_url": _attr(usuario, "avatar_url"),
        "tarjetas": [],  # TODO: Incluir tarjetas del usuario
    }


@router.post("/2fa/enable")
async def enable_2fa(user_id: str = Depends(get_current_user_id)):
    """Habilita 2FA TOTP. Retorna QR code. (No implementado aun)"""
    return {
        "secret": "placeholder-totp-secret",
        "qr_code_url": "otpauth://totp/FinanceReport:user?secret=XXX",
    }


@router.post("/2fa/verify")
async def verify_2fa(body: dict = Body(...)):
    """Verifica y activa 2FA. (No implementado aun)"""
    return {"status": "verified"}
