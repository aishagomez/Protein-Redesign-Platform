# Escenario 2 — Refinamiento y docking proteína–proteína

## Modelo biológico

| Rol | Archivo de entrada | Estructura fuente |
|---|---|---|
| Receptor | `barnase_A.pdb` | PDB 1A2P, cadena A |
| Ligando | `barstar_A.pdb` | PDB 1A19, cadena A |

Barnasa y barstar son una pareja enzima–inhibidor. Los archivos preparados contienen una única cadena por proteína; los PDB originales se conservan para trazabilidad. El complejo PDB 1BRS se usa solamente como referencia biológica para interpretar el resultado, no como entrada de docking.

## Configuración

### Refinamiento (GNNRefine)

| Parámetro | Valor |
|---|---:|
| `input` | `barnase_A.pdb` (primera ejecución) y `barstar_A.pdb` (segunda ejecución) |
| `n_decoy` | `1` |
| `n_proc` | `1` |
| `device_id` | `-1` |
| `save_qa` | `false` |

Las dos proteínas se refinan independientemente con GNNRefine. El docking recibe las salidas refinadas de barnasa como receptor y de barstar como ligando.

### Docking (GRAMM)

| Parámetro | Valor |
|---|---:|
| `receptor` | salida refinada de `barnase_A.pdb` |
| `ligand` | salida refinada de `barstar_A.pdb` |
| `receptor_id` | `barnase` |
| `ligand_id` | `barstar` |
| `mmode` | `docking` |
| `eta` | `3.5` |
| `ro` | `9` |
| `ai` | `10` |
| `maxm` | `30000` |
| `mtch_l` | `20000` |
| `rclusl` | `10` |
| `maxmch` | `100` |
| `sejo` | `joint` |
