"""Cliente Redis — Cache de dashboards, sesiones y rate limiting.

Usa redis-py async para conexion con Redis (Upstash o local).
Keys con TTL para evitar datos stale.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class RedisClient:
    """Cliente Redis async para cache y rate limiting.

    Patrones de key:
    - dashboard:{user_id}:{extract_id}:summary (TTL 60s)
    - session:{session_id} (TTL 30d)
    - rate_limit:{user_id} (token bucket)
    - merchant_translate:{nombre} (TTL 24h)
    - exchange_rate:{from}:{to}:{date} (TTL 24h)
    """

    def __init__(self, url: str = "redis://localhost:6379/0") -> None:
        import os

        self.url = url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._redis: redis.Redis | None = None

    async def connect(self) -> None:
        """Establece conexion con Redis."""
        self._redis = redis.from_url(
            self.url,
            encoding="utf-8",
            decode_responses=True,
        )
        await self._redis.ping()
        logger.info(f"Redis conectado: {self.url}")

    async def disconnect(self) -> None:
        """Cierra la conexion con Redis."""
        if self._redis:
            await self._redis.close()
            logger.info("Redis desconectado")

    @property
    def client(self) -> redis.Redis:
        if self._redis is None:
            raise RuntimeError("Redis no conectado. Llama a connect() primero.")
        return self._redis

    # ---------------------------------------------------------------
    # Cache operations
    # ---------------------------------------------------------------
    async def get_cached(self, key: str) -> dict | None:
        """Obtiene un valor cacheado como dict."""
        value = await self.client.get(key)
        if value:
            return json.loads(value)
        return None

    async def set_cached(self, key: str, value: dict | list, ttl: int = 60) -> None:
        """Guarda un valor en cache con TTL."""
        await self.client.setex(key, ttl, json.dumps(value, default=str))
        logger.debug(f"Cache SET: {key} (TTL={ttl}s)")

    async def invalidate(self, key: str) -> None:
        """Invalida una entrada de cache."""
        await self.client.delete(key)
        logger.debug(f"Cache INVALIDATE: {key}")

    async def invalidate_pattern(self, pattern: str) -> None:
        """Invalida todas las keys que coinciden con un patron."""
        keys = await self.client.keys(pattern)
        if keys:
            await self.client.delete(*keys)
            logger.debug(f"Cache INVALIDATE pattern '{pattern}': {len(keys)} keys")

    # ---------------------------------------------------------------
    # Dashboard cache helpers
    # ---------------------------------------------------------------
    async def get_dashboard_summary(self, user_id: str, extract_id: str) -> dict | None:
        key = f"dashboard:{user_id}:{extract_id}:summary"
        return await self.get_cached(key)

    async def set_dashboard_summary(
        self, user_id: str, extract_id: str, data: dict, ttl: int = 60
    ) -> None:
        key = f"dashboard:{user_id}:{extract_id}:summary"
        await self.set_cached(key, data, ttl)

    async def get_dashboard_by_category(self, user_id: str, extract_id: str) -> dict | None:
        key = f"dashboard:{user_id}:{extract_id}:by_category"
        return await self.get_cached(key)

    async def set_dashboard_by_category(
        self, user_id: str, extract_id: str, data: dict, ttl: int = 60
    ) -> None:
        key = f"dashboard:{user_id}:{extract_id}:by_category"
        await self.set_cached(key, data, ttl)

    # ---------------------------------------------------------------
    # Session cache
    # ---------------------------------------------------------------
    async def get_session(self, session_id: str) -> dict | None:
        key = f"session:{session_id}"
        return await self.get_cached(key)

    async def set_session(self, session_id: str, data: dict, ttl: int = 30 * 24 * 3600) -> None:
        key = f"session:{session_id}"
        await self.set_cached(key, data, ttl)

    # ---------------------------------------------------------------
    # Rate limiting (token bucket)
    # ---------------------------------------------------------------
    async def check_rate_limit(
        self, user_id: str, max_requests: int = 100, window_seconds: int = 60
    ) -> bool:
        """Verifica si el usuario esta dentro del rate limit.

        Args:
            user_id: ID del usuario.
            max_requests: Maximo de requests permitidos en la ventana.
            window_seconds: Ventana de tiempo en segundos.

        Returns:
            True si el request esta permitido, False si excede el limite.
        """
        key = f"rate_limit:{user_id}"
        current = await self.client.incr(key)
        if current == 1:
            await self.client.expire(key, window_seconds)
        return current <= max_requests

    async def get_rate_limit_remaining(self, user_id: str, max_requests: int = 100) -> int:
        """Retorna los requests restantes en la ventana actual."""
        key = f"rate_limit:{user_id}"
        current = await self.client.get(key)
        if current is None:
            return max_requests
        return max(0, max_requests - int(current))

    # ---------------------------------------------------------------
    # Merchant translation cache
    # ---------------------------------------------------------------
    async def get_merchant_translation(self, nombre: str) -> str | None:
        """Busca traduccion cacheada de un comercio."""
        key = f"merchant_translate:{nombre}"
        return await self.client.get(key)

    async def set_merchant_translation(
        self, nombre: str, traduccion: str, ttl: int = 24 * 3600
    ) -> None:
        """Cachea la traduccion de un comercio."""
        key = f"merchant_translate:{nombre}"
        await self.client.setex(key, ttl, traduccion)


# Instancia singleton
_redis_client: RedisClient | None = None


async def get_redis_client() -> RedisClient:
    """Retorna la instancia singleton del cliente Redis."""
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisClient()
        await _redis_client.connect()
    return _redis_client
