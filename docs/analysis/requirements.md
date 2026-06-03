# Requerimientos — App de Clasificacion y Analisis de Gastos Personales

> **Proyecto**: Finance Report
> **Autor**: Prompt generado por experto en finanzas + IA
> **Fecha**: Junio 2026

---

## 1. Contexto del negocio

El usuario recibe mensualmente extractos de su tarjeta de credito en formato Excel (.xlsx) con la siguiente estructura:

### Estructura del extracto bancario

| Seccion | Filas | Contenido |
|---------|-------|-----------|
| Informacion del cliente | 1-3 | Nombre, direccion, ciudad, departamento |
| Informacion de la tarjeta | 5-6 | Numero enmascarado (****7681), millas acumuladas, moneda |
| Periodo facturado | 7-8 | Fechas de corte y limite de pago |
| Resumen financiero | 9-12 | Pago minimo, pago total, cupo total, cupo disponible |
| Tasas de interes | 15-20 | Tasas por tipo de transaccion (compra, avances, mora) |
| Resumen de saldos | 22-28 | Saldo anterior, compras del mes, intereses, abonos, cargos |
| **Transacciones** | **31+** | Datos transaccionales (ver tabla abajo) |
| Separadores | Cada ~20 filas | "Movimientos durante el periodo" + re-encabezado |

### Columnas de la tabla de transacciones

| Columna | Nombre | Tipo | Observaciones |
|---------|--------|------|---------------|
| A | Numero de autorizacion | string | Codigo unico de la transaccion |
| B | Fecha | date | DD/MM/YYYY |
| C | Movimientos | string | Descripcion del comercio (nombres criticos) |
| D | Valor Movimiento | decimal | Monto total. Negativo = abono/pago |
| E | Numero de cuotas | string | Formato "1/1", "1/36", vacio si es abono |
| F | Valor cuota/abono | decimal | Monto mensual de la cuota o abono |
| G | Interes mensual (%) | decimal | 0.0000 si es a una cuota |
| H | Interes anual (%) | decimal | 0.0000 si es a una cuota |
| I | Saldo pendiente | decimal | Capital pendiente por pagar de cuotas |

### Particularidades del formato real

1. **Transacciones en moneda extranjera**: despues de ciertas filas aparece una sub-fila "VR MONEDA ORIG {monto} {codigo}" (EC = Ecuador USD, PA = Panama USD, US = Dolares). Estas sub-filas no tienen numero de autorizacion.
2. **Compras a cuotas**: formato "1/36" con interes mensual y anual no cero. El saldo pendiente muestra el capital restante.
3. **Abonos/pagos**: monto negativo en Valor Movimiento y Valor cuota/abono. Ej: "ABONO SUCURSAL VIRTUAL".
4. **Multiples secciones**: el extracto puede tener "Movimientos durante el periodo" y "Movimientos antes del periodo" cada uno con su propio encabezado repetido.
5. **Nombres de comercio no amigables**: "DLO*DIDI FOOD CO PAYIN", "CGPREZI COM", "PMZ MREMH VISAS SPLIT", "BOLD*Password PC Sas".

### Datos reales observados (extracto mayo 2026)

- **Total transacciones**: ~70 movimientos en 34 dias
- **Categorias observadas**: Transporte (Uber, Didi), Domicilios (Rappi, Didi Food), Supermercado (Exito), Salud (Clinica Oftalmologica, Metlife Seguros), Vestuario (Polo Club, Champs Outlet), Restaurantes (Lenos y Carbon), Tecnologia (BOLD/Password), Viajes (Avianca, Go Quito Hotel, Duty Free), Financieros (Cuota de manejo, Intereses), Hogar (Imusa), Suscripciones (LifeMiles), Ingresos (Abono sucursal virtual)
- **Rango de montos**: $8.789 (Uber minimo) a $5.355.000 (BOLD tecnologia a 2 cuotas)
- **% compras a cuotas**: ~40% de las transacciones son a 36 cuotas (viajes al exterior)
- **Monedas presentes**: COP (pesos colombianos), USD (via Ecuador, Panama)

---

## 2. Actores del sistema

| Actor | Descripcion |
|-------|-------------|
| **Usuario** | Persona natural que carga sus extractos bancarios mensuales y consulta analisis. Usa la app principalmente desde movil (80%). |
| **Admin** | Usuario con permisos de gestion de la plataforma (administracion de usuarios, configuracion global). |
| **Sistema externo - Banco** | Origen de los archivos Excel. En el futuro podria integrarse via API/Open Banking. |

---

## 3. Requerimientos funcionales

### RF01 — Carga y procesamiento de extractos

El sistema debe permitir cargar extractos bancarios mensuales en formato Excel (.xlsx) mediante una interfaz web.

**RF01.1 — Parseo inteligente**: Detectar automaticamente la estructura del archivo:
- Filas de metadatos (cliente, tarjeta, periodo, resumen)
- Encabezados de tabla de transacciones
- Datos transaccionales
- Sub-filas de moneda original (asociarlas a su transaccion padre)
- Separadores de periodo ("Movimientos durante el periodo", "Movimientos antes del periodo")
- El parser debe ser tolerante a variaciones de formato entre distintos bancos.

**RF01.2 — Deduplicacion**: Si un archivo del mismo periodo (mismo mes/año + misma tarjeta) ya fue cargado, preguntar si se reemplaza o se omite.

**RF01.3 — Validacion de integridad**: Verificar que la suma de movimientos + otros cargos cuadre con el pago total del resumen. Reportar discrepancias.

**RF01.4 — Extraccion de metadatos**: Almacenar del extracto: periodo facturado (fecha inicio, fecha fin), fecha de corte, fecha limite de pago, pago minimo, pago total, cupo total, cupo disponible, tasas de interes vigentes.

### RF02 — Clasificacion de gastos

El sistema debe categorizar cada transaccion usando un motor de clasificacion hibrido (reglas + aprendizaje).

**RF02.1 — Categorias predefinidas**:

| Categoria | Palabras clave/patrones | Ejemplos del extracto |
|-----------|------------------------|----------------------|
| **Transporte** | UBER, DIDI, taxi, bus, metro, peaje, parqueadero, TRANSPORTE, COMBUSTIBLE | UBER RIDES, DLO*DIDI |
| **Alimentacion** | RAPPI, DIDI FOOD, EXITO, CARREFOUR, JUMBO, OLIMPLCA, RESTAURANTE, LENOS, CARBON, DOMICILIO, FOOD | RAPPI COLOMBIA, DLO*DIDI FOOD, ALMACENES EXITO, LENOS Y CARBON |
| **Salud** | CLINICA, OFTALMOLOGICA, SEGURO, METLIFE, MEDICO, ODONTOLOGIA, FARMACIA, DROGUERIA, EPS | CLINICA DE OFT SANDIEG, METLIFE COLOMBIA SEG |
| **Vivienda** | ARRIENDO, ADMINISTRACION, SERVICIOS PUBLICOS, EPM, ACUEDUCTO, ENERGIA, GAS, IMUSA, HOME, HOGAR | IMUSA HOME Y COOK |
| **Entretenimiento** | CINE, NETFLIX, SPOTIFY, STARBUCKS, EVENTO, CONCIERTO, TEATRO, PARQUE | STARBUCKS CCI |
| **Vestuario** | ROPA, CALZADO, POLO, CHAMPS, OUTLET, ZARA, H&M, FALABELLA, ARTURO CALLE | POLO CLUB MAYORCA, CHAMPS OUTLET, MARMETTINA AMSTERDAM |
| **Viajes** | AVIANCA, HOTEL, DUTY FREE, AIRBNB, BOOKING, VUELO, TURISMO, AEROLINEA, LATAM | AVIANCA, GO QUITO HOTEL, DUTYFREE PARTNERS |
| **Educacion** | CURSO, LIBRO, UNIVERSIDAD, PLATZI, UDEMY, CERTIFICACION, COLEGIATURA, MATRICULA | — |
| **Tecnologia** | BOLD, PASSWORD, SOFTWARE, APP, HARDWARE, COMPUTADOR, CELULAR, MICROSOFT, GOOGLE, APPLE | BOLD*Password PC Sas |
| **Financieros** | CUOTA DE MANEJO, INTERES, COMISION, RETIRO, AVANCE, SEGURO DE VIDA TARJETA | CUOTA DE MANEJO, COSTO DE LA TRANSACCIO |
| **Suscripciones** | SUSCRIPCI, MEMBRESIA, LICENCIA, PLAN, SUBSCRIPTION, PLUS, PREMIUM, LIFEMILES | SUSCRIPCILIFEMILES PLU |
| **Ingresos** | ABONO, PAGO, REEMBOLSO, CONSIGNACION, TRANSFERENCIA, DEPOSITO | ABONO SUCURSAL VIRTUAL |
| **Servicios** | NEZZIA, CGPREZI, ONLY NATURAL, REGISTRO CIVIL, PTP, GOBIERNO, NOTARIA, TRAMITE | NEZZIA, CGPREZI COM, ONLY NATURAL, PTP - REGISTRO CIVIL |
| **Otros** | (default cuando no hay match) | — |

**RF02.2 — Motor de reglas + ML**:
- Reglas iniciales basadas en palabras clave y expresiones regulares.
- Aprendizaje por correccion del usuario: si el usuario recategoriza una transaccion, el sistema aprende el mapeo comercio → categoria para futuras ocurrencias.
- Nivel de confianza en la clasificacion automatica: alto (>90%), medio (70-90%), bajo (<70%). Las de confianza baja se presentan al usuario para confirmacion en lote.

**RF02.3 — Subcategorias personalizables**: El usuario puede crear, editar y eliminar sus propias categorias y subcategorias. Las categorias predefinidas son la base inicial.

**RF02.4 — Clasificacion masiva**: Capacidad de seleccionar multiples transacciones (checkbox) y asignarles la misma categoria en un solo paso.

### RF03 — Dashboard y visualizaciones

**RF03.1 — Resumen del periodo actual** (widgets tipo tarjeta/KPI):
- Total gastado en el mes (COP)
- Total de ingresos/abonos
- Gasto promedio diario
- % del cupo utilizado
- Dias restantes para el corte
- Variacion vs. mes anterior (indicador visual: flecha verde/roja con %)

**RF03.2 — Grafico de distribucion por categoria (Donut/Pie)**:
- Proporcion del gasto total por categoria.
- Top 3 categorias con etiquetas visibles de valor absoluto y porcentaje.
- Categoria "Otros" agrupa las de menor participacion (< 3% cada una).
- Filtro interactivo: click en una categoria → drill-down a detalle de transacciones.

**RF03.3 — Grafico de gasto diario (Barras apiladas)**:
- Eje X: dia del mes (1-31).
- Eje Y: monto en COP.
- Barras apiladas por categoria (cada color = una categoria).
- Linea de tendencia del promedio diario.
- Tooltip con detalle: fecha, total del dia, desglose por categoria.

**RF03.4 — Grafico de tendencia mensual (Linea)**:
- Eje X: meses (ultimos 6-12).
- Eje Y: monto total.
- Multiples lineas: gastos totales, ingresos/abonos, saldo neto.
- Opcional: linea adicional de gasto promedio movil (3 meses).

**RF03.5 — Treemap de subcategorias**:
- Vista jerarquica para navegar dentro de una categoria y ver sus subcategorias.
- Tamano proporcional al monto. Color por intensidad.
- Interactivo: click para expandir/contraer.

**RF03.6 — Proyeccion de cuotas pendientes**:
- Grafico de barras horizontales: cada compra a cuotas como una barra.
- Eje Y: nombre del comercio + monto original.
- Eje X: tiempo (meses). La barra muestra desde el mes de compra hasta el mes de finalizacion.
- Tooltip: cuota mensual, interes pagado, capital pendiente, fecha de liberacion.
- Indicador visual de "proxima liberacion" (semaforo: verde = > 6 meses, amarillo = 3-6 meses, rojo = < 3 meses para liberarse).

**RF03.7 — Heatmap calendario**:
- Vista de calendario anual con intensidad de color por dia (similar a GitHub contributions).
- Verde claro = gasto bajo, verde oscuro = gasto alto, rojo = gasto excepcional.
- Tooltip: fecha, total del dia, top 3 transacciones.
- Permite identificar patrones (ej. "todos los viernes hay pico de gasto").

### RF04 — Identificacion de malos habitos financieros

El sistema debe generar alertas e insights automaticos basados en patrones de gasto detectados.

**RF04.1 — Deteccion de suscripciones fantasma**:
- **Patron**: mismo comercio, mismo monto (±5%), frecuencia mensual, 3+ ocurrencias consecutivas.
- **Alerta**: "Llevas {N} meses pagando ${MONTO} a {COMERCIO}. Gasto acumulado: ${TOTAL}. ¿Aun lo usas?"
- **Accion sugerida**: "Si cancelas esta suscripcion, ahorraras ${MONTO} al mes (${ANUAL} al ano)."

**RF04.2 — Domicilios excesivos**:
- **Patron**: categoria Alimentacion con subcategoria Domicilios > 30% del total de Alimentacion.
- **Alerta**: "El {PORCENTAJE}% de tu gasto en alimentacion son domicilios (${MONTO}). Esto es {N}% mas que el promedio de usuarios similares."
- **Accion sugerida**: "Reducir Rappi/Didi Food de {FRECUENCIA} a {MITAD} veces al mes te ahorraria ${ESTIMADO}."

**RF04.3 — Gasto emocional por dia de la semana**:
- **Patron**: analisis de varianza del gasto diario agrupado por dia de la semana.
- **Alerta**: "Tus viernes y sabados tienen un gasto {N}% mayor al promedio semanal, principalmente en {CATEGORIA_TOP}."
- **Accion sugerida**: "Definir un presupuesto especifico para fines de semana (actualmente: ${PROMEDIO_FIN_SEMANA})."

**RF04.4 — Micro-gastos frecuentes (efecto cafe latte)**:
- **Patron**: transacciones < ${UMBRAL} con frecuencia > {N} por semana en categoria no esencial.
- **Alerta**: "Realizaste {N} transacciones de Rappi esta semana por un total de ${TOTAL}. La mas frecuente: {COMERCIO}."
- **Accion sugerida**: "Reducir de {N} a {MITAD} veces por semana libera ${AHORRO_MENSUAL} al mes."

**RF04.5 — Costo real de las cuotas**:
- **Patron**: compras a plazos con interes > 0%.
- **Alerta**: "Tu compra en {COMERCIO} por ${MONTO_ORIGINAL} a {N} cuotas tiene un costo total de ${TOTAL_CON_INTERESES}. Los intereses suman ${INTERESES} ({PORCENTAJE}% extra)."
- **Accion sugerida**: "Si adelantas el pago de esta cuota, te ahorras ${INTERESES_RESTANTES} en intereses futuros."

**RF04.6 — Tasa de quemado (burn rate) del cupo**:
- **Patron**: gasto diario actual proyectado hasta la fecha de corte > cupo disponible.
- **Alerta**: "A este ritmo de gasto diario (${PROMEDIO}/dia), agotaras tu cupo disponible (${CUPO_DISPONIBLE}) en {DIAS} dias, {DIAS_ANTES} del corte."
- **Accion sugerida**: "Para mantener un margen del 20%, tu gasto diario no deberia superar ${GASTO_MAXIMO_DIARIO}."

**RF04.7 — Alerta de sobreendeudamiento**:
- **Patron**: pago total > 70% del cupo durante 3+ meses consecutivos.
- **Alerta**: "Llevas {MESES} meses utilizando mas del 70% de tu cupo (actualmente {PORCENTAJE}%). Esto puede afectar tu score crediticio."
- **Accion sugerida**: "Prioriza liberar cupo: tus compras a cuotas actuales suman ${CUOTAS_MENSUALES} al mes y se liberaran completamente en {FECHA_LIBERACION_TOTAL}."

**RF04.8 — Score de salud financiera (0-100)**:
- Calculo basado en:
  - % gastos esenciales vs. discrecionales (peso: 25%)
  - Relacion ingresos/gastos del mes (peso: 30%)
  - Tendencia de ahorro (peso: 20%)
  - Diversificacion del gasto (peso: 15%)
  - % compras a cuotas vs. contado (peso: 10%)
- Visualizacion tipo velocimetro (gauge) con zonas: rojo (0-40), amarillo (40-70), verde (70-100).
- Historico del score mes a mes (grafico de linea).

### RF05 — Presupuestos y metas

**RF05.1 — Presupuesto por categoria**:
- El usuario define un limite mensual por categoria.
- Barra de progreso visual durante el mes: verde (0-50%), amarillo (50-80%), naranja (80-100%), rojo (>100%).
- Alerta push/email cuando se alcanza el 80% y el 100%.

**RF05.2 — Meta de ahorro**:
- El usuario define una meta con: nombre, monto objetivo, fecha deseada (opcional).
- El sistema calcula el ahorro mensual promedio y proyecta la fecha de cumplimiento.
- Barra de progreso con % completado, monto acumulado y meses restantes.

**RF05.3 — Simulador "que pasaria si"**:
- Interfaz interactiva donde el usuario ajusta sliders de gasto por categoria.
- El sistema recalcula en tiempo real el impacto proyectado en 1, 3, 6 y 12 meses.
- Ejemplo: "Si reduces domicilios un 30%, en 6 meses ahorrarias $X y tu score de salud financiera subiria de 55 a 68."

### RF06 — Historial y comparativas

**RF06.1 — Comparativa mes a mes**:
- Tabla pivote: categorias como filas, meses como columnas, monto como valor.
- Colores condicionales: rojo si aumento > 20%, verde si disminuyo > 20%.
- Totales por fila y columna.

**RF06.2 — Comparativa interanual**:
- Mismo mes, ano anterior con variacion porcentual.
- Deteccion de estacionalidad (ej. "En diciembre tu gasto en viajes es consistentemente 3x el promedio").

**RF06.3 — Ranking de comercios**:
- Top 10 comercios por monto acumulado (selector: mes, trimestre, ano).
- Top 10 comercios por frecuencia de visitas.
- Indicador de tendencia: flecha arriba/abajo respecto al periodo anterior.

**RF06.4 — Exportacion de reportes**:
- PDF: diseno profesional tipo informe bancario con graficos, tablas y resumen ejecutivo. Personalizable: seleccionar que secciones incluir.
- Excel: datos crudos de transacciones con categorias, util para contabilidad personal.

### RF07 — Notificaciones y recordatorios

| Tipo | Gatillo | Canal | Mensaje ejemplo |
|------|--------|-------|-----------------|
| Recordatorio de pago | 3 dias antes de fecha limite | Push + Email | "Tu tarjeta ****7681 vence el {FECHA}. Pago minimo: ${MONTO}" |
| Alerta de transaccion grande | Compra > umbral configurable | Push | "Compra detectada: ${MONTO} en {COMERCIO}" |
| Resumen semanal | Cada lunes 8am | Push | "Semana {N}: gastaste ${MONTO}. Top categoria: {CATEGORIA}. 3 alertas nuevas" |
| Alerta de presupuesto | Categoria al 80% y 100% | Push | "Entretenimiento al {PORCENTAJE}%. Quedan ${RESTANTE} para {DIAS} dias" |
| Recordatorio de corte | 2 dias antes del corte | Push | "Corte de tarjeta en 2 dias. Gasto actual: ${MONTO} de ${CUPO}" |
| Alerta de habito | Deteccion de patron negativo | Push + In-app | "Llevas 4 meses de LifeMiles. ¿Cancelar?" |
| Resumen mensual | Dia del corte | Email | Informe completo mensual con graficos |

### RF08 — Asistente financiero con IA

**RF08.1 — Consultas en lenguaje natural**:
- Chat integrado en la interfaz.
- El usuario puede preguntar: "¿cuanto gaste en Rappi el ultimo trimestre?", "¿que mes tuve el mayor gasto en salud?", "¿cuanto me falta para liberar el cupo de la tarjeta?", "¿cual es mi categoria con mayor crecimiento?"
- Respuesta con datos precisos y un mini-grafico relevante.

**RF08.2 — Recomendaciones proactivas**:
- El asistente puede iniciar la conversacion: "Veo que tu gasto en Viajes aumento 300% este mes. ¿Quieres que cree un presupuesto temporal para esta categoria?"

### RF09 — Traduccion de comercios

- Base de conocimiento que mapea nombres criticos de extractos a nombres amigables.
- Ejemplos del extracto real:
  - "DLO*DIDI FOOD CO PAYIN" → "Didi Food"
  - "CGPREZI COM" → "Prezi"
  - "BOLD*Password PC Sas" → "Password (Bold)"
  - "PMZ MREMH VISAS SPLIT" → "Tramite de Visas (Panama)"
- El usuario puede sugerir traducciones. Las traducciones aprobadas se comparten con la comunidad (colaborativo).
- Nivel de confianza en la traduccion. Las no traducidas se muestran con un indicador "¿Ayudanos a identificar este comercio?"

### RF10 — Multi-moneda inteligente

- Detectar transacciones en moneda extranjera (sub-filas "VR MONEDA ORIG").
- Mostrar el monto en la moneda local (COP) usando la tasa de cambio del dia de la transaccion (si esta disponible en el extracto) o una tasa historica estimada.
- Mantener visible el monto en moneda original.
- Indicador visual (flag) para transacciones en moneda extranjera.
- Dashboard: toggle para ver montos en COP o en USD (util para usuarios con ingresos en dolares).

---

## 4. Requerimientos no funcionales

| Categoria | Requerimiento | Detalle |
|-----------|---------------|---------|
| **Disponibilidad** | 99.5% uptime | La carga de extractos es critica (ocurre 1 vez al mes por usuario). El dashboard se consulta con frecuencia. |
| **Seguridad** | Encriptacion de datos financieros | En reposo: AES-256. En transito: TLS 1.3. Nunca almacenar el numero completo de tarjeta (solo ultimos 4 digitos). |
| **Seguridad** | Autenticacion | OAuth2 con Google/Microsoft. 2FA opcional (TOTP). |
| **Seguridad** | Cumplimiento | No almacenar CVV, fecha de expiracion ni PIN. Los datos son de consumo personal, no se comparten con terceros sin consentimiento explicito. |
| **Rendimiento** | Carga de extracto | < 3 segundos para un archivo de ~150 filas. |
| **Rendimiento** | Dashboard | < 1 segundo para cargar graficos y KPIs. Usar cache para consultas frecuentes. |
| **Rendimiento** | Clasificacion automatica | < 500ms para clasificar ~70 transacciones. |
| **Escalabilidad** | Picos de uso | Primeros 5 dias del mes (cierres de tarjeta). Arquitectura serverless/cloud-native con auto-scaling. |
| **Usabilidad** | Mobile-first | El 80% de las consultas se haran desde celular. UI responsive con diseño adaptativo. |
| **Usabilidad** | Onboarding | Tutorial interactivo con extracto de ejemplo precargado para que el usuario entienda el valor sin necesidad de cargar sus datos reales. |
| **Portabilidad** | Migracion de datos | Capacidad de exportar/importar datos historicos si el usuario cambia de banco/tarjeta. API de importacion desde CSV, PDF (otros bancos). |
| **Portabilidad** | Multi-banco | El sistema debe soportar extractos de multiples bancos colombianos (Bancolombia, Davivienda, BBVA, etc.) con diferentes formatos. |
| **Observabilidad** | Monitoreo | Health checks, logging estructurado, metricas de uso (cargas por dia, tiempo de clasificacion, tasa de acierto de categorizacion). |
| **Internacionalizacion** | i18n | Inicialmente en espanol. Preparado para ingles y portugues. |

---

## 5. Reglas de negocio

| ID | Regla | Descripcion |
|----|-------|-------------|
| BN-01 | Un extracto por periodo | No puede haber dos extractos del mismo mes/año para la misma tarjeta. Si se intenta cargar un duplicado, se ofrece reemplazar el existente. |
| BN-02 | Transaccion padre-hijo | Las sub-filas "VR MONEDA ORIG" pertenecen a la transaccion inmediatamente anterior sin numero de autorizacion. No son transacciones independientes. |
| BN-03 | Abonos no son gastos | Las transacciones con Valor Movimiento negativo (ABONO, PAGO) se clasifican como Ingresos y se excluyen de los calculos de gasto. |
| BN-04 | Cuotas = 1 pago contado | Las transacciones con Numero de cuotas "1/1" se consideran pago de contado. El Valor Movimiento completo se asigna al mes actual. |
| BN-05 | Cuotas > 1 pago diferido | Las transacciones con cuotas "1/N" (N>1) generan N pagos futuros. El Valor cuota/abono se asigna al mes actual. El Saldo pendiente es el capital que se pagara en meses futuros. |
| BN-06 | Intereses en cuotas | El costo total real de una compra a cuotas = (Valor cuota/abono × N). El sobrecosto = costo total - Valor Movimiento. |
| BN-07 | Periodo de facturacion vs. periodo de transaccion | Una transaccion pertenece al periodo de facturacion del extracto, no necesariamente al mes calendario en que ocurrio. El sistema debe agrupar por periodo de facturacion. |
| BN-08 | Categoria por defecto | Las transacciones no clasificadas por el motor automatico se asignan a "Otros - Sin clasificar" con confianza baja y se presentan al usuario para revision. |
| BN-09 | Aprendizaje de categorias | Cuando el usuario cambia la categoria de una transaccion, todas las transacciones pasadas y futuras del mismo comercio se actualizan automaticamente. |
| BN-10 | Presupuesto mensual | Los presupuestos se evaluan contra el periodo de facturacion (fecha de corte a fecha de corte), no contra el mes calendario. |

---

## 6. Glosario de dominio

| Termino | Definicion |
|---------|------------|
| **Extracto** | Archivo Excel que contiene el resumen mensual de movimientos de una tarjeta de credito. |
| **Periodo de facturacion** | Rango de fechas entre dos cortes consecutivos de la tarjeta (ej. 15 abril - 18 mayo). |
| **Fecha de corte** | Dia en que el banco cierra el ciclo de facturacion y genera el extracto. |
| **Fecha limite de pago** | Fecha maxima para pagar sin incurrir en mora. |
| **Pago total** | Monto total a pagar para no generar intereses. |
| **Pago minimo** | Monto minimo requerido para mantener la cuenta al dia. |
| **Cupo total** | Limite de credito aprobado por el banco. |
| **Cupo disponible** | Cupo total menos saldo actual y cuotas pendientes. |
| **Transaccion** | Registro individual de un movimiento (compra, pago, comision) en la tarjeta. |
| **Cuota** | Pago parcial periodico de una compra financiada a plazos. "1/36" = cuota 1 de 36. |
| **Compra a contado** | Transaccion de una sola cuota (1/1). Sin intereses. |
| **Compra a plazos** | Transaccion diferida en N cuotas (1/N, N>1). Genera intereses. |
| **Abono** | Pago realizado por el usuario a la tarjeta. Monto negativo en el extracto. |
| **Saldo pendiente** | Capital restante por pagar de una compra a plazos. |
| **Moneda original** | Divisa en que se realizo la transaccion en el extranjero. |
| **VR MONEDA ORIG** | Fila adicional en el extracto que indica el valor en moneda original de una transaccion en el exterior. |
| **Cuota de manejo** | Cobro mensual fijo que el banco hace por el uso de la tarjeta. |
| **Comercio** | Establecimiento donde se realizo la transaccion. |
| **Categoria** | Clasificacion del gasto segun su naturaleza (Transporte, Alimentacion, etc.). |
| **Subcategoria** | Nivel secundario de clasificacion (ej. Alimentacion > Domicilios, Alimentacion > Supermercado). |
| **Score de salud financiera** | Indicador numerico (0-100) que evalua la calidad de las finanzas personales. |
| **Habito financiero** | Patron de gasto recurrente, positivo o negativo. |
| **Tasa de quemado (burn rate)** | Velocidad a la que se consume el cupo disponible de la tarjeta. |
| **Gasto fantasma** | Cobro recurrente por un servicio que el usuario ya no utiliza activamente. |

---

## 7. Diferenciadores (no disponibles en apps actuales)

Basado en analisis de **Mint**, **YNAB**, **Fintonic**, **Wallet by BudgetBakers**, **Spendee**, **MoneyLover**, **Toshl** y **Emma**:

| Funcionalidad | Estado en el mercado | Propuesta |
|---------------|---------------------|-----------|
| **Proyeccion de cuotas** | Ninguna app lo resuelve bien. Algunas muestran gastos recurrentes pero no proyectan el flujo de caja futuro de compras a plazos. | Calendario visual con todas las cuotas pendientes, fecha de liberacion, y simulacion de flujo de caja futuro. "En agosto 2026 se liberan $2.677.500 de BOLD" |
| **Radar de gasto fantasma** | Solo Truebill/RocketMoney lo hace bien, pero son apps separadas para suscripciones. Integrarlo en una app de finanzas personales es diferencial. | Deteccion automatica de suscripciones y cobros recurrentes con notificacion proactiva y calculo de costo anual acumulado. |
| **Traduccion de comercios** | Fintonic lo hace para bancos espanoles. Ninguna app lo hace para bancos colombianos. | Base de conocimiento colaborativa que traduce nombres criticos de extractos bancarios colombianos a nombres amigables. |
| **Multi-moneda inteligente** | Wallet y Spendee lo tienen, pero no integrado con extractos bancarios que mezclan monedas en el mismo archivo (como el caso real). | Deteccion de sub-filas "VR MONEDA ORIG" en extractos colombianos con conversion y visualizacion dual. |
| **Asistente IA en espanol** | Cleo y Emma tienen chat en ingles. No existe un asistente financiero en espanol para el mercado latinoamericano. | Chat integrado con consultas en lenguaje natural y respuestas con datos + graficos. |
| **Comparativa social anonimizada** | Fintonic lo tiene en Espana con datos agregados. No existe en LatAm. | Benchmark de gasto por categoria contra usuarios de perfil similar en la misma ciudad/pais. |
| **Score de salud financiera** | Algunas apps tienen "financial wellness score" pero es generico. | Score adaptado a la realidad colombiana (cupo de tarjeta, tasas de interes locales, categorias de gasto locales). |

---

## 8. Stack tecnologico (a definir en fase de diseno)

La tecnologia se definira en la fase de **diseno** con el usuario y se persistira en `docs/architecture.md`.

### Opciones sugeridas para evaluar

| Capa | Opcion A (recomendada) | Opcion B | Opcion C |
|------|------------------------|----------|----------|
| **Lenguaje** | TypeScript | Python | C# |
| **Runtime** | Node.js | CPython | .NET |
| **Framework** | Next.js (full-stack) | FastAPI + React | ASP.NET Core + Blazor |
| **ORM** | Prisma | SQLAlchemy | Entity Framework Core |
| **Base de datos** | PostgreSQL | PostgreSQL | PostgreSQL |
| **Cache** | Redis | Redis | Redis |
| **Mensajeria** | RabbitMQ | RabbitMQ | Azure Service Bus |
| **Testing** | Vitest | pytest | xUnit |
| **Logging** | Winston | logging (stdlib) | Serilog |
| **Contenedores** | Docker | Docker | Docker |
| **Orquestacion** | Docker Compose | Docker Compose | Kubernetes |
| **CI/CD** | GitHub Actions | GitHub Actions | GitHub Actions |
| **Observabilidad** | OpenTelemetry + Grafana | OpenTelemetry + Grafana | OpenTelemetry + Grafana |
| **LLM / IA** | OpenAI API / Anthropic | OpenAI API / Anthropic | Azure OpenAI |
| **Almacenamiento** | S3-compatible (MinIO) | S3-compatible (MinIO) | Azure Blob Storage |
