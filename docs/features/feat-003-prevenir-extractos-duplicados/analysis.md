# Analisis DDD — feat-003: Prevenir extractos duplicados

> **Feature ID**: feat-003
> **Dependencia**: feat-002 (identificar tarjeta desde extracto) — completada
> **Stack**: Python 3.12+ / FastAPI / PostgreSQL 16 / Clean Architecture + DDD
> **Fecha**: Junio 2026

---

## 1. Contexto del problema

Cuando un usuario sube un extracto que ya existe (misma tarjeta + mismo periodo), el flujo actual falla tarde y mal:

1. El archivo se sube a R2 (gasto innecesario de almacenamiento)
2. Se parsea el Excel completo (gasto de CPU)
3. Al persistir, PostgreSQL lanza `IntegrityError` por el constraint `uq_extracto_tarjeta_periodo`
4. El usuario recibe un error 500 generico sin contexto

La solucion es mover la validacion de unicidad al inicio del flujo (pre-flight check), antes de cualquier operacion costosa o con efectos secundarios.

---

## 2. Event Storming simplificado

### 2.1 Timeline de eventos

```
                    feat-002 garantiza
                    tarjeta_id correcto
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│  COMANDO: CargarExtracto                                │
│                                                         │
│  1. Subir archivo a R2               ─── side effect    │
│  2. Parsear Excel                     ─── CPU-bound      │
│     └─ Obtener periodo_inicio, periodo_fin              │
│  3. Identificar tarjeta (feat-002)   ─── DB read        │
│     └─ Obtener tarjeta_id                              │
│                                                         │
│  ◄── NUEVO (feat-003): PRE-FLIGHT CHECK ──►             │
│  4. Buscar extracto existente        ─── DB read        │
│     extracto_repo.get_by_tarjeta_and_periodo(            │
│         tarjeta_id, periodo_inicio, periodo_fin)         │
│                                                         │
│     ┌─ NO existe ──► continuar flujo normal             │
│     │              5. Persistir extracto                │
│     │              6. Emitir ExtractoCreado              │
│     │                                                   │
│     └─ SI existe ──► 7. Emitir ExtractoDuplicadoDetectado│
│                      8. Lanzar ExtractoDuplicadoException│
│                      9. Router → 409 Conflict            │
└─────────────────────────────────────────────────────────┘
```

### 2.2 Evento de dominio nuevo

| Evento | `ExtractoDuplicadoDetectado` |
|--------|-----------------------------|
| **Disparador** | `get_by_tarjeta_and_periodo()` retorna un extracto existente |
| **Payload** | `extracto_id_existente`, `tarjeta_id`, `periodo_inicio`, `periodo_fin`, `timestamp` |
| **Momento** | Pre-persistencia, en la capa de aplicacion (`handle_cargar_extracto`) |
| **Suscriptores** | Logging estructurado (WARN), metricas (contador de intentos duplicados), potencialmente notificacion al usuario |
| **Naturaleza** | Evento de dominio (no de integracion). No modifica estado; es informativo. |

### 2.3 Comando afectado

| Comando | `CargarExtracto` |
|---------|------------------|
| **Flujo normal** | Subir → Parsear → Identificar tarjeta → **Validar unicidad** → Persistir → `ExtractoCreado` |
| **Flujo alterno (duplicado)** | Subir → Parsear → Identificar tarjeta → **Validar unicidad** → `ExtractoDuplicadoDetectado` → excepcion |

> **Nota**: En esta fase actual, el archivo se sube a R2 antes del pre-flight check. En una iteracion futura (feat-004+), se puede optimizar moviendo la subida a R2 despues de validar unicidad. Esto requiere parsear el Excel desde el stream en memoria antes de persistir el archivo, lo cual es un trade-off (memoria vs. storage).

---

## 3. Reglas de negocio

### BN-DUP-01 — Unicidad de extracto por tarjeta + periodo

| Atributo | Valor |
|----------|-------|
| **ID** | BN-DUP-01 |
| **Declaracion** | No puede existir mas de un extracto para la misma tarjeta en el mismo periodo de facturacion |
| **Validacion** | Pre-persistencia: `extracto_repo.get_by_tarjeta_and_periodo(tarjeta_id, periodo_inicio, periodo_fin)` |
| **Resultado (existe)** | Se lanza `ExtractoDuplicadoException(extracto_id_existente)` → router captura → `409 Conflict` |
| **Resultado (no existe)** | El flujo continua normalmente |
| **Safety net** | El constraint `uq_extracto_tarjeta_periodo` en PostgreSQL permanece como ultima linea de defensa ante race conditions |
| **Relacion con BN-01** | BN-01 (requerimientos) dice "ofrecer reemplazar el existente". BN-DUP-01 implementa la deteccion; la funcionalidad de reemplazo queda para feat-004. |
| **Prioridad** | Alta — convierte un error 500 en una respuesta controlada 409 |

### BN-DUP-02 — Periodo requerido para validacion

| Atributo | Valor |
|----------|-------|
| **ID** | BN-DUP-02 |
| **Declaracion** | Si `periodo_inicio` o `periodo_fin` no pudieron extraerse del Excel, no se puede validar unicidad. Se permite la carga pero se registra un WARN. |
| **Fundamento** | Un extracto sin periodo no es comparable. El constraint de BD igual aplicara, pero la validacion pre-flight se omite. |
| **Resultado** | WARN en logs. El extracto se persiste; si hay duplicado real, el constraint de BD lo rechazara. |

---

## 4. Modelo de dominio

### 4.1 Entidades afectadas

```python
# Entidad existente (feat-001/002) — no se modifica
class Extracto(AggregateRoot):
    id: ExtractoId
    tarjeta_id: TarjetaId
    periodo_inicio: date
    periodo_fin: date
    archivo_r2_key: str
    # ... resto de campos
```

### 4.2 Value Object: PeriodoFacturacion (existente)

```python
@dataclass(frozen=True)
class PeriodoFacturacion:
    """Identifica de forma unica un periodo junto con la tarjeta"""
    inicio: date
    fin: date

    def __eq__(self, other): ...
    def __hash__(self): ...
```

### 4.3 Excepcion de dominio nueva

```python
class ExtractoDuplicadoException(DomainException):
    """Se lanza cuando se detecta que el extracto ya existe para la misma tarjeta + periodo"""
    def __init__(self, extracto_id_existente: UUID, tarjeta_id: UUID,
                 periodo_inicio: date, periodo_fin: date):
        self.extracto_id = extracto_id_existente
        self.tarjeta_id = tarjeta_id
        self.periodo_inicio = periodo_inicio
        self.periodo_fin = periodo_fin
        super().__init__(
            f"El extracto para la tarjeta {tarjeta_id} "
            f"periodo {periodo_inicio} - {periodo_fin} ya existe (id: {extracto_id_existente})"
        )
```

### 4.4 Repositorio (existente, feat-002)

```python
class ExtractoRepository:
    # Ya implementado — feat-002
    def get_by_tarjeta_and_periodo(
        self, tarjeta_id: UUID, periodo_inicio: date, periodo_fin: date
    ) -> Optional[Extracto]:
        """Busca un extracto existente por tarjeta + periodo"""
        ...
```

### 4.5 Mapa de bounded contexts

```
┌──────────────────────────────────────┐
│   Carga de Extractos                 │
│   (bounded context afectado)         │
│                                      │
│   feat-002 ──► IdentificarTarjeta    │
│   feat-003 ──► PrevenirDuplicado     │
│                                      │
│        ┌──────────────────┐          │
│        │  Extracto         │          │
│        │  (aggregate root) │          │
│        └────────┬─────────┘          │
│                 │                    │
│    ┌────────────┼────────────┐       │
│    │            │            │       │
│    ▼            ▼            ▼       │
│  Tarjeta    Periodo     Transaccion  │
│  (feat-002) (existente) (feat-001)   │
└──────────────────────────────────────┘
```

---

## 5. Criterios de aceptacion BDD (Gherkin)

> **Engine**: `pytest-bdd` (stack Python)
> **Feature file**: `tests/features/extracto/upload_extracto.feature`

```gherkin
Feature: Prevenir carga de extractos duplicados
  Como usuario
  Quiero que el sistema rechace extractos duplicados con un mensaje claro
  Para no gastar recursos innecesarios y evitar confusion

  Background:
    Given que existe una tarjeta "7681" del banco "Bancolombia"
    And que la tarjeta tiene un extracto cargado para el periodo "2026-05-01" a "2026-05-31"

  Scenario: Rechazar extracto duplicado con el mismo periodo exacto
    When el usuario sube un extracto para la tarjeta "7681" con periodo "2026-05-01" a "2026-05-31"
    Then el sistema responde con codigo 409 Conflict
    And el cuerpo de la respuesta contiene "extracto_id" del extracto ya existente
    And el mensaje incluye el id de la tarjeta y el rango del periodo
    And NO se persiste un nuevo extracto en la base de datos
    And se emite el evento de dominio "ExtractoDuplicadoDetectado"

  Scenario: Permitir carga de extracto con periodo diferente en la misma tarjeta
    When el usuario sube un extracto para la tarjeta "7681" con periodo "2026-06-01" a "2026-06-30"
    Then el sistema responde con codigo 201 Created
    And el extracto se persiste correctamente en la base de datos
    And se emite el evento de dominio "ExtractoCreado"

  Scenario: Permitir carga de extracto con mismo periodo pero diferente tarjeta
    Given que existe una tarjeta "4321" del banco "Bancolombia"
    And que la tarjeta "4321" NO tiene extracto para el periodo "2026-05-01" a "2026-05-31"
    When el usuario sube un extracto para la tarjeta "4321" con periodo "2026-05-01" a "2026-05-31"
    Then el sistema responde con codigo 201 Created

  Scenario: Comportamiento cuando el extracto no tiene periodo detectable
    Given que el archivo Excel no contiene informacion de periodo facturado
    When el usuario sube el extracto para la tarjeta "7681"
    Then el sistema responde con codigo 201 Created
    And se registra un log de nivel WARN indicando "periodo no detectable, validacion de duplicado omitida"
```

---

## 6. Analisis de edge cases

### 6.1 `periodo_inicio` es `None`

| Escenario | Comportamiento |
|-----------|---------------|
| El parser no pudo extraer las fechas del Excel | `get_by_tarjeta_and_periodo()` no se invoca (BN-DUP-02) |
| Se emite WARN: `"periodo no extraido del extracto. Validacion de duplicado omitida"` | |
| El extracto se persiste | Si es duplicado, el constraint `uq_extracto_tarjeta_periodo` lo rechazara |
| **Riesgo**: dos extractos sin periodo para la misma tarjeta | El constraint de BD tiene columnas nullable; si ambas fechas son NULL, la unicidad no se garantiza. **Mitigacion**: evaluar en feat-004 si se debe rechazar la carga cuando el periodo es indetectable. |

### 6.2 Archivo sin informacion de periodo

| Escenario | Comportamiento |
|-----------|---------------|
| El extracto no tiene filas de periodo facturado (formato desconocido) | `periodo_inicio = None`, `periodo_fin = None` |
| Mismo comportamiento que 6.1 | WARN + persistir sin validacion pre-flight |
| **Recomendacion**: Agregar metrica `extract_sin_periodo_total` para monitorear que tan frecuente es esto |

### 6.3 Race condition (concurrencia)

| Escenario | Comportamiento |
|-----------|---------------|
| Dos requests simultaneos suben el mismo extracto (misma tarjeta + mismo periodo) | Ambos pasan el pre-flight check porque aun no se ha persistido ninguno |
| Ambos intentan insertar | Uno gana. El otro recibe `IntegrityError` de PostgreSQL |
| **Estrategia de defensa en profundidad**: | |
| Capa 1 (aplicacion) | `get_by_tarjeta_and_periodo()` pre-flight — evita el 95% de los casos |
| Capa 2 (base de datos) | `uq_extracto_tarjeta_periodo` — safety net para race conditions |
| Capa 3 (aplicacion) | El `IntegrityError` debe capturarse y convertirse en 409 Conflict (no 500) |
| **Tarea T007** | Implementar manejo de `IntegrityError` en el repositorio/capa de infraestructura |

### 6.4 Periodos solapados parcialmente

| Escenario | Comportamiento |
|-----------|---------------|
| Extracto existente: 2026-05-01 a 2026-05-31 | |
| Nuevo extracto: 2026-05-15 a 2026-06-14 | El pre-flight check usa `periodo_inicio AND periodo_fin` exactos. NO detecta solapamiento parcial. |
| **Decision**: La unicidad es por periodo exacto, no por solapamiento. Esto es correcto porque cada banco emite un extracto por periodo fijo. | Si en el futuro se soportan extractos con periodos moviles, se debe cambiar la validacion a `OVERLAPS`. |

### 6.5 Tarjeta no identificada

| Escenario | Comportamiento |
|-----------|---------------|
| feat-002 falla en identificar la tarjeta | El flujo de feat-003 no se ejecuta porque no hay `tarjeta_id` |
| **Dependencia explicita**: feat-003 solo aplica despues de feat-002 exitoso. Si feat-002 lanza excepcion, el flujo completo se aborta antes de llegar al pre-flight check. | |

### 6.6 Multiples bancos — mismo numero de tarjeta

| Escenario | Comportamiento |
|-----------|---------------|
| Dos bancos distintos emiten tarjetas que terminan en los mismos 4 digitos | feat-002 identifica la tarjeta por `(banco_id, ultimos_4_digitos)`, garantizando `tarjeta_id` unico |
| No hay riesgo de colision entre bancos | |

---

## 7. Contrato API (intencion)

### 7.1 Endpoint afectado

```
POST /api/v1/extracts/upload
```

### 7.2 Response — 409 Conflict (nuevo)

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

### 7.3 Response — 201 Created (sin cambios)

El flujo exitoso no cambia.

### 7.4 Response — 409 Conflict (race condition, safety net)

```json
{
  "error": "EXTRACTO_DUPLICADO",
  "message": "Conflicto de concurrencia: el extracto fue creado por otra solicitud simultanea",
  "extracto_id": null
}
```

> Este caso ocurre cuando el pre-flight paso limpio pero el constraint de BD rechazo la insercion. El `extracto_id` no se conoce porque el duplicado lo creo otra transaccion concurrente.

---

## 8. Resumen de artefactos generados

| Artefacto | Ubicacion | Descripcion |
|-----------|-----------|-------------|
| Evento de dominio | `ExtractoDuplicadoDetectado` | Nuevo evento informativo |
| Excepcion de dominio | `ExtractoDuplicadoException` | Nueva excepcion en capa de dominio |
| Regla de negocio | BN-DUP-01 | Validacion pre-persistencia |
| Regla de negocio | BN-DUP-02 | Periodo requerido para validacion |
| Feature BDD | `extracto/upload_extracto.feature` | 4 escenarios |
| API contract | `POST /api/v1/extracts/upload` → `409 Conflict` | Nuevo status code |

---

## 9. Trazabilidad con tareas

| Tarea | Descripcion | Cubierto en |
|-------|-------------|-------------|
| T001 | Analisis DDD | Este documento |
| T002 | API contract 409 | Seccion 7 |
| T003 | Pre-flight check | Seccion 2.1, BN-DUP-01 |
| T004 | Handler 409 | Seccion 7.2 |
| T005 | Test unitario | Seccion 5 (BDD scenarios) |
| T006 | Test integracion | Seccion 5 (BDD scenarios) |
| T007 | Race condition | Seccion 6.3 |
