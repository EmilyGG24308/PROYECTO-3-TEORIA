import itertools
import unittest
from pathlib import Path

from mt.lector import cargar_archivo
from mt.simulador import ACEPTADA, RECHAZADA, simular

EJEMPLOS = Path(__file__).resolve().parent.parent / "ejemplos"


def todas(alfabeto, hasta):
    for largo in range(hasta + 1):
        for tupla in itertools.product(alfabeto, repeat=largo):
            yield "".join(tupla)


class PruebasReconocedora(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.maquina, cls.cadenas = cargar_archivo(EJEMPLOS / "reconocedora.yaml")

    def test_cadenas_de_demostracion(self):
        esperado = {"aaabbbccc": ACEPTADA, "aaaabbbbcccc": ACEPTADA,
                    "aaabbbbccc": RECHAZADA, "aabbccabc": RECHAZADA}
        self.assertEqual(self.cadenas, list(esperado))
        for cadena, motivo in esperado.items():
            self.assertEqual(simular(self.maquina, cadena, 10000).motivo, motivo, cadena)

    def test_contra_referencia(self):
        # referencia en Python solo para comparar, la maquina no la usa
        for cadena in todas("abc", 8):
            n = len(cadena) // 3
            en_l = n >= 1 and cadena == "a" * n + "b" * n + "c" * n
            motivo = simular(self.maquina, cadena, 10000).motivo
            self.assertEqual(motivo, ACEPTADA if en_l else RECHAZADA, cadena)


class PruebasAlteradora(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.maquina, cls.cadenas = cargar_archivo(EJEMPLOS / "alteradora.yaml")

    def test_cadenas_de_demostracion(self):
        esperado = {"00101": "10100", "110010": "010011", "1011001": "1001101", "00011": "11000"}
        self.assertEqual(self.cadenas, list(esperado))
        for cadena, invertida in esperado.items():
            r = simular(self.maquina, cadena, 10000)
            self.assertEqual(r.motivo, ACEPTADA)
            self.assertEqual("".join(r.cinta_final), invertida)

    def test_contra_referencia(self):
        for cadena in todas("01", 10):
            r = simular(self.maquina, cadena, 10000)
            self.assertEqual(r.motivo, ACEPTADA, cadena)
            # sin marcas ni blancos sobrantes
            self.assertEqual("".join(r.cinta_final), cadena[::-1], cadena)


if __name__ == "__main__":
    unittest.main()
