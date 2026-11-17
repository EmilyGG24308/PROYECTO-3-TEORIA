from pathlib import Path

import yaml

from .maquina import BLANCO, MOVIMIENTOS, Maquina, Transicion

CAMPOS = ("q_states", "alphabet", "tape_alphabet", "delta", "simulation_strings")
CAMPOS_ESTADOS = ("q_list", "initial", "final")
CAMPOS_PARAMS = ("initial_state", "mem_cache_value", "tape_input")
CAMPOS_OUTPUT = ("final_state", "mem_cache_value", "tape_output", "tape_displacement")


class ErrorConfiguracion(Exception):
    def __init__(self, errores):
        self.errores = errores
        super().__init__("\n".join(errores))


def cargar_archivo(ruta):
    ruta = Path(ruta)
    if not ruta.is_file():
        raise ErrorConfiguracion([f"no existe el archivo '{ruta}'"])
    try:
        texto = ruta.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise ErrorConfiguracion([f"no se pudo leer '{ruta}': {error}"])
    return cargar_texto(texto)


def cargar_texto(texto):
    try:
        datos = yaml.safe_load(texto)
    except yaml.YAMLError as error:
        raise ErrorConfiguracion([f"YAML mal formado: {error}"])
    return construir(datos)


def ver(valor):
    if valor is BLANCO:
        return "null (blanco)"
    return repr(valor)


def construir(datos):
    """Valida los datos del YAML y devuelve (maquina, cadenas)."""
    if not isinstance(datos, dict):
        raise ErrorConfiguracion(["el archivo debe ser un mapa con los campos " + ", ".join(CAMPOS)])

    errores = []
    faltan = [campo for campo in CAMPOS if campo not in datos]
    if faltan:
        raise ErrorConfiguracion(["faltan campos obligatorios: " + ", ".join(faltan)])
    sobran = [str(campo) for campo in datos if campo not in CAMPOS]
    if sobran:
        errores.append("campos desconocidos: " + ", ".join(sobran))

    estados, inicial, finales = _leer_estados(datos["q_states"], errores)
    alfabeto = _leer_simbolos(datos["alphabet"], "alphabet", errores, acepta_blanco=False)
    alfabeto_cinta = _leer_simbolos(datos["tape_alphabet"], "tape_alphabet", errores, acepta_blanco=True)

    if alfabeto_cinta is not None:
        if BLANCO not in alfabeto_cinta:
            errores.append("tape_alphabet debe incluir el blanco (null o una entrada vacía)")
        if alfabeto is not None:
            fuera = [s for s in alfabeto if s not in alfabeto_cinta]
            if fuera:
                errores.append("alphabet no está contenido en tape_alphabet; faltan: "
                               + ", ".join(ver(s) for s in fuera))

    transiciones = _leer_delta(datos["delta"], estados, alfabeto_cinta, errores)
    cadenas = _leer_cadenas(datos["simulation_strings"], alfabeto, errores)

    if errores:
        raise ErrorConfiguracion(errores)
    maquina = Maquina(estados, inicial, finales, alfabeto, alfabeto_cinta, transiciones)
    return maquina, cadenas


def _leer_estados(q_states, errores):
    if not isinstance(q_states, dict):
        errores.append("q_states debe ser un mapa con q_list, initial y final")
        return None, None, None
    faltan = [campo for campo in CAMPOS_ESTADOS if campo not in q_states]
    if faltan:
        errores.append("faltan campos en q_states: " + ", ".join(faltan))
        return None, None, None

    lista = q_states["q_list"]
    if not isinstance(lista, list) or not lista:
        errores.append("q_states.q_list debe ser una lista no vacía de estados")
        return None, None, None
    estados = []
    for estado in lista:
        if not isinstance(estado, str) or not estado:
            errores.append(f"q_states.q_list: el estado {ver(estado)} debe ser texto (usá comillas si es un número)")
        elif estado in estados:
            errores.append(f"q_states.q_list: el estado {estado!r} está repetido")
        else:
            estados.append(estado)

    inicial = q_states["initial"]
    if not isinstance(inicial, str) or inicial not in estados:
        errores.append(f"q_states.initial: {ver(inicial)} no es un estado declarado en q_list")

    # se acepta un solo estado final o una lista de estados finales
    final = q_states["final"]
    finales = final if isinstance(final, list) else [final]
    if not finales:
        errores.append("q_states.final no puede estar vacío")
    for estado in finales:
        if not isinstance(estado, str) or estado not in estados:
            errores.append(f"q_states.final: {ver(estado)} no es un estado declarado en q_list")

    return estados, inicial, finales


def _leer_simbolos(lista, campo, errores, acepta_blanco):
    if not isinstance(lista, list):
        errores.append(f"{campo} debe ser una lista de símbolos")
        return None
    simbolos = []
    for simbolo in lista:
        if simbolo is BLANCO:
            if not acepta_blanco:
                errores.append(f"{campo}: el blanco no puede ser parte del alfabeto de entrada")
                continue
        elif not isinstance(simbolo, str):
            errores.append(f"{campo}: el símbolo {simbolo!r} debe ser texto (usá comillas en el YAML)")
            continue
        elif len(simbolo) != 1:
            errores.append(f"{campo}: el símbolo {simbolo!r} debe tener exactamente un carácter")
            continue
        if simbolo in simbolos:
            errores.append(f"{campo}: el símbolo {ver(simbolo)} está repetido")
        else:
            simbolos.append(simbolo)
    return simbolos


def _revisar_campos(mapa, esperados, donde, errores):
    if not isinstance(mapa, dict):
        errores.append(f"{donde} debe ser un mapa con " + ", ".join(esperados))
        return False
    faltan = [c for c in esperados if c not in mapa]
    sobran = [str(c) for c in mapa if c not in esperados]
    if faltan:
        errores.append(f"{donde}: faltan campos " + ", ".join(faltan))
    if sobran:
        errores.append(f"{donde}: campos desconocidos " + ", ".join(sobran))
    return not faltan and not sobran


def _leer_delta(delta, estados, alfabeto_cinta, errores):
    if not isinstance(delta, list):
        errores.append("delta debe ser una lista de transiciones")
        return {}

    transiciones = {}
    origen = {}
    for numero, item in enumerate(delta, start=1):
        donde = f"delta #{numero}"
        if not isinstance(item, dict):
            errores.append(f"{donde} debe tener params y output")
            continue
        bien = _revisar_campos(item, ("params", "output"), donde, errores)
        if not bien:
            continue
        params, output = item["params"], item["output"]
        bien_params = _revisar_campos(params, CAMPOS_PARAMS, donde + " params", errores)
        bien_output = _revisar_campos(output, CAMPOS_OUTPUT, donde + " output", errores)
        if not (bien_params and bien_output):
            continue

        antes = len(errores)
        _revisar_estado(params["initial_state"], estados, donde + " params.initial_state", errores)
        _revisar_estado(output["final_state"], estados, donde + " output.final_state", errores)
        _revisar_simbolo(params["mem_cache_value"], alfabeto_cinta, donde + " params.mem_cache_value", errores)
        _revisar_simbolo(output["mem_cache_value"], alfabeto_cinta, donde + " output.mem_cache_value", errores)
        _revisar_simbolo(params["tape_input"], alfabeto_cinta, donde + " params.tape_input", errores)
        _revisar_simbolo(output["tape_output"], alfabeto_cinta, donde + " output.tape_output", errores)
        if output["tape_displacement"] not in MOVIMIENTOS:
            errores.append(f"{donde} output.tape_displacement: {ver(output['tape_displacement'])} "
                           "no es un movimiento válido (L, R o S)")
        if len(errores) > antes:
            continue

        transicion = Transicion(
            params["initial_state"], params["mem_cache_value"], params["tape_input"],
            output["final_state"], output["mem_cache_value"], output["tape_output"],
            output["tape_displacement"],
        )
        # no se permiten dos transiciones para la misma combinación
        if transicion.clave in transiciones:
            estado, memoria, simbolo = transicion.clave
            errores.append(f"{donde} repite la combinación (estado {estado!r}, memoria {ver(memoria)}, "
                           f"símbolo {ver(simbolo)}) de delta #{origen[transicion.clave]}")
            continue
        transiciones[transicion.clave] = transicion
        origen[transicion.clave] = numero
    return transiciones


def _revisar_estado(estado, estados, donde, errores):
    if estados is not None and (not isinstance(estado, str) or estado not in estados):
        errores.append(f"{donde}: {ver(estado)} no es un estado declarado en q_list")


def _revisar_simbolo(simbolo, alfabeto_cinta, donde, errores):
    # la memoria y la cinta usan los mismos símbolos: el alfabeto de cinta (incluye el blanco)
    if simbolo is not BLANCO and not isinstance(simbolo, str):
        errores.append(f"{donde}: {simbolo!r} debe ser texto o null (usá comillas en el YAML)")
    elif alfabeto_cinta is not None and simbolo not in alfabeto_cinta:
        errores.append(f"{donde}: {ver(simbolo)} no pertenece a tape_alphabet")


def _leer_cadenas(lista, alfabeto, errores):
    if not isinstance(lista, list):
        errores.append("simulation_strings debe ser una lista de cadenas")
        return []
    cadenas = []
    for numero, cadena in enumerate(lista, start=1):
        # una entrada vacía en la lista es la cadena vacía
        if cadena is None:
            cadena = ""
        if not isinstance(cadena, str):
            errores.append(f"simulation_strings #{numero}: {cadena!r} debe ser texto "
                           "(usá comillas, por ejemplo '00101', para no perder ceros)")
            continue
        if alfabeto is not None:
            fuera = sorted({s for s in cadena if s not in alfabeto})
            if fuera:
                errores.append(f"simulation_strings #{numero}: '{cadena}' tiene símbolos fuera de alphabet: "
                               + ", ".join(repr(s) for s in fuera))
                continue
        cadenas.append(cadena)
    return cadenas
