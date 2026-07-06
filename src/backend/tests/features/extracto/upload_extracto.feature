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

  Scenario: Permitir carga de extracto sin periodo facturable detectable (proteccion por hash)
    Given que existe una tarjeta "7681" del banco "Bancolombia"
    And que el archivo Excel no contiene informacion de periodo facturado
    When el usuario sube el extracto para la tarjeta "7681"
    Then el sistema responde con codigo 201 Created
    And el extracto se persiste correctamente en la base de datos
    And se registra un log de nivel WARN indicando que el periodo no es detectable

  Scenario: Rechazar extracto duplicado con mismo hash de archivo
    Given que existe una tarjeta "7681" del banco "Bancolombia"
    And que la tarjeta tiene un extracto cargado con hash "abc123"
    When el usuario sube el mismo archivo Excel con hash "abc123" para la tarjeta "7681"
    Then el sistema responde con codigo 409 Conflict
    And el mensaje indica que el extracto ya existe por hash
