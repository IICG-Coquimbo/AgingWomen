# Complemento de la Fase 35B: informe de integridad

*05-11-2026. Programa: `scripts/integridad_b33.py`. Registros: `integridad/manifiesto_antes.json` (antes de ejecutar) e `integridad/integridad_final.json` (al terminar, 22:50).*

## 1. Qué se protegió

Se calculó la SHA-256 de 5.977 archivos:
- todo `analisis/` salvo esta carpeta y `__pycache__`, lo que incluye las Fases 34 a 39 y los archivos antiguos de estabilidad;
- todo `src/`, es decir, Django;
- `datos/`, salvo `datos/reales` y `dataset_usuaria_verdad.csv`, que no se abrieron.

## 2. Resultado

| Control | Antes | Después |
|---|---|---|
| Archivos comparados | 5.977 | 5.977 |
| Cambiados | — | **0** |
| Eliminados | — | **0** |
| Nuevos fuera de esta carpeta | — | **0** |
| HEAD de git | 745d689 | 745d689 |
| Rama | datos-simulados | datos-simulados |
| `git status` sin contar esta carpeta | 52 entradas | Igual (53 con la carpeta nueva, sin seguimiento) |
| `__pycache__` en la carpeta nueva | — | 0 (se ejecutó con `PYTHONDONTWRITEBYTECODE=1`) |
| Commit o push | — | Ninguno |

## 3. Archivos históricos verificados uno por uno

Todos tienen la misma huella que antes de ejecutar:
- `analisis/resultados/usuaria/estabilidad_remuestreos.csv`
- `analisis/resultados/usuaria/estabilidad_fcbf.csv`
- `analisis/resultados/usuaria/estabilidad_global.csv`
- `analisis/resultados/usuaria/log_seleccion_fase35b.txt`
- `analisis/figuras/seleccion_35b/estabilidad_seleccion.png`
- `analisis/reunion_2026-11-03/revision_33_variables/log_revision_33.txt`

## 4. Memoria y procesos

- Un solo proceso de análisis durante toda la corrida.
- Duración: 3.697 s (61,6 min), unos 7,4 s por remuestreo.
- Memoria libre mínima: 1.224 MB. El programa tenía un corte de seguridad en 400 MB, que no se activó.

## 5. Trazabilidad

`configuracion/configuracion.json` registra:
- los parámetros y las versiones de Python y de las bibliotecas;
- la SHA-256 de los datos de entrada;
- la SHA-256 del código reutilizado sin modificar y del código propio;
- la ejecución.

`protocolo/sello.json` guarda la huella del protocolo, escrito antes de ejecutar.

Cada remuestreo guarda la huella de sus índices, así que cualquiera de los 500 se puede reproducir por separado.
