package cl.duoc.devops.minibiblioteca.controller;

import cl.duoc.devops.minibiblioteca.exception.LibroNoEncontradoException;
import cl.duoc.devops.minibiblioteca.model.Libro;
import cl.duoc.devops.minibiblioteca.service.LibroService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import java.util.List;

import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/**
 * Pruebas de la capa web: verifican las URL, los códigos HTTP y el JSON
 * que recibe el frontend. El servicio se simula con Mockito, así que no
 * se levanta Spring completo y la prueba tarda milisegundos.
 */
@ExtendWith(MockitoExtension.class)
class LibroControllerTest {

    @Mock
    private LibroService libroService;

    @InjectMocks
    private LibroController libroController;

    private MockMvc mockMvc;

    @BeforeEach
    void setUp() {
        // MockMvc simula peticiones HTTP sin abrir un puerto real.
        // Se registra ApiExceptionHandler para probar también el 404.
        mockMvc = MockMvcBuilders.standaloneSetup(libroController)
                .setControllerAdvice(new ApiExceptionHandler())
                .build();
    }

    @Test
    void listar_deberiaResponder200ConLosLibros() throws Exception {
        when(libroService.listar()).thenReturn(List.of(
                new Libro(1L, "Clean Code", "Robert C. Martin", true),
                new Libro(2L, "Docker Deep Dive", "Nigel Poulton", false)
        ));

        mockMvc.perform(get("/api/libros"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.length()").value(2))
                .andExpect(jsonPath("$[0].titulo").value("Clean Code"));
    }

    @Test
    void buscar_deberiaResponder200CuandoElLibroExiste() throws Exception {
        when(libroService.buscarPorId(1L))
                .thenReturn(new Libro(1L, "Clean Code", "Robert C. Martin", true));

        mockMvc.perform(get("/api/libros/1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.autor").value("Robert C. Martin"));
    }

    @Test
    void buscar_deberiaResponder404CuandoElLibroNoExiste() throws Exception {
        when(libroService.buscarPorId(99L)).thenThrow(new LibroNoEncontradoException(99L));

        mockMvc.perform(get("/api/libros/99"))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.error").value("No existe un libro con id 99"));
    }

    @Test
    void resumen_deberiaInformarTotalYDisponibles() throws Exception {
        when(libroService.listar()).thenReturn(List.of(
                new Libro(1L, "A", "Autor A", true),
                new Libro(2L, "B", "Autor B", false),
                new Libro(3L, "C", "Autor C", true)
        ));
        when(libroService.contarDisponibles()).thenReturn(2L);

        mockMvc.perform(get("/api/resumen"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.total").value(3))
                .andExpect(jsonPath("$.disponibles").value(2));
    }

    @Test
    void health_deberiaResponderUp() throws Exception {
        mockMvc.perform(get("/api/health"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("UP"));
    }
}
