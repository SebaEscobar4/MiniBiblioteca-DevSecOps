# Versión fija de Nginx (rama stable). Variante "unprivileged": corre con
# el usuario nginx (UID 101) y escucha en el puerto 8080, lo que permite
# aplicar la política de "contenedores sin root" también en Kubernetes.
FROM nginxinc/nginx-unprivileged:1.30-alpine

ARG APP_VERSION=local
LABEL org.opencontainers.image.title="minibiblioteca-frontend" \
      org.opencontainers.image.revision="${APP_VERSION}"

# Parches de seguridad de Alpine (se aplican como root solo durante el build).
USER root
RUN apk upgrade --no-cache

# Plantilla: se convierte en /etc/nginx/conf.d/default.conf al arrancar.
COPY default.conf.template /etc/nginx/templates/default.conf.template
COPY index.html /usr/share/nginx/html/index.html
COPY styles.css /usr/share/nginx/html/styles.css
COPY app.js /usr/share/nginx/html/app.js

# Archivo de versión: permite comprobar qué commit está publicado
# abriendo http://HOST/version.txt (trazabilidad del despliegue).
RUN echo "${APP_VERSION}" > /usr/share/nginx/html/version.txt \
    && rm -f /etc/nginx/conf.d/default.conf \
    && chown -R 101:101 /etc/nginx/conf.d

# Valores por defecto para Docker Compose; Kubernetes los sobrescribe.
ENV NGINX_RESOLVER=127.0.0.11 \
    BACKEND_HOST=backend

USER 101
EXPOSE 8080

HEALTHCHECK --interval=10s --timeout=3s --retries=5 \
  CMD wget -qO- http://127.0.0.1:8080/healthz >/dev/null || exit 1
