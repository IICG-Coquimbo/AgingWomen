# Conclusión

B1 pide 3 respuestas y se explica en cuatro pasos. A pide 29 respuestas, transformador, PCA de 12 componentes y centroides. **A no muestra un beneficio claro que compense esa diferencia**, y con esta evidencia tampoco se puede decir que B sea «mejor»: es más simple y deja menos cosas que puedan fallar.

Todo el análisis usa el conjunto sintético de usuarias (N = 529). Sus asociaciones vienen de una simulación, por lo que los resultados no permiten afirmar nada sobre mujeres reales.

Comprobación exploratoria y posterior al cierre técnico de la Fase 37C. No cambia la conclusión B, no elige un modelo definitivo y no inicia la Fase 37D. La decisión queda en manos de la responsable del proyecto.

# Comparación

| Dimensión | Modelo A | B1 | B2 |
|---|---|---|---|
| Preguntas necesarias | 29 variables generales | 3 | 3 |
| Reducción dimensional | PCA, 12 componentes | Ninguna | Ninguna |
| Agrupamiento | K-means, k = 4 | Tabla de 20 celdas; se lee en 4 pasos | K-means, k = 4; equivale a una tabla |
| Estabilidad entre repeticiones | 0,77 | 1,00 | 0,96 |
| Interpretación | Cuatro segmentos multivariables provisionales, cortes de un continuo | Directa: tres respuestas | Directa, pero corte de ejercicio menos claro |
| Nuevas participantes | Transformador, PCA y centroides | Regla sencilla | Regla o centroides |
| Imputación expuesta | 78 % tiene alguna respuesta imputada | 16 % | 16 % |
| Incertidumbre | Margen mediano 0,15; 31 % bajo 0,10 | Pureza de celda: 9 % bajo 0,80 | Margen no comparable con el de A: datos discretos |
| Información adicional | Solo circular | Referencia de simplicidad | Referencia de simplicidad |


# Sensibilidades

**B1.** Se reconstruyó la tabla imitando cada variante sellada de A. Mide cómo cambiaría la regla si cambiara su objetivo. Una vez congelada, la regla no depende de A.

| Variante | ARI de A (Fase 37C) | ARI de B1 | Segmentos de B1 |
|---|---|---|---|
| S-ORD | 0,69 | 0,77 | 4 |
| S-SOLAPE | 0,36 | 0,55 | 3 |
| S-EDAD | 0,97 | 1,00 | 4 |
| S-BLOQUE | 0,14 | 0,33 | 4 |
| S-TRA | 0,96 | 1,00 | 4 |
| S-CUI | 0,95 | 1,00 | 4 |
| S-EJE | 0,88 | 1,00 | 4 |
| S-IMPMODA | 0,91 | 1,00 | 4 |


**B2.** Reajustada con cada variante propia.

| Variante | Grupo | ARI con B2 | Filas de ajuste |
|---|---|---|---|
| Días como ridit | Codificación | 0,69 | 529 |
| Días como normal | Codificación | 0,74 | 529 |
| Peso de ejercicio × 0.5 | Ponderación | 0,74 | 529 |
| Peso de ejercicio × 2 | Ponderación | 0,33 | 529 |
| Ajuste sin imputadas de trabaja_actualmente | Población | 0,95 | 507 |
| Ajuste sin imputadas de tiene_pareja | Población | 0,93 | 501 |
| Ajuste sin imputadas de dias_ejercicio_semana | Población | 0,95 | 493 |
| Ajuste sin imputadas en ninguna de las tres | Población | 0,93 | 447 |
| S-IMPMODA: no cambia las tres preguntas | Por construcción | No aplica: no le afecta por construcción | 529 |
| S-SOLAPE: quita variables que B2 no usa | Por construcción | No aplica: no le afecta por construcción | 529 |
| S-EDAD: quita variables que B2 no usa | Por construcción | No aplica: no le afecta por construcción | 529 |


B2 no resuelve la fragilidad frente a la codificación: 0,69 con ridit frente a 0,69 de A. Que S-SOLAPE no le afecte es por construcción y no se presenta como un logro.

# ¿Se justifican 12 componentes y K-means?

- **12 componentes:** con 8 y 16 las particiones son casi las mismas (ARI con A: 0,91 y 0,92), y tampoco añaden información: ΔR² entre -0,010 y -0,004 con 8, y entre -0,011 y -0,004 con 16. Los datos no distinguen entre ellas.
- **K-means:** es estable y permite asignar directamente, pero su partición depende del algoritmo (ARI con Ward 0,33). Solo se justifica si se decide conservar A, y no por haber mostrado información adicional.

# En lenguaje sencillo

El modelo complejo necesita diez veces más respuestas y varios pasos técnicos para llegar a grupos muy parecidos. Si los dos dan casi lo mismo, lo más simple resulta más fácil de explicar y de mantener.
