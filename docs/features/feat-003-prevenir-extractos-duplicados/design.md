# Diseño — feat-003: Prevenir extractos duplicados

> **Feature ID**: feat-003
> **Dependencia**: feat-002 (identificar tarjeta desde extracto) — completada
> **Stack**: Python 3.12+ / FastAPI / PostgreSQL 16 / SQLAlchemy 2.0+ / Clean Architecture + DDD
> **Fecha**: Julio 2026

---

## 1. Contrato API — POST /api/v1/extracts/upload

### 1.1 Endpoint

```
POST /api/v1/extracts/upload
Content-Type: multipart/form-data
Authorization: Bearer <JWT>
```

### 1.2 Request

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `file` | `file` (binary) | Sí | Archivo Excel (.xlsx) del extracto bancario |
| `banco_id` | `string` (UUID) | Sí | ID del banco emisor del extracto (ej. Bancolombia) |

**Ejemplo de request (curl)**:
```bash
curl -X POST http://localhost:8000/api/v1/extracts/upload \
  -H "Authorization: Bearer <JWT>" \
  -F "file=@extracto_mayo_2026.xlsx" \
  -F "banco_id=550e8400-e29b-41d4-a716-446655440000"
```

### 1.3 Response — 201 Created (flujo exitoso, sin cambios respecto a feat-001/002)

```json
{
  "extracto_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "tarjeta_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "periodo_inicio": "2026-05-01",
  "periodo_fin": "2026-05-31",
  "banco": "Bancolombia",
  "ultimos_4_digitos": "7681",
  "total_transacciones": 45,
  "created_at": "2026-07-04T15:30:00Z"
}
```

### 1.4 Response — 409 Conflict (nuevo — extracto duplicado)

**Caso 1: Duplicado detectado en pre-flight check** (95% de los casos)

```json
{
  "error": "EXTRACTO_DUPLICADO",
  "message": "El extracto para la tarjeta 7681 periodo 2026-05-01 a 2026-05-31 ya existe",
  "extracto_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "tarjeta_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
  "periodo_inicio": "2026-05-01",
  "periodo_fin": "2026-05-31"
}
```

**Caso 2: Race condition capturada por safety net de BD** (<5% de los casos, ver sección 6.3 del análisis)

```json
{
  "error": "EXTRACTO_DUPLICADO",
  "message": "Conflicto de concurrencia: el extracto fue creado por otra solicitud simultánea",
  "extracto_id": null,
  "tarjeta_id": null,
  "periodo_inicio": null,
  "periodo_fin": null
}
```

### 1.5 Response — 422 Unprocessable Entity (archivo inválido)

```json
{
  "error": "VALIDACION_FALLIDA",
  "message": "El archivo no contiene un formato de extracto reconocible para el banco <banco_nombre>",
  "detalles": {
    "razon": "No se pudo extraer el periodo de facturación del archivo Excel",
    "columna_esperada": "periodo_facturado",
    "filas_procesadas": 0
  }
}
```

### 1.6 Response — 401 Unauthorized

```json
{
  "error": "NO_AUTENTICADO",
  "message": "Token JWT inválido o expirado"
}
```

### 1.7 Response — 404 Not Found (tarjeta no identificable)

```json
{
  "error": "TARJETA_NO_ENCONTRADA",
  "message": "No se pudo identificar la tarjeta con últimos 4 dígitos '7681' para el banco 'Bancolombia'"
}
```

### 1.8 Especificación OpenAPI (fragmento relevante)

```yaml
openapi: 3.0.3
info:
  title: Finance Report — Extracts API
  version: 1.0.0
paths:
  /api/v1/extracts/upload:
    post:
      summary: Cargar un extracto bancario
      description: |
        Sube un archivo Excel de extracto bancario, lo parsea, identifica la tarjeta,
        valida que no sea duplicado y persiste las transacciones.
      operationId: uploadExtract
      tags:
        - Extractos
      security:
        - BearerAuth: []
      requestBody:
        required: true
        content:
          multipart/form-data:
            schema:
              type: object
              required:
                - file
                - banco_id
              properties:
                file:
                  type: string
                  format: binary
                  description: Archivo Excel (.xlsx) del extracto
                banco_id:
                  type: string
                  format: uuid
                  description: ID del banco emisor
      responses:
        '201':
          description: Extracto cargado exitosamente
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ExtractoResponse'
        '409':
          description: Extracto duplicado — ya existe para la misma tarjeta + periodo
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ExtractoDuplicadoError'
        '422':
          description: El archivo Excel no tiene un formato reconocible
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ValidacionError'
        '401':
          description: No autenticado
        '404':
          description: Tarjeta no identificada

components:
  schemas:
    ExtractoResponse:
      type: object
      properties:
        extracto_id:
          type: string
          format: uuid
        tarjeta_id:
          type: string
          format: uuid
        periodo_inicio:
          type: string
          format: date
        periodo_fin:
          type: string
          format: date
        banco:
          type: string
        ultimos_4_digitos:
          type: string
          pattern: '^\d{4}$'
        total_transacciones:
          type: integer
        created_at:
          type: string
          format: date-time

    ExtractoDuplicadoError:
      type: object
      required:
        - error
        - message
      properties:
        error:
          type: string
          enum: [EXTRACTO_DUPLICADO]
        message:
          type: string
        extracto_id:
          type: string
          format: uuid
          nullable: true
          description: ID del extracto ya existente (null en race condition)
        tarjeta_id:
          type: string
          format: uuid
          nullable: true
        periodo_inicio:
          type: string
          format: date
          nullable: true
        periodo_fin:
          type: string
          format: date
          nullable: true

    ValidacionError:
      type: object
      required:
        - error
        - message
      properties:
        error:
          type: string
          enum: [VALIDACION_FALLIDA]
        message:
          type: string
        detalles:
          type: object

  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
```

---

## 2. Modelo de datos

### 2.1 Entidad Extracto (existente, sin modificar)

La entidad `Extracto` (AggregateRoot) no se modifica. La validación de unicidad se implementa en la capa de aplicación, no en la entidad.

```python
# src/backend/src/domain/extracto/entities.py

@dataclass
class Extracto(AggregateRoot):
    """Extracto bancario — Aggregate Root del bounded context de Carga de Extractos"""
    id: ExtractoId
    tarjeta_id: TarjetaId
    periodo_inicio: Optional[date]
    periodo_fin: Optional[date]
    archivo_r2_key: str
    banco_id: UUID
    estado: ExtractoEstado
    total_transacciones: int
    creado_en: datetime

    # La regla de unicidad NO se valida en la entidad.
    # Se valida en el caso de uso (application layer) para permitir
    # el pre-flight check antes de persistir.
```

### 2.2 Value Object: PeriodoFacturacion (existente)

```python
# src/backend/src/domain/extracto/value_objects.py

@dataclass(frozen=True)
class PeriodoFacturacion:
    """Identifica de forma única un periodo junto con la tarjeta"""
    inicio: date
    fin: date

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PeriodoFacturacion):
            return NotImplemented
        return self.inicio == other.inicio and self.fin == other.fin

    def __hash__(self) -> int:
        return hash((self.inicio, self.fin))

    def es_valido(self) -> bool:
        """Un periodo es válido si ambas fechas están presentes y fin >= inicio"""
        return self.inicio is not None and self.fin is not None and self.fin >= self.inicio
```

### 2.3 Evento de dominio: ExtractoDuplicadoDetectado (nuevo)

```python
# src/backend/src/domain/extracto/eventos.py

@dataclass(frozen=True)
class ExtractoDuplicadoDetectado(DomainEvent):
    """Se emite cuando se detecta un intento de cargar un extracto duplicado.
    Es un evento informativo: no modifica estado, solo habilita logging, métricas y notificaciones."""
    extracto_id_existente: UUID
    tarjeta_id: UUID
    periodo_inicio: Optional[date]
    periodo_fin: Optional[date]
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @property
    def event_name(self) -> str:
        return "extracto.extracto_duplicado_detectado"

    @property
    def payload(self) -> dict:
        return {
            "extracto_id_existente": str(self.extracto_id_existente),
            "tarjeta_id": str(self.tarjeta_id),
            "periodo_inicio": self.periodo_inicio.isoformat() if self.periodo_inicio else None,
            "periodo_fin": self.periodo_fin.isoformat() if self.periodo_fin else None,
            "timestamp": self.timestamp.isoformat(),
        }
```

### 2.4 Excepción de dominio: ExtractoDuplicadoException (nueva)

```python
# src/backend/src/domain/extracto/exceptions.py

class ExtractoDuplicadoException(DomainException):
    """Se lanza cuando se detecta que el extracto ya existe para la misma tarjeta + periodo"""

    def __init__(
        self,
        extracto_id_existente: Optional[UUID] = None,
        tarjeta_id: Optional[UUID] = None,
        periodo_inicio: Optional[date] = None,
        periodo_fin: Optional[date] = None,
        message: Optional[str] = None,
    ):
        self.extracto_id = extracto_id_existente
        self.tarjeta_id = tarjeta_id
        self.periodo_inicio = periodo_inicio
        self.periodo_fin = periodo_fin

        if message is None and tarjeta_id and periodo_inicio and periodo_fin:
            message = (
                f"El extracto para la tarjeta {tarjeta_id} "
                f"periodo {periodo_inicio} a {periodo_fin} ya existe "
                f"(id: {extracto_id_existente})"
            )
        elif message is None:
            message = "Conflicto de concurrencia: el extracto fue creado por otra solicitud simultánea"

        super().__init__(message, error_code="EXTRACTO_DUPLICADO")
```

### 2.5 Repositorio: ExtractoRepository (interfaz en dominio)

```python
# src/backend/src/domain/extracto/repository.py

class ExtractoRepository(ABC):
    """Interfaz del repositorio de extractos (patrón Repository)"""

    @abstractmethod
    async def get_by_id(self, extracto_id: UUID) -> Optional[Extracto]:
        """Obtiene un extracto por su ID"""
        ...

    @abstractmethod
    async def get_by_tarjeta_and_periodo(
        self, tarjeta_id: UUID, periodo_inicio: date, periodo_fin: date
    ) -> Optional[Extracto]:
        """
        Busca un extracto existente por tarjeta + periodo exacto.

        Args:
            tarjeta_id: ID de la tarjeta
            periodo_inicio: Fecha de inicio del periodo
            periodo_fin: Fecha de fin del periodo

        Returns:
            El extracto existente si lo hay, None en caso contrario.
            La búsqueda es por coincidencia exacta de ambas fechas.
        """
        ...

    @abstractmethod
    async def save(self, extracto: Extracto) -> Extracto:
        """
        Persiste un nuevo extracto.

        Raises:
            IntegrityError: Si el constraint uq_extracto_tarjeta_periodo falla (race condition).
                Debe ser capturado por la capa de infraestructura y convertido a ExtractoDuplicadoException.
        """
        ...
```

### 2.6 Constraint de base de datos (safety net)

```sql
-- Migración Alembic (existente de feat-001, se documenta aquí para referencia)
ALTER TABLE extractos
ADD CONSTRAINT uq_extracto_tarjeta_periodo
UNIQUE NULLS NOT DISTINCT (tarjeta_id, periodo_inicio, periodo_fin);
```

> **Nota**: PostgreSQL 15+ soporta `UNIQUE NULLS NOT DISTINCT`. Esto significa que dos filas con `(tarjeta_id, NULL, NULL)` se consideran duplicadas. Esto es intencional: si dos extractos no tienen periodo, asumimos que son el mismo (caso extremadamente raro).

---

## 3. Patrones de integración

### 3.1 Diagrama de secuencia del caso de uso CargarExtracto (con feat-003)

```
┌──────┐     ┌──────────┐     ┌──────────────────┐     ┌─────────────────┐     ┌──────────┐
│Router│     │ Handler  │     │ ExtractoRepo      │     │ DomainEvents    │     │ Postgres │
│(API) │     │(App Layer)│     │(Infra, interfaz) │     │ Publisher       │     │          │
└──┬───┘     └────┬─────┘     └────────┬─────────┘     └────────┬────────┘     └────┬─────┘
   │              │                    │                        │                   │
   │ POST /upload │                    │                        │                   │
   │──────────────>                    │                        │                   │
   │              │                    │                        │                   │
   │              │ handle(file,       │                        │                   │
   │              │ banco_id)          │                        │                   │
   │              │                    │                        │                   │
   │              │── 1. Subir a R2 ─────────────────────────────────────────────────>
   │              │<── archivo_r2_key ───────────────────────────────────────────────────
   │              │                    │                        │                   │
   │              │── 2. Parsear Excel (en memoria)            │                   │
   │              │    └─ obtener periodo_inicio, periodo_fin  │                   │
   │              │                    │                        │                   │
   │              │── 3. Identificar tarjeta (feat-002) ───────│───────────────────>
   │              │<── tarjeta_id ─────────────────────────────│────────────────────
   │              │                    │                        │                   │
   │              │── 4. PRE-FLIGHT CHECK (feat-003) ──────►   │                   │
   │              │    get_by_tarjeta_and_periodo(              │                   │
   │              │      tarjeta_id, periodo_inicio, periodo_fin)                   │
   │              │                    │                        │                   │
   │              │                    ├────────────────────────│──────────────────►
   │              │                    │  SELECT ... WHERE      │                   │
   │              │                    │  tarjeta_id AND        │                   │
   │              │                    │  periodo_inicio AND    │                   │
   │              │                    │  periodo_fin           │                   │
   │              │                    │<───────────────────────│───────────────────
   │              │                    │                        │                   │
   │              │            ┌───────┴────────┐               │                   │
   │              │            │  ¿Resultado?   │               │                   │
   │              │            └───────┬────────┘               │                   │
   │              │                    │                        │                   │
   │              │     ┌─ NO existe ──┤                        │                   │
   │              │     │              └─ SI existe ──┐         │                   │
   │              │     │                             │         │                   │
   │              │     │ 5. Persistir extracto       │         │                   │
   │              │     │    repo.save(extracto)      │         │                   │
   │              │     │              │              │         │                   │
   │              │     │              ├──────────────│─────────│──────────────────►
   │              │     │              │ INSERT INTO  │         │                   │
   │              │     │              │<─────────────│─────────│───────────────────
   │              │     │              │              │         │                   │
   │              │     │              │              │         │                   │
   │              │     │ 6. Emitir    │              │         │                   │
   │              │     │    ExtractoCreado           │         │                   │
   │              │     │              │              ├────────►│                   │
   │              │     │              │              │         │                   │
   │              │     │ return 201 ──│──────────────│─────────│───────────────────
   │<─────────────│─────│───── 201 Created            │         │                   │
   │              │     │              │              │         │                   │
   │              │     │              │              │         │                   │
   │              │     │              │     ┌────────┴────────┐│                   │
   │              │     │              │     │ SI existe       ││                   │
   │              │     │              │     │ (duplicado)     ││                   │
   │              │     │              │     └────────┬────────┘│                   │
   │              │     │              │              │         │                   │
   │              │     │              │ 7. Emitir    │         │                   │
   │              │     │              │    ExtractoDuplicadoDetectado              │
   │              │     │              │              ├────────►│                   │
   │              │     │              │              │         │                   │
   │              │     │              │ 8. Lanzar    │         │                   │
   │              │     │              │    ExtractoDuplicadoException              │
   │              │     │              │              │         │                   │
   │              │     │              │ 9. Middleware captura → 409                │
   │<─────────────│─────│───── 409 Conflict           │         │                   │
   │              │     │              │              │         │                   │
   │              │     │              │              │         │                   │
   │              │     │              │     ┌────────┴────────┐│                   │
   │              │     │              │     │ RACE CONDITION  ││                   │
   │              │     │              │     │ (safety net)    ││                   │
   │              │     │              │     └────────┬────────┘│                   │
   │              │     │              │              │         │                   │
   │              │     │              │ 10. Capturar │         │                   │
   │              │     │              │     IntegrityError    │                   │
   │              │     │              │              ├─────────│──────────────────►
   │              │     │              │              │  INSERT falla (constraint) │
   │              │     │              │              │<────────│───────────────────
   │              │     │              │              │         │                   │
   │              │     │              │ 11. Convertir│         │                   │
   │              │     │              │     → ExtractoDuplicadoException           │
   │              │     │              │     (sin extracto_id)                      │
   │              │     │              │              │         │                   │
   │              │     │              │ 12. Middleware captura → 409               │
   │<─────────────│─────│───── 409 Conflict (race)      │         │                   │
```

### 3.2 Flujo en el handler de aplicación

```python
# src/backend/src/application/extracts/handlers.py

async def handle_cargar_extracto(
    command: CargarExtracto,
    extracto_repo: ExtractoRepository,
    tarjeta_repo: TarjetaRepository,
    parser_factory: ParserFactory,
    storage: R2StorageClient,
    event_publisher: DomainEventPublisher,
    logger: structlog.BoundLogger,
) -> ExtractoResponse:
    """
    Caso de uso: Cargar Extracto Bancario.

    Flujo completo:
    1. Subir archivo a R2
    2. Parsear Excel
    3. Identificar tarjeta (feat-002)
    4. Pre-flight check de duplicado (feat-003) ← NUEVO
    5. Persistir extracto + transacciones
    6. Emitir evento ExtractoCreado
    """

    # --- PASOS 1-3 (feat-001/002, sin cambios) ---
    # 1. Subir archivo a R2
    archivo_r2_key = await storage.upload(command.file_content, command.file_name)

    # 2. Parsear Excel
    parser = parser_factory.get_parser(command.banco_id)
    resultado_parseo = await parser.parse(command.file_content)

    # 3. Identificar tarjeta (feat-002)
    tarjeta = await tarjeta_repo.find_or_create(
        banco_id=command.banco_id,
        ultimos_4_digitos=resultado_parseo.ultimos_4_digitos,
    )

    # --- PASO 4: PRE-FLIGHT CHECK (feat-003, NUEVO) ---
    if resultado_parseo.periodo_inicio is not None and resultado_parseo.periodo_fin is not None:
        # BN-DUP-01: Validar unicidad
        extracto_existente = await extracto_repo.get_by_tarjeta_and_periodo(
            tarjeta_id=tarjeta.id,
            periodo_inicio=resultado_parseo.periodo_inicio,
            periodo_fin=resultado_parseo.periodo_fin,
        )

        if extracto_existente is not None:
            # BN-DUP-01 (rama SI existe): Emitir evento + lanzar excepción
            await event_publisher.publish(
                ExtractoDuplicadoDetectado(
                    extracto_id_existente=extracto_existente.id,
                    tarjeta_id=tarjeta.id,
                    periodo_inicio=resultado_parseo.periodo_inicio,
                    periodo_fin=resultado_parseo.periodo_fin,
                )
            )
            logger.warning(
                "extracto_duplicado_detectado",
                extracto_id=extracto_existente.id,
                tarjeta_id=tarjeta.id,
                periodo_inicio=resultado_parseo.periodo_inicio,
                periodo_fin=resultado_parseo.periodo_fin,
            )
            raise ExtractoDuplicadoException(
                extracto_id_existente=extracto_existente.id,
                tarjeta_id=tarjeta.id,
                periodo_inicio=resultado_parseo.periodo_inicio,
                periodo_fin=resultado_parseo.periodo_fin,
            )
    else:
        # BN-DUP-02: Periodo no detectable — omitir validación
        logger.warning(
            "periodo_no_detectado_validacion_duplicado_omitida",
            tarjeta_id=tarjeta.id,
            ultimos_4_digitos=resultado_parseo.ultimos_4_digitos,
        )

    # --- PASO 5: Persistir extracto + transacciones (feat-001, sin cambios) ---
    try:
        extracto = Extracto(
            id=ExtractoId.generate(),
            tarjeta_id=tarjeta.id,
            periodo_inicio=resultado_parseo.periodo_inicio,
            periodo_fin=resultado_parseo.periodo_fin,
            archivo_r2_key=archivo_r2_key,
            banco_id=command.banco_id,
            estado=ExtractoEstado.PROCESADO,
            total_transacciones=len(resultado_parseo.transacciones),
            creado_en=datetime.utcnow(),
        )

        extracto = await extracto_repo.save(extracto)
    except IntegrityError:
        # Safety net: Race condition capturada en capa de infraestructura
        logger.error(
            "race_condition_detectada_extracto_duplicado",
            tarjeta_id=tarjeta.id,
            periodo_inicio=resultado_parseo.periodo_inicio,
            periodo_fin=resultado_parseo.periodo_fin,
        )
        raise ExtractoDuplicadoException()  # Sin extracto_id (no sabemos cuál ganó)

    # --- PASO 6: Emitir evento ExtractoCreado (feat-001, sin cambios) ---
    await event_publisher.publish(
        ExtractoCreado(
            extracto_id=extracto.id,
            tarjeta_id=tarjeta.id,
            total_transacciones=extracto.total_transacciones,
        )
    )

    return ExtractoResponse.from_entity(extracto, tarjeta)
```

### 3.3 Mapeo de excepciones a HTTP en el router

```python
# src/backend/src/api/routes/extracts.py

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from src.domain.extracto.exceptions import ExtractoDuplicadoException
from src.domain.tarjeta.exceptions import TarjetaNoEncontradaException
from src.domain.shared.exceptions import DomainException

router = APIRouter(prefix="/api/v1/extracts", tags=["Extractos"])


@router.post("/upload", status_code=201)
async def upload_extract(
    file: UploadFile = File(...),
    banco_id: UUID = Form(...),
    handler: CargarExtractoHandler = Depends(get_cargar_extracto_handler),
):
    """
    Carga un extracto bancario desde un archivo Excel.

    - 201: Extracto cargado exitosamente
    - 409: Extracto duplicado (misma tarjeta + mismo periodo)
    - 422: Archivo Excel no reconocible
    - 404: Tarjeta no identificada
    """
    try:
        result = await handler.handle(CargarExtracto(
            file_content=await file.read(),
            file_name=file.filename,
            banco_id=banco_id,
            tenant_id=request.state.tenant_id,
        ))
        return result
    except ExtractoDuplicadoException as e:
        raise HTTPException(
            status_code=409,
            detail={
                "error": e.error_code,
                "message": str(e),
                "extracto_id": str(e.extracto_id) if e.extracto_id else None,
                "tarjeta_id": str(e.tarjeta_id) if e.tarjeta_id else None,
                "periodo_inicio": e.periodo_inicio.isoformat() if e.periodo_inicio else None,
                "periodo_fin": e.periodo_fin.isoformat() if e.periodo_fin else None,
            },
        )
    except TarjetaNoEncontradaException as e:
        raise HTTPException(status_code=404, detail={"error": e.error_code, "message": str(e)})
    except ValidacionFallidaException as e:
        raise HTTPException(status_code=422, detail={"error": e.error_code, "message": str(e)})
```

### 3.4 Alternativa: Middleware global de manejo de excepciones

Como complemento al manejo en el router, se puede usar un middleware global que capture `DomainException` y las mapee automáticamente:

```python
# src/backend/src/api/middleware/error_handler.py

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.domain.extracto.exceptions import ExtractoDuplicadoException
from src.domain.shared.exceptions import DomainException


EXCEPTION_STATUS_MAP = {
    "EXTRACTO_DUPLICADO": 409,
    "TARJETA_NO_ENCONTRADA": 404,
    "VALIDACION_FALLIDA": 422,
    "NO_AUTENTICADO": 401,
    "PERMISO_DENEGADO": 403,
}


class DomainExceptionMiddleware(BaseHTTPMiddleware):
    """Captura DomainException y las convierte en respuestas HTTP adecuadas."""

    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except DomainException as e:
            status_code = EXCEPTION_STATUS_MAP.get(e.error_code, 400)

            body = {
                "error": e.error_code,
                "message": str(e),
            }

            # Enriquecer con datos adicionales si es ExtractoDuplicadoException
            if isinstance(e, ExtractoDuplicadoException):
                body.update({
                    "extracto_id": str(e.extracto_id) if e.extracto_id else None,
                    "tarjeta_id": str(e.tarjeta_id) if e.tarjeta_id else None,
                    "periodo_inicio": e.periodo_inicio.isoformat() if e.periodo_inicio else None,
                    "periodo_fin": e.periodo_fin.isoformat() if e.periodo_fin else None,
                })

            return JSONResponse(status_code=status_code, content=body)
```

> **Recomendación**: Usar el middleware global como estrategia principal (DRY). El manejo explícito en el router se reserva para casos donde se necesite lógica adicional en la respuesta (no es el caso aquí).

### 3.5 Manejo de IntegrityError (race condition) en infraestructura

```python
# src/backend/src/infrastructure/persistence/repositories/extracto_repository.py

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.extracto.entities import Extracto
from src.domain.extracto.exceptions import ExtractoDuplicadoException
from src.domain.extracto.repository import ExtractoRepository


class SqlAlchemyExtractoRepository(ExtractoRepository):
    """Implementación SQLAlchemy del repositorio de extractos."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_tarjeta_and_periodo(
        self, tarjeta_id: UUID, periodo_inicio: date, periodo_fin: date
    ) -> Optional[Extracto]:
        """Pre-flight check: busca extracto existente por tarjeta + periodo exacto."""
        stmt = (
            select(ExtractoModel)
            .where(
                ExtractoModel.tarjeta_id == tarjeta_id,
                ExtractoModel.periodo_inicio == periodo_inicio,
                ExtractoModel.periodo_fin == periodo_fin,
            )
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def save(self, extracto: Extracto) -> Extracto:
        """Persiste un nuevo extracto. Captura IntegrityError como safety net ante race conditions."""
        model = ExtractoModel.from_domain(extracto)
        self._session.add(model)
        try:
            await self._session.flush()
        except IntegrityError:
            await self._session.rollback()
            # No podemos obtener el extracto_id del duplicado porque lo insertó otra transacción.
            raise ExtractoDuplicadoException()  # Sin argumentos → mensaje genérico de race condition

        return model.to_domain()
```

---

## 4. Métricas y observabilidad

### 4.1 Métricas Prometheus

| Métrica | Tipo | Descripción |
|---------|------|-------------|
| `extractos_cargados_total` | Counter | Total de extractos cargados exitosamente |
| `extractos_duplicados_total` | Counter | Total de intentos de carga duplicada (pre-flight + race condition) |
| `extractos_duplicados_race_condition_total` | Counter | Subconjunto: duplicados detectados solo por constraint BD (race condition) |
| `extractos_sin_periodo_total` | Counter | Extractos donde no se pudo detectar el periodo (BN-DUP-02) |
| `carga_extracto_duracion_segundos` | Histogram | Duración total del flujo de carga |

### 4.2 Logging estructurado

| Evento | Nivel | Campos |
|--------|-------|--------|
| `extracto_duplicado_detectado` | WARNING | `extracto_id`, `tarjeta_id`, `periodo_inicio`, `periodo_fin`, `tenant_id` |
| `periodo_no_detectado_validacion_duplicado_omitida` | WARNING | `tarjeta_id`, `ultimos_4_digitos`, `tenant_id` |
| `race_condition_detectada_extracto_duplicado` | ERROR | `tarjeta_id`, `periodo_inicio`, `periodo_fin`, `tenant_id` |
| `extracto_cargado` | INFO | `extracto_id`, `tarjeta_id`, `total_transacciones`, `duracion_segundos` |

---

## 5. Testing strategy

### 5.1 Escenarios BDD

Los 4 escenarios definidos en el análisis (sección 5) se implementan con `pytest-bdd` en:
```
tests/features/extracto/upload_extracto.feature
```

### 5.2 Tests unitarios (TDD)

| Test | Capa | Descripción |
|------|------|-------------|
| `TestCargarExtractoHandler.test_raise_409_when_duplicate_detected` | Application | Verifica que el handler lanza `ExtractoDuplicadoException` cuando `get_by_tarjeta_and_periodo` retorna un extracto |
| `TestCargarExtractoHandler.test_emit_domain_event_when_duplicate_detected` | Application | Verifica que se emite `ExtractoDuplicadoDetectado` |
| `TestCargarExtractoHandler.test_skip_validation_when_periodo_none` | Application | BN-DUP-02: Si periodo es None, no se llama `get_by_tarjeta_and_periodo` |
| `TestExtractoRepositorySave.test_convert_integrity_error_to_domain_exception` | Infrastructure | Verifica que `IntegrityError` se convierte en `ExtractoDuplicadoException` |

### 5.3 Tests de integración

| Test | Descripción |
|------|-------------|
| `TestUploadExtractAPI.test_return_409_when_duplicate` | End-to-end: POST con archivo duplicado → 409 + JSON body con campos esperados |
| `TestUploadExtractAPI.test_return_201_when_valid` | Flujo feliz sin cambios |
| `TestUploadExtractAPI.test_race_condition_handled` | Concurrencia simulada: dos requests simultáneos, uno recibe 201, otro recibe 409 |

### 5.4 Mocking

- **Repositorios**: Mockeados en tests de capa de aplicación
- **R2 Storage**: Mockeado en todos los tests (no se sube a R2 real en tests)
- **Parser**: Stub que devuelve datos predefinidos
- **Base de datos**: TestContainers con PostgreSQL para tests de integración

---

## 6. Resumen de artefactos generados por el diseño

| Artefacto | Ubicación | Tipo | Descripción |
|-----------|-----------|------|-------------|
| API contract | `design.md` sección 1 | OpenAPI 3.0 | Contrato completo del endpoint POST /api/v1/extracts/upload con todos los status codes |
| `api-contract.yaml` | `docs/features/feat-003-prevenir-extractos-duplicados/api-contract.yaml` | OpenAPI file | Fragmento standalone del contrato |
| `data-model.md` | `docs/features/feat-003-prevenir-extractos-duplicados/data-model.md` | Documento | Modelo de datos detallado |
| Evento de dominio | `ExtractoDuplicadoDetectado` | Clase Python | Evento informativo de duplicado detectado |
| Excepción de dominio | `ExtractoDuplicadoException` | Clase Python | Excepción con metadata del duplicado |
| Handler | `handle_cargar_extracto` modificado | Función Python | Pre-flight check integrado |
| Middleware | `DomainExceptionMiddleware` | Clase Python | Mapeo global de excepciones de dominio a HTTP |
| Repositorio | `SqlAlchemyExtractoRepository.save` modificado | Clase Python | Safety net de IntegrityError |
| Métricas | `extractos_duplicados_total`, etc. | Prometheus | Contadores para monitoreo |

---

## 7. Trazabilidad con tareas

| Tarea | Estado anterior | Estado nuevo | Artefactos cubiertos |
|-------|-----------------|--------------|---------------------|
| T001 | done | done | Analysis DDD |
| T002 | pending | **done** | API contract (sección 1), `api-contract.yaml` |
| T003 | pending | pending | Pre-flight check en handler (implementación en fase `develop`) |
| T004 | pending | pending | Mapeo 409 en router/middleware (implementación en fase `develop`) |
| T005 | pending | pending | Test unitario (implementación en fase `develop` con TDD) |
| T006 | pending | pending | Test de integración (implementación en fase `develop`) |
| T007 | pending | pending | Race condition safety net (implementación en fase `develop`) |
