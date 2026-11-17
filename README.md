# Proyecto 3 — Simulador de Máquinas de Turing

Simulador genérico de Máquinas de Turing (MT) de **una cinta** con memoria finita. La máquina y las cadenas a simular se describen en un archivo YAML; el programa muestra todas las descripciones instantáneas de cada cadena, la cinta final y si la cadena fue aceptada, rechazada o si se alcanzó el límite de pasos.

El simulador no tiene lógica de ningún lenguaje en particular: solo aplica las transiciones que vienen en el YAML.

## Requisitos

- Python 3.10 o superior (probado con Python 3.14).
- PyYAML 6 (`requirements.txt`).

## Instalación

```bash
python -m pip install -r requirements.txt
```

Opcionalmente dentro de un entorno virtual (`python -m venv .venv`).

## Ejecución

```bash
python main.py ejemplos/reconocedora.yaml
python main.py ejemplos/alteradora.yaml
python main.py ejemplos/alteradora.yaml --max-steps 10000
```

Opciones:

| Opción | Uso |
|---|---|
| `archivo` | YAML con la máquina y las cadenas (obligatorio). |
| `--max-steps N` | Máximo de transiciones por cadena. Por defecto `10000`. |
| `--blanco S` | Carácter con el que se *muestra* el blanco. Por defecto `□`. No puede estar en el alfabeto de cinta. |

Código de salida: `0` si se simuló todo, `1` si el archivo tiene errores de configuración, `2` si los argumentos son inválidos.

## Formato YAML

```yaml
q_states:
  q_list: ['q0', 'q1', 'q2']   # estados
  initial: 'q0'                 # estado inicial
  final: 'q2'                   # estado de aceptación (también se acepta una lista)

alphabet: ['a', 'b']            # alfabeto de entrada
tape_alphabet: ['a', 'b', 'X', null]   # alfabeto de cinta, debe incluir el blanco

delta:
  - params:
      initial_state: 'q0'       # estado actual
      mem_cache_value: null     # memoria actual
      tape_input: 'a'           # símbolo leído
    output:
      final_state: 'q1'         # nuevo estado
      mem_cache_value: 'a'      # nueva memoria
      tape_output: 'X'          # símbolo escrito
      tape_displacement: R      # L, R o S

simulation_strings:
  - 'aab'
  - 'abb'
```

Los cinco campos de primer nivel y todos los campos de cada transición son obligatorios. Se puede usar estilo de bloque o el estilo compacto `{...}` de YAML (los ejemplos usan el compacto).

Reglas:

- Estados y símbolos se escriben como texto. Los símbolos tienen exactamente un carácter, porque cada cadena de `simulation_strings` se separa carácter por carácter.
- Conviene poner comillas a todo (`'0'`, `'*'`, `'00101'`): sin comillas YAML convierte `00101` en el número `101` y `*` es sintaxis de alias. El simulador **no** corrige eso: lo reporta como error.
- Una entrada vacía en `simulation_strings` (`-` sin valor) o `''` es la cadena vacía.

### El blanco

- Internamente el blanco es `None`, que corresponde a `null` en YAML. Un valor vacío (`tape_output:`) o una entrada vacía en `tape_alphabet` (`-` sin valor) también es `null`.
- `null` sin comillas es el blanco; `'null'` entre comillas es texto y se rechaza por tener más de un carácter.
- En consola el blanco se muestra como `□` (configurable con `--blanco`). Es solo la representación visual.

### Memoria finita

La configuración de la máquina es `[estado, memoria]` más la cinta, como en `δ([q0, B], a) = ([q1, a], B, R)`.

- La memoria guarda **un símbolo del alfabeto de cinta o el blanco**. Ese es su dominio finito, así que no hace falta ningún campo extra en el YAML: cualquier `mem_cache_value` fuera de `tape_alphabet` es un error.
- La memoria empieza en blanco en cada cadena.
- `null` en `params.mem_cache_value` significa "la memoria está en blanco"; no es comodín. En `output.mem_cache_value` significa "dejar la memoria en blanco", no "conservar el valor".

## Procesamiento

1. Se lee el YAML con `yaml.safe_load` y se valida todo (ver abajo).
2. Se construye la tabla de transiciones con clave `(estado, memoria, símbolo leído)`.
3. Por cada cadena se crea una cinta nueva, con el cabezal en el primer símbolo (o sobre un blanco si la cadena es vacía), estado inicial y memoria en blanco.
4. En cada paso se busca la transición para `(estado, memoria, símbolo leído)`; si existe, se escribe, se mueve el cabezal y se actualizan estado y memoria.
5. La simulación para cuando:
   - el estado es de aceptación → **ACEPTADA** (se revisa antes de cada paso, incluso en el paso 0);
   - no existe transición → **RECHAZADA**;
   - se ejecutaron `--max-steps` transiciones → **LÍMITE DE PASOS ALCANZADO**. Esto no se reporta como rechazo, porque no prueba que la máquina no acepte.

La cinta es infinita en las dos direcciones: el cabezal puede ir a posiciones negativas.

### Validaciones

Antes de simular se revisa, y se reportan **todos** los errores juntos como "Error de configuración" (sin simular nada):

- archivo inexistente o YAML mal formado;
- campos faltantes, desconocidos o con tipo inválido;
- estado inicial o final que no esté en `q_list`, estados repetidos;
- estados de las transiciones que no estén declarados;
- símbolos leídos, escritos o de memoria fuera de `tape_alphabet`;
- `alphabet` no contenido en `tape_alphabet`, o blanco dentro de `alphabet`;
- blanco ausente en `tape_alphabet`;
- movimiento distinto de `L`, `R` o `S`;
- dos transiciones con la misma combinación `(estado, memoria, símbolo)`;
- cadenas con símbolos fuera de `alphabet`.

Un rechazo es un resultado de una máquina válida; un error de configuración significa que el archivo no describe una MT válida.

## Arquitectura

```
main.py              entrada por consola y presentación (único lugar que imprime)
mt/lector.py         lectura segura del YAML y validación -> (Maquina, cadenas)
mt/maquina.py        Maquina, Transicion y la constante BLANCO
mt/cinta.py          cinta infinita en ambas direcciones
mt/simulador.py      motor: simular(maquina, cadena, max_pasos) -> Resultado
ejemplos/            las dos máquinas de la demostración
tests/               pruebas con unittest
```

- `Maquina.transiciones` es un diccionario `{(estado, memoria, lee): Transicion}`; buscar una transición es una consulta al diccionario.
- `Cinta` guarda solo las celdas no blancas en un diccionario `{posición: símbolo}`, así crece hacia los dos lados sin desplazar nada. Escribir un blanco borra la celda.
- `simular` devuelve un `Resultado` con todas las descripciones instantáneas, las transiciones aplicadas, el motivo de parada y la cinta final. No imprime nada; `main.py` se encarga de mostrarlo.

## Cómo leer la salida

Primero se muestra la máquina (estados, alfabetos y todas sus transiciones). Luego, por cada cadena:

```
Cadena original: 00101    (longitud 5)
   paso | estado | mem |  pos | cinta         | siguiente
      0 | q0     |  □  |    0 | [0] 0 1 0 1   | → (q1, 0, *, R)
      1 | q1     |  0  |    1 | * [0] 1 0 1   | → (q1, 0, 0, R)
   ...
     31 | q6     |  □  |    5 | 1 0 1 0 0 [□] | (parada)
Cinta final: 10100
Transiciones ejecutadas: 31
Resultado: ACEPTADA, se llegó al estado de aceptación q6
```

Cada fila es una descripción instantánea:

- `paso`: transiciones aplicadas hasta ese momento (0 = configuración inicial).
- `estado` y `mem`: el par `[estado, memoria]`.
- `pos`: posición del cabezal (0 es el primer símbolo de la entrada; puede ser negativa).
- `cinta`: la parte no blanca de la cinta más la celda del cabezal; la celda leída va entre `[ ]`, aunque sea un blanco.
- `siguiente`: la transición que se aplica desde esa fila, como `(nuevo estado, nueva memoria, escribe, movimiento)`. La última fila dice `(parada)`.

Al final se muestra la cinta final (sin blancos de los extremos), la cantidad de transiciones, el resultado con su motivo y un resumen de todas las cadenas.

## Máquina reconocedora — `ejemplos/reconocedora.yaml`

Reconoce **L = { aⁿ bⁿ cⁿ | n ≥ 1 }**, que no es libre de contexto.

Estrategia: en cada ronda marca una `a` con `X`, la primera `b` libre con `Y` y la primera `c` libre con `Z`, y regresa a la última `X`. Cuando ya no hay `a` libres (se lee `Y` en `q0`), revisa que el resto sea solo `Y`, luego solo `Z` y luego blanco. Cualquier símbolo fuera de lugar deja a la máquina sin transición y la cadena se rechaza. No usa la memoria (siempre `null`).

| Estado | Función |
|---|---|
| q0 | Marca la siguiente `a` (`a/X,R → q1`) o, si lee `Y`, pasa a verificar (`→ q4`). |
| q1 | Salta `a` y `Y` a la derecha; en `b` escribe `Y` y pasa a `q2`. |
| q2 | Salta `b` y `Z`; en `c` escribe `Z` y regresa (`L → q3`). |
| q3 | Va a la izquierda sobre `a, b, Y, Z`; en `X` se mueve a la derecha y vuelve a `q0`. |
| q4 | Salta `Y`; en `Z` pasa a `q5`. |
| q5 | Salta `Z`; en blanco acepta (`→ q6`, `S`). |
| q6 | Aceptación. |

17 transiciones en total (todas en el YAML).

| Cadena | Resultado | Pasos | Cinta final |
|---|---|---|---|
| `aaabbbccc` | aceptada | 46 | `XXXYYYZZZ` |
| `aaaabbbbcccc` | aceptada | 77 | `XXXXYYYYZZZZ` |
| `aaabbbbccc` | rechazada (q4 lee `b`) | 48 | `XXXYYYbZZZ` |
| `aabbccabc` | rechazada (q5 lee `a`) | 22 | `XXYYZZabc` |

## Máquina alteradora — `ejemplos/alteradora.yaml`

Invierte una cadena binaria en la misma cinta y termina dejando **solo** la cadena invertida.

Símbolos auxiliares: `*` (hueco), `x` (un 0 ya colocado), `y` (un 1 ya colocado).

Estrategia: en cada ronda intercambia el primer y el último símbolo pendientes usando la memoria finita para cargar el símbolo que se está moviendo.

| Estado | Función |
|---|---|
| q0 | Guarda el primer símbolo pendiente en memoria y deja `*`. Si lee `x`/`y` ya no hay pendientes (`S → q4`). Con la cadena vacía acepta directo. |
| q1 | Va a la derecha sobre `0`/`1` hasta encontrar `x`, `y` o blanco; retrocede uno (`→ q2`). |
| q2 | En el último pendiente escribe la versión marcada del símbolo en memoria y guarda en memoria el que estaba ahí (`→ q3`). Si ese último pendiente es el mismo `*` (centro de una cadena impar), lo marca y pasa a limpiar. |
| q3 | Va a la izquierda hasta `*`, escribe ahí la versión marcada del símbolo en memoria, deja la memoria en blanco y vuelve a `q0`. |
| q4 | Va a la izquierda hasta el blanco antes de la cadena. |
| q5 | Recorre a la derecha cambiando `x → 0` y `y → 1`; en el blanco acepta. |
| q6 | Aceptación. |

33 transiciones en total. La memoria toma valores en `{□, 0, 1}`.

| Entrada | Cinta final | Pasos |
|---|---|---|
| `00101` | `10100` | 31 |
| `110010` | `010011` | 40 |
| `1011001` | `1001101` | 49 |
| `00011` | `11000` | 31 |

## Pruebas

```bash
python -m unittest -v
```

Se ejecutan desde la raíz del repositorio. Cubren:

- `tests/test_simulador.py`: movimiento a la izquierda del origen, movimiento `S`, lectura y escritura de blancos, memoria (guardar, consultar y que `null` no sea comodín), falta de transición, aceptación, reinicio independiente entre cadenas y límite de pasos.
- `tests/test_lector.py`: cada una de las validaciones de configuración.
- `tests/test_ejemplos.py`: las ocho cadenas de demostración, la reconocedora contra todas las cadenas sobre `{a, b, c}` de longitud ≤ 8 y la alteradora contra todas las cadenas binarias de longitud ≤ 10. Las pruebas usan conteos y `[::-1]` solo como referencia para comparar; las máquinas no los usan.
