package cl.duoc.devops.minibiblioteca.controller;

import cl.duoc.devops.minibiblioteca.exception.ErrorSimuladoException;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * Endpoint de diagnóstico para la demostración de observabilidad: provoca un
 * error 500 controlado que queda registrado en las métricas
 * (http_server_requests_seconds_count{status="500"}), en los logs (nivel ERROR)
 * y, por lo tanto, en el panel "Errores" del dashboard.
 *
 * Se puede desactivar con app.diagnostico.habilitado=false.
 */
@RestController
@RequestMapping("/api/diagnostico")
@ConditionalOnProperty(name = "app.diagnostico.habilitado", havingValue = "true")
public class DiagnosticoController {

    @GetMapping("/error")
    public void error() {
        throw new ErrorSimuladoException();
    }
}
