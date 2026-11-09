# Fase 37D: informe de integridad inicial

Verificación hecha antes de calcular cualquier análisis, justo después de sellar el protocolo.

- **Fecha:** 2026-11-05T16:47:10.
- **Protocolo:** sellado el 2026-11-05T16:44:19, huella `f7c8d125aa9181224360c226586eb990779d15776a5adb00a26ac5e54eb326b9`.
- **Git:** rama `datos-simulados`, HEAD 745d689. Sin cambios en `src/` (Django), sin cambios en datos versionados y sin cambios fuera de `analisis/`.
- **`__pycache__` en fases protegidas:** 0.

| Fase | Archivos | Comparados por huella | Sin verificar por nombre | Distintos |
|---|---|---|---|---|
| Fases 34-35 (cierre) | 1.130 | 1.126 | 4 | 0 |
| Fase 36 | 258 | 258 | 0 | 0 |
| Fase 37A | 175 | 175 | 0 | 0 |
| Fase 37B | 654 | 654 | 0 | 0 |
| Fase 37C | 1.131 | 1.131 | 0 | 0 |
| Complemento 37C | 188 | 188 | 0 | 0 |


Los 4 archivos sin verificar del manifiesto 34-35 corresponden al simulador: `bitacora_suciedad.csv`, `dataset_usuaria_sucio.csv`, `dataset_usuaria_verdad.csv` y `diabetes_diagnostico_verdad.csv`. No están versionados y este proceso no los abre. Las huellas de las entradas usadas están en `integridad/huellas_entradas_inicial.csv`.
