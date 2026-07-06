"""Google OAuth2 Service — Validacion de id_token de Google.

Usa la API publica de Google tokeninfo para validar el id_token
sin necesidad de instalar google-auth ni dependencias pesadas.

En modo desarrollo (ENVIRONMENT=development), acepta un token de
desarrollo sin validacion real contra Google.
"""

from __future__ import annotations

import os
from typing import Any

import httpx

# URL publica de Google para validar tokens
GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"


class GoogleOAuthService:
    """Servicio que valida id_tokens de Google OAuth2."""

    def __init__(self, client_id: str | None = None) -> None:
        self.client_id = client_id or os.getenv("GOOGLE_CLIENT_ID", "")
        self._http_client: httpx.AsyncClient | None = None

    async def _get_http_client(self) -> httpx.AsyncClient:
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=10.0)
        return self._http_client

    async def _fetch_token_info(self, id_token: str) -> dict[str, Any]:
        """Llama a la API de Google tokeninfo para validar el id_token.

        API: GET https://oauth2.googleapis.com/tokeninfo?id_token={TOKEN}

        Args:
            id_token: El token JWT emitido por Google OAuth2.

        Returns:
            Diccionario con los claims del token (email, sub, name, picture, etc.).

        Raises:
            Exception: Si la API de Google no responde o retorna error.
        """
        client = await self._get_http_client()
        response = await client.get(
            GOOGLE_TOKENINFO_URL,
            params={"id_token": id_token},
        )
        response.raise_for_status()
        payload = response.json()

        if "error" in payload:
            raise Exception(
                f"Google tokeninfo error: {payload.get('error_description', payload['error'])}"
            )

        return payload

    async def validate_id_token(self, id_token: str) -> dict[str, Any]:
        """Valida un id_token de Google OAuth2 y extrae la info del usuario.

        Args:
            id_token: Token JWT emitido por Google Sign-In.

        Returns:
            Diccionario con:
                - valid (bool): True si el token es valido.
                - email, nombre, avatar_url, provider, provider_id (si valido).
                - error (str): Mensaje de error si no es valido.
        """
        # Modo desarrollo: aceptar token "dev-token" sin validar
        if os.getenv("ENVIRONMENT", "production") == "development" and (
            id_token == "dev-token" or id_token.startswith("dev-")
        ):
            return {
                "valid": True,
                "email": "dev@financereport.local",
                "nombre": "Dev User",
                "avatar_url": None,
                "provider": "google",
                "provider_id": "dev-google-id",
            }

        try:
            payload = await self._fetch_token_info(id_token)

            # Validar issuer
            iss = payload.get("iss", "")
            if "accounts.google.com" not in iss and "https://accounts.google.com" not in iss:
                return {"valid": False, "error": "Issuer invalido: no es de Google"}

            # Validar email verificado
            email_verified = payload.get("email_verified", "false")
            if str(email_verified).lower() != "true":
                return {"valid": False, "error": "Email no verificado por Google"}

            # Validar audience (client_id) si esta configurado
            aud = payload.get("aud", "")
            if self.client_id and aud != self.client_id:
                return {"valid": False, "error": "Audience no coincide con el client_id"}

            return {
                "valid": True,
                "email": payload.get("email", ""),
                "nombre": payload.get("name", payload.get("email", "").split("@")[0]),
                "avatar_url": payload.get("picture"),
                "provider": "google",
                "provider_id": payload.get("sub", ""),
            }

        except Exception as e:
            return {"valid": False, "error": str(e)}
