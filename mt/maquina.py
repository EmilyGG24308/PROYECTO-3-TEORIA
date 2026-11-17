from dataclasses import dataclass

# el blanco se guarda como None, igual que el null del YAML
BLANCO = None
MOVIMIENTOS = ("L", "R", "S")


@dataclass(frozen=True)
class Transicion:
    estado: str
    memoria: str | None
    lee: str | None
    nuevo_estado: str
    nueva_memoria: str | None
    escribe: str | None
    movimiento: str

    @property
    def clave(self):
        return (self.estado, self.memoria, self.lee)


@dataclass
class Maquina:
    estados: list
    inicial: str
    finales: list
    alfabeto: list
    alfabeto_cinta: list
    transiciones: dict

    def buscar(self, estado, memoria, simbolo):
        return self.transiciones.get((estado, memoria, simbolo))
