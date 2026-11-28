#!/usr/bin/env bash
# ============================================================
# GENERA TRÁFICO DE PRUEBA CONTRA LA APLICACIÓN
# ============================================================
# Sirve para que el dashboard muestre datos: peticiones normales,
# errores 404 (libro inexistente) y errores 500 (endpoint de diagnóstico).
#
# Uso: bash scripts/generar-trafico.sh http://localhost:8088 [rondas]
# ============================================================
set -euo pipefail

URL="${1:-http://localhost:8088}"
RONDAS="${2:-30}"
ok=0; cliente=0; servidor=0

for i in $(seq 1 "$RONDAS"); do
  for ruta in /api/libros /api/resumen /api/libros/1 /api/libros/$(( (i % 6) + 1 )); do
    codigo=$(curl -s -o /dev/null -w '%{http_code}' "${URL}${ruta}")
    case "$codigo" in 2*) ok=$((ok+1));; 4*) cliente=$((cliente+1));; *) servidor=$((servidor+1));; esac
  done
  # Uno de cada 5 ciclos provoca un error 500 controlado.
  if (( i % 5 == 0 )); then
    curl -s -o /dev/null "${URL}/api/diagnostico/error" && servidor=$((servidor+1)) || true
  fi
  sleep 0.2
done

echo "Tráfico generado contra ${URL}: ${ok} respuestas 2xx, ${cliente} 4xx, ${servidor} 5xx."
