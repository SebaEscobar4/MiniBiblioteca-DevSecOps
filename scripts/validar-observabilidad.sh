#!/usr/bin/env bash
# ============================================================
# VALIDA QUE EL MONITOREO ESTÉ REGISTRANDO LA APLICACIÓN
# ============================================================
# Consulta Prometheus y Loki y falla si alguna señal no aparece:
#   1. Réplicas del backend medidas por Prometheus (>= 2)
#   2. Sondas de disponibilidad en verde
#   3. La versión desplegada coincide con el commit
#   4. Errores 500 registrados (generados por el tráfico de prueba)
#   5. Métricas del pipeline publicadas (cobertura)
#   6. Logs del backend recibidos en Loki
#
# Uso: bash scripts/validar-observabilidad.sh <prometheus> <loki> <commit>
# Reintenta hasta 3 minutos porque Prometheus mide cada 15 s.
# ============================================================
set -uo pipefail

PROM="${1:-http://127.0.0.1:9090}"
LOKI="${2:-http://127.0.0.1:3100}"
COMMIT="${3:-local}"
mkdir -p evidencias

consulta() {
  curl -fsS -G "${PROM}/api/v1/query" --data-urlencode "query=$1" \
    | jq -r '.data.result[0].value[1] // empty' 2>/dev/null
}

logs_backend() {
  curl -fsS -G "${LOKI}/loki/api/v1/query_range" \
    --data-urlencode 'query=sum(count_over_time({service="backend"}[10m]))' \
    | jq -r '.data.result[0].values[-1][1] // empty' 2>/dev/null
}

declare -A ESPERADO=(
  [replicas]='sum(up{job="backend"})'
  [disponibilidad]='min(probe_success)'
  [version]="max(minibiblioteca_build_info{version=\"${COMMIT}\"})"
  [errores500]='sum(http_server_requests_seconds_count{status="500"})'
  [cobertura]='max(minibiblioteca_ci_cobertura_porcentaje)'
)

for intento in $(seq 1 18); do
  replicas=$(consulta "${ESPERADO[replicas]}")
  disponibilidad=$(consulta "${ESPERADO[disponibilidad]}")
  version=$(consulta "${ESPERADO[version]}")
  errores=$(consulta "${ESPERADO[errores500]}")
  cobertura=$(consulta "${ESPERADO[cobertura]}")
  logs=$(logs_backend)

  ok=1
  [ "${replicas%.*}" -ge 2 ] 2>/dev/null || ok=0
  [ "$disponibilidad" = "1" ] || ok=0
  [ "$version" = "1" ] || ok=0
  [ "${errores%.*}" -ge 1 ] 2>/dev/null || ok=0
  [ -n "$cobertura" ] || ok=0
  [ "${logs%.*}" -ge 1 ] 2>/dev/null || ok=0

  if [ "$ok" = "1" ]; then break; fi
  echo "Esperando señales de monitoreo... intento ${intento}/18"
  sleep 10
done

marca() { [ "$1" = "1" ] && echo "✅" || echo "❌"; }
r_ok=$([ "${replicas%.*}" -ge 2 ] 2>/dev/null && echo 1 || echo 0)
d_ok=$([ "$disponibilidad" = "1" ] && echo 1 || echo 0)
v_ok=$([ "$version" = "1" ] && echo 1 || echo 0)
e_ok=$([ "${errores%.*}" -ge 1 ] 2>/dev/null && echo 1 || echo 0)
c_ok=$([ -n "$cobertura" ] && echo 1 || echo 0)
l_ok=$([ "${logs%.*}" -ge 1 ] 2>/dev/null && echo 1 || echo 0)

cat > evidencias/validacion.md <<EOF

### Validación de observabilidad

| Señal | Fuente | Valor | OK |
|---|---|---|---|
| Réplicas del backend medidas | Prometheus | ${replicas:-0} | $(marca "$r_ok") |
| Disponibilidad (sondas blackbox) | Prometheus | ${disponibilidad:-0} | $(marca "$d_ok") |
| Versión desplegada = commit | Prometheus | ${version:-no} | $(marca "$v_ok") |
| Errores 500 registrados | Prometheus | ${errores:-0} | $(marca "$e_ok") |
| Cobertura publicada por el pipeline | Pushgateway | ${cobertura:-no} % | $(marca "$c_ok") |
| Logs del backend (10 min) | Loki | ${logs:-0} | $(marca "$l_ok") |
EOF
cat evidencias/validacion.md

if [ "$ok" != "1" ]; then
  echo "OBSERVABILIDAD INCOMPLETA: el monitoreo no registra todas las señales."
  exit 1
fi
echo "Observabilidad validada para el commit ${COMMIT}."
