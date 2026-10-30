# ============================================================
# ETAPA 1 - BUILD
# Maven compila el JAR. Esta etapa NO queda en la imagen final.
# ============================================================
FROM maven:3-eclipse-temurin-26-alpine AS build
WORKDIR /build

# Copiamos primero el POM para aprovechar la caché de Docker.
COPY pom.xml .
RUN mvn -B -DskipTests dependency:go-offline

# Copiamos el código y construimos el JAR.
COPY src ./src
RUN mvn -B -DskipTests clean package

# Separa el JAR en capas: dependencias (cambian poco) y código propio
# (cambia en cada commit). Así un cambio de código solo reemplaza una
# capa pequeña y el despliegue transfiere menos datos.
RUN java -Djarmode=tools -jar target/minibiblioteca-backend-0.0.1-SNAPSHOT.jar \
    extract --layers --destination /build/extracted

# ============================================================
# ETAPA 2 - RUNTIME
# Solo contiene Java Runtime + aplicación terminada.
# ============================================================
FROM eclipse-temurin:21-jre-alpine

# Trazabilidad: el pipeline envía el SHA del commit y la fecha.
ARG APP_VERSION=local
ARG BUILD_DATE=unknown
LABEL org.opencontainers.image.title="minibiblioteca-backend" \
      org.opencontainers.image.revision="${APP_VERSION}" \
      org.opencontainers.image.created="${BUILD_DATE}"

# curl se utiliza en el healthcheck.
# apk upgrade aplica los parches de seguridad publicados para Alpine.
RUN apk upgrade --no-cache \
    && apk add --no-cache curl \
    && addgroup -S app \
    && adduser -S app -G app

WORKDIR /app

# Las capas se copian de la que menos cambia a la que más cambia.
COPY --from=build --chown=app:app /build/extracted/dependencies/ ./
COPY --from=build --chown=app:app /build/extracted/spring-boot-loader/ ./
COPY --from=build --chown=app:app /build/extracted/snapshot-dependencies/ ./
COPY --from=build --chown=app:app /build/extracted/application/ ./

# Usuario sin privilegios: si alguien compromete la app, no es root.
USER app
EXPOSE 8080

# La imagen se autodiagnostica: Docker marca el contenedor como
# healthy/unhealthy aunque se ejecute fuera de Compose.
HEALTHCHECK --interval=10s --timeout=4s --start-period=20s --retries=12 \
  CMD curl -fsS http://127.0.0.1:8080/api/health || exit 1

ENTRYPOINT ["java", "-jar", "/app/minibiblioteca-backend-0.0.1-SNAPSHOT.jar"]
