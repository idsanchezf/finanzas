"""Tests para el clasificador deterministico por reglas.

Verifica la implementacion concreta de ClasificadorGastos usando
palabras clave de las 14 categorias predefinidas.

Casos de prueba basados en comercios reales de extractos Bancolombia.
Cada test verifica que un comercio especifico se clasifique en la
categoria correcta con confianza adecuada.

Convencion TDD:
- Carpeta: ClasificadorReglasTests/
- Archivo: test_clasificar_por_reglas.py
"""

import pytest

from src.domain.entities.categoria import Categoria


# ---------------------------------------------------------------------------
# Fixtures compartidas
# ---------------------------------------------------------------------------
@pytest.fixture
def categorias():
    """14 categorias predefinidas con sus palabras clave."""
    return Categoria.precargadas()


@pytest.fixture
def clasificador(categorias):
    """Instancia del clasificador deterministico."""
    from src.infrastructure.excel.clasificador_reglas import ClasificadorReglas

    return ClasificadorReglas()


# ===========================================================================
# Clasificaciones correctas (camino feliz)
# ===========================================================================
class TestClasificarPorReglas:
    """Verifica que comercios reales se clasifiquen correctamente."""

    # -- Alimentacion -------------------------------------------------------
    def test_Should_ClassifyAsAlimentacion_When_DidiFood(self, clasificador, categorias):
        # Arrange --------------------------------------------------------
        comercio = "DLO*DIDI FOOD CO PAYIN"

        # Act ------------------------------------------------------------
        cat_id, confidence = clasificador.clasificar_por_reglas(comercio, categorias)

        # Assert ----------------------------------------------------------
        assert cat_id is not None
        cat = next(c for c in categorias if c.id == cat_id)
        assert cat.nombre == "Alimentacion"
        assert confidence > 50

    def test_Should_ClassifyAsAlimentacion_When_Rappi(self, clasificador, categorias):
        # Arrange --------------------------------------------------------
        comercio = "RAPPI *FOOD BOGOTA"

        # Act ------------------------------------------------------------
        cat_id, confidence = clasificador.clasificar_por_reglas(comercio, categorias)

        # Assert ----------------------------------------------------------
        cat = next(c for c in categorias if c.id == cat_id)
        assert cat.nombre == "Alimentacion"

    def test_Should_ClassifyAsAlimentacion_When_Restaurante(self, clasificador, categorias):
        # Arrange --------------------------------------------------------
        comercio = "RESTAURANTE LA CASONA PRINCIPAL"

        # Act ------------------------------------------------------------
        cat_id, confidence = clasificador.clasificar_por_reglas(comercio, categorias)

        # Assert ----------------------------------------------------------
        cat = next(c for c in categorias if c.id == cat_id)
        assert cat.nombre == "Alimentacion"

    def test_Should_ClassifyAsAlimentacion_When_Supermercado(self, clasificador, categorias):
        # Arrange --------------------------------------------------------
        comercio = "SUPERMERCADO EXITO CALLE 80"

        # Act ------------------------------------------------------------
        cat_id, confidence = clasificador.clasificar_por_reglas(comercio, categorias)

        # Assert ----------------------------------------------------------
        cat = next(c for c in categorias if c.id == cat_id)
        assert cat.nombre == "Alimentacion"

    # -- Transporte --------------------------------------------------------
    def test_Should_ClassifyAsTransporte_When_UberTrip(self, clasificador, categorias):
        # Arrange --------------------------------------------------------
        comercio = "UBER *TRIP HELP.UBER.COM"

        # Act ------------------------------------------------------------
        cat_id, confidence = clasificador.clasificar_por_reglas(comercio, categorias)

        # Assert ----------------------------------------------------------
        cat = next(c for c in categorias if c.id == cat_id)
        assert cat.nombre == "Transporte"
        assert confidence > 50

    def test_Should_ClassifyAsTransporte_When_Taxi(self, clasificador, categorias):
        # Arrange --------------------------------------------------------
        comercio = "TAXI SEGURO BOGOTA APP"

        # Act ------------------------------------------------------------
        cat_id, confidence = clasificador.clasificar_por_reglas(comercio, categorias)

        # Assert ----------------------------------------------------------
        cat = next(c for c in categorias if c.id == cat_id)
        assert cat.nombre == "Transporte"

    def test_Should_ClassifyAsTransporte_When_Gasolina(self, clasificador, categorias):
        # Arrange --------------------------------------------------------
        comercio = "EDS GASOLINA TERPEL NORTE"

        # Act ------------------------------------------------------------
        cat_id, confidence = clasificador.clasificar_por_reglas(comercio, categorias)

        # Assert ----------------------------------------------------------
        cat = next(c for c in categorias if c.id == cat_id)
        assert cat.nombre == "Transporte"

    def test_Should_ClassifyAsTransporte_When_Transmilenio(self, clasificador, categorias):
        # Arrange --------------------------------------------------------
        comercio = "TRANSMILENIO RECARGA TULLAVE"

        # Act ------------------------------------------------------------
        cat_id, confidence = clasificador.clasificar_por_reglas(comercio, categorias)

        # Assert ----------------------------------------------------------
        cat = next(c for c in categorias if c.id == cat_id)
        assert cat.nombre == "Transporte"

    # -- Vivienda ----------------------------------------------------------
    def test_Should_ClassifyAsVivienda_When_Energia(self, clasificador, categorias):
        # Arrange --------------------------------------------------------
        comercio = "EPM ENERGIA PAGO ELECTRONICO"

        # Act ------------------------------------------------------------
        cat_id, confidence = clasificador.clasificar_por_reglas(comercio, categorias)

        # Assert ----------------------------------------------------------
        cat = next(c for c in categorias if c.id == cat_id)
        assert cat.nombre == "Vivienda"

    def test_Should_ClassifyAsVivienda_When_Arriendo(self, clasificador, categorias):
        # Arrange --------------------------------------------------------
        comercio = "PAGO ARRIENDO ABRIL 2026"

        # Act ------------------------------------------------------------
        cat_id, confidence = clasificador.clasificar_por_reglas(comercio, categorias)

        # Assert ----------------------------------------------------------
        cat = next(c for c in categorias if c.id == cat_id)
        assert cat.nombre == "Vivienda"

    def test_Should_ClassifyAsVivienda_When_Internet(self, clasificador, categorias):
        # Arrange --------------------------------------------------------
        comercio = "CLARO INTERNET HOGAR PAGO"

        # Act ------------------------------------------------------------
        cat_id, confidence = clasificador.clasificar_por_reglas(comercio, categorias)

        # Assert ----------------------------------------------------------
        cat = next(c for c in categorias if c.id == cat_id)
        assert cat.nombre == "Vivienda"

    # -- Salud -------------------------------------------------------------
    def test_Should_ClassifyAsSalud_When_Farmacia(self, clasificador, categorias):
        # Arrange --------------------------------------------------------
        comercio = "FARMACIA CRUZ VERDE AV 19"

        # Act ------------------------------------------------------------
        cat_id, confidence = clasificador.clasificar_por_reglas(comercio, categorias)

        # Assert ----------------------------------------------------------
        cat = next(c for c in categorias if c.id == cat_id)
        assert cat.nombre == "Salud"

    def test_Should_ClassifyAsSalud_When_Hospital(self, clasificador, categorias):
        # Arrange --------------------------------------------------------
        comercio = "HOSPITAL SAN IGNACIO CONSULTA"

        # Act ------------------------------------------------------------
        cat_id, confidence = clasificador.clasificar_por_reglas(comercio, categorias)

        # Assert ----------------------------------------------------------
        cat = next(c for c in categorias if c.id == cat_id)
        assert cat.nombre == "Salud"

    def test_Should_ClassifyAsSalud_When_EPS(self, clasificador, categorias):
        # Arrange --------------------------------------------------------
        comercio = "EPS SANITAS PAGO MENSUAL"

        # Act ------------------------------------------------------------
        cat_id, confidence = clasificador.clasificar_por_reglas(comercio, categorias)

        # Assert ----------------------------------------------------------
        cat = next(c for c in categorias if c.id == cat_id)
        assert cat.nombre == "Salud"

    # -- Entretenimiento ---------------------------------------------------
    def test_Should_ClassifyAsEntretenimiento_When_Netflix(self, clasificador, categorias):
        # Arrange --------------------------------------------------------
        comercio = "NETFLIX.COM SUBSCRIPCION"

        # Act ------------------------------------------------------------
        cat_id, confidence = clasificador.clasificar_por_reglas(comercio, categorias)

        # Assert ----------------------------------------------------------
        cat = next(c for c in categorias if c.id == cat_id)
        assert cat.nombre == "Entretenimiento"

    def test_Should_ClassifyAsEntretenimiento_When_Spotify(self, clasificador, categorias):
        # Arrange --------------------------------------------------------
        comercio = "SPOTIFY PREMIUM PAGO"

        # Act ------------------------------------------------------------
        cat_id, confidence = clasificador.clasificar_por_reglas(comercio, categorias)

        # Assert ----------------------------------------------------------
        cat = next(c for c in categorias if c.id == cat_id)
        assert cat.nombre == "Entretenimiento"

    def test_Should_ClassifyAsEntretenimiento_When_Cine(self, clasificador, categorias):
        # Arrange --------------------------------------------------------
        comercio = "CINEMARK CINE COLOMBIA BOLETERIA"

        # Act ------------------------------------------------------------
        cat_id, confidence = clasificador.clasificar_por_reglas(comercio, categorias)

        # Assert ----------------------------------------------------------
        cat = next(c for c in categorias if c.id == cat_id)
        assert cat.nombre == "Entretenimiento"

    # -- Educacion ---------------------------------------------------------
    def test_Should_ClassifyAsEducacion_When_Universidad(self, clasificador, categorias):
        # Arrange --------------------------------------------------------
        comercio = "UNIVERSIDAD JAVERIANA MATRICULA"

        # Act ------------------------------------------------------------
        cat_id, confidence = clasificador.clasificar_por_reglas(comercio, categorias)

        # Assert ----------------------------------------------------------
        cat = next(c for c in categorias if c.id == cat_id)
        assert cat.nombre == "Educacion"

    def test_Should_ClassifyAsEducacion_When_Udemy(self, clasificador, categorias):
        # Arrange --------------------------------------------------------
        comercio = "UDEMY ONLINE COURSES"

        # Act ------------------------------------------------------------
        cat_id, confidence = clasificador.clasificar_por_reglas(comercio, categorias)

        # Assert ----------------------------------------------------------
        cat = next(c for c in categorias if c.id == cat_id)
        assert cat.nombre == "Educacion"

    # -- Ropa y Moda -------------------------------------------------------
    def test_Should_ClassifyAsRopa_When_Falabella(self, clasificador, categorias):
        # Arrange --------------------------------------------------------
        comercio = "FALABELLA COMPRA ROPA BOGOTA"

        # Act ------------------------------------------------------------
        cat_id, confidence = clasificador.clasificar_por_reglas(comercio, categorias)

        # Assert ----------------------------------------------------------
        cat = next(c for c in categorias if c.id == cat_id)
        assert cat.nombre == "Ropa y Moda"

    def test_Should_ClassifyAsRopa_When_Zara(self, clasificador, categorias):
        # Arrange --------------------------------------------------------
        comercio = "ZARA ESPANA SUC COLOMBIA"

        # Act ------------------------------------------------------------
        cat_id, confidence = clasificador.clasificar_por_reglas(comercio, categorias)

        # Assert ----------------------------------------------------------
        cat = next(c for c in categorias if c.id == cat_id)
        assert cat.nombre == "Ropa y Moda"

    # -- Financieros -------------------------------------------------------
    def test_Should_ClassifyAsFinancieros_When_CuotaManejo(self, clasificador, categorias):
        # Arrange --------------------------------------------------------
        comercio = "CUOTA MANEJO T.C. BANCOLOMBIA"

        # Act ------------------------------------------------------------
        cat_id, confidence = clasificador.clasificar_por_reglas(comercio, categorias)

        # Assert ----------------------------------------------------------
        cat = next(c for c in categorias if c.id == cat_id)
        assert cat.nombre == "Financieros"
        assert confidence >= 80

    def test_Should_ClassifyAsFinancieros_When_Comision(self, clasificador, categorias):
        # Arrange --------------------------------------------------------
        comercio = "COMISION TRANSFERENCIA BANCOLOMBIA"

        # Act ------------------------------------------------------------
        cat_id, confidence = clasificador.clasificar_por_reglas(comercio, categorias)

        # Assert ----------------------------------------------------------
        cat = next(c for c in categorias if c.id == cat_id)
        assert cat.nombre == "Financieros"

    def test_Should_ClassifyAsFinancieros_When_4x1000(self, clasificador, categorias):
        # Arrange --------------------------------------------------------
        comercio = "GMV 4X1000 RETIRO CAJERO"

        # Act ------------------------------------------------------------
        cat_id, confidence = clasificador.clasificar_por_reglas(comercio, categorias)

        # Assert ----------------------------------------------------------
        cat = next(c for c in categorias if c.id == cat_id)
        assert cat.nombre == "Financieros"

    # -- Tecnologia --------------------------------------------------------
    def test_Should_ClassifyAsTecnologia_When_Apple(self, clasificador, categorias):
        # Arrange --------------------------------------------------------
        comercio = "APPLE.COM/BILL ITUNES"

        # Act ------------------------------------------------------------
        cat_id, confidence = clasificador.clasificar_por_reglas(comercio, categorias)

        # Assert ----------------------------------------------------------
        cat = next(c for c in categorias if c.id == cat_id)
        assert cat.nombre == "Tecnologia"

    def test_Should_ClassifyAsTecnologia_When_Google(self, clasificador, categorias):
        # Arrange --------------------------------------------------------
        comercio = "GOOGLE PLAY APPS COMPRA"

        # Act ------------------------------------------------------------
        cat_id, confidence = clasificador.clasificar_por_reglas(comercio, categorias)

        # Assert ----------------------------------------------------------
        cat = next(c for c in categorias if c.id == cat_id)
        assert cat.nombre == "Tecnologia"

    # -- Viajes ------------------------------------------------------------
    def test_Should_ClassifyAsViajes_When_Avianca(self, clasificador, categorias):
        # Arrange --------------------------------------------------------
        comercio = "AVIANCA TICKET VUELO BOG-MDE"

        # Act ------------------------------------------------------------
        cat_id, confidence = clasificador.clasificar_por_reglas(comercio, categorias)

        # Assert ----------------------------------------------------------
        cat = next(c for c in categorias if c.id == cat_id)
        assert cat.nombre == "Viajes"

    def test_Should_ClassifyAsViajes_When_Hotel(self, clasificador, categorias):
        # Arrange --------------------------------------------------------
        comercio = "HOTEL BOGOTA PLAZA RESERVACION"

        # Act ------------------------------------------------------------
        cat_id, confidence = clasificador.clasificar_por_reglas(comercio, categorias)

        # Assert ----------------------------------------------------------
        cat = next(c for c in categorias if c.id == cat_id)
        assert cat.nombre == "Viajes"

    # -- Servicios ---------------------------------------------------------
    def test_Should_ClassifyAsServicios_When_Peluqueria(self, clasificador, categorias):
        # Arrange --------------------------------------------------------
        comercio = "PELUQUERIA ELITE CORTE CABALLERO"

        # Act ------------------------------------------------------------
        cat_id, confidence = clasificador.clasificar_por_reglas(comercio, categorias)

        # Assert ----------------------------------------------------------
        cat = next(c for c in categorias if c.id == cat_id)
        assert cat.nombre == "Servicios"

    # -- Suscripciones -----------------------------------------------------
    def test_Should_ClassifyAsSuscripciones_When_OnlyFans(self, clasificador, categorias):
        # Arrange --------------------------------------------------------
        comercio = "ONLYFANS SUBSCRIPCION"

        # Act ------------------------------------------------------------
        cat_id, confidence = clasificador.clasificar_por_reglas(comercio, categorias)

        # Assert ----------------------------------------------------------
        cat = next(c for c in categorias if c.id == cat_id)
        assert cat.nombre == "Suscripciones"

    def test_Should_ClassifyAsSuscripciones_When_GoogleOne(self, clasificador, categorias):
        # Arrange --------------------------------------------------------
        comercio = "GOOGLE ONE MEMBRESIA MENSUAL"

        # Act ------------------------------------------------------------
        cat_id, confidence = clasificador.clasificar_por_reglas(comercio, categorias)

        # Assert ----------------------------------------------------------
        cat = next(c for c in categorias if c.id == cat_id)
        assert cat.nombre == "Suscripciones"

    # -- Mascotas ----------------------------------------------------------
    def test_Should_ClassifyAsMascotas_When_Veterinaria(self, clasificador, categorias):
        # Arrange --------------------------------------------------------
        comercio = "VETERINARIA ANIMAL HEALTH CENTER"

        # Act ------------------------------------------------------------
        cat_id, confidence = clasificador.clasificar_por_reglas(comercio, categorias)

        # Assert ----------------------------------------------------------
        cat = next(c for c in categorias if c.id == cat_id)
        assert cat.nombre == "Mascotas"

    def test_Should_ClassifyAsMascotas_When_PetShop(self, clasificador, categorias):
        # Arrange --------------------------------------------------------
        comercio = "PET SHOP ALIMENTO PERROS GATOS"

        # Act ------------------------------------------------------------
        cat_id, confidence = clasificador.clasificar_por_reglas(comercio, categorias)

        # Assert ----------------------------------------------------------
        cat = next(c for c in categorias if c.id == cat_id)
        assert cat.nombre == "Mascotas"
