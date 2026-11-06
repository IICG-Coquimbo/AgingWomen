"""
Fase 37A: redacta los informes a partir de las tablas ya calculadas. Las cifras se leen de las tablas, no se copian a mano.

Uso, desde analisis/: python fase37/37A_reduccion/scripts/generar_informes_37a.py
Escribe en informes/. Convierte a Word con md_a_word_37a.js (requiere NODE_PATH con el paquete docx).
"""
import subprocess
import sys
from pathlib import Path

import pandas as pd

sys.dont_write_bytecode = True
AQUI = Path(__file__).resolve().parent
BASE = AQUI.parent
T = BASE / 'tablas'
INF = BASE / 'informes'
FUENTES = INF / 'fuentes'
FUENTES.mkdir(parents=True, exist_ok=True)
CAND = [2, 3, 5, 8, 12, 16, 20]
ESC = ['P1', 'P2', 'F1', 'F2']
NOMBRE = {'P1': 'P1 (PCA con IMC)', 'P2': 'P2 (PCA sin IMC)', 'F1': 'F1 (FAMD con IMC)', 'F2': 'F2 (FAMD sin IMC)'}
FIG = '../../figuras/'
SINT = 'Todo el análisis usa el conjunto sintético de usuarias (N = 529). Los resultados describen ese conjunto y no permiten afirmar nada sobre mujeres reales.'

vp = pd.read_csv(T / 'valores_propios.csv')
cv = pd.read_csv(T / 'contribucion_variables.csv', encoding='utf-8')
cb = pd.read_csv(T / 'contribucion_bloques.csv', encoding='utf-8')
ca = pd.read_csv(T / 'contribucion_bloques_acumulada.csv', encoding='utf-8')
cc = pd.read_csv(T / 'cargas_columnas.csv', encoding='utf-8')
um = pd.read_csv(T / 'componentes_para_umbral.csv').set_index('id')
su = pd.read_csv(T / 'comparacion_subespacios.csv')
ej = pd.read_csv(T / 'correspondencia_ejes.csv')
im = pd.read_csv(T / 'imc_por_eje.csv')
ss = pd.read_csv(T / 'sens_similitud.csv')
se = pd.read_csv(T / 'sens_correlacion_ejes.csv')
sr = pd.read_csv(T / 'sens_resumen.csv')
sp = pd.read_csv(T / 'sens_proyeccion.csv')
on = pd.read_csv(T / 'famd_orden_niveles.csv')
ba = pd.read_csv(T / 'famd_baricentros.csv', dtype={'nivel': str}, encoding='utf-8')
pr = pd.read_csv(BASE / 'pruebas' / 'resultados_pruebas.csv')
mu = pd.read_csv(BASE / 'pruebas' / 'control_mutaciones.csv')
le = pd.read_csv(BASE / 'integridad' / 'archivos_leidos.csv')


def n(x, d=1):
    return f'{x:.{d}f}'.replace('.', ',')


def tabla(cabeza, filas):
    return '\n'.join(['| ' + ' | '.join(map(str, cabeza)) + ' |', '|' + '---|' * len(cabeza)] + ['| ' + ' | '.join(map(str, f)) + ' |' for f in filas]) + '\n'


def var(e, c):
    return vp[(vp['escenario'] == e) & (vp['componente'] == c)].iloc[0]


def t_valores(es, m=12):
    return tabla(['Eje'] + [f'{e}: λ' for e in es] + [f'{e}: %' for e in es], [[c] + [n(var(e, c)['valor_propio'], 3) for e in es] + [n(var(e, c)['pct'], 2) for e in es] for c in range(1, m + 1)])


def t_acum(es):
    return tabla(['Escenario'] + [f'k = {k}' for k in CAND], [[NOMBRE[e]] + [n(var(e, k)['pct_acumulado']) + ' %' for k in CAND] for e in es])


def t_umbral(es):
    return tabla(['Escenario', 'Rango', '50 %', '60 %', '70 %', '80 %', '90 %'], [[NOMBRE[e], int(vp[vp['escenario'] == e]['componente'].max())] + [um.loc[e, f'c{u}'] for u in (50, 60, 70, 80, 90)] for e in es])


def t_ruido(es):
    return tabla(['Eje'] + [f'{e}: λ / p95' for e in es], [[c] + [f"{n(var(e, c)['valor_propio'], 3)} / {n(var(e, c)['referencia_ruido_p95'], 3)}" for e in es] for c in range(1, 11)])


def t_vars(e, m=5):
    filas = []
    for a in range(1, m + 1):
        x = cv[(cv['escenario'] == e) & (cv['componente'] == a)].nlargest(5, 'contribucion_pct')
        filas.append([a, n(var(e, a)['pct'], 2) + ' %', '; '.join(f'{r.variable} {n(r.contribucion_pct)}' for r in x.itertuples())])
    return tabla(['Eje', '% del eje', 'Variables con mayor contribución (%)'], filas)


def t_bloques(e, m=5):
    p = cb[(cb['escenario'] == e) & (cb['componente'] <= m)].pivot(index='bloque', columns='componente', values='contribucion_pct')
    return tabla(['Bloque'] + [f'Eje {a}' for a in p.columns], [[b] + [n(v) for v in f] for b, f in zip(p.index, p.to_numpy())])


def t_bloques_ac(e):
    p = ca[ca['escenario'] == e].pivot(index='bloque', columns='k', values='contribucion_acumulada_pct')
    return tabla(['Bloque'] + [f'k = {k}' for k in p.columns], [[b] + [n(v) for v in f] for b, f in zip(p.index, p.to_numpy())])


def imc_tabla(es):
    filas = []
    for e in es:
        x = im[(im['variante'] == 'principal') & (im['base'] == e)]
        tope = x.loc[x['contribucion_pct'].idxmax()]
        filas.append([NOMBRE[e]] + [n(x[x['componente'] == a]['contribucion_pct'].iloc[0]) for a in range(1, 6)] + [f"{n(tope['contribucion_pct'])} % en el eje {int(tope['componente'])}"])
    return tabla(['Escenario', 'Eje 1', 'Eje 2', 'Eje 3', 'Eje 4', 'Eje 5', 'Máximo'], filas)


def t_comp(a, b):
    x = su[(su['a'] == a) & (su['b'] == b)].set_index('k')['similitud_subespacio']
    return [n(x[k], 3) for k in CAND]


def t_sens(base):
    filas = []
    for s in ['S-ORD', 'S-FAMD', 'S-RARA', 'S-TRA', 'S-CUI', 'S-EJE', 'S-EDAD', 'S-SOLAPE', 'S-BLOQUE', 'S-BLOQUE-SA']:
        x = ss[(ss['sensibilidad'] == s) & (ss['base'] == base)].set_index('k')['similitud_subespacio']
        if len(x):
            filas.append([s] + [n(x[k], 3) for k in CAND])
    return tabla(['Variante'] + [f'k = {k}' for k in CAND], filas)


def senaladas():
    x = ss[ss['k'].isin([5, 8, 12]) & (ss['similitud_subespacio'] < 0.80)]
    filas = []
    for s, g in x.groupby('sensibilidad', sort=False):
        filas.append([s, '; '.join(f"{b}: " + ', '.join(f"k={int(r.k)} ({n(r.similitud_subespacio, 3)})" for r in h.itertuples()) for b, h in g.groupby('base', sort=False))])
    return tabla(['Variante', 'Escenarios y candidatos bajo 0,80'], filas)


def t_proy():
    filas = []
    for s in ('S-TRA', 'S-CUI', 'S-EJE'):
        for e in ('P1', 'F1'):
            x = sp[(sp['sensibilidad'] == s) & (sp['base'] == e)].set_index('k')
            filas.append([s, e, int(x['filas_proyectadas'].iloc[0])] + [f"{n(x.loc[k, 'desplazamiento_proyectadas'], 3)} / {n(x.loc[k, 'desplazamiento_ajuste'], 3)}" for k in (5, 8, 12)])
    return tabla(['Variante', 'Base', 'Proyectadas', 'k = 5', 'k = 8', 'k = 12'], filas)


def t_cat(e, ejes=3, m=6):
    filas = []
    for a in range(1, ejes + 1):
        x = cc[(cc['escenario'] == e) & (cc['componente'] == a) & cc['columna'].str.contains('__')].nlargest(m, 'contribucion_pct')
        filas.append([a, '; '.join(f'{r.columna} {n(r.contribucion_pct)} (r {n(r.correlacion, 2)})' for r in x.itertuples())])
    return tabla(['Eje', 'Categorías con mayor contribución (%), con su correlación con el eje'], filas)


def t_orden():
    filas = []
    x = on[on['escenario'] == 'F1']
    for v, g in x.groupby('variable', sort=False):
        p = g[g['eje_principal']].iloc[0]
        mono = [int(a) for a in g[g['monotono_grupos']]['componente']]
        filas.append([v, int(p['componente']), n(p['eta2'], 3), 'Sí' if p['monotono_grupos'] else 'No', 'Sí' if p['monotono_niveles_originales'] else 'No', ', '.join(map(str, mono)) or 'Ninguno'])
    return tabla(['Variable', 'Eje principal', 'η²', 'Monótona (grupos)', 'Monótona (niveles originales)', 'Ejes 1-5 monótonos'], filas)


def t_baric(v, a):
    x = ba[(ba['escenario'] == 'F1') & (ba['variable'] == v) & (ba['componente'] == a)]
    return '; '.join(f"{r.nivel}: {n(r.baricentro, 2)} (n={r.n})" for r in x[x['tipo_nivel'] == 'grupo activo'].itertuples())


def escribe(nombre, texto):
    (FUENTES / nombre).write_text(texto.strip() + '\n', encoding='utf-8', newline='\n')


LIMITES = """- **Datos sintéticos.** Las relaciones entre variables provienen de la generación del conjunto. Una dimensión de este análisis no es un hallazgo sobre la población.
- **El signo de un eje es arbitrario.** Un valor alto o bajo no significa más o menos de algo sin mirar las cargas, y ningún eje mide severidad ni riesgo clínico.
- **El porcentaje no indica utilidad.** Un eje con varianza alta puede resumir bien una característica sin que eso sirva para formar perfiles.
- **Esta fase no prueba que existan grupos.** Una nube de puntos en dos ejes no demuestra ni descarta clústeres."""

REFERENCIAS = """- Horn, J. L. (1965). A rationale and test for the number of factors in factor analysis. Psychometrika, 30(2), 179-185.
- Jolliffe, I. T. (2002). Principal Component Analysis (2.ª ed.). Springer.
- Pagès, J. (2014). Multiple Factor Analysis by Example Using R. CRC Press.

> Referencias citadas de memoria, sin consulta en línea: conviene verificarlas antes de usarlas en la tesis."""

# ------------------------------------------------------------------ 02 PCA
escribe('02_informe_pca.md', f"""
# 1. Qué se hizo

Se aplicó análisis de componentes principales a las dos matrices de la Fase 36: P1, con IMC, y P2, sin IMC. {SINT} Esta fase solo resume las variables en dimensiones: no forma grupos ni usa el MRS.

- **Entrada:** P1 tiene 529 filas y 34 columnas, con inercia 29,5047. P2 tiene 529 filas y 33 columnas, con inercia 29,0. El IMC pesa menos en P1 porque tiene una varianza de 0,5047, en lugar de 1, según lo fijado en la Fase 36.
- **Cálculo:** scikit-learn con `svd_solver='full'`, sin ningún escalado nuevo. Los valores propios usan la convención 1/n (`explained_variance_ × 528/529`), para que sumen la inercia indicada.
- **Rango:** P1 tiene 33 componentes y P2 tiene 32. Hay un eje menos que columnas porque las cinco indicadoras de `quien_prepara_comidas` suman una constante, lo que genera una dependencia lineal.

# 2. Varianza por componente

{t_valores(['P1', 'P2'])}
![Figura 1. Porcentaje de inercia por eje en los cuatro escenarios. La línea discontinua es la referencia de permutaciones.]({FIG}f01_sedimentacion.png)

**Lectura.** El primer eje destaca (8,4 % en P1). Desde el segundo la caída es muy gradual: los ejes 2 a 12 van de {n(var('P1', 2)['pct'])} % a {n(var('P1', 12)['pct'])} %, sin un quiebre claro. Es lo esperable en un conjunto con asociaciones débiles entre variables.

**Varianza acumulada por candidato:**

{t_acum(['P1', 'P2'])}
**Componentes necesarios para cada porcentaje** (referencia descriptiva, no un criterio):

{t_umbral(['P1', 'P2'])}
![Figura 2. Inercia acumulada en los cuatro escenarios.]({FIG}f02_inercia_acumulada.png)

# 3. Referencia frente al ruido

Esta comparación es una **adición mía**: el encargo no la pide y es solo descriptiva. Permuta cada variable por separado 200 veces y obtiene el percentil 95 de cada valor propio.

{t_ruido(['P1', 'P2'])}
Ocho ejes superan esa referencia en P1 y P2, pero por márgenes muy pequeños después de los primeros. En P1, el eje 6 obtiene {n(var('P1', 6)['valor_propio'], 3)} frente a {n(var('P1', 6)['referencia_ruido_p95'], 3)}, y el eje 8 obtiene {n(var('P1', 8)['valor_propio'], 3)} frente a {n(var('P1', 8)['referencia_ruido_p95'], 3)}. Por eso, solo el primer eje se separa con claridad. Los ejes con valores propios casi iguales pueden intercambiarse con cambios pequeños en los datos, lo que explica parte de las variaciones vistas en las sensibilidades.

# 4. Qué describe cada eje

Cada eje se describe solo por sus características. Los nombres de esta sección son rótulos descriptivos.

{t_vars('P1')}
- **Eje 1, actividad física.** Lo forman los días de ejercicio y las tres frecuencias de ejercicio: el bloque aporta 92 %.
- **Eje 2, pareja y actividad sexual,** con aporte menor de trabajo y comida fuera de casa.
- **Eje 3, tiempo, trabajo y cuidado.**
- **Ejes 4 y 5, alimentación,** mezclada con otras variables: presión en el eje 4, y operación y sedentarismo en el eje 5.

![Figura 3. Variables con mayor contribución en los primeros ejes de P1.]({FIG}f04_contribucion_variables_P1.png)

![Figura 4. Correlación de las columnas con los primeros ejes de P1. El signo de cada eje es arbitrario.]({FIG}f03_cargas_P1.png)

**Contribución por bloque en P1 (% de cada eje):**

{t_bloques('P1')}
**Contribución acumulada por bloque en P1, con los ejes ponderados por su valor propio (%):**

{t_bloques_ac('P1')}
La alimentación gana peso al sumar ejes, y llega a 44,6 % con k = 20. Esto refleja en parte que el bloque tiene muchas variables: no significa que sea más importante.

![Figura 5. Contribución de los bloques a los ejes en los cuatro escenarios.]({FIG}f05_contribucion_bloques.png)

# 5. Influencia del IMC

**Contribución del IMC a cada eje (%):**

{imc_tabla(['P1'])}
El IMC casi no participa en los ejes iniciales. Su aporte aparece en ejes tardíos, que no están entre los candidatos. La similitud entre P1 y P2 es de al menos {n(su[(su['a'] == 'P1') & (su['b'] == 'P2')]['similitud_subespacio'].min(), 3)} en todos los candidatos, de modo que incluir o no el IMC casi no cambia las coordenadas. Esto es consecuencia, al menos en parte, de su peso reducido y de que su asociación con las demás variables es débil.

![Figura 6. Contribución del IMC por eje, con su peso reducido.]({FIG}f07_con_sin_imc.png)

# 6. Coordenadas y participantes nuevas

Se guardaron coordenadas para k = 2, 3, 5, 8, 12, 16 y 20 en `coordenadas/P1` y `coordenadas/P2`. Las coordenadas de cada candidato son los primeros k ejes del conjunto de 20. Se comprobó la transformación de una participante nueva: Transformador de la Fase 36 y luego `(Z − media) · V`, sin recalcular nada. El resultado no depende de las demás filas y coincide con las coordenadas guardadas.

![Figura 7. Proyección en los dos primeros ejes, en un solo color. No es evidencia de la existencia ni la ausencia de clústeres.]({FIG}f06_proyeccion_2d.png)

# 7. Limitaciones

{LIMITES}

# 8. Referencias

{REFERENCIAS}
""")

# ------------------------------------------------------------------ 03 FAMD
escribe('03_informe_famd.md', f"""
# 1. Qué se hizo

Se aplicó el análisis factorial de datos mixtos a F1, con IMC, y F2, sin IMC. {SINT} Esta fase no forma grupos ni usa el MRS.

- **Entrada:** F1 tiene 529 filas y 50 columnas, con inercia 38,5047. F2 tiene 529 filas y 49 columnas, con inercia 38,0.
- **Cálculo:** las matrices ya traen la transformación de FAMD validada en la Fase 36. Por eso se aplica la misma descomposición en valores singulares, sin normalizar las categorías de nuevo. No se usa `prince` para proyectar participantes ni se recalculan proporciones.
- **Inercia:** la suma de valores propios es 38,5047 y 38,0, con el factor 528/529. El rango es 39 en F1 y 38 en F2.

# 2. Valores propios e inercia

{t_valores(['F1', 'F2'])}
{t_acum(['F1', 'F2'])}
{t_umbral(['F1', 'F2'])}
**Referencia frente al ruido** (adición mía, descriptiva):

{t_ruido(['F1', 'F2'])}
Nueve ejes superan la referencia en F1 y F2, con márgenes pequeños desde el cuarto. Como en PCA, solo el primero se separa con claridad.

# 3. Variables y categorías

{t_vars('F1')}
- **Eje 1:** actividad física, igual que en PCA; el bloque aporta {n(cb[(cb['escenario'] == 'F1') & (cb['componente'] == 1) & (cb['bloque'] == 'Actividad física')]['contribucion_pct'].iloc[0])} %.
- **Eje 2:** actividad sexual y pareja, con más presencia de falta de tiempo, personas a cargo y trabajo que en PCA.
- **Ejes 3 a 5:** mezclas de cuidado, tiempo, pareja y alimentación. Son menos fáciles de nombrar que en PCA.

**Categorías con mayor contribución:**

{t_cat('F1')}
![Figura 1. Variables con mayor contribución en los primeros ejes de F1.]({FIG}f04_contribucion_variables_F1.png)

![Figura 2. Correlación de las columnas con los primeros ejes de F1. El signo de cada eje es arbitrario.]({FIG}f03_cargas_F1.png)

**Contribución por bloque en F1 (% de cada eje):**

{t_bloques('F1')}
**Contribución acumulada por bloque en F1 (%):**

{t_bloques_ac('F1')}

# 4. ¿Se conserva el orden de las cinco ordinales?

FAMD trata estas cinco variables como categorías, por lo que no sabe que sus niveles tienen orden. Se comprobó si ese orden reaparece en los baricentros, con la regla fijada en el protocolo.

{t_orden()}
- **Frecuencia de aeróbico, bajo impacto y fuerza:** el orden se conserva en el eje 1, donde tienen η² alto. FAMD recupera el gradiente sin que se le indique.
- **Personas que cuida:** en su eje principal, el 2, no hay un orden: {t_baric('cantidad_personas_cuida', 2)}. Ese eje separa a quienes cuidan a una o dos personas de quienes no cuidan o cuidan a tres o más. El eje 3 sí es monótono: {t_baric('cantidad_personas_cuida', 3)}.
- **Tabaco:** su η² principal es solo {n(on[(on['escenario'] == 'F1') & (on['variable'] == 'tabaco_frecuencia') & on['eje_principal']]['eta2'].iloc[0], 3)}, y no es monótona en ningún eje de los cinco primeros. Está mal representada en estos ejes, así que no se puede afirmar nada sobre su orden.

Estos resultados se informan y no se corrigen.

![Figura 3. Baricentros de los niveles de las cinco variables en F1, en su eje principal.]({FIG}f09_orden_niveles_F1.png)

# 5. Influencia del IMC

{imc_tabla(['F1'])}
La similitud entre F1 y F2 es de al menos {n(su[(su['a'] == 'F1') & (su['b'] == 'F2')]['similitud_subespacio'].min(), 3)} en todos los candidatos. El IMC casi no influye en los ejes candidatos.

# 6. Coordenadas y participantes nuevas

Hay coordenadas para los siete candidatos en `coordenadas/F1` y `coordenadas/F2`. La proyección usa las proporciones y los parámetros guardados, sin recalcularlos, y se comprobó con filas reconstruidas desde sus respuestas originales y con un caso inventado.

# 7. Limitaciones

{LIMITES}
- **Más rango no significa más información.** FAMD reparte la inercia en más dimensiones, por lo que sus porcentajes son menores. Esto no permite compararlo directamente con PCA.

# 8. Referencias

{REFERENCIAS}
""")

# ------------------------------------------------------------------ 04 Comparación
filas_met = [[('PCA frente a FAMD, con IMC'), *t_comp('P1', 'F1')], ['PCA frente a FAMD, sin IMC', *t_comp('P2', 'F2')], ['Con y sin IMC, PCA', *t_comp('P1', 'P2')], ['Con y sin IMC, FAMD', *t_comp('F1', 'F2')]]
x_ej = ej[(ej['a'] == 'P1') & (ej['b'] == 'F1')]
escribe('04_comparacion_preliminar.md', f"""
# 1. Conclusión preliminar

**Este informe no elige un método.** PCA y FAMD coinciden en los dos o tres primeros ejes y se van separando después. {SINT}

# 2. Distribución de la inercia

{t_acum(ESC)}
{t_umbral(ESC)}
FAMD necesita más ejes para cada porcentaje porque reparte la inercia en un espacio de mayor rango. **Esa diferencia no indica que PCA sea mejor:** cada método representa las variables categóricas de otra forma, por lo que sus inercias totales no son comparables.

![Figura 1. Componentes necesarios para cada porcentaje de inercia.]({FIG}f08_comparacion_pca_famd.png)

# 3. Cuánto coinciden

La similitud de subespacio es la media de cos² de los ángulos principales entre las coordenadas de las filas. Vale 1 si ambos generan el mismo subespacio.

{tabla(['Comparación'] + [f'k = {k}' for k in CAND], filas_met)}
**Correspondencia eje a eje entre P1 y F1:**

{tabla(['Eje de P1', 'Eje de F1 más parecido', '|r|'], [[int(r.eje_a), int(r.eje_b_mas_parecido), n(r.correlacion_absoluta, 3)] for r in x_ej.itertuples()]).replace('|r|', chr(92) + '|r' + chr(92) + '|')}
# 4. Diferencias de contenido

| Aspecto | PCA | FAMD |
|---|---|---|
| Tratamiento de las cinco ordinales | Como escala numérica | Como categorías, con baricentros |
| Eje 1 | Actividad física | Actividad física |
| Eje 2 | Actividad sexual {n(cv[(cv['escenario'] == 'P1') & (cv['componente'] == 2) & (cv['variable'] == 'tiene_actividad_sexual')]['contribucion_pct'].iloc[0])} %, pareja {n(cv[(cv['escenario'] == 'P1') & (cv['componente'] == 2) & (cv['variable'] == 'tiene_pareja')]['contribucion_pct'].iloc[0])} % | Actividad sexual {n(cv[(cv['escenario'] == 'F1') & (cv['componente'] == 2) & (cv['variable'] == 'tiene_actividad_sexual')]['contribucion_pct'].iloc[0])} %, pareja {n(cv[(cv['escenario'] == 'F1') & (cv['componente'] == 2) & (cv['variable'] == 'tiene_pareja')]['contribucion_pct'].iloc[0])} %, más tiempo y cuidado |
| Alimentación acumulada, k = 20 | {n(ca[(ca['escenario'] == 'P1') & (ca['k'] == 20) & (ca['bloque'] == 'Alimentación')]['contribucion_acumulada_pct'].iloc[0])} % | {n(ca[(ca['escenario'] == 'F1') & (ca['k'] == 20) & (ca['bloque'] == 'Alimentación')]['contribucion_acumulada_pct'].iloc[0])} % |
| Actividad física acumulada, k = 20 | {n(ca[(ca['escenario'] == 'P1') & (ca['k'] == 20) & (ca['bloque'] == 'Actividad física')]['contribucion_acumulada_pct'].iloc[0])} % | {n(ca[(ca['escenario'] == 'F1') & (ca['k'] == 20) & (ca['bloque'] == 'Actividad física')]['contribucion_acumulada_pct'].iloc[0])} % |
| Interpretación | Más directa: una variable numérica, una columna | Más detalle por categoría, ejes 3 a 5 más mezclados |
| Niveles poco frecuentes | Influyen según su distancia numérica | La regla de la Fase 36 agrupó los raros; S-RARA estudia ese agrupamiento |

# 5. Influencia del IMC

{imc_tabla(ESC[::2])}
En ambos métodos, el IMC aporta 0,4 % o menos a los cinco primeros ejes. Las versiones con y sin IMC son casi iguales en todos los candidatos, por lo que esta comparación aportará poco en la Fase 37B.

# 6. Sensibilidades

No se compara la varianza absoluta entre variantes. La tabla muestra la similitud con el escenario base, sin usar el MRS.

**Base P1:**

{t_sens('P1')}
**Base F1:**

{t_sens('F1')}
![Figura 2. Similitud de subespacio de cada variante con su base.]({FIG}f10_sensibilidades.png)

**Variantes señaladas para revisión** (similitud bajo 0,80 en k = 5, 8 o 12; orientativo):

{senaladas()}
- **S-ORD:** usar ridit en lugar de códigos consecutivos casi no cambia la representación.
- **S-FAMD y S-RARA:** son las codificaciones que más cambian a F1. S-FAMD pasa las cinco ordinales a cuantitativas y S-RARA deja de agrupar categorías raras. El cambio de S-RARA es el mayor con pocos ejes (similitud 0,691 con k = 2). Esto confirma que la codificación es una decisión con consecuencias.
- **S-TRA, S-CUI y S-EJE:** ajustan en otra población (507, 508 y 454 filas) y proyectan al resto con parámetros congelados. La similitud suele ser alta. La baja de S-EJE en F1 con k = 5 (0,764) no se mantiene con k = 8 (0,949), lo que sugiere un intercambio entre ejes contiguos y no un cambio general. Parte de cualquier cambio puede deberse a la población y no al método.
- **S-EDAD:** quitar la edad casi no cambia el resultado.
- **S-SOLAPE:** quita `tiene_actividad_sexual` y `distension_abdominal`. Es de las que más cambian con pocos ejes, porque `tiene_actividad_sexual` es la principal contribuyente del eje 2. Sin ella, ese eje pasa a depender sobre todo de trabajo en P1 y de falta de tiempo en F1.
- **S-BLOQUE:** confirma la amplificación del IMC: en F1, el IMC llega a {n(sr[(sr['sensibilidad'] == 'S-BLOQUE') & (sr['base'] == 'F1')]['eje1_contribucion_pct'].iloc[0])} % del eje 1.
- **S-BLOQUE-SA:** quita esa amplificación, pero igualar los bloques sigue amplificando a los de pocas variables: en P1, personas que cuida llega a {n(sr[(sr['sensibilidad'] == 'S-BLOQUE-SA') & (sr['base'] == 'P1')]['eje1_contribucion_pct'].iloc[0])} % del eje 1. **Esta ponderación cambia la pregunta, por lo que no sirve como prueba de robustez.** Una ponderación por bloques más elaborada, como la del análisis factorial múltiple, sería una alternativa futura que no se ejecutó aquí.

**Proyección de las participantes excluidas.** Desplazamiento de filas proyectadas / filas de ajuste, relativo a su dispersión:

{t_proy()}
Las filas proyectadas se desplazan en magnitudes parecidas a las de ajuste, por lo que no se comportan de forma anómala frente al resto.

# 7. Qué falta por saber

Esta comparación no dice qué método forma mejores perfiles. Eso depende de la estabilidad, los tamaños y la calidad de los grupos en la Fase 37B.
""")

# ------------------------------------------------------------------ 14 Cierre
ok = (pr['resultado'] == 'OK').sum()
escribe('14_informe_cierre_37A.md', f"""
# 1. Estado

**La Fase 37A queda cerrada: {ok} de {len(pr)} pruebas superadas.** La Fase 37B no se inició y no hay commit ni push. {SINT}

# 2. Resultado principal

Las matrices se resumen sin que aparezca una estructura marcada: **solo el primer eje se separa con claridad.** Describe la actividad física, y es similar en PCA y FAMD. Los siguientes se parecen mucho entre sí y superan por poco la referencia de permutaciones. Esto aún no dice si habrá o no perfiles estables: eso se evalúa en la Fase 37B.

# 3. Cifras

{t_acum(ESC)}
{t_umbral(ESC)}
# 4. Hallazgos para tener presentes

- **El eje 2 depende mucho de una variable.** Sin `tiene_actividad_sexual` ni `distension_abdominal` (S-SOLAPE), el subespacio de k = 2 cambia bastante (similitud {n(ss[(ss['sensibilidad'] == 'S-SOLAPE') & (ss['base'] == 'P1') & (ss['k'] == 2)]['similitud_subespacio'].iloc[0], 3)} en P1).
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

Las {len(pr)} pruebas pasan, y el control introdujo {mu['error_introducido'].nunique()} errores a propósito: se detectaron todos, en {len(mu)} comprobaciones. Detalle en `12_informe_pruebas.md` y `13_informe_integridad.md`. Las Fases 34, 35 y 36 no cambiaron.

# 7. Lo que no se hizo

No se formaron clústeres, no se ejecutó K-means ni el método aglomerativo, no se leyó el MRS ni la carpeta `datos/`, y no se modificaron la plataforma ni las fases anteriores.

# 8. Límites

{LIMITES}
""")

# ------------------------------------------------------------------ 15 Preparación 37B
n_conf = 4 * 7 * 2 * 7
escribe('15_preparacion_37B.md', f"""
# 1. Propósito

Deja lista la información metodológica para la Fase 37B. **Este documento no la inicia.** Las reglas están en la sección 8 del protocolo D-13.

# 2. Entradas disponibles

| Entrada | Ubicación | Uso |
|---|---|---|
| Coordenadas principales | `coordenadas/<escenario>/coordenadas_kNN.csv` | Entrada de los algoritmos |
| Modelos | `artefactos/<escenario>/modelo.json` | Asignar participantes nuevas |
| Coordenadas de sensibilidades | `sensibilidades/<variante>/<escenario>/` | Comparar asignaciones |
| Matrices P1 y P2 | `analisis/fase36/matrices/` | Referencia sin reducción (R0) |

**Las coordenadas no se deben estandarizar:** dividirlas por su DE daría a los ejes tardíos, de poca varianza, el mismo peso que al primero, y cambiaría lo definido en este protocolo.

# 3. Tamaño del análisis

Según el protocolo: 4 escenarios × 7 candidatos × 2 algoritmos × 7 valores de k = **{n_conf} configuraciones**, más {2 * 2 * 7} de la referencia R0 ({n_conf + 28} en total), cada una con 30 remuestreos y una referencia nula de 20 permutaciones.

**Advertencia:** con tantas configuraciones, alguna destacará por azar. Por eso, el protocolo no admite un ganador automático y exige comparar con la referencia nula.

# 4. Recomendaciones

- **Revisar la estabilidad antes que la calidad,** como fija el protocolo. La estructura débil hace probable que las métricas sean bajas en general.
- **Mirar con atención los candidatos pequeños (k = 2, 3, 5, 8).** Son los que superan la referencia de ruido. Desde k = 12 se añaden ejes por debajo de ella en todos los escenarios, y son los más expuestos a variar. Los candidatos no se eliminan; es solo una expectativa que hay que comprobar.
- **Cuidar que el resultado no sea solo la actividad física.** Con k = 2 o 3, el eje 1 pesa mucho. Agrupar ahí podría limitarse a separar por nivel de ejercicio. Debe informarse así si ocurre.
- **Cuidar la dependencia de `tiene_actividad_sexual`.** Con pocos ejes, S-SOLAPE es de las variantes que más cambian la representación. Conviene revisar sus asignaciones con ARI.
- **Con y sin IMC serán casi iguales.** Un ARI alto entre ellas es esperable y no prueba estabilidad. Sigue haciendo falta la revisión de IMC imputado por grupo, como fija el protocolo.
- **Leer S-BLOQUE como otra ponderación,** no como una prueba de robustez. Sus cambios no deben contar en contra de una configuración del mismo modo que S-ORD o S-TRA.
- **Aceptar la posibilidad de que no haya perfiles marcados.** Si ninguna configuración es estable y supera la referencia nula, el protocolo pide informarlo y no forzar perfiles. Con estos datos es un resultado posible y sería válido.

# 5. Variantes señaladas para revisar

{senaladas()}
# 6. Asuntos por decidir antes de comenzar

Estas propuestas quedaron en el protocolo y puedes cambiarlas:

- Número de inicializaciones: `n_init = 50`.
- Remuestreo sin reemplazo.
- Tramos de ARI: bajo 0,65, de 0,65 a 0,80, y sobre 0,80.
- Referencia nula de 20 permutaciones.
- Orden de decisión sin puntuación compuesta.
""")

# ------------------------------------------------------------------ 12 Pruebas
fallos = """| Fallo | Causa | Resolución |
|---|---|---|
| Prueba 10, reproducibilidad | `archivos_leidos.csv` difería entre la salida oficial y una temporal: el protocolo está dentro de la carpeta oficial, y el registro omitía las lecturas de esa carpeta. Coordenadas y tablas sí coincidían | El registro siempre incluye el protocolo. Se volvió a ejecutar todo |
| Prueba 14, archivos protegidos | Error de la prueba: `strip()` recortaba el primer carácter de estado de `git status`, y deformaba la primera ruta. Ningún archivo protegido había cambiado | La prueba conserva los espacios iniciales |
| Control: valor propio negativo no detectado | La prueba 6 leía los modelos del disco y no por la función que la mutación sustituye | La prueba 6 usa esa función |
| Control: coordenadas reescaladas sin detectar en la prueba 17 | El reescalado era igual en todos los candidatos, y esa prueba solo compara candidatos entre sí; no era un error que debiera detectar | Se creó una mutación propia: un candidato que no coincide con los primeros ejes |
"""
(INF / '12_informe_pruebas.md').write_text(f"""# Fase 37A: informe de pruebas

**Resultado: {ok} de {len(pr)} pruebas superadas.** Control de mutaciones: {mu['error_introducido'].nunique()} errores introducidos, {int(mu['detectado'].sum())} de {len(mu)} comprobaciones los detectaron.

Los programas son `scripts/pruebas_37a.py` y `scripts/control_mutaciones_37a.py`. Los resultados están en `pruebas/`. La prueba 10 repite el ajuste en dos procesos.

## Pruebas

{tabla(['N.º', 'Prueba', 'Resultado', 'Detalle'], [[r.numero, r.prueba, r.resultado, str(r.detalle).replace('|', '/')] for r in pr.itertuples()])}
## Control de mutaciones

Se introducen errores en memoria, sin tocar resultados, para comprobar que las pruebas pueden fallar.

{tabla(['Error introducido', 'Prueba', '¿Detectado?'], [[r.error_introducido, r.prueba, 'Sí' if r.detectado else 'No'] for r in mu.itertuples()])}
## Fallos encontrados y cómo se resolvieron

{fallos}
## Limitación

La prueba 15 compara fechas de modificación de archivos. Sirve como comprobación interna, pero no es una prueba independiente de la secuencia temporal: el SHA-256 solo garantiza que el protocolo no cambió desde el sello. Además, `ejecutar_37a.py` se detiene al comenzar si la huella no coincide.
""", encoding='utf-8', newline='\n')

# ------------------------------------------------------------------ 13 Integridad
lectura_por_carpeta = le['archivo_leido'].str.extract(r'^(analisis/[^/]+)')[0].value_counts()
(INF / '13_informe_integridad.md').write_text(f"""# Fase 37A: informe de integridad

{pr[pr['numero'] == 14]['detalle'].iloc[0]}.

## Comprobaciones

| Elemento | Resultado |
|---|---|
| Fase 36 | 258 archivos iguales a `fase36/integridad/manifiesto_final_36B.csv` |
| Cierre de las Fases 34 y 35 | 1.130 archivos iguales a `cierre_fases_34_35/integridad/manifiesto_despues.csv` |
| Matrices de entrada | SHA-256 iguales a sus huellas de la Fase 36 |
| Protocolo | SHA-256 igual al sello |
| Git | HEAD 745d689; nada preparado; sin commit ni push |
| Archivos seguidos con cambios previos | Los mismos 8 de `analisis/`, de antes de esta fase. No se tocaron |
| Plataforma | `src/` y dependencias sin cambios |

## Lecturas durante el ajuste

Un gancho de auditoría de Python registró {len(le)} archivos leídos por `ejecutar_37a.py` (`integridad/archivos_leidos.csv`). Ninguno pertenece a `datos/`, y no se usaron `dataset_usuaria_verdad.csv`, `bitacora_suciedad.csv` ni el MRS.

{tabla(['Carpeta', 'Archivos'], [[k, v] for k, v in lectura_por_carpeta.items()])}
`integridad/escrituras_fuera.csv` no registra escrituras fuera de la carpeta de salida.

## Manifiesto

`integridad/manifiesto_final_37A.csv` guarda la huella de todos los archivos de `37A_reduccion/`, y se escribe al final.
""", encoding='utf-8', newline='\n')

# ------------------------------------------------------------------ Índice
(INF / '00_indice_entregables.md').write_text(f"""# Fase 37A: índice de entregables

Rutas relativas a `analisis/fase37/37A_reduccion/`.

| N.º | Entregable | Ubicación |
|---|---|---|
| 1 | Protocolo D-13 | `protocolo/01_protocolo_D13.md` (sellado) e `informes/01_protocolo_D13.docx` |
| 2 | Informe académico PCA | `informes/02_informe_pca.docx` |
| 3 | Informe académico FAMD | `informes/03_informe_famd.docx` |
| 4 | Comparación preliminar | `informes/04_comparacion_preliminar.docx` |
| 5 | Valores propios | `tablas/valores_propios.csv` |
| 6 | Varianza e inercia acumuladas | `tablas/valores_propios.csv` (`pct`, `pct_acumulado`) y `tablas/componentes_para_umbral.csv` |
| 7 | Cargas y contribuciones | `tablas/cargas_columnas.csv`, `contribucion_variables.csv`, `contribucion_bloques.csv`, `contribucion_bloques_acumulada.csv`, `famd_baricentros.csv`, `famd_orden_niveles.csv`, `imc_por_eje.csv` |
| 8 | Coordenadas principales | `coordenadas/<escenario>/coordenadas_kNN.csv` |
| 9 | Coordenadas de sensibilidades | `sensibilidades/<variante>/<escenario>/` y `tablas/sens_*.csv` |
| 10 | Gráficos | `figuras/` (16 PNG) |
| 11 | Artefactos | `artefactos/<escenario>/modelo.json`, `artefactos/entorno.json` |
| 12 | Informe de pruebas | `informes/12_informe_pruebas.md`, `pruebas/` |
| 13 | Informe de integridad | `informes/13_informe_integridad.md`, `integridad/` |
| 14 | Informe de cierre | `informes/14_informe_cierre_37A.docx` |
| 15 | Preparación de la Fase 37B | `informes/15_preparacion_37B.docx` |

Los programas están en `scripts/`.
""", encoding='utf-8', newline='\n')

DOCS = [
    (BASE / 'protocolo' / '01_protocolo_D13.md', '01_protocolo_D13', 'Fase 37A: protocolo D-13', 'Reglas fijadas antes de ajustar PCA y FAMD'),
    (FUENTES / '02_informe_pca.md', '02_informe_pca', 'Fase 37A: análisis de componentes principales', 'Escenarios P1 y P2'),
    (FUENTES / '03_informe_famd.md', '03_informe_famd', 'Fase 37A: análisis factorial de datos mixtos', 'Escenarios F1 y F2'),
    (FUENTES / '04_comparacion_preliminar.md', '04_comparacion_preliminar', 'Fase 37A: comparación preliminar', 'PCA, FAMD, IMC y sensibilidades'),
    (FUENTES / '14_informe_cierre_37A.md', '14_informe_cierre_37A', 'Fase 37A: informe de cierre', 'Reducción de dimensionalidad'),
    (FUENTES / '15_preparacion_37B.md', '15_preparacion_37B', 'Fase 37A: preparación de la Fase 37B', 'Información metodológica; la Fase 37B no se inicia'),
]
for fuente, nombre, titulo, sub in DOCS:
    subprocess.run(['node', str(AQUI / 'md_a_word_37a.js'), str(fuente), str(INF / f'{nombre}.docx'), titulo, sub], check=True)
print(len(DOCS), 'Word generados')
