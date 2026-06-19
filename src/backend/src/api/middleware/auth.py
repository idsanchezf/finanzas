"""Middleware de autenticacion — Validacion de JWT Bearer tokens."""

from __future__ import annotations

import os

from fastapi import HTTPException, Request, status
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware que valida JWT en cada request (excepto rutas publicas).

    Rutas publicas (sin autenticacion):
    - /health, /health/ready
    - /docs, /redoc, /openapi.json
    - POST /api/v1/auth/login
    - POST /api/v1/auth/refresh
    """

    PUBLIC_PATHS = {
        "/health",
        "/health/ready",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/auth/login",
        "/api/v1/auth/refresh",
        "/api/v1/auth/logout",
    }

    async def dispatch(self, request: Request, call_next):
        # Rutas publicas: pasar sin validacion
        if request.url.path in self.PUBLIC_PATHS or request.url.path.startswith("/docs"):
            return await call_next(request)

        # Validar token
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            # En desarrollo, permitir sin token
            if os.getenv("ENVIRONMENT") == "development":
                request.state.user_id = "dev-user-id"
                return await call_next(request)

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de autenticacion requerido",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = auth_header.replace("Bearer ", "")

        try:
            secret = os.getenv("JWT_SECRET", "dev-secret")
            payload = jwt.decode(token, secret, algorithms=["HS256"])
            request.state.user_id = payload.get("sub", "unknown")
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token invalido o expirado: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            ) from e

        return await call_next(request)
