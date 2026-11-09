# Fase 37C: informe de integridad

- **Fases protegidas:** la prueba 1 compara 2.217 archivos de las Fases 36, 37A, 37B y del cierre de las Fases 34 y 35 con sus manifiestos: todos iguales.
- **Lecturas:** 93 archivos leídos, ninguno de `datos/`. El gancho de auditoría registra `integridad/archivos_leidos.csv`.
- **Escrituras fuera de la subfase:** 0. Registro: `integridad/escrituras_fuera.csv`.
- **Git:** HEAD sigue en 745d689. Sin commit y sin push. Sin cambios fuera de `analisis/` (Django y plataforma intactos).
- **Protocolo:** `protocolo/01_protocolo_37C.md` y `02_enmienda_referencia_nula.md` coinciden con sus sellos. Huella del protocolo: `62fd1d0b06e761129d26c4028526260bb1ea00565054eb8b378faa54ccb5e18f`.
- **Reproducción:** las etiquetas de la Fase 37B y las recalculadas son idénticas (50 configuraciones). `integridad/reproduccion_etiquetas.csv`.
- **Manifiesto final:** `integridad/manifiesto_final_37C.csv`, con la huella de todos los archivos de la subfase salvo él mismo.

## Avances recuperados

| Elemento | Cantidad | Estado |
|---|---|---|
| Réplicas 000 a 071 | 72 | Recuperadas tras validar sello, parámetros, dimensiones y silueta de control |
| Réplicas inválidas | 0 | Ninguna repetida |
| Réplicas 072 a 099 | 28 | Ejecutadas por primera vez |
| Contraste α = 0 | 20 | Por separado, en `lotes_alpha0/`, sin sobrescribir |
| Lotes de estabilidad | 360 | Válidos, sin repetir |


## Memoria

La primera corrida, con 10 procesos, fue detenida por el sistema por falta de memoria con 72 réplicas completas. Se reanudó con un máximo de 3 procesos, un hilo por biblioteca y `scripts/vigilar_memoria.py`. Desde entonces no hubo presión de memoria: el mínimo registrado fue 0,94 GB libres, sobre el límite de 0,7 GB. Registro: `integridad/registro_memoria.csv`.

## Restricciones

Sin MRS, Random Forest, Shannon ni GMM en la selección; sin verdad del simulador; sin reglas de asociación; sin caracterización clínica; sin iniciar la Fase 37D.
