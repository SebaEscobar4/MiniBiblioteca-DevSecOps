"""Genera observabilidad/grafana/dashboards/minibiblioteca.json."""
import json
import sys

PROM = {"type": "prometheus", "uid": "prometheus"}
LOKI = {"type": "loki", "uid": "loki"}
APP = 'application="minibiblioteca-backend"'

paneles = []
pid = 0


def nuevo_id():
    global pid
    pid += 1
    return pid


def fila(titulo, y):
    paneles.append({"type": "row", "title": titulo, "id": nuevo_id(), "collapsed": False,
                    "gridPos": {"h": 1, "w": 24, "x": 0, "y": y}, "panels": []})


def stat(titulo, expr, x, y, w=4, unidad="none", decimales=None, umbrales=None, leyenda=None,
         texto="value", descripcion=""):
    p = {
        "type": "stat", "title": titulo, "id": nuevo_id(), "datasource": PROM, "description": descripcion,
        "gridPos": {"h": 4, "w": w, "x": x, "y": y},
        "targets": [{"refId": "A", "datasource": PROM, "expr": expr, "instant": True,
                     "legendFormat": leyenda or "__auto"}],
        "options": {"reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
                    "colorMode": "background", "graphMode": "none", "textMode": texto, "justifyMode": "center"},
        "fieldConfig": {"defaults": {"unit": unidad, "noValue": "sin datos",
                                     "thresholds": {"mode": "absolute", "steps": umbrales or [
                                         {"color": "blue", "value": None}]}},
                        "overrides": []},
    }
    if decimales is not None:
        p["fieldConfig"]["defaults"]["decimals"] = decimales
    paneles.append(p)


def serie(titulo, targets, x, y, w=12, h=8, unidad="none", descripcion=""):
    paneles.append({
        "type": "timeseries", "title": titulo, "id": nuevo_id(), "datasource": PROM, "description": descripcion,
        "gridPos": {"h": h, "w": w, "x": x, "y": y},
        "targets": [{"refId": chr(65 + i), "datasource": PROM, "expr": e, "legendFormat": l}
                    for i, (e, l) in enumerate(targets)],
        "fieldConfig": {"defaults": {"unit": unidad, "custom": {"lineWidth": 2, "fillOpacity": 10}}, "overrides": []},
        "options": {"legend": {"displayMode": "list", "placement": "bottom"}, "tooltip": {"mode": "multi"}},
    })


def logs(titulo, expr, x, y, w=12, h=9, descripcion=""):
    paneles.append({
        "type": "logs", "title": titulo, "id": nuevo_id(), "datasource": LOKI, "description": descripcion,
        "gridPos": {"h": h, "w": w, "x": x, "y": y},
        "targets": [{"refId": "A", "datasource": LOKI, "expr": expr}],
        "options": {"showTime": True, "wrapLogMessage": True, "sortOrder": "Descending", "enableLogDetails": True},
    })


ROJO_VERDE = [{"color": "red", "value": None}, {"color": "green", "value": 1}]

# ---------- Fila 1: estado general ----------
fila("Estado general del servicio", 0)
stat("Réplicas del backend activas", 'sum(up{job="backend"})', 0, 1, umbrales=ROJO_VERDE,
     descripcion="Réplicas que responden a Prometheus en /actuator/prometheus.")
stat("Disponibilidad ahora", "avg(probe_success) * 100", 4, 1, unidad="percent", decimales=0,
     umbrales=[{"color": "red", "value": None}, {"color": "green", "value": 100}],
     descripcion="Sondas HTTP de blackbox contra el frontend y la API.")
stat("Disponibilidad en el período", "avg_over_time((avg(probe_success))[$__range:30s]) * 100", 8, 1,
     unidad="percent", decimales=2,
     umbrales=[{"color": "red", "value": None}, {"color": "orange", "value": 99}, {"color": "green", "value": 99.9}])
stat("Errores 5xx en el período",
     f'sum(increase(http_server_requests_seconds_count{{{APP},status=~"5.."}}[$__range])) or vector(0)', 12, 1,
     decimales=0, umbrales=[{"color": "green", "value": None}, {"color": "red", "value": 1}],
     descripcion="Errores registrados por el backend (incluye /api/diagnostico/error).")
stat("Alertas activas", 'count(ALERTS{alertstate="firing"}) or vector(0)', 16, 1, decimales=0,
     umbrales=[{"color": "green", "value": None}, {"color": "red", "value": 1}])
stat("Versión desplegada", "max by (version) (minibiblioteca_build_info)", 20, 1, leyenda="{{version}}",
     texto="name", descripcion="Commit que está corriendo (trazabilidad).")

# ---------- Fila 2: CI/CD ----------
fila("Pipeline CI/CD (publicado por GitHub Actions en Pushgateway)", 5)
stat("Cobertura de pruebas", "max(minibiblioteca_ci_cobertura_porcentaje)", 0, 6, unidad="percent", decimales=1,
     umbrales=[{"color": "red", "value": None}, {"color": "green", "value": 80}],
     descripcion="Cobertura de líneas medida por JaCoCo; el mínimo exigido es 80 %.")
stat("Pruebas ejecutadas", "max(minibiblioteca_ci_pruebas_total)", 4, 6, decimales=0)
stat("Pruebas fallidas", "max(minibiblioteca_ci_pruebas_fallidas)", 8, 6, decimales=0,
     umbrales=[{"color": "green", "value": None}, {"color": "red", "value": 1}])
stat("Tiempo de despliegue", "max(minibiblioteca_ci_despliegue_segundos)", 12, 6, unidad="s", decimales=0,
     descripcion="Desde kubectl apply hasta que todas las réplicas quedan listas.")
stat("Duración del pipeline", "max(minibiblioteca_ci_pipeline_segundos)", 16, 6, unidad="s", decimales=0,
     descripcion="Desde el inicio del workflow hasta el fin del despliegue.")
stat("Último pipeline", "max(minibiblioteca_ci_ultima_ejecucion_timestamp_seconds) * 1000", 20, 6,
     unidad="dateTimeFromNow")

# ---------- Fila 3: tráfico y errores ----------
fila("Tráfico, errores y latencia", 10)
serie("Peticiones por segundo por endpoint",
      [(f'sum by (uri) (rate(http_server_requests_seconds_count{{{APP},uri!~"/actuator.*"}}[1m]))', "{{uri}}")],
      0, 11, w=8, unidad="reqps")
serie("Errores por código HTTP",
      [(f'sum by (status) (rate(http_server_requests_seconds_count{{{APP},status=~"4..|5.."}}[1m]))',
        "HTTP {{status}}")],
      8, 11, w=8, unidad="reqps", descripcion="4xx = error del cliente (p. ej. libro inexistente); 5xx = error del servidor.")
serie("Tiempo de respuesta (percentil 95)",
      [(f'histogram_quantile(0.95, sum by (le) (rate(http_server_requests_seconds_bucket{{{APP},uri!~"/actuator.*"}}[1m])))',
        "p95")],
      16, 11, w=8, unidad="s")

# ---------- Fila 4: recursos ----------
fila("Uso de recursos", 19)
serie("Uso de CPU por réplica", [("process_cpu_usage * 100", "{{instance}}")], 0, 20, unidad="percent",
      descripcion="Porcentaje de CPU que usa el proceso Java de cada réplica.")
serie("Memoria heap por réplica",
      [('sum by (instance) (jvm_memory_used_bytes{area="heap"})', "usada {{instance}}"),
       ('sum by (instance) (jvm_memory_max_bytes{area="heap"})', "máxima {{instance}}")],
      12, 20, unidad="bytes")

# ---------- Fila 5: logs y alertas ----------
fila("Logs y alertas", 28)
logs("Logs de error del backend", '{service="backend"} | json | log_level="ERROR"', 0, 29,
     descripcion="Logs JSON (formato ECS) filtrados por nivel ERROR.")
logs("Logs de la aplicación (backend y frontend)", '{service=~"backend|frontend"} != "Blackbox-Exporter" != "kube-probe"', 12, 29,
     descripcion="Sin las sondas de salud automáticas, para ver solo tráfico real.")
paneles.append({
    "type": "table", "title": "Alertas activas", "id": nuevo_id(), "datasource": PROM,
    "gridPos": {"h": 6, "w": 24, "x": 0, "y": 38},
    "targets": [{"refId": "A", "datasource": PROM, "expr": 'ALERTS{alertstate="firing"}', "instant": True,
                 "format": "table"}],
    "transformations": [{"id": "organize", "options": {
        "excludeByName": {"Time": True, "Value": True, "__name__": True},
        "renameByName": {"alertname": "Alerta", "severity": "Severidad", "instance": "Instancia"}}}],
    "fieldConfig": {"defaults": {"noValue": "Sin alertas activas"}, "overrides": []},
})

dashboard = {
    "uid": "minibiblioteca-devops",
    "title": "MiniBiblioteca - Observabilidad DevOps",
    "description": "Disponibilidad, errores, recursos, logs y métricas del pipeline CI/CD.",
    "tags": ["minibiblioteca", "devops", "ep3"],
    "timezone": "browser",
    "schemaVersion": 39,
    "version": 1,
    "editable": False,
    "refresh": "10s",
    "time": {"from": "now-30m", "to": "now"},
    "panels": paneles,
}

with open(sys.argv[1], "w", encoding="utf-8") as f:
    json.dump(dashboard, f, ensure_ascii=False, indent=2)
print(len(paneles), "paneles")
