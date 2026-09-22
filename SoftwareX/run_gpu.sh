#!/bin/bash
# SoftwareX - Lanzador general desde la raíz del paquete
# Permite ejecutar ./run_gpu.sh directamente al entrar en la carpeta SoftwareX
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
chmod +x "$SCRIPT_DIR/code/run_gpu.sh" 2>/dev/null
exec "$SCRIPT_DIR/code/run_gpu.sh" "$@"
