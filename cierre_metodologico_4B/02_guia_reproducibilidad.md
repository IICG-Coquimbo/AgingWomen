# Etapa 4B · Documento 02 · Guía de reproducibilidad

**Fecha:** 2026-11-09 · **Rama:** `datos-simulados` · **HEAD:** `573d3a31100c03519d47e220f4a065df3e9caf9a`
**Alcance:** guía documental. Durante su elaboración no se ejecutaron scripts, no se instalaron paquetes ni se recalcularon huellas. Las huellas proceden de registros existentes.

Abreviaturas de rutas:

| Abreviatura | Ruta |
|---|---|
| `REV33/` | `analisis/reunion_2026-11-03/revision_33_variables/` |
| `RF33/` | `analisis/random_forest_revision_35b_33_variables/` |
| `BOOT/` | `analisis/complemento_bootstrap_33/` |
| `F36/` | `analisis/fase36/` |
| `F37/` | `analisis/fase37/` |
| `38R/` | `analisis/fase38/38R_reglas_asociacion_corregidas/` |
| `39R/` | `analisis/fase39/39R_asociaciones_condicionadas_corregidas/` |

---

## A. Fuente definitiva de variables

**Archivo definitivo:** `analisis/reunion_2026-11-03/revision_33_variables/fase35a/predictores_elegibles_33.csv`

| Dato | Valor |
|---|---|
| Filas | 33 variables: 30 generales, 2 laborales (n = 287) y 1 de cuidadoras (n = 239) |
| SHA-256 registrado | `9a534d717c24f975ac7c02a87466189d48a48036baa47c5cbaca3ed75f187866` |
| Registro de la huella | `38R/preparacion/verificacion_preparacion.json`, clave `elegibles_33` |

### Universo por capa

| Capa | Variables | Uso |
|---|---|---|
| Elegibles | 33 | 35B revisada, bootstrap |
| Generales | 30 | P1 y F1 (Fase 36) |
| Generales sin `imc` | 29 | P2 y F2, 38R, 39R |
| Módulos | 2 laborales y 1 de cuidadoras | Aparte, solo en sus subpoblaciones |

`sobrecarga_fisica_emocional` entra al universo de 33. Se incorpora desde `datos/limpio_usuaria/dataset_usuaria_limpio.csv`.

### Advertencia: fuentes que no deben usarse como lista de variables

Estas fuentes reintroducen variables excluidas o corresponden a etapas anteriores. **Se conservan sin modificar**, porque son registros históricos.

| Fuente | Problema | Uso correcto |
|---|---|---|
| `analisis/preprocesamiento/configuracion.py` (`:29,93,99,165,200`) | Incluye `usa_medicamentos_diabetes` y `prevision` | Historia del preprocesamiento |
| `datos/analitico/dataset_fase35.csv` | Incluye diabetes | Usar solo aplicando las 33 candidatas |
| `datos/analitico/dataset_fase35b.csv` | Incluye diabetes; histórico | No usar |
| `datos/analitico/dataset_fase35_33_variables.csv` (529 × 39) | Trae `prevision` y `doble_carga`; no trae `sobrecarga_fisica_emocional` | Entrada documentada del Random Forest, con sus exclusiones |
| `analisis/fase38/38_reglas_asociacion_generales/scripts/nucleo_38.py` (`PRINCIPAL:50-56`) | Lista histórica de la Fase 38 | No usar la lista. 38R la reemplaza |
| `nucleo_39` y referencias `N38.*` | Heredan la lista histórica | Mismo criterio; 39R aplica sus barreras |
| Nota 16 de la 37D | Propone diabetes como opción | No forma parte del universo |

**Regla práctica.** La lista de variables se toma del CSV definitivo y se aplica a los datos. Nunca se deduce de los encabezados de un conjunto ni de `configuracion.py`.

---

## B. Tabla de dependencias

| Fase | Datos de origen | Universo | N | Configuración | Resultados de referencia | Depende de |
|---|---|---|---|---|---|---|
| **35B revisada** | `dataset_fase35_33_variables.csv` y limpio | 33 | 529 / 287 / 239 | `REV33/protocolo_revision_33.md`, `analisis/reunion_2026-11-03/protocolo_revision_35b.md`, `analisis/protocolo_fase35b.md` | `REV33/permutaciones_50000/relevancia_33.csv`, `decisiones_fcbf.csv` | 34, 35A, cierre 34-35 |
| **Random Forest** | `dataset_fase35_33_variables.csv` | Modelos A 3, B 30, C0 29, C1 31, D0 30, D1 31 | 529 | `RF33/protocolo_random_forest_33.md`, `rf_33_variables.py` | `RF33/resultados/rendimiento_modelos.csv`, `registro_ejecucion.txt` | 35B revisada. No selecciona variables |
| **Bootstrap** | `datos/analitico/dataset_fase35.csv`, con 33 candidatas | 33 | 529 / 287 / 239 | `BOOT/protocolo/01_revision_y_configuracion.md`, `BOOT/configuracion/{configuracion,semillas_y_parametros}.json` | `BOOT/resultados/resultado_global.csv`, `BOOT/remuestreos/ejecucion.json` | 35B revisada |
| **36** | Limpio y CSV de 33 | 30 / 29 + módulos | 529 | `F36/configuracion_fase36.py`, `F36/construir_fase36.py`, `F36/informes/fuentes/01_protocolo_fase36A_ajustado.md` | `F36/matrices/`, `F36/modulos/`, `F36/sensibilidades/`, `F36/integridad/manifiesto_final_36B.csv` | Cierre 34-35. Commit esperado `745d689` |
| **37A** | `F36/matrices/` | P1, P2, F1, F2 | 529 | `F37/37A_reduccion/protocolo/01_protocolo_D13.md` | `F37/37A_reduccion/tablas/valores_propios.csv` | 36 |
| **37B** | Salidas 37A | Mismas | 529 | `F37/37B_clustering/` (`nucleo_37b.py`) | `resultados/configuraciones.csv`, `estabilidad/resumen_estabilidad.csv` | 37A |
| **37C** | Salidas 37B | P2 | 529 | Protocolo y enmienda 1 en `F37/37C_comparacion_seleccion/protocolo/` | `seleccion/decision_final_37C.json`, `seleccion/artefactos_provisionales/P2_c12_km_k4/etiquetas.csv` | 37B |
| **Complemento 37C** | Datos 36 y 37C | 3 preguntas | 529 | `F37/37C_complemento_tres_preguntas/definiciones/definicion_B1_B2.json` | `asignaciones/etiquetas_alternativas.csv` (`B1_doble_uso`) | 37C |
| **37D** | Etiquetas y limpio | Descriptivas | 529 | `F37/37D_caracterizacion/protocolo/01_protocolo_37D.md` | `resultados/resumen_37D.json`, `resultados/individual/F1_total.csv` | 37C y complemento |
| **38R** | 36, 37C, complemento, `dataset_fase35.csv`, limpio | 29, 90 ítems | 529 (281/248) | `38R/protocolo/01_protocolo_38R.md`, `38R/scripts/nucleo_38r.py` | `38R/reglas/{reglas_principal.csv,resumen_principal.json}`, `38R/informes/informe_comparativo_38R.md` | Fase 38 histórica (`algoritmos_38`, `evaluacion_38`, `nucleo_38`) y sus 34 archivos leídos |
| **39R** | Mismos que 38R | 29, 90 ítems, 9 estratos | 529 | `39R/protocolo/01_protocolo_39R.md`, `02_modificaciones_posteriores.md`, `39R/scripts/nucleo_39r.py` | `39R/reglas/reglas_todos_estratos.csv`, `39R/comparacion/*`, `39R/resultados/conclusion_39R.json`, `39R/informes/informe_comparativo_39R.md` | 38R y Fases 38 y 39 históricas (`barreras_38r`, `nucleo_38r`, `nucleo_39`, `busqueda_39`) |

**Las fases correctivas no son autónomas.** `39R/scripts/nucleo_39r.py` añade a `sys.path` las carpetas de scripts de la 38, la 38R y la 39. Conservar 39R sin esas carpetas impide ejecutarla.

---

## C. Entorno de ejecución

`requirements.txt` solo cubre la aplicación web. **El entorno de análisis no está fijado en ningún archivo único.** Las versiones siguientes salen de registros existentes.

| Fase | Python | NumPy | pandas | SciPy | scikit-learn | Registro |
|---|---|---|---|---|---|---|
| 35B revisada | 3.12.5 | 2.2.4 | 2.2.3 | no verificada | no verificada | `REV33/log_revision_33.txt:6` |
| Random Forest | 3.12.5 | 2.2.4 | 2.2.3 | no verificada | 1.6.1 | `RF33/registro_ejecucion.txt:5` |
| Bootstrap | 3.12.5 | 2.2.4 | 2.2.3 | 1.15.2 | no verificada | `BOOT/configuracion/configuracion.json:70-74` |
| 36 | 3.12.5 | 2.2.4 | 2.2.3 | 1.15.2 | 1.6.1 | `F36/artefactos/P2/entorno.json` |
| 37A | 3.12.5 | 2.2.4 | 2.2.3 | 1.15.2 | 1.6.1 | `F37/37A_reduccion/artefactos/entorno.json` |
| 37B | 3.12.5 | 2.2.4 | 2.2.3 | 1.15.2 | 1.6.1 | `F37/37B_clustering/resultados/entorno.json` |
| 37C | no verificada | no verificada | no verificada | no verificada | no verificada | Sin registro localizado |
| Complemento 37C | no verificada | no verificada | no verificada | no verificada | no verificada | Sin registro localizado |
| 37D | no verificada | no verificada | no verificada | no verificada | no verificada | Sin registro localizado |
| 38R | 3.12.5 | 2.2.4 | 2.2.3 | 1.15.2 | no aplica | `38R/reglas/entorno.json` (Windows-11-10.0.26200-SP0, 1 hilo) |
| 39R | no verificada | no verificada | no verificada | no verificada | no verificada | No existe `39R/reglas/entorno.json` |

Las versiones coinciden en todos los registros disponibles, lo que sugiere un entorno único. Eso es una inferencia: no acredita las fases sin registro.

**Documentos Word de 38R y 39R.** Las herramientas están en `38R/documentos_definitivos/herramientas_word/` (`package-lock.json`, `requirements-documentos.txt`, `LEEME.md`). El control de maquetación necesita Microsoft Word. La versión de Node no se verificó.

---

## D. Protocolos, semillas, huellas y resultados

### D.1 Huellas registradas

Tomadas de los archivos `protocolo/sello*.json` de cada carpeta. No se recalcularon en esta etapa. En la Etapa 4A, 13 de 13 coincidieron con su archivo.

| Protocolo | SHA-256 registrado |
|---|---|
| Bootstrap | `4fe6794944fce62f8ed61f60f5d69b46c7d255a095c7b2c032c40c3f23f1a4ef` |
| 37A | `3c4d2de951c2769eb69e9680c7eb07bf0d0f69e2b3e26c6b7a62b574221eb39b` |
| 37B | `6b7c974d25b6e52114985e146017f721d5e9f27da43405193647915ac86926c6` |
| 37C | `62fd1d0b06e761129d26c4028526260bb1ea00565054eb8b378faa54ccb5e18f` |
| 37C, enmienda 1 | `3ab606c8d1a46e34e22f37299203e0b0e5ec2267f5951fe788d486b1ddd4e48d` |
| Complemento 37C | `6e00dec20c9e3336ec6a8160b3f5f1beba1165163bf2e0a1d293f9e5af392f9a` |
| Nota del complemento | `a3716c1ef6bfc07796746ebedb8c26963cec19d25efa2e279369e849b5ef4363` |
| 37D | `f7c8d125aa9181224360c226586eb990779d15776a5adb00a26ac5e54eb326b9` |
| Nota 37D | `bf5938d5d393399c22827074d0954c6357c4c6e2a2fab0c198566f866634642b` |
| 38 (histórica) | `9f9614115801805f9cde6c1586a8d7571ee44116c18ac7638025a645ee7f5a82` |
| 38R | `32a64ec8d5cdd4ceec8a13f54e44abccfbda689517cf430299eaf6a4b601e867` |
| 39 (histórica) | `18f15f821635f8c3d55a31f539d84d95ef8e5a32591e465073fb181a424c9042` |
| 39R | `c17c5bf05cc8f8ce9346a91638a19381399011647571ce15fa722581d2d8bb4e` |

La Fase 36 no tiene archivo de sello. Su control es `F36/integridad/manifiesto_final_36B.csv`. La Fase 35B se protegió con el commit previo `32cfdfd`.

### D.2 Semillas, parámetros y resultados

| Fase | Semillas y parámetros | Resultado definitivo |
|---|---|---|
| **35B** | SU = 2I/(H+H); p = (1+k)/(B+1); 5.000, 10.000 y 50.000 permutaciones; `SeedSequence(42, spawn_key=(1103,0,tipo,índice))`; q < 0,10 | 6 con q < 0,10 (días de ejercicio, bajo impacto, imc, fuerza, lugar, trabaja); 2 con q < 0,05. FCBF adaptada: fuerza, imc, lugar, trabaja. FCBF estándar: fuerza, lugar |
| **Random Forest** | `n_estimators=500, min_samples_leaf=5, max_features="sqrt", class_weight="balanced", random_state=42, n_jobs=1`; `RepeatedStratifiedKFold(5,3,random_state=42)`; 200 permutaciones | AUC: B 0,622; C1 0,659; D1 0,654. No selecciona variables |
| **Bootstrap** | Semilla raíz 42; id_analisis 1; 500 remuestreos; 5.000 permutaciones; alfa 0,10 | Nogueira 0,129 (0,118–0,139); relevancia 0,337 |
| **36** | Semilla 42, solo para validación | Matrices P1 529×34, P2 529×33, F1 529×50, F2 529×49 |
| **37A** | PCA `svd_solver='full'`; componentes 2, 3, 5, 8, 12, 16 y 20; análisis paralelo con 200 permutaciones, semilla 42 | `tablas/valores_propios.csv` |
| **37B** | Semilla 42; `KMeans(n_init=50, random_state=semilla, algorithm='lloyd')`; Ward; 30 remuestreos de 423; 20 réplicas nulas | 420 configuraciones; sin grupos naturales claros |
| **37C** | Protocolo sellado y enmienda 1 | Provisional: conclusión B, `P2_c12_km_k4`, 150/76/132/171 |
| **Complemento** | Regla de 4 pasos | B1 150/79/126/174; ARI A–B1 0,688 (CV 0,677) |
| **37D** | Protocolo sellado | 11 de 36 características asociadas con el MRS total tras la corrección (F1), todas con efecto pequeño (`informes/fuentes/15_informe_final_37D.md:48`) |
| **38R** | Semilla 42; 1.000 permutaciones; 200 submuestras de 80 %; n_A ≥ 53; n_AC ≥ 27; 15 sensibilidades; 1 hilo | 529 (281/248); 29 variables; 90 ítems; 42.937 conjuntos; 9.761 reglas; 971 marcadas; 1 de clase 6; p de exceso 0,013 |
| **39R** | Semillas `[42,39,k]`, `[42,39,100+d]`, `[42,39,2,k]`, `[42,39,3,d]`, `[42,39,1000+20·i+k]`, `[42,39,2000+10·i+d]`, `[42,39,200+10·g+k]`, `[42,39,110+g]`, `[42,39,3,10+g]` | 9 estratos; 47.912 reglas; 9.085 marcadas; 4.336 comparaciones; ninguna regla supera la nula de estrato (p mínimo 0,0549); resultado C |

### D.3 Diferencias entre universos

| Comparación | Diferencia |
|---|---|
| Fase 38 → 38R | La 38R retira las variables excluidas y usa 29 variables y 90 ítems |
| Fase 39 → 39R | Mismo universo que 38R. Las reglas pasan de 59.672 a 47.912. El resultado sigue siendo C |
| 33 → 30 → 29 | Módulos aparte, luego sin `imc` |
| Random Forest | Sus modelos usan 3 a 31 variables y no equivalen al universo de reglas |
| Bootstrap | Parte de `dataset_fase35.csv` y aplica las 33 candidatas |

Las Fases 38 y 39 históricas se conservan como antecedente. **Sus resultados no son los definitivos.**

### D.4 Limitaciones

Registradas en `auditoria_metodologica_final/INFORME_ETAPA_4A.md`. Siguen vigentes y no se corrigieron en esta etapa.

| Hallazgo | Limitación |
|---|---|
| Datos | Conjunto sintético de 529 participantes, sin validez clínica ni causalidad |
| H-05 | `configuracion.py` reintroduce las variables excluidas |
| H-06 | Entorno de análisis sin fijar |
| H-07 | El p de exceso no se ajusta entre los 9 estratos, y `19_informe_cierre_39R.md:123` generaliza |
| H-08 | Resolución Monte Carlo: 0,0549 [0,041–0,070]; 0,04995 [0,037–0,064]; clase 6 0,033 [0,022–0,045] |
| H-09 | La nota 16 de la 37D propone diabetes |
| H-10 | «Desaparece» mezcla causas distintas |
| H-11 | S7a y S7b significan cosas distintas en 38R y 39R |
| H-12 | La fórmula de p del protocolo 38 difiere de `evaluacion_38.py:80` |
| H-13 | ¬A incluye faltantes (`nucleo_38.py:379-386`) |

---

## E. Qué se puede reproducir hoy

| Aspecto | Estado |
|---|---|
| Reconstrucción conceptual de cada fase | Posible con protocolos, parámetros y semillas registrados |
| Reejecución de 38R y 39R desde un clon limpio | **No posible todavía:** ambas carpetas están sin control de versiones |
| Coincidencia de huellas tras un clon en Windows | **En riesgo:** `core.autocrlf=true` sin `.gitattributes`. Ver documento 03 |
| Identidad numérica de resultados | **No verificada** en esta etapa, porque no se ejecutó nada. El entorno debe coincidir con la sección C |
| Fases sin registro de entorno | Versiones **no verificadas** |
| Datos | Dependen de archivos bajo `datos/`. Parte está ignorada por `.gitignore`. Los cuatro archivos vedados no se revisaron |
