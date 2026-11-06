# 1. Propósito

Deja lista la información metodológica para comparar configuraciones en la Fase 37C. **Este documento no la inicia ni elige un modelo.**

# 2. Punto de partida

La Fase 37C debe partir de esta pregunta: si no hay grupos naturales marcados, ¿sirve una segmentación reproducible para los fines de la plataforma? Una posible respuesta es que no, y sería válida.

# 3. Dos listas para comparar

**Lista A, regla del protocolo** (108 configuraciones; `resultados/tabla_completa_configuraciones.csv`). La vista resumida:

| Configuración | Silueta | ARI entre | Percentil 5 | Grupo menor | Peso del eje 1 | Señales |
|---|---|---|---|---|---|---|
| F1_c02_km_k2 | 0,508 | 0,98 | 0,94 | 92 | 1,00 | eje 1 |
| F2_c02_km_k3 | 0,413 | 0,98 | 0,95 | 83 | 0,65 | Ninguna |
| F1_c03_km_k4 | 0,298 | 0,95 | 0,91 | 76 | 0,51 | Ninguna |
| F1_c03_km_k6 | 0,270 | 0,90 | 0,76 | 30 | 0,47 | Ninguna |
| F2_c03_ward_k2 | 0,399 | 0,79 | 0,61 | 79 | 0,99 | eje 1, inestables |
| P1_c08_km_k2 | 0,219 | 0,98 | 0,93 | 94 | 0,98 | eje 1 |
| P1_c02_km_k3 | 0,424 | 0,96 | 0,89 | 82 | 0,63 | Ninguna |
| P2_c12_km_k4 | 0,080 | 0,84 | 0,70 | 76 | 0,48 | Ninguna |
| P1_c02_km_k5 | 0,413 | 0,96 | 0,91 | 51 | 0,67 | Ninguna |
| P1_c02_km_k6 | 0,392 | 0,87 | 0,72 | 51 | 0,65 | Ninguna |
| P2_c02_km_k7 | 0,394 | 0,86 | 0,69 | 23 | 0,63 | grupo pequeño |
| P2_c02_km_k8 | 0,392 | 0,84 | 0,68 | 22 | 0,62 | grupo pequeño |
| P2_c02_ward_k2 | 0,512 | 0,81 | 0,51 | 63 | 0,99 | eje 1, inestables |
| P1_c02_ward_k5 | 0,367 | 0,67 | 0,52 | 58 | 0,69 | inestables |
| R0P1_cTodas_km_k2 | 0,127 | 0,94 | 0,88 | 90 | 0,95 | eje 1 |
| R0P1_cTodas_ward_k2 | 0,127 | 0,72 | 0,58 | 73 | 0,91 | eje 1, inestables |

**Lista B, sugerencia mía, hecha después de ver los resultados.** No estaba en el protocolo, por lo que debe tratarse como exploratoria. Toma de la Lista A las que cumplen: sin dominio del eje 1, sin repeticiones inestables, al menos 3 componentes, y ARI mediano de 0,85 o más en la familia de población.

| Configuración | Silueta | ARI entre | Nula: ARI media | S-TRA | S-EJE | S-ORD | S-SOLAPE |
|---|---|---|---|---|---|---|---|
| F1_c03_km_k3 | 0,296 | 0,94 | 0,56 | 0,97 | 0,80 | 0,80 | 0,24 |
| F1_c05_km_k3 | 0,186 | 0,88 | 0,38 | 0,94 | 0,87 | 0,20 | 0,24 |
| F1_c08_km_k3 | 0,120 | 0,81 | 0,28 | 0,91 | 0,88 | 0,19 | 0,23 |
| F2_c03_km_k3 | 0,300 | 0,95 | 0,56 | 0,96 | 0,77 | 0,82 | 0,24 |
| F2_c05_km_k3 | 0,186 | 0,88 | 0,39 | 0,95 | 0,85 | 0,20 | 0,25 |
| F2_c08_km_k3 | 0,120 | 0,81 | 0,28 | 0,89 | 0,87 | 0,19 | 0,24 |
| P1_c03_km_k3 | 0,299 | 0,86 | 0,57 | 0,95 | 0,85 | 0,51 | 0,24 |
| P1_c05_km_k3 | 0,190 | 0,85 | 0,38 | 0,91 | 0,78 | 0,55 | 0,23 |
| P2_c03_km_k3 | 0,300 | 0,86 | 0,56 | 0,94 | 0,87 | 0,51 | 0,24 |
| P2_c05_km_k3 | 0,190 | 0,85 | 0,38 | 0,90 | 0,82 | 0,55 | 0,23 |
| F1_c03_km_k4 | 0,298 | 0,95 | 0,72 | 0,89 | 0,75 | 0,80 | 0,41 |
| F2_c03_km_k4 | 0,300 | 0,95 | 0,71 | 0,89 | 0,56 | 0,80 | 0,41 |
| P1_c12_km_k4 | 0,079 | 0,83 | 0,25 | 0,99 | 0,88 | 0,67 | 0,35 |
| P2_c08_km_k4 | 0,116 | 0,79 | 0,30 | 0,87 | 0,84 | 0,62 | 0,36 |
| P2_c12_km_k4 | 0,080 | 0,84 | 0,24 | 0,96 | 0,88 | 0,69 | 0,36 |

Las versiones con y sin IMC son casi iguales, de modo que bastaría revisar una de cada par. Como referencia de la división por actividad física, se puede agregar una con k = 2, como `F1_c05_km_k2` o `P1_c05_km_k2`.

**Observaciones sobre la Lista B:**

- Todas son K-means.
- Todas con k = 3 tienen S-SOLAPE cerca de 0,24, y las de k = 4 de 0,35 a 0,41: conviene mirar qué separa esos grupos.
- S-ORD no es igual en todas: F1 con 3 ejes y k = 3 obtiene 0,80, y F1 con 5 ejes y k = 3 obtiene 0,20.

# 4. Qué falta por evaluar

| Asunto | Por qué importa |
|---|---|
| Interpretabilidad de los grupos, por sus variables | Es el criterio que aún no se evaluó |
| Una nula que conserve las correlaciones (propuesta) | La nula actual solo descarta independencia. Una nula con la misma covarianza, sin grupos, diría si hay algo más que un continuo correlacionado |
| Recalcular la reducción en cada remuestreo (propuesta) | La estabilidad actual no incluye la de la reducción |
| Qué hacer con S-ORD | La codificación de las ordinales afecta la división principal. Conviene decidir si es un riesgo que se acepta |
| Descripción de la severidad por grupo | Solo después de elegir, y sin poder cambiar la elección, según D-13 |
| Casos alejados de los prototipos | `prototipos/distancias_*.csv` tiene la distancia y el margen; falta definir qué hacer con ellos en la plataforma |

# 5. Asuntos para decidir antes de comenzar

- Usar la Lista A, la Lista B o ambas.
- Agregar o no las dos propuestas de la sección 4.
- Si se descarta el método aglomerativo como candidato principal, o se conserva para comparación.

# 6. Entradas disponibles

| Entrada | Ubicación |
|---|---|
| Etiquetas | `etiquetas/etiquetas_principales.csv` |
| Centroides, distancias y márgenes | `prototipos/` |
| Métricas y señales | `resultados/tabla_completa_configuraciones.csv` |
| Sensibilidades | `sensibilidades/comparacion_sensibilidades.csv` |
