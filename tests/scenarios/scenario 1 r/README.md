# Escenario 1 — Refinamiento estructural

## Modelo biológico

- **Entrada:** `barnase_A.pdb`.
- **Proteína:** barnasa de *Bacillus amyloliquefaciens*.
- **Estructura fuente:** PDB 1A2P, cadena A.

`barnase_A.pdb` conserva únicamente los registros atómicos de la cadena A. El archivo original `1A2P.pdb` se mantiene en esta carpeta como fuente trazable y no debe cargarse al flujo, porque incluye tres copias cristalográficas (cadenas A, B y C).

## Configuración de la etapa GNNRefine

| Parámetro | Valor |
|---|---:|
| `input` | `barnase_A.pdb` |
| `n_decoy` | `1` |
| `n_proc` | `1` |
| `device_id` | `-1` |
| `save_qa` | `false` |
| `save_le_decoy` | `false` |
| `save_all_decoy` | `false` |
| `only_pred_dist` | `false` |
