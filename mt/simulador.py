from dataclasses import dataclass

from .cinta import Cinta
from .maquina import BLANCO

ACEPTADA = "aceptada"
RECHAZADA = "rechazada"
LIMITE = "limite"


@dataclass
class Descripcion:
    paso: int
    estado: str
    memoria: str | None
    inicio: int
    celdas: list
    cabezal: int

    @property
    def leido(self):
        return self.celdas[self.cabezal - self.inicio]


@dataclass
class Resultado:
    cadena: str
    descripciones: list
    # aplicadas[i] es la transicion que lleva de descripciones[i] a descripciones[i + 1]
    aplicadas: list
    motivo: str
    cinta_final: list

    @property
    def pasos(self):
        return len(self.aplicadas)


def _foto(paso, estado, memoria, cinta):
    inicio, fin = cinta.rango_visible()
    return Descripcion(paso, estado, memoria, inicio, cinta.contenido(inicio, fin), cinta.cabezal)


def simular(maquina, cadena, max_pasos):
    # cada cadena arranca con cinta, estado y memoria nuevos
    cinta = Cinta(cadena)
    estado = maquina.inicial
    memoria = BLANCO
    descripciones = [_foto(0, estado, memoria, cinta)]
    aplicadas = []

    transicion = maquina.buscar(estado, memoria, cinta.leer())
    while estado not in maquina.finales and transicion is not None and len(aplicadas) < max_pasos:
        cinta.escribir(transicion.escribe)
        cinta.mover(transicion.movimiento)
        estado = transicion.nuevo_estado
        memoria = transicion.nueva_memoria
        aplicadas.append(transicion)
        descripciones.append(_foto(len(aplicadas), estado, memoria, cinta))
        transicion = maquina.buscar(estado, memoria, cinta.leer())

    if estado in maquina.finales:
        motivo = ACEPTADA
    elif transicion is None:
        # si no hay transicion, se rechaza
        motivo = RECHAZADA
    else:
        motivo = LIMITE

    return Resultado(cadena, descripciones, aplicadas, motivo, cinta.contenido_final())
