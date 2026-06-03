---
name: tdd
description: Test-Driven Development. Usar cuando se implemente codigo nuevo o se modifique existente. Ciclo RED-GREEN-REFACTOR con persistencia automatica del progreso en .harness-state.json para retomar tras interrupcion. Organizacion: una carpeta por clase, un archivo por metodo con todos sus escenarios, nombramiento Gherkin y patron AAA.
---

# TDD — Test-Driven Development

## Principio

TDD es independiente de la tecnologia. El flujo RED-GREEN-REFACTOR aplica a cualquier lenguaje, framework o stack. Las herramientas especificas (framework de testing, mocking, assertions) se toman del stack tecnologico definido en `docs/architecture.md`.

## Flujo TDD estricto

```
RED  ->  GREEN  ->  REFACTOR
```

## Estructura de archivos de prueba

Organiza las pruebas reflejando la estructura del codigo fuente.

- **Una carpeta por cada clase a testear**
- **Un archivo por cada metodo de negocio**
- **Todos los escenarios de ese metodo dentro del mismo archivo**

```
tests/{Service}.UnitTests/
├── Application/
│   └── Orders/
│       ├── CreateOrderHandlerTests/
│       │   ├── HandleTests.cs                    ← metodo Handle
│       │   └── ValidateTests.cs                  ← metodo Validate (si existe)
│       └── CancelOrderHandlerTests/
│           └── HandleTests.cs
├── Domain/
│   └── Orders/
│       └── OrderTests/
│           ├── AddLineItemTests.cs               ← metodo AddLineItem
│           └── SubmitTests.cs                    ← metodo Submit
```

### Reglas de organizacion

| Regla | Ejemplo |
|-------|---------|
| Carpeta por clase | `CreateOrderHandlerTests/` para `CreateOrderHandler` |
| Un archivo por metodo | `HandleTests.cs` para el metodo `Handle` |
| N escenarios dentro | Todos los casos de prueba del metodo `Handle` en `HandleTests.cs` |
| Clase nombrada `{Metodo}Tests` | `public class HandleTests` |

## Nombramiento Gherkin para escenarios

Dentro de la clase de test, cada metodo de prueba sigue el patron:

```
Should_{ResultadoEsperado}_When_{Condicion}
```

> El nombre del metodo bajo prueba ya esta en la clase y el archivo. No se repite en el nombre del escenario.

### Prefijos segun tipo de escenario

| Prefijo | Uso |
|---------|-----|
| `Should_` | Camino feliz: resultado esperado |
| `Should_ReturnError_When_` | Error de validacion o dominio |
| `Should_Throw_When_` | Excepcion esperada |
| `Should_Rollback_When_` | Compensacion o saga |

## Patron AAA (Arrange, Act, Assert)

Cada metodo de prueba se organiza estrictamente en tres bloques visibles:

```
// Arrange --------------------------------------------------------
//   Preparar mocks, stubs, datos de entrada, estado inicial

// Act ------------------------------------------------------------
//   Una unica llamada al metodo bajo prueba (SUT)

// Assert ----------------------------------------------------------
//   Todas las aserciones + Verify de mocks
```

### Reglas AAA

- Los comentarios `// Arrange`, `// Act`, `// Assert` con separador visual (`----`) son obligatorios
- Una linea en blanco entre bloques
- **Arrange**: mocks, stubs, datos de prueba, callbacks para capturar parametros
- **Act**: una unica expresion llamando al SUT
- **Assert**: aserciones + verificaciones de mocks sin logica adicional

## Flujo TDD paso a paso

### 1. RED — Escribir el primer escenario que falle

1. Crear carpeta `{Clase}Tests/`
2. Crear archivo `{Metodo}Tests.{ext}`
3. Escribir el constructor con mocks y SUT
4. Escribir el primer `Should_{Resultado}_When_{Condicion}` con AAA
5. Ejecutar el test runner → **ROJO**

### 2. GREEN — Escribir el minimo codigo para pasar

Implementar solo lo necesario en el SUT para que ese escenario pase.

Ejecutar el test runner → **VERDE**.

### 3. REFACTOR — Mejorar sin romper

- Extraer validacion a validador dedicado
- Mover logica de creacion a metodo de fabrica en la entidad
- Introducir Value Objects para encapsular reglas
- Ejecutar tests despues de cada micro-cambio

### 4. Siguiente escenario (RED → GREEN → REFACTOR)

Agregar otro escenario en el mismo archivo `HandleTests.{ext}`:

```
Should_ReturnError_When_ProductNotFound
```

Ciclo RED-GREEN-REFACTOR se repite hasta cubrir todos los escenarios del metodo.

## Convenciones de la clase de test

```pseudocode
class {Metodo}Tests:
    // Mocks/stubs como campos
    depMock = Mock(IDependencia)
    otraMock = Mock(IOtraDependencia)

    // SUT — System Under Test
    sut = new {ClaseProbada}(depMock, otraMock)

    test Should_{Resultado}_When_{Condicion}():
        // Arrange --------------------------------------------------------

        // Act ------------------------------------------------------------

        // Assert ----------------------------------------------------------

    test Should_ReturnError_When_{OtraCondicion}():
        // Arrange --------------------------------------------------------

        // Act ------------------------------------------------------------

        // Assert ----------------------------------------------------------

    // ... mas escenarios del mismo metodo
```

Las herramientas concretas (framework, mocking, assertions) se toman de la tabla "Stack tecnologico" en `docs/architecture.md`:
- Fila "Testing" — framework de pruebas
- Fila "Mocking" — libreria de mocking
- Fila "Aserciones" — libreria de aserciones

## Persistencia entre sesiones

El progreso TDD se guarda automaticamente en `.harness-state.json` via el subagente `features`. Si la sesion se corta, al reabrir el `leader` detecta el campo `tdd` y te indica exactamente donde retomar.

Cada vez que completas un paso del ciclo (RED, GREEN, REFACTOR), el agente `develop` invoca:

```
@features tdd save F004 step=green class=CreateOrderHandler method=Handle testFile=.../HandleTests.ext scenario=Should_ReturnError_When_ProductNotFound
```

Esto actualiza el campo `tdd` de la feature en `.harness-state.json`:

```json
"tdd": {
  "step": "green",
  "class": "CreateOrderHandler",
  "method": "Handle",
  "testFile": "tests/.../HandleTests.ext",
  "scenario": "Should_ReturnError_When_ProductNotFound",
  "scenariosCompleted": ["Should_CreateOrder_When_CommandIsValid"],
  "scenariosPending": ["Should_ReturnError_When_ProductNotFound", "Should_RollbackInventory_When_PaymentFails"]
}
```

Al reabrir opencode, el `leader` reporta: _"Retomando F004 en HandleTests.ext, paso GREEN, escenario Should_ReturnError_When_ProductNotFound. Faltan 2 escenarios pendientes."_

## Reglas

- Nunca escribas codigo de produccion sin una prueba que lo exija
- Nunca escribas mas de una prueba unitaria que falle a la vez
- Nunca escribas mas codigo del necesario para pasar la prueba actual
- Corre los tests despues de cada ciclo RED-GREEN-REFACTOR
- Una carpeta por clase probada (`{Clase}Tests/`)
- Un archivo por metodo con **todos** sus escenarios dentro
- Nombramiento Gherkin: `Should_{Resultado}_When_{Condicion}` para cada test
- Patron AAA obligatorio con comentarios `// Arrange -----`, `// Act -----`, `// Assert -----`
- Las herramientas de testing se toman de la tabla "Stack tecnologico" en `docs/architecture.md`
