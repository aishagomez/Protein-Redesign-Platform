# Escenario 3 — Flujo completo: refinamiento, docking y optimización de interacción

## Modelo biológico y archivos de entrada

| Rol | Archivo | Fuente |
|---|---|---|
| Receptor | `barnase_A.pdb` | PDB 1A2P, cadena A |
| Ligando | `barstar_A.pdb` | PDB 1A19, cadena A |
| Datos auxiliares de ProteinEA | `protein_ea_inputs/` | Preparados para el complejo barnasa–barstar |

Los PDB preparados contienen una sola cadena. Tras el docking, el complejo publicado por GRAMM debe tener cadenas A (barnasa) y B (barstar). ProteinEA debe recibir ese complejo desde la etapa anterior; por ello, el directorio `protein_ea_inputs` **no debe incluir un PDB**.

## Parámetros

### Refinamiento (GNNRefine)

| Parámetro | Valor |
|---|---:|
| `input` | `barnase_A.pdb` (primera ejecución) y `barstar_A.pdb` (segunda ejecución) |
| `n_decoy` | `1` |
| `n_proc` | `1` |
| `device_id` | `-1` |
| `save_qa` | `false` |

Se ejecutan dos etapas de GNNRefine independientes, una por cada proteína. Sus salidas alimentan el docking.

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

### Optimización de interacción (ProteinEA)

| Parámetro | Valor |
|---|---:|
| `scenario_path` | `protein_ea_inputs/` |
| `algorithm` | `sea` |
| `partners` | `A_B` |
| `ligand_chain` | `B` |
| `gen` | `1` |
| `popsize` | `1` |
| `mutp` | `1` |
| `fitness_idxs` | `2,3` |
| `fitness_weights` | `-1,1` |
| `checkpoint` | `false` |
| `checks` | `2` |
| `mobj` | `false` |
| `randomseed` | `15` |
| `face1_file_name` | `faceA.txt` |
| `face2_file_name` | `faceB.txt` |
| `msa_matrix` | `MSA_matrix.tsv` |
