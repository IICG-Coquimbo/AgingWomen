# Alcance

Esta nota prepara la Fase 37D. No la inicia, no usa el MRS y no caracteriza grupos. Lo que aquí se propone es provisional. La decisión final queda en manos de la responsable del proyecto.

Todo el análisis usa el conjunto sintético de usuarias (N = 529). Sus asociaciones vienen de una simulación, por lo que los resultados no permiten afirmar nada sobre mujeres reales.

# Punto de decisión previo

Antes de la Fase 37D, la responsable debe elegir entre:

1. Continuar con la segmentación operativa `P2_c12_km_k4`.
2. Usar la alternativa simple de tres preguntas (`trabaja_actualmente + tiene_pareja + dias_ejercicio_semana`).
3. No segmentar y tratar las variables como continuas.

También queda por resolver la imputación de `tiene_actividad_sexual`.

# Riesgos que la Fase 37D debe controlar

- **Circularidad.** `tiene_actividad_sexual` y `distension_abdominal` entran en la partición y se relacionan con síntomas. La asociación entre grupos y MRS puede estar inflada. Conviene repetir la comparación con la partición de S-SOLAPE.
- **Doble uso de datos.** Los grupos se crearon con estas 529 participantes. Las diferencias entre grupos en las variables usadas para crearlos son esperables y no constituyen una validación.
- **Verdad del simulador.** Una asociación con el MRS en datos sintéticos refleja lo que la simulación programó.
- **Nombres.** Evitar nombres que sugieran tipos clínicos. Un continuo no admite «perfiles» en sentido estricto.
- **Fronteras.** Informar los resultados también sin las participantes de margen bajo, para ver si dependen de ellas. Conviene presentar la comparación por cada corte.

# Comparaciones recomendadas

- Frente a la regla de tres preguntas: si esta explica lo mismo, es preferible por simple.
- Frente a variables continuas sin agrupar.
- Frente a `P2_c08_km_k4`, `P2_c16_km_k4` y la partición con ridit, para ver si lo encontrado depende de la configuración.

# Lo disponible

| Elemento | Ubicación |
|---|---|
| Etiquetas provisionales | `seleccion/artefactos_provisionales/P2_c12_km_k4/etiquetas.csv` |
| Centroides y procedencia | `seleccion/artefactos_provisionales/P2_c12_km_k4/modelo_segmentacion.json` |
| Alternativa | `seleccion/artefactos_provisionales/P2_c08_km_k4/` |
| Decisión | `seleccion/decision_final_37C.json` |
| Variables que más separan | `seleccion/variables_que_mas_separan.csv` |
| Grilla de incertidumbre | `asignacion/grilla_incertidumbre.csv` |


La Fase 37D no se inició. Requiere una instrucción expresa.
