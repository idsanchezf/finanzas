"""Cliente Cloudflare R2 — Almacenamiento S3-compatible.

Usa boto3 (sync) y aioboto3 (async) para operaciones con R2.
Almacena extractos Excel originales, reportes PDF/Excel generados y modelos ML.

En desarrollo (ENVIRONMENT=development), si no hay credenciales R2 configuradas,
usa almacenamiento local en disco en lugar de R2.
"""

from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path
from typing import Any

import boto3
from botocore.config import Config

logger = logging.getLogger(__name__)


class R2Storage:
    """Cliente para Cloudflare R2 (S3-compatible).

    Buckets:
    - finance-extracts: Extractos Excel originales
    - finance-reports: Reportes PDF/Excel generados (TTL 30 dias)
    - finance-models: Modelos ML serializados (.pkl)

    En desarrollo sin credenciales R2, usa almacenamiento local en disco.
    """

    # Directorio base para almacenamiento local en desarrollo
    DEV_STORAGE_BASE = Path(os.getenv("DEV_STORAGE_PATH", "/app/storage"))

    def __init__(
        self,
        access_key: str = "",
        secret_key: str = "",
        endpoint_url: str = "",
        region: str = "auto",
    ) -> None:
        self.access_key = access_key or os.getenv("R2_ACCESS_KEY", "")
        self.secret_key = secret_key or os.getenv("R2_SECRET_KEY", "")
        self.endpoint_url = endpoint_url or os.getenv("R2_ENDPOINT", "")
        self.region = region
        self._client = None

        # Detectar si usar almacenamiento local (desarrollo sin credenciales reales)
        self._use_local = self._should_use_local()

    def _should_use_local(self) -> bool:
        """Determina si se debe usar almacenamiento local en lugar de R2."""
        is_dev = os.getenv("ENVIRONMENT", "production") == "development"
        has_placeholder = (
            "your-r2-access-key" in self.access_key
            or "your-account" in self.endpoint_url
            or not self.access_key
            or not self.endpoint_url
        )
        return is_dev and has_placeholder

    def _local_path(self, bucket: str, key: str) -> Path:
        """Retorna la ruta local para un archivo en un bucket."""
        path = self.DEV_STORAGE_BASE / bucket / key
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def client(self) -> Any:
        """Cliente boto3 S3 configurado para R2."""
        if self._use_local:
            return None
        if self._client is None:
            self._client = boto3.client(
                "s3",
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region,
                config=Config(
                    signature_version="s3v4",
                    retries={"max_attempts": 3, "mode": "standard"},
                ),
            )
        return self._client

    def upload_file(
        self, bucket: str, key: str, file_path: str | None = None, file_content: bytes | None = None
    ) -> str:
        """Sube un archivo a R2 (o local en desarrollo).

        Args:
            bucket: Nombre del bucket (finance-extracts, finance-reports, finance-models).
            key: Ruta del objeto en el bucket (ej. 'user_id/extract_id/filename.xlsx').
            file_path: Ruta local del archivo (alternativa a file_content).
            file_content: Contenido binario del archivo (alternativa a file_path).

        Returns:
            URL publica del objeto subido (o ruta local en desarrollo).
        """
        if self._use_local:
            local = self._local_path(bucket, key)
            if file_content:
                local.write_bytes(file_content)
            elif file_path:
                shutil.copy2(file_path, local)
            else:
                raise ValueError("Se requiere file_path o file_content")
            logger.info(f"Archivo guardado localmente (dev): {local}")
            return str(local)

        if file_content:
            self.client.put_object(
                Bucket=bucket,
                Key=key,
                Body=file_content,
            )
        elif file_path:
            self.client.upload_file(file_path, bucket, key)
        else:
            raise ValueError("Se requiere file_path o file_content")

        logger.info(f"Archivo subido a R2: {bucket}/{key}")
        return f"{self.endpoint_url}/{bucket}/{key}"

    def download_file(self, bucket: str, key: str) -> bytes:
        """Descarga un archivo desde R2 (o local en desarrollo).

        Returns:
            Contenido binario del archivo.
        """
        if self._use_local:
            local = self._local_path(bucket, key)
            if not local.exists():
                raise FileNotFoundError(f"Archivo no encontrado localmente: {local}")
            return local.read_bytes()

        response = self.client.get_object(Bucket=bucket, Key=key)
        content = response["Body"].read()
        logger.debug(f"Archivo descargado de R2: {bucket}/{key}")
        return content

    def delete_file(self, bucket: str, key: str) -> None:
        """Elimina un archivo de R2 (o local en desarrollo)."""
        if self._use_local:
            local = self._local_path(bucket, key)
            if local.exists():
                local.unlink()
                logger.info(f"Archivo eliminado localmente (dev): {local}")
            return

        self.client.delete_object(Bucket=bucket, Key=key)
        logger.info(f"Archivo eliminado de R2: {bucket}/{key}")

    def list_files(self, bucket: str, prefix: str = "") -> list[dict[str, Any]]:
        """Lista archivos en un bucket con un prefijo dado."""
        if self._use_local:
            base = self.DEV_STORAGE_BASE / bucket
            if not base.exists():
                return []
            results = []
            for f in base.rglob("*"):
                if f.is_file():
                    rel = str(f.relative_to(base))
                    if rel.startswith(prefix):
                        results.append(
                            {
                                "key": rel,
                                "size": f.stat().st_size,
                                "last_modified": f.stat().st_mtime,
                            }
                        )
            return results

        response = self.client.list_objects_v2(Bucket=bucket, Prefix=prefix)
        if "Contents" not in response:
            return []
        return [
            {
                "key": obj["Key"],
                "size": obj["Size"],
                "last_modified": obj["LastModified"],
            }
            for obj in response["Contents"]
        ]

    def generate_presigned_url(self, bucket: str, key: str, expiration: int = 3600) -> str:
        """Genera URL prefirmada para acceso temporal.

        Args:
            expiration: Tiempo de expiracion en segundos (default 1 hora).
        """
        if self._use_local:
            return str(self._local_path(bucket, key))

        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expiration,
        )


# Instancia singleton
_storage: R2Storage | None = None


def get_storage() -> R2Storage:
    """Retorna la instancia singleton del cliente R2."""
    global _storage
    if _storage is None:
        _storage = R2Storage()
    return _storage
