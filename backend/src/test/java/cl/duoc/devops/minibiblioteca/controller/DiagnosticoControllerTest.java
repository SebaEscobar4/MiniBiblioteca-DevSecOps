package cl.duoc.devops.minibiblioteca.controller;

import org.junit.jupiter.api.Test;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/**
 * El endpoint de diagnóstico debe responder 500 con un JSON de error,
 * que es lo que después se cuenta como "error registrado" en el dashboard.
 */
class DiagnosticoControllerTest {

    private final MockMvc mockMvc = MockMvcBuilders.standaloneSetup(new DiagnosticoController())
            .setControllerAdvice(new ApiExceptionHandler())
            .build();

    @Test
    void error_deberiaResponder500ConMensaje() throws Exception {
        mockMvc.perform(get("/api/diagnostico/error"))
                .andExpect(status().isInternalServerError())
                .andExpect(jsonPath("$.error").value("Error simulado para la demostración de observabilidad"));
    }
}
