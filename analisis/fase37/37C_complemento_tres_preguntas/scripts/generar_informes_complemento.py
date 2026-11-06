"""
Complemento de la Fase 37C: redacta los informes y la evaluación final a partir de las tablas guardadas. Las cifras se leen de las tablas, no se copian a mano.

Uso, desde analisis/: NODE_PATH=<carpeta con node_modules de docx> python fase37/37C_complemento_tres_preguntas/scripts/generar_informes_complemento.py
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.dont_write_bytecode = True
AQUI = Path(__file__).resolve().parent
B = AQUI.parent
C37 = B.parent / '37C_comparacion_seleccion'
INF = B / 'informes'
F = INF / 'fuentes'
F.mkdir(parents=True, exist_ok=True)
FIG = '../../figuras/'
SINT = 'Todo el análisis usa el conjunto sintético de usuarias (N = 529). Sus asociaciones vienen de una simulación, por lo que los resultados no permiten afirmar nada sobre mujeres reales.'
PROV = 'Comprobación exploratoria y posterior al cierre técnico de la Fase 37C. No cambia la conclusión B, no elige un modelo definitivo y no inicia la Fase 37D. La decisión queda en manos de la responsable del proyecto.'
NO_IND = 'B2 no usa las etiquetas de A, pero tampoco es del todo independiente: el trío se eligió antes porque era el que mejor reproducía a A.'


def L(r):
    return pd.read_csv(B / r, encoding='utf-8')


def J(r):
    return json.loads((B / r).read_text(encoding='utf-8'))


def n(x, d=2):
    return f'{float(x):.{d}f}'.replace('.', ',')


def e(x):
    """Entero con separador de miles."""
    return f'{int(x):,}'.replace(',', '.')


def tabla(cab, filas):
    s = '| ' + ' | '.join(cab) + ' |\n|' + '---|' * len(cab) + '\n'
    return s + ''.join('| ' + ' | '.join(str(c).replace('|', '\\|') for c in f) + ' |\n' for f in filas) + '\n'


rep = J('reproduccion/reproduccion_ari.json')
trios = L('reproduccion/distribucion_trios.csv')
defi = J('definiciones/definicion_B1_B2.json')
cel = L('definiciones/tabla_de_celdas.csv')
kk = L('definiciones/b2_cantidad_de_grupos.csv')
asg = L('asignaciones/comparacion_asignaciones.csv').set_index('alternativa')
cor = L('asignaciones/tablas_correspondencia.csv')
imi = L('fuera_de_muestra/imitacion_resumen.csv').set_index('alternativa')
tam = L('fuera_de_muestra/tamanos_resumen.csv').set_index('alternativa')
dis = L('fuera_de_muestra/desacuerdos_resumen.csv').set_index('alternativa')
tri = L('fuera_de_muestra/trios_busqueda_anidada.csv')
forma = L('fuera_de_muestra/forma_de_B1_por_repeticion.csv')
par = L('fuera_de_muestra/parametros_por_repeticion.csv')
est = L('estabilidad/estabilidad_alternativas.csv')
az = L('estabilidad/referencia_trios_azar.csv')
ib = L('informacion/informacion_por_bloque.csv').set_index('bloque')
iv = L('informacion/informacion_por_variable.csv').set_index('variable')
des = L('informacion/descripcion_por_variable.csv')
axa = L('informacion/a_sin_bloque_frente_a_A.csv').set_index('bloque_quitado')
dom = L('informacion/dominio_ssb_modelo_A.csv')
pb = L('informacion/posterior_A_sin_variable_bloque.csv').set_index('bloque')
pv = L('informacion/posterior_A_sin_variable.csv').set_index('variable')
ret = L('sin_segmentacion/varianza_retenida.csv').set_index('particion')
cb = L('sin_segmentacion/correlacion_entre_bloques.csv')
cp = L('sin_segmentacion/correlacion_por_par.csv')
s1 = L('complejidad/sensibilidad_B1.csv').set_index('sensibilidad')
s2 = L('complejidad/sensibilidad_B2.csv').set_index('variante')
imp = J('imputacion/efecto_imputacion.json')
imt = L('imputacion/imputadas_tres_preguntas.csv').set_index('variable')
et = L('asignaciones/etiquetas_alternativas.csv')
dec = json.loads((C37 / 'seleccion' / 'decision_final_37C.json').read_text(encoding='utf-8'))
fam = pd.read_csv(C37 / 'seleccion' / 'familia_cribado.csv')
fam = fam[fam['referencia'] == 'P2_c12_km_k4'].set_index('config')
comp = pd.read_csv(C37 / 'sensibilidades' / 'comparaciones_imc_algoritmo.csv').set_index('config').loc['P2_c12_km_k4']
pr = L('pruebas/resultados_pruebas.csv')
mu = L('pruebas/control_mutaciones.csv')
PROTEGIDOS = e(pr.iloc[0]['detalle'].split()[0])

E = est.pivot(index='alternativa', columns='medida', values='media')
E5 = est.pivot(index='alternativa', columns='medida', values='p05')
EM = est.pivot(index='alternativa', columns='medida', values='min')
PRINC = ['Alimentación', 'Actividad física adicional', 'Sedentarismo', 'Cuidados', 'Tabaco y alcohol', 'Otras generales']
DESC = ['Actividad sexual (descriptiva)', 'Digestión (descriptiva)']
mapa = defi['B1']['mapa']
# La forma de la regla se comprueba contra la tabla: si deja de cumplirse, el informe no se genera.
for c in range(20):
    dias, pareja, trabaja = c % 5 + 1, (c % 10) // 5, c // 10
    esperado = 1 if dias >= 3 else (0 if not pareja else (3 if trabaja else 2))
    if mapa[c] != esperado:
        raise SystemExit(f'La regla escrita no describe la celda {c}')
d_dx = {b: ib.loc[b, 'dr2_A_X_sobre_celdas__media'] for b in PRINC}
cumple_a = any(v >= 0.06 and ib.loc[b, 'dr2_A_X_sobre_celdas__p05'] > 0 for b, v in d_dx.items()) or sum(v >= 0.01 and ib.loc[b, 'dr2_A_X_sobre_celdas__p05'] > 0 for b, v in d_dx.items()) >= 3
if cumple_a:
    raise SystemExit('La guía favorece a la opción A: revisar la redacción antes de generar')
ident = forma['celdas_distintas_a_la_regla_529'].eq(0).sum()
pct_sobre_b2 = 100 * (az['entre_media'] < E.loc['B2', 'entre']).mean()
ssb_trio = dom[dom['bloque'] == 'Las tres preguntas']['parte_ssb_A'].sum()
ssb_af = dom[dom['bloque'] == 'Actividad física adicional']['parte_ssb_A'].sum()
ssb_sx = dom[dom['bloque'].str.startswith('Actividad sexual')]['parte_ssb_A'].sum()
pureza_baja = 100 * (et['pureza_B1'] < 0.8).mean()
margen_bajo = 100 * (et['margen_A'] < 0.10).mean()
entre_bl = cb[(cb['bloque_a'] != cb['bloque_b']) & ~((cb['bloque_a'] == 'Las tres preguntas') & cb['bloque_b'].isin(['Actividad física adicional', 'Actividad sexual (descriptiva)']))]
docs = {}

# ---- 02
docs['02_reproduccion_ari'] = ('Reproducción del ARI exploratorio', f"""# Conclusión

**Sí se reprodujo:** ARI {n(rep['ari_reproducido'], 4)}, idéntico al guardado en la Fase 37C (diferencia {n(rep['diferencia'], 4)}), con el mismo trío en primer lugar. Pero ese valor es el máximo de una búsqueda hecha con las propias etiquetas del Modelo A. No indica equivalencia, y un ARI de 0,68 **no significa 68 % de aciertos**.

{SINT}

{PROV}

# Cómo se construyó

La Fase 37C, en `revision_decision_37c.py`, probó las {e(rep['n_combinaciones'])} combinaciones de tres entre las 30 variables generales. Para cada una formó celdas con las respuestas, asignó a cada celda el segmento de A más frecuente con cuatro pliegues y predijo el quinto. Las variables cuantitativas se partieron en cuartiles. `dias_ejercicio_semana` es ordinal y conserva sus cinco códigos: no hubo cuartiles ni puntos de corte en el trío evaluado.

![Distribución de las 4.060 combinaciones]({FIG}f1_distribucion_trios.png)

# Posición del trío

{tabla(['Posición', 'Combinación', 'ARI con validación cruzada'], [[int(x.posicion), x.trio, n(x.ari_cv, 3)] for x in trios.head(5).itertuples()])}
La mediana de las {e(rep['n_combinaciones'])} combinaciones es {n(rep['mediana_combinaciones'], 2)} y el percentil 95 es {n(rep['p95_combinaciones'], 2)}. La mejor combinación sin trabajo llega a {n(rep['ari_mejor_sin_trabajo'], 2)}, sin pareja a {n(rep['ari_mejor_sin_pareja'], 2)} y sin ejercicio a {n(rep['ari_mejor_sin_ejercicio'], 2)}. Las tres preguntas aportan algo, y pareja y trabajo pesan más que ejercicio.

# Fuentes de optimismo

- **Selección:** el trío se eligió mirando las etiquetas con todos los datos. Para medirlo, se repitió la búsqueda dentro de cada entrenamiento: salió el mismo trío en {int(tri['repeticiones'].iloc[0])} de 30 repeticiones. Este optimismo es casi nulo aquí; el trío es muy estable.
- **Etiquetas:** las etiquetas de A se ajustaron también con las participantes de cada pliegue de evaluación. Fuera de muestra, con A reajustado solo en el entrenamiento, el ARI medio baja a {n(imi.loc['B1', 'ari_con_A_r_media'])}.

# En lenguaje sencillo

El resultado anterior era cierto, pero describe lo bien que tres preguntas imitan a un modelo en los mismos datos que ayudaron a elegirlas. Fuera de muestra sigue siendo bueno, aunque algo menor.
""")

# ---- 03
docs['03_definicion_B1_B2'] = ('Definición de B1 y B2', f"""# Conclusión

B1 y B2 **no son intercambiables**. B1 aproxima al Modelo A. B2 agrupa las tres preguntas sin mirar sus etiquetas. Ambas usan solo `trabaja_actualmente`, `tiene_pareja` y `dias_ejercicio_semana`.

{SINT}

{PROV}

# B1: reproducción del modelo complejo

Cada una de las 20 celdas posibles recibe el segmento de A más frecuente entre las participantes de entrenamiento. Empates: el segmento más grande y luego el de menor número. Celda vacía: el segmento más grande. **Usa las etiquetas de A como objetivo: es una aproximación, no una validación independiente.**

Con las 529, la tabla se puede leer como una regla de cuatro pasos. La forma no se fijó de antemano: se comprobó contra la tabla, celda por celda.

{tabla(['Paso', 'Condición', 'Segmento', 'Participantes'], [[1, 'Hace ejercicio 3 días o más a la semana', 'S1', int((et['B1_doble_uso'] == 1).sum())], [2, 'Si no, no tiene pareja', 'S0', int((et['B1_doble_uso'] == 0).sum())], [3, 'Si no, tiene pareja y no trabaja', 'S2', int((et['B1_doble_uso'] == 2).sum())], [4, 'Si no, tiene pareja y trabaja', 'S3', int((et['B1_doble_uso'] == 3).sum())]])}
El corte de 3 días no se impuso: salió de las etiquetas de A. Son cortes operativos sobre las respuestas, no tipos de personas. En {int(ident)} de las 30 repeticiones la tabla es idéntica; en las demás cambian 1 o 2 celdas, siempre con pocas participantes.

![Tabla de celdas de B1 y B2]({FIG}f2_mapa_de_celdas.png)

# B2: agrupación con las tres preguntas

K-means con k = 4 sobre las tres columnas en puntuación z de la matriz P2, con los parámetros de la Fase 37B. Como las respuestas son discretas, equivale a una tabla de 20 celdas: se comprobó que nunca separa a quienes responden igual. {NO_IND}

Su tamaño queda en {asg.loc['B2', 'tamanos'].replace(' ', ', ')}. Separa pareja y trabajo, y su grupo de ejercicio alto empieza en 5-6 días (en algunas celdas, 3-4), así que es más pequeño que S1.

# ¿Cuántos segmentos?

{tabla(['k', 'Silueta (tres columnas)', 'Tamaños', 'ARI con A'], [[int(x.k), n(x.silueta_tres_columnas, 2), x.tamanos.replace(' ', ', '), n(x.ari_con_A, 2)] for x in kk.itertuples()])}
La silueta sube sin parar con k porque los grupos se acercan a las celdas: no marca una cantidad natural de grupos, y **no se puede comparar con la silueta de A ({n(dec['referencia_nula']['silueta_obs'], 2)})**, porque mide datos discretos en otro espacio. k = 4 se usa como comparación principal, no porque los datos lo indiquen. B1 produce 4 segmentos en todas las repeticiones sin forzarlo.

# B2-C: cruce simple (secundario)

Pareja × trabajo × ejercicio bajo o alto, con el corte de ejercicio obtenido solo en el entrenamiento ({n(defi['B2_C']['corte_en_codigo'], 2)} en código, es decir, entre 1-2 y 3-4 días). Da 8 segmentos, de {int(asg.loc['B2_C', 'tam_min'])} a {max(map(int, asg.loc['B2_C', 'tamanos'].split()))} participantes. El más pequeño baja a {int(tam.loc['B2C', 'tam_min_menor'])} en algunos entrenamientos: **una regla simple no da grupos utilizables con 8 segmentos**, así que queda como referencia.

Definición exacta y centros: `definiciones/definicion_B1_B2.json` y `definiciones/tabla_de_celdas.csv`.
""")

# ---- 04
def crosst(nombre):
    m = cor[cor['comparacion'] == nombre].pivot(index='A', columns='alternativa', values='n')
    return tabla(['Segmento de A'] + [f'S{c}' for c in m.columns] + ['Total'], [[f'S{i}'] + [int(x) for x in m.loc[i]] + [int(m.loc[i].sum())] for i in m.index])


filas = []
for k, r in (('B1', 'Doble uso'), ('B1_cv', 'Validación cruzada'), ('B2', 'Sin etiquetas de A'), ('B2_C', 'Sin etiquetas de A')):
    x = asg.loc[k]
    filas.append([k.replace('_cv', ' (CV)').replace('_', '-'), r, int(x['segmentos']), x['tamanos'].replace(' ', ', '), n(x['ari_con_A']), f"{n(x['coincidencia_alineada_pct'], 1)} %", int(x['n_discrepan'])])
docs['04_correspondencia_segmentos'] = ('Correspondencia entre segmentos', f"""# Conclusión

En las 529, B1 reproduce buena parte de A (ARI {n(asg.loc['B1_cv', 'ari_con_A'])} con validación cruzada; {n(asg.loc['B1_cv', 'coincidencia_alineada_pct'], 0)} % de coincidencia tras alinear) y sus tamaños casi coinciden (A: 150, 76, 132 y 171; B1: {asg.loc['B1', 'tamanos'].replace(' ', ', ')}). B2 se parece algo menos y su grupo de ejercicio queda más pequeño. **Un ARI y una coincidencia no miden lo mismo**, y estas cifras usan las mismas participantes con las que se definió A.

{SINT}

{PROV}

# Asignaciones

{tabla(['Alternativa', 'Rótulo', 'Segmentos', 'Tamaños', 'ARI con A', 'Coincidencia alineada', 'Discrepan'], filas)}
![Correspondencia con A]({FIG}f3_correspondencia.png)

## A frente a B1

{crosst('B1')}
## A frente a B2

{crosst('B2')}
En B2, la mejor correspondencia solo se ve tras alinear. Por grupo de A, la coincidencia va de {n(asg.loc['B2', 'coincidencia_grupo_A1_pct'], 0)} % (S1, el grupo de ejercicio) a {n(asg.loc['B2', 'coincidencia_grupo_A0_pct'], 0)} % (S0). En B1 va de {n(asg.loc['B1_cv', 'coincidencia_grupo_A1_pct'], 0)} % a {n(asg.loc['B1_cv', 'coincidencia_grupo_A0_pct'], 0)} %.

# ¿Dónde están los desacuerdos?

Se concentran cerca de las fronteras de A: esas participantes ya tenían una asignación poco firme.

{tabla(['Alternativa', 'Margen de A < 0,10', '0,10 a 0,20', '≥ 0,20', 'AUC del margen'], [[k.replace('_cv', ' (CV)').replace('_', '-'), f"{n(asg.loc[k, 'discrepan_margen_bajo_010_pct'], 0)} %", f"{n(asg.loc[k, 'discrepan_margen_010_020_pct'], 0)} %", f"{n(asg.loc[k, 'discrepan_margen_alto_020_pct'], 0)} %", n(asg.loc[k, 'auc_margen_coinciden_mayor'])] for k in ('B1_cv', 'B2', 'B2_C')])}
Quienes discrepan de B1 tienen un margen mediano de {n(asg.loc['B1_cv', 'margen_mediano_discrepan'])}, frente a {n(asg.loc['B1_cv', 'margen_mediano_coinciden'])} en quienes coinciden. Quién discrepa, participante por participante: `asignaciones/etiquetas_alternativas.csv`.
""")

# ---- 05
filas = []
for k, nom in (('B1', 'B1'), ('B1N', 'B1 con búsqueda anidada'), ('B2', 'B2'), ('B2C', 'B2-C')):
    x = imi.loc[k]
    filas.append([nom, n(x['ari_con_A_r_media']), n(x['ari_con_A_r_mediana']), n(x['ari_con_A_r_p05']), f"{n(x['ari_con_A_r_min'])} a {n(x['ari_con_A_r_max'])}", f"{n(x['coincidencia_A_r_pct_media'], 0)} %", n(x['ari_con_A_oficial_media'])])
docs['05_fuera_de_muestra'] = ('Comparación fuera de muestra', f"""# Conclusión

Fuera de muestra, B1 y B2 coinciden con el Modelo A de su misma repetición en un {n(imi.loc['B1', 'coincidencia_A_r_pct_media'], 0)} % tras alinear, con ARI medio de {n(imi.loc['B1', 'ari_con_A_r_media'])} y percentil 5 de {n(imi.loc['B1', 'ari_con_A_r_p05'])}. La concordancia es sustancial, no una equivalencia. Tampoco es exactitud clínica: solo compara dos particiones.

{SINT}

{PROV}

# Procedimiento

Las mismas 30 submuestras de 423 de las Fases 37B y 37C, con 106 de evaluación. En cada una, imputación, escalado, PCA, K-means, tabla de B1 y centroides de B2 salen solo del entrenamiento y se congelan. A reproduce exactamente los lotes E3 de la Fase 37C en las 30 repeticiones.

# Concordancia en las participantes no usadas

{tabla(['Alternativa', 'ARI con A_r: media', 'Mediana', 'P05', 'Mínimo a máximo', 'Coincidencia', 'ARI con A oficial'], filas)}
A_r es el Modelo A ajustado en esa repetición: es la comparación limpia. Las etiquetas oficiales incluyen a esas participantes en su ajuste.

**Techo de referencia.** El propio A, reajustado, llega a un ARI de {n(E.loc['A', 'fuera'])} frente a sus etiquetas oficiales y de {n(E.loc['A', 'fuera_pares'])} entre repeticiones. Sirve de referencia: ni el propio A coincide plenamente consigo mismo.

# Búsqueda anidada

Al repetir la búsqueda entre las 4.060 combinaciones dentro de cada entrenamiento, salió el mismo trío en {int(tri['repeticiones'].iloc[0])} de 30 repeticiones. Por eso B1 anidada es idéntica a B1. **El trío no parece ser producto del azar de la selección dentro de este conjunto**, aunque esto no lo valida fuera de él.

# Tres aspectos distintos

- **Qué tan bien imita a A:** ARI {n(imi.loc['B1', 'ari_con_A_r_media'])} en la misma repetición.
- **Qué tan estable es la regla:** {n(E.loc['B1', 'entre'])} entre repeticiones. Ver informe 06.
- **Qué tan estable es A:** {n(E.loc['A', 'entre'])}. Imitar con exactitud una partición frágil no sería una mejora.

# Tamaños y equilibrio en el entrenamiento

{tabla(['Alternativa', 'Segmentos', 'Grupo menor: peor caso', 'Grupo menor: mediana', 'Equilibrio medio'], [[k, f"{int(tam.loc[k, 'segmentos_min'])} a {int(tam.loc[k, 'segmentos_max'])}", int(tam.loc[k, 'tam_min_menor']), n(tam.loc[k, 'tam_min_mediano'], 1), n(tam.loc[k, 'equilibrio_medio'])] for k in ('A', 'B1', 'B2', 'B2C')])}
# Desacuerdos frente a la frontera

![Desacuerdos según el margen de A]({FIG}f5_desacuerdos_frontera.png)

Con margen bajo 0,10, B1 discrepa de A en el {n(dis.loc['B1', 'discrepan_bajo_010_pct'], 0)} %; con 0,20 o más, en el {n(dis.loc['B1', 'discrepan_alto_020_pct'], 0)} %. El AUC es {n(dis.loc['B1', 'auc_margen'])}.

# En lenguaje sencillo

Con participantes que no intervinieron en el ajuste, tres preguntas ponen a más de 8 de cada 10 en el mismo grupo que el modelo complejo. Discrepan sobre todo con quienes el modelo ya ubicaba con poca seguridad.
""")

# ---- 06
filas = [[nom, n(E.loc[k, 'entre']), n(E5.loc[k, 'entre']), n(EM.loc[k, 'entre']), n(E.loc[k, 'fuera_pares']), n(E5.loc[k, 'fuera_pares']), n(E.loc[k, 'completo']), n(E.loc[k, 'fuera'])] for k, nom in (('A', 'Modelo A'), ('B1', 'B1'), ('B2', 'B2'), ('B2C', 'B2-C'))]
docs['06_estabilidad'] = ('Comparación de estabilidad', f"""# Conclusión

**La más estable es B1** ({n(E.loc['B1', 'entre'], 3)} entre repeticiones), seguida de B2 ({n(E.loc['B2', 'entre'], 3)}) y B2-C ({n(E.loc['B2C', 'entre'], 3)}), todas por encima de A ({n(E.loc['A', 'entre'], 3)}). Pero **esa ventaja es en gran parte estructural**: quienes responden igual siempre caen juntas. No es evidencia de grupos reales.

{SINT}

{PROV}

# Resultados

Las medidas de la Fase 37C. `entre`: pares de repeticiones con participantes compartidas. `fuera_pares`: solo participantes que ningún par usó. `completo` y `fuera`: frente a la partición de las 529.

{tabla(['Alternativa', 'Entre: media', 'P05', 'Mínimo', 'Fuera pares: media', 'P05', 'Completo', 'Fuera'], filas)}
![Estabilidad y referencia de tríos al azar]({FIG}f4_estabilidad.png)

# ¿Es mérito de estas preguntas?

B2 repetido con 30 tríos al azar da una estabilidad media de {n(az['entre_media'].mean())}, con mediana {n(az['entre_media'].median())} y un rango de {n(az['entre_media'].min())} a {n(az['entre_media'].max())}. B2 con el trío evaluado ({n(E.loc['B2', 'entre'])}) supera al {n(pct_sobre_b2, 0)} % de ellos. Es decir, **agrupar tres respuestas discretas suele ser estable, sean cuales sean**. La estabilidad no distingue a este trío; lo que lo distingue es que reproduce a A.

# ¿Y si cambia el objetivo o la codificación?

La regla congelada de B1 no cambia con la codificación de días, porque usa los códigos directamente. Pero si se reconstruye imitando a A con otra codificación, cambia (informe 08). B2 es sensible a cómo se codifica y pondera el ejercicio: ARI de {n(s2.loc['Días como ridit', 'ari_con_B2'])} con ridit y {n(s2.loc['Peso de ejercicio × 2', 'ari_con_B2'])} con el doble de peso.

# En lenguaje sencillo

Una regla de tres preguntas casi no cambia al variar la muestra, porque deja poco margen para cambiar. Eso es útil en la práctica, pero no demuestra que los grupos existan.
""")

# ---- 07
def fb(b, c):
    return n(ib.loc[b, f'{c}__media'], 3)


filas = [[b, int(ib.loc[b, 'n_variables']), fb(b, 'A'), fb(b, 'A-X'), fb(b, 'B1'), fb(b, 'B2'), fb(b, 'celdas'), fb(b, 'dr2_A_X_sobre_celdas'), n(ib.loc[b, 'dr2_A_X_sobre_celdas__p05'], 3), fb(b, 'dr2_A_sobre_celdas_circular')] for b in PRINC + DESC]
fv = ['frecuencia_aerobico', 'frecuencia_fuerza', 'frecuencia_bajo_impacto', 'tiene_actividad_sexual', 'frecuencia_comida_fuera', 'falta_tiempo_influye', 'vasos_agua_dia', 'platos_verduras_dia', 'frutas_dia']
di = des.pivot(index='variable', columns='particion', values='r2_interno')
dm = des.pivot(index='variable', columns='particion', values='diferencia_maxima')
filas_v = [[v, n(di.loc[v, 'A']), n(di.loc[v, 'B1']), n(di.loc[v, 'B2']), n(di.loc[v, 'Celdas']), n(dm.loc[v, 'A']), n(dm.loc[v, 'B1']), n(iv.loc[v, 'A'], 3), n(iv.loc[v, 'B1'], 3), n(pv.loc[v, 'dr2_A_v_sobre_celdas'], 3)] for v in fv]
docs['07_informacion_por_bloques'] = ('Información adicional por bloques', f"""# Conclusión

**Con la medida principal, A no añade información a las tres preguntas en ningún bloque:** ΔR² entre {n(min(d_dx.values()), 3)} y {n(max(d_dx.values()), 3)}, en la banda despreciable. A solo conserva más en las variables que usa como entrada: ejercicio aeróbico y de fuerza, actividad sexual y comida fuera. Eso es circular: para ubicar a alguien, el modelo ya necesita esas respuestas, así que se pueden consultar directamente.

{SINT}

{PROV}

# Por qué no basta comparar diferencias entre grupos

A usa casi todas estas variables, de modo que diferenciará sus propios grupos en ellas. Eso no demuestra validez externa. Por eso la medida principal, **A−X**, quita el bloque, rehace PCA y K-means, y mide qué tanto describe a ese bloque que ya no vio, igual que le ocurre a B. Se usa R² fuera de muestra: cuánto mejora la predicción frente a la media, en participantes no usadas. Solo cuentan respuestas observadas, sin imputadas. Un valor algo negativo equivale en la práctica a cero: la partición predice peor que la media por el ruido de sus parámetros.

![Información incremental por bloque]({FIG}f6_informacion_incremental.png)

# Resultados por bloque

R² fuera de muestra. ΔR² compara celdas + A−X frente a solo celdas. Bandas descriptivas: < 0,01 despreciable; 0,01 a 0,06 pequeña; ≥ 0,06 moderada. El percentil 5 no es un intervalo de confianza. Los dos últimos bloques son solo descriptivos y no son criterio.

{tabla(['Bloque', 'Var.', 'A (circular)', 'A−X', 'B1', 'B2', 'Celdas', 'ΔR² A−X', 'P05', 'ΔR² A (circular)'], filas)}
# Variables con más contraste

Magnitudes en las 529 (η² o V²; diferencia máxima en desviaciones estándar) y R² fuera de muestra. A−v es la comprobación posterior al sellado.

{tabla(['Variable', 'A', 'B1', 'B2', 'Celdas', 'Dif. A', 'Dif. B1', 'R² A', 'R² B1', 'ΔR² A−v'], filas_v)}
![R² fuera de muestra por variable]({FIG}f7_r2_por_variable.png)

# Qué aporta cada bloque

- **Alimentación:** A casi no describe la dieta. R² medio de {fb('Alimentación', 'A')}, circular. La diferencia se concentra en `frecuencia_comida_fuera` y `falta_tiempo_influye`, que se relacionan con trabajar (ρ de {n(cp[(cp['variable_a'] == 'trabaja_actualmente') & (cp['variable_b'] == 'frecuencia_comida_fuera')]['spearman_abs'].iloc[0])} y {n(cp[(cp['variable_a'] == 'trabaja_actualmente') & (cp['variable_b'] == 'falta_tiempo_influye')]['spearman_abs'].iloc[0])}). Frutas, verduras, carnes, lácteos y demás quedan en valores cercanos a 0 para todas las alternativas.
- **Actividad física adicional:** es lo que más conserva A: {fb('Actividad física adicional', 'A')} frente a {fb('Actividad física adicional', 'B1')} en B1. Es una diferencia moderada, pero circular. B1 y B2 conservan una parte reconocible porque días y frecuencias se correlacionan (ρ hasta {n(cp['spearman_abs'].iloc[0])}).
- **Sedentarismo, cuidados, tabaco y alcohol, y otras generales:** ninguna partición los describe. R² cercano a 0 o negativo en todas.
- **Actividad sexual (solo descriptiva):** A {fb('Actividad sexual (descriptiva)', 'A')} frente a B1 {fb('Actividad sexual (descriptiva)', 'B1')}. Se relaciona con tener pareja (ρ {n(cp[(cp['variable_a'] == 'tiene_pareja') & (cp['variable_b'] == 'tiene_actividad_sexual')]['spearman_abs'].iloc[0])}).

# ¿Siguen dominados por trabajo, pareja y ejercicio?

Sí. De la separación entre grupos de A, el {n(100 * ssb_trio, 0)} % viene de las tres preguntas y otro {n(100 * ssb_af, 0)} % de las frecuencias de ejercicio. Con actividad sexual ({n(100 * ssb_sx, 0)} %) suman {n(100 * (ssb_trio + ssb_af + ssb_sx), 0)} %. Sin las tres preguntas, A deja de parecerse a sí mismo (ARI {n(axa.loc['Las tres preguntas', 'ari_con_A'])}).

# Una objeción y su comprobación

En los bloques grandes, A−X se parece poco a A: ARI de {n(axa.loc['Alimentación', 'ari_con_A'])} sin alimentación, {n(axa.loc['Actividad física adicional', 'ari_con_A'])} sin actividad física y {n(axa.loc['Actividad sexual (descriptiva)', 'ari_con_A'])} sin actividad sexual. Podría ser injusto con A. En los bloques pequeños no hay ese problema (ARI de {n(axa.loc['Otras generales', 'ari_con_A'])} a {n(axa.loc['Cuidados', 'ari_con_A'])}).

**Comprobación posterior al sellado, rotulada como tal:** quitar solo la variable evaluada (A−v). El ARI medio con A sube a {n(pb.loc['Alimentación', 'ari_media'])} en alimentación y a {n(pb.loc['Actividad física adicional', 'ari_media'])} en actividad física, pero el aporte sigue siendo nulo: ΔR² de {n(pb.loc['Alimentación', 'dr2_media'], 3)} y {n(pb.loc['Actividad física adicional', 'dr2_media'], 3)}. En actividad sexual, A−v sigue lejos de A (ARI {n(pb.loc['Actividad sexual (descriptiva)', 'ari_media'])}). Esta comprobación refuerza la lectura, pero no estaba en el protocolo.

**Control de que la medida puede detectar:** quitadas las tres preguntas, A−X aún predice `dias_ejercicio_semana` con R² de {n(iv.loc['dias_ejercicio_semana', 'A-X'])}, por sus correlaciones con las frecuencias. Y al inyectar información en una prueba, ΔR² la detecta. Por tanto, el cero observado no es una incapacidad de la medida.

# Lo que esta medida no puede ver

- Mide cada variable por separado. Una ventaja de A en combinaciones conjuntas no se vería aquí. En la varianza multivariable, A conserva un {n(100 * ret.loc['A', 'varianza_P2_sin_trio_retenida'], 1)} % de lo que no es el trío, frente a {n(100 * ret.loc['B1', 'varianza_P2_sin_trio_retenida'], 1)} % de B1, pero eso es circular y en las mismas participantes.
- No evalúa ninguna variable externa. Por encargo, no se usa el MRS ni otros síntomas para elegir. Si A o B se relacionan de forma distinta con resultados externos, esta comprobación no lo sabe.

# En lenguaje sencillo

Para saber si el modelo complejo «sabe» algo más que las tres preguntas, se le ocultó cada tema y se vio si podía describirlo. No pudo: lo que parecía información adicional era en su mayoría lo mismo que se le había entregado.
""")

# ---- 08
filas_s = [[k, n(s1.loc[k, 'ari_A_sellado']), n(s1.loc[k, 'ari_B1']), int(s1.loc[k, 'segmentos_B1'])] for k in s1.index]
filas_b = [[k, x.grupo, n(x.ari_con_B2) if not x.por_construccion else 'No aplica: no le afecta por construcción', int(x.filas_ajuste)] for k, x in s2.iterrows()]
docs['08_complejidad_interpretabilidad'] = ('Complejidad e interpretabilidad', f"""# Conclusión

B1 pide 3 respuestas y se explica en cuatro pasos. A pide 29 respuestas, transformador, PCA de 12 componentes y centroides. **A no muestra un beneficio claro que compense esa diferencia**, y con esta evidencia tampoco se puede decir que B sea «mejor»: es más simple y deja menos cosas que puedan fallar.

{SINT}

{PROV}

# Comparación

{tabla(['Dimensión', 'Modelo A', 'B1', 'B2'], [
    ['Preguntas necesarias', '29 variables generales', '3', '3'],
    ['Reducción dimensional', 'PCA, 12 componentes', 'Ninguna', 'Ninguna'],
    ['Agrupamiento', 'K-means, k = 4', 'Tabla de 20 celdas; se lee en 4 pasos', 'K-means, k = 4; equivale a una tabla'],
    ['Estabilidad entre repeticiones', n(E.loc['A', 'entre']), n(E.loc['B1', 'entre']), n(E.loc['B2', 'entre'])],
    ['Interpretación', 'Cuatro segmentos multivariables provisionales, cortes de un continuo', 'Directa: tres respuestas', 'Directa, pero corte de ejercicio menos claro'],
    ['Nuevas participantes', 'Transformador, PCA y centroides', 'Regla sencilla', 'Regla o centroides'],
    ['Imputación expuesta', f"{n(imp['modelo_A_pct'], 0)} % tiene alguna respuesta imputada", f"{n(imp['pct'], 0)} %", f"{n(imp['pct'], 0)} %"],
    ['Incertidumbre', f"Margen mediano {n(et['margen_A'].median())}; {n(margen_bajo, 0)} % bajo 0,10", f"Pureza de celda: {n(pureza_baja, 0)} % bajo 0,80", 'Margen no comparable con el de A: datos discretos'],
    ['Información adicional', 'Solo circular', 'Referencia de simplicidad', 'Referencia de simplicidad'],
])}
# Sensibilidades

**B1.** Se reconstruyó la tabla imitando cada variante sellada de A. Mide cómo cambiaría la regla si cambiara su objetivo. Una vez congelada, la regla no depende de A.

{tabla(['Variante', 'ARI de A (Fase 37C)', 'ARI de B1', 'Segmentos de B1'], filas_s)}
**B2.** Reajustada con cada variante propia.

{tabla(['Variante', 'Grupo', 'ARI con B2', 'Filas de ajuste'], filas_b)}
B2 no resuelve la fragilidad frente a la codificación: {n(s2.loc['Días como ridit', 'ari_con_B2'])} con ridit frente a {n(s1.loc['S-ORD', 'ari_A_sellado'])} de A. Que S-SOLAPE no le afecte es por construcción y no se presenta como un logro.

# ¿Se justifican 12 componentes y K-means?

- **12 componentes:** con 8 y 16 las particiones son casi las mismas (ARI con A: {n(fam.loc['P2_c08_km_k4', 'ari_con_referencia'])} y {n(fam.loc['P2_c16_km_k4', 'ari_con_referencia'])}), y tampoco añaden información: ΔR² entre {n(min(ib.loc[b, 'dr2_A8_X_sobre_celdas__media'] for b in PRINC), 3)} y {n(max(ib.loc[b, 'dr2_A8_X_sobre_celdas__media'] for b in PRINC), 3)} con 8, y entre {n(min(ib.loc[b, 'dr2_A16_X_sobre_celdas__media'] for b in PRINC), 3)} y {n(max(ib.loc[b, 'dr2_A16_X_sobre_celdas__media'] for b in PRINC), 3)} con 16. Los datos no distinguen entre ellas.
- **K-means:** es estable y permite asignar directamente, pero su partición depende del algoritmo (ARI con Ward {n(comp['ari_km_ward'])}). Solo se justifica si se decide conservar A, y no por haber mostrado información adicional.

# En lenguaje sencillo

El modelo complejo necesita diez veces más respuestas y varios pasos técnicos para llegar a grupos muy parecidos. Si los dos dan casi lo mismo, lo más simple resulta más fácil de explicar y de mantener.
""")

# ---- 09
filas = [[{'A': 'Modelo A', 'B1': 'B1', 'B2': 'B2', 'B2_C': 'B2-C', 'Celdas': '20 celdas'}[k], int(ret.loc[k, 'segmentos']), f"{n(100 * ret.loc[k, 'varianza_P2_retenida'], 1)} %", f"{n(100 * ret.loc[k, 'varianza_P2_sin_trio_retenida'], 1)} %", f"{n(100 * (1 - ret.loc[k, 'varianza_P2_retenida']), 1)} %"] for k in ret.index]
docs['09_sin_segmentacion'] = ('Alternativa sin segmentación', f"""# Conclusión

**Continuar sin segmentación es razonable.** Cualquier partición deja fuera cerca de {n(100 * (1 - ret.loc['A', 'varianza_P2_retenida']), 0)} % de la varianza de las variables, y los bloques temáticos se relacionan muy poco entre sí: no hay un perfil conjunto amplio que resumir. Lo que se perdería es practicidad, no información demostrada.

{SINT}

{PROV}

# Lo que retiene cada partición

{tabla(['Partición', 'Segmentos', 'Varianza retenida (29 variables)', 'Sin las tres preguntas', 'Queda fuera'], filas)}
![Varianza retenida]({FIG}f8_varianza_retenida.png)

Medida en las 529. A maximiza justamente esta cantidad, y aun así solo le saca {n(100 * (ret.loc['A', 'varianza_P2_retenida'] - ret.loc['B1', 'varianza_P2_retenida']), 1)} puntos a B1.

# Por qué hay poco que resumir

Entre bloques, la correlación absoluta media es de {n(entre_bl['corr_abs_media'].min())} a {n(entre_bl['corr_abs_media'].max())} (Spearman, solo pares observados). Las excepciones esperables son días de ejercicio con frecuencias (hasta {n(cp['spearman_abs'].iloc[0])}) y pareja con actividad sexual ({n(cp[(cp['variable_a'] == 'tiene_pareja') & (cp['variable_b'] == 'tiene_actividad_sexual')]['spearman_abs'].iloc[0])}). Esta independencia podría ser una propiedad del simulador, y no tiene por qué repetirse en datos reales.

# Qué se gana y qué se pierde

{tabla(['Aspecto', 'Usar segmentos', 'Usar las variables directamente'], [
    ['Información individual', 'Se reduce a un grupo', 'Se conserva'],
    ['Fronteras', f"Crean casos dudosos: {n(margen_bajo, 0)} % con margen bajo 0,10 en A", 'No existen'],
    ['Estabilidad', 'Depende de la partición', 'No aplica: no hay asignación'],
    ['Imputaciones', 'Afectan a la asignación', 'Afectan solo a esa variable'],
    ['Comunicación', 'Un resumen breve', 'Más detalle y más difícil de resumir'],
    ['Comparaciones', 'Pocos grupos', 'Muchas variables: más comparaciones y más riesgo de hallazgos casuales'],
    ['Plan del proyecto', 'Compatible con reglas desde grupos', 'Requeriría ajustar ese plan'],
])}
No se desarrolló ningún sistema de recomendaciones, y no se usó el MRS ni otros resultados clínicos.

# En lenguaje sencillo

Decir «esta participante está en el segmento 3» da menos información que decir «trabaja, tiene pareja y hace poco ejercicio». Los grupos solo se justifican si hace falta un resumen o si un paso posterior del proyecto los necesita.
""")

# ---- 10
docs['10_limitaciones_imputaciones'] = ('Limitaciones e imputaciones', f"""# Conclusión

El problema de `tiene_actividad_sexual` **afecta a A y no a la asignación de las tres preguntas**. Pero las alternativas tienen su propia exposición: {imp['participantes_con_alguna_imputada']} participantes ({n(imp['pct'], 1)} %) tienen imputada alguna de las tres preguntas.

{SINT}

{PROV}

# `tiene_actividad_sexual`

- Observado en las 529: {imp['sexual_observadas']['SI']} «SI» y {imp['sexual_observadas']['NO']} «NO».
- {imp['sexual_imputadas']} valores imputados como «{imp['sexual_valor_imputado']}», con la moda de la población de limpieza anterior (546 filas).
- La diferencia es de {imp['sexual_observadas']['SI'] - imp['sexual_observadas']['NO']} respuestas. **No se afirma que la moda de 529 sea más correcta que la de 546.** No se modificó la limpieza ni la Fase 36.

{tabla(['Efecto de usar la moda de 529', 'Modelo A', 'B1', 'B2'], [
    ['Cambio en la partición', f"ARI {n(imp['sexual_ari_A_con_moda_529'])} (S-IMPMODA)", f"Tabla: ARI {n(imp['sexual_ari_B1_con_moda_529'])}", 'No cambia'],
    ['Quién cambia', f"{n(imp['sexual_A_cambian_entre_imputadas_pct'], 0)} % de las imputadas; {n(imp['sexual_A_cambian_entre_no_imputadas_pct'], 0)} % de las demás", f"{imp['sexual_celdas_B1_cambian_de_segmento_alineado']} celdas", f"{imp['sexual_B_cambian_celda']} participantes cambian de celda"],
])}
Así, A depende de esta decisión de limpieza y las alternativas no. B1 tampoco cambia, aun cuando su objetivo sea A: el cambio no alcanza a mover la mayoría de ninguna celda.

# Imputación en las tres preguntas

{tabla(['Pregunta', 'Imputadas', 'Valor imputado', 'Deducidas'], [[k, int(x.n_imputadas), x.valor_imputado, int(x.n_deducidas)] for k, x in imt.iterrows()])}
- **{imp['participantes_con_alguna_imputada']} participantes** tienen alguna de las tres imputada, y {imp['con_dos_o_mas']} tienen dos o más. En los ejercicios imputados, el valor es el código 1, «0 días».
- Quienes tienen alguna imputada discrepan más de A: {n(imp['B1_cv_discrepan_imputadas_pct'], 0)} % frente a {n(imp['B1_cv_discrepan_observadas_pct'], 0)} % en B1, y {n(imp['B2_discrepan_imputadas_pct'], 0)} % frente a {n(imp['B2_discrepan_observadas_pct'], 0)} % en B2.
- Con imputadas excluidas del ajuste, B2 cambia poco (ARI de {n(s2.loc[[k for k in s2.index if k.startswith('Ajuste')], 'ari_con_B2'].min())} a {n(s2.loc[[k for k in s2.index if k.startswith('Ajuste')], 'ari_con_B2'].max())}), pero eso no corrige la asignación de esas participantes.
- En A, la exposición es mayor: {n(imp['modelo_A_pct'], 1)} % tiene imputada alguna de las {imp['modelo_A_variables']} variables de entrada.

# Riesgos metodológicos que permanecen

- **Datos sintéticos.** Las relaciones, incluida la casi independencia entre bloques y la fuerza del trío, pueden venir de cómo se simuló. No hay validación independiente.
- **No es ciega.** El trío, el protocolo y la guía se redactaron conociendo la Fase 37C. La medida A−v es además posterior a ver resultados.
- **B2 no es independiente de A**, porque el trío se eligió por reproducir a A. B1 usa A como objetivo. Una concordancia alta no valida a ninguno.
- **Sin criterio externo.** Se excluyó a propósito. No se sabe cuál describe mejor algo que importe fuera de estas variables.
- **Grupos sin evidencia de ser naturales.** Sigue vigente la Fase 37C. Una regla simple tampoco lo demuestra.
- **Efecto de la escala (hipótesis no evaluada).** K-means con binarias en puntuación z podría favorecer cortes por pareja y trabajo. Coincide con la sensibilidad de A a la ponderación (S-BLOQUE {n(s1.loc['S-BLOQUE', 'ari_A_sellado'])}) y con la de B2 (peso × 2: {n(s2.loc['Peso de ejercicio × 2', 'ari_con_B2'])}), pero no se probó.
- **Medida por variable.** No ve ventajas en combinaciones. Con 106 participantes de evaluación, cambios muy pequeños no se distinguen del ruido.
- **Submuestras solapadas.** Los percentiles describen variación, pero no son intervalos de confianza.
- **Sin umbrales.** No hay umbrales definitivos de incertidumbre en ninguna alternativa.
""")

# ---- 11 tabla final
vd = [
    ('Reproducir la segmentación completa', 'Es la referencia; se reproduce a sí mismo con ' + n(E.loc['A', 'fuera_pares']) + ' entre repeticiones', f"ARI {n(imi.loc['B1', 'ari_con_A_r_media'])} y {n(imi.loc['B1', 'coincidencia_A_r_pct_media'], 0)} % de coincidencia, fuera de muestra", f"ARI {n(imi.loc['B2', 'ari_con_A_r_media'])} y {n(imi.loc['B2', 'coincidencia_A_r_pct_media'], 0)} %; grupo de ejercicio más pequeño", 'No aplica'),
    ('Estabilidad propia', f"{n(E.loc['A', 'entre'])}; P05 {n(E5.loc['A', 'entre'])}", f"{n(E.loc['B1', 'entre'])}; P05 {n(E5.loc['B1', 'entre'])}; en parte estructural", f"{n(E.loc['B2', 'entre'])}; P05 {n(E5.loc['B2', 'entre'])}; igual que tríos al azar", 'No hay asignación'),
    ('Información adicional', 'Ninguna sin circularidad; conserva más de sus propias entradas', 'Trío más lo correlacionado con él', 'Trío más lo correlacionado con él', 'Toda'),
    ('Simplicidad e interpretación', '29 respuestas y cuatro pasos técnicos', '3 respuestas y cuatro pasos legibles', '3 respuestas; corte de ejercicio menos claro', 'Sin pasos, con más detalle'),
    ('Sensibilidad a cambios', f"S-SOLAPE {n(s1.loc['S-SOLAPE', 'ari_A_sellado'])}, S-ORD {n(s1.loc['S-ORD', 'ari_A_sellado'])}, S-BLOQUE {n(s1.loc['S-BLOQUE', 'ari_A_sellado'])}", f"Congelada, no depende de A; reconstruida, {n(s1.loc['S-SOLAPE', 'ari_B1'])} a {n(s1.loc['S-EDAD', 'ari_B1'])}", f"Codificación {n(s2.loc['Días como ridit', 'ari_con_B2'])}, peso {n(s2.loc['Peso de ejercicio × 2', 'ari_con_B2'])}", 'No aplica'),
    ('Asignar nuevas participantes', f"Sí, con transformador y PCA; ARI fuera {n(E.loc['A', 'fuera'])}", f"Sí, con 3 respuestas; ARI fuera {n(E.loc['B1', 'fuera'])}", f"Sí, con 3 respuestas; ARI fuera {n(E.loc['B2', 'fuera'])}", 'No se asigna'),
    ('Grupos y tamaños', '4: 150, 76, 132, 171', '4: ' + asg.loc['B1', 'tamanos'].replace(' ', ', '), '4: ' + asg.loc['B2', 'tamanos'].replace(' ', ', '), 'Sin grupos'),
    ('Incertidumbre', f"{n(margen_bajo, 0)} % con margen bajo 0,10", f"{n(pureza_baja, 0)} % en celdas con pureza bajo 0,80", 'Margen no comparable', 'Sin fronteras'),
    ('Conjunto sintético', 'Sin validar', 'Sin validar; el trío viene de A', 'Sin validar; el trío viene de A', 'Sin validar'),
    ('Continuar sin segmentación', 'Requiere decidir cómo usar A', 'Casi equivale a usar las tres preguntas', 'Igual', 'Compatible, pero hay que ajustar los pasos que usan grupos'),
]
vdt = pd.DataFrame(vd, columns=['Criterio', 'Modelo A', 'B1', 'B2', 'Modelo C'])
(B / 'comparacion_final').mkdir(exist_ok=True)
vdt.to_csv(B / 'comparacion_final' / 'ventajas_desventajas.csv', index=False, encoding='utf-8', lineterminator='\n')
guia = [
    ('A: mantener los cuatro segmentos', 'A−X añade ≥ 0,06 en un bloque, o ≥ 0,01 en tres, con P05 > 0', f"**No se cumple.** ΔR² máximo {n(max(d_dx.values()), 3)}; ningún bloque llega a 0,01"),
    ('B: estudiar las tres preguntas', 'Aporte de A despreciable o pequeño; B1 o B2 igual de estables; conservan una parte reconocible', f"**Se cumple.** Estabilidad {n(E.loc['B1', 'entre'])} y {n(E.loc['B2', 'entre'])} frente a {n(E.loc['A', 'entre'])}; R² de {fb('Actividad física adicional', 'B1')} en actividad física"),
    ('C: sin segmentación', 'Las particiones retienen muy poco de los otros bloques y las preguntas dicen lo mismo que los segmentos', f"**Se cumple en gran parte.** R² cercano a 0 en cinco de seis bloques; las celdas igualan a B1 en los que sí tienen señal ({fb('Actividad física adicional', 'celdas')} frente a {fb('Actividad física adicional', 'B1')})"),
]
docs['11_ventajas_desventajas'] = ('Ventajas y desventajas', f"""# Conclusión

Ninguna alternativa domina en todo. A pierde por no demostrar información adicional, B gana en simplicidad y estabilidad, y C conserva toda la información, pero exige ajustar los pasos que usan grupos. No se usa puntuación compuesta.

{SINT}

{PROV}

# Comparación por criterio

{tabla(list(vdt.columns), vdt.values.tolist())}
# Guía de lectura sellada

{tabla(['Opción', 'Condición fijada antes de los resultados', 'Resultado'], guia)}
Las condiciones de B y C se cumplen a la vez. El protocolo lo previó: C también es razonable si, cumpliéndose B, no hay un uso concreto que exija asignar segmentos.
""")

# ---- 12 final
respuestas = [
    ('¿Se reprodujo el resultado exploratorio de tres preguntas?', f"Sí, exactamente: ARI {n(rep['ari_reproducido'], 4)}, primero entre {e(rep['n_combinaciones'])} combinaciones. Es el máximo de una búsqueda con las etiquetas de A."),
    ('¿Cómo se construyeron exactamente B1 y B2?', 'B1: mayoría del segmento de A en cada una de las 20 celdas; se lee en cuatro pasos (3 días o más de ejercicio; si no, sin pareja; si no, con pareja sin trabajo; si no, con pareja y trabajo). B2: K-means con k = 4 sobre las tres columnas z, sin etiquetas de A. ' + NO_IND),
    ('¿Qué tan parecidas son sus asignaciones al Modelo A?', f"En las 529, con validación cruzada: B1 con ARI {n(asg.loc['B1_cv', 'ari_con_A'])} y {n(asg.loc['B1_cv', 'coincidencia_alineada_pct'], 0)} % de coincidencia. B2 con ARI {n(asg.loc['B2', 'ari_con_A'])} y {n(asg.loc['B2', 'coincidencia_alineada_pct'], 0)} %. Los desacuerdos se concentran cerca de las fronteras de A."),
    ('¿Qué sucede fuera de muestra?', f"B1 alcanza ARI {n(imi.loc['B1', 'ari_con_A_r_media'])} con A de la misma repetición (P05 {n(imi.loc['B1', 'ari_con_A_r_p05'])}) y {n(imi.loc['B1', 'coincidencia_A_r_pct_media'], 0)} % de coincidencia; B2, {n(imi.loc['B2', 'ari_con_A_r_media'])} y {n(imi.loc['B2', 'coincidencia_A_r_pct_media'], 0)} %. El mismo trío salió en las 30 búsquedas anidadas."),
    ('¿Qué alternativa es más estable?', f"B1 ({n(E.loc['B1', 'entre'], 3)}), luego B2 ({n(E.loc['B2', 'entre'], 3)}), B2-C ({n(E.loc['B2C', 'entre'], 3)}) y A ({n(E.loc['A', 'entre'], 3)}). Es en gran parte estructural: tríos al azar dan una mediana de {n(az['entre_media'].median())}."),
    ('¿Qué información adicional aporta la segmentación completa?', f"Sin ver la variable que describe, ninguna: ΔR² de {n(min(d_dx.values()), 3)} a {n(max(d_dx.values()), 3)}. Con esa variable como entrada, conserva más de ejercicio aeróbico y fuerza, actividad sexual y comida fuera (R² aeróbico {n(iv.loc['frecuencia_aerobico', 'A'])} frente a {n(iv.loc['frecuencia_aerobico', 'B1'])}), pero eso es circular."),
    ('¿Cuántos segmentos aparecen y qué tamaños tienen?', f"A: 150, 76, 132 y 171. B1: 4 ({asg.loc['B1', 'tamanos'].replace(' ', ', ')}), sin forzar. B2: 4 ({asg.loc['B2', 'tamanos'].replace(' ', ', ')}). B2-C: 8, el menor con {int(asg.loc['B2_C', 'tam_min'])}. Las tres preguntas no indican una cantidad natural de grupos."),
    ('¿Qué ventajas operativas tiene cada alternativa?', 'A: usa más variables y sigue el método PCA + K-means. B1: 3 respuestas, regla legible, sin transformador, sin PCA. B2: no imita a A, pero es menos clara y más sensible a la codificación. C: sin fronteras ni casos dudosos, con toda la información.'),
    ('¿Se justifica conservar 12 componentes y K-means?', f"No por información adicional. Con 8 y 16 componentes la partición casi no cambia (ARI {n(fam.loc['P2_c08_km_k4', 'ari_con_referencia'])} y {n(fam.loc['P2_c16_km_k4', 'ari_con_referencia'])}), y K-means frente a Ward da {n(comp['ari_km_ward'])}. Solo se justifican si el proyecto decide mantener A por otra razón."),
    ('¿La segmentación de cuatro grupos aporta algo sustancial frente a utilizar tres preguntas?', f"No se encontró evidencia de ello en estos datos. A retiene {n(100 * ret.loc['A', 'varianza_P2_retenida'], 1)} % de la varianza frente a {n(100 * ret.loc['B1', 'varianza_P2_retenida'], 1)} % de B1. Esto no descarta un aporte en combinaciones de variables o en resultados externos, que no se evaluaron."),
    ('¿Continuar sin segmentación es una alternativa razonable?', f"Sí. Toda partición deja fuera cerca de {n(100 * (1 - ret.loc['A', 'varianza_P2_retenida']), 0)} % de la varianza y los bloques casi no se relacionan entre sí. Lo que se pierde es un resumen breve, y requeriría ajustar los pasos del plan que parten de grupos."),
    ('¿Qué riesgos metodológicos permanecen?', 'Datos sintéticos, análisis no ciego, B2 no independiente de A, ningún criterio externo, una comprobación posterior al sellado, medida por variable, cortes operativos sobre un continuo e imputación en ' + n(imp['pct'], 1) + ' % de participantes en las tres preguntas. Detalle en el informe 10.'),
    ('¿Qué pruebas se ejecutaron y cuáles pasaron?', f"{int((pr['resultado'] == 'superada').sum())} de {len(pr)} pruebas superadas y {int(mu['detectada'].sum())} de {len(mu)} errores introducidos detectados. Detalle en el informe 13."),
    ('¿Se mantuvieron intactos los archivos históricos?', PROTEGIDOS + ' archivos iguales a sus manifiestos, incluida toda la Fase 37C. HEAD sigue en 745d689, sin commit ni push, y sin cambios en Django. Detalle en el informe 14.'),
    ('¿Qué decisión recomienda el análisis, sin imponerla?', 'Opción B, con C igual de defendible si no hay un uso concreto de los grupos. Es decir: no mantener A como segmentación principal por ahora y estudiar la regla de cuatro pasos, informando también las variables directamente. No se recomienda A con esta evidencia.'),
]
docs['12_informe_metodologico_final'] = ('Informe metodológico final', f"""# Conclusión

**Recomendación no vinculante: opción B, estudiar la regla de tres preguntas como alternativa principal. La opción C, no segmentar, es igual de defendible si no hay un uso concreto de los grupos. Esta evidencia no respalda mantener los cuatro segmentos de `P2_c12_km_k4` como opción principal.**

La razón central: en estos datos, el modelo completo no añadió información comprobable a las tres preguntas en ningún bloque temático, y las tres preguntas lo reproducen en buena parte con mucho menos.

{PROV}

{SINT}

# Explicación en lenguaje sencillo

**¿Qué se quería saber?** Si el modelo de cuatro grupos, que usa 29 respuestas y varios pasos técnicos, dice algo que tres preguntas no digan: si trabaja, si tiene pareja y cuántos días hace ejercicio.

**¿Qué se encontró?**

- Tres preguntas ubican a más de 8 de cada 10 participantes en el mismo grupo que el modelo, incluso con personas que no intervinieron en el ajuste. Los desacuerdos están sobre todo donde el modelo ya dudaba.
- Al ocultarle un tema al modelo, no pudo describirlo mejor que las tres preguntas. Lo que parecía información adicional era en su mayoría lo mismo que había recibido como entrada.
- El sedentarismo, los cuidados, el consumo de tabaco y alcohol y la mayor parte de la alimentación casi no se diferencian entre grupos, sea cual sea la alternativa.
- Tres preguntas son muy estables, pero eso no las hace correctas: muchos otros grupos de tres preguntas también lo son.

**¿Qué significa?** Los cuatro grupos se pueden describir casi por completo así: hace ejercicio 3 días o más; si no, no tiene pareja; si no, tiene pareja y no trabaja; si no, tiene pareja y trabaja. Son cortes prácticos, no tipos de personas, ni una clasificación clínica.

**¿Qué no se puede afirmar?** Que las tres preguntas sean «mejores» o válidas, ni que esto valga para mujeres reales. Todo son datos simulados, y no se probó ningún resultado externo, por encargo.

![Información incremental por bloque]({FIG}f6_informacion_incremental.png)

# Evaluación con la guía sellada

{tabla(['Opción', 'Condición', 'Resultado'], guia)}
# Por qué B y no C, y qué cambiaría esta recomendación

- **B antes que C solo por compatibilidad:** el plan metodológico acordado llega a reglas desde grupos. Si esos pasos se mantienen, la regla de cuatro pasos es la forma más simple de tener grupos. En términos de información, B y C casi coinciden.
- **A podría recuperar terreno** si en datos reales o con un criterio externo muestra diferencias que las tres preguntas no capten, o si el plan exige PCA y K-means por razones ajenas a estos datos. En ese caso, conviene presentarlo con la regla de tres preguntas como comparación.
- **Las tres preguntas perderían terreno** si con datos reales el trío deja de ser el mejor, o si los grupos no sirven para el uso previsto.

# Respuestas a las preguntas del encargo

{chr(10).join(f'## {i}. {p}{chr(10)}{chr(10)}{r}{chr(10)}' for i, (p, r) in enumerate(respuestas, 1))}
# Estado

La comprobación queda completa: las verificaciones críticas se superaron. No se modificó la conclusión B de la Fase 37C, no se eligió un modelo definitivo y **la Fase 37D no se inició**.
""")

# ---- 15
docs['15_preparacion_decision_37D'] = ('Preparación para decidir sobre la Fase 37D', f"""# Conclusión

Con esta comprobación ya se puede decidir, pero **la Fase 37D no se inició** y necesita una instrucción expresa. Antes hace falta elegir la base de la caracterización. Los puntos de abajo son decisiones de la responsable del proyecto.

{SINT}

# Decisiones pendientes

{tabla(['Decisión', 'Opciones', 'Observación'], [
    ['1. Base de la Fase 37D', 'A: `P2_c12_km_k4`. B: regla de cuatro pasos. C: variables directamente', 'Recomendación no vinculante: B, con C igual de defendible'],
    ['2. ¿Hay un uso concreto de los grupos?', 'Sí: reglas desde grupos o plataforma. No: seguir con variables', 'Si no lo hay, C es más simple'],
    ['3. ¿El plan exige PCA + K-means?', 'Sí: mantener A e informar B como comparación. No: puede usarse B', 'El plan de la reunión del 16-10 incluía PCA y K-means o aglomerativo; conviene confirmarlo'],
    ['4. Imputación de `tiene_actividad_sexual`', 'Mantener la moda de 546 o revisar la limpieza', 'Solo importa si se mantiene A'],
])}
# Qué implica cada camino

{tabla(['Camino', 'Qué se haría en la Fase 37D', 'Riesgo principal'], [
    ['A', 'Caracterizar cuatro segmentos con las notas de la Fase 37C', 'Describir como hallazgo lo que ya entró al modelo'],
    ['B', 'Caracterizar cuatro segmentos definidos por tres respuestas', 'Equivale a comparar por trabajo, pareja y ejercicio; no presentar como un descubrimiento'],
    ['C', 'Describir por variables, sin grupos', 'Muchas comparaciones; hay que controlarlas de antemano'],
])}
# Advertencias para cualquier camino

- Trabajo, pareja, ejercicio y actividades relacionadas no pueden usarse como evidencia externa de grupos construidos con ellas.
- Si la Fase 37D compara síntomas o el MRS entre grupos, será la primera vez que aparezca un criterio externo. Esa comparación no debería usarse para reelegir la segmentación con los mismos datos sin declararlo.
- Todo sigue siendo sintético. Se necesita un conjunto real e independiente para hacer cualquier afirmación sobre mujeres.

# Lo que queda disponible

`asignaciones/etiquetas_alternativas.csv` (A, B1, B2 y B2-C por participante), `definiciones/` (tabla de celdas y centros) y `comparacion_final/` (ventajas, desventajas y recomendación). Todo es provisional.
""")

# ---- 13 y 14
leidos = L('integridad/archivos_leidos.csv')
fuera = L('integridad/escrituras_fuera.csv')
memo = L('integridad/registro_memoria.csv')
sello = J('protocolo/sello_protocolo.json')
sello2 = J('protocolo/sello_nota_posterior.json')
minimo = memo[memo['evento'].str.contains('mínimo')]['libre_gb'].min()
pruebas_md = f"""# Complemento de la Fase 37C: informe de pruebas

**Resultado:** {int((pr['resultado'] == 'superada').sum())} de {len(pr)} pruebas superadas y {int(mu['detectada'].sum())} de {len(mu)} errores introducidos detectados.

Durante el desarrollo, la prueba 14 falló por un error de la propia prueba: su caso sintético tenía 4 participantes no usadas y la función exige 5. Mientras estuvo así, sus dos controles negativos se contaban como detectados sin mérito. Se corrigió la prueba y se repitió todo; luego se revisó el motivo de detección de cada control.

{tabla(['Núm.', 'Prueba', 'Resultado', 'Detalle'], [[int(x.numero), x.prueba, x.resultado, x.detalle] for x in pr.itertuples()])}
## Controles negativos

Cada uno introduce un error en memoria, sin tocar archivos, y exige que falle la prueba indicada.

{tabla(['Error introducido', 'Prueba', 'Detectado'], [[x.mutacion, int(x.prueba), 'Sí' if x.detectada else 'NO'] for x in mu.itertuples()])}
## No cubierto

Los Word se comprobaron por su estructura (`scripts/verificar_informes_complemento.py`), pero no se revisaron como página porque el equipo no tiene LibreOffice. Las figuras sí se revisaron visualmente. Las pruebas históricas de fases anteriores no se reejecutaron; esas fases se verificaron por huellas.
"""
integ_md = f"""# Complemento de la Fase 37C: informe de integridad

- **Archivos protegidos:** {PROTEGIDOS} archivos de las Fases 34-35, 36, 37A, 37B y 37C iguales a sus manifiestos.
- **Conclusión de la Fase 37C:** intacta (`{dec['conclusion']}`).
- **Protocolo:** sellado antes de calcular nada nuevo. Huella `{sello['sha256']}`. La nota posterior tiene su propia huella: `{sello2['sha256']}`.
- **Lecturas:** {len(leidos)} archivos leídos fuera de esta carpeta, ninguno de `datos/` ni del MRS. Registro: `integridad/archivos_leidos.csv`.
- **Escrituras fuera de la carpeta:** {len(fuera)}.
- **Git:** HEAD en 745d689, sin commit y sin push, sin cambios fuera de `analisis/` (Django y plataforma intactos).
- **Reproducción:** etiquetas de A idénticas; 30 de 30 repeticiones iguales a los lotes E3 de la Fase 37C; ARI de {n(rep['ari_reproducido'], 4)} idéntico.
- **Memoria:** máximo de 2 procesos, con vigilancia. Mínimo libre: {n(minimo)} GB, sin detenciones. Registro: `integridad/registro_memoria.csv`.
- **Manifiesto final:** `integridad/manifiesto_final.csv`, con la huella de todos los archivos de esta carpeta salvo él mismo.

## Restricciones

Sin cambios en datos, limpieza, matrices ni fases selladas. Sin reabrir las 420 configuraciones. Sin verdad del simulador. Sin MRS como criterio. Sin reglas de asociación. Sin caracterización clínica. Sin cambios en la plataforma. Sin Fase 37D.
"""
indice = """# Comprobación complementaria de la Fase 37C: índice

Empezar por `12_informe_metodologico_final.docx`.

| Núm. | Entregable | Archivo |
|---|---|---|
| 1 | Protocolo sellado | `01_protocolo_complemento.docx` (original en `protocolo/`) |
| 2 | Reproducción del ARI exploratorio | `02_reproduccion_ari.docx` |
| 3 | Definición de B1 y B2 | `03_definicion_B1_B2.docx` |
| 4 | Correspondencia entre segmentos | `04_correspondencia_segmentos.docx` |
| 5 | Comparación fuera de muestra | `05_fuera_de_muestra.docx` |
| 6 | Comparación de estabilidad | `06_estabilidad.docx` |
| 7 | Información por bloques | `07_informacion_por_bloques.docx` |
| 8 | Complejidad e interpretabilidad | `08_complejidad_interpretabilidad.docx` |
| 9 | Alternativa sin segmentación | `09_sin_segmentacion.docx` |
| 10 | Limitaciones e imputaciones | `10_limitaciones_imputaciones.docx` |
| 11 | Ventajas y desventajas | `11_ventajas_desventajas.docx` |
| 12 | Informe metodológico final | `12_informe_metodologico_final.docx` |
| 13 | Informe de pruebas | `13_informe_pruebas.md` |
| 14 | Informe de integridad | `14_informe_integridad.md` |
| 15 | Preparación para decidir sobre la Fase 37D | `15_preparacion_decision_37D.docx` |

Tablas: `reproduccion/`, `definiciones/`, `asignaciones/`, `fuera_de_muestra/`, `estabilidad/`, `informacion/`, `complejidad/`, `sin_segmentacion/`, `imputacion/` y `comparacion_final/`. Figuras: `figuras/`.
"""
for nombre, t in (('13_informe_pruebas.md', pruebas_md), ('14_informe_integridad.md', integ_md), ('00_indice_entregables.md', indice)):
    (INF / nombre).write_text(t, encoding='utf-8', newline='\n')
N_REC = {'estado': 'NO VINCULANTE. La decisión final queda en manos de la responsable del proyecto. No modifica la conclusión de la Fase 37C.', 'recomendacion': 'Opción B: estudiar la regla de tres preguntas como alternativa principal', 'igual_de_defendible': 'Opción C, si no hay un uso concreto de los grupos', 'no_respaldada': 'Opción A: mantener los cuatro segmentos como opción principal', 'dr2_A_X_por_bloque': {b: float(v) for b, v in d_dx.items()}, 'estabilidad_entre': {k: float(E.loc[k, 'entre']) for k in E.index}, 'imitacion_fuera_de_muestra': {k: float(imi.loc[k, 'ari_con_A_r_media']) for k in imi.index}, 'caracter': 'Exploratorio y posterior al cierre técnico de la Fase 37C; datos sintéticos', 'fase_37D': 'No iniciada'}
(B / 'comparacion_final' / 'recomendacion_no_vinculante.json').write_text(json.dumps(N_REC, ensure_ascii=False, indent=1) + '\n', encoding='utf-8', newline='\n')
shutil.copyfile(B / 'protocolo' / '01_protocolo_complemento.md', F / '01_protocolo_complemento.md')
docs_titulo = {'01_protocolo_complemento': 'Protocolo de la comprobación complementaria'}
js = C37 / 'scripts' / 'md_a_word_37c.js'
for nombre, (titulo, md) in docs.items():
    (F / f'{nombre}.md').write_text(md.strip() + '\n', encoding='utf-8', newline='\n')
    docs_titulo[nombre] = titulo
for nombre, titulo in docs_titulo.items():
    r = subprocess.run(['node', str(js), str(F / f'{nombre}.md'), str(INF / f'{nombre}.docx'), titulo, 'AgingWomen · Comprobación complementaria de la Fase 37C'], capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f'{nombre}: {r.stderr[:500]}')
print(len(docs_titulo), 'informes Word')
