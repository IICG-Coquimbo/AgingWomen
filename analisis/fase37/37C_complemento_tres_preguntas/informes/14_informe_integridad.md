# Complemento de la Fase 37C: informe de integridad

- **Archivos protegidos:** 3.348 archivos de las Fases 34-35, 36, 37A, 37B y 37C iguales a sus manifiestos.
- **Conclusión de la Fase 37C:** intacta (`B. Segmentación operativa condicionada`).
- **Protocolo:** sellado antes de calcular nada nuevo. Huella `6e00dec20c9e3336ec6a8160b3f5f1beba1165163bf2e0a1d293f9e5af392f9a`. La nota posterior tiene su propia huella: `a3716c1ef6bfc07796746ebedb8c26963cec19d25efa2e279369e849b5ef4363`.
- **Lecturas:** 27 archivos leídos fuera de esta carpeta, ninguno de `datos/` ni del MRS. Registro: `integridad/archivos_leidos.csv`.
- **Escrituras fuera de la carpeta:** 0.
- **Git:** HEAD en 745d689, sin commit y sin push, sin cambios fuera de `analisis/` (Django y plataforma intactos).
- **Reproducción:** etiquetas de A idénticas; 30 de 30 repeticiones iguales a los lotes E3 de la Fase 37C; ARI de 0,6768 idéntico.
- **Memoria:** máximo de 2 procesos, con vigilancia. Mínimo libre: 0,93 GB, sin detenciones. Registro: `integridad/registro_memoria.csv`.
- **Manifiesto final:** `integridad/manifiesto_final.csv`, con la huella de todos los archivos de esta carpeta salvo él mismo.

## Restricciones

Sin cambios en datos, limpieza, matrices ni fases selladas. Sin reabrir las 420 configuraciones. Sin verdad del simulador. Sin MRS como criterio. Sin reglas de asociación. Sin caracterización clínica. Sin cambios en la plataforma. Sin Fase 37D.
