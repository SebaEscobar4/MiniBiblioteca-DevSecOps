## Qué cambia

<!-- Describe el cambio en 1-3 líneas. -->

## Checklist de cumplimiento

- [ ] El pipeline está en verde (Snyk, auditoría, pruebas, SonarQube, Trivy, Kubernetes).
- [ ] No se agregan credenciales, `.env` ni llaves `.pem` al repositorio.
- [ ] Si cambia la infraestructura (`k8s/`, `docker-compose*.yml`, Dockerfile), la auditoría de cumplimiento sigue aprobada.
- [ ] Si cambia una métrica o alerta, el dashboard de Grafana sigue funcionando.
