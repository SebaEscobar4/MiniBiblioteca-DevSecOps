package cl.duoc.devops.minibiblioteca.exception;

public class ErrorSimuladoException extends RuntimeException {

    public ErrorSimuladoException() {
        super("Error simulado para la demostración de observabilidad");
    }
}
