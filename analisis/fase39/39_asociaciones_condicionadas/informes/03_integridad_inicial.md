# Fase 39: auditoría de integridad inicial

Hecha justo después de sellar el protocolo y antes de cualquier búsqueda.

- **Fecha:** 2026-11-05T19:31:10.
- **Protocolo:** sellado el 2026-11-05T19:30:04, huella `18f15f821635f8c3d55a31f539d84d95ef8e5a32591e465073fb181a424c9042`.
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
| Fase 38 | 275 | 275 | 0 | 0 |


**Archivos sin verificar:** los 4 del manifiesto 34-35 corresponden al simulador. Este proceso no los abre; el gancho de auditoría lo impide.

**Huellas de las entradas:** están en `integridad/huellas_entradas_inicial.csv`. Las entradas son:
- los datos limpios, la Fase 35 y la Fase 36;
- las etiquetas A y B1 y la definición de B1;
- los núcleos de las Fases 37D y 38, que se importan sin escribir en sus carpetas;
- la matriz principal de la Fase 38;
- el modelo de la encuesta, de solo lectura;
- el conversor a Word.
