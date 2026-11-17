import unittest

from mt.cinta import Cinta
from mt.lector import cargar_texto
from mt.maquina import BLANCO
from mt.simulador import ACEPTADA, LIMITE, RECHAZADA, simular


def maquina(estados, final, alfabeto, cinta, delta, cadenas=("a",)):
    # arma un YAML pequeño con el mismo formato del proyecto
    lineas = [
        "q_states:",
        f"  q_list: {estados}",
        "  initial: 'q0'",
        f"  final: '{final}'",
        f"alphabet: {alfabeto}",
        f"tape_alphabet: {cinta}",
        "delta:" if delta else "delta: []",
    ]
    for (q, m, s), (q2, m2, w, d) in delta:
        lineas.append(f"  - params: {{initial_state: '{q}', mem_cache_value: {m}, tape_input: {s}}}")
        lineas.append(f"    output: {{final_state: '{q2}', mem_cache_value: {m2}, tape_output: {w}, "
                      f"tape_displacement: {d}}}")
    lineas.append("simulation_strings:")
    lineas += [f"  - '{c}'" for c in cadenas]
    return cargar_texto("\n".join(lineas))[0]


class PruebasCinta(unittest.TestCase):
    def test_izquierda_del_origen(self):
        cinta = Cinta("ab")
        cinta.mover("L")
        self.assertEqual(cinta.cabezal, -1)
        self.assertIs(cinta.leer(), BLANCO)
        cinta.escribir("X")
        self.assertEqual(cinta.contenido_final(), ["X", "a", "b"])

    def test_movimiento_s(self):
        cinta = Cinta("ab")
        cinta.mover("S")
        self.assertEqual(cinta.cabezal, 0)
        self.assertEqual(cinta.leer(), "a")

    def test_blancos(self):
        cinta = Cinta("abc")
        cinta.mover("R")
        cinta.escribir(BLANCO)
        self.assertIs(cinta.leer(), BLANCO)
        self.assertEqual(cinta.contenido_final(), ["a", BLANCO, "c"])
        vacia = Cinta("")
        self.assertIs(vacia.leer(), BLANCO)
        self.assertEqual(vacia.rango_visible(), (0, 0))
        self.assertEqual(vacia.contenido_final(), [])


class PruebasSimulador(unittest.TestCase):
    def test_moverse_a_la_izquierda_del_origen(self):
        m = maquina("['q0', 'q1', 'q2']", "q2", "['a']", "['a', 'X', null]", [
            (("q0", "null", "'a'"), ("q1", "null", "'a'", "L")),
            (("q1", "null", "null"), ("q2", "null", "'X'", "S")),
        ])
        r = simular(m, "a", 100)
        self.assertEqual(r.motivo, ACEPTADA)
        self.assertEqual(r.descripciones[1].cabezal, -1)
        self.assertEqual(r.cinta_final, ["X", "a"])

    def test_memoria_se_guarda_y_se_consulta(self):
        # copia el primer simbolo al final de la cadena usando la memoria
        delta = [(("q0", "null", "'a'"), ("q1", "'a'", "'a'", "R")),
                 (("q0", "null", "'b'"), ("q1", "'b'", "'b'", "R"))]
        for m_ in ("'a'", "'b'"):
            for s in ("'a'", "'b'"):
                delta.append((("q1", m_, s), ("q1", m_, s, "R")))
            delta.append((("q1", m_, "null"), ("q2", "null", m_, "S")))
        m = maquina("['q0', 'q1', 'q2']", "q2", "['a', 'b']", "['a', 'b', null]", delta)
        r = simular(m, "bab", 100)
        self.assertEqual(r.motivo, ACEPTADA)
        self.assertEqual([d.memoria for d in r.descripciones], [BLANCO, "b", "b", "b", BLANCO])
        self.assertEqual("".join(r.cinta_final), "babb")

    def test_null_en_memoria_no_es_comodin(self):
        m = maquina("['q0', 'q1', 'q2']", "q2", "['a']", "['a', null]", [
            (("q0", "null", "'a'"), ("q1", "'a'", "'a'", "S")),
            (("q1", "null", "'a'"), ("q2", "null", "'a'", "S")),
        ])
        r = simular(m, "a", 100)
        self.assertEqual(r.motivo, RECHAZADA)
        self.assertEqual(r.descripciones[-1].memoria, "a")

    def test_sin_transicion_se_rechaza(self):
        m = maquina("['q0', 'q1']", "q1", "['a', 'b']", "['a', 'b', null]", [
            (("q0", "null", "'a'"), ("q0", "null", "'a'", "R")),
        ])
        r = simular(m, "aab", 100)
        self.assertEqual(r.motivo, RECHAZADA)
        self.assertEqual(r.pasos, 2)
        self.assertEqual(r.descripciones[-1].leido, "b")

    def test_aceptacion_sin_pasos(self):
        m = maquina("['q0']", "q0", "['a']", "['a', null]", [])
        r = simular(m, "aaa", 100)
        self.assertEqual(r.motivo, ACEPTADA)
        self.assertEqual(r.pasos, 0)

    def test_cada_cadena_empieza_de_cero(self):
        m = maquina("['q0', 'q1']", "q1", "['a', 'b']", "['a', 'b', 'X', null]", [
            (("q0", "null", "'a'"), ("q0", "'a'", "'X'", "R")),
            (("q0", "'a'", "'a'"), ("q0", "'a'", "'X'", "R")),
            (("q0", "'a'", "null"), ("q1", "'a'", "null", "S")),
        ])
        primera = simular(m, "aa", 100)
        segunda = simular(m, "b", 100)
        self.assertEqual(primera.motivo, ACEPTADA)
        self.assertEqual(segunda.motivo, RECHAZADA)
        inicio = segunda.descripciones[0]
        self.assertEqual((inicio.estado, inicio.memoria, inicio.cabezal, inicio.celdas), ("q0", BLANCO, 0, ["b"]))
        self.assertEqual(segunda.cinta_final, ["b"])

    def test_limite_de_pasos(self):
        m = maquina("['q0', 'q1']", "q1", "['a']", "['a', null]", [
            (("q0", "null", "'a'"), ("q0", "null", "'a'", "R")),
            (("q0", "null", "null"), ("q0", "null", "null", "R")),
        ])
        r = simular(m, "a", 25)
        self.assertEqual(r.motivo, LIMITE)
        self.assertEqual(r.pasos, 25)
        self.assertEqual(len(r.descripciones), 26)

    def test_rechazo_justo_en_el_limite(self):
        m = maquina("['q0', 'q1']", "q1", "['a']", "['a', null]", [
            (("q0", "null", "'a'"), ("q0", "null", "'a'", "R")),
        ])
        self.assertEqual(simular(m, "aaa", 3).motivo, RECHAZADA)


if __name__ == "__main__":
    unittest.main()
