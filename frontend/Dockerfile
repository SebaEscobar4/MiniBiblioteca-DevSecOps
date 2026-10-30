# Versión fija de Nginx (rama stable): "nginx:alpine" cambia sola con
# el tiempo y una build de hoy podría no ser igual a la de mañana.
FROM nginx:1.30-alpine

ARG APP_VERSION=local
LABEL org.opencontainers.image.title="minibiblioteca-frontend" \
      org.opencontainers.image.revision="${APP_VERSION}"

# Parches de seguridad de Alpine.
RUN apk upgrade --no-cache

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY index.html /usr/share/nginx/html/index.html
COPY styles.css /usr/share/nginx/html/styles.css
COPY app.js /usr/share/nginx/html/app.js

# Archivo de versión: permite comprobar qué commit está publicado
# abriendo http://HOST/version.txt (trazabilidad del despliegue).
RUN echo "${APP_VERSION}" > /usr/share/nginx/html/version.txt

EXPOSE 80

HEALTHCHECK --interval=10s --timeout=3s --retries=5 \
  CMD wget -qO- http://127.0.0.1/ >/dev/null || exit 1
