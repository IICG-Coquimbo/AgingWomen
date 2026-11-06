# Análisis complementario exploratorio de la Fase 35B

*Registrado el 02-11-2026, después de conocer los resultados de la ejecución oficial y antes de ejecutar este análisis.*

## 1. Carácter

Este análisis es **exploratorio y posterior a la ejecución original**. No sustituye el resultado oficial de la Fase 35B: 0 variables seleccionadas con 5.000 permutaciones y q < 0,05 (commit `745d689937a18c35b62fd25eccc401b169b20e11`, protocolo `analisis/protocolo_fase35b.md`).

El umbral q < 0,10 se eligió conociendo que, en la ejecución oficial, ninguna candidata alcanzaba q < 0,05 y cinco tenían q < 0,10. Por eso sus resultados no son confirmatorios.

## 2. Escenarios

Cada escenario calcula de nuevo la relevancia, las pruebas de pares que correspondan a sus relevantes y las dos variantes de FCBF. La redundancia no se deduce aplicando otro umbral a una tabla, porque la familia de pares depende de qué variables resulten relevantes.

| Escenario | Permutaciones | Umbral q | Función |
|---|---:|---:|---|
| E1 | 5.000 | 0,05 | Reproduce el resultado oficial; si no coincide, el análisis se detiene |
| E2 | 5.000 | 0,10 | Comparación |
| E3 | 50.000 | 0,05 | Comparación |
| E4 | 50.000 | 0,10 | Análisis complementario |

El umbral se aplica con comparación estricta y sin tolerancia, tanto en relevancia como en redundancia. La variante estándar no exige q en los pares, pero usa el umbral de su escenario en la relevancia.

## 3. Lo que no cambia

Semilla base 42 y el mismo mecanismo de generación (identificador de análisis 0); definición de SU; discretizaciones; valores faltantes; 30 candidatas; 4 controles, que pasan sin filtro y no se recalculan aquí; `prevision` pendiente; poblaciones de cada etapa (529 y 287); orden exacto y desempate alfabético; reglas de cobertura y de eliminación; tolerancia absoluta 1e-12 solo en los dos usos de la sección 12 del protocolo original.

No se buscan semillas. El programa no admite otra semilla, otras permutaciones ni otros umbrales por consola.

## 4. Separación

- Salidas solo en `analisis/complementario_35b_q10/`, con lista cerrada y sin sobrescribir.
- No se genera dataset, caché ni figuras, y no se modifica ningún archivo protegido.
- El umbral se cambia solo en memoria, durante el cálculo de cada escenario, y se restaura siempre.
- No se ejecutan remuestreos bootstrap ni sensibilidades.

## 5. Condiciones para ejecutar

La ejecución se detiene si ocurre cualquiera de estas situaciones:

1. Falla alguna prueba, de `test_entropia.py` o de `test_complementario_35b.py`.
2. HEAD no es el commit original, hay cambios en archivos versionados o difieren los hashes del respaldo.
3. E1 no reproduce los archivos oficiales.
4. Dos corridas de E4 no coinciden exactamente.
5. Cambia cualquier archivo vigilado: resultados originales, caché, archivos protegidos o código.

Este código no queda en un commit, por decisión de la usuaria. El registro guarda el commit original y el SHA-256 del programa, de este protocolo y de sus pruebas.

## 6. Cómo leer el resultado

- **Más permutaciones** mejoran la precisión con que se estima cada valor p. No hacen más permisiva la prueba.
- **Subir el umbral a 0,10** hace menos estricta la selección y aumenta el riesgo de incluir variables por azar: se tolera que, en promedio, hasta cerca de 1 de cada 10 variables declaradas relevantes sea un falso positivo.
