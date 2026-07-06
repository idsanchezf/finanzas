# Modelo de datos — feat-003: Prevenir extractos duplicados

> **Feature ID**: feat-003
> **Stack**: Python 3.12+ / FastAPI / PostgreSQL 16 / SQLAlchemy 2.0+

---

## 1. Tabla: extractos

La tabla `extractos` existe desde feat-001. feat-003 **no modifica la tabla**. Solo documenta el constraint de unicidad existente y su rol como safety net.

### 1.1 Esquema DDL (existente, feat-001)

```sql
CREATE TABLE extractos (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tarjeta_id      UUID NOT NULL REFERENCES tarjetas(id) ON DELETE CASCADE,
    periodo_inicio  DATE,
    periodo_fin     DATE,
    archivo_r2_key  VARCHAR(512) NOT NULL,
    banco_id        UUID NOT NULL REFERENCES bancos(id),
    estado          VARCHAR(20) NOT NULL DEFAULT 'PROCESADO',
    total_transacciones INTEGER NOT NULL DEFAULT 0,
    creado_en       TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraint de unicidad: safety net para feat-003
    CONSTRAINT uq_extracto_tarjeta_periodo
        UNIQUE NULLS NOT DISTINCT (tarjeta_id, periodo_inicio, periodo_fin)
);

-- Índices existentes
CREATE INDEX idx_extractos_tarjeta_id ON extractos(tarjeta_id);
CREATE INDEX idx_extractos_creado_en ON extractos(creado_en DESC);
```

### 1.2 Constraint uq_extracto_tarjeta_periodo — Rol en feat-003

| Atributo | Valor |
|----------|-------|
| **Propósito** | Safety net ante race conditions |
| **Capa de defensa** | Capa 2 (base de datos), complementa Capa 1 (pre-flight check en aplicación) |
| **Comportamiento** | `UNIQUE NULLS NOT DISTINCT`: dos filas con `(tarjeta_id, NULL, NULL)` se consideran duplicadas |
| **Cuando se activa** | Dos requests simultáneos pasan el pre-flight check antes de que ninguno persista |
| **Error SQLAlchemy** | `IntegrityError` → capturado en `SqlAlchemyExtractoRepository.save()` → convertido a `ExtractoDuplicadoException()` |
| **Frecuencia esperada** | <5% de los intentos de carga duplicada |

### 1.3 Modelo ORM (SQLAlchemy 2.0+)

```python
# src/backend/src/infrastructure/persistence/models.py

from sqlalchemy import Column, String, Date, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid
from datetime import date, datetime


class ExtractoModel(Base):
    __tablename__ = "extractos"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tarjeta_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tarjetas.id", ondelete="CASCADE"), nullable=False
    )
    periodo_inicio: Mapped[date | None] = mapped_column(Date, nullable=True)
    periodo_fin: Mapped[date | None] = mapped_column(Date, nullable=True)
    archivo_r2_key: Mapped[str] = mapped_column(String(512), nullable=False)
    banco_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bancos.id"), nullable=False
    )
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="PROCESADO")
    total_transacciones: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    # Relationships
    tarjeta = relationship("TarjetaModel", back_populates="extractos")
    transacciones = relationship("TransaccionModel", back_populates="extracto")

    # Constraints (SQLAlchemy level)
    __table_args__ = (
        UniqueConstraint(
            "tarjeta_id",
            "periodo_inicio",
            "periodo_fin",
            name="uq_extracto_tarjeta_periodo",
            # Nota: SQLAlchemy 2.0 no expone NULLS NOT DISTINCT directamente.
            # Se aplica en la migración Alembic con raw SQL.
        ),
    )
```

---

## 2. Migración Alembic (existente, documentada para referencia)

```python
# alembic/versions/xxxx_create_extractos_table.py
# Esta migración ya existe desde feat-001. Se documenta aquí para trazabilidad.

def upgrade():
    op.create_table(
        'extractos',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tarjeta_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tarjetas.id'), nullable=False),
        sa.Column('periodo_inicio', sa.Date(), nullable=True),
        sa.Column('periodo_fin', sa.Date(), nullable=True),
        sa.Column('archivo_r2_key', sa.String(512), nullable=False),
        sa.Column('banco_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('bancos.id'), nullable=False),
        sa.Column('estado', sa.String(20), nullable=False, server_default='PROCESADO'),
        sa.Column('total_transacciones', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('creado_en', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Índices
    op.create_index('idx_extractos_tarjeta_id', 'extractos', ['tarjeta_id'])
    op.create_index('idx_extractos_creado_en', 'extractos', ['creado_en'])

    # Constraint de unicidad con NULLS NOT DISTINCT (PostgreSQL 15+)
    op.execute("""
        ALTER TABLE extractos
        ADD CONSTRAINT uq_extracto_tarjeta_periodo
        UNIQUE NULLS NOT DISTINCT (tarjeta_id, periodo_inicio, periodo_fin)
    """)
```

---

## 3. Evento de dominio: ExtractoDuplicadoDetectado

### 3.1 Estructura del payload

```json
{
  "event_name": "extracto.extracto_duplicado_detectado",
  "event_id": "e7f8a9b0-c1d2-3456-efgh-ij1234567890",
  "timestamp": "2026-07-04T15:30:00Z",
  "payload": {
    "extracto_id_existente": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "tarjeta_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
    "periodo_inicio": "2026-05-01",
    "periodo_fin": "2026-05-31"
  }
}
```

### 3.2 Ciclo de vida

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐     ┌──────────────┐
│  Handler    │────►│ DomainEvent      │────►│  RabbitMQ   │────►│ Suscriptores │
│  (App Layer)│     │ Publisher        │     │  Exchange   │     │              │
└─────────────┘     └──────────────────┘     └─────────────┘     └──────┬───────┘
                                                                        │
                                                    ┌───────────────────┼───────┐
                                                    │                   │       │
                                                    ▼                   ▼       ▼
                                              ┌──────────┐     ┌──────────┐ ┌──────────┐
                                              │ Logging  │     │ Métricas │ │ Notif.   │
                                              │ (struct) │     │ (Prom)   │ │ (futuro) │
                                              └──────────┘     └──────────┘ └──────────┘
```

### 3.3 Suscriptores

| Suscriptor | Acción | Prioridad |
|------------|--------|-----------|
| **Logging** | Registrar WARN con `extracto_id`, `tarjeta_id`, `periodo` | Alta |
| **Métricas** | Incrementar contador `extractos_duplicados_total` | Alta |
| **Notificación** (futuro) | Enviar push/email al usuario: "Este extracto ya fue cargado. ¿Deseas reemplazarlo?" (feat-004) | Baja |

---

## 4. Value Object: PeriodoFacturacion

```python
@dataclass(frozen=True)
class PeriodoFacturacion:
    """Value Object inmutable que representa un periodo de facturación."""
    inicio: Optional[date]
    fin: Optional[date]

    def es_valido(self) -> bool:
        """True si ambas fechas están presentes y fin >= inicio."""
        if self.inicio is None or self.fin is None:
            return False
        return self.fin >= self.inicio

    def puede_ser_duplicado(self) -> bool:
        """
        BN-DUP-02: Solo se puede validar duplicidad si el periodo es válido.
        Retorna True si ambas fechas están presentes.
        """
        return self.inicio is not None and self.fin is not None
```

---

## 5. Notas de diseño

### 5.1 ¿Por qué UNIQUE NULLS NOT DISTINCT?

PostgreSQL 15+ introdujo `NULLS NOT DISTINCT` para constraints unique. Sin esta opción, `(tarjeta_id, NULL, NULL)` sería tratado como distinto de otro `(tarjeta_id, NULL, NULL)`, permitiendo múltiples extractos sin periodo para la misma tarjeta.

Con `NULLS NOT DISTINCT`, dos extractos sin periodo para la misma tarjeta se consideran duplicados. Esto es intencional: si el parser no pudo extraer el periodo de dos archivos, es casi seguro que son el mismo extracto subido dos veces.

### 5.2 ¿Por qué no validar en la entidad Extracto?

La validación de unicidad requiere acceso al repositorio (consulta a BD). Por principios de Clean Architecture, la entidad de dominio no debe depender de infraestructura. La validación se realiza en el caso de uso (application layer), que tiene acceso al repositorio via dependency injection.

### 5.3 ¿Por qué no usar SELECT FOR UPDATE?

Una alternativa para prevenir race conditions sería `SELECT ... FOR UPDATE` en el pre-flight check. Esto bloquearía la fila hasta que la transacción termine. Sin embargo:
- **Contra**: Bloqueo en la tabla `extractos` durante toda la transacción de carga (que incluye inserción de múltiples transacciones)
- **Contra**: Si la fila no existe aún (caso normal), no hay nada que bloquear — la race condition sigue siendo posible
- **A favor del constraint**: Es la solución más simple y robusta. PostgreSQL garantiza atomicidad del constraint check.

### 5.4 Trazabilidad con tareas

| Artefacto | Tarea asociada | Capa |
|-----------|---------------|------|
| `uq_extracto_tarjeta_periodo` | T007 (safety net) | Infrastructure / DB |
| `ExtractoDuplicadoDetectado` | T003 (evento de dominio) | Domain |
| `ExtractoDuplicadoException` | T004 (excepción → 409) | Domain / API |
| `PeriodoFacturacion.puede_ser_duplicado()` | T003 (pre-flight check, BN-DUP-02) | Domain |
