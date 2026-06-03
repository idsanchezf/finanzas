"""Cliente Cloudflare R2 — Almacenamiento S3-compatible.

Usa boto3 (sync) y aioboto3 (async) para operaciones con R2.
Almacena extractos Excel originales, reportes PDF/Excel generados y modelos ML.
"""

from __future__ import annotations

import logging
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
    """

    def __init__(
        self,
        access_key: str = "",
        secret_key: str = "",
        endpoint_url: str = "",
        region: str = "auto",
    ) -> None:
        import os

        self.access_key = access_key or os.getenv("R2_ACCESS_KEY", "")
        self.secret_key = secret_key or os.getenv("R2_SECRET_KEY", "")
        self.endpoint_url = endpoint_url or os.getenv("R2_ENDPOINT", "")
        self.region = region
        self._client = None

    @property
    def client(self) -> Any:
        """Cliente boto3 S3 configurado para R2."""
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
        """Sube un archivo a R2.

        Args:
            bucket: Nombre del bucket (finance-extracts, finance-reports, finance-models).
            key: Ruta del objeto en el bucket (ej. 'user_id/extract_id/filename.xlsx').
            file_path: Ruta local del archivo (alternativa a file_content).
            file_content: Contenido binario del archivo (alternativa a file_path).

        Returns:
            URL publica del objeto subido.
        """
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
        """Descarga un archivo desde R2.

        Returns:
            Contenido binario del archivo.
        """
        response = self.client.get_object(Bucket=bucket, Key=key)
        content = response["Body"].read()
        logger.debug(f"Archivo descargado de R2: {bucket}/{key}")
        return content

    def delete_file(self, bucket: str, key: str) -> None:
        """Elimina un archivo de R2."""
        self.client.delete_object(Bucket=bucket, Key=key)
        logger.info(f"Archivo eliminado de R2: {bucket}/{key}")

    def list_files(self, bucket: str, prefix: str = "") -> list[dict[str, Any]]:
        """Lista archivos en un bucket con un prefijo dado."""
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
