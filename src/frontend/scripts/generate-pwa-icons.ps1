# =============================================================================
# Generador de iconos PWA — Finance Report
# =============================================================================
# Requisito previo: Tener un icono fuente SVG o PNG de al menos 512x512px
#   en public/icons/icon-source.svg o public/icons/icon-source.png
#
# Herramientas necesarias:
#   - ImageMagick (choco install imagemagick)  o
#   - Sharp CLI (npm install sharp-cli)
#
# Tamanos generados:
#   48x48, 72x72, 96x96, 128x128, 144x144, 152x152,
#   192x192, 256x256, 384x384, 512x512
#
# Uso:
#   .\scripts\generate-pwa-icons.ps1
# =============================================================================

param(
    [string]$SourceFile = "public/icons/icon-source.svg",
    [string]$OutputDir = "public/icons",
    [string]$BackgroundColor = "#3B82F6",
    [int]$Padding = 20
)

$ErrorActionPreference = "Stop"

# Tamanos requeridos por PWA y Apple
$SIZES = @(48, 72, 96, 128, 144, 152, 192, 256, 384, 512)

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Generador de Iconos PWA - Finance Report" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Verificar que el archivo fuente existe
if (-not (Test-Path -LiteralPath $SourceFile)) {
    Write-Host "ERROR: No se encontro el archivo fuente: $SourceFile" -ForegroundColor Red
    Write-Host ""
    Write-Host "Opciones:" -ForegroundColor Yellow
    Write-Host "  1. Crea tu propio icono y guardalo como $SourceFile"
    Write-Host "  2. Usa un placeholder temporal:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "     Aqui tienes un SVG minimo para comenzar:" -ForegroundColor Gray
    Write-Host '     <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">' -ForegroundColor Gray
    Write-Host '       <rect width="512" height="512" rx="100" fill="#3B82F6"/>' -ForegroundColor Gray
    Write-Host '       <text x="256" y="320" text-anchor="middle" fill="white" font-size="280" font-family="sans-serif" font-weight="bold">FR</text>' -ForegroundColor Gray
    Write-Host '     </svg>' -ForegroundColor Gray
    Write-Host ""
    Write-Host "  3. Usa un generador online: https://maskable.app/editor" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

If (-not (Test-Path -LiteralPath $OutputDir)) {
    New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
}

Write-Host "Archivo fuente:" $SourceFile -ForegroundColor Green
Write-Host ""

# Detectar herramienta disponible
$useImageMagick = $null
try { $useImageMagick = Get-Command "magick" -ErrorAction SilentlyContinue } catch { }
try { if (-not $useImageMagick) { $useImageMagick = Get-Command "convert" -ErrorAction SilentlyContinue } } catch { }
try { if (-not $useImageMagick) { $useImageMagick = Get-Command "npx" -ErrorAction SilentlyContinue } } catch { }

if (-not $useImageMagick) {
    Write-Host "ADVERTENCIA: No se encontro ImageMagick ni Sharp." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Instala ImageMagick:" -ForegroundColor Yellow
    Write-Host "  choco install imagemagick" -ForegroundColor Gray
    Write-Host ""
    Write-Host "O instala Sharp CLI:" -ForegroundColor Yellow
    Write-Host "  npm install -g sharp-cli" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Mientras tanto, puedes crear los iconos manualmente usando:" -ForegroundColor Yellow
    Write-Host "  https://maskable.app/editor" -ForegroundColor Gray
    Write-Host ""
    exit 0
}

Write-Host "Generando iconos..." -ForegroundColor Green
Write-Host ""

foreach ($size in $SIZES) {
    $outputFile = "$OutputDir/icon-${size}x${size}.png"
    $paddingSize = [math]::Round($size * $Padding / 512)

    $resizeArg = "${size}x${size}"

    if ($useImageMagick.Name -eq "magick") {
        & magick "$SourceFile" `
            -resize $resizeArg `
            -gravity center `
            -background $BackgroundColor `
            -extent $resizeArg `
            "$outputFile" 2>$null
    } elseif ($useImageMagick.Name -eq "convert") {
        & convert "$SourceFile" `
            -resize $resizeArg `
            -gravity center `
            -background $BackgroundColor `
            -extent $resizeArg `
            "$outputFile" 2>$null
    } elseif ($useImageMagick.Name -eq "npx") {
        & npx sharp-cli -i "$SourceFile" -o "$outputFile" resize $size $size --fit contain --background "$BackgroundColor"
    }

    if (Test-Path -LiteralPath $outputFile) {
        Write-Host "  [OK] icon-${size}x${size}.png" -ForegroundColor Green
    } else {
        Write-Host "  [FAIL] icon-${size}x${size}.png" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Iconos generados!" -ForegroundColor Green
Write-Host "  Revisa: $OutputDir/" -ForegroundColor Gray
Write-Host ""
Write-Host "  Siguiente paso: Actualiza manifest.json con los nuevos iconos." -ForegroundColor Yellow
Write-Host "============================================" -ForegroundColor Cyan
