# 1. Estado

**La Fase 37A queda cerrada: 19 de 19 pruebas superadas.** La Fase 37B no se inició y no hay commit ni push. Todo el análisis usa el conjunto sintético de usuarias (N = 529). Los resultados describen ese conjunto y no permiten afirmar nada sobre mujeres reales.

# 2. Resultado principal

Las matrices se resumen sin que aparezca una estructura marcada: **solo el primer eje se separa con claridad.** Describe la actividad física, y es similar en PCA y FAMD. Los siguientes se parecen mucho entre sí y superan por poco la referencia de permutaciones. Esto aún no dice si habrá o no perfiles estables: eso se evalúa en la Fase 37B.

# 3. Cifras

| Escenario | k = 2 | k = 3 | k = 5 | k = 8 | k = 12 | k = 16 | k = 20 |
|---|---|---|---|---|---|---|---|
| P1 (PCA con IMC) | 13,9 % | 19,1 % | 28,3 % | 40,9 % | 55,8 % | 68,5 % | 79,7 % |
| P2 (PCA sin IMC) | 14,1 % | 19,4 % | 28,8 % | 41,5 % | 56,7 % | 69,6 % | 81,0 % |
| F1 (FAMD con IMC) | 10,8 % | 14,9 % | 22,6 % | 33,1 % | 45,7 % | 56,9 % | 66,9 % |
| F2 (FAMD sin IMC) | 11,0 % | 15,1 % | 22,9 % | 33,5 % | 46,2 % | 57,6 % | 67,7 % |

| Escenario | Rango | 50 % | 60 % | 70 % | 80 % | 90 % |
|---|---|---|---|---|---|---|
| P1 (PCA con IMC) | 33 | 11 | 14 | 17 | 21 | 25 |
| P2 (PCA sin IMC) | 32 | 11 | 13 | 17 | 20 | 24 |
| F1 (FAMD con IMC) | 39 | 14 | 18 | 22 | 26 | 32 |
| F2 (FAMD sin IMC) | 38 | 14 | 17 | 21 | 26 | 31 |

# 4. Hallazgos para tener presentes

- **El eje 2 depende mucho de una variable.** Sin `tiene_actividad_sexual` ni `distension_abdominal` (S-SOLAPE), el subespacio de k = 2 cambia bastante (similitud 0,604 en P1).
- **El IMC casi no está representado en los candidatos.** Aporta 0,4 % o menos en los cinco primeros ejes, y las versiones con y sin IMC casi coinciden.
- **La codificación importa.** S-RARA y, en menor medida, S-FAMD cambian la representación de FAMD.
- **Igualar bloques no es neutro.** S-BLOQUE y S-BLOQUE-SA concentran el primer eje en muy pocas variables.
- **Dos ordinales no muestran orden en FAMD.** Personas que cuida tiene una relación no lineal en su eje principal, y tabaco está mal representada.

# 5. Adiciones y decisiones propias

El encargo no pidió lo siguiente; lo incorporé y queda a tu criterio:

- **Análisis paralelo** (200 permutaciones): solo descriptivo; no selecciona ejes.
- **Pruebas adicionales:** identidad de contribuciones FAMD, sello del protocolo, sin clústeres, orden de niveles y control de mutaciones.
- **Umbral de revisión de 0,80:** orientativo.
- **Propuestas para 37B:** `n_init = 50`, remuestreo sin reemplazo, tramos de ARI, orden de decisión y referencia nula. Pueden cambiarse antes de ejecutar la Fase 37B.

# 6. Pruebas e integridad

Las 19 pruebas pasan, y el control introdujo 11 errores a propósito: se detectaron todos, en 14 comprobaciones. Detalle en `12_informe_pruebas.md` y `13_informe_integridad.md`. Las Fases 34, 35 y 36 no cambiaron.

# 7. Lo que no se hizo

No se formaron clústeres, no se ejecutó K-means ni el método aglomerativo, no se leyó el MRS ni la carpeta `datos/`, y no se modificaron la plataforma ni las fases anteriores.

# 8. Límites

- **Datos sintéticos.** Las relaciones entre variables provienen de la generación del conjunto. Una dimensión de este análisis no es un hallazgo sobre la población.
- **El signo de un eje es arbitrario.** Un valor alto o bajo no significa más o menos de algo sin mirar las cargas, y ningún eje mide severidad ni riesgo clínico.
- **El porcentaje no indica utilidad.** Un eje con varianza alta puede resumir bien una característica sin que eso sirva para formar perfiles.
- **Esta fase no prueba que existan grupos.** Una nube de puntos en dos ejes no demuestra ni descarta clústeres.
