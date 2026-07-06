# ============================================================
# Finance Report — Smoke Tests (Post-Deploy) — PowerShell
# ============================================================
# Verifica que los endpoints criticos respondan correctamente
# despues de un despliegue.
#
# Uso:
#   $env:BASE_URL="https://api.financereport.app"; .\scripts\smoke-test.ps1
#   $env:BASE_URL="http://localhost:8000"; .\scripts\smoke-test.ps1
# ============================================================

param()

$ErrorActionPreference = "Stop"

$BASE_URL = if ($env:BASE_URL) { $env:BASE_URL } else { "http://localhost:8000" }
$TIMEOUT_SEC = 10
$Pass = 0
$Fail = 0
$Total = 0

Write-Host "============================================" -ForegroundColor Cyan
Write-Host " Finance Report — Smoke Tests" -ForegroundColor Cyan
Write-Host " Target: $BASE_URL" -ForegroundColor Cyan
Write-Host " Time:   $(Get-Date -Format 'yyyy-MM-ddTHH:mm:ssZ')" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

function Invoke-SmokeTest {
    param(
        [string]$Name,
        [string]$Method = "GET",
        [string]$Path,
        [int]$ExpectedStatus = 200,
        [string]$ExpectedBodyContains = ""
    )

    $script:Total++
    Write-Host "[$Total] $Name... " -NoNewline

    try {
        $headers = @{
            "Accept" = "application/json"
            "User-Agent" = "SmokeTest/1.0"
        }

        $response = Invoke-WebRequest `
            -Uri "$BASE_URL$Path" `
            -Method $Method `
            -Headers $headers `
            -TimeoutSec $TIMEOUT_SEC `
            -SkipCertificateCheck `
            -UseBasicParsing `
            -ErrorAction Stop

        $httpCode = $response.StatusCode

        if ($httpCode -ne $ExpectedStatus) {
            Write-Host "FAIL" -ForegroundColor Red
            Write-Host "       Expected status: $ExpectedStatus, got: $httpCode" -ForegroundColor Red
            $bodyPreview = if ($response.Content) { $response.Content.Substring(0, [Math]::Min(200, $response.Content.Length)) } else { "" }
            Write-Host "       Response body (first 200 chars): $bodyPreview" -ForegroundColor Red
            $script:Fail++
            return
        }

        if ($ExpectedBodyContains -and $response.Content -notmatch $ExpectedBodyContains) {
            Write-Host "WARN" -ForegroundColor Yellow
            Write-Host "       Status OK ($httpCode), pero body no contiene: $ExpectedBodyContains" -ForegroundColor Yellow
        }

        Write-Host "PASS ($httpCode)" -ForegroundColor Green
        $script:Pass++
    }
    catch {
        $statusCode = if ($_.Exception.Response) { [int]$_.Exception.Response.StatusCode } else { 0 }
        if ($statusCode -ne $ExpectedStatus) {
            Write-Host "FAIL" -ForegroundColor Red
            Write-Host "       Expected status: $ExpectedStatus, got: $statusCode ($($_.Exception.Message))" -ForegroundColor Red
            $script:Fail++
        }
        else {
            Write-Host "PASS ($statusCode)" -ForegroundColor Green
            $script:Pass++
        }
    }
}

# ============================================================
# Health Checks
# ============================================================
Write-Host "--- Health Checks ---" -ForegroundColor White
Invoke-SmokeTest -Name "Liveness probe" -Method GET -Path "/health" -ExpectedStatus 200 -ExpectedBodyContains "ok"
Invoke-SmokeTest -Name "Readiness probe" -Method GET -Path "/health/ready" -ExpectedStatus 200 -ExpectedBodyContains "status"

# ============================================================
# API Documentation
# ============================================================
Write-Host ""
Write-Host "--- API Documentation ---" -ForegroundColor White
Invoke-SmokeTest -Name "OpenAPI schema" -Method GET -Path "/openapi.json" -ExpectedStatus 200 -ExpectedBodyContains "openapi"
Invoke-SmokeTest -Name "Swagger UI" -Method GET -Path "/docs" -ExpectedStatus 200
Invoke-SmokeTest -Name "ReDoc" -Method GET -Path "/redoc" -ExpectedStatus 200

# ============================================================
# Auth endpoints
# ============================================================
Write-Host ""
Write-Host "--- Auth Endpoints ---" -ForegroundColor White
Invoke-SmokeTest -Name "Login (sin credenciales)" -Method POST -Path "/api/v1/auth/login" -ExpectedStatus 422

# ============================================================
# Protected Endpoints
# ============================================================
Write-Host ""
Write-Host "--- Protected Endpoints (esperado 401/403) ---" -ForegroundColor White
Invoke-SmokeTest -Name "Dashboard summary (sin auth)" -Method GET -Path "/api/v1/dashboard/summary" -ExpectedStatus 401
Invoke-SmokeTest -Name "Transacciones (sin auth)" -Method GET -Path "/api/v1/transactions" -ExpectedStatus 401
Invoke-SmokeTest -Name "Extractos (sin auth)" -Method GET -Path "/api/v1/extracts" -ExpectedStatus 401
Invoke-SmokeTest -Name "Categorias (sin auth)" -Method GET -Path "/api/v1/categories" -ExpectedStatus 401

# ============================================================
# Performance
# ============================================================
Write-Host ""
Write-Host "--- Performance ---" -ForegroundColor White
Write-Host -NoNewline "Latencia /health... "
$sw = [System.Diagnostics.Stopwatch]::StartNew()
try {
    $null = Invoke-WebRequest -Uri "$BASE_URL/health" -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
}
catch { }
$sw.Stop()
$durationMs = $sw.ElapsedMilliseconds
if ($durationMs -lt 500) {
    Write-Host "${durationMs}ms (OK < 500ms)" -ForegroundColor Green
}
else {
    Write-Host "${durationMs}ms (WARN > 500ms)" -ForegroundColor Yellow
}

# ============================================================
# Resumen
# ============================================================
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " Smoke Test Results" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " Total:  $Total"
Write-Host " Pass:   $Pass" -ForegroundColor Green
Write-Host " Fail:   $Fail" -ForegroundColor Red
Write-Host ""

if ($Fail -gt 0) {
    Write-Host "SMOKE TESTS FAILED: $Fail test(s) failed." -ForegroundColor Red
    exit 1
}
else {
    Write-Host "SMOKE TESTS PASSED: All $Pass tests passed." -ForegroundColor Green
    exit 0
}
