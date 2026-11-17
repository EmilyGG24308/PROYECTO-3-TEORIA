from .maquina import BLANCO


class Cinta:
    # solo se guardan las celdas no blancas, asi la cinta crece hacia los dos lados
    def __init__(self, cadena):
        self.celdas = {i: simbolo for i, simbolo in enumerate(cadena)}
        self.cabezal = 0

    def leer(self):
        return self.celdas.get(self.cabezal, BLANCO)

    def escribir(self, simbolo):
        if simbolo is BLANCO:
            self.celdas.pop(self.cabezal, None)
        else:
            self.celdas[self.cabezal] = simbolo

    def mover(self, movimiento):
        if movimiento == "L":
            self.cabezal -= 1
        elif movimiento == "R":
            self.cabezal += 1

    def rango_visible(self):
        # lo no blanco mas la celda del cabezal, aunque sea blanca
        posiciones = list(self.celdas) + [self.cabezal]
        return min(posiciones), max(posiciones)

    def contenido(self, desde, hasta):
        return [self.celdas.get(i, BLANCO) for i in range(desde, hasta + 1)]

    def contenido_final(self):
        if not self.celdas:
            return []
        return self.contenido(min(self.celdas), max(self.celdas))
