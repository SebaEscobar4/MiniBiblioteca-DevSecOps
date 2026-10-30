package cl.duoc.devops.minibiblioteca.repository;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * Pruebas del repositorio real (lista en memoria). No necesita mocks:
 * se prueba directamente la clase concreta.
 */
class LibroRepositoryMemoriaTest {

    private final LibroRepositoryMemoria repositorio = new LibroRepositoryMemoria();

    @Test
    void findAll_deberiaRetornarLosCuatroLibrosIniciales() {
        assertEquals(4, repositorio.findAll().size());
    }

    @Test
    void findById_deberiaEncontrarUnLibroExistente() {
        assertEquals("Clean Code", repositorio.findById(1L).orElseThrow().titulo());
    }

    @Test
    void findById_deberiaRetornarVacioCuandoNoExiste() {
        assertTrue(repositorio.findById(99L).isEmpty());
    }
}
