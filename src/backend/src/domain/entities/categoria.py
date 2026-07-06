"""Entidad Categoria — Jerarquica con subcategorias.

14 categorias predefinidas + categorias personalizadas por usuario.
Contiene palabras clave para el motor de reglas deterministicas.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


@dataclass
class Categoria:
    """Categoria de gasto con jerarquia de subcategorias."""

    id: UUID = field(default_factory=uuid4)
    nombre: str = ""
    icono: str = "📁"
    color: str = "#6B7280"
    parent_id: UUID | None = None
    es_predefinida: bool = False
    usuario_id: UUID | None = None
    palabras_clave: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def es_subcategoria(self) -> bool:
        """True si esta categoria es una subcategoria (tiene parent)."""
        return self.parent_id is not None

    @property
    def es_personalizada(self) -> bool:
        """True si la categoria fue creada por un usuario (no predefinida)."""
        return not self.es_predefinida and self.usuario_id is not None

    def agregar_palabras_clave(self, palabras: list[str]) -> None:
        """Agrega nuevas palabras clave al motor de reglas."""
        for palabra in palabras:
            if palabra not in self.palabras_clave:
                self.palabras_clave.append(palabra)

    def remover_palabras_clave(self, palabras: list[str]) -> None:
        """Elimina palabras clave existentes."""
        self.palabras_clave = [p for p in self.palabras_clave if p not in palabras]

    # ============================================================
    # Categorias predefinidas (las 14 categorias del sistema)
    # ============================================================
    @classmethod
    def precargadas(cls) -> list[Categoria]:
        """Retorna las 14 categorias predefinidas del sistema."""
        return [
            cls(
                nombre="Alimentacion",
                icono="🍔",
                color="#FF6B6B",
                es_predefinida=True,
                palabras_clave=[
                    "restaurante",
                    "comida",
                    "almuerzo",
                    "cena",
                    "supermercado",
                    "mercado",
                    "didi food",
                    "rappi",
                    "uber eats",
                    "domicilios",
                    "dlo*",
                    "ifood",
                    "pedidos ya",
                ],
            ),
            cls(
                nombre="Transporte",
                icono="🚗",
                color="#4ECDC4",
                es_predefinida=True,
                palabras_clave=[
                    "uber",
                    "didi",
                    "taxi",
                    "transporte",
                    "bus",
                    "metro",
                    "gasolina",
                    "combustible",
                    "peaje",
                    "parqueadero",
                    "estacionamiento",
                    "transmilenio",
                    "cabify",
                    "beat",
                ],
            ),
            cls(
                nombre="Vivienda",
                icono="🏠",
                color="#45B7D1",
                es_predefinida=True,
                palabras_clave=[
                    "arriendo",
                    "administracion",
                    "servicios publicos",
                    "agua",
                    "luz",
                    "gas",
                    "energia",
                    "internet",
                    "aseo",
                    "alcantarillado",
                ],
            ),
            cls(
                nombre="Salud",
                icono="🏥",
                color="#96CEB4",
                es_predefinida=True,
                palabras_clave=[
                    "eps",
                    "medico",
                    "hospital",
                    "farmacia",
                    "medicina",
                    "drogueria",
                    "droga",
                    "medicamento",
                    "consulta",
                    "odontologia",
                    "laboratorio",
                    "examen",
                    "cirugia",
                    "seguro salud",
                    "sanitas",
                    "cruz verde",
                    "eps sanitas",
                ],
            ),
            cls(
                nombre="Entretenimiento",
                icono="🎮",
                color="#FFEAA7",
                es_predefinida=True,
                palabras_clave=[
                    "cine",
                    "teatro",
                    "concierto",
                    "netflix",
                    "spotify",
                    "disney",
                    "hbo",
                    "prime video",
                    "youtube",
                    "videojuego",
                    "steam",
                    "playstation",
                    "xbox",
                    "evento",
                    "espectaculo",
                ],
            ),
            cls(
                nombre="Educacion",
                icono="📚",
                color="#5B2C6F",
                es_predefinida=True,
                palabras_clave=[
                    "universidad",
                    "colegio",
                    "curso",
                    "matricula",
                    "libro",
                    "udemy",
                    "coursera",
                    "platzi",
                    "certificacion",
                    "maestria",
                ],
            ),
            cls(
                nombre="Ropa y Moda",
                icono="👕",
                color="#F39C12",
                es_predefinida=True,
                palabras_clave=[
                    "ropa",
                    "zapato",
                    "tenis",
                    "vestido",
                    "camisa",
                    "pantalon",
                    "falabella",
                    "zara",
                    "hym",
                    "pull&bear",
                    "bershka",
                    "americanino",
                ],
            ),
            cls(
                nombre="Financieros",
                icono="💳",
                color="#E74C3C",
                es_predefinida=True,
                palabras_clave=[
                    "comision",
                    "interes",
                    "cuota manejo",
                    "seguro tarjeta",
                    "cajero",
                    "retiro",
                    "avance",
                    "transferencia",
                    "banco",
                    "impuesto",
                    "4x1000",
                    "gmv",
                    "gasto financiero",
                ],
            ),
            cls(
                nombre="Tecnologia",
                icono="💻",
                color="#3498DB",
                es_predefinida=True,
                palabras_clave=[
                    "computador",
                    "celular",
                    "iphone",
                    "samsung",
                    "xiaomi",
                    "apple",
                    "google",
                    "microsoft",
                    "software",
                    "licencia",
                    "dominio",
                    "hosting",
                    "servidor",
                    "tablet",
                    "audifono",
                ],
            ),
            cls(
                nombre="Viajes",
                icono="✈️",
                color="#1ABC9C",
                es_predefinida=True,
                palabras_clave=[
                    "avion",
                    "vuelo",
                    "hotel",
                    "airbnb",
                    "booking",
                    "despegar",
                    "avianca",
                    "latam",
                    "viva air",
                    "wingo",
                    "tiquete",
                    "pasaje",
                    "equipaje",
                    "maleta",
                ],
            ),
            cls(
                nombre="Servicios",
                icono="🔧",
                color="#95A5A6",
                es_predefinida=True,
                palabras_clave=[
                    "peluqueria",
                    "barberia",
                    "belleza",
                    "spa",
                    "reparacion",
                    "mantenimiento",
                    "lavanderia",
                    "aseo hogar",
                    "limpieza",
                    "plomero",
                    "electricista",
                    "jardineria",
                ],
            ),
            cls(
                nombre="Suscripciones",
                icono="📱",
                color="#8E44AD",
                es_predefinida=True,
                palabras_clave=[
                    "suscripcion",
                    "membresia",
                    "plan",
                    "premium",
                    "icloud",
                    "google one",
                    "amazon prime",
                    "onlyfans",
                    "patreon",
                    "adobe",
                    "canva",
                    "notion",
                    "dropbox",
                ],
            ),
            cls(
                nombre="Mascotas",
                icono="🐾",
                color="#D35400",
                es_predefinida=True,
                palabras_clave=[
                    "veterinaria",
                    "veterinario",
                    "mascota",
                    "perro",
                    "gato",
                    "alimento mascota",
                    "peluqueria canina",
                    "concentrado",
                    "pet shop",
                    "guarderia mascotas",
                ],
            ),
            cls(
                nombre="Otros",
                icono="📦",
                color="#7F8C8D",
                es_predefinida=True,
                palabras_clave=[
                    "varios",
                    "general",
                    "sin clasificar",
                    "desconocido",
                    "compra",
                    "pago",
                    "debito automatico",
                ],
            ),
        ]
