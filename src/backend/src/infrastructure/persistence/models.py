"""Modelos ORM — SQLAlchemy 2.0 declarative mappings.

Reflejan el modelo de datos definido en docs/architecture.md seccion 10.
Usan UUID como PK, NUMERIC para montos, y JSONB para datos semi-estructurados.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base para todos los modelos ORM."""

    pass


# ============================================================
# Usuario
# ============================================================
class UsuarioModel(Base):
    __tablename__ = "usuarios"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    auth_provider: Mapped[str] = mapped_column(String(20), nullable=False)
    auth_provider_id: Mapped[str] = mapped_column(String(255), nullable=False)
    tfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    tfa_secret: Mapped[str | None] = mapped_column(String(255), nullable=True)
    preferencias_json: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relaciones
    tarjetas: Mapped[list[TarjetaModel]] = relationship(back_populates="usuario", lazy="selectin")
    extractos: Mapped[list[ExtractoModel]] = relationship(back_populates="usuario", lazy="selectin")
    refresh_tokens: Mapped[list[RefreshTokenModel]] = relationship(
        back_populates="usuario", lazy="selectin"
    )

    __table_args__ = (
        UniqueConstraint("auth_provider", "auth_provider_id", name="uq_auth_provider"),
    )


# ============================================================
# RefreshToken
# ============================================================
class RefreshTokenModel(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False
    )
    token_jti: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    usuario: Mapped[UsuarioModel] = relationship(back_populates="refresh_tokens", lazy="joined")

    __table_args__ = (
        Index("ix_refresh_tokens_usuario", "usuario_id"),
        Index("ix_refresh_tokens_jti", "token_jti"),
    )


# ============================================================
# Tarjeta
# ============================================================
class TarjetaModel(Base):
    __tablename__ = "tarjetas"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False
    )
    banco: Mapped[str] = mapped_column(String(100), nullable=False)
    ultimos_4_digitos: Mapped[str] = mapped_column(String(4), nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    alias: Mapped[str | None] = mapped_column(String(100), nullable=True)
    activa: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    usuario: Mapped[UsuarioModel] = relationship(back_populates="tarjetas")
    extractos: Mapped[list[ExtractoModel]] = relationship(back_populates="tarjeta", lazy="selectin")


# ============================================================
# Extracto
# ============================================================
class ExtractoModel(Base):
    __tablename__ = "extractos"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tarjeta_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("tarjetas.id", ondelete="CASCADE"), nullable=False
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False
    )
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")
    periodo_inicio: Mapped[date | None] = mapped_column(Date, nullable=True)
    periodo_fin: Mapped[date | None] = mapped_column(Date, nullable=True)
    fecha_corte: Mapped[date | None] = mapped_column(Date, nullable=True)
    fecha_limite_pago: Mapped[date | None] = mapped_column(Date, nullable=True)
    pago_minimo: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    pago_total: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    cupo_total: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    cupo_disponible: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    tasas_interes_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    metadatos_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    archivo_s3_key: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    file_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    progress_pct: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    tarjeta: Mapped[TarjetaModel] = relationship(back_populates="extractos")
    usuario: Mapped[UsuarioModel] = relationship(back_populates="extractos")
    transacciones: Mapped[list[TransaccionModel]] = relationship(
        back_populates="extracto", lazy="selectin"
    )

    __table_args__ = (
        UniqueConstraint(
            "tarjeta_id",
            "periodo_inicio",
            "periodo_fin",
            name="uq_extracto_tarjeta_periodo",
        ),
        UniqueConstraint(
            "tarjeta_id",
            "file_hash",
            name="uq_extracto_tarjeta_file_hash",
        ),
        Index("ix_extractos_usuario_estado", "usuario_id", "estado"),
        Index("ix_extractos_tarjeta_fecha", "tarjeta_id", "periodo_inicio"),
        Index("ix_extractos_file_hash", "tarjeta_id", "file_hash"),
    )


# ============================================================
# Transaccion
# ============================================================
class TransaccionModel(Base):
    __tablename__ = "transacciones"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    extracto_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("extractos.id", ondelete="CASCADE"), nullable=False
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False
    )
    numero_autorizacion: Mapped[str | None] = mapped_column(String(100), nullable=True)
    fecha: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    comercio_original: Mapped[str] = mapped_column(String(500), nullable=False)
    comercio_traducido: Mapped[str | None] = mapped_column(String(500), nullable=True)
    valor: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    numero_cuotas: Mapped[str | None] = mapped_column(String(20), nullable=True)
    cuotas_totales: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cuota_actual: Mapped[int | None] = mapped_column(Integer, nullable=True)
    valor_cuota: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    interes_mensual_pct: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    interes_anual_pct: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    saldo_pendiente: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    moneda_original: Mapped[str | None] = mapped_column(String(10), nullable=True)
    valor_moneda_original: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    categoria_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("categorias.id", ondelete="SET NULL"), nullable=True
    )
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    es_abono: Mapped[bool] = mapped_column(Boolean, default=False)
    es_cuota: Mapped[bool] = mapped_column(Boolean, default=False)
    parent_transaccion_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("transacciones.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    extracto: Mapped[ExtractoModel] = relationship(back_populates="transacciones")
    categoria: Mapped[CategoriaModel | None] = relationship(
        "CategoriaModel", foreign_keys=[categoria_id], lazy="joined"
    )
    parent: Mapped[TransaccionModel | None] = relationship(
        "TransaccionModel", remote_side=[id], foreign_keys=[parent_transaccion_id]
    )

    # ============================================================
    # Propiedades derivadas (compatibles con dominio)
    # ============================================================
    @property
    def nombre_visible(self) -> str:
        """Nombre amigable del comercio para mostrar al usuario."""
        return self.comercio_traducido or self.comercio_original

    @property
    def es_confianza_baja(self) -> bool:
        """True si la clasificacion tiene confianza baja (<70%)."""
        return self.confidence is not None and self.confidence < 70

    __table_args__ = (
        Index("ix_transacciones_extracto", "extracto_id"),
        Index("ix_transacciones_categoria", "categoria_id"),
        Index("ix_transacciones_comercio", "comercio_original"),
        Index("ix_transacciones_usuario_fecha", "usuario_id", "fecha"),
        Index(
            "ix_transacciones_busqueda",
            "comercio_original",
            postgresql_using="gin",
            postgresql_ops={"comercio_original": "gin_trgm_ops"},
        ),
    )


# ============================================================
# Categoria
# ============================================================
class CategoriaModel(Base):
    __tablename__ = "categorias"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    icono: Mapped[str] = mapped_column(String(10), default="📁")
    color: Mapped[str] = mapped_column(String(7), default="#6B7280")
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("categorias.id", ondelete="CASCADE"), nullable=True
    )
    es_predefinida: Mapped[bool] = mapped_column(Boolean, default=False)
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=True
    )
    palabras_clave: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    subcategorias: Mapped[list[CategoriaModel]] = relationship(
        "CategoriaModel", back_populates="parent", remote_side=[parent_id], lazy="selectin"
    )
    parent: Mapped[CategoriaModel | None] = relationship(
        "CategoriaModel", remote_side=[id], back_populates="subcategorias"
    )


# ============================================================
# Presupuesto
# ============================================================
class PresupuestoModel(Base):
    __tablename__ = "presupuestos"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False
    )
    categoria_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("categorias.id", ondelete="CASCADE"), nullable=False
    )
    limite_mensual: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    alerta_80pct: Mapped[bool] = mapped_column(Boolean, default=True)
    alerta_100pct: Mapped[bool] = mapped_column(Boolean, default=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("usuario_id", "categoria_id", name="uq_presupuesto_usuario_categoria"),
        CheckConstraint("limite_mensual > 0", name="ck_limite_positivo"),
    )


# ============================================================
# MetaAhorro
# ============================================================
class MetaAhorroModel(Base):
    __tablename__ = "metas_ahorro"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False
    )
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    monto_objetivo: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    monto_acumulado: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    fecha_deseada: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ============================================================
# TraduccionComercio
# ============================================================
class TraduccionComercioModel(Base):
    __tablename__ = "traducciones_comercios"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre_original: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    nombre_traducido: Mapped[str] = mapped_column(String(500), nullable=False)
    categoria_sugerida_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("categorias.id", ondelete="SET NULL"), nullable=True
    )
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    votos: Mapped[int] = mapped_column(Integer, default=0)
    estado: Mapped[str] = mapped_column(String(20), default="pendiente")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ============================================================
# Notificacion
# ============================================================
class NotificacionModel(Base):
    __tablename__ = "notificaciones"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False
    )
    tipo: Mapped[str] = mapped_column(String(50), nullable=False)
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    mensaje: Mapped[str] = mapped_column(Text, nullable=False)
    leida: Mapped[bool] = mapped_column(Boolean, default=False)
    canal: Mapped[str] = mapped_column(String(20), nullable=False, default="in_app")
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (Index("ix_notificaciones_usuario_leida", "usuario_id", "leida"),)


# ============================================================
# SesionChat
# ============================================================
class SesionChatModel(Base):
    __tablename__ = "sesiones_chat"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False
    )
    titulo: Mapped[str] = mapped_column(String(200), default="Nueva conversacion")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    mensajes: Mapped[list[MensajeChatModel]] = relationship(
        back_populates="sesion", lazy="selectin", order_by="MensajeChatModel.created_at"
    )


# ============================================================
# MensajeChat
# ============================================================
class MensajeChatModel(Base):
    __tablename__ = "mensajes_chat"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sesion_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("sesiones_chat.id", ondelete="CASCADE"), nullable=False
    )
    rol: Mapped[str] = mapped_column(String(20), nullable=False)  # user, assistant, system
    contenido: Mapped[str] = mapped_column(Text, nullable=False)
    tokens_usados: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    sesion: Mapped[SesionChatModel] = relationship(back_populates="mensajes")
