"""Configuracion CORS — Origenes permitidos para la API."""

import os

CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:8000",
).split(",")

CORS_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]

CORS_HEADERS = [
    "Content-Type",
    "Authorization",
    "X-Correlation-ID",
    "X-Requested-With",
]
