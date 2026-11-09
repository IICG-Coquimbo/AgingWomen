# Resultado

Apriori, FP-Growth y una enumeración exhaustiva producen **exactamente los mismos 52.685 conjuntos frecuentes, con los mismos recuentos, y las mismas 12.201 reglas**.

- **Parámetros comunes:** soporte conjunto mínimo de 27 participantes, hasta 3 condiciones de antecedente y un consecuente.
- **Elección del algoritmo:** ninguno se eligió por las reglas que entrega. Las sensibilidades usan FP-Growth.
- **Sin reajuste:** los tres son deterministas, no usan semillas y no se reajustan.

| Algoritmo | Conjuntos frecuentes | Reglas | Segundos | Memoria máxima (MB) |
|---|---|---|---|---|
| apriori | 52.685 | 12.201 | 0,72 | 27,7 |
| fpgrowth | 52.685 | 12.201 | 4,37 | 23,7 |
| exhaustiva | 52.685 | 12.201 | 0,31 | 13,4 |


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
- **Implementación:** Apriori, FP-Growth y enumeración exhaustiva propios (scripts/algoritmos_38.py); mlxtend no instalado y no se instala.
- **Memoria:** cada etapa corrió bajo el vigilante (`integridad/registro_memoria.csv`), con un solo proceso de análisis.
