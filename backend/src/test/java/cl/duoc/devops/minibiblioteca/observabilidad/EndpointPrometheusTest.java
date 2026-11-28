package cl.duoc.devops.minibiblioteca.observabilidad;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.core.env.Environment;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * Prueba de integraciÃ³n: levanta la aplicaciÃ³n completa en un puerto aleatorio
 * y verifica lo que Prometheus y Kubernetes van a consultar.
 */
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT,
        properties = "app.version=test-sha")
class EndpointPrometheusTest {

    @Autowired
    private Environment environment;

    private final HttpClient http = HttpClient.newHttpClient();

    private HttpResponse<String> get(String ruta) throws Exception {
        String puerto = environment.getProperty("local.server.port");
        HttpRequest request = HttpRequest.newBuilder(URI.create("http://localhost:" + puerto + ruta)).build();
        return http.send(request, HttpResponse.BodyHandlers.ofString());
    }

    @Test
    void prometheus_deberiaPublicarMetricasHttpJvmYPropias() throws Exception {
        get("/api/libros");

        HttpResponse<String> respuesta = get("/actuator/prometheus");

        assertEquals(200, respuesta.statusCode());
        String cuerpo = respuesta.body();
        assertTrue(cuerpo.contains("http_server_requests_seconds_count"), "mÃ©tricas HTTP");
        assertTrue(cuerpo.contains("jvm_memory_used_bytes"), "memoria JVM");
        assertTrue(cuerpo.contains("process_cpu_usage"), "uso de CPU");
        assertTrue(cuerpo.contains("minibiblioteca_build_info{"), "versiÃ³n desplegada");
        assertTrue(cuerpo.contains("version=\"test-sha\""), "etiqueta con el commit");
        assertTrue(cuerpo.contains("application=\"minibiblioteca-backend\""), "etiqueta de aplicaciÃ³n");
    }

    @Test
    void probes_deberianEstarDisponiblesParaKubernetes() throws Exception {
        assertEquals(200, get("/actuator/health/liveness").statusCode());
        assertEquals(200, get("/actuator/health/readiness").statusCode());
    }
}
