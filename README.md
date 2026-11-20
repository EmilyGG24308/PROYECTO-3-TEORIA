# Proyecto 3 — Simulador de Máquinas de Turing

## Video
https://canva.link/3vc22x8nu2jaxna

## Instalación y uso

Requiere Python 3.10+ (probado con 3.14).

```bash
python -m pip install -r requirements.txt
python main.py ejemplos/reconocedora.yaml
python main.py ejemplos/alteradora.yaml --max-steps 10000
python -m unittest -v
```

- `--max-steps N`: máximo de transiciones por cadena (por defecto 10000).
- `--blanco S`: carácter para mostrar el blanco (por defecto `□`).

## Formato YAML

```yaml
q_states:
  q_list: ['q0', 'q1']
  initial: 'q0'
  final: 'q1'
alphabet: ['a']
tape_alphabet: ['a', 'X', null]
delta:
  - params: {initial_state: 'q0', mem_cache_value: null, tape_input: 'a'}
    output: {final_state: 'q1', mem_cache_value: 'a', tape_output: 'X', tape_displacement: R}
simulation_strings:
  - 'aaa'
```

- Estados y símbolos van como texto entre comillas; cada símbolo es un solo carácter.
- **Blanco**: `null` o un valor vacío. Por dentro es `None` y en consola se muestra `□`. `'null'` con comillas no es el blanco.
- **Memoria**: guarda un símbolo de `tape_alphabet` o el blanco, empieza en blanco en cada cadena. `null` no es comodín.
- Movimientos: `L`, `R`, `S`. La cinta es infinita hacia ambos lados.
- Un YAML inválido (campos faltantes, estados o símbolos no declarados, movimientos inválidos, transiciones duplicadas, cadenas fuera del alfabeto, etc.) se reporta como error de configuración y no se simula.

## Salida

Cada fila es una descripción instantánea: `paso | estado | mem | pos | cinta | siguiente`. La celda bajo el cabezal va entre `[ ]` y `siguiente` es la transición aplicada (nuevo estado, memoria, escribe, movimiento).

La simulación para con:
- **ACEPTADA**: llegó al estado final.
- **RECHAZADA**: no hay transición para (estado, memoria, símbolo).
- **LÍMITE DE PASOS ALCANZADO**: se llegó a `--max-steps`; no se considera rechazo.



## Máquinas de ejemplo

**Reconocedora** (`ejemplos/reconocedora.yaml`): L = { aⁿbⁿcⁿ | n ≥ 1 }. Cada ronda marca una `a`→`X`, una `b`→`Y` y una `c`→`Z`; al terminar revisa que solo queden `Y`, `Z` y blanco.

| Cadena | Resultado |
|---|---|
| `aaabbbccc` | aceptada |
| `aaaabbbbcccc` | aceptada |
| `aaabbbbccc` | rechazada |
| `aabbccabc` | rechazada |

**Alteradora** (`ejemplos/alteradora.yaml`): invierte una cadena binaria. Intercambia el primer y último símbolo pendientes usando la memoria (`*` = hueco, `x`/`y` = 0/1 ya colocados) y al final quita las marcas.

| Entrada | Salida |
|---|---|
| `00101` | `10100` |
| `110010` | `010011` |
| `1011001` | `1001101` |
| `00011` | `11000` |
