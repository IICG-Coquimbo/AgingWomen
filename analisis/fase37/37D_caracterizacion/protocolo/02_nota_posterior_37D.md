# Nota posterior al sellado del protocolo de la Fase 37D

Esta nota se redactó después de calcular los resultados. No cambia ninguna familia, prueba, umbral ni conclusión del protocolo sellado (`01_protocolo_37D.md`). Registra cuatro puntos para que nada quede implícito. Todo lo que aparece aquí se rotula en los informes como «posterior al sellado».

## 1. Celda deducida tratada como no observada (precisión)

El protocolo pedía tratar como faltantes, en S-OBS, las celdas imputadas y las de pregunta madre imputada. El código también trata así la única celda **deducida** de las 29 variables: `trabaja_actualmente` de la participante 462. Por eso S-SIN-IMP3 tiene 446 participantes y no 447. Es la opción más conservadora y afecta a una sola persona.

## 2. η² ajustado en la tabla de varianza dentro de los segmentos (adición)

Con 20 celdas, η² crece aunque no haya diferencias reales: su valor esperado sin asociación ronda (k − 1)/(n − 1) = 0,036. Por eso la tabla `varianza_dentro_segmentos.csv` agrega η² ajustado, 1 − (1 − η²)(n − 1)/(n − k), para poder comparar 4 grupos con 20 celdas. El η² sin ajustar se conserva.

## 3. Detalle por grupo de la asociación dentro de los segmentos (adición tras ver resultados)

Tras ver que trabajo, pareja y actividad sexual tenían, dentro de los grupos de A, asociaciones con el MRS más fuertes que sin segmentar, se guardó el detalle por grupo con el tamaño del nivel minoritario (`asociacion_dentro_por_grupo.csv`). El detalle muestra que esas cifras dependen de grupos con muy pocas participantes en un nivel. Por ejemplo, en el Grupo 3 de A solo 8 participantes no trabajan. Es una explicación descriptiva y no se usa para elegir nada.

## 4. Archivos del simulador en un manifiesto protegido

El manifiesto de cierre de las Fases 34-35 incluye cuatro archivos cuyo nombre corresponde al simulador:

- `bitacora_suciedad.csv`
- `dataset_usuaria_sucio.csv`
- `dataset_usuaria_verdad.csv`
- `diabetes_diagnostico_verdad.csv`

Para no abrirlos, este proceso no calcula su huella: los cuenta como «sin verificar por nombre». Los otros 3.532 archivos protegidos sí se compararon.
