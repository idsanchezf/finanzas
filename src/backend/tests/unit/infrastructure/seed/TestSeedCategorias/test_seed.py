"""Test unitario para el script seed_categorias.

Verifica que las categorias predefinidas cumplan con los requisitos minimos:
- Al menos 14 categorias raiz (padres)
- Cada categoria tiene subcategorias, icono, color y palabras clave
- Los UUID son deterministicos (idempotencia)
"""

from __future__ import annotations

import pytest

from scripts.seed_categorias import (
    CATEGORIAS_PREDEFINIDAS,
    cat_uuid,
    subcat_uuid,
)


class TestCategoriasPredefinidas:
    """Verifica la estructura de datos de categorias predefinidas."""

    def test_al_menos_14_categorias_padre(self):
        """Todas las 14 categorias raiz definidas en la tabla de requerimientos."""
        count = len(CATEGORIAS_PREDEFINIDAS)
        assert count >= 14, (
            f"Se esperaban al menos 14 categorias predefinidas, "
            f"pero se encontraron {count}"
        )

    def test_cada_categoria_tiene_nombre_no_vacio(self):
        """Cada categoria padre tiene nombre, icono y color definidos."""
        for cat in CATEGORIAS_PREDEFINIDAS:
            assert cat["nombre"], f"Categoria sin nombre: {cat}"
            assert cat["icono"], f"Categoria '{cat['nombre']}' sin icono"
            assert cat["color"], f"Categoria '{cat['nombre']}' sin color"
            # El color debe ser un hex valido (7 caracteres: #000000)
            assert cat["color"].startswith("#"), (
                f"Categoria '{cat['nombre']}': color '{cat['color']}' no empieza con #"
            )
            assert len(cat["color"]) == 7, (
                f"Categoria '{cat['nombre']}': color '{cat['color']}' "
                f"no tiene 7 caracteres"
            )

    def test_cada_categoria_tiene_subcategorias(self):
        """Cada categoria padre tiene al menos 2 subcategorias."""
        for cat in CATEGORIAS_PREDEFINIDAS:
            assert len(cat["subcategorias"]) >= 2, (
                f"Categoria '{cat['nombre']}' tiene menos de 2 subcategorias "
                f"({len(cat['subcategorias'])})"
            )

    def test_cada_categoria_tiene_palabras_clave(self):
        """Cada categoria padre tiene al menos 3 palabras clave para el clasificador."""
        for cat in CATEGORIAS_PREDEFINIDAS:
            assert len(cat["palabras_clave"]) >= 3, (
                f"Categoria '{cat['nombre']}' tiene menos de 3 palabras clave "
                f"({len(cat['palabras_clave'])})"
            )

    def test_subcategorias_tienen_palabras_clave(self):
        """Cada subcategoria tiene al menos 1 palabra clave."""
        for cat in CATEGORIAS_PREDEFINIDAS:
            for sub_name, sub_keywords in cat["subcategorias"]:
                assert len(sub_keywords) >= 1, (
                    f"Subcategoria '{sub_name}' de '{cat['nombre']}' "
                    f"no tiene palabras clave"
                )

    def test_nombres_categorias_son_unicos(self):
        """Los nombres de categorias padre no se repiten."""
        nombres = [cat["nombre"] for cat in CATEGORIAS_PREDEFINIDAS]
        assert len(nombres) == len(set(nombres)), (
            f"Hay nombres de categoria duplicados: {nombres}"
        )

    def test_nombres_subcategorias_son_unicos_dentro_del_padre(self):
        """Las subcategorias no se repiten dentro de la misma categoria padre."""
        for cat in CATEGORIAS_PREDEFINIDAS:
            sub_nombres = [sub[0] for sub in cat["subcategorias"]]
            assert len(sub_nombres) == len(set(sub_nombres)), (
                f"Subcategorias duplicadas en '{cat['nombre']}': {sub_nombres}"
            )

    def test_iconos_no_vacios(self):
        """Cada categoria padre tiene un emoji/icono valido."""
        for cat in CATEGORIAS_PREDEFINIDAS:
            icono = cat["icono"].strip()
            assert len(icono) >= 1, (
                f"Categoria '{cat['nombre']}' tiene icono vacio"
            )

    def test_colores_formato_hex_valido(self):
        """Cada color es un codigo hexadecimal valido de 6 digitos."""
        import re

        hex_pattern = re.compile(r"^#[0-9A-Fa-f]{6}$")
        for cat in CATEGORIAS_PREDEFINIDAS:
            assert hex_pattern.match(cat["color"]), (
                f"Categoria '{cat['nombre']}' tiene color invalido: "
                f"'{cat['color']}'"
            )


class TestUUIDDeterministicos:
    """Verifica idempotencia de los UUIDs generados."""

    def test_cat_uuid_es_deterministico(self):
        """El mismo nombre siempre produce el mismo UUID."""
        uuid1 = cat_uuid("🍔 Comida")
        uuid2 = cat_uuid("🍔 Comida")
        assert uuid1 == uuid2, "UUIDs deberian ser identicos para el mismo nombre"

    def test_cat_uuid_es_diferente_para_nombres_distintos(self):
        """Nombres diferentes producen UUIDs diferentes."""
        uuid1 = cat_uuid("🍔 Comida")
        uuid2 = cat_uuid("🚗 Transporte")
        assert uuid1 != uuid2, "UUIDs deberian ser diferentes para nombres distintos"

    def test_subcat_uuid_es_deterministico(self):
        """La misma subcategoria produce el mismo UUID."""
        uuid1 = subcat_uuid("🍔 Comida", "Delivery")
        uuid2 = subcat_uuid("🍔 Comida", "Delivery")
        assert uuid1 == uuid2, "UUIDs de subcategoria deberian ser identicos"

    def test_subcat_uuid_diferente_para_distinto_padre(self):
        """Subcategorias con mismo nombre en distintos padres tienen UUIDs diferentes."""
        uuid1 = subcat_uuid("🍔 Comida", "Ropa")
        uuid2 = subcat_uuid("👕 Ropa y Calzado", "Ropa")
        assert uuid1 != uuid2, (
            "Subcategorias con mismo nombre en padres distintos "
            "deberian tener UUIDs diferentes"
        )

    def test_todas_las_categorias_tienen_uuid_unico(self):
        """Todas las categorias padre tienen UUIDs unicos."""
        uuids = [cat_uuid(cat["nombre"]) for cat in CATEGORIAS_PREDEFINIDAS]
        assert len(uuids) == len(set(uuids)), "Hay UUIDs duplicados entre categorias"

    def test_todas_las_subcategorias_tienen_uuid_unico(self):
        """Todas las subcategorias tienen UUIDs unicos."""
        uuids = []
        for cat in CATEGORIAS_PREDEFINIDAS:
            for sub_name, _ in cat["subcategorias"]:
                uuids.append(subcat_uuid(cat["nombre"], sub_name))
        assert len(uuids) == len(set(uuids)), "Hay UUIDs duplicados entre subcategorias"


class TestCategoriasEspecificas:
    """Verifica categorias clave del requerimiento."""

    EXPECTED_CATEGORIES = [
        ("🍔 Comida", "🍔", "#EF4444"),
        ("🚗 Transporte", "🚗", "#F59E0B"),
        ("🏠 Hogar", "🏠", "#8B5CF6"),
        ("🛍️ Compras", "🛍️", "#EC4899"),
        ("🎮 Entretenimiento", "🎮", "#06B6D4"),
        ("✈️ Viajes", "✈️", "#3B82F6"),
        ("💪 Salud", "💪", "#10B981"),
        ("🎓 Educacion", "🎓", "#6366F1"),
        ("💰 Ingresos", "💰", "#22C55E"),
        ("💳 Servicios Financieros", "💳", "#64748B"),
        ("👕 Ropa y Calzado", "👕", "#D946EF"),
        ("🎁 Regalos", "🎁", "#F97316"),
        ("📱 Telecomunicaciones", "📱", "#0EA5E9"),
        ("🔧 Otros", "🔧", "#9CA3AF"),
    ]

    def test_categorias_esperadas_existen(self):
        """Las 14 categorias definidas en la tabla de requerimientos existen."""
        nombres_existentes = [cat["nombre"] for cat in CATEGORIAS_PREDEFINIDAS]
        for nombre, icono, color in self.EXPECTED_CATEGORIES:
            assert nombre in nombres_existentes, (
                f"Falta la categoria '{nombre}' (icono={icono}, color={color})"
            )

    def test_categorias_esperadas_tienen_atributos_correctos(self):
        """Cada categoria esperada tiene los atributos definidos en la tabla."""
        cat_map = {cat["nombre"]: cat for cat in CATEGORIAS_PREDEFINIDAS}
        for nombre, icono, color in self.EXPECTED_CATEGORIES:
            cat = cat_map.get(nombre)
            assert cat is not None, f"Categoria '{nombre}' no encontrada"
            assert cat["icono"] == icono, (
                f"Categoria '{nombre}': icono esperado '{icono}', "
                f"obtenido '{cat['icono']}'"
            )
            assert cat["color"] == color, (
                f"Categoria '{nombre}': color esperado '{color}', "
                f"obtenido '{cat['color']}'"
            )

    def test_categoria_ingresos_existe(self):
        """La categoria de Ingresos es necesaria para clasificar abonos."""
        nombres = [cat["nombre"] for cat in CATEGORIAS_PREDEFINIDAS]
        assert "💰 Ingresos" in nombres, "Falta la categoria de Ingresos"

    def test_categoria_servicios_financieros_existe(self):
        """La categoria de Servicios Financieros incluye cuota de manejo."""
        for cat in CATEGORIAS_PREDEFINIDAS:
            if cat["nombre"] == "💳 Servicios Financieros":
                sub_nombres = [s[0] for s in cat["subcategorias"]]
                assert "Cuota manejo" in sub_nombres, (
                    "Servicios Financieros debe incluir 'Cuota manejo'"
                )
                return
        pytest.fail("Categoria '💳 Servicios Financieros' no encontrada")


class TestPalabrasClaveColombianas:
    """Verifica que las palabras clave incluyen comercios colombianos."""

    COLOMBIAN_KEYWORDS = [
        "EXITO", "CARULLA", "D1", "JUMBO", "ARA", "OLIMPICA",
        "TERPEL", "PRIMAX", "BIOMAX",
        "AVIANCA", "LATAM", "WINGO",
        "ENEL", "EPM", "CODENSA",
        "CLARO", "TIGO", "MOVISTAR",
        "FALABELLA", "ALKOSTO", "BOSI", "ARTURO CALLE", "KOOS",
        "CINECOLOMBIA", "CINEMARK",
        "SMARTFIT", "BODYTECH",
        "SURA", "SANITAS",
        "UDEA", "PLATZI",
        "COLPAGOS",
        "CRUZ VERDE",
        "TRANSMILENIO",
        "DESPEGAR",
    ]

    def test_palabras_clave_colombianas_presentes(self):
        """Verifica que comercios colombianos clave esten en las palabras clave."""
        # Recopilar todas las palabras clave (padre + subcategorias)
        all_keywords: set[str] = set()
        for cat in CATEGORIAS_PREDEFINIDAS:
            all_keywords.update(kw.upper() for kw in cat["palabras_clave"])
            for _, sub_keywords in cat["subcategorias"]:
                all_keywords.update(kw.upper() for kw in sub_keywords)

        missing = []
        for kw in self.COLOMBIAN_KEYWORDS:
            if kw.upper() not in all_keywords:
                missing.append(kw)

        assert not missing, (
            f"Faltan palabras clave de comercios colombianos: {missing}"
        )
