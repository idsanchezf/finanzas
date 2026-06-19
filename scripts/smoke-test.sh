#!/usr/bin/env bash
# ============================================================
# Finance Report — Smoke Tests (Post-Deploy)
# ============================================================
# Verifica que los endpoints criticos respondan correctamente
# despues de un despliegue.
#
# Uso:
#   BASE_URL=https://api.financereport.app bash scripts/smoke-test.sh
#   BASE_URL=http://localhost:8000 bash scripts/smoke-test.sh
# ============================================================

set -euo pipefail

# Configuracion
BASE_URL="${BASE_URL:-http://localhost:8000}"
TIMEOUT=10
PASS=0
FAIL=0
TOTAL=0

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "============================================"
echo " Finance Report — Smoke Tests"
echo " Target: ${BASE_URL}"
echo " Time:   $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
echo "============================================"
echo ""

# Funcion para ejecutar un test
run_test() {
  local name="$1"
  local method="$2"
  local path="$3"
  local expected_status="${4:-200}"
  local expected_body_contains="${5:-}"

  TOTAL=$((TOTAL + 1))
  echo -n "[${TOTAL}] ${name}... "

  # Construir comando curl
  local curl_cmd="curl -s -o /tmp/smoke_response.txt -w '%{http_code}' --max-time ${TIMEOUT}"
  if [ "$method" != "GET" ]; then
    curl_cmd="${curl_cmd} -X ${method}"
  fi
  # Headers
  curl_cmd="${curl_cmd} -H 'Accept: application/json'"
  curl_cmd="${curl_cmd} -H 'User-Agent: SmokeTest/1.0'"

  local http_code
  http_code=$(eval "${curl_cmd} ${BASE_URL}${path}" 2>/dev/null) || {
    http_code="000"
  }

  # Limpiar http_code (curl puede devolver caracteres extra)
  http_code=$(echo "$http_code" | tr -d '[:space:]')

  local body
  body=$(cat /tmp/smoke_response.txt 2>/dev/null || echo "")

  # Verificar status code
  if [ "$http_code" != "$expected_status" ]; then
    echo -e "${RED}FAIL${NC}"
    echo "       Expected status: ${expected_status}, got: ${http_code}"
    echo "       Response body (first 200 chars): $(echo "$body" | head -c 200)"
    FAIL=$((FAIL + 1))
    return 1
  fi

  # Verificar contenido del body si se especifico
  if [ -n "$expected_body_contains" ]; then
    if ! echo "$body" | grep -q "$expected_body_contains"; then
      echo -e "${YELLOW}WARN${NC}"
      echo "       Status OK (${http_code}), pero body no contiene: ${expected_body_contains}"
      # Contar como pass pero con advertencia
    fi
  fi

  echo -e "${GREEN}PASS${NC} (${http_code})"
  PASS=$((PASS + 1))
  return 0
}

# ============================================================
# Health Checks
# ============================================================
echo "--- Health Checks ---"
run_test "Liveness probe" "GET" "/health" "200" "ok"
run_test "Readiness probe" "GET" "/health/ready" "200" 'status'

# ============================================================
# API Documentation
# ============================================================
echo ""
echo "--- API Documentation ---"
run_test "OpenAPI schema" "GET" "/openapi.json" "200" "openapi"
run_test "Swagger UI" "GET" "/docs" "200" "swagger"
run_test "ReDoc" "GET" "/redoc" "200" "redoc"

# ============================================================
# Auth endpoints
# ============================================================
echo ""
echo "--- Auth Endpoints ---"
# Login sin credenciales debe devolver error (pero la API responde)
run_test "Login (sin credenciales)" "POST" "/api/v1/auth/login" "422" ""
# Refresh sin token
run_test "Refresh (sin token)" "POST" "/api/v1/auth/refresh" "422" ""

# ============================================================
# Public endpoints (deberian requerir auth)
# ============================================================
echo ""
echo "--- Protected Endpoints (esperado 401/403) ---"
run_test "Dashboard summary (sin auth)" "GET" "/api/v1/dashboard/summary" "401" ""
run_test "Transacciones (sin auth)" "GET" "/api/v1/transactions" "401" ""
run_test "Extractos (sin auth)" "GET" "/api/v1/extracts" "401" ""
run_test "Categorias (sin auth)" "GET" "/api/v1/categories" "401" ""

# ============================================================
# Performance check: respuesta rapida
# ============================================================
echo ""
echo "--- Performance ---"
echo -n "Latencia /health... "
START=$(date +%s%N)
curl -s -o /dev/null -w '' --max-time 5 "${BASE_URL}/health" 2>/dev/null
END=$(date +%s%N)
DURATION_MS=$(( (END - START) / 1000000 ))
if [ "$DURATION_MS" -lt 500 ]; then
  echo -e "${GREEN}${DURATION_MS}ms${NC} (OK < 500ms)"
else
  echo -e "${YELLOW}${DURATION_MS}ms${NC} (WARN > 500ms)"
fi

# ============================================================
# Resumen
# ============================================================
echo ""
echo "============================================"
echo " Smoke Test Results"
echo "============================================"
echo " Total:  ${TOTAL}"
echo -e " Pass:   ${GREEN}${PASS}${NC}"
echo -e " Fail:   ${RED}${FAIL}${NC}"
echo ""

if [ "$FAIL" -gt 0 ]; then
  echo -e "${RED}SMOKE TESTS FAILED: ${FAIL} test(s) failed.${NC}"
  exit 1
else
  echo -e "${GREEN}SMOKE TESTS PASSED: All ${PASS} tests passed.${NC}"
  exit 0
fi
