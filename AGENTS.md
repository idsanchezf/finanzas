# AGENTS.md

## Harness Engineering para Desarrollo de Software

Este proyecto utiliza ingenieria de arneses con opencode para orquestar el ciclo de vida completo de desarrollo de software. La tecnologia se define en la fase de diseno con el usuario y se almacena como configuracion en `docs/architecture.md`.

### Estructura

```
.opencode/
  agents/
    leader.md      # Agente lider (orquestador principal)
    analysis.md    # Analisis DDD y requerimientos
    architect.md   # Definicion arquitectonica (architecture.md + ADR)
    design.md      # Contratos API, modelo de datos, integracion + seleccion de tecnologia
    scaffold.md    # Scaffolding de solucion y proyectos
    develop.md     # Implementacion y codificacion
    test.md        # Estrategia de pruebas
    quality.md     # Calidad de codigo y seguridad
    deploy.md      # CI/CD, infraestructura, despliegue
    features.md    # Gestion de features, backlog, ramas, estado
  skills/
    tdd/                   # Test-Driven Development (RED-GREEN-REFACTOR) — generico
      SKILL.md
    bdd/                   # Behavior-Driven Development (Gherkin) — generico
      SKILL.md
    git-flow/              # Estrategia de branching Git Flow — generico
      SKILL.md
    dotnet-microservice/   # Perfil tecnologico: .NET Core
      SKILL.md
    # Opcional: otros perfiles tecnologicos (nodejs, python, java, go, etc.)
```

### Uso

1. Inicia con el agente lider para tareas integrales de desarrollo
2. Cada fase del SDLC tiene un subagente especializado
3. Los subagentes son invocados automaticamente por el lider segun la fase
4. La tecnologia se elige en la fase de **diseno** (`design`) con el usuario
5. Los artefactos generados se almacenan en `docs/` y `src/` segun corresponda

### Instrucciones generales

- La tecnologia y stack se definen durante la fase `design` y se persisten en `docs/architecture.md` en la seccion "Stack tecnologico"
- Seguir Clean Architecture / patron modular y principios SOLID adaptados al stack elegido
- Generar siempre health checks, logging estructurado y metricas
- Usar estrategia Git Flow: cada feature en su propia rama `feature/{id}-{slug}`
- Aplicar TDD (skill `tdd`) en implementacion y BDD (skill `bdd`) en criterios de aceptacion
- Mantener vivo `docs/architecture.md` con ADRs actualizados via agente `architect`

### Validacion de codigo antes de commit

**Obligatorio** ejecutar ambos comandos de ruff y los tests en local antes de cada commit. El pipeline de CI fallara si alguno no pasa:

```bash
# Desde el directorio raiz del proyecto:
docker compose exec backend ruff check src/
docker compose exec backend ruff format --check src/

# Si ruff format reporta archivos que necesitan reformateo:
docker compose exec backend ruff format src/

# Ejecutar todos los tests:
docker compose exec -e PYTHONPATH=/app backend pytest tests/ -v
```

Reglas de linter — **corregir, no ignorar**. Si una regla no puede corregirse, consultar antes de agregarla a `ignore` en `pyproject.toml`. Unica excepcion documentada: `B008` (patron idiomatico de FastAPI: `Depends()`, `Body()`, `File()`, `Query()` en argumentos por defecto).

### Seleccion de tecnologia

La tecnologia se define en la fase `design` y se persiste en `docs/architecture.md` en la tabla "Stack tecnologico":

```markdown
## 5. Stack tecnologico

| Capa | Tecnologia | Version | Justificacion |
|------|-----------|---------|---------------|
| Lenguaje | csharp / typescript / python / java / go | | |
| Runtime | .NET / Node.js / CPython / JVM / Go | version LTS | |
| Framework | ASP.NET Core / Express / FastAPI / Spring Boot / Gin | | |
| ORM | Entity Framework Core / Prisma / SQLAlchemy / Hibernate / GORM | | |
| Base de datos | PostgreSQL / SQL Server / MongoDB | | |
| Cache | Redis | | |
| Mensajeria | RabbitMQ / Kafka / Azure Service Bus | | |
| Testing | xUnit / Vitest / pytest / JUnit / testing | | |
| Logging | Serilog / Winston / logging / Logback / zerolog | | |
| Contenedores | Docker | | |
| Orquestacion | Kubernetes / Docker Compose / Nomad | | |
| CI/CD | GitHub Actions / Azure DevOps / GitLab CI | | |
| Observabilidad | OpenTelemetry + Prometheus + Grafana | | |
```

Todos los agentes subsiguientes leen el stack tecnologico de `docs/architecture.md` y adaptan su comportamiento al stack seleccionado.
