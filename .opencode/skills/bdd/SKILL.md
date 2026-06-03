---
name: bdd
description: Behavior-Driven Development con lenguaje Gherkin. Usar cuando se definan criterios de aceptacion con lenguaje Gherkin (Given-When-Then) y se automaticen como pruebas vivas de especificacion. Las herramientas de automatizacion dependen del stack definido en docs/architecture.md.
---

# BDD — Behavior-Driven Development

## Principio

BDD es independiente de la tecnologia. El lenguaje Gherkin (Given-When-Then) es universal. Las herramientas de automatizacion (engine BDD, test runner) se toman del stack tecnologico definido en `docs/architecture.md`.

## Flujo BDD

```
Descubrimiento  ->  Formulacion  ->  Automatizacion
```

### 1. Descubrimiento — Refinar requisitos con ejemplos concretos

Realizar sesiones de Example Mapping o Specification by Example con stakeholders.

### 2. Formulacion — Escribir en Gherkin

```gherkin
# features/orders/create_order.feature
Feature: Crear pedido

  Scenario: Pedido valido con items en stock
    Given un producto "Laptop" con stock 10 y precio 1500 USD
    And un cliente autenticado con id "C001"
    When el cliente crea un pedido con 2 unidades de "Laptop"
    Then el pedido se registra con estado "Pendiente"
    And el total del pedido es 3000 USD
    And el stock de "Laptop" se reduce a 8

  Scenario: Cantidad negativa rechazada
    When el cliente intenta crear un pedido con -3 unidades de "Laptop"
    Then el sistema rechaza con error "Order.Quantity.Negative"
```

### 3. Automatizacion — Implementar step definitions

La implementacion de step definitions depende del stack tecnologico en `docs/architecture.md`.

**Ejemplo conceptual (pseudocodigo):**

```pseudocode
@Binding
class CreateOrderSteps:
    repo: IOrderRepository
    mediator: IMediator
    result: Result<OrderDto>

    @Given("un producto \"{name}\" con stock {stock} y precio {price} USD")
    func GivenProductWithStockAndPrice(name, stock, price):
        # Setup

    @When("el cliente crea un pedido con {qty} unidades de \"{product}\"")
    func WhenClientCreatesOrder(qty, product):
        # Act

    @Then("el pedido se registra con estado \"{status}\"")
    func ThenOrderRegisteredWithStatus(status):
        # Assert
```

## Herramientas por ecosistema

| Stack | Engine BDD | Test Runner |
|-------|-----------|-------------|
| .NET Core | Reqnroll (antes SpecFlow) | xUnit |
| Node.js | Cucumber.js | Jest / Vitest |
| Python | Behave / pytest-bdd | pytest |
| Java | Cucumber-JVM | JUnit |
| Go | Godog | testing |

La herramienta concreta se selecciona durante la fase `design` y queda registrada en `docs/architecture.md`.

## Reglas

- Un archivo `.feature` por feature de negocio
- Cada scenario debe ser independiente (no compartir estado entre scenarios)
- Mantener los step definitions reusables (usar parametros, no duplicar)
- Las pruebas BDD son pruebas de aceptacion, no unitarias: validan el sistema completo
- Usar el engine BDD y test runner correspondientes al stack definido en `docs/architecture.md`
