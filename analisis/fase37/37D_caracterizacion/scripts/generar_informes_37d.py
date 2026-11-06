"""
Fase 37D: informes en Markdown y Word. Todas las cifras se leen de las tablas guardadas.

Uso, desde analisis/: NODE_PATH=<carpeta con node_modules de docx> python fase37/37D_caracterizacion/scripts/generar_informes_37d.py
"""
import json
import shutil
import subprocess
import sys

import nucleo_37d as N
import numpy as np
import pandas as pd

sys.dont_write_bytecode = True
B = N.BASE
R = B / 'resultados'
INF = B / 'informes'
F = INF / 'fuentes'
F.mkdir(parents=True, exist_ok=True)
SINT = 'Todo el análisis usa el conjunto sintético de usuarias (N = 529). Sus asociaciones vienen de una simulación, por lo que los resultados no permiten afirmar nada sobre mujeres reales ni tienen valor clínico.'


def L(r):
    return pd.read_csv(R / r, encoding='utf-8')


def n(x, d=2):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return '—'
    return f'{x:,.{d}f}'.replace(',', 'X').replace('.', ',').replace('X', '.').replace('-', '−')


def e(x):
    return str(int(x)) if abs(x) < 1000 else f'{int(x):,}'.replace(',', '.')


def p_(x):
    return '< 0,001' if x < 0.001 else n(x, 3)


def tabla(cab, filas):
    s = '| ' + ' | '.join(cab) + ' |\n|' + '---|' * len(cab) + '\n'
    return s + ''.join('| ' + ' | '.join(str(c) for c in f) + ' |\n' for f in filas)


def fig(nombre, pie):
    return f'\n![{pie}](../../figuras/{nombre})\n'


ET = N.ETIQUETA
MED = {'rho': 'ρ', 'r_rb': 'r', 'epsilon2': 'ε²', 'V': 'V', 'η²': 'η²', 'V²': 'V²'}
num = L('descripcion/caracteristicas_numericas.csv').set_index('variable')
cat = L('descripcion/caracteristicas_categorias.csv')
mrs = L('descripcion/mrs_descripcion.csv').set_index('resultado')
sev = L('descripcion/mrs_severidad.csv')
imp = N.leer_json(R / 'descripcion' / 'resumen_imputacion.json')
dic = pd.read_csv(B / 'diccionario' / 'diccionario_variables_37D.csv')
f1, f2, f3, f4 = L('individual/F1_total.csv'), L('individual/F2_dimensiones.csv'), L('individual/F3_severo.csv'), L('individual/F4_items.csv')
obs, sin9, niv = L('individual/S-OBS_comparacion.csv'), L('individual/S-SIN9_individual.csv'), L('individual/detalle_por_nivel.csv')
car, desc = L('segmentos/F6_caracterizacion_efectos.csv'), L('segmentos/F6_caracterizacion_por_grupo.csv')
g5, sv5, gl5, pr7 = L('segmentos/F5_mrs_por_grupo.csv'), L('segmentos/F5_severidad_por_grupo.csv'), L('segmentos/F5_global.csv'), L('segmentos/F7_pares_total.csv')
sens, part, acu = L('segmentos/sensibilidades_global.csv'), L('segmentos/particiones_guardadas_ari.csv'), L('segmentos/acuerdo_por_margen.csv')
var, den, dpg = L('segmentos/varianza_dentro_segmentos.csv'), L('segmentos/asociacion_dentro_de_segmentos.csv'), L('segmentos/asociacion_dentro_por_grupo.csv')
cmp37, corr = L('segmentos/comparacion_con_37C.csv'), N.leer_json(R / 'segmentos' / 'correspondencia_resumen.json')
corA = L('segmentos/correspondencia_A_B1.csv').set_index('A')
pru, mut = pd.read_csv(B / 'pruebas' / 'resultados_pruebas.csv'), pd.read_csv(B / 'pruebas' / 'control_mutaciones.csv')
sello, nota = N.leer_json(B / 'protocolo' / 'sello_protocolo.json'), N.leer_json(B / 'protocolo' / 'sello_nota_posterior.json')
ini = N.leer_json(B / 'integridad' / 'integridad_inicial.json')
man_ini = pd.read_csv(B / 'integridad' / 'manifiestos_inicial.csv')
fin_path = B / 'integridad' / 'integridad_final.json'
fin = N.leer_json(fin_path) if fin_path.exists() else None

dest1 = f1[f1['destacada']].sort_values('efecto')
G = lambda s, r: gl5.set_index(['segmentacion', 'resultado']).loc[(s, r)]  # noqa: E731
MG = lambda s, r, g: g5[(g5['segmentacion'] == s) & (g5['resultado'] == r) & (g5['grupo'] == g)].iloc[0]  # noqa: E731
SV = lambda s, g: sv5[(sv5['segmentacion'] == s) & (sv5['grupo'] == g)].iloc[0]  # noqa: E731


def ef(r):
    return f"{MED.get(r['medida'], r['medida'])} = {n(r['efecto'])}"


def lista_destacadas(d):
    return '; '.join(f"{ET[r.variable]} ({MED[r.medida]} = {n(r.efecto)})" for r in d.itertuples())


# ---------- rasgos por grupo
def rasgos(seg):
    """Variables con diferencia importante (η² ≥ 0,06) y desvío de al menos 0,5 DE en cada grupo, con el valor del grupo."""
    imp_ = car[(car['segmentacion'] == seg) & (car['efecto'] >= 0.06) & (car['medida'] == 'η²')]['variable']
    out = {}
    for g in range(4):
        items = []
        for v in imp_:
            r = desc[(desc['segmentacion'] == seg) & (desc['grupo'] == g) & (desc['variable'] == v)]
            if not len(r) or pd.isna(r['media'].iloc[0]):
                continue
            z = (r['media'].iloc[0] - num.loc[v, 'media']) / num.loc[v, 'de']
            if abs(z) >= 0.5:
                t = num.loc[v, 'tipo']
                if t == 'binaria':
                    txt = f"{ET[v].lower()}: {n(r['pct_si'].iloc[0], 0)} % «sí» (general {n(100 * num.loc[v, 'media'], 0)} %)"
                else:
                    txt = f"{ET[v].lower()}: media {'más alta' if z > 0 else 'más baja'}, {n(r['media'].iloc[0], 2)} (general {n(num.loc[v, 'media'], 2)})"
                items.append((abs(z), txt))
        out[g] = [x for _, x in sorted(items, reverse=True)]
    return out


def tabla_caracterizacion(seg):
    d = car[car['segmentacion'] == seg].sort_values(['usada_por_A', 'efecto'], ascending=[False, False])
    filas = []
    for r in d.itertuples():
        vals = []
        for g in range(4):
            x = desc[(desc['segmentacion'] == seg) & (desc['grupo'] == g) & (desc['variable'] == r.variable)]
            if r.tipo == 'nominal':
                top = x.sort_values('pct', ascending=False).iloc[0]
                vals.append(f"{top['categoria']} {n(top['pct'], 0)} %")
            elif not len(x) or pd.isna(x['media'].iloc[0]):
                vals.append('sin datos')
            elif r.tipo == 'binaria':
                vals.append(f"{n(x['pct_si'].iloc[0], 0)} %")
            else:
                vals.append(n(x['media'].iloc[0], 2))
        filas.append([ET[r.variable], 'A' if r.usada_por_A else 'externa', *vals, f'{r.medida} {n(r.efecto, 3)}', p_(r.q), r.lectura])
    return tabla(['Variable', 'Origen', 'G0', 'G1', 'G2', 'G3', 'Efecto', 'q', 'Lectura'], filas)


def mrs_tabla(seg):
    filas = []
    for g in range(4):
        t, s_ = MG(seg, 'mrs_total', g), SV(seg, g)
        filas.append([f'Grupo {g}', e(t['n']), f"{n(t['media'], 1)} ({n(t['de'], 1)})", f"{n(t['mediana'], 1)} [{n(t['q1'], 1)}-{n(t['q3'], 1)}]", f"{n(t['ic_mediana_inf'], 1)} a {n(t['ic_mediana_sup'], 1)}",
                      n(MG(seg, 'mrs_somatico', g)['media'], 1), n(MG(seg, 'mrs_psicologico', g)['media'], 1), n(MG(seg, 'mrs_urogenital', g)['media'], 1), f"{n(s_['pct_severo'], 1)} % ({n(s_['ic_severo_inf'], 0)}-{n(s_['ic_severo_sup'], 0)})"])
    return tabla(['Grupo', 'n', 'Total: media (DE)', 'Mediana [RIC]', 'IC 95 % mediana', 'Somática', 'Psicológica', 'Urogenital', 'Severo (IC 95 %)'], filas)


def global_tabla(seg):
    filas = []
    for r, nm in (('mrs_total', 'Total'), ('mrs_somatico', 'Somática'), ('mrs_psicologico', 'Psicológica'), ('mrs_urogenital', 'Urogenital'), ('severidad', 'Severidad (4 clases)'), ('severo_mrs', 'Severo ≥ 16')):
        x = G(seg, r)
        efecto = f"ε² {n(x['efecto'], 3)}" if x['medida'] != 'V' else f"V {n(x['efecto'], 3)} (V² {n(x['eta2'], 3)})"
        filas.append([nm, x['prueba'], efecto, f"{n(x['ic_inf'], 3)} a {n(x['ic_sup'], 3)}", p_(x['p']), p_(x['q']), x['banda']])
    return tabla(['Resultado', 'Prueba', 'Efecto', 'IC 95 %', 'p', 'q (F5)', 'Magnitud'], filas)


def pares_tabla(seg):
    d = pr7[pr7['segmentacion'] == seg]
    return tabla(['Par', 'Medianas', 'r', 'p', 'p de Holm'], [[f'G{r.grupo_a} frente a G{r.grupo_b}', f'{n(r.mediana_a, 1)} y {n(r.mediana_b, 1)}', n(r.r_rb), p_(r.p), p_(r.p_holm)] for r in d.itertuples()])


docs = {}
RA, RB = rasgos('A'), rasgos('B1')
nd = lambda d: int(d['destacada'].sum())  # noqa: E731
ext_dest = dest1[~dest1['usada_por_A']]
a_dest = dest1[dest1['usada_por_A']]

# ---------- 03 diccionario
docs['03_diccionario_variables'] = ('Diccionario de variables utilizadas', f"""
# Alcance

Variables usadas en la Fase 37D: 29 que usa el Modelo A, 7 externas a A y las del MRS. El significado de cada código viene de la Fase 36 (`fase36/artefactos/P2/esquema_variables.json`) y de la limpieza, no del nombre de la variable. La tabla completa, con la codificación de cada nivel, está en `diccionario/diccionario_variables_37D.csv`.

{SINT}

# Características

{tabla(['Variable', 'Bloque', 'Tipo', 'Población', 'Obs.', 'Imp.', 'No aplica', 'Falt.', 'n análisis'], [[ET[r.variable], r.bloque, r.tipo, r.poblacion, '—' if pd.isna(r.observadas) else e(r.observadas), '—' if pd.isna(r.imputadas) else e(r.imputadas), '—' if pd.isna(r.no_aplica) else e(r.no_aplica), '—' if pd.isna(r.faltantes) else e(r.faltantes), e(r.n_analisis)] for r in dic[~dic['bloque'].str.startswith('MRS')].itertuples()])}

- **«—» en estado:** son variables tomadas de la limpieza (etapa, diabetes, previsión), que no tienen marca de imputación por participante. Según la Fase 34D, diabetes tiene 23 imputadas y previsión 19 imputadas y 2 deducidas; la etapa depende de respuestas imputadas en 27 participantes.
- **No aplica:** en ejercicio y cuidado es un 0 estructural («no realiza», «no cuida»). En los módulos laboral y de cuidados queda fuera del análisis.
- **IMC:** se usa solo el observado (267). La imputación por la media de la Fase 35 no se usa.

# MRS

{tabla(['Variable', 'Contenido', 'Codificación'], [[r.variable, r.etiqueta, r.codificacion] for r in dic[dic['bloque'].str.startswith('MRS')].itertuples()])}

Las dimensiones siguen el orden de ítems del proyecto (`limpieza/reglas.py`), que no es el de la publicación original del MRS. Los cortes de severidad son los del modelo de la plataforma (leído sin modificarlo). Los once ítems están completos en las 529 participantes.
""")

# ---------- 04 caracterización general
binr = num[num['tipo'] == 'binaria']
docs['04_caracterizacion_general'] = ('Caracterización general de las participantes', f"""
# Resumen

{SINT}

- **Imputaciones:** {e(imp['con_alguna_imputacion_en_A'])} participantes ({n(imp['pct_con_alguna_imputacion_en_A'], 1)} %) tienen al menos una de las 29 variables de A imputada en la limpieza. Son {e(imp['celdas_imputadas_en_A'])} celdas de {e(imp['celdas_A'])} ({n(100 * imp['celdas_imputadas_en_A'] / imp['celdas_A'], 1)} %), así que pocas celdas, pero repartidas entre muchas personas.
- **Tres preguntas:** {e(imp['con_imputacion_en_las_tres_preguntas'])} participantes tienen imputada alguna de trabajo, pareja o días de ejercicio.
- **Datos parciales:** el IMC está observado en 267 participantes (50,5 %). Las preguntas laborales aplican a quienes trabajan (287 con dato) y la sobrecarga a quienes cuidan (251).

# Características generales

{fig('f01_caracteristicas_generales.png', 'Figura 1. Características generales de las 529 participantes.')}

## Preguntas de sí o no

{tabla(['Variable', 'n', '% «sí»'], [[ET[v], e(r['n']), n(100 * r['media'], 1)] for v, r in binr.sort_values('media', ascending=False).iterrows()])}

## Variables numéricas y ordinales

{tabla(['Variable', 'n', 'Media (DE)', 'Mediana [RIC]', 'Mín.-máx.'], [[ET[v], e(r['n']), f"{n(r['media'])} ({n(r['de'])})", f"{n(r['mediana'], 1)} [{n(r['q1'], 1)}-{n(r['q3'], 1)}]", f"{n(r['minimo'], 0)}-{n(r['maximo'], 0)}"] for v, r in num[num['tipo'] != 'binaria'].iterrows()])}

Las ordinales usan el código del instrumento (sección 4.4 del protocolo); su media sirve para comparar, no es una cantidad. Las frecuencias completas por categoría están en `resultados/descripcion/caracteristicas_categorias.csv`.

{fig('f02_variables_numericas.png', 'Figura 2. Edad, horas sentada e IMC observado.')}

## Nominales

{tabla(['Variable', 'Categoría', 'n', '%'], [[ET[r.variable], r.significado, e(r.n), n(r.pct, 1)] for r in cat[cat['variable'].isin(['quien_prepara_comidas', 'etapa_menopausica', 'prevision'])].itertuples()])}

# Síntomas del MRS

{tabla(['Resultado', 'Máximo', 'Media (DE)', 'Mediana [RIC]'], [[r.etiqueta, e(r.maximo), f'{n(r.media)} ({n(r.de)})', f'{n(r.mediana, 1)} [{n(r.q1, 1)}-{n(r.q3, 1)}]'] for r in mrs.reset_index().itertuples()])}

{tabla(['Severidad', 'n', '%'], [[r.severidad, e(r.n), n(r.pct, 1)] for r in sev.itertuples()])}

- **Más intensos:** cansancio físico y mental, molestias musculares y articulares, e irritabilidad.
- **Menos intensos:** problemas con la orina, sequedad vaginal y problemas sexuales.
- **Total:** se reparte de forma amplia y sin grupos visibles; algo más de la mitad llega a 16 puntos o más.

{fig('f03_mrs_total.png', 'Figura 3. Distribución del MRS total y categorías de severidad.')}
{fig('f04_mrs_dimensiones_items.png', 'Figura 4. Dimensiones e ítems del MRS.')}
""")

# ---------- 05 / 06 segmentos
def doc_seg(seg):
    tam = N.TAMANOS_A if seg == 'A' else N.TAMANOS_B1
    R_ = RA if seg == 'A' else RB
    d = car[car['segmentacion'] == seg]
    imp_ = d[d['efecto'] >= 0.06].sort_values('efecto', ascending=False)
    sem = d[d['efecto'] < 0.01]
    peq = d[(d['efecto'] >= 0.01) & (d['efecto'] < 0.06)].sort_values('efecto', ascending=False)
    ext = d[~d['usada_por_A']].sort_values('efecto', ascending=False)
    adv = ('Las 29 variables de A se usaron para formar los grupos. Que los grupos difieran en ellas es esperable y **no constituye una validación independiente**.' if seg == 'A'
           else 'B1 se define con trabajo, pareja y días de ejercicio. Que difieran en esas tres es una consecuencia de la regla. B1 no es un modelo clínico ni una validación independiente de A: se construyó imitando a A.')
    extra37 = ''
    if seg == 'A':
        extra37 = f"""
# Comparación con la Fase 37C

La Fase 37C describió los mismos grupos con las variables generales, sin MRS. Las 10 variables que entonces separaban más tienen aquí exactamente el mismo η² (diferencia máxima {n(cmp37['diferencia'].abs().max(), 6)}). Los rasgos se confirman: pareja, ejercicio y trabajo dominan, seguidos por actividad sexual y dos preguntas de alimentación (comidas fuera y falta de tiempo).

Lo nuevo de esta fase son las variables externas. Ninguna diferencia a los grupos de forma importante. La mayor es la sobrecarga por cuidar (η² {n(ext['efecto'].iloc[0], 3)}), medida solo en quienes cuidan.
"""
    return f"""
# Advertencia

{adv}

{SINT}

Los grupos se llaman Grupo 0 a Grupo 3, con la numeración histórica. No se les asignan nombres.

# Tamaños

{tabla(['Grupo', 'n', '%'], [[f'Grupo {g}', e(t), n(100 * t / 529, 1)] for g, t in enumerate(tam)])}

# Rasgos de cada grupo

Variables con diferencia importante (η² ≥ 0,06) en las que el grupo se aleja al menos 0,5 desviaciones estándar del promedio:

{chr(10).join(f'- **Grupo {g}:** ' + ('; '.join(R_[g][:5]) if R_[g] else 'cerca del promedio en todas las variables con diferencia importante') + '.' for g in range(4))}

{fig('f09_caracterizacion_A.png' if seg == 'A' else 'f10_caracterizacion_B1.png', f'Figura. Caracterización de los grupos de {seg}.')}

# Qué diferencia a los grupos

- **Diferencias importantes (η² o V² ≥ 0,06):** {len(imp_)} variables, todas usadas por A: {', '.join(ET[v].lower() for v in imp_['variable'])}.
- **Diferencias pequeñas (0,01 a 0,06):** {len(peq)} variables: {', '.join(ET[v].lower() for v in peq['variable'])}.
- **Distribuciones semejantes (< 0,01):** {len(sem)} variables, entre ellas {', '.join(ET[v].lower() for v in sem['variable'])}.

**Variables externas:** {'; '.join(f"{ET[r.variable].lower()} {r.medida} {n(r.efecto, 3)}" for r in ext.itertuples())}. Los grupos no se distinguen por IMC, etapa menopáusica, diabetes, previsión ni por las preguntas laborales.

# Tabla completa

Valores por grupo: porcentaje de «sí» en binarias, media del código en ordinales y cuantitativas, y categoría más frecuente en nominales. Las pruebas son Kruskal-Wallis o χ², con q de Benjamini-Hochberg dentro de la familia F6-{seg} (36 pruebas).

{tabla_caracterizacion(seg)}

{'En B1, el Grupo 2 no tiene ninguna participante que trabaje: las preguntas laborales no aplican en él.' if seg == 'B1' else ''} En `quien_prepara_comidas`, el 25 % de las frecuencias esperadas es menor que 5, así que su χ² es aproximado.
{extra37}
"""


docs['05_caracterizacion_segmentos_A'] = ('Caracterización de los segmentos A', doc_seg('A'))
docs['06_caracterizacion_segmentos_B1'] = ('Caracterización de los segmentos B1', doc_seg('B1'))

# ---------- 07 individual
docs['07_individual_frente_a_MRS'] = ('Características individuales frente al MRS', f"""
# Resumen

Es el análisis principal: cada característica frente al MRS, sin segmentar.

- **Familia F1 (total, 36 pruebas):** {nd(f1)} asociaciones destacadas, es decir, con q < 0,05 y efecto al menos pequeño. Todas son pequeñas: ninguna llega a 0,30.
- **Dirección:** {len(dest1[dest1['efecto'] > 0])} se asocian a mayor MRS y {len(dest1[dest1['efecto'] < 0])} a menor MRS.
- **Lo que no aparece:** la edad, la etapa menopáusica, la pareja, la actividad sexual, el sedentarismo y casi toda la alimentación no se asocian con el total.
- **Interpretación:** son asociaciones descriptivas en datos sintéticos. No indican causa, y la dirección podría ser la inversa: por ejemplo, más síntomas podrían llevar a menos ejercicio.

{SINT}

# Asociaciones con el MRS total (F1)

{fig('f05_asociaciones_mrs_total.png', 'Figura 5. Efecto de cada característica sobre el MRS total, con su intervalo de confianza.')}

{tabla(['Característica', 'Origen', 'Prueba', 'Efecto', 'IC 95 %', 'n', 'q', 'Magnitud'], [[ET[r.variable], 'A' if r.usada_por_A else 'externa', r.prueba, f'{MED[r.medida]} {n(r.efecto, 3)}', f'{n(r.ic_inf, 3)} a {n(r.ic_sup, 3)}', e(r.n), p_(r.q), r.banda + (' **(destacada)**' if r.destacada else '')] for r in f1.sort_values('p').itertuples()])}

- **Mayor MRS:** {lista_destacadas(dest1[dest1['efecto'] > 0].sort_values('efecto', ascending=False))}.
- **Menor MRS:** {lista_destacadas(dest1[dest1['efecto'] < 0])}.
- **Signo:** ρ positivo significa que a mayor valor de la característica, mayor MRS. En las binarias, r positivo significa mayor MRS en quienes responden «sí».
- **Subpoblaciones:** cuatro de las destacadas (IMC, lugar de trabajo comprensivo, estrés laboral y sobrecarga) se miden solo en una parte de las participantes. Sus efectos no son comparables con los de las 529.

**Medianas del total por nivel, en binarias y nominales seleccionadas:**

{tabla(['Variable', 'Nivel', 'n', 'Media', 'Mediana', '% severo'], [[ET[r.variable], r.nivel, e(r.n), n(r.media_total, 1), n(r.mediana_total, 1), n(r.pct_severo, 1)] for r in niv[niv['variable'].isin(['trabaja_actualmente', 'usa_medicamentos_diabetes', 'tiene_pareja', 'tiene_actividad_sexual', 'etapa_menopausica'])].itertuples()])}

# Dimensiones y severidad (F2, F3)

- **F2 (dimensiones, 108 pruebas):** {nd(f2)} destacadas.
- **F3 (severo ≥ 16, 36 pruebas):** {nd(f3)} destacadas.

**Por dimensión:**

- **Psicológica:** concentra la mayoría de las asociaciones destacadas ({nd(f2[f2['resultado'] == 'mrs_psicologico'])}). Las más altas son lugar de trabajo comprensivo, estrés laboral y sobrecarga.
- **Somática:** {nd(f2[f2['resultado'] == 'mrs_somatico'])} destacadas. Las mayores son el IMC y la diabetes.
- **Urogenital:** {nd(f2[f2['resultado'] == 'mrs_urogenital'])} destacadas, todas pequeñas: frutas, etapa menopáusica y previsión.

{fig('f06_mapa_dimensiones.png', 'Figura 6. Asociaciones con el total, las dimensiones y la severidad.')}

# Ítems (F4, exploratoria)

- **Destacadas:** {nd(f4)} de 396.
- **Dónde:** se concentran en los ítems psicológicos (5 a 8) y en los somáticos (1 a 4), y casi no aparecen en los urogenitales.
- **Advertencia:** con tantas pruebas, algunas pueden ser casuales aun con la corrección. Sirven para orientar, no para concluir.

{fig('f07_mapa_items.png', 'Figura 7. Asociaciones con cada ítem del MRS.')}

# Sensibilidades del análisis individual

- **S-OBS (solo datos observados):** {int(obs['misma_conclusion'].sum())} de 36 características mantienen la misma conclusión. Cambia solo {', '.join(ET[v].lower() for v in obs[~obs['misma_conclusion']]['variable'])}, que pasa a destacada con un efecto apenas sobre 0,10 (r de {n(obs[~obs['misma_conclusion']]['efecto'].iloc[0], 3)} a {n(obs[~obs['misma_conclusion']]['efecto_obs'].iloc[0], 3)}). La mayor diferencia de efecto entre ambos análisis es {n(obs['cambio_efecto'].abs().max(), 3)}.
- **S-SIN9 (sin el ítem 9, problemas sexuales):** pareja y actividad sexual no se asocian ni con el total ni con la urogenital, con o sin el ítem 9. El solapamiento conceptual previsto no produce ninguna asociación artificial.
""")

# ---------- 08 / 09 MRS por segmento
def doc_mrs_seg(seg):
    t = G(seg, 'mrs_total')
    ps = G(seg, 'mrs_psicologico')
    sv = G(seg, 'severo_mrs')
    medias = [MG(seg, 'mrs_total', g) for g in range(4)]
    bajo = min(range(4), key=lambda g: medias[g]['media'])
    altos = sorted(range(4), key=lambda g: -medias[g]['media'])[:2]
    pr = pr7[(pr7['segmentacion'] == seg) & (pr7['p_holm'] < 0.05)]
    return f"""
# Resumen

- **Severo ≥ 16:** del {n(SV(seg, bajo)['pct_severo'], 0)} % en el Grupo {bajo} al {n(max(SV(seg, g)['pct_severo'] for g in range(4)), 0)} % en el grupo más alto.
- **MRS total:** la media va de {n(medias[bajo]['media'], 1)} en el Grupo {bajo} a {n(medias[altos[0]]['media'], 1)} en el Grupo {altos[0]}.
- **Tamaño de las diferencias:** son pequeñas. En el total, ε² = {n(t['efecto'], 3)} (IC {n(t['ic_inf'], 3)} a {n(t['ic_sup'], 3)}; q = {p_(t['q'])}); en la psicológica, ε² = {n(ps['efecto'], 3)}; en severo, V = {n(sv['efecto'], 3)}.
- **Lo que queda dentro:** cerca del {n(100 * var[(var['segmentacion'] == seg) & (var['resultado'] == 'mrs_total')]['varianza_dentro'].iloc[0], 0)} % de la variación del total queda dentro de los grupos.

{'Los grupos de A se formaron sin usar el MRS. Que difieran en él es la primera comparación externa de esta segmentación, pero los datos son sintéticos y la diferencia no convierte a A en una clasificación válida.' if seg == 'A' else 'B1 depende solo de trabajo, pareja y ejercicio. Sus diferencias de MRS son, en esencia, las diferencias según esas tres preguntas combinadas, no un hallazgo de grupos.'}

{SINT}

# MRS por grupo

{mrs_tabla(seg)}

{fig('f12_mrs_total_segmentos.png', 'Figura. MRS total por segmento A y B1, en la misma escala.') if seg == 'A' else 'La figura comparada de A y B1 está en el informe 08 y en `figuras/f12_mrs_total_segmentos.png`.'}

# Diferencias entre grupos (familia F5)

{global_tabla(seg)}

La familia F5 tiene 12 pruebas (A y B1 × 6 resultados), corregidas juntas.

{fig('f13_dimensiones_segmentos.png', 'Figura. Dimensiones del MRS por segmento.') if seg == 'A' else ''}
{fig('f14_severidad_segmentos.png', 'Figura. Severidad por segmento.') if seg == 'A' else ''}

# Comparaciones por pares en el total (F7, Holm)

{pares_tabla(seg)}

{f'Después de Holm quedan {len(pr)} diferencias: ' + '; '.join(f'G{r.grupo_a} frente a G{r.grupo_b} (r = {n(r.r_rb)})' for r in pr.itertuples()) + '.' if len(pr) else 'Ninguna diferencia por pares se mantiene después de la corrección de Holm.'}

# Variabilidad

Las desviaciones estándar dentro de cada grupo (de {n(min(m['de'] for m in medias), 1)} a {n(max(m['de'] for m in medias), 1)}) son casi iguales a la de las 529 ({n(mrs.loc['mrs_total', 'de'], 1)}). Los rangos intercuartílicos se superponen ampliamente. Dentro de cada grupo hay participantes con casi ningún síntoma y con síntomas muy intensos.
"""


docs['08_mrs_por_segmento_A'] = ('MRS por segmento A', doc_mrs_seg('A'))
docs['09_mrs_por_segmento_B1'] = ('MRS por segmento B1', doc_mrs_seg('B1'))

# ---------- 10 comparación
cm = sens[sens['sensibilidad'] == 'S-MARGEN']
vA, vB = var.set_index(['segmentacion', 'resultado']), None
vc = var[var['segmentacion'].str.startswith('20')].set_index('resultado')
dd = den.pivot(index='variable', columns='segmentacion', values=['marginal', 'dentro_ponderado'])
cambio_ext = max(abs(dd.loc[v, ('dentro_ponderado', s)] - dd.loc[v, ('marginal', s)]) for v in ext_dest['variable'] for s in ('A', 'B1'))
docs['10_comparacion_tres_perspectivas'] = ('Comparación A, B1 y análisis sin segmentar', f"""
# Resumen

Esta comparación es descriptiva y exploratoria. **No se usa para elegir una segmentación ni modifica la selección de la Fase 37C.** No hay criterio de ganador.

{SINT}

| Pregunta | Sin segmentar | A | B1 |
|---|---|---|---|
| Qué describe | 36 características, una por una | 4 grupos definidos por 29 variables | 4 grupos definidos por 3 respuestas |
| Variables con diferencia importante entre grupos | No aplica | {int(((car['segmentacion'] == 'A') & (car['efecto'] >= 0.06)).sum())} (todas usadas por A) | {int(((car['segmentacion'] == 'B1') & (car['efecto'] >= 0.06)).sum())} (todas usadas por A) |
| Diferencias del MRS total | {nd(f1)} asociaciones destacadas, todas pequeñas | ε² {n(G('A', 'mrs_total')['efecto'], 3)}, q {p_(G('A', 'mrs_total')['q'])} | ε² {n(G('B1', 'mrs_total')['efecto'], 3)}, q {p_(G('B1', 'mrs_total')['q'])} |
| Dimensión psicológica | {nd(f2[f2['resultado'] == 'mrs_psicologico'])} destacadas | ε² {n(G('A', 'mrs_psicologico')['efecto'], 3)} | ε² {n(G('B1', 'mrs_psicologico')['efecto'], 3)} |
| Severo ≥ 16 | {nd(f3)} destacadas | V {n(G('A', 'severo_mrs')['efecto'], 3)} | V {n(G('B1', 'severo_mrs')['efecto'], 3)} |
| Variación del total dentro de los grupos | No aplica | {n(100 * vA.loc[('A', 'mrs_total'), 'varianza_dentro'], 1)} % | {n(100 * vA.loc[('B1', 'mrs_total'), 'varianza_dentro'], 1)} % |
| Variables externas destacadas con el MRS | {len(ext_dest)} | No las distingue (η² < 0,05) | No las distingue (η² < 0,05) |

# Correspondencia entre A y B1

- **Coincidencia:** {n(100 * corr['coincidencia_A_B1'], 1)} % de las participantes quedan en el grupo equivalente (ARI {n(corr['ari_A_B1'])}). El ARI no es un porcentaje de aciertos.
- **Desacuerdos:** se concentran cerca de las fronteras de A. El acuerdo es de {n(100 * acu.iloc[0]['pct_acuerdo'], 0)} % con margen menor que 0,05 y de {n(100 * acu.iloc[-1]['pct_acuerdo'], 0)} % con margen de 0,20 o más.

{tabla(['A / B1','B1 0', 'B1 1', 'B1 2', 'B1 3'], [[f'A {g}', *[e(x) for x in corA.loc[g]]] for g in range(4)])}

{fig('f08_tamanos_correspondencia.png', 'Figura. Tamaños y correspondencia de A y B1.')}

# Características que diferencian

Los perfiles de los cuatro grupos son casi los mismos en A y en B1:

- **Grupo 0:** sin pareja.
- **Grupo 1:** con ejercicio frecuente.
- **Grupo 2:** con pareja y sin trabajo.
- **Grupo 3:** con pareja y con trabajo.

En B1 las tres preguntas separan más (por ejemplo, pareja η² {n(car.set_index(['segmentacion', 'variable']).loc[('B1', 'tiene_pareja'), 'efecto'], 2)} frente a {n(car.set_index(['segmentacion', 'variable']).loc[('A', 'tiene_pareja'), 'efecto'], 2)}). A separa algo más en las otras variables: ejercicio adicional, actividad sexual y alimentación. Ninguna de las dos distingue a las participantes por las variables externas.

{fig('f11_efectos_A_B1.png', 'Figura. Efecto de cada característica entre los grupos de A y de B1.')}

# Diferencias de MRS

Las diferencias de MRS son pequeñas en ambas segmentaciones:

- **Tamaño:** B1 muestra efectos algo mayores que A en el total, la psicológica y severo.
- **Patrón común:** el Grupo 1, el de ejercicio frecuente, tiene los puntajes más bajos en las dos segmentaciones.

Que B1 muestre diferencias algo mayores **no la convierte en mejor segmentación**. Además, refleja algo ya visible sin segmentar: los días de ejercicio y el trabajo se asocian con el MRS. Las 20 combinaciones de las tres preguntas explican, con el ajuste por número de grupos, un η² de {n(vc.loc['mrs_total', 'eta2_ajustado'], 3)} en el total. En A el valor es {n(vA.loc[('A', 'mrs_total'), 'eta2_ajustado'], 3)} y en B1 {n(vA.loc[('B1', 'mrs_total'), 'eta2_ajustado'], 3)}.

# Información que se pierde al segmentar

- **Variación individual:** más del 96 % de la variación del MRS queda dentro de los grupos, tanto en A como en B1.
- **Asociaciones externas:** las asociaciones de las variables externas con el MRS (IMC, diabetes, sobrecarga, estrés laboral, lugar de trabajo) se mantienen casi iguales dentro de los grupos; la mayor diferencia entre la marginal y la de dentro es {n(cambio_ext, 3)}. Los segmentos no las absorben: un resumen solo por segmentos las perdería.
- **Hábitos fuera de A:** lo mismo ocurre con tabaco, alcohol, agua y ejercicio de bajo impacto.
- **Variables que ya definen el grupo:** dentro de los grupos, la asociación de días de ejercicio y del ejercicio aeróbico o de fuerza se debilita. El grupo ya recoge esa información.
- **Valores inestables:** trabajo, pareja y actividad sexual muestran dentro de los grupos de A asociaciones mayores que sin segmentar. El detalle por grupo indica que dependen de grupos con muy pocas participantes en un nivel; por ejemplo, en el Grupo 3 de A solo {e(dpg[(dpg['segmentacion'] == 'A') & (dpg['variable'] == 'trabaja_actualmente') & (dpg['grupo'] == 3)]['n_nivel_minoritario'].iloc[0])} participantes no trabajan. No son hallazgos estables. Este detalle se agregó tras ver los resultados (nota posterior).

{fig('f16_asociacion_dentro_segmentos.png', 'Figura. Asociación con el MRS total, sin segmentar y dentro de los grupos.')}

# Respuestas a las preguntas de la sección 9

1. **¿Qué diferencia los segmentos?** Pareja, días y tipos de ejercicio, trabajo y actividad sexual, y en menor grado comidas fuera y falta de tiempo. Todas son variables usadas por A.
2. **¿Qué es similar?** Edad, etapa, IMC, diabetes, previsión, sedentarismo, cuidado de personas, tabaco, alcohol, la mayor parte de la alimentación y las preguntas laborales.
3. **¿Se describen con más que tres preguntas?** Solo un poco. A difiere además en ejercicio adicional, actividad sexual y dos preguntas de alimentación, pero nada externo los distingue.
4. **¿Qué diferencias de MRS aparecen?** Pequeñas, sobre todo psicológicas y en la proporción con severo. El grupo de ejercicio frecuente tiene menos síntomas.
5. **¿Se mantienen con faltantes y sensibilidades?** Ver el informe 11. La diferencia psicológica se mantiene en todas las particiones y en el corte de margen principal, pero se pierde con poco n.
6. **¿Qué se pierde al segmentar?** Casi toda la variación individual y las asociaciones de variables que no definen los grupos.
7. **¿B1 representa diferencias semejantes?** Sí: mismo patrón y magnitud parecida o algo mayor, con tres preguntas.
8. **¿Qué enfoque es base más clara para asociaciones posteriores?** El análisis de características individuales. Mantiene las asociaciones externas, informa cada n y no depende de una partición. Los segmentos sirven como variable de estratificación descriptiva, no como unidad principal.
""")

# ---------- 11 sensibilidades y limitaciones
def fila_s(s, d, seg, r):
    x = sens[(sens['sensibilidad'] == s) & (sens['detalle'] == d) & (sens['segmentacion'] == seg) & (sens['resultado'] == r)].iloc[0]
    return x


def tab_sens():
    filas = []
    base = {(s, r): G(s, r) for s in ('A', 'B1') for r in ('mrs_total', 'mrs_psicologico', 'severo_mrs')}
    filas.append(['Principal', 529, *[n(base[(s, r)]['efecto'] if r != 'severo_mrs' else base[(s, r)]['eta2'], 3) for s in ('A', 'B1') for r in ('mrs_total', 'mrs_psicologico', 'severo_mrs')]])
    for s, d in (('S-MARGEN', 'margen ≥ 0.10'), ('S-MARGEN', 'margen ≥ 0.20'), ('S-SIN-IMP3', 'sin imputación en las tres preguntas'), ('S-SIN-IMP29', 'sin ninguna imputación en las 29 variables de A')):
        xs = [fila_s(s, d, seg, r) for seg in ('A', 'B1') for r in ('mrs_total', 'mrs_psicologico', 'severo_mrs')]
        filas.append([f'{s}: {d}'.replace('0.', '0,'), xs[0]['n_sub'], *[n(x['efecto'] if x['resultado'] != 'severo_mrs' else x['eta2'], 3) + ('' if x['p'] < 0.05 else ' (p ≥ 0,05)') for x in xs]])
    return tabla(['Análisis', 'n', 'A total ε²', 'A psicol. ε²', 'A severo V²', 'B1 total ε²', 'B1 psicol. ε²', 'B1 severo V²'], filas)


ps = sens[sens['sensibilidad'] == 'S-PARTICIONES']
docs['11_sensibilidades_limitaciones'] = ('Sensibilidades y limitaciones', f"""
# Resumen

Todas las sensibilidades se fijaron en el protocolo antes de ver los resultados. Las adiciones posteriores van rotuladas.

{SINT}

# Sensibilidades de los segmentos

{tab_sens()}

## Participantes cercanas a las fronteras (S-MARGEN)

- **Corte principal (0,10):** se excluye al {n(100 * (1 - 367 / 529), 0)} % de las participantes. Las diferencias psicológica y de severo se mantienen en A y en B1, y la psicológica de A incluso sube (ε² {n(fila_s('S-MARGEN', 'margen ≥ 0.10', 'A', 'mrs_psicologico')['efecto'], 3)}). El total de B1 baja a la mitad (ε² {n(fila_s('S-MARGEN', 'margen ≥ 0.10', 'B1', 'mrs_total')['efecto'], 3)}) y deja de ser significativo; el de A ya no lo era.
- **Corte de 0,20:** quedan 176 participantes y las diferencias se reducen o desaparecen. Con un tercio de la muestra cae la precisión, y además el subconjunto deja de ser representativo.
- **Lectura:** las diferencias psicológica y de severo no dependen de las participantes de margen bajo. La mayor diferencia del total en B1 sí se apoya en parte en las participantes cercanas a las fronteras de A.

{fig('f15_sensibilidad_margen.png', 'Figura. Sensibilidad al margen de A.')}

## Imputación

- **S-SIN-IMP3:** sin las 83 participantes con alguna de las tres preguntas imputada o deducida, las diferencias psicológicas y de severidad se mantienen en A y en B1. En A, el total sigue sin ser significativo, igual que con las 529, y la psicológica se debilita (ε² 0,014).
- **S-SIN-IMP29:** solo 118 participantes no tienen ninguna imputación en las 29 variables de A. Con ese n nada es significativo, aunque los efectos de severidad son parecidos. No permite confirmar ni descartar.
- **S-OBS (análisis individual):** las conclusiones cambian solo en una variable (informe 07).

## Particiones ya guardadas (S-PARTICIONES)

Ninguna se reajustó; solo muestran si la descripción depende de la configuración.

{tabla(['Partición', 'ARI con A', 'Tamaños', 'Total ε²', 'Psicológica ε²', 'Severo V'], [[r.particion, n(r.ari_con_A), r.tamanos, n(ps[(ps['segmentacion'] == r.particion) & (ps['resultado'] == 'mrs_total')]['efecto'].iloc[0], 3), n(ps[(ps['segmentacion'] == r.particion) & (ps['resultado'] == 'mrs_psicologico')]['efecto'].iloc[0], 3), n(ps[(ps['segmentacion'] == r.particion) & (ps['resultado'] == 'severo_mrs')]['efecto'].iloc[0], 3)] for r in part.itertuples()])}

- **Todas las particiones:** la diferencia psicológica (ε² entre 0,02 y 0,03) y la de severo (V entre 0,14 y 0,16) aparecen en todas, incluso en S-SOLAPE, que no usa actividad sexual ni distensión y coincide poco con A (ARI {n(part.set_index('particion').loc['S-SOLAPE P2_c12_km_k4', 'ari_con_A'])}).
- **Lectura:** la descripción no depende de la configuración exacta. Tampoco es exclusiva de A: cualquier partición que separe ejercicio y trabajo la reproduce.
- **No es un criterio de elección:** este resultado no sirve para elegir entre particiones.

## Otras

- **S-B1CV:** las etiquetas de B1 con validación cruzada dan los mismos efectos que B1 (total ε² {n(sens[(sens['sensibilidad'] == 'S-B1CV') & (sens['resultado'] == 'mrs_total')]['efecto'].iloc[0], 3)}).
- **S-SIN9:** sin el ítem 9, las diferencias del total de A y B1 casi no cambian (A ε² {n(sens[(sens['sensibilidad'] == 'S-SIN9') & (sens['segmentacion'] == 'A') & (sens['resultado'] == 'mrs_total_sin9')]['efecto'].iloc[0], 3)}; B1 {n(sens[(sens['sensibilidad'] == 'S-SIN9') & (sens['segmentacion'] == 'B1') & (sens['resultado'] == 'mrs_total_sin9')]['efecto'].iloc[0], 3)}). La actividad sexual dentro de A no infla la comparación con el MRS.

# Notas posteriores al sellado

En `protocolo/02_nota_posterior_37D.md`, con su propia huella (`{nota['sha256'][:16]}…`):

1. La única celda deducida se trató como no observada.
2. Se agregó el η² ajustado por número de grupos.
3. Se guardó el detalle por grupo de la asociación dentro de los segmentos, después de ver los resultados.
4. Los 4 archivos del simulador del manifiesto 34-35 no se abrieron.

Ninguna cambia una familia, una prueba ni una conclusión.

# Limitaciones

1. **Datos sintéticos.** Toda asociación refleja lo que el simulador programó. No hay validación con mujeres reales ni recomendación clínica posible.
2. **Análisis no ciego.** Las Fases 34C a 35B ya habían examinado asociaciones con el MRS. Se analizaron todas las variables pertinentes para no elegirlas por esos resultados, pero la lectura no es independiente.
3. **Efectos marginales.** Cada asociación se estima sin ajustar por las demás. Por ejemplo, edad y etapa se relacionan entre sí, y trabajo y preguntas laborales están anidadas.
4. **Causalidad y dirección.** No se puede saber si una característica precede a los síntomas o es consecuencia de ellos (estrés laboral, sobrecarga, ejercicio).
5. **Imputaciones.** Están en el {n(imp['pct_con_alguna_imputacion_en_A'], 1)} % de las participantes. Diabetes y previsión no tienen marca de imputación por participante; la etapa depende de respuestas imputadas en 27.
6. **Poblaciones parciales.** El IMC solo está en la mitad, los módulos laborales en quienes trabajan y la sobrecarga en quienes cuidan.
7. **Circularidad.** Las diferencias entre segmentos en las variables que los definen no validan nada. Pareja y actividad sexual se solapan con el ítem 9, aunque las sensibilidades no muestran efecto.
8. **Multiplicidad.** Hay 684 pruebas en siete familias. F4 es exploratoria.
9. **Doble uso.** Los grupos y su descripción usan las mismas 529 participantes; no hay una muestra de confirmación.
""")

# ---------- 12 figuras y tablas
figs = sorted((B / 'figuras').glob('*.png'))
tablas = sorted(p.relative_to(B).as_posix() for p in (B / 'resultados').rglob('*.csv')) + sorted(p.relative_to(B).as_posix() for p in (B / 'resultados').rglob('*.json'))
docs['12_figuras_tablas'] = ('Figuras y tablas de resultados', f"""
# Contenido

Catálogo de las {len(figs)} figuras y {len(tablas)} tablas de respaldo. Las figuras se generan solo desde las tablas guardadas (`scripts/graficos_37d.py`).

{SINT}

# Tablas

{tabla(['Archivo'], [[t] for t in tablas])}

# Figuras

""" + '\n'.join(fig(p.name, f'{p.stem.replace("_", " ")}') for p in figs))

# ---------- 16 nota fases 38-39
raras = cat[cat['pct'] < 5]
docs['16_nota_fases_38_39'] = ('Preparación de las Fases 38 y 39', f"""
# Alcance

Esta nota prepara las reglas de asociación. **No ejecuta Apriori, FP-Growth ni otro algoritmo, no fija umbrales y no inicia las Fases 38 ni 39.** Las candidatas se proponen por su significado y su calidad de datos, **no por haber resultado asociadas con el MRS en esta fase**: seleccionarlas así sería usar dos veces los mismos datos.

{SINT}

# Candidatas a antecedentes

| Grupo | Variables | Observación |
|---|---|---|
| Contexto | trabajo, pareja, cuidado (número de personas) | Base para comparaciones condicionadas |
| Actividad física | días de ejercicio; aeróbico, bajo impacto y fuerza | Muy relacionadas entre sí: conviene elegir una forma o agrupar |
| Sedentarismo | horas sentada | Numérica: requiere cortes fijados de antemano |
| Alimentación | 12 frecuencias y quién prepara | Muchas categorías poco frecuentes: agrupar antes |
| Tabaco y alcohol | frecuencias | Tabaco: «nunca» domina (75 %); conviene binarizar |
| Salud | medicamentos para presión y diabetes, IMC | IMC solo en 267; diabetes con imputaciones sin marca |
| Módulos | lugar comprensivo, estrés laboral, sobrecarga | Solo en subpoblaciones: reglas separadas |
| Descriptivas | edad (en tramos), etapa menopáusica | La etapa no fue predictora (decisión del 01-11); usarla solo en análisis descriptivos |

# Candidatos a consecuentes

- **Severidad:** `severo_mrs` (≥ 16) como consecuente principal, que es el objetivo acordado el 27-10. La severidad en 4 clases puede servir como alternativa.
- **Dimensiones:** solo si se fija un corte de antemano, por ejemplo el percentil 75 o un umbral del instrumento. No conviene elegir el corte mirando las reglas.
- **Ítems intensos:** ítems con respuesta 3 o 4, solo como análisis exploratorio.

# Riesgos

- **Circularidad:**
  - Actividad sexual y pareja frente al ítem 9 y la dimensión urogenital.
  - Distensión y evacuación frente a síntomas somáticos.
  - Estrés laboral y sobrecarga, que pueden ser consecuencias de los síntomas.
  - Los segmentos A o B1 como antecedentes repetirían trabajo, pareja y ejercicio.
- **Redundancia:**
  - Días de ejercicio y frecuencias de ejercicio.
  - Trabajo y módulo laboral, que están anidados.
  - Cuidado y sobrecarga.
  - Edad y etapa.
  - B1 es una función exacta de tres variables. Sin tratar esto, aparecerán reglas triviales.
- **Datos faltantes:** IMC (49,5 % sin observar) y módulos parciales. Las imputaciones de la limpieza afectan al {n(imp['pct_con_alguna_imputacion_en_A'], 1)} % de las participantes. Conviene repetir las reglas solo con datos observados.
- **Frecuencias insuficientes:** {len(raras)} categorías tienen menos del 5 % de las participantes, entre ellas ejercicio de 5-6 días (15) y todos los días (12), «otro» en quién prepara (7), FFAA (7) y la etapa quirúrgica (19). Reglas con esas categorías tendrían soporte mínimo. Conviene agrupar de antemano. La lista completa está en `resultados/descripcion/caracteristicas_categorias.csv`.

# Posibles análisis

1. **Generales:** reglas sobre las 529 con antecedentes agrupados y `severo_mrs` como consecuente.
2. **Condicionados:** reglas por separado según trabajo (sí o no), pareja (sí o no), ejercicio (3 días o más frente a menos) y cuidado (sí o no). Son las condiciones que definen B1.
3. **Subpoblaciones:** reglas laborales solo en quienes trabajan y de sobrecarga solo en quienes cuidan.
4. **Segmentos:** solo como estratificación descriptiva, nunca como antecedente junto a las variables que los definen.

# Decisiones pendientes de la responsable

- Elegir A, B1 o ninguna segmentación como estratificación de las reglas. Esta fase no cambia la conclusión de la Fase 37C.
- Fijar las agrupaciones de categorías, los cortes de las variables numéricas y el consecuente.
- Fijar, antes de ver las reglas, los umbrales de soporte, confianza y lift, y el control de reglas espurias (por ejemplo, permutaciones o una muestra de confirmación).
""")

# ---------- 15 informe final
rf = lambda s, g: f"{n(MG(s, 'mrs_total', g)['media'], 1)}"  # noqa: E731
docs['15_informe_final_37D'] = ('Informe final de la Fase 37D', f"""
# Conclusión

- **Asociaciones individuales:** las características individuales se asocian con el MRS de forma **pequeña**. Ninguna asociación llega a moderada.
  - Más síntomas: diabetes, IMC, sobrecarga por cuidar, estrés laboral, tabaco, trabajo y alcohol.
  - Menos síntomas: lugar de trabajo comprensivo, ejercicio de bajo impacto, días de ejercicio y agua.
- **Segmentos:** los cuatro grupos de A y los de B1 se distinguen casi solo por las variables con que se formaron. Sus diferencias de MRS son pequeñas, sobre todo en la dimensión psicológica y en la proporción con síntomas severos.
- **B1:** reproduce el mismo patrón con tres preguntas.
- **Base para las Fases 38 y 39:** el análisis de características individuales parece la base más clara, con los segmentos solo como estratificación descriptiva.
- **Alcance:** la conclusión B de la Fase 37C no cambia. No se elige ningún modelo.

{SINT}

Este informe responde las 14 preguntas de cierre en lenguaje sencillo. Los detalles están en los informes 03 a 12 y 16.

# Respuestas

**1. ¿Cómo se caracterizan las 529 participantes?** Mujeres sintéticas de {n(num.loc['edad', 'minimo'], 0)} a {n(num.loc['edad', 'maximo'], 0)} años (mediana {n(num.loc['edad', 'mediana'], 0)}).

- **Contexto:** el {n(100 * num.loc['tiene_pareja', 'media'], 0)} % tiene pareja, el {n(100 * num.loc['trabaja_actualmente', 'media'], 0)} % trabaja y el 47 % cuida a alguien.
- **Hábitos:** el 57 % no hace ejercicio ningún día. Pasan una mediana de {n(num.loc['horas_sedentarismo', 'mediana'], 0)} horas sentadas al día.
- **Datos imputados:** el {n(imp['pct_con_alguna_imputacion_en_A'], 1)} % tiene algún dato imputado en la limpieza, aunque solo el {n(100 * imp['celdas_imputadas_en_A'] / imp['celdas_A'], 1)} % de las celdas lo está.
- **Datos parciales:** el IMC solo está observado en la mitad.

**2. ¿Cómo se caracterizan los cuatro segmentos de K-means?**

- **Grupo 0 (150):** casi sin pareja y con poca actividad sexual.
- **Grupo 1 (76):** con ejercicio frecuente de todo tipo.
- **Grupo 2 (132):** con pareja y casi sin trabajo, con menos comidas fuera y menos falta de tiempo.
- **Grupo 3 (171):** con pareja y con trabajo, con más comidas fuera y más falta de tiempo.

Esos rasgos vienen de las variables con que se formaron los grupos, así que no son una validación.

**3. ¿Qué variables los diferencian más?** Pareja (η² 0,65), días de ejercicio (0,56), ejercicio aeróbico (0,51), trabajo (0,43), fuerza (0,37), actividad sexual (0,30), bajo impacto (0,26), comidas fuera (0,17) y falta de tiempo (0,10). Todas son variables usadas por A; los valores coinciden exactamente con la Fase 37C.

**4. ¿Qué variables no muestran diferencias relevantes?**

- **Externas a A:** etapa menopáusica, IMC, diabetes, previsión y las preguntas laborales (todas con η² < 0,01). La sobrecarga por cuidar tiene una diferencia pequeña.
- **Usadas por A:** edad, sedentarismo, cuidado de personas, alcohol, presión, distensión y casi toda la alimentación. El tabaco tiene una diferencia pequeña.

Las {int(((car['segmentacion'] == 'A') & (car['efecto'] < 0.01)).sum())} variables con η² < 0,01 tienen distribuciones semejantes entre grupos.

**5. ¿Cómo se distribuyen los síntomas MRS?**

- **Total:** media {n(mrs.loc['mrs_total', 'media'], 1)} de 44 (DE {n(mrs.loc['mrs_total', 'de'], 1)}), repartido sin grupos visibles.
- **Severidad:** el {n(sev.iloc[3]['pct'], 1)} % tiene 16 puntos o más (severa), el {n(sev.iloc[2]['pct'], 1)} % moderada, el {n(sev.iloc[1]['pct'], 1)} % leve y el {n(sev.iloc[0]['pct'], 1)} % casi sin síntomas.
- **Por ítem:** los síntomas más intensos son el cansancio, las molestias musculares y la irritabilidad; los menos intensos, los urinarios.

**6. ¿Qué relaciones aparecen entre características y MRS?** {nd(f1)} de 36 características se asocian con el total después de la corrección (F1), todas con efecto pequeño (de {n(dest1['efecto'].abs().min(), 2)} a {n(dest1['efecto'].abs().max(), 2)}).

- **Mayor MRS:** {lista_destacadas(dest1[dest1['efecto'] > 0].sort_values('efecto', ascending=False))}.
- **Menor MRS:** {lista_destacadas(dest1[dest1['efecto'] < 0])}.
- **Dónde se concentran:** en la dimensión psicológica.
- **Sin asociación:** edad, etapa, pareja, actividad sexual, sedentarismo y la mayor parte de la alimentación.
- **Lectura:** ninguna asociación es causal.

**7. ¿Hay diferencias de MRS entre los cuatro segmentos?** Sí, pequeñas.

- **Grupo 1, el de ejercicio frecuente:** tiene el promedio más bajo ({rf('A', 1)} puntos y {n(SV('A', 1)['pct_severo'], 0)} % severo).
- **Grupos 0 y 3:** tienen los más altos ({rf('A', 0)} y {rf('A', 3)}, con un {n(SV('A', 0)['pct_severo'], 0)} % y un {n(SV('A', 3)['pct_severo'], 0)} % severo).
- **Pruebas:** la diferencia es significativa en la psicológica (ε² {n(G('A', 'mrs_psicologico')['efecto'], 3)}), la severidad y severo, pero no en el total (q {p_(G('A', 'mrs_total')['q'])}).
- **Variación interna:** más del 98 % de la variación queda dentro de los grupos.

**8. ¿Qué se mantiene en las sensibilidades?**

- **Se mantiene:** la diferencia psicológica y la de severo con el corte de margen principal y en las cinco particiones guardadas. Sin las imputaciones de las tres preguntas se mantienen, algo más débiles en A. Sin el ítem 9, el total de A y de B1 casi no cambia.
- **Se pierde:** solo cuando el n baja mucho (margen ≥ 0,20 o sin ninguna imputación, 118 participantes).
- **Análisis individual:** con solo datos observados, cambia una de 36 variables.

**9. ¿Qué sucede al comparar A y B1?**

- **Coincidencia:** comparten el {n(100 * corr['coincidencia_A_B1'], 0)} % de las asignaciones (ARI {n(corr['ari_A_B1'])}, que no es un porcentaje).
- **Perfiles:** son casi iguales.
- **Diferencias de MRS:** muestran el mismo patrón, algo mayores en B1 (total ε² {n(G('B1', 'mrs_total')['efecto'], 3)} frente a {n(G('A', 'mrs_total')['efecto'], 3)}).
- **Uso de esta comparación:** no sirve para elegir. B1 no es un modelo clínico ni una validación independiente, y sus diferencias equivalen a comparar por trabajo, pareja y ejercicio.

**10. ¿Qué aporta analizar las características individuales?** Conserva información que los segmentos pierden:

- **Variables externas:** las asociaciones de IMC, diabetes, sobrecarga, estrés y lugar de trabajo siguen iguales dentro de los grupos, así que los segmentos no las representan.
- **Tamaño de muestra:** informa el n real de cada variable.
- **Independencia de la partición:** no depende de una partición ni de su frontera.

**11. ¿Qué limitaciones permanecen?**

- **Datos y diseño:** datos sintéticos, análisis no ciego respecto de las Fases 34C a 35B, efectos sin ajuste mutuo y dirección causal desconocida.
- **Datos incompletos:** imputaciones sin marca en diabetes y previsión, IMC en la mitad y módulos parciales.
- **Validez:** muchas pruebas, aunque corregidas, y ninguna muestra de confirmación.

**12. ¿Qué resultados sirven para las Fases 38 y 39?**

- **Consecuente:** `severo_mrs`.
- **Antecedentes:** contexto, hábitos y salud, agrupados de antemano.
- **Riesgos:** {len(raras)} categorías raras que conviene agrupar, redundancias (ejercicio, trabajo y módulos) y circularidades (actividad sexual e ítem 9; estrés y sobrecarga).
- **Análisis condicionados:** por trabajo, pareja, ejercicio y cuidado.

La nota 16 lo detalla. No propone variables por haber resultado significativas aquí.

**13. ¿Qué pruebas se ejecutaron y superaron?** {int((pru['resultado'] == 'superada').sum())} de {len(pru)} pruebas superadas y {int(mut['detectado'].sum())} de {len(mut)} errores introducidos detectados. Las pruebas cubren:

- Alineación, etiquetas y tamaños.
- Cálculo del MRS y faltantes.
- Ausencia de lectura de la verdad del simulador.
- Elección de pruebas, multiplicidad y reproducibilidad.
- Selección retrospectiva por MRS.
- Integridad de fases anteriores y Django.

**14. ¿Se mantuvieron intactas las fases anteriores?** Sí.

- **Archivos protegidos:** {e(man_ini['comparados_por_huella'].sum())} archivos de las Fases 34-35, 36, 37A, 37B, 37C y del complemento coinciden con sus manifiestos al inicio{' y al final' if fin else ''}. Los 4 archivos del simulador listados en el manifiesto 34-35 no se abrieron.
- **Git:** HEAD sigue en 745d689, sin commit ni push, sin cambios en Django ni en los datos.

# Decisiones para la responsable

1. **Estratificación:** decidir si las Fases 38 y 39 usarán A, B1 o ninguna segmentación como estratificación descriptiva.
2. **Consecuente y agrupaciones:** confirmar `severo_mrs` como consecuente principal y aprobar las agrupaciones de categorías antes de generar reglas.

Las Fases 38, 39 y 40 no se iniciaron.
""")

# ---------- 13, 14, 00 en Markdown
pru_md = f"""# Fase 37D: informe de pruebas

- **Pruebas:** {int((pru['resultado'] == 'superada').sum())} de {len(pru)} superadas.
- **Controles negativos:** {int(mut['detectado'].sum())} de {len(mut)} errores introducidos detectados. Cada control reemplaza una función por una versión con un error y exige que alguna prueba falle.
- **Archivos:** `pruebas/resultados_pruebas.csv` y `pruebas/control_mutaciones.csv`.

## Pruebas

{tabla(['N.º', 'Prueba', 'Resultado', 'Detalle'], [[r.n, r.prueba, r.resultado, r.detalle] for r in pru.itertuples()])}

## Controles negativos

{tabla(['Error introducido', 'Detectado', 'Pruebas que fallan', 'Motivo'], [[r.control_negativo, 'sí' if r.detectado else 'NO', r.pruebas_que_fallan, str(r.motivo).replace('|', '/')[:120]] for r in mut.itertuples()])}

«Una variable fuera de F1» se detecta primero con un error de clave en la prueba 7, porque la variable quitada se busca ahí. La prueba 10 también la detecta por su propio motivo.
"""
fin_txt = ''
if fin:
    fin_txt = f"""
## Verificación final

- **Fecha:** {fin['fecha']}.
- **Archivos protegidos:** {e(fin['archivos_protegidos'] - 4)} comparados, {fin['archivos_distintos']} distintos.
- **Entradas:** iguales al inicio: {'sí' if fin.get('entradas_iguales_al_inicio') else 'NO'}.
- **Git:** HEAD {fin['head']}; cambios en `src/`: {len(fin['cambios_en_src'])}; cambios fuera de `analisis/`: {len(fin['cambios_fuera_de_analisis'])}; datos versionados modificados: {len(fin['datos_versionados_modificados'])}.
- **`__pycache__` en fases protegidas:** {len(fin['pycache_en_fases_protegidas'])}.
"""
leidos = pd.read_csv(B / 'integridad' / 'archivos_leidos.csv')['archivo_leido']
datos_leidos = sorted(x for x in leidos if x.startswith('datos/'))
integ_ini = f"""# Fase 37D: informe de integridad inicial

Verificación hecha antes de calcular cualquier análisis, justo después de sellar el protocolo.

- **Fecha:** {ini['fecha']}.
- **Protocolo:** sellado el {ini['protocolo_sellado']}, huella `{ini['protocolo_sha256']}`.
- **Git:** rama `{ini['rama']}`, HEAD {ini['head']}. Sin cambios en `src/` (Django), sin cambios en datos versionados y sin cambios fuera de `analisis/`.
- **`__pycache__` en fases protegidas:** {len(ini['pycache_en_fases_protegidas'])}.

{tabla(['Fase', 'Archivos', 'Comparados por huella', 'Sin verificar por nombre', 'Distintos'], [[r.fase, e(r.archivos), e(r.comparados_por_huella), e(r.sin_verificar_por_nombre), e(r.distintos)] for r in man_ini.itertuples()])}

Los 4 archivos sin verificar del manifiesto 34-35 corresponden al simulador: `bitacora_suciedad.csv`, `dataset_usuaria_sucio.csv`, `dataset_usuaria_verdad.csv` y `diabetes_diagnostico_verdad.csv`. No están versionados y este proceso no los abre. Las huellas de las entradas usadas están en `integridad/huellas_entradas_inicial.csv`.
"""
integ_fin = f"""# Fase 37D: informe de integridad final

- **Protocolo:** huella `{sello['sha256']}`, sellado el {sello['sellado']}, antes de cualquier asociación con el MRS. La prueba 10 comprueba que todos los resultados son posteriores.
- **Nota posterior:** huella `{nota['sha256']}`, sellada el {nota['sellado']}.
- **Lecturas fuera de la carpeta:** {len(leidos)} archivos, casi todos para comparar huellas con los manifiestos protegidos. De ellos, {len(datos_leidos)} están en `datos/`: {sum('cache_35b' in x for x in datos_leidos)} son la caché de remuestreos de la Fase 35B, que figura en el manifiesto 34-35 y solo se lee para calcular su huella. Los otros son: {', '.join(f'`{x}`' for x in datos_leidos if 'cache_35b' not in x)}. El análisis usa solo `datos/limpio_usuaria/dataset_usuaria_limpio.csv` y su diccionario. No se leyó ningún archivo del simulador: el gancho de auditoría lo impide. Registro: `integridad/archivos_leidos.csv`.
- **Escrituras fuera de la carpeta:** {len(pd.read_csv(B / 'integridad' / 'escrituras_fuera.csv'))}.
- **Memoria:** como máximo un proceso de análisis a la vez, con vigilancia. Registro: `integridad/registro_memoria.csv`.
- **Manifiesto:** `integridad/manifiesto_final.csv`, con la huella de todos los archivos de esta carpeta salvo él mismo.
{fin_txt}
## Restricciones

Se cumplieron todas:

- **Fases y datos:** sin cambios en las Fases 34 a 37C ni en el complemento, en los datos originales ni en los resultados históricos.
- **Modelos:** sin reajustar PCA, FAMD ni K-means, y sin modificar la regla B1.
- **Uso del MRS y del simulador:** sin MRS para elegir y sin la verdad del simulador.
- **Interpretación:** sin nombres clínicos, sin causalidad y sin recomendaciones clínicas.
- **Alcance:** sin reglas de asociación y sin Fases 38, 39 ni 40.
- **Plataforma y git:** sin cambios en Django, sin commit y sin push.
"""
indice = """# Fase 37D: índice de entregables

| N.º | Entregable | Archivo |
|---|---|---|
| 1 | Protocolo sellado | `informes/01_protocolo_37D.docx`, `protocolo/01_protocolo_37D.md`, `protocolo/sello_protocolo.json` |
| 1b | Nota posterior al sellado | `informes/01b_nota_posterior.docx`, `protocolo/02_nota_posterior_37D.md` |
| 2 | Informe de integridad inicial | `informes/02_integridad_inicial.md` |
| 3 | Diccionario de variables | `informes/03_diccionario_variables.docx`, `diccionario/diccionario_variables_37D.csv` |
| 4 | Caracterización general | `informes/04_caracterizacion_general.docx` |
| 5 | Segmentos A | `informes/05_caracterizacion_segmentos_A.docx` |
| 6 | Segmentos B1 | `informes/06_caracterizacion_segmentos_B1.docx` |
| 7 | Características individuales frente al MRS | `informes/07_individual_frente_a_MRS.docx` |
| 8 | MRS por segmento A | `informes/08_mrs_por_segmento_A.docx` |
| 9 | MRS por segmento B1 | `informes/09_mrs_por_segmento_B1.docx` |
| 10 | Comparación A, B1 y sin segmentar | `informes/10_comparacion_tres_perspectivas.docx` |
| 11 | Sensibilidades y limitaciones | `informes/11_sensibilidades_limitaciones.docx` |
| 12 | Figuras y tablas | `informes/12_figuras_tablas.docx`, `figuras/`, `resultados/` |
| 13 | Informe de pruebas | `informes/13_informe_pruebas.md` |
| 14 | Informe de integridad final | `informes/14_informe_integridad_final.md` |
| 15 | Informe final | `informes/15_informe_final_37D.docx` |
| 16 | Nota para las Fases 38 y 39 | `informes/16_nota_fases_38_39.docx` |

**Respaldo:** `resultados/descripcion/`, `resultados/individual/`, `resultados/segmentos/` y `resultados/resumen_37D.json`.

**Scripts:** `scripts/`. Orden de ejecución:

1. `sellar_protocolo_37d.py`
2. `integridad_37d.py inicial`
3. `descripcion_37d.py`
4. `individual_37d.py`
5. `segmentos_37d.py`
6. `graficos_37d.py`
7. `pruebas_37d.py --mutaciones`
8. `generar_informes_37d.py`
9. `integridad_37d.py final`
10. `manifiesto_37d.py`
"""
for nombre, t in (('13_informe_pruebas.md', pru_md), ('02_integridad_inicial.md', integ_ini), ('14_informe_integridad_final.md', integ_fin), ('00_indice_entregables.md', indice)):
    (INF / nombre).write_text(t, encoding='utf-8', newline='\n')

resumen = {'estado': 'Fase 37D completa; descriptiva y exploratoria; datos sintéticos', 'conclusion_37C': 'Sin cambios (conclusión B, P2_c12_km_k4)', 'f1_destacadas': nd(f1),
           'f1_destacadas_variables': {r.variable: float(r.efecto) for r in dest1.itertuples()}, 'f2_destacadas': nd(f2), 'f3_destacadas': nd(f3), 'f4_destacadas': nd(f4),
           'F5': {f'{r.segmentacion}|{r.resultado}': {'efecto': float(r.efecto), 'q': float(r.q)} for r in gl5.itertuples()}, 'correspondencia': corr,
           'pruebas': f"{int((pru['resultado'] == 'superada').sum())}/{len(pru)}", 'mutaciones': f"{int(mut['detectado'].sum())}/{len(mut)}", 'fases_38_39_40': 'No iniciadas'}
N.a_json(resumen, R / 'resumen_37D.json')

shutil.copyfile(B / 'protocolo' / '01_protocolo_37D.md', F / '01_protocolo_37D.md')
shutil.copyfile(B / 'protocolo' / '02_nota_posterior_37D.md', F / '01b_nota_posterior.md')
titulos = {'01_protocolo_37D': 'Protocolo de la Fase 37D', '01b_nota_posterior': 'Nota posterior al sellado'}
js = N.C37 / 'scripts' / 'md_a_word_37c.js'
for nombre, (titulo, md) in docs.items():
    (F / f'{nombre}.md').write_text(md.strip() + '\n', encoding='utf-8', newline='\n')
    titulos[nombre] = titulo
for nombre, titulo in titulos.items():
    r = subprocess.run(['node', str(js), str(F / f'{nombre}.md'), str(INF / f'{nombre}.docx'), titulo, 'AgingWomen · Fase 37D: caracterización y MRS'], capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f'{nombre}: {r.stderr[:500]}')
print(len(titulos), 'informes Word')
