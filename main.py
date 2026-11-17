import argparse
import sys

from mt.lector import ErrorConfiguracion, cargar_archivo
from mt.maquina import BLANCO
from mt.simulador import ACEPTADA, LIMITE, RECHAZADA, simular

MAX_PASOS = 10000
BLANCO_VISIBLE = "□"


def ver(simbolo, blanco):
    return blanco if simbolo is BLANCO else simbolo


def texto_cinta(celdas, blanco):
    if not celdas:
        return "(vacía)"
    return "".join(ver(s, blanco) for s in celdas)


def texto_transicion(t, blanco):
    return (f"δ({t.estado}, {ver(t.memoria, blanco)}, {ver(t.lee, blanco)}) = "
            f"({t.nuevo_estado}, {ver(t.nueva_memoria, blanco)}, {ver(t.escribe, blanco)}, {t.movimiento})")


def mostrar_maquina(ruta, maquina, cadenas, blanco):
    simbolos = ", ".join(ver(s, blanco) for s in maquina.alfabeto_cinta)
    print("=" * 70)
    print(f"Máquina: {ruta}")
    print(f"Estados: {', '.join(maquina.estados)}")
    print(f"Estado inicial: {maquina.inicial}    Aceptación: {', '.join(maquina.finales)}")
    print(f"Alfabeto de entrada: {', '.join(maquina.alfabeto)}")
    print(f"Alfabeto de cinta: {simbolos}    (blanco = {blanco})")
    print(f"Transiciones ({len(maquina.transiciones)}), formato δ(estado, memoria, lee) = "
          "(nuevo estado, nueva memoria, escribe, movimiento):")
    for t in maquina.transiciones.values():
        print(f"  {texto_transicion(t, blanco)}")
    print(f"Cadenas a simular: {', '.join(repr(c) for c in cadenas)}")


def mostrar_resultado(resultado, blanco):
    print("=" * 70)
    cadena = resultado.cadena if resultado.cadena else "ε (vacía)"
    print(f"Cadena original: {cadena}    (longitud {len(resultado.cadena)})")
    print("Descripciones instantáneas (el cabezal está entre [ ]):")

    filas = []
    for d in resultado.descripciones:
        celdas = [f"[{ver(s, blanco)}]" if d.inicio + i == d.cabezal else ver(s, blanco)
                  for i, s in enumerate(d.celdas)]
        filas.append((d, " ".join(celdas)))
    ancho_estado = max(len("estado"), *(len(d.estado) for d, _ in filas))
    ancho_cinta = max(len("cinta"), *(len(c) for _, c in filas))

    print(f"  {'paso':>5} | {'estado':<{ancho_estado}} | mem | {'pos':>4} | {'cinta':<{ancho_cinta}} | siguiente")
    for d, cinta in filas:
        if d.paso < len(resultado.aplicadas):
            t = resultado.aplicadas[d.paso]
            siguiente = f"→ ({t.nuevo_estado}, {ver(t.nueva_memoria, blanco)}, {ver(t.escribe, blanco)}, {t.movimiento})"
        else:
            siguiente = "(parada)"
        print(f"  {d.paso:>5} | {d.estado:<{ancho_estado}} | {ver(d.memoria, blanco):^3} | "
              f"{d.cabezal:>4} | {cinta:<{ancho_cinta}} | {siguiente}")

    ultima = resultado.descripciones[-1]
    print(f"Cinta final: {texto_cinta(resultado.cinta_final, blanco)}")
    print(f"Transiciones ejecutadas: {resultado.pasos}")
    print(f"Resultado: {texto_motivo(resultado, ultima, blanco)}")


def texto_motivo(resultado, ultima, blanco):
    if resultado.motivo == ACEPTADA:
        return f"ACEPTADA, se llegó al estado de aceptación {ultima.estado}"
    if resultado.motivo == RECHAZADA:
        return (f"RECHAZADA, no hay transición para (estado {ultima.estado}, "
                f"memoria {ver(ultima.memoria, blanco)}, lee {ver(ultima.leido, blanco)})")
    return "LÍMITE DE PASOS ALCANZADO, la simulación se detuvo sin decidir (no se afirma rechazo)"


def mostrar_resumen(resultados, blanco):
    nombres = {ACEPTADA: "aceptada", RECHAZADA: "rechazada", LIMITE: "límite de pasos alcanzado"}
    print("=" * 70)
    print("Resumen:")
    for r in resultados:
        cadena = r.cadena if r.cadena else "ε"
        print(f"  {cadena:<15} {nombres[r.motivo]:<26} pasos: {r.pasos:<6} "
              f"cinta final: {texto_cinta(r.cinta_final, blanco)}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Simulador de Máquinas de Turing de una cinta")
    parser.add_argument("archivo", help="archivo YAML con la máquina y las cadenas")
    parser.add_argument("--max-steps", type=int, default=MAX_PASOS,
                        help=f"máximo de transiciones por cadena (por defecto {MAX_PASOS})")
    parser.add_argument("--blanco", default=BLANCO_VISIBLE,
                        help=f"símbolo para mostrar el blanco (por defecto {BLANCO_VISIBLE})")
    args = parser.parse_args(argv)

    if args.max_steps < 1:
        parser.error("--max-steps debe ser un entero mayor que 0")
    if len(args.blanco) != 1:
        parser.error("--blanco debe ser un solo carácter")

    try:
        maquina, cadenas = cargar_archivo(args.archivo)
    except ErrorConfiguracion as error:
        print(f"Error de configuración en '{args.archivo}':")
        for mensaje in error.errores:
            print(f"  - {mensaje}")
        return 1

    if args.blanco in maquina.alfabeto_cinta:
        print(f"El símbolo '{args.blanco}' ya está en el alfabeto de cinta; elegí otro con --blanco")
        return 1

    mostrar_maquina(args.archivo, maquina, cadenas, args.blanco)
    resultados = []
    for cadena in cadenas:
        resultado = simular(maquina, cadena, args.max_steps)
        mostrar_resultado(resultado, args.blanco)
        resultados.append(resultado)
    mostrar_resumen(resultados, args.blanco)
    return 0


if __name__ == "__main__":
    # para que □ y δ se vean bien aunque la salida se redirija a un archivo
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
