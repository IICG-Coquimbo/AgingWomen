# Conclusión

El problema de `tiene_actividad_sexual` **afecta a A y no a la asignación de las tres preguntas**. Pero las alternativas tienen su propia exposición: 82 participantes (15,5 %) tienen imputada alguna de las tres preguntas.

Todo el análisis usa el conjunto sintético de usuarias (N = 529). Sus asociaciones vienen de una simulación, por lo que los resultados no permiten afirmar nada sobre mujeres reales.

Comprobación exploratoria y posterior al cierre técnico de la Fase 37C. No cambia la conclusión B, no elige un modelo definitivo y no inicia la Fase 37D. La decisión queda en manos de la responsable del proyecto.

# `tiene_actividad_sexual`

- Observado en las 529: 251 «SI» y 248 «NO».
- 30 valores imputados como «NO», con la moda de la población de limpieza anterior (546 filas).
- La diferencia es de 3 respuestas. **No se afirma que la moda de 529 sea más correcta que la de 546.** No se modificó la limpieza ni la Fase 36.

| Efecto de usar la moda de 529 | Modelo A | B1 | B2 |
|---|---|---|---|
| Cambio en la partición | ARI 0,91 (S-IMPMODA) | Tabla: ARI 1,00 | No cambia |
| Quién cambia | 17 % de las imputadas; 2 % de las demás | 0 celdas | 0 participantes cambian de celda |


Así, A depende de esta decisión de limpieza y las alternativas no. B1 tampoco cambia, aun cuando su objetivo sea A: el cambio no alcanza a mover la mayoría de ninguna celda.

# Imputación en las tres preguntas

| Pregunta | Imputadas | Valor imputado | Deducidas |
|---|---|---|---|
| trabaja_actualmente | 22 | True | 1 |
| tiene_pareja | 28 | SI | 0 |
| dias_ejercicio_semana | 36 | 1 | 0 |


- **82 participantes** tienen alguna de las tres imputada, y 4 tienen dos o más. En los ejercicios imputados, el valor es el código 1, «0 días».
- Quienes tienen alguna imputada discrepan más de A: 18 % frente a 12 % en B1, y 17 % frente a 15 % en B2.
- Con imputadas excluidas del ajuste, B2 cambia poco (ARI de 0,93 a 0,95), pero eso no corrige la asignación de esas participantes.
- En A, la exposición es mayor: 77,5 % tiene imputada alguna de las 29 variables de entrada.

# Riesgos metodológicos que permanecen

- **Datos sintéticos.** Las relaciones, incluida la casi independencia entre bloques y la fuerza del trío, pueden venir de cómo se simuló. No hay validación independiente.
- **No es ciega.** El trío, el protocolo y la guía se redactaron conociendo la Fase 37C. La medida A−v es además posterior a ver resultados.
- **B2 no es independiente de A**, porque el trío se eligió por reproducir a A. B1 usa A como objetivo. Una concordancia alta no valida a ninguno.
- **Sin criterio externo.** Se excluyó a propósito. No se sabe cuál describe mejor algo que importe fuera de estas variables.
- **Grupos sin evidencia de ser naturales.** Sigue vigente la Fase 37C. Una regla simple tampoco lo demuestra.
- **Efecto de la escala (hipótesis no evaluada).** K-means con binarias en puntuación z podría favorecer cortes por pareja y trabajo. Coincide con la sensibilidad de A a la ponderación (S-BLOQUE 0,14) y con la de B2 (peso × 2: 0,33), pero no se probó.
- **Medida por variable.** No ve ventajas en combinaciones. Con 106 participantes de evaluación, cambios muy pequeños no se distinguen del ruido.
- **Submuestras solapadas.** Los percentiles describen variación, pero no son intervalos de confianza.
- **Sin umbrales.** No hay umbrales definitivos de incertidumbre en ninguna alternativa.
