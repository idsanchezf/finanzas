"""Comando: CargarExtracto.

Representa la intencion de un usuario de cargar un archivo Excel de extracto bancario.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class CargarExtractoCommand:
    """Comando para iniciar la carga y procesamiento de un extracto.

    El handler:
    1. Valida el archivo (.xlsx, tamano maximo).
    2. Almacena el archivo en R2/S3.
    3. Registra el extracto en estado PENDING.
    4. Publica el evento ExtractoCargado en RabbitMQ.
    """

    usuario_id: UUID
    filename: str
    file_content: bytes  # Contenido del archivo Excel
    tarjeta_id: UUID | None = None  # Opcional: se auto-crea tarjeta default si no se especifica
