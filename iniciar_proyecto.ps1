# Script para iniciar el entorno Conda 'crms' y arrancar el Geo-RAG Explorer automáticamente.
# Ejecutar desde PowerShell en la carpeta raíz del proyecto.

Write-Host "==========================================================" -ForegroundColor Green
Write-Host "  Iniciando Entorno Conda 'crms' y Geo-RAG Explorer..." -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green

# 1. Ejecutar el gancho de inicialización de Anaconda
$CondaHookPath = "C:\Users\fdemiguel\AppData\Local\anaconda3\shell\condabin\conda-hook.ps1"
if (Test-Path $CondaHookPath) {
    Write-Host "[Conda] Cargando ganchos de inicialización..." -ForegroundColor Yellow
    . $CondaHookPath
} else {
    Write-Host "[ADVERTENCIA] No se encontró el gancho de conda en $CondaHookPath" -ForegroundColor Red
    Write-Host "Intentando activar conda de forma estándar..." -ForegroundColor Red
}

# 2. Activar el entorno virtual 'crms'
Write-Host "[Conda] Activando entorno virtual 'crms'..." -ForegroundColor Yellow
conda activate crms

# 3. Lanzar la aplicación
Write-Host "[App] Iniciando servidor híbrido run_app.py..." -ForegroundColor Yellow
python run_app.py
