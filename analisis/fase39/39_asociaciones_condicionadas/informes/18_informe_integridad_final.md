# Fase 39: informe de integridad final

- **Protocolo:** huella `18f15f821635f8c3d55a31f539d84d95ef8e5a32591e465073fb181a424c9042`, sellado el 2026-11-05T19:30:04, antes de cualquier búsqueda (prueba 20).
- **Lecturas fuera de la carpeta:** 3.766 archivos, casi todos para comparar huellas con los manifiestos. Registro: `integridad/archivos_leidos.csv`.
- **Simulador:** no se leyó ningún archivo del simulador.
- **Escrituras fuera de la carpeta:** 0.
- **Fases 37D y 38:** sus scripts se importaron con la escritura de bytecode desactivada. Sus carpetas no cambiaron y no tienen `__pycache__`.
- **Memoria:** un proceso de análisis más el vigilante, con un hilo por biblioteca. La memoria libre mínima registrada estuvo cerca de 0,73 GB, sobre el límite de 0,7 GB. Registro: `integridad/registro_memoria.csv`.
- **Manifiesto:** `integridad/manifiesto_final.csv`.

## Verificación final

- **Fecha:** 2026-11-05T19:48:52.
- **Archivos protegidos:** 3.917 comparados por huella, 0 distintos.
- **Entradas:** iguales al inicio: sí.
- **Git:** HEAD 745d689; cambios en `src/`: 0; cambios fuera de `analisis/`: 0; datos versionados modificados: 0.
- **`__pycache__` en fases protegidas:** 0.

## Restricciones

Se cumplieron todas:

- **Fases y datos:** sin cambios en las Fases 34 a 38 ni en los datos originales.
- **Simulador y agrupamientos:** sin la verdad del simulador y sin recalcular ni seleccionar agrupamientos (A y B1 se usaron con sus etiquetas históricas).
- **Recomendaciones e integración:** sin recomendaciones clínicas, sin modificar Django y sin iniciar la integración del tablero.
- **Git:** sin commit ni push.
