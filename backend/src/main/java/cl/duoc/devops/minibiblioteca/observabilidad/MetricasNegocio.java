package cl.duoc.devops.minibiblioteca.observabilidad;

import cl.duoc.devops.minibiblioteca.service.LibroService;
import io.micrometer.core.instrument.Gauge;
import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.core.instrument.binder.MeterBinder;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

/**
 * Métricas propias del microservicio, además de las que Spring Boot publica
 * automáticamente (peticiones HTTP, JVM, CPU, memoria).
 *
 * - minibiblioteca_build_info{version="<sha>"} = 1  -> qué commit está corriendo.
 * - minibiblioteca_libros_total / _disponibles      -> estado del catálogo.
 */
@Component
public class MetricasNegocio implements MeterBinder {

    private final LibroService libroService;
    private final String version;

    public MetricasNegocio(LibroService libroService, @Value("${app.version}") String version) {
        this.libroService = libroService;
        this.version = version;
    }

    @Override
    public void bindTo(MeterRegistry registry) {
        Gauge.builder("minibiblioteca.build.info", () -> 1)
                .description("Versión (commit) desplegada del backend")
                .tag("version", version)
                .register(registry);

        Gauge.builder("minibiblioteca.libros.total", libroService, s -> s.listar().size())
                .description("Cantidad de libros en el catálogo")
                .register(registry);

        Gauge.builder("minibiblioteca.libros.disponibles", libroService, LibroService::contarDisponibles)
                .description("Cantidad de libros disponibles")
                .register(registry);
    }
}
