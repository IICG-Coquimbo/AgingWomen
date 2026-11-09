# Fase 38: auditoría de integridad inicial

Hecha justo después de sellar el protocolo y antes de calcular ninguna regla.

- **Fecha:** 2026-11-05T17:52:33.
- **Protocolo:** sellado el 2026-11-05T17:52:08, huella `9f9614115801805f9cde6c1586a8d7571ee44116c18ac7638025a645ee7f5a82`.
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
| Fase 37D | 110 | 110 | 0 | 0 |


**Archivos sin verificar:** los 4 del manifiesto 34-35 corresponden al simulador (`bitacora_suciedad.csv`, `dataset_usuaria_sucio.csv`, `dataset_usuaria_verdad.csv` y `diabetes_diagnostico_verdad.csv`). Este proceso no los abre.

**Huellas de las entradas:** están en `integridad/huellas_entradas_inicial.csv`. Las entradas son:
- los datos limpios;
- la Fase 35;
- la procedencia, los identificadores y el esquema de la Fase 36;
- el núcleo de la 37D, que se importa sin escribir en su carpeta;
- la definición de la encuesta, de solo lectura;
- el conversor a Word de la 37C.
