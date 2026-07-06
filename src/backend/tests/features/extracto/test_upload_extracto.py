"""Archivo de test BDD — registra los escenarios del feature file.

Los step definitions estan en conftest.py (fixtures y steps compartidos).
"""

from pytest_bdd import scenarios

scenarios("upload_extracto.feature")
