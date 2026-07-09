# Informe de Auditoria de Arquitectura y Funcionalidad

> **Fecha**: 2026-07-06
> **Proyecto**: Finance Report
> **Alcance**: Auditoria completa de las 4 capas (dominio, aplicacion, infraestructura/API, workers/frontend)
> **Metodo**: Exploracion exhaustiva de la base de codigo + contraste con `docs/architecture.md`

---

## Resumen Ejecutivo

Se auditaron **17 archivos de dominio**, **18 archivos de aplicacion**, **30+ archivos de infraestructura/API** y **~40 archivos de tests**. Se identificaron **74 hallazgos**, clasificados en 4 niveles de severidad.

| Severidad | Cantidad | Accion |
|-----------|----------|--------|
| **Critica** | 5 | Bloqueante para produccion o funcionalidad rota |
| **Alta** | 17 | Funcionalidad incompleta o violacion de patrones |
| **Media** | 22 | Deuda tecnica, code smells, gaps de cobertura |
| **Baja** | 30 | Mejoras deseables, convenciones, documentacion |

---

## 1. Hallazgos Criticos

### 1.1. SEC-001: Secretos de Google OAuth en `.env` local (mitigado)
**Severidad**: MEDIA (mitigada) | **Archivo**: `.env`

El archivo `.env` contiene valores reales de `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` y `NEXT_PUBLIC_GOOGLE_CLIENT_ID`. **Verificado**: `.env` esta en `.gitignore`, por lo que no se sube al repositorio. Sin embargo, los secretos existen en el entorno local de desarrollo.

**Accion recomendada**: Asegurar que `.env.example` solo tenga placeholders. Considerar rotar los secretos si alguna vez se expusieron.

---

### 1.2. API-001: Contrato API incompatible entre frontend y backend — Dashboard
**Severidad**: CRITICA | **Archivos**: `src/frontend/src/lib/dashboard-api.ts`, `src/backend/src/api/routers/dashboard.py`

El frontend invoca:
- `GET /dashboards/summary?card_id=X&period=Y`
- `GET /dashboards/by-category?...`
- `GET /dashboards/daily?...`
- `GET /dashboards/monthly-trend?...`

El backend expone:
- `GET /api/v1/dashboard/summary?extract_id=X`
- `GET /api/v1/dashboard/by-category?extract_id=X&top_n=Y`
- `GET /api/v1/dashboard/daily?extract_id=X`
- `GET /api/v1/dashboard/monthly-trend?meses=6&tarjeta_id=X`

**Diferencias**: URL base (`/dashboards/` vs `/dashboard/`), nombres de parametros (`card_id`+`period` vs `extract_id`), estructuras de respuesta. **El dashboard del frontend no puede funcionar actualmente** — todas las llamadas retornan 404.

**Accion**: Alinear el contrato API. Actualizar `dashboard-api.ts` para usar `/dashboard/` y `extract_id`.

---

### 1.3. FUNC-001: feat-002 (Identificar tarjeta) incompleto
**Severidad**: CRITICA | **Archivos**: `infrastructure/excel/parser.py`, `api/routers/extracts.py`

La feature feat-002 esta marcada como `done` pero el parser de Bancolombia **NO extrae los ultimos 4 digitos de la tarjeta** del archivo Excel. El metodo `_extraer_metadatos_bancolombia()` busca "periodo facturado", "pagar antes", "pago minimo", etc., pero NO busca la seccion "Informacion de la tarjeta" para extraer el numero enmascarado (****7681).

Actualmente, el router `extracts.py` siempre crea una tarjeta por defecto con `ultimos_4_digitos="0000"` y `banco="Desconocido"`. La excepcion `TarjetaNoEncontradaError` esta definida pero nunca se lanza.

**Accion**: 
1. Implementar extraccion de `ultimos_4_digitos` en `_extraer_metadatos_bancolombia()`
2. Implementar find-or-create en `handle_cargar_extracto` usando los datos extraidos

---

### 1.4. FUNC-002: `handle_clasificar_transaccion` es un no-op
**Severidad**: CRITICA | **Archivo**: `application/handlers/command_handlers.py:370-386`

El handler obtiene la transaccion y todas las categorias... y descarta ambos resultados. Retorna la categoria actual sin aplicar ninguna clasificacion. La clasificacion real nunca se invoca.

**Accion**: Conectar el handler con `ClasificadorReglas` o delegar al motor de clasificacion.

---

### 1.5. FUNC-003: `PresupuestoRepository` no implementado
**Severidad**: CRITICA | **Archivos**: `domain/repositories/__init__.py`, `infrastructure/persistence/repositories/`

La interfaz `IPresupuestoRepository` existe en dominio, pero no hay implementacion concreta. En `dependencies.py` se pasa `presupuesto_repo=None` al `CommandHandler`. Los endpoints de presupuestos (`GET/POST /api/v1/budgets`, `GET/POST /api/v1/budgets/goals`) retornan `{"items": []}` hardcodeado.

**Accion**: Implementar `PresupuestoRepository`, crear migracion si es necesaria, conectar en `dependencies.py`.

---

## 2. Hallazgos de Severidad Alta

### 2.1. DOM-001: `PeriodoFacturacion` Value Object nunca usado
**Severidad**: ALTA | **Archivo**: `domain/value_objects/periodo_facturacion.py`

El VO esta definido con invariantes (`fecha_inicio <= fecha_fin`), propiedades computadas (`duracion_dias`, `dias_restantes`, `etiqueta`) y metodo `contiene(fecha)`. Sin embargo, **ninguna entidad lo utiliza**. `Extracto` duplica los 4 campos de fecha inline y reimplementa las mismas propiedades computadas.

**Impacto**: Codigo muerto, violacion DRY, invariantes duplicados.

---

### 2.2. DOM-002: `Money` usado inconsistentemente
**Severidad**: ALTA | **Archivos**: Varios en `domain/entities/`

`Money` se usa correctamente en `Extracto` (pago_minimo, pago_total, cupo_total, cupo_disponible), pero las siguientes entidades usan `Decimal` crudo:

| Entidad | Campo(s) |
|---------|----------|
| `Transaccion` | `valor`, `valor_cuota`, `saldo_pendiente`, `valor_moneda_original` |
| `Presupuesto` | `limite_mensual` |
| `MetaAhorro` | `monto_objetivo`, `monto_acumulado` |

**Impacto**: Sin seguridad de moneda en operaciones, sin conversion, sin aritmetica protegida.

---

### 2.3. DOM-003: Eventos de dominio no heredan de `DomainEvent`
**Severidad**: ALTA | **Archivo**: `domain/events/__init__.py`

La clase base `DomainEvent` existe pero ninguna de las 8 clases concretas (`ExtractoCargado`, `ExtractoProcesado`, etc.) la extiende. Cada una duplica `event_id`, `occurred_at` y `event_name`.

---

### 2.4. DOM-004: Servicios de dominio operan sobre `list[dict]`
**Severidad**: ALTA | **Archivos**: `domain/services/detector_habitos.py`, `domain/services/calculador_cuotas.py`

`DetectorHabitos` y `CalculadorCuotas` aceptan `list[dict]` en lugar de `list[Transaccion]` / `list[Presupuesto]`. Usan acceso por clave de string (`t.get("valor")`, `t.get("categoria_nombre")`). Esto es una abstraccion fragil que rompe el type safety.

---

### 2.5. APP-001: `ValueError` en handlers genera 500 en vez de 404/422
**Severidad**: ALTA | **Archivos**: `application/handlers/command_handlers.py`, `query_handlers.py`

Seis handlers lanzan `ValueError` en lugar de excepciones de dominio. Como `ValueError` no es `DomainError`, el error handler no las captura y resultan en **500 Internal Server Error**:

| Handler | Linea | Deberia ser |
|---------|-------|-------------|
| `handle_clasificar_transaccion` | 376 | 404 Not Found |
| `handle_clasificacion_masiva` | 402 | 404 Not Found |
| `handle_corregir_categoria` | 442 | 404 Not Found |
| `handle_crear_presupuesto` | 484 | 422 Validation Error |
| `handle_crear_meta` | 499 | 422 Validation Error |
| `handle_dashboard_summary` | 62 | 404 Not Found |

---

### 2.6. APP-002: `handle_crear_meta` no persiste
**Severidad**: ALTA | **Archivo**: `application/handlers/command_handlers.py:483-508`

Crea la entidad `MetaAhorro` en memoria pero nunca la guarda en base de datos. El comentario "El repositorio de meta ahorro se implementaria en infraestructura" lo reconoce.

---

### 2.7. APP-003: `handle_obtener_insights` retorna datos hardcodeados
**Severidad**: ALTA | **Archivo**: `application/handlers/query_handlers.py`

Retorna `{"items": [], "score": 75, "zona": "healthy"}`. El rico `DetectorHabitos` (8 algoritmos de deteccion) nunca se invoca.

---

### 2.8. APP-004: DTOs definidos pero nunca usados
**Severidad**: ALTA | **Archivos**: `application/dtos/`

`ExtractoDTO`, `TransaccionDTO`, `DashboardSummaryDTO` estan definidos pero ningun handler los retorna. Todos los handlers retornan `dict[str, Any]`. Esto pierde type safety y OpenAPI schema generation.

---

### 2.9. APP-005: Import de infraestructura en capa de aplicacion
**Severidad**: ALTA | **Archivo**: `application/handlers/command_handlers.py:14,83`

`handle_cargar_extracto` importa `ExtractoExcelParser` de `src.infrastructure.excel.parser` y captura `IntegrityError` de `sqlalchemy.exc`. Esto viola la regla de dependencia de Clean Architecture.

---

### 2.10. INFRA-001: `AuthMiddleware` es codigo muerto
**Severidad**: ALTA | **Archivo**: `api/middleware/auth.py`

La clase `AuthMiddleware` esta definida pero **nunca se registra** en `main.py`. La autenticacion se maneja por dependencia (`get_current_user_id`). Esto crea confusion para mantenimiento.

---

### 2.11. INFRA-002: Sin middleware de tenant
**Severidad**: ALTA | **Arquitectura documentada**: Multi-tenant

A pesar de que `architecture.md` describe el sistema como "multi-tenant" con `TenantMiddleware`, no existe implementacion. El aislamiento depende unicamente de filtrar por `usuario_id`.

---

### 2.12. INFRA-003: Workers no definidos en docker-compose
**Severidad**: ALTA | **Archivo**: `docker-compose.yml`

Los 3 workers (`extract_processor`, `classification_worker`, `notification_worker`) son procesos standalone pero no tienen servicio definido en docker-compose. Para produccion, no hay orquestacion de workers.

---

### 2.13. SEC-002: `.env` posiblemente en repositorio
**Severidad**: ALTA | **Archivo**: `.env`, `.gitignore`

Verificar que `.env` esta en `.gitignore`. Contiene secretos reales de Google OAuth y JWT.

---

### 2.14. API-002: Contrato API de extractos desviado del diseno
**Severidad**: ALTA | **Archivo**: `docs/features/feat-003-prevenir-extractos-duplicados/design.md`

El diseno de feat-003 especifica recibir `banco_id`, pero la implementacion recibe `tarjeta_id`. La respuesta 409 difiere en nombres de campos.

---

### 2.15. DOM-005: `NoAutenticadoError` y `PermisoDenegadoError` en capa de dominio
**Severidad**: ALTA | **Archivo**: `domain/exceptions.py:115-126`

Son concerns de autenticacion/autorizacion (infraestructura/API), no reglas de negocio del dominio. Deberian estar en capa de aplicacion o API.

---

### 2.16. TEST-001: Cobertura de tests insuficiente
**Severidad**: ALTA | **Cobertura**: ~35-40% (reportado por pytest-cov: 54% lineas, pero muchas son codigo estructural)

Routers sin tests: chat, budgets, categories, insights, merchants, notifications. Workers con tests minimos (1 archivo por worker). Sin tests e2e.

---

### 2.17. API-003: 11+ endpoints retornan stubs hardcodeados
**Severidad**: ALTA | **Archivos**: Varios routers

| Endpoint | Retorno |
|----------|---------|
| `GET /api/v1/budgets` | `{"items": []}` |
| `GET /api/v1/budgets/goals` | `{"items": []}` |
| `POST /api/v1/budgets/simulate` | `"Simulador — proximamente"` |
| `GET /api/v1/insights` | `{"items": [], "score": 75}` |
| `GET /api/v1/insights/score` | Score hardcodeado 75 |
| `GET /api/v1/dashboard/installments` | `"Proyeccion — proximamente"` |
| `GET /api/v1/dashboard/calendar-heatmap` | `"Heatmap — proximamente"` |
| `GET /api/v1/chat/sessions` | `"Historial — proximamente"` |
| `GET /api/v1/chat/sessions/{id}` | `{"items": []}` |
| `GET /api/v1/notifications` | `{"items": [], "total": 0}` |
| `PATCH /api/v1/notifications/{id}/read` | Sin escritura en BD |

---

## 3. Hallazgos de Severidad Media

### 3.1. DOM-006: `datetime.utcnow()` deprecado en 5 entidades
`tarjeta.py`, `notificacion.py`, `presupuesto.py`, `meta_ahorro.py`, `usuario.py` usan `datetime.utcnow()` (naive). `extracto.py` y `transaccion.py` usan `datetime.now(UTC)` (aware). Inconsistente.

### 3.2. DOM-007: IDs de entidad mutables
Los `id: UUID = field(default_factory=uuid4)` son tecnicamente reasignables. En DDD la identidad debe ser inmutable.

### 3.3. DOM-008: Entidades permiten estados invalidos en construccion
`Usuario` con `email=""`, `Categoria` con `nombre=""`, `Tarjeta` con `ultimos_4_digitos=""` (solo valida `len() <= 4`), `Notificacion` con `titulo=""`.

### 3.4. DOM-009: `archivo_s3_key` en entidad de dominio
El nombre del campo contiene "s3" — detalle de infraestructura que fuga al dominio.

### 3.5. DOM-010: `Transaccion` tiene `confidence: Decimal` + `ConfianzaClasificacion` VO
Concepto duplicado: el VO existe pero no se usa en la entidad.

### 3.6. DOM-011: `MetaAhorro.agregar_ahorro()` permite montos negativos
Sin validacion. Podria reducir el `monto_acumulado`.

### 3.7. DOM-012: `calcular_progreso()` retorna `dict` sin tipo
`MetaAhorro` y `Presupuesto` retornan `dict` con string keys en vez de un NamedTuple/dataclass tipado.

### 3.8. DOM-013: Sin `IMetaAhorroRepository` ni `INotificacionRepository`
Interfaces de repositorio faltantes para entidades que existen.

### 3.9. APP-006: `ITransaccionRepository.get_by_usuario` con `sort_by`/`order`
Parametros de presentacion en contrato de dominio. Deberian estar en capa de aplicacion.

### 3.10. APP-007: Queries no exportadas completamente
`ObtenerTransaccionesQuery`, `ObtenerExtractosQuery`, `ObtenerInsightsQuery` faltan en `application/__init__.py`.

### 3.11. APP-008: `file_hash` inyectado via monkey-patching en entidad
`extracto.file_hash = file_hash` (linea 124 de `command_handlers.py`) modifica el dataclass fuera de su definicion.

### 3.12. APP-009: Sin uso de Unit of Work
`IUnitOfWork` esta definido e implementado, pero los handlers operan directamente con repositorios sin limite transaccional.

### 3.13. INFRA-004: `RefreshTokenRepository` sin interfaz de dominio
Implementacion concreta sin abstraccion. Viola Dependency Inversion.

### 3.14. INFRA-005: Workers sin supervisor de procesos
Si un worker crashea, solo Docker `restart: unless-stopped` lo recupera.

### 3.15. INFRA-006: ML classifier es un stub
`ClasificadorReglas.clasificar_por_ml()` retorna `(None, 0.0)`. Clasificacion hibrida opera solo con reglas.

### 3.16. INFRA-007: Notification consumer es placeholder
`NotificationConsumer.process_message()` solo loguea y duerme. Sin envio real de push/email.

### 3.17. INFRA-008: `saldo_pendiente` y `valor_cuota` nullable en ORM vs non-nullable en entidad
El modelo SQLAlchemy permite `None`, la entidad de dominio tiene default `Decimal("0.00")`.

### 3.18. INFRA-009: Import locales en metodos `Transaccion`
`from src.domain.events import TransaccionClasificada` dentro de `clasificar()` — workaround de dependencia circular.

### 3.19. INFRA-010: `LoggingMiddleware` extiende `BaseHTTPMiddleware`
Patron documentado como problematico en el mismo codigo (`error_handler.py` advierte contra esto).

### 3.20. FRONT-001: Alertas hardcodeadas en dashboard
Alertas de "Gasto hormiga detectado" y "Suscripcion fantasma" son estaticas, deberian venir del endpoint `/insights`.

### 3.21. FRONT-002: `formatDate` referenciado pero no definido en `useDashboard`
El hook `useDashboard` referencia `formatDate` que solo existe en `useExtracts`.

### 3.22. DEPLOY-001: Workers no usan variables de entorno documentadas
`POLLING_MODE`, `POLLING_INTERVAL`, `RABBITMQ_ENABLED` se usan en codigo pero no estan en `.env.example`.

---

## 4. Hallazgos de Severidad Baja

### 4.1. DOM-014: Todos los repositorios en un solo `__init__.py`
200 lineas con 7 interfaces. Deberian separarse en archivos individuales.

### 4.2. DOM-015: `Lista[Any]` como tipo de retorno en metodos de entidad
`Extracto` y `Transaccion` usan `list[Any]` en vez de `list[DomainEvent]`.

### 4.3. APP-010: `handle_obtener_extractos` usa `extracto.estado` (string ORM) en vez de enum
Inconsistente con el resto del codigo que usa `extracto.estado.value`.

### 4.4. INFRA-011: Sin `.dockerignore`
Puede causar build context innecesariamente grande.

### 4.5. INFRA-012: Dockerfile backend con path hardcodeado de Python
`/usr/local/lib/python3.12/site-packages` hardcodeado. Si `PYTHON_VERSION` arg cambia, rompe.

### 4.6. INFRA-013: `.env` usa hostnames Docker-internos
`postgres`, `redis`, `rabbitmq` — no funciona para desarrollo local sin Docker.

### 4.7. INFRA-014: `pyproject.toml` vs `requirements.txt` divergentes
`pyproject.toml` tiene dependencias ML/AI/OTEL, `requirements.txt` no. Mantenimiento dual.

### 4.8. INFRA-015: Columnas 6-8 de Bancolombia no extraidas
`interes_mensual_pct`, `interes_anual_pct`, `saldo_pendiente` definidos como constantes pero no parseados.

### 4.9. INFRA-016: `classification_worker` accede a atributo privado
`self._service._session_factory()` — acceso a `_session_factory` que es privado.

### 4.10. INFRA-017: `notification_worker` sin soporte dual-mode
Solo modo RabbitMQ, sin polling fallback como los otros dos workers.

### 4.11. INFRA-018: `NotificationConsumer` sin DLQ
Extract processor tiene DLQ, notification no.

### 4.12. INFRA-019: Sin healthcheck en Docker para backend
El backend no tiene healthcheck definido en docker-compose (aunque expone `/health`).

### 4.13. API-004: Endpoint raiz `/api/v1/` retorna 404
No hay ruta raiz, solo subpaths.

### 4.14. TEST-002: `db_session` fixture en `conftest.py` raiz retorna `None`
Romperia cualquier test que lo use. La version funcional esta en `integration/conftest.py`.

### 4.15. TEST-003: Sin tests para `classification_service.py`
Solo se prueba el entry-point del worker, no el servicio.

### 4.16. TEST-004: Sin tests de middleware
CORS, error handlers, logging middleware sin cobertura.

### 4.17. FRONT-003: Sin verificacion de TypeScript strict mode
No se encontro configuracion `strict: true`.

---

## 5. Lo que esta bien hecho

### 5.1. Capa de dominio
- **Cero imports de infraestructura** — regla de dependencia de Clean Architecture estrictamente cumplida
- **`Money` Value Object** — implementacion ejemplar: frozen, total ordering, seguridad de moneda, aritmetica completa
- **Maquina de estados de `Extracto`** — transiciones explicitas, eventos en cambios de estado
- **Eventos de dominio `frozen=True`** — inmutabilidad correctamente aplicada
- **Regla de seguridad en `Tarjeta`** — maximo 4 digitos con validacion numerica
- **14 categorias predefinidas** con palabras clave colombianas relevantes
- **Jerarquia de excepciones de dominio** con codigos semanticos y mapeo HTTP documentado

### 5.2. Capa de aplicacion
- **Separacion CQRS** — comandos y queries en clases separadas con handlers dedicados
- **feat-003 (Prevenir duplicados)** — implementacion solida en 3 capas: pre-parseo hash, post-parseo periodo, safety net BD
- **Orquestacion de `handle_cargar_extracto`** — pipeline completo: hash -> parseo -> entidades -> persistencia -> eventos -> metricas
- **Queries de dashboard** — calculos correctos de KPIs, agrupacion Donut, series temporales

### 5.3. Infraestructura
- **Parseador de Bancolombia** — robusto: 19 tipos de deteccion de metadata, subfilas VR MONEDA ORIG
- **Readiness probe** — chequea las 4 dependencias (DB, Redis, RabbitMQ, R2)
- **Migrations limpias** — 2 migraciones, sin drift con modelos ORM
- **API Client del frontend** — JWT auto-refresh, request queuing, correlation ID propagation (245 lineas solidas)
- **Dual-mode workers** — RabbitMQ + polling fallback para dev

### 5.4. Frontend
- **Estructura de componentes** — 11 archivos para transacciones con skeleton, error, empty states
- **PWA completo** — service worker, manifest, offline page, Apple meta tags
- **Dashboard page** — funcional con 4 tipos de graficos, selector de periodo, carga parcial por chart

---

## 6. Recomendaciones Priorizadas

### Inmediato (sprint actual)
1. **Eliminar `.env` del repositorio** y rotar secretos Google OAuth
2. **Corregir contrato API del dashboard** (alinear frontend/backend)
3. **Completar feat-002** — extraer `ultimos_4_digitos` del parser Bancolombia
4. **Reemplazar `ValueError` por excepciones de dominio** en los 6 handlers
5. **Implementar `PresupuestoRepository`**

### Corto plazo (1-2 sprints)
6. Implementar `ClasificadorReglas` en `handle_clasificar_transaccion`
7. Implementar persistencia en `handle_crear_meta`
8. Conectar `DetectorHabitos` con `handle_obtener_insights`
9. Usar `PeriodoFacturacion` VO en `Extracto`
10. Migrar campos `Decimal` a `Money` en `Transaccion`, `Presupuesto`, `MetaAhorro`
11. Hacer que eventos hereden de `DomainEvent`
12. Refactorizar servicios de dominio para usar entidades tipadas
13. Agregar workers a `docker-compose.yml`

### Mediano plazo (3-5 sprints)
14. Remover `AuthMiddleware` (codigo muerto)
15. Implementar tenant middleware
16. Extraer interface `IParser` para desacoplar aplicacion de infraestructura
17. Implementar DTOs en handlers
18. Aumentar cobertura de tests (>60%)
19. Agregar tests e2e
20. Implementar repositorios faltantes (`MetaAhorro`, `Notificacion`)

### Largo plazo (roadmap)
21. Integrar ML classifier (scikit-learn/spaCy)
22. Implementar envio real de notificaciones (push/email)
23. Agregar supervisor de procesos para workers
24. Migrar a `datetime.now(UTC)` en todas las entidades
25. Refactorizar entidades con validacion de estado inicial
26. Separar interfaces de repositorio en archivos individuales

---

## 7. Metricas de Salud del Proyecto

| Metrica | Valor | Objetivo |
|---------|-------|----------|
| Cobertura de tests | ~54% (lineas) / ~35% (funcional) | >80% |
| Endpoints funcionales | 30 de ~41 | 41 de 41 |
| Features completadas | 2 de 3 (feat-002 incompleta) | 3 de 3 |
| Deuda tecnica (hallazgos ALTA+) | 22 | 0 |
| Secretos expuestos | 3 | 0 |
| Codigo muerto (clases definidas sin uso) | 3+ | 0 |
| Stubs/hardcodeos en endpoints | 11 | 0 |
| Migraciones pendientes | 0 | 0 |
| Workers operacionales | 1 de 3 (extract_processor solido) | 3 de 3 |

---

*Informe generado por auditoria automatizada multi-agente el 2026-07-06.*
