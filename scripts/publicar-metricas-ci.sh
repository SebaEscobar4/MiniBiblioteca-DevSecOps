#!/usr/bin/env bash
# ============================================================
# PUBLICA LAS MÉTRICAS DEL PIPELINE EN PUSHGATEWAY
# ============================================================
# Prometheus "pregunta" (scrape) a los servicios que viven todo el tiempo,
# pero un job de CI dura minutos: por eso el pipeline EMPUJA sus métricas
# a Pushgateway y Prometheus las lee desde ahí.
#
# Uso:
#   PUSHGATEWAY_URL=http://localhost:9091 \
#   COBERTURA=91.7 PRUEBAS_TOTAL=16 PRUEBAS_FALLIDAS=0 \
#   DESPLIEGUE_SEGUNDOS=42 PIPELINE_SEGUNDOS=480 \
#   COMMIT=abc123 bash scripts/publicar-metricas-ci.sh
#
# Las variables que falten se omiten.
# ============================================================
set -euo pipefail

PUSHGATEWAY_URL="${PUSHGATEWAY_URL:-http://localhost:9091}"
COMMIT="${COMMIT:-local}"
RAMA="${RAMA:-local}"

metricas=""
agregar() {
  local nombre="$1" valor="$2" ayuda="$3"
  [ -z "$valor" ] && return 0
  metricas+="# HELP ${nombre} ${ayuda}"$'\n'
  metricas+="# TYPE ${nombre} gauge"$'\n'
  metricas+="${nombre}{commit=\"${COMMIT}\",rama=\"${RAMA}\"} ${valor}"$'\n'
}

agregar minibiblioteca_ci_cobertura_porcentaje "${COBERTURA:-}" "Cobertura de lineas JaCoCo (%)"
agregar minibiblioteca_ci_pruebas_total "${PRUEBAS_TOTAL:-}" "Pruebas ejecutadas"
agregar minibiblioteca_ci_pruebas_fallidas "${PRUEBAS_FALLIDAS:-}" "Pruebas fallidas o con error"
agregar minibiblioteca_ci_despliegue_segundos "${DESPLIEGUE_SEGUNDOS:-}" "Tiempo de despliegue (s)"
agregar minibiblioteca_ci_pipeline_segundos "${PIPELINE_SEGUNDOS:-}" "Duracion del pipeline hasta el despliegue (s)"
agregar minibiblioteca_ci_ultima_ejecucion_timestamp_seconds "$(date +%s)" "Fecha de la ultima ejecucion"

# Grupo "job=ci-cd": cada publicación reemplaza la anterior.
printf '%s' "$metricas" | curl -fsS --data-binary @- "${PUSHGATEWAY_URL}/metrics/job/ci-cd"
echo "Métricas del pipeline publicadas en ${PUSHGATEWAY_URL} (commit ${COMMIT})."
