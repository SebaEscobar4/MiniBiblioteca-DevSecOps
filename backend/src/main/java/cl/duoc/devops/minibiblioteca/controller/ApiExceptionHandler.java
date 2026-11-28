package cl.duoc.devops.minibiblioteca.controller;

import cl.duoc.devops.minibiblioteca.exception.ErrorSimuladoException;
import cl.duoc.devops.minibiblioteca.exception.LibroNoEncontradoException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.util.Map;

@RestControllerAdvice
public class ApiExceptionHandler {

    private static final Logger log = LoggerFactory.getLogger(ApiExceptionHandler.class);

    @ExceptionHandler(LibroNoEncontradoException.class)
    @ResponseStatus(HttpStatus.NOT_FOUND)
    public Map<String, String> libroNoEncontrado(LibroNoEncontradoException ex) {
        // WARN: es un error del cliente, no del sistema.
        log.warn("Libro no encontrado: {}", ex.getMessage());
        return Map.of("error", ex.getMessage());
    }

    @ExceptionHandler(ErrorSimuladoException.class)
    @ResponseStatus(HttpStatus.INTERNAL_SERVER_ERROR)
    public Map<String, String> errorSimulado(ErrorSimuladoException ex) {
        // ERROR: aparece en los logs y en el panel de errores del dashboard.
        log.error("Error interno: {}", ex.getMessage());
        return Map.of("error", ex.getMessage());
    }
}
