# Fase 36B: aspectos pendientes para la Fase 37

Nada de esto se ejecutó. La Fase 37 no se inició.

## 1. Decidir antes de ver resultados (D-13)

- Rango de clústeres y número de componentes.
- Tamaño mínimo aceptable de un grupo.
- Medida de estabilidad.
- Qué cambio en una sensibilidad se considera relevante.
- Regla para elegir entre con y sin IMC, y entre PCA y FAMD.

## 2. Cómo usar las matrices

- **No aplicar otra estandarización.** Una segunda pasada llevaría el IMC de 0,5047 a 1 y cambiaría las indicadoras. El esquema lo advierte en `reescalar_prohibido`.
- **Valores propios.** `PCA` de scikit-learn informa `explained_variance_` con n − 1. Para obtener los valores propios de FAMD hay que multiplicar por (n − 1)/n, es decir, 528/529. La suma debe dar 38,5047 o 38.
- **Solucionador.** Usar `svd_solver='full'`, o fijar la semilla 42 si se usa otro.
- **Etiqueta de F1.** Es una FAMD con peso reducido en el IMC; F2 es la estándar. Conviene decirlo al informar.
- **R0.** La referencia sin reducción usa P1 y P2. No tiene archivo propio.
- **`prince`.** No debe usarse para proyectar participantes: al recibir una sola fila recalcula las proporciones y su resultado cambia (hasta 1,28 unidades en los datos de prueba).

## 3. Diagnósticos ya anunciados

- Proporción de IMC imputado por clúster, para detectar grupos creados por el valor repetido.
- Acuerdo (ARI) con y sin IMC, en las 529 y en las 267.
- Contribución del IMC a los ejes.
- Orden de las coordenadas de los niveles de las cinco ordinales categóricas en FAMD. Si no siguen el orden, se informa como relación no lineal.
- Grupos muy pequeños causados por colas largas (`frecuencia_fuerza`, `alcohol_frecuencia`, `dias_ejercicio_semana`).

## 4. Sensibilidades que quedan por ejecutar

| ID | Observación para la Fase 37 |
|---|---|
| S-ORD | Si cambia mucho los perfiles, el supuesto de equidistancia no puede sostenerse |
| S-FAMD, S-RARA | Son las que más cambian la dimensión: 37 a 58 columnas |
| S-TRA, S-CUI | Proyectan 22 y 21 participantes |
| S-EJE | Proyecta **75 participantes (14,2 %)**, más de lo previsto. El ajuste queda en 454 |
| S-BLOQUE | Amplifica el IMC por 2,70 en P1 y 3,09 en F1, aunque la mitad de esa columna es un valor imputado. Interpretarla con cuidado, o decidir antes si se excluye ese bloque |
| S-EDAD, S-SOLAPE | Se obtienen omitiendo columnas; no necesitan parámetros nuevos |

Las variantes de «punto de quiebre» de S-TRA y S-CUI no se prepararon: son opcionales.

## 5. Riesgos de interpretación

- **Estructura débil.** 424 de 435 pares de variables están bajo |0,2|. Puede no haber clústeres marcados, y esa posibilidad debe informarse sin forzar el resultado.
- **Alimentación.** Con 13 de 30 variables, puede orientar los perfiles en la ruta sin ponderar.
- **Datos sintéticos.** Todo se calcula sobre el conjunto simulado. Los parámetros congelados no son aplicables a usuarias reales sin recalibrar con una versión nueva.
- **Cuidadoras.** 99 de las 239 con sobrecarga observada no trabajan, y la pregunta menciona el trabajo.
- **Módulos.** Solo caracterizan. No deben influir en la formación de grupos.

## 6. Para fases posteriores

- **D-09 (Fase 40):** límite de respuestas ausentes para asignar un perfil.
- **D-15 (Fases 38 y 39):** agrupación de los ítems de los módulos en las reglas.
- **Fase 40:**
  - llevar el transformador a la plataforma, sin modificarla antes de esa fase;
  - revisar los límites de plausibilidad (`edad` 18-110, `imc` 10-80, `horas_sedentarismo` 0-24), que son un criterio técnico mío;
  - decidir si «Sí realiza» con frecuencia «Nunca» debe advertirse en el formulario;
  - definir qué hacer bajo los 36 años, donde habría extrapolación.
- **Aglomerativo:** no tiene `predict`. Hay que usar el centroide más cercano e informar cuánto concuerda con la asignación original.

## 7. Administración del repositorio

- No hay commit de las Fases 34 a 36. La carpeta `analisis/fase36/` ocupa unos 12 MB.
- `fase36_diseno/scripts/verificar_diseno.py` marcará ahora «existe carpeta de implementación». Es esperado: esa comprobación era válida antes de la Fase 36B.
- Para repetir la comparación externa de FAMD hay que instalar `prince` 0.23.1 y `narwhals` fuera del proyecto (`pip install --no-deps --target CARPETA`) y pasar `--referencia CARPETA`. Sin esa opción, las demás comprobaciones se ejecutan igual.
