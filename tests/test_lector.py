import unittest

from mt.lector import ErrorConfiguracion, cargar_archivo, cargar_texto
from mt.maquina import BLANCO

BASE = """
q_states:
  q_list: ['q0', 'q1']
  initial: 'q0'
  final: 'q1'
alphabet: ['a']
tape_alphabet: ['a', 'X', null]
delta:
  - params:
      initial_state: 'q0'
      mem_cache_value:
      tape_input: 'a'
    output:
      final_state: 'q1'
      mem_cache_value:
      tape_output:
      tape_displacement: R
simulation_strings:
  - 'aa'
"""


class PruebasLector(unittest.TestCase):
    def error_con(self, texto, fragmento):
        with self.assertRaises(ErrorConfiguracion) as ctx:
            cargar_texto(texto)
        self.assertTrue(any(fragmento in e for e in ctx.exception.errores),
                        f"no se encontro '{fragmento}' en {ctx.exception.errores}")

    def test_base_valida(self):
        maquina, cadenas = cargar_texto(BASE)
        self.assertEqual(cadenas, ["aa"])
        t = maquina.buscar("q0", BLANCO, "a")
        # los valores vacios del YAML son el blanco
        self.assertIs(t.nueva_memoria, BLANCO)
        self.assertIs(t.escribe, BLANCO)

    def test_null_es_distinto_de_la_cadena_null(self):
        self.error_con(BASE.replace("tape_alphabet: ['a', 'X', null]", "tape_alphabet: ['a', 'X', 'null']"),
                       "debe tener exactamente un carácter")

    def test_archivo_inexistente(self):
        with self.assertRaises(ErrorConfiguracion) as ctx:
            cargar_archivo("no_existe.yaml")
        self.assertIn("no existe el archivo", ctx.exception.errores[0])

    def test_yaml_mal_formado(self):
        self.error_con("q_states: [a, b\nalphabet: x", "YAML mal formado")

    def test_campos_faltantes(self):
        self.error_con(BASE.replace("simulation_strings:\n  - 'aa'\n", ""), "faltan campos obligatorios")
        self.error_con(BASE.replace("      tape_input: 'a'\n", ""), "faltan campos tape_input")

    def test_tipos_invalidos(self):
        self.error_con(BASE.replace("alphabet: ['a']", "alphabet: 'a'"), "alphabet debe ser una lista")
        self.error_con(BASE.replace("  - 'aa'", "  - 101"), "debe ser texto")

    def test_estados_no_declarados(self):
        self.error_con(BASE.replace("final_state: 'q1'", "final_state: 'q9'"), "'q9' no es un estado declarado")

    def test_inicial_y_final_invalidos(self):
        self.error_con(BASE.replace("initial: 'q0'", "initial: 'q5'"), "q_states.initial")
        self.error_con(BASE.replace("final: 'q1'", "final: 'qf'"), "q_states.final")

    def test_simbolos_fuera_de_la_cinta(self):
        self.error_con(BASE.replace("tape_input: 'a'", "tape_input: 'b'"), "no pertenece a tape_alphabet")
        self.error_con(BASE.replace("      tape_output:\n", "      tape_output: 'Q'\n"),
                       "no pertenece a tape_alphabet")
        self.error_con(BASE.replace("      mem_cache_value:\n      tape_output:",
                                    "      mem_cache_value: 'Q'\n      tape_output:"),
                       "output.mem_cache_value")

    def test_alfabeto_no_contenido(self):
        self.error_con(BASE.replace("alphabet: ['a']", "alphabet: ['a', 'b']"), "no está contenido")

    def test_falta_el_blanco(self):
        self.error_con(BASE.replace("tape_alphabet: ['a', 'X', null]", "tape_alphabet: ['a', 'X']"),
                       "debe incluir el blanco")

    def test_blanco_como_entrada_vacia(self):
        texto = BASE.replace("tape_alphabet: ['a', 'X', null]", "tape_alphabet:\n  - 'a'\n  - 'X'\n  -")
        maquina, _ = cargar_texto(texto)
        self.assertIn(BLANCO, maquina.alfabeto_cinta)

    def test_movimiento_invalido(self):
        self.error_con(BASE.replace("tape_displacement: R", "tape_displacement: D"), "L, R o S")

    def test_transicion_duplicada(self):
        repetida = BASE.split("delta:\n")[1].split("simulation_strings")[0]
        texto = BASE.replace("simulation_strings", repetida + "simulation_strings", 1)
        self.error_con(texto, "repite la combinación")

    def test_cadena_fuera_del_alfabeto(self):
        self.error_con(BASE.replace("  - 'aa'", "  - 'aXa'"), "fuera de alphabet")

    def test_varios_errores_juntos(self):
        texto = BASE.replace("initial: 'q0'", "initial: 'q7'").replace("tape_displacement: R", "tape_displacement: X")
        with self.assertRaises(ErrorConfiguracion) as ctx:
            cargar_texto(texto)
        self.assertEqual(len(ctx.exception.errores), 2)


if __name__ == "__main__":
    unittest.main()
