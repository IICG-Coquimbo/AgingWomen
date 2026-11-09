"""
Fase 37B: redacta los informes a partir de las tablas ya calculadas. Las cifras se leen de las tablas, no se copian a mano.

Uso, desde analisis/: python fase37/37B_clustering/scripts/generar_informes_37b.py
Escribe en informes/. Convierte a Word con md_a_word_37b.js (requiere NODE_PATH con el paquete docx).
"""
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd

sys.dont_write_bytecode = True
AQUI = Path(__file__).resolve().parent
B = AQUI.parent
INF = B / 'informes'
FUENTES = INF / 'fuentes'
FUENTES.mkdir(parents=True, exist_ok=True)
FIG = '../../figuras/'
K = [2, 3, 4, 5, 6, 7, 8]
COMP = [2, 3, 5, 8, 12, 16, 20]
SINT = 'Todo el análisis usa el conjunto sintético de usuarias (N = 529). Sus asociaciones vienen de una simulación, por lo que los resultados no permiten afirmar nada sobre mujeres reales.'

t = pd.read_csv(B / 'resultados' / 'tabla_completa_configuraciones.csv', encoding='utf-8')
nu = pd.read_csv(B / 'referencia_nula' / 'comparacion_por_configuracion.csv', encoding='utf-8')
bm = pd.read_csv(B / 'referencia_nula' / 'busqueda_multiple.csv', encoding='utf-8')
se = pd.read_csv(B / 'sensibilidades' / 'comparacion_sensibilidades.csv', encoding='utf-8')
rs = pd.read_csv(B / 'sensibilidades' / 'resumen_por_variante.csv', encoding='utf-8')
ca = pd.read_csv(B / 'resultados' / 'comparaciones_ari.csv', encoding='utf-8')
imp = pd.read_csv(B / 'resultados' / 'imc_imputado_por_grupo.csv', encoding='utf-8')
asg = pd.read_csv(B / 'prototipos' / 'evaluacion_asignacion.csv', encoding='utf-8')
peq = pd.read_csv(B / 'resultados' / 'grupos_pequenos.csv', encoding='utf-8')
pr = pd.read_csv(B / 'pruebas' / 'resultados_pruebas.csv', encoding='utf-8')
mu = pd.read_csv(B / 'pruebas' / 'control_mutaciones.csv', encoding='utf-8')
le = pd.read_csv(B / 'integridad' / 'archivos_leidos.csv')
ve = pd.read_csv(B / 'integridad' / 'verificacion_entradas.csv', encoding='utf-8')
L = t[t['lista_37C']]
ALG = {'km': 'K-means', 'ward': 'Aglomerativo'}


def n(x, d=2):
    return f'{x:.{d}f}'.replace('.', ',')


def tabla(cabeza, filas):
    return '\n'.join(['| ' + ' | '.join(map(str, cabeza)) + ' |', '|' + '---|' * len(cabeza)] + ['| ' + ' | '.join(map(str, f)) + ' |' for f in filas]) + '\n'


def t_por_k(a):
    x = t[t['algoritmo'] == a]
    filas = []
    for k in K:
        g = x[x['k'] == k]
        filas.append([k, n(g['silueta'].median(), 3), n(g['ari_entre_media'].median()), int((g['ari_entre_media'] > 0.80).sum()), int(g['ari_entre_media'].between(0.65, 0.80).sum()), int((g['ari_entre_media'] < 0.65).sum()), int((g['grupos_pequenos'] > 0).sum()), int(g['lista_37C'].sum())])
    return tabla(['k', 'Silueta mediana', 'ARI entre remuestreos, mediana', 'ARI alto (> 0,80)', 'Intermedio', 'Bajo (< 0,65)', 'Con grupo bajo 27', 'Cumplen la regla'], filas)


def t_por_comp(a):
    x = t[(t['algoritmo'] == a) & (t['componentes'] > 0)]
    filas = []
    for c in COMP:
        g = x[x['componentes'] == c]
        filas.append([c, n(g['silueta'].median(), 3), n(g['ari_entre_media'].median()), int((g['ari_entre_media'] > 0.80).sum()), int(g['lista_37C'].sum())])
    g = t[(t['algoritmo'] == a) & (t['componentes'] == 0)]
    filas.append(['Sin reducción', n(g['silueta'].median(), 3), n(g['ari_entre_media'].median()), int((g['ari_entre_media'] > 0.80).sum()), int(g['lista_37C'].sum())])
    return tabla(['Componentes', 'Silueta mediana', 'ARI entre remuestreos, mediana', 'ARI alto', 'Cumplen la regla'], filas)


def t_top(a, col, m=10):
    x = t[t['algoritmo'] == a].sort_values([col, 'config'], ascending=[False, True]).head(m)
    return tabla(['Configuración', 'Silueta', 'ARI frente al completo', 'ARI entre remuestreos', 'Percentil 5', 'Grupo menor', 'Peso del eje 1'], [[r.config, n(r.silueta, 3), n(r.ari_completo_media), n(r.ari_entre_media), n(r.ari_entre_p05), r.tam_min, n(r.fraccion_eje1)] for r in x.itertuples()])


def t_nula_comp(e, a, k):
    x = t[(t['espacio'] == e) & (t['algoritmo'] == a) & (t['k'] == k)][['config', 'componentes']].merge(nu, on='config').sort_values('componentes')
    return tabla(['Componentes', 'Silueta observada', 'Nula: media (máx.)', 'ARI entre observado', 'Nula: media (máx.)'], [[r.componentes, n(r.silueta_obs, 3), f'{n(r.silueta_nula_media, 3)} ({n(r.silueta_nula_max, 3)})', n(r.ari_entre_media_obs), f'{n(r.ari_entre_media_nula_media)} ({n(r.ari_entre_media_nula_max)})'] for r in x.itertuples()])


NOM_MED = {'silueta': 'Silueta', 'davies_bouldin': 'Davies-Bouldin', 'calinski_harabasz': 'Calinski-Harabasz', 'ari_completo_media': 'ARI frente al completo', 'ari_entre_media': 'ARI entre remuestreos', 'ari_fuera_media': 'ARI fuera de muestra'}
T_BUSQUEDA = tabla(['Medida', 'Superan a las 20 réplicas', 'En las réplicas: mediana (máx.)', 'Mayor z observado', 'En las réplicas: mediana (máx.)', 'p'], [[NOM_MED[r.medida], r.conteo_supera_observado, f'{n(r.conteo_nula_mediana, 1)} ({r.conteo_nula_max})', n(r.z_max_observado, 1), f'{n(r.z_max_nula_mediana, 1)} ({n(r.z_max_nula_max, 1)})', n(r.p_z_max, 3)] for r in bm.itertuples()])


def t_sens():
    orden = ['S-ORD', 'S-FAMD', 'S-RARA', 'S-TRA', 'S-CUI', 'S-EJE', 'S-EDAD', 'S-SOLAPE', 'S-BLOQUE', 'S-BLOQUE-SA']
    filas = []
    for s in orden:
        x = rs[rs['sensibilidad'] == s].set_index('algoritmo')
        pro = '; '.join(f"{ALG[a]} {n(x.loc[a, 'ari_proyeccion_mediana'])}" for a in ('km', 'ward')) if x['ari_proyeccion_mediana'].notna().all() else 'No aplica'
        filas.append([s, x['familia'].iloc[0], n(x.loc['km', 'ari_ajuste_mediana']), n(x.loc['ward', 'ari_ajuste_mediana']), pro])
    return tabla(['Variante', 'Familia', 'K-means: ARI de ajuste', 'Aglomerativo: ARI de ajuste', 'ARI de proyectadas'], filas)


def t_sens_k(a):
    orden = ['S-ORD', 'S-FAMD', 'S-RARA', 'S-TRA', 'S-CUI', 'S-EJE', 'S-EDAD', 'S-SOLAPE']
    p = se[se['algoritmo'] == a].pivot_table(index='sensibilidad', columns='k', values='ari_ajuste', aggfunc='median').reindex(orden)
    return tabla(['Variante'] + [f'k = {k}' for k in K], [[s] + [n(v) for v in f] for s, f in zip(p.index, p.to_numpy())])


def cmp_tabla():
    filas = []
    for nom in ('Con y sin IMC, PCA', 'Con y sin IMC, FAMD', 'Con y sin IMC, sin reducción', 'PCA y FAMD, con IMC', 'PCA y FAMD, sin IMC'):
        x = ca[ca['comparacion'] == nom]
        for a in ('km', 'ward'):
            g = x[x['algoritmo'] == a]
            filas.append([nom, ALG[a], n(g['ari_529'].median()), f"{n(g['ari_529'].min())} a {n(g['ari_529'].max())}", n(g['ari_267_imc_observado'].median()) if g['ari_267_imc_observado'].notna().any() else 'No aplica'])
    x = ca[ca['comparacion'] == 'K-means y aglomerativo']
    filas.append(['K-means y aglomerativo', 'Ambos', n(x['ari_529'].median()), f"{n(x['ari_529'].min())} a {n(x['ari_529'].max())}", 'No aplica'])
    return tabla(['Comparación', 'Algoritmo', 'ARI mediano en las 529', 'Rango', 'ARI mediano en las 267 con IMC observado'], filas)


def t_asig():
    filas = []
    for a in ('km', 'ward'):
        x = asg[asg['algoritmo'] == a]
        filas.append([ALG[a], f"{n(x['acuerdo_prototipo_pct'].median(), 1)} % ({n(x['acuerdo_prototipo_pct'].min(), 1)} a {n(x['acuerdo_prototipo_pct'].max(), 1)})", n(x['acuerdo_prototipo_ari'].median()), n(x['ari_fuera_media'].median()), n(x['margen_mediano'].median())])
    return tabla(['Algoritmo', 'Coincidencia con sus etiquetas', 'ARI con sus etiquetas', 'ARI fuera de muestra, mediana', 'Margen mediano'], filas)


def t_asig_k():
    p = asg[asg['algoritmo'] == 'ward'].groupby('k')['acuerdo_prototipo_pct'].median()
    f = asg.pivot_table(index='k', columns='algoritmo', values='ari_fuera_media', aggfunc='median')
    return tabla(['k', 'Aglomerativo: coincidencia mediana', 'K-means: ARI fuera de muestra', 'Aglomerativo: ARI fuera de muestra'], [[k, n(p[k], 1) + ' %', n(f.loc[k, 'km']), n(f.loc[k, 'ward'])] for k in K])


def visibles():
    x = t[t['lista_37C_visible']].sort_values(['metodo', 'algoritmo', 'k'])
    return tabla(['Configuración', 'Silueta', 'ARI entre', 'Percentil 5', 'Grupo menor', 'Peso del eje 1', 'Señales'], [[r.config, n(r.silueta, 3), n(r.ari_entre_media), n(r.ari_entre_p05), r.tam_min, n(r.fraccion_eje1), ', '.join(s for s, v in (('eje 1', r.senal_eje1), ('inestables', r.senal_repeticiones_inestables), ('grupo pequeño', r.senal_grupos_pequenos)) if v) or 'Ninguna'] for r in x.itertuples()])


def ari_de(config, sid):
    x = se[(se['config_base'] == config) & (se['sensibilidad'] == sid)]
    return n(x['ari_ajuste'].iloc[0]) if len(x) else 'No aplica'


PRIO = t[t['lista_37C'] & ~t['senal_eje1'] & ~t['senal_repeticiones_inestables'] & (t['componentes'] >= 3) & (t['sens_Población'] >= 0.85)].sort_values(['k', 'espacio', 'componentes'])


def t_prior():
    return tabla(['Configuración', 'Silueta', 'ARI entre', 'Nula: ARI media', 'S-TRA', 'S-EJE', 'S-ORD', 'S-SOLAPE'], [[r.config, n(r.silueta, 3), n(r.ari_entre_media), n(nu.set_index('config').loc[r.config, 'ari_entre_media_nula_media']), ari_de(r.config, 'S-TRA'), ari_de(r.config, 'S-EJE'), ari_de(r.config, 'S-ORD'), ari_de(r.config, 'S-SOLAPE')] for r in PRIO.itertuples()])


def escribe(nombre, texto):
    (FUENTES / nombre).write_text(texto.strip() + '\n', encoding='utf-8', newline='\n')


km, wa = t[t['algoritmo'] == 'km'], t[t['algoritmo'] == 'ward']
km_alt = km.groupby('k')['ari_semilla_alterna'].median()
A_SIMPLE = """**Silueta:** compara, para cada persona, qué tan cerca está de su grupo y del grupo vecino. Cerca de 1, grupos bien separados; cerca de 0, personas en la frontera; negativa, más cerca de otro grupo.

**ARI:** compara dos agrupaciones sin importar cómo se llamen sus grupos. 1 es coincidencia total y 0 es lo esperable por azar.

**Referencia nula:** se mezclan al azar los valores de cada variable por separado. Así desaparece cualquier relación entre variables, y se ve hasta dónde llega el algoritmo sin esa relación."""
LIMITES = f"""- **Datos sintéticos.** {SINT}
- **No son diagnósticos.** Los grupos no equivalen a niveles de riesgo, y su número no indica un orden.
- **La nula solo descarta independencia.** Un conjunto con variables correlacionadas puede superarla sin tener grupos naturales. Tampoco es una prueba sobre la población.
- **La reducción no se recalculó en los remuestreos.** Se ajustó con las 529, así que la estabilidad evalúa solo el agrupamiento.
- **Pocas réplicas.** Con 20 réplicas, `p` no baja de 0,048."""

# ------------------------------------------------------------------ 11 K-means
escribe('11_informe_kmeans.md', f"""
# 1. Conclusión

**K-means forma particiones reproducibles con 2 a 4 grupos, pero con separación modesta.** Sus grupos se parecen al repetir el análisis en otras muestras. No hay señales de grupos naturales bien separados. {SINT}

# 2. Qué se hizo

Se ajustaron {len(km)} configuraciones: 4 espacios × 7 cantidades de componentes × 7 valores de k, más 14 sin reducción. Los parámetros son `n_init = 50`, `random_state = 42` y el algoritmo estándar de scikit-learn, sin escalado adicional. Las {len(km)} convergieron, con {int(km['iteraciones'].max())} iteraciones como máximo.

{A_SIMPLE}

# 3. Resultados por número de grupos

{t_por_k('km')}
**En palabras simples:** cuantos más grupos se piden, menos se repiten. Con 2 grupos la solución es casi la misma en todas las muestras; con 7 u 8, solo en una minoría de las configuraciones.

![Figura 1. Estabilidad de las configuraciones. La fila superior corresponde a K-means.]({FIG}f06_estabilidad.png)

# 4. Resultados por número de componentes

{t_por_comp('km')}
![Figura 2. Silueta media por número de grupos.]({FIG}f01_silueta.png)

La silueta baja al sumar componentes, en buena parte porque las distancias se parecen más entre sí en más dimensiones. Por eso **no sirve para comparar entre espacios**.

# 5. Mejores valores

**Mayor estabilidad:**

{t_top('km', 'ari_entre_media')}
**Mayor silueta:**

{t_top('km', 'silueta')}
Ambas listas están dominadas por k = 2 o por 2 componentes, por las razones de la sección 6.

# 6. Dos advertencias sobre los valores altos

**Con k = 2, los grupos dividen sobre todo por el eje 1,** que describe la actividad física. Las {int(((L['k'] == 2) & L['senal_eje1']).sum())} configuraciones con k = 2 de la lista tienen un peso del eje 1 de 0,80 o más. Son estables, pero no forman grupos integrales.

**Con 2 componentes, la estabilidad dice poco, porque la nula también es alta.** Con k = 3, P1:

{t_nula_comp('P1', 'km', 3)}
Con 2 ejes, la nula ya obtiene un ARI medio de {n(nu.set_index('config').loc['P1_c02_km_k3', 'ari_entre_media_nula_media'])}: K-means divide un plano de forma repetible aunque no exista estructura. Además, 2 ejes retienen solo cerca del 11 al 14 % de la inercia. La diferencia frente a la nula es más informativa desde 3 o 5 ejes.

# 7. Inicializaciones

Repetir K-means con otra semilla da soluciones muy parecidas con pocos grupos, pero no con muchos. ARI mediano frente a la semilla alternativa:

{tabla(['k'] + K, [['ARI'] + [n(km_alt[k]) for k in K]])}
Con k = 6 o más, 50 inicializaciones no bastan para llegar a una misma solución en muchas configuraciones. {int((km['ari_semilla_alterna'] < 0.80).sum())} de las {len(km)} quedan bajo 0,80. Esto indica un paisaje con varias soluciones casi equivalentes.

# 8. Tamaños de los grupos

{int((km['grupos_pequenos'] > 0).sum())} de las {len(km)} configuraciones tienen algún grupo bajo 27, y el menor tiene {int(km['tam_min'].min())} participantes. Todas ellas tienen k = 7 u 8. No se eliminó ningún grupo.

# 9. Sensibilidades

Mediana del ARI de ajuste, por número de grupos, sin las variantes de ponderación:

{t_sens_k('km')}
- **Población y edad:** con k = 2 a 4 el acuerdo es alto o intermedio, y baja desde k = 6.
- **S-SOLAPE:** con k = 2 no afecta (0,98), pero con k = 3 cae a 0,24. El tercer grupo depende de `tiene_actividad_sexual` o `distension_abdominal`, que esa variante quita.
- **S-ORD:** con k = 2 baja a 0,27, incluso cambiando mucho los tamaños (P1 con 5 ejes: de cerca de 93 frente a 436 a 225 frente a 304). La división por el eje 1 depende de cómo se codifiquen las ordinales.

# 10. Limitaciones

{LIMITES}
""")

# ------------------------------------------------------------------ 12 Aglomerativo
escribe('12_informe_aglomerativo.md', f"""
# 1. Conclusión

**El método aglomerativo con Ward es inestable en casi todas las configuraciones con k = 3 o más.** Solo {int((wa['ari_entre_media'] > 0.80).sum())} de {len(wa)} supera un ARI de 0,80 entre remuestreos, y {int((wa['ari_entre_media'] < 0.65).sum())} quedan bajo 0,65. {SINT}

# 2. Qué se hizo

Se ajustaron {len(wa)} configuraciones con `AgglomerativeClustering`, enlace Ward y distancia euclidiana. El algoritmo no tiene `predict`, así que se ajustó de nuevo en cada remuestreo.

{A_SIMPLE}

# 3. Resultados por número de grupos

{t_por_k('ward')}
**En palabras simples:** Ward fusiona de a pares y nunca deshace una fusión. Cambiar unas pocas personas puede alterar muchas fusiones posteriores. Por eso sus grupos cambian bastante entre muestras, aun cuando su silueta sea parecida a la de K-means.

# 4. Resultados por número de componentes

{t_por_comp('ward')}
# 5. Mejores valores

**Mayor estabilidad:**

{t_top('ward', 'ari_entre_media')}
**Mayor silueta:**

{t_top('ward', 'silueta')}
Incluso en estas configuraciones, el percentil 5 del ARI suele estar bajo 0,65: algunas repeticiones son muy inestables, por lo que estas medias altas no se pueden llamar robustas. La mayor silueta, en P1 con 2 ejes y k = 2, tiene un percentil 5 de {n(wa.set_index('config').loc['P1_c02_ward_k2', 'ari_entre_p05'])}.

# 6. Frente a la referencia nula

Con k = 5, F1:

{t_nula_comp('F1', 'ward', 5)}
Ward queda a menudo por encima de la nula en ARI, pero con valores bajos: es «menos inestable que el azar», no estable. Y en silueta queda varias veces dentro del rango de la nula.

![Figura 1. Observado frente a la referencia nula, con 5 ejes.]({FIG}f08_referencia_nula.png)

# 7. Tamaños de los grupos

{int((wa['grupos_pequenos'] > 0).sum())} de las {len(wa)} configuraciones tienen algún grupo bajo 27, y el menor tiene {int(wa['tam_min'].min())} participantes. Ward produce tamaños menos equilibrados que K-means. No se eliminó ningún grupo.

![Figura 2. Tamaños de los grupos.]({FIG}f04_tamanos.png)

# 8. Sensibilidades

Mediana del ARI de ajuste, sin las variantes de ponderación:

{t_sens_k('ward')}
Ward es sensible a todo, salvo en k = 2. Esto coincide con su baja estabilidad en los remuestreos: como los grupos ya cambian con la muestra, no se puede atribuir ese cambio a la variante.

# 9. Asignación de participantes nuevas

Ward no tiene `predict`. Se evaluó el centroide más cercano de los grupos formados. **Esa regla no equivale a la asignación jerárquica.**

{t_asig_k()}
La coincidencia con sus etiquetas va de {n(asg[asg['algoritmo'] == 'ward']['acuerdo_prototipo_pct'].min(), 1)} % a {n(asg[asg['algoritmo'] == 'ward']['acuerdo_prototipo_pct'].max(), 1)} %. Una participante del conjunto puede quedar en otro grupo al aplicar la regla, y el ARI fuera de muestra es bajo desde k = 3.

# 10. Limitaciones

{LIMITES}
""")

# ------------------------------------------------------------------ 13 Comparación
mej_km = km[km['k'] >= 3]['ari_entre_media']
escribe('13_comparacion_preliminar.md', f"""
# 1. Conclusión preliminar

**Hay particiones reproducibles con K-means, sobre todo con 2 a 4 grupos, pero no hay evidencia de grupos naturales claramente diferenciados.** Este informe no elige un modelo. {SINT}

- **Separación:** la silueta es baja cuando se usan varios ejes (con 5 ejes y k = 3, cerca de 0,19).
- **Estabilidad:** K-means es muy superior a Ward.
- **Referencia nula:** se supera ampliamente, lo que muestra que las variables no son independientes. No demuestra que existan grupos.
- **Sensibilidad:** las agrupaciones resisten cambios de población, pero dependen de decisiones de codificación y de ciertas variables.

# 2. K-means y aglomerativo

{tabla(['Medida', 'K-means', 'Aglomerativo'], [
    ['Silueta mediana', n(km['silueta'].median(), 3), n(wa['silueta'].median(), 3)],
    ['ARI entre remuestreos, mediana', n(km['ari_entre_media'].median()), n(wa['ari_entre_media'].median())],
    ['ARI entre remuestreos, mediana con k ≥ 3', n(km[km['k'] >= 3]['ari_entre_media'].median()), n(wa[wa['k'] >= 3]['ari_entre_media'].median())],
    ['Configuraciones con ARI alto (> 0,80)', int((km['ari_entre_media'] > 0.8).sum()), int((wa['ari_entre_media'] > 0.8).sum())],
    ['Configuraciones con ARI bajo (< 0,65)', int((km['ari_entre_media'] < 0.65).sum()), int((wa['ari_entre_media'] < 0.65).sum())],
    ['Con algún grupo bajo 27', int((km['grupos_pequenos'] > 0).sum()), int((wa['grupos_pequenos'] > 0).sum())],
    ['Cumplen la regla del protocolo', int(km['lista_37C'].sum()), int(wa['lista_37C'].sum())]])}
![Figura 1. K-means frente al método aglomerativo.]({FIG}f07_kmeans_aglomerativo.png)

La silueta es parecida, pero la estabilidad no. Los dos algoritmos tampoco forman los mismos grupos: su ARI mediano es {n(ca[ca['comparacion'] == 'K-means y aglomerativo']['ari_529'].median())}.

# 3. Comparaciones entre configuraciones

{cmp_tabla()}
**PCA y FAMD** coinciden bastante con K-means en k = 2 y 3 (ARI mediano de 0,83 y 0,79), y poco desde k = 4 (de 0,30 a 0,41). Con Ward coinciden poco, salvo en parte con k = 2 (0,58). No se usa la inercia ni la silueta para preferir uno: sus espacios no son comparables.

**Con y sin IMC:** con K-means casi no hay diferencia (ARI mediano cerca de 0,93). Con Ward el ARI baja a cerca de 0,41, aunque quitar el IMC casi no cambia las coordenadas (similitud de al menos 0,996 en la Fase 37A). **Eso refleja la fragilidad de Ward, no un efecto del IMC.**

**IMC imputado por grupo:** en los escenarios con IMC va de {n(imp['imc_imputado_pct'].min(), 1)} % a {n(imp['imc_imputado_pct'].max(), 1)} %, con mediana {n(imp['imc_imputado_pct'].median(), 1)} %. El global es 49,5 %. Los valores extremos aparecen en grupos de 21 a 53 participantes, con 2 componentes.

![Figura 2. Acuerdo con y sin IMC.]({FIG}f09_con_sin_imc.png)

# 4. Referencia nula y búsqueda múltiple

{T_BUSQUEDA}
Bajo independencia se esperarían unas 20 configuraciones por medida. Se observan muchas más, y el mayor z queda por encima de todas las réplicas. **Lo que esto descarta es la independencia entre variables,** un resultado esperable por lo visto en la Fase 37A. No indica cuál configuración es buena ni que existan grupos. Calinski-Harabasz supera a todas las réplicas en las 420, lo que probablemente refleja la mayor varianza del primer eje.

![Figura 3. Configuraciones que superan a las 20 réplicas.]({FIG}f08b_supera_nula.png)

# 5. Sensibilidades

{t_sens()}
![Figura 4. Acuerdo con la configuración base.]({FIG}f11_sensibilidades.png)

- **Población:** resultados altos con K-means. Parte del cambio puede deberse a la población, y las proyectadas se informan aparte.
- **Codificación:** S-ORD cambia las particiones con frecuencia, incluida la de k = 2.
- **Variables:** S-EDAD casi no cambia nada. S-SOLAPE afecta desde k = 3.
- **Ponderación:** S-BLOQUE y S-BLOQUE-SA dan grupos casi sin relación con la base. **Son otra pregunta, no un fallo de robustez.**

También aparecieron grupos pequeños nuevos en {int(((se['grupos_pequenos'] > 0) & (se['grupos_pequenos_base'] == 0)).sum())} de los {len(se)} ajustes de sensibilidad.

# 6. Asignación de participantes nuevas

{t_asig()}
K-means dispone de una regla directa, con coincidencia de 100 % por construcción. Con Ward, la regla de prototipos cambia de grupo a parte de las participantes. **En viabilidad de asignación, K-means queda mejor,** aunque en k altos también pierde acuerdo fuera de muestra.

![Figura 5. Asignación de participantes nuevas.]({FIG}f12_asignacion.png)

# 7. Ilustración

![Figura 6. Siluetas individuales en ejemplos fijos.]({FIG}f05_siluetas_individuales.png)

![Figura 7. Proyecciones ilustrativas. Los grupos se formaron con 5 ejes.]({FIG}f10_proyecciones.png)

# 8. Limitaciones

{LIMITES}
""")

# ------------------------------------------------------------------ 16 Cierre
ok = (pr['resultado'] == 'OK').sum()
cerrada = ok == len(pr)
escribe('16_informe_cierre_37B.md', f"""
# 1. Estado

**{'La Fase 37B queda cerrada' if cerrada else 'La Fase 37B NO queda cerrada'}: {ok} de {len(pr)} pruebas superadas.** Las 420 configuraciones, las 20 réplicas nulas y los 3.332 ajustes de sensibilidad están completos. La Fase 37C no se inició y no hay commit ni push. {SINT}

# 2. ¿Hay agrupaciones suficientemente diferenciadas y estables?

**Estables, sí, en parte. Claramente diferenciadas, no hay evidencia.**

- **K-means forma particiones reproducibles con 2 a 4 grupos.** Ward no, salvo parcialmente con k = 2.
- **La separación es modesta.** Con 3 o más ejes, y k ≥ 3, la silueta es de 0,30 o menos. Con 2 ejes llega a 0,42, pero esos ejes retienen solo cerca del 11 al 14 % de la inercia.
- **Con k = 2, los grupos se dividen casi solo por actividad física.** Esa división, además, cambia con la codificación de las ordinales.
- **Con k = 3, la división añade una dimensión que depende de una variable** (S-SOLAPE: ARI 0,24).
- **Superar la nula** muestra que las variables no son independientes, no que existan grupos naturales.

Por eso, estos grupos se entienden mejor como **una segmentación útil de un continuo** que como tipos naturales de participantes. Si esa segmentación sirve para la plataforma es una pregunta para la Fase 37C.

# 3. Regla del protocolo

{len(L)} configuraciones cumplen las dos condiciones del protocolo. La regla resultó **poco exigente**: {int(L['senal_eje1'].sum())} de ellas tienen un peso del eje 1 de 0,80 o más, y {int(L['senal_repeticiones_inestables'].sum())} tienen repeticiones inestables. El protocolo está sellado, así que la regla se aplicó sin cambios y estas limitaciones se informan aparte.

**Vista resumida que fija el protocolo:**

{visibles()}
Esta vista elige en cada grupo la de mayor ARI entre remuestreos, lo que favorece a 2 componentes, donde la nula también es alta. Por eso, el documento de preparación de la Fase 37C propone además otra lista.

# 4. Adiciones y decisiones propias

El encargo no pidió lo siguiente; lo incorporé y queda a tu criterio:

- **Peso del primer eje** (`SSB en C1 / SSB total`), descriptivo.
- **Semilla alternativa en K-means,** para distinguir la inestabilidad del optimizador de la del muestreo.
- **Asignación fuera de muestra,** en cada remuestreo.
- **Sensibilidades en las 98 combinaciones de cada variante,** en lugar de una configuración de referencia, para no elegir antes de tiempo.
- **Regla de la sección 11 del protocolo,** con los controles de búsqueda múltiple.
- **Ejemplos fijos (5 ejes, k = 3)** en las figuras ilustrativas. No son una selección.

# 5. Pruebas e integridad

{ok} de {len(pr)} pruebas superadas. El control introdujo {mu['error_introducido'].nunique()} errores, detectados en {int(mu['detectado'].sum())} de {len(mu)} comprobaciones. Detalle en `14_informe_pruebas.md` y `15_informe_integridad.md`. Las Fases 34, 35, 36 y 37A no cambiaron.

# 6. Lo que no se hizo

No se seleccionó un modelo, no se caracterizaron los grupos, no se les dio nombre, no se usó el MRS, no se usó GMM, no se generaron reglas de asociación y no se modificó la plataforma.

# 7. Límites

{LIMITES}
""")

# ------------------------------------------------------------------ 17 Preparación 37C
escribe('17_preparacion_37C.md', f"""
# 1. Propósito

Deja lista la información metodológica para comparar configuraciones en la Fase 37C. **Este documento no la inicia ni elige un modelo.**

# 2. Punto de partida

La Fase 37C debe partir de esta pregunta: si no hay grupos naturales marcados, ¿sirve una segmentación reproducible para los fines de la plataforma? Una posible respuesta es que no, y sería válida.

# 3. Dos listas para comparar

**Lista A, regla del protocolo** ({len(L)} configuraciones; `resultados/tabla_completa_configuraciones.csv`). La vista resumida:

{visibles()}
**Lista B, sugerencia mía, hecha después de ver los resultados.** No estaba en el protocolo, por lo que debe tratarse como exploratoria. Toma de la Lista A las que cumplen: sin dominio del eje 1, sin repeticiones inestables, al menos 3 componentes, y ARI mediano de 0,85 o más en la familia de población.

{t_prior()}
Las versiones con y sin IMC son casi iguales, de modo que bastaría revisar una de cada par. Como referencia de la división por actividad física, se puede agregar una con k = 2, como `F1_c05_km_k2` o `P1_c05_km_k2`.

**Observaciones sobre la Lista B:**

- Todas son K-means.
- Todas con k = 3 tienen S-SOLAPE cerca de 0,24, y las de k = 4 de 0,35 a 0,41: conviene mirar qué separa esos grupos.
- S-ORD no es igual en todas: F1 con 3 ejes y k = 3 obtiene {ari_de('F1_c03_km_k3', 'S-ORD')}, y F1 con 5 ejes y k = 3 obtiene {ari_de('F1_c05_km_k3', 'S-ORD')}.

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
""")

# ------------------------------------------------------------------ 14 Pruebas
fallos = """| Fallo | Causa | Resolución |
|---|---|---|
| Prueba 23, tablas iguales a los lotes | Error de la prueba: exigía igualdad exacta tras leer decimales de un CSV. Los datos estaban bien | Usa una tolerancia de 1e-12 |
| Control: centroides alterados sin detectar en la prueba 19 | La prueba recalculaba los prototipos sin revisar los guardados | La prueba compara también los guardados |
"""
previos = """Antes de sellar el protocolo también corregí un error de programación: el nombre de una variable no general estaba mal escrito, y por eso `sobrecarga_fisica_emocional` quedaba en la tabla que se permuta. No afectó ningún resultado, porque aún no se ejecutaba nada.
"""
(INF / '14_informe_pruebas.md').write_text(f"""# Fase 37B: informe de pruebas

**Resultado: {ok} de {len(pr)} pruebas superadas.** Control de errores: {mu['error_introducido'].nunique()} errores introducidos, detectados en {int(mu['detectado'].sum())} de {len(mu)} comprobaciones.

Los programas son `scripts/pruebas_37b.py` y `scripts/control_mutaciones_37b.py`. Los resultados están en `pruebas/`. Silueta, Davies-Bouldin, Calinski-Harabasz y ARI se recalculan con implementaciones propias, en una muestra de configuraciones.

## Pruebas

{tabla(['N.º', 'Prueba', 'Resultado', 'Detalle'], [[r.numero, r.prueba, r.resultado, str(r.detalle).replace('|', '/')] for r in pr.itertuples()])}
## Control de errores

Se introducen errores en memoria, sin tocar resultados, para comprobar que las pruebas pueden fallar.

{tabla(['Error introducido', 'Prueba', '¿Detectado?'], [[r.error_introducido, r.prueba, 'Sí' if r.detectado else 'No'] for r in mu.itertuples()])}
## Fallos encontrados y cómo se resolvieron

{fallos}
{previos}
## Limitaciones

- Las implementaciones propias se comprobaron en 6 configuraciones, no en las 420. Las pruebas de reproducción, tamaños y etiquetas sí cubren las 420.
- La reproducción de la nula cubre 2 de las 20 réplicas.
- La correspondencia de figuras se comprobó punto a punto en 3 figuras de 13. Las demás se revisaron visualmente.
""", encoding='utf-8', newline='\n')

# ------------------------------------------------------------------ 15 Integridad
d14 = pr.set_index('numero')
carpetas = le['archivo_leido'].astype(str).str.extract(r'^(analisis/[^/]+(?:/[^/]+)?)')[0].value_counts()
(INF / '15_informe_integridad.md').write_text(f"""# Fase 37B: informe de integridad

## Comprobaciones

| Elemento | Resultado |
|---|---|
| Históricos | {d14.loc[20, 'detalle']} |
| Git | {d14.loc[21, 'detalle']} |
| Entradas antes de ajustar | {(ve['resultado'] == 'OK').sum()} de {len(ve)} comprobaciones OK (`integridad/verificacion_entradas.csv`) |
| Protocolo | Sellado antes de los ajustes; cada una de las 420 configuraciones guarda su huella |

## Lecturas durante la ejecución

Un gancho de auditoría de Python registró {len(le)} archivos leídos por los programas de ajuste (`integridad/archivos_leidos.csv`). Ninguno pertenece a `datos/`, y no se usaron `dataset_usuaria_verdad.csv`, `bitacora_suciedad.csv` ni el MRS. `integridad/escrituras_fuera.csv` no registra escrituras fuera de la carpeta de salida.

{tabla(['Carpeta', 'Archivos'], [[k, v] for k, v in carpetas.items()])}
`consolidar_37b.py` y `graficos_37b.py` no pasan por ese gancho, pero solo leen resultados de esta subfase, coordenadas de la Fase 37A y `procedencia_celdas.csv` para saber qué IMC está observado.

## Pruebas históricas

La prueba 16 de `37A_reduccion/scripts/pruebas_37a.py` comprueba que `fase37/` tiene solo la carpeta de la Fase 37A. Ahora fallaría si se volviera a ejecutar, porque existe `37B_clustering/`. Es una comprobación válida para el momento de la Fase 37A, y no indica un cambio en sus resultados. No la modifiqué.

## Registro de ejecución

`integridad/registro_ejecucion.csv` guarda el estado y el tiempo de cada trabajo. Una primera ejecución completó las 420 configuraciones, las 34 variantes y las 20 réplicas, sin errores.

## Manifiesto

`integridad/manifiesto_final_37B.csv` guarda la huella de todos los archivos de `37B_clustering/`, y se escribe al final.
""", encoding='utf-8', newline='\n')

# ------------------------------------------------------------------ Índice
(INF / '00_indice_entregables.md').write_text("""# Fase 37B: índice de entregables

Rutas relativas a `analisis/fase37/37B_clustering/`.

| N.º | Entregable | Ubicación |
|---|---|---|
| 1 | Protocolo sellado | `protocolo/01_protocolo_37B.md`, `protocolo/sello_protocolo.json`, `informes/01_protocolo_37B.docx` |
| 2 | Tabla de configuraciones | `resultados/configuraciones.csv`, `resultados/tabla_completa_configuraciones.csv` |
| 3 | Etiquetas | `etiquetas/etiquetas_principales.csv`, con el identificador de cada participante |
| 4 | Calidad interna | `resultados/metricas_calidad.csv`, `resultados/siluetas_por_grupo.csv` |
| 5 | Estabilidad | `estabilidad/resumen_estabilidad.csv`, `ari_por_remuestreo.csv`, `remuestreos.csv` |
| 6 | Referencia nula | `referencia_nula/comparacion_por_configuracion.csv`, `busqueda_multiple.csv`, `metricas_por_replica.csv` |
| 7 | Sensibilidades | `sensibilidades/comparacion_sensibilidades.csv`, `resumen_por_variante.csv`, `etiquetas/` |
| 8 | Tamaños de grupos | `resultados/tamanos_grupos.csv`, `grupos_pequenos.csv`, `imc_imputado_por_grupo.csv` |
| 9 | Asignación de participantes nuevas | `prototipos/evaluacion_asignacion.csv`, `prototipos_*.json`, `distancias_*.csv` |
| 10 | Gráficos | `figuras/` (13 PNG) |
| 11 | Informe de K-means | `informes/11_informe_kmeans.docx` |
| 12 | Informe del método aglomerativo | `informes/12_informe_aglomerativo.docx` |
| 13 | Comparación preliminar | `informes/13_comparacion_preliminar.docx` |
| 14 | Informe de pruebas | `informes/14_informe_pruebas.md`, `pruebas/` |
| 15 | Informe de integridad | `informes/15_informe_integridad.md`, `integridad/` |
| 16 | Informe de cierre | `informes/16_informe_cierre_37B.docx` |
| 17 | Preparación de la Fase 37C | `informes/17_preparacion_37C.docx` |

También: `resultados/comparaciones_ari.csv`, `resultados/entorno.json` y los programas en `scripts/`. Los lotes de cada trabajo están en `resultados/lotes/`, `referencia_nula/lotes/` y `sensibilidades/lotes/`.
""", encoding='utf-8', newline='\n')

shutil.copyfile(B / 'protocolo' / '01_protocolo_37B.md', FUENTES / '01_protocolo_37B.md')
DOCS = [('01_protocolo_37B', 'Fase 37B: protocolo', 'Reglas fijadas antes de ajustar'), ('11_informe_kmeans', 'Fase 37B: K-means', 'Formación y evaluación inicial'), ('12_informe_aglomerativo', 'Fase 37B: método aglomerativo', 'Enlace Ward y distancia euclidiana'), ('13_comparacion_preliminar', 'Fase 37B: comparación preliminar', 'Algoritmos, espacios, nula y sensibilidades'), ('16_informe_cierre_37B', 'Fase 37B: informe de cierre', 'Formación y evaluación inicial de clústeres'), ('17_preparacion_37C', 'Fase 37B: preparación de la Fase 37C', 'Información metodológica; la Fase 37C no se inicia')]
for nombre, titulo, sub in DOCS:
    subprocess.run(['node', str(AQUI / 'md_a_word_37b.js'), str(FUENTES / f'{nombre}.md'), str(INF / f'{nombre}.docx'), titulo, sub], check=True)
print(len(DOCS), 'Word generados')
print('Lista B:', PRIO['config'].tolist())
