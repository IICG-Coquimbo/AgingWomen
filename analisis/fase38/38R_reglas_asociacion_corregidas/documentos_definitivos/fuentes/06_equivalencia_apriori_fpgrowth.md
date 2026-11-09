> **Versión correctiva (Fase 38R).** Corrige la Fase 38 histórica retirando de la matriz principal `prevision` y `usa_medicamentos_diabetes`, que las decisiones de las Fases 35 y 36 excluían del modelado. Ninguna de las dos es predictora autorizada y solo se nombran para documentar ese motivo. Todas las cifras de este documento provienen de los resultados corregidos; las cifras de la versión anterior no están vigentes. Las sensibilidades se identifican siempre como tales y no sustituyen al análisis principal.

# Resultado

Apriori, FP-Growth y una enumeración exhaustiva producen **exactamente los mismos 42.937 conjuntos frecuentes, con los mismos recuentos, y las mismas 9.761 reglas**.

- **Parámetros comunes:** soporte conjunto mínimo de 27 participantes, hasta 3 condiciones de antecedente y un consecuente.
- **Elección del algoritmo:** ninguno se eligió por las reglas que entrega. Las sensibilidades usan FP-Growth.
- **Sin reajuste:** los tres son deterministas, no usan semillas y no se reajustan.

| Algoritmo | Conjuntos frecuentes | Reglas | Segundos | Memoria máxima (MB) |
|---|---|---|---|---|
| apriori | 42.937 | 9.761 | 0,61 | 22,2 |
| fpgrowth | 42.937 | 9.761 | 3,21 | 19,1 |
| exhaustiva | 42.937 | 9.761 | 0,23 | 10,1 |


| Comparación | Mismos conjuntos y recuentos | Diferencias | Mismas reglas |
|---|---|---|---|
| apriori frente a fpgrowth | sí | 0 | sí |
| apriori frente a exhaustiva | sí | 0 | sí |
| fpgrowth frente a exhaustiva | sí | 0 | sí |


# Evaluador matricial

La referencia nula y la estabilidad usan un evaluador matricial que recuenta los mismos antecedentes frecuentes.

- **Por qué basta recontar:** las agrupaciones no dependen del consecuente, así que permutar la severidad o tomar una submuestra no cambia qué antecedentes existen.
- **Verificación:** la prueba 11 confirma que el evaluador da los mismos recuentos que FP-Growth ejecutado de nuevo en dos permutaciones y en una submuestra.

# Entorno

- **Versiones:** Python 3.12.5, NumPy 2.2.4, pandas 2.2.3 y SciPy 1.15.2.
- **Recursos:** un hilo por biblioteca numérica y semilla 42 para permutaciones y submuestras.
- **Implementación:** Apriori, FP-Growth y enumeración exhaustiva históricos (fase38/.../scripts/algoritmos_38.py), importados sin modificar.
- **Memoria:** cada etapa corrió bajo el vigilante (`integridad/registro_memoria.csv`), con un solo proceso de análisis.
