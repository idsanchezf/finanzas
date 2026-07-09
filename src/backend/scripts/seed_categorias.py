"""Script de seed para categorias predefinidas.

Inserta ~14 categorias raiz con sus subcategorias y palabras clave
para el clasificador deterministico de gastos con tarjeta de credito,
orientado al mercado colombiano.

Ejecutar:
    cd src/backend && python -m scripts.seed_categorias

Variables de entorno:
    DATABASE_URL  — URL de conexion (postgresql+asyncpg://...).
                    Fallback: sqlite+aiosqlite:///finance_report.db
    SQL_ECHO      — Si es "true", imprime queries SQL.

El script es idempotente: verifica si las categorias ya existen
antes de insertar, usando UUID deterministicos basados en el nombre.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Any

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("seed_categorias")

# ---------------------------------------------------------------------------
# Namespace deterministico para UUIDs (idempotencia)
# ---------------------------------------------------------------------------
CATEGORIA_NAMESPACE = uuid.UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")


def cat_uuid(nombre: str) -> uuid.UUID:
    """Genera un UUID v5 deterministico basado en el nombre de la categoria."""
    return uuid.uuid5(CATEGORIA_NAMESPACE, nombre)


def subcat_uuid(parent_name: str, sub_name: str) -> uuid.UUID:
    """Genera un UUID v5 deterministico para una subcategoria."""
    return uuid.uuid5(CATEGORIA_NAMESPACE, f"{parent_name}::{sub_name}")


# ---------------------------------------------------------------------------
# Definicion de categorias predefinidas
# ---------------------------------------------------------------------------
# Cada entrada: (nombre, icono, color, subcategorias, palabras_clave)
# subcategorias: lista de (nombre, palabras_clave)

CATEGORIAS_PREDEFINIDAS: list[dict[str, Any]] = [
    {
        "nombre": "🍔 Comida",
        "icono": "🍔",
        "color": "#EF4444",
        "subcategorias": [
            ("Restaurantes", ["RESTAURANTE", "RESTAURANTES", "ALMUERZO", "CENA"]),
            (
                "Comida rapida",
                [
                    "MCDONALDS",
                    "BURGER KING",
                    "KFC",
                    "SUBWAY",
                    "DOMINOS",
                    "PAPA JOHNS",
                    "PIZZA HUT",
                    "EL CORRAL",
                    "PRESTO",
                ],
            ),
            (
                "Supermercado",
                [
                    "CARULLA",
                    "EXITO",
                    "JUMBO",
                    "D1",
                    "ARA",
                    "OLIMPICA",
                    "SUPERMERCADO",
                    "MERCADO",
                    "LA 14",
                    "ALMACENES EXITO",
                ],
            ),
            (
                "Delivery",
                [
                    "DIDI FOOD",
                    "RAPPI",
                    "UBER EATS",
                    "IFOOD",
                    "DOMICILIOS",
                    "PEDIDOS YA",
                    "DLO*",
                ],
            ),
        ],
        "palabras_clave": [
            "DIDI FOOD",
            "RAPPI",
            "MCDONALDS",
            "DOMICILIOS",
            "CARULLA",
            "EXITO",
            "JUMBO",
            "D1",
            "COMIDA",
            "RESTAURANTE",
            "ALMUERZO",
            "CENA",
            "SUPERMERCADO",
            "MERCADO",
            "DELIVERY",
        ],
    },
    {
        "nombre": "🚗 Transporte",
        "icono": "🚗",
        "color": "#F59E0B",
        "subcategorias": [
            (
                "Gasolina",
                [
                    "TERPEL",
                    "EXXON",
                    "PRIMAX",
                    "BIOMAX",
                    "PETROBRAS",
                    "GASOLINA",
                    "COMBUSTIBLE",
                    "EDS",
                    "ESTACION",
                ],
            ),
            (
                "Taxi/Plataforma",
                [
                    "UBER",
                    "DIDI",
                    "CABIFY",
                    "INDIRIVE",
                    "BEAT",
                    "TAXI",
                    "TRANSPORTE APP",
                ],
            ),
            ("Peajes", ["COLPAGOS", "PEAJE", "AUTOPISTA", "VIA"]),
            (
                "Parqueadero",
                [
                    "PARQUEADERO",
                    "PARKING",
                    "ESTACIONAMIENTO",
                    "PARQUEAR",
                ],
            ),
            (
                "Transporte publico",
                [
                    "TRANSMILENIO",
                    "TRANSMETRO",
                    "MIO",
                    "METRO",
                    "BUS",
                    "SITP",
                    "TRANSPORTE PUBLICO",
                ],
            ),
        ],
        "palabras_clave": [
            "UBER",
            "DIDI",
            "CABIFY",
            "INDIRIVE",
            "TERPEL",
            "EXXON",
            "PRIMAX",
            "COLPAGOS",
            "PEAJE",
            "GASOLINA",
            "TAXI",
            "PARQUEADERO",
            "TRANSMILENIO",
            "BUS",
            "METRO",
            "TRANSPORTE",
        ],
    },
    {
        "nombre": "🏠 Hogar",
        "icono": "🏠",
        "color": "#8B5CF6",
        "subcategorias": [
            ("Arriendo", ["ARRIENDO", "CANON", "RENTA", "ALQUILER", "ARRENDAMIENTO"]),
            (
                "Servicios publicos",
                [
                    "ENEL",
                    "EPM",
                    "CODENSA",
                    "ENERGIA",
                    "LUZ",
                    "ACUEDUCTO",
                    "AGUA",
                    "ALCANTARILLADO",
                    "ASEO",
                    "EMCALI",
                    "EMPRESAS PUBLICAS",
                    "SERVICIOS PUBLICOS",
                ],
            ),
            (
                "Internet/TV",
                [
                    "CLARO",
                    "TIGO",
                    "MOVISTAR",
                    "DIRECTV",
                    "ETB",
                    "INTERNET",
                    "TELEVISION",
                    "FIBRA OPTICA",
                    "TV CABLE",
                ],
            ),
            (
                "Mantenimiento",
                [
                    "MANTENIMIENTO",
                    "REPARACION",
                    "REPARACIONES",
                    "PLOMERO",
                    "ELECTRICISTA",
                    "PINTOR",
                    "OBRERO",
                ],
            ),
            (
                "Decoracion",
                [
                    "HOME",
                    "HOGAR",
                    "DECORACION",
                    "MUEBLES",
                    "HOME CENTER",
                    "HOME SENTRY",
                    "DECORAR",
                    "ILUMINACION",
                    "CASA BONITA",
                ],
            ),
        ],
        "palabras_clave": [
            "ENEL",
            "EPM",
            "CLARO",
            "TIGO",
            "MOVISTAR",
            "HOME",
            "HOGAR",
            "ARRIENDO",
            "SERVICIOS PUBLICOS",
            "MANTENIMIENTO",
            "DECORACION",
            "MUEBLES",
            "HOME CENTER",
        ],
    },
    {
        "nombre": "🛍️ Compras",
        "icono": "🛍️",
        "color": "#EC4899",
        "subcategorias": [
            (
                "Ropa",
                [
                    "FALABELLA",
                    "ZARA",
                    "ADIDAS",
                    "NIKE",
                    "BOSI",
                    "ARTURO CALLE",
                    "KOOS",
                    "STUDIO F",
                    "ELA",
                    "TENNIS",
                    "PULL&BEAR",
                    "BERSHKA",
                    "H&M",
                    "AMERICANINO",
                ],
            ),
            (
                "Tecnologia",
                [
                    "ALKOSTO",
                    "AMAZON",
                    "MERCADOLIBRE",
                    "APPLE",
                    "SAMSUNG",
                    "XIAOMI",
                    "HUAWEI",
                    "LG",
                    "ALCOSTO",
                ],
            ),
            (
                "Mascotas",
                [
                    "VETERINARIA",
                    "VETERINARIO",
                    "MASCOTA",
                    "PERRO",
                    "GATO",
                    "CONCENTRADO",
                    "PET SHOP",
                    "AGROGUAU",
                    "LAIKA",
                    "PETCO",
                    "ALIMENTO MASCOTA",
                ],
            ),
            (
                "Libros",
                [
                    "LIBRO",
                    "LIBRERIA",
                    "PANAMERICANA",
                    "LERNER",
                    "BUSCALIBRE",
                    "BOOK",
                    "LIBROS",
                ],
            ),
            (
                "Farmacia",
                [
                    "CRUZ VERDE",
                    "FARMACIA",
                    "DROGUERIA",
                    "MEDICINA",
                    "MEDICAMENTO",
                    "DROGA",
                    "FARMACODO",
                    "PASTEUR",
                    "DROGAS LA REBAJA",
                    "LOCATEL",
                ],
            ),
        ],
        "palabras_clave": [
            "FALABELLA",
            "ALKOSTO",
            "AMAZON",
            "MERCADOLIBRE",
            "CRUZ VERDE",
            "FARMACIA",
            "VETERINARIA",
            "COMPRA",
            "TIENDA",
            "ONLINE",
            "RETAIL",
        ],
    },
    {
        "nombre": "🎮 Entretenimiento",
        "icono": "🎮",
        "color": "#06B6D4",
        "subcategorias": [
            (
                "Cine/Teatro",
                [
                    "CINEMA",
                    "CINECOLOMBIA",
                    "CINEPLANET",
                    "CINEMARK",
                    "CINE",
                    "TEATRO",
                    "PELICULA",
                    "ROYAL FILMS",
                ],
            ),
            (
                "Streaming",
                [
                    "NETFLIX",
                    "SPOTIFY",
                    "DISNEY",
                    "HBO",
                    "PRIME VIDEO",
                    "YOUTUBE PREMIUM",
                    "APPLE TV",
                    "PARAMOUNT",
                    "STAR+",
                ],
            ),
            (
                "Juegos",
                [
                    "STEAM",
                    "PLAYSTATION",
                    "PLAY STATION",
                    "XBOX",
                    "NINTENDO",
                    "EPIC GAMES",
                    "VIDEOJUEGO",
                    "JUEGO",
                ],
            ),
            (
                "Eventos",
                [
                    "EVENTO",
                    "CONCIERTO",
                    "FESTIVAL",
                    "ESTEREO PICNIC",
                    "JAMMING",
                    "TICKET",
                    "BOLETERIA",
                    "TUBOLETA",
                ],
            ),
            ("Musica", ["MUSICA", "MUSICAL", "INSTRUMENTO", "GUITARRA", "CONCIERTO"]),
        ],
        "palabras_clave": [
            "CINEMA",
            "CINECOLOMBIA",
            "NETFLIX",
            "SPOTIFY",
            "DISNEY",
            "HBO",
            "STEAM",
            "PLAYSTATION",
            "CINE",
            "TEATRO",
            "CONCIERTO",
        ],
    },
    {
        "nombre": "✈️ Viajes",
        "icono": "✈️",
        "color": "#3B82F6",
        "subcategorias": [
            (
                "Vuelos",
                [
                    "AVIANCA",
                    "LATAM",
                    "WINGO",
                    "VIVA AIR",
                    "VUELO",
                    "TICKETE",
                    "PASAJE",
                    "AEROLINEA",
                    "AVION",
                    "JETSMART",
                    "COPA AIRLINES",
                    "EASYFLY",
                ],
            ),
            (
                "Hoteles",
                [
                    "HOTEL",
                    "HOTELES",
                    "ALOJAMIENTO",
                    "HOSPEDAJE",
                    "ESTADIA",
                    "RESORT",
                    "APARTA HOTEL",
                ],
            ),
            (
                "Turismo",
                [
                    "DESPEGAR",
                    "BOOKING",
                    "AIRBNB",
                    "EXPEDIA",
                    "KAYAK",
                    "TRIPADVISOR",
                    "TURISMO",
                    "TOUR",
                    "EXCURSION",
                    "VIAJE",
                ],
            ),
            (
                "Alquiler auto",
                [
                    "RENT A CAR",
                    "ALQUILER AUTO",
                    "ALQUILER CARRO",
                    "LOCALIZA",
                    "HERTZ",
                    "AVIS",
                    "RENTAR AUTO",
                ],
            ),
        ],
        "palabras_clave": [
            "AVIANCA",
            "LATAM",
            "WINGO",
            "DESPEGAR",
            "BOOKING",
            "AIRBNB",
            "VUELO",
            "HOTEL",
            "VIAJE",
            "TURISMO",
        ],
    },
    {
        "nombre": "💪 Salud",
        "icono": "💪",
        "color": "#10B981",
        "subcategorias": [
            (
                "Gimnasio",
                [
                    "GYM",
                    "SMARTFIT",
                    "BODYTECH",
                    "GIMNASIO",
                    "FITNESS",
                    "CROSSFIT",
                    "SPINNING",
                    "ATHLETIC",
                ],
            ),
            (
                "Medico",
                [
                    "EPS",
                    "SURA",
                    "SANITAS",
                    "COMPENSAR",
                    "NUEVA EPS",
                    "MEDICO",
                    "HOSPITAL",
                    "CLINICA",
                    "CONSULTA",
                    "LABORATORIO",
                    "EXAMEN",
                    "CIRUGIA",
                ],
            ),
            (
                "Dental",
                [
                    "ODONTO",
                    "DENTAL",
                    "ORTODONCIA",
                    "ODONTOLOGIA",
                    "ODONTOLOGO",
                    "BRACKETS",
                    "DISENO SONRISA",
                ],
            ),
            (
                "Seguro salud",
                [
                    "SEGURO",
                    "POLIZA SALUD",
                    "MEDICINA PREPAGADA",
                    "COLSANITAS",
                    "SEGURO DE SALUD",
                    "PLAN COMPLEMENTARIO",
                ],
            ),
        ],
        "palabras_clave": [
            "GYM",
            "SMARTFIT",
            "BODYTECH",
            "EPS",
            "SURA",
            "ODONTO",
            "MEDICO",
            "HOSPITAL",
            "CLINICA",
            "SALUD",
            "DENTAL",
        ],
    },
    {
        "nombre": "🎓 Educacion",
        "icono": "🎓",
        "color": "#6366F1",
        "subcategorias": [
            (
                "Universidad",
                [
                    "UDEA",
                    "UNIVERSIDAD",
                    "MATRICULA",
                    "PENSION",
                    "SEMESTRE",
                    "POSTGRADO",
                    "MAESTRIA",
                    "DOCTORADO",
                    "UNIANDES",
                    "JAVERIANA",
                    "ICESI",
                    "EAFIT",
                    "UNINORTE",
                    "SERGIO ARBOLEDA",
                    "TADEO",
                ],
            ),
            (
                "Cursos",
                [
                    "PLATZI",
                    "UDEMY",
                    "CURSERA",
                    "DOMESTIKA",
                    "CREHANA",
                    "COURSERA",
                    "CURSO",
                    "CERTIFICACION",
                    "TALLER",
                    "WORKSHOP",
                    "CAPACITACION",
                ],
            ),
            (
                "Libros",
                [
                    "LIBRO",
                    "LIBROS",
                    "EDUCACION",
                    "TEXTO",
                    "PANAMERICANA",
                    "BOOKS",
                ],
            ),
            (
                "Suscripciones",
                [
                    "SUSCRIPCION EDUCATIVA",
                    "MEMBRESIA",
                    "LICENCIA",
                    "MATRICULA ONLINE",
                ],
            ),
        ],
        "palabras_clave": [
            "UDEA",
            "UNIVERSIDAD",
            "PLATZI",
            "UDEMY",
            "CURSERA",
            "CURSO",
            "MATRICULA",
            "EDUCACION",
            "CERTIFICACION",
        ],
    },
    {
        "nombre": "💰 Ingresos",
        "icono": "💰",
        "color": "#22C55E",
        "subcategorias": [
            (
                "Salario",
                [
                    "ABONO",
                    "SALARIO",
                    "NOMINA",
                    "PAGO NOMINA",
                    "PAGO SALARIAL",
                    "HONORARIOS",
                    "SUELDO",
                ],
            ),
            (
                "Freelance",
                [
                    "FREELANCE",
                    "CONSULTORIA",
                    "PROYECTO",
                    "ASESORIA",
                    "INDEPENDIENTE",
                    "CONTRATO PRESTACION SERVICIOS",
                    "UPWORK",
                    "FIVERR",
                    "WORKANA",
                ],
            ),
            (
                "Reembolso",
                [
                    "REEMBOLSO",
                    "DEVOLUCION",
                    "REINTEGRO",
                    "CASHBACK",
                    "REVERSA",
                    "NOTA CREDITO",
                ],
            ),
            (
                "Transferencia",
                [
                    "TRANSFERENCIA",
                    "CONSIGNACION",
                    "DEPOSITO",
                    "PAGO RECIBIDO",
                    "GIRO",
                    "PSE RECIBIDO",
                ],
            ),
        ],
        "palabras_clave": [
            "ABONO",
            "PAGO",
            "SALARIO",
            "TRANSFERENCIA",
            "REEMBOLSO",
            "NOMINA",
            "DEVOLUCION",
            "CONSIGNACION",
            "DEPOSITO",
        ],
    },
    {
        "nombre": "💳 Servicios Financieros",
        "icono": "💳",
        "color": "#64748B",
        "subcategorias": [
            (
                "Comisiones",
                [
                    "COMISION",
                    "COMISION BANCARIA",
                    "COMISIONES",
                    "CARGO BANCARIO",
                    "COSTO TRANSFERENCIA",
                ],
            ),
            (
                "Intereses",
                [
                    "INTERES",
                    "INTERESES",
                    "TASA",
                    "INTERES CORRIENTE",
                    "INTERES MORA",
                ],
            ),
            (
                "Seguros",
                [
                    "SEGURO",
                    "SEGURO DE VIDA",
                    "SEGURO TARJETA",
                    "POLIZA",
                    "ASISTENCIA",
                    "PROTECCION TARJETA",
                ],
            ),
            (
                "Cuota manejo",
                [
                    "CUOTA MANEJO",
                    "CUOTA DE MANEJO",
                    "MANEJO TARJETA",
                    "CARGO FIJO",
                    "ADMINISTRACION TARJETA",
                ],
            ),
        ],
        "palabras_clave": [
            "COMISION",
            "INTERES",
            "SEGURO",
            "CUOTA MANEJO",
            "BANCARIO",
            "TARJETA",
            "CARGO FIJO",
            "FINANCIERO",
        ],
    },
    {
        "nombre": "👕 Ropa y Calzado",
        "icono": "👕",
        "color": "#D946EF",
        "subcategorias": [
            (
                "Ropa",
                [
                    "ZARA",
                    "ARTURO CALLE",
                    "STUDIO F",
                    "ELA",
                    "TENNIS",
                    "PULL&BEAR",
                    "BERSHKA",
                    "H&M",
                    "AMERICANINO",
                    "FALABELLA",
                    "ROPABELLA",
                ],
            ),
            (
                "Calzado",
                [
                    "ADIDAS",
                    "NIKE",
                    "BOSI",
                    "KOOS",
                    "ZAPATO",
                    "TENIS",
                    "CALZADO",
                    "ZAPATERIA",
                    "CROYDON",
                    "REEBOK",
                    "PUMA",
                    "NEW BALANCE",
                    "UNDER ARMOUR",
                ],
            ),
            (
                "Accesorios",
                [
                    "ACCESORIO",
                    "ACCESORIOS",
                    "JOYERIA",
                    "RELOJ",
                    "LENTES",
                    "GAFAS",
                    "BOLSOS",
                    "CARTERA",
                    "MOCHILA",
                    "TOTTO",
                    "GEF",
                    "PIEL",
                ],
            ),
        ],
        "palabras_clave": [
            "ZARA",
            "ADIDAS",
            "NIKE",
            "BOSI",
            "ARTURO CALLE",
            "KOOS",
            "ROPA",
            "CALZADO",
            "ZAPATO",
            "TENIS",
            "MODA",
            "ACCESORIOS",
        ],
    },
    {
        "nombre": "🎁 Regalos",
        "icono": "🎁",
        "color": "#F97316",
        "subcategorias": [
            (
                "Regalos",
                [
                    "REGALO",
                    "REGALOS",
                    "OBSEQUIO",
                    "DETALLE",
                    "CUMPLEANOS",
                    "NAVIDAD",
                    "AMIGO SECRETO",
                    "FLORES",
                ],
            ),
            (
                "Donaciones",
                [
                    "DONACION",
                    "DONACIONES",
                    "CARIDAD",
                    "BENEFICENCIA",
                    "FUNDACION",
                    "ONG",
                    "CROWDFUNDING",
                    "GOFUNDME",
                ],
            ),
        ],
        "palabras_clave": [
            "REGALO",
            "DONACION",
            "DONACIONES",
            "OBSEQUIO",
            "FLORES",
            "FUNDACION",
            "BENEFICENCIA",
        ],
    },
    {
        "nombre": "📱 Telecomunicaciones",
        "icono": "📱",
        "color": "#0EA5E9",
        "subcategorias": [
            (
                "Celular",
                [
                    "CLARO",
                    "MOVISTAR",
                    "TIGO",
                    "WOM",
                    "VIRGIN",
                    "CELULAR",
                    "TELEFONO",
                    "LINEA",
                    "PLAN MOVIL",
                ],
            ),
            (
                "Internet",
                [
                    "INTERNET",
                    "FIBRA",
                    "BANDA ANCHA",
                    "WIFI",
                    "ETB",
                    "MOVISTAR FIBRA",
                ],
            ),
            (
                "Plan datos",
                [
                    "PLAN DATOS",
                    "RECARGA",
                    "PAQUETE DATOS",
                    "PLAN CELULAR",
                    "PLAN MOVIL",
                    "RECARGA MOVIL",
                ],
            ),
        ],
        "palabras_clave": [
            "CLARO",
            "MOVISTAR",
            "TIGO",
            "WOM",
            "VIRGIN",
            "CELULAR",
            "INTERNET",
            "PLAN",
            "RECARGA",
            "TELEFONO",
            "FIBRA",
            "LINEA",
        ],
    },
    {
        "nombre": "🔧 Otros",
        "icono": "🔧",
        "color": "#9CA3AF",
        "subcategorias": [
            (
                "Miscelaneos",
                [
                    "OTROS",
                    "VARIOS",
                    "MISCELANEOS",
                    "GENERAL",
                    "NO CLASIFICADO",
                    "PAGO VARIOS",
                ],
            ),
            (
                "No clasificado",
                [
                    "SIN CLASIFICAR",
                    "DESCONOCIDO",
                    "NO IDENTIFICADO",
                    "COMPRA",
                    "PAGO",
                    "DEBITO AUTOMATICO",
                ],
            ),
        ],
        "palabras_clave": [
            "OTROS",
            "VARIOS",
            "MISCELANEOS",
            "NO CLASIFICADO",
            "DESCONOCIDO",
            "COMPRA",
            "PAGO",
            "GENERAL",
        ],
    },
]


# ---------------------------------------------------------------------------
# Funcion principal de seed
# ---------------------------------------------------------------------------
async def ensure_tables(session_factory) -> None:
    """Crea las tablas en la BD si no existen (para SQLite/dev).

    En PostgreSQL se asume que Alembic ya creo las tablas.
    Esta funcion es un fallback para entornos de desarrollo.
    """
    from src.infrastructure.persistence.models import Base

    engine = session_factory.kw["bind"]

    async with engine.begin() as conn:
        from sqlalchemy import inspect

        # Usar run_sync para verificar existencia de tablas
        def _check_tables(sync_conn):
            insp = inspect(sync_conn)
            tables = insp.get_table_names()
            return tables

        existing_tables = await conn.run_sync(_check_tables)

        if "categorias" not in existing_tables:
            logger.info("Creando tablas (no existen en esta BD)...")
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Tablas creadas exitosamente.")
        else:
            logger.debug("Tablas ya existen, omitiendo create_all.")


async def seed_categorias(
    session_factory,
    rebuild: bool = False,
) -> dict[str, int]:
    """Inserta las categorias predefinidas en la BD.

    Args:
        session_factory: SQLAlchemy async_sessionmaker.
        rebuild: Si True, elimina las categorias predefinidas existentes
                 y las vuelve a insertar.

    Returns:
        dict con conteo: {"padres": n, "subcategorias": m, "total": n+m}
    """
    from src.infrastructure.persistence.models import CategoriaModel
    from sqlalchemy import select, delete

    # Asegurar que las tablas existen (para SQLite/dev)
    await ensure_tables(session_factory)

    async with session_factory() as session:
        # Verificar si ya existen categorias predefinidas
        stmt = select(CategoriaModel).where(CategoriaModel.es_predefinida == True)
        result = await session.execute(stmt)
        existing = result.scalars().all()

        if existing and not rebuild:
            parent_count = sum(1 for c in existing if c.parent_id is None)
            sub_count = sum(1 for c in existing if c.parent_id is not None)
            logger.info(
                "Categorias predefinidas ya existen: %d padres, %d subcategorias. "
                "Usa --rebuild para reinsertar.",
                parent_count,
                sub_count,
            )
            return {"padres": parent_count, "subcategorias": sub_count, "total": len(existing)}

        # Si rebuild, eliminar las existentes
        if existing and rebuild:
            stmt_delete = delete(CategoriaModel).where(CategoriaModel.es_predefinida == True)
            # Eliminar subcategorias primero (por FK self-referencial)
            stmt_delete_subs = delete(CategoriaModel).where(
                CategoriaModel.es_predefinida == True,
                CategoriaModel.parent_id.isnot(None),
            )
            stmt_delete_parents = delete(CategoriaModel).where(
                CategoriaModel.es_predefinida == True,
                CategoriaModel.parent_id.is_(None),
            )
            await session.execute(stmt_delete_subs)
            await session.execute(stmt_delete_parents)
            await session.flush()
            logger.info("Categorias predefinidas eliminadas para rebuild.")

        now = datetime.now(timezone.utc)
        padres_insertados = 0
        subcategorias_insertadas = 0

        for cat_data in CATEGORIAS_PREDEFINIDAS:
            # Insertar categoria padre
            padre = CategoriaModel(
                id=cat_uuid(cat_data["nombre"]),
                nombre=cat_data["nombre"],
                icono=cat_data["icono"],
                color=cat_data["color"],
                parent_id=None,
                es_predefinida=True,
                usuario_id=None,
                palabras_clave=cat_data["palabras_clave"],
                created_at=now,
            )
            session.add(padre)
            padres_insertados += 1

            # Insertar subcategorias
            for sub_nombre, sub_palabras in cat_data["subcategorias"]:
                sub = CategoriaModel(
                    id=subcat_uuid(cat_data["nombre"], sub_nombre),
                    nombre=sub_nombre,
                    icono="",  # subcategorias no necesitan icono propio
                    color=cat_data["color"],  # heredan color del padre
                    parent_id=cat_uuid(cat_data["nombre"]),
                    es_predefinida=True,
                    usuario_id=None,
                    palabras_clave=sub_palabras,
                    created_at=now,
                )
                session.add(sub)
                subcategorias_insertadas += 1

        await session.commit()
        total = padres_insertados + subcategorias_insertadas
        logger.info(
            "Seed completado: %d categorias padre, %d subcategorias (%d total).",
            padres_insertados,
            subcategorias_insertadas,
            total,
        )
        return {
            "padres": padres_insertados,
            "subcategorias": subcategorias_insertadas,
            "total": total,
        }


# ---------------------------------------------------------------------------
# Creacion de sesion (soporta PostgreSQL y SQLite)
# ---------------------------------------------------------------------------
def _get_session_factory():
    """Crea una session factory async basada en DATABASE_URL del entorno.

    Fallback: sqlite+aiosqlite:///finance_report.db para desarrollo local.
    """
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    database_url = os.getenv(
        "DATABASE_URL",
        "sqlite+aiosqlite:///finance_report.db",
    )

    # Si la URL es postgresql:// o postgresql+asyncpg://, usarla tal cual.
    # Si es sqlite+aiosqlite://, usarla tal cual.
    # Si es postgresql:// sin driver async, convertir a asyncpg.
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)

    echo = os.getenv("SQL_ECHO", "false").lower() == "true"

    engine = create_async_engine(
        database_url,
        echo=echo,
        pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
        max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10")),
    )

    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


# ---------------------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------------------
async def main() -> None:
    """Punto de entrada del script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Seed de categorias predefinidas para Finance Report"
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Elimina y reinserta todas las categorias predefinidas.",
    )
    args = parser.parse_args()

    logger.info("Iniciando seed de categorias predefinidas...")
    logger.info(
        "DATABASE_URL: %s",
        os.getenv("DATABASE_URL", "sqlite+aiosqlite:///finance_report.db (fallback)"),
    )

    try:
        session_factory = _get_session_factory()
    except Exception as exc:
        logger.error("Error al crear conexion a BD: %s", exc)
        sys.exit(1)

    try:
        resultado = await seed_categorias(session_factory, rebuild=args.rebuild)

        # Resumen final
        print("\n" + "=" * 60)
        print("  SEED DE CATEGORIAS PREDEFINIDAS — RESUMEN")
        print("=" * 60)
        print(f"  Categorias padre:     {resultado['padres']:>4}")
        print(f"  Subcategorias:        {resultado['subcategorias']:>4}")
        print("-" * 60)
        print(f"  TOTAL:                {resultado['total']:>4}")
        print("=" * 60)

        if resultado["padres"] >= 14:
            print("  [OK] Se insertaron al menos 14 categorias raiz.")
        else:
            print(f"  [WARN] Solo {resultado['padres']} categorias raiz (< 14 esperadas).")
        print("=" * 60 + "\n")

    except Exception as exc:
        logger.exception("Error durante el seed: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
