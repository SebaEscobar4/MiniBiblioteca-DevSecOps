package cl.duoc.devops.minibiblioteca.observabilidad;

import cl.duoc.devops.minibiblioteca.model.Libro;
import cl.duoc.devops.minibiblioteca.service.LibroService;
import io.micrometer.core.instrument.simple.SimpleMeterRegistry;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.Mockito.when;

/**
 * Las métricas propias se registran con los valores del servicio y la versión
 * desplegada queda como etiqueta de minibiblioteca.build.info.
 */
@ExtendWith(MockitoExtension.class)
class MetricasNegocioTest {

    @Mock
    private LibroService libroService;

    @Test
    void bindTo_deberiaPublicarVersionYTotalesDelCatalogo() {
        when(libroService.listar()).thenReturn(List.of(
                new Libro(1L, "A", "Autor A", true),
                new Libro(2L, "B", "Autor B", false)));
        when(libroService.contarDisponibles()).thenReturn(1L);

        SimpleMeterRegistry registry = new SimpleMeterRegistry();
        new MetricasNegocio(libroService, "abc123").bindTo(registry);

        assertEquals(1.0, registry.get("minibiblioteca.build.info").tag("version", "abc123").gauge().value());
        assertEquals(2.0, registry.get("minibiblioteca.libros.total").gauge().value());
        assertEquals(1.0, registry.get("minibiblioteca.libros.disponibles").gauge().value());
    }
}
