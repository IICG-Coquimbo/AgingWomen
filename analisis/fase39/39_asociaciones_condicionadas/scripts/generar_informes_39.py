"""
Fase 39: informes en Markdown y Word (20 entregables). Todas las cifras se leen de las tablas guardadas.

Uso, desde la carpeta scripts: NODE_PATH=<node_modules con docx> python generar_informes_39.py
"""
import shutil
import subprocess
import sys

import nucleo_39 as N
import numpy as np
import pandas as pd

sys.dont_write_bytecode = True
B = N.BASE
INF = B / 'informes'
F = INF / 'fuentes'
F.mkdir(parents=True, exist_ok=True)
SINT = ('Todo el análisis usa el conjunto **sintético** de 529 participantes. Los resultados describen la simulación, no a mujeres reales. No son diagnósticos ni '
        'predicciones, no permiten recomendaciones de salud y ninguna asociación indica causa. Es un análisis **exploratorio**: los estratos y la pregunta se '
        'definieron después de conocer las Fases 37D y 38.')


def n(x, d=2):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return '—'
    return f'{x:,.{d}f}'.replace(',', 'X').replace('.', ',').replace('X', '.').replace('-', '−')


def e(x):
    return f'{int(x):,}'.replace(',', '.')


def pc(x, d=1):
    return n(100 * x, d) + ' %'


def p_(x):
    return '< 0,001' if x < 0.001 else n(x, 3)


def tabla(cab, filas):
    s = '| ' + ' | '.join(cab) + ' |\n|' + '---|' * len(cab) + '\n'
    return s + ''.join('| ' + ' | '.join(str(c).replace('|', '/') for c in f) + ' |\n' for f in filas)


def fig(nombre, pie):
    return f'\n![{pie}](../../figuras/{nombre})\n'


def NOM(x):
    return N.NOMBRE.get(x, x.replace('_', ' '))


L = lambda r: pd.read_csv(B / r, encoding='utf-8')  # noqa: E731
J = lambda r: N.leer_json(B / r)  # noqa: E731
sello = J('protocolo/sello_protocolo.json')
DIC, DIFB, SUPER, VER = L('preparacion/diccionario_estratos.csv'), L('preparacion/diferencias_basales.csv'), L('preparacion/superposicion_dimensiones.csv'), J('preparacion/verificacion_codificacion.json')
RE, TODAS, TOPZ = L('reglas/resumen_estratos.csv'), L('reglas/reglas_todos_estratos.csv'), L('reglas/reglas_mayor_z_por_estrato.csv')
Hs = {g: L(f'comparacion/comparacion_{g}.csv') for g in N.DIMENSIONES}
NH = {g: L(f'comparacion/nula_comparacion_{g}.csv') for g in N.DIMENSIONES}
MH = L('comparacion/resumen_comparacion.csv')
SIGR = L('comparacion/significacion_nominal_resumen.csv')
SR, SH, SUPS = L('sensibilidades/resumen_sensibilidades_estratos.csv'), L('sensibilidades/resumen_sensibilidades_comparacion.csv'), L('sensibilidades/reglas_superan_nula_sensibilidades.csv')
LECT, PEQ, DEP = L('sensibilidades/lectura_comparaciones_resumen.csv'), L('sensibilidades/grupos_pequenos_comparaciones.csv'), L('sensibilidades/dependencia_items_estratos.csv')
ABG, ABC, ABR, ABX = L('ab1/resumen_grupos_A_B1.csv'), L('ab1/resumen_comparacion_A_B1.csv'), L('ab1/reglas_grupos_A_B1.csv'), L('ab1/cruce_A_B1.csv')
ABCOMP = L('ab1/composicion_A_B1_por_dimension.csv')
CONC = J('resultados/conclusion_39.json')
PRU, MUT = L('pruebas/resultados_pruebas.csv'), L('pruebas/control_mutaciones.csv')
INI, MAN_INI = J('integridad/integridad_inicial.json'), L('integridad/manifiestos_inicial.csv')
FIN = J('integridad/integridad_final.json') if (B / 'integridad' / 'integridad_final.json').exists() else None
S3B = L('sensibilidades/comparacion/S3-bajo/comparacion_ejercicio.csv')
S3B = S3B[S3B['supera_nula_dimension']]
cls = TODAS['clase'].value_counts()
TOT_REGLAS = len(TODAS)
TOT_MARC = int(TODAS['marcada'].sum())
TOT_RED = int((TODAS['marcada'] & TODAS['redundante'].fillna(False).astype(bool)).sum())


def basal(g, est):
    r = DIC[(DIC['grupo'] == g) & (DIC['estrato'] == est)].iloc[0]
    return r


def fila_estrato(dim, est):
    r = RE[(RE['dimension'] == dim) & (RE['estrato'] == est)].iloc[0]
    b = basal(dim, est)
    return r, b


def regla_txt(a, cons):
    return f"{N.legible_regla(a)} → {'severos' if cons.endswith('SI') else 'no severos'}"


def tabla_reglas(D, extra=True):
    filas = []
    for r in D.itertuples():
        f = [N.legible_regla(r.antecedente), 'severos' if r.consecuente.endswith('SI') else 'no severos', f'{e(r.n_conjunto)} de {e(r.n_antecedente)}',
             f'{pc(r.confianza)} ({n(100 * r.ic_confianza_inf, 0)}-{n(100 * r.ic_confianza_sup, 0)})', pc(r.frecuencia_basal), n(r.lift),
             f'{"+" if r.diferencia_riesgo >= 0 else ""}{n(100 * r.diferencia_riesgo, 1)} pts', p_(r.p_ajustado_estrato)]
        if extra:
            f += [pc(r.reaparece_marcada, 0), r.clase[2:]]
        filas.append(f)
    cab = ['Antecedente', 'Consecuente', 'n (con / antecedente)', 'Confianza (IC 95 %)', 'Basal del estrato', 'Lift', 'Diferencia de riesgo', 'p ajustado (estrato)']
    return tabla(cab + (['Reaparece', 'Clase'] if extra else []), filas)


def tabla_comp(H, dim, k=8):
    est = N.dims_de(dim)
    t = H[~H['redundante']].sort_values('Q', ascending=False).head(k)
    filas = []
    for _, r in t.iterrows():
        celdas = [f"{e(r[f'nAC_{x}'])}/{e(r[f'nA_{x}'])} ({pc(r[f'confianza_{x}'], 0)}) · DR {n(r[f'DR_{x}'], 2)} [{n(r[f'DR_inf_{x}'], 2)}; {n(r[f'DR_sup_{x}'], 2)}]" for x in est]
        filas.append([N.legible_regla(r['antecedente']), *celdas, n(r['rango_DR'], 2), n(r['Q'], 1), p_(r['p_chi2']), p_(r['p_ajustado_dimension']), r['clase'][3:]])
    return tabla(['Antecedente', *[f'{NOM(x)}: severas/n_A (confianza) · DR [IC 95 %]' for x in est], 'Rango DR', 'Q', 'p sin ajuste', 'p ajustado (dimensión)', 'Clase'], filas)


docs = {}

# ---------- 04 diccionario de estratos
docs['04_diccionario_estratos'] = ('Diccionario de estratos', f"""
# Alcance

{SINT}

Hay cuatro dimensiones. Cada una divide a las 529 en estratos que no se superponen. Las dimensiones sí se superponen entre sí: una participante pertenece a un estrato de cada dimensión.

- **A y B1:** se agregan solo como comparación secundaria, con sus etiquetas históricas sin reajustar.
- **Pertenencia:** se recalcula desde los códigos de la Fase 36. La prueba 4 la vuelve a calcular desde las respuestas crudas de la limpieza, sin discrepancias.

{tabla(['Dimensión', 'Estrato', 'Definición', 'Participantes', 'Variables excluidas dentro del estrato', 'Uso'],
       [[NOM(r.grupo) if r.grupo in N.DIMENSIONES else r.grupo, NOM(r.estrato), r.definicion, e(r.participantes), r.variables_excluidas, r.uso] for r in DIC.itertuples()])}

# Reglas de construcción

- **Ítems:** son los de la Fase 38 (94 ítems y reglas R1 a R7), con las agrupaciones fijadas con las 529 y sin el MRS. La matriz de las 529 es idéntica a la de la Fase 38 (prueba 5).
- **Ítems quitados en cada estrato:** los de la variable que define la dimensión, y los que todas o ninguna participantes del estrato cumplen.
- **Ejercicio de 3 días o más:** reúne 3-4 días (52), 5-6 días (15) y todos los días (12). La agrupación se fija por el significado de las respuestas, como en B1 y en la sensibilidad S2b de la Fase 38, sin mirar el MRS.
- **Cuidado:** compara a quienes cuidan a una o más personas con quienes no cuidan, sin separar por número de personas. Los grupos de 2 personas (67) y de 3 o más (48) serían demasiado pequeños.
- **Módulos:** el laboral (que menciona los síntomas) y la sobrecarga solo entran en las sensibilidades S7a y S7b, dentro del único estrato donde existen.
- **A y B1:** se excluyen trabajo, pareja y días de ejercicio, porque esas tres preguntas determinan casi por completo los grupos.

# Superposición entre dimensiones

{tabla(['Dimensión 1', 'Estrato', 'Dimensión 2', 'Estrato', 'Participantes'], [[NOM(r.dimension_1), NOM(r.estrato_1), NOM(r.dimension_2), NOM(r.estrato_2), e(r.participantes)] for r in SUPER.itertuples()])}
""")

# ---------- 05 tamaños y basales
docs['05_tamanos_frecuencias_basales'] = ('Tamaños y frecuencias basales', f"""
# Tamaños, frecuencia basal y viabilidad

{SINT}

**Frecuencia basal:** la proporción de participantes del estrato con MRS ≥ 16. Cada regla del estrato se compara con **esta** basal, no con el 53,1 % general.

{tabla(['Grupo', 'Estrato', 'n', 'Severas', 'Basal (IC 95 %)', 'Largo máximo', 'n_A mínimo', 'n_AC mínimo', 'Ítems en el estrato', 'Búsqueda'],
       [[NOM(r.grupo) if r.grupo in N.DIMENSIONES else r.grupo, NOM(r.estrato), e(r.participantes), e(r.severas), f'{pc(r.frecuencia_basal_si)} ({pc(r.ic_basal_inf, 0)}-{pc(r.ic_basal_sup, 0)})',
         r.largo_maximo, r.umbral_antecedente, r.umbral_conjunto, r.items, r.busqueda] for r in DIC.itertuples()])}

{fig('f01_tamanos_basales.png', 'Figura 1. Frecuencia basal de MRS severo por estrato y por grupo A/B1.')}

# Diferencias de frecuencia basal entre estratos

Esta tabla muestra cuánto cambia la **proporción de severas** de un estrato a otro, es decir, la asociación del propio contexto con la severidad. **No** es una diferencia en la asociación de los hábitos (eso se trata en el informe 12). Es descriptiva, sin ajuste por búsqueda.

{tabla(['Grupo', 'Estrato 1', 'Estrato 2', 'Basal 1', 'Basal 2', 'Diferencia (IC 95 %)', 'p de Fisher'],
       [[NOM(r.grupo) if r.grupo in N.DIMENSIONES else r.grupo, NOM(r.estrato_1), NOM(r.estrato_2), pc(r.basal_1), pc(r.basal_2),
         f'{n(100 * r.diferencia, 1)} pts ({n(100 * r.ic_inf, 1)} a {n(100 * r.ic_sup, 1)})', p_(r.p_fisher)] for r in DIFB.itertuples()])}

**Lectura:**
- **Ejercicio:** quienes hacen 3 días o más tienen menos síntomas severos (32,9 %) que quienes no hacen ejercicio (58,6 %).
- **Trabajo:** quienes trabajan tienen algo más que quienes no trabajan (57,6 % frente a 46,8 %).
- **Pareja y cuidado:** las diferencias son pequeñas y sus intervalos incluyen el 0.
- **Coherencia con la Fase 37D:** coincide con lo que mostró sobre el MRS.
- **Advertencia:** son diferencias marginales, sin ajuste y en datos sintéticos.

# Viabilidad

- **Estratos de 250 o más:** trabaja, tiene pareja, 0 días, cuida y no cuida admiten antecedentes de hasta 3 condiciones.
- **Estratos de 120 a 249:** no trabaja, no tiene pareja y 1-2 días admiten hasta 2 condiciones.
- **Estratos de 60 a 119:** 3 días o más (79) admite solo antecedentes de 1 condición, con al menos 20 participantes. Con eso solo hay {e(int(fila_estrato('ejercicio', '3_o_mas_dias')[0]['reglas']))} reglas posibles.
- **Estratos de menos de 60:** ninguno queda solo descriptivo.
""")

# ---------- 06 preparación
docs['06_preparacion_matrices_condicionadas'] = ('Preparación de las matrices condicionadas', f"""
# Contenido

{SINT}

**Archivos:**
- **Matrices por estrato:** `preparacion/matrices/matriz_<grupo>_<estrato>.csv`, con una fila por participante del estrato, su identificador original, una columna 0/1 por ítem admisible y los dos consecuentes.
- **Pertenencia:** `preparacion/pertenencia_estratos.csv` asigna cada participante a su estrato en cada dimensión y a sus grupos A y B1.
- **Prevalencia por estrato:** `preparacion/items_por_estrato.csv`.
- **Trazabilidad:** `preparacion/trazabilidad_items_fase38.csv` indica de qué códigos sale cada ítem.

# Verificaciones

- **Identificadores:** las 529 participantes, en el orden de la Fase 36: {'sí' if VER['ids_iguales_y_en_orden'] else 'NO'}.
- **Ítems y matriz:** los mismos {VER['items']} ítems y la misma matriz que la Fase 38: {'sí' if VER['misma_matriz'] else 'NO'}.
- **Severidad:** recalculada desde los 11 ítems, con {VER['severos']} severas y {VER['no_severos']} no severas, igual a la Fase 38: {'sí' if VER['consecuente_igual'] else 'NO'}.
- **B1:** la etiqueta histórica es igual a la regla de cuatro pasos: {'sí' if VER['B1_igual_a_regla'] else 'NO'}.

# Ítems por estrato

{tabla(['Grupo', 'Estrato', 'Ítems admisibles', 'Constantes quitados', 'Variables excluidas'], [[NOM(r.grupo) if r.grupo in N.DIMENSIONES else r.grupo, NOM(r.estrato), r.items, r.items_constantes_quitados, r.variables_excluidas] for r in DIC.itertuples()])}

- **Sin reagrupar:** dentro de cada estrato no se reagrupa ninguna categoría. Una categoría con pocos casos en el estrato simplemente no alcanza el umbral.
- **Estados de las celdas:** se conservan los estados observado, imputado, deducido y no aplica. La sensibilidad S1 quita las celdas imputadas y deducidas.
""")


# ---------- 07-10 reglas por dimensión
def informe_dim(dim):
    est = N.dims_de(dim)
    filas = []
    for x in est:
        r, b = fila_estrato(dim, x)
        filas.append([NOM(x), e(r['n']), pc(r['frecuencia_basal_si']), r['largo_maximo'], f"{e(r['umbral_antecedente'])} / {e(r['umbral_conjunto'])}", e(r['reglas']),
                      e(r['marcadas']), f"{e(round(r['nula_media_marcadas']))} (p95 {e(round(r['nula_p95_marcadas']))})", p_(r['p_exceso_marcadas']), e(r['supera_nula_estrato'])])
    top = TOPZ[TOPZ['dimension'] == dim].sort_values(['estrato', 'consecuente', 'z'], key=lambda s: s.abs() if s.name == 'z' else s, ascending=[True, True, False])
    top = top.groupby(['estrato', 'consecuente']).head(3)
    H = Hs[dim]
    m = MH[MH['grupo'] == dim].iloc[0]
    txt = f"""
# Resumen

{SINT}

**A. Asociación dentro de cada estrato.** La búsqueda de reglas se hizo dentro de cada estrato, con su basal propia y una referencia nula que permuta la severidad solo dentro del estrato.

{tabla(['Estrato', 'n', 'Basal', 'Largo', 'n_A / n_AC mínimos', 'Reglas', 'Marcadas', 'Marcadas bajo la nula: media', 'p de exceso', 'Superan la nula del estrato'], filas)}

- **Ninguna regla de esta dimensión supera la referencia nula de su estrato.**
- **Marcadas frente a la nula:** la columna «p de exceso» indica si hay más reglas marcadas (≥ 10 puntos sobre la basal) de lo que produce el azar.

**Clases de las reglas:**

{tabla(['Estrato', *[c[2:] for c in sorted(TODAS['clase'].unique())]], [[NOM(x), *[e(((TODAS['dimension'] == dim) & (TODAS['estrato'] == x) & (TODAS['clase'] == c)).sum()) for c in sorted(TODAS['clase'].unique())]] for x in est])}

# Reglas más fuertes de cada estrato

Se muestran las 3 reglas no redundantes con mayor |z| por estrato y consecuente. **No son hallazgos:** todas son compatibles con la referencia nula de su estrato. Se muestran para que se vea qué hay.

{tabla_reglas(top)}

# B. Diferencia de asociación entre estratos

- **Antecedentes comparados:** {e(m['comparables'])} antecedentes comparables de 1 o 2 condiciones, de {e(m['candidatos'])} posibles. Son comparables los que tienen al menos 20 participantes con y sin el antecedente en cada estrato.
- **Diferencias marcadas:** {e(m['marcadas'])} tienen un rango de diferencias de riesgo de al menos 0,10 entre estratos. Bajo la referencia nula aparecen {e(round(m['nula_media_marcadas']))} en promedio (p de exceso {p_(m['p_exceso_marcadas'])}). **No hay más diferencias marcadas de las que produce el azar.**
- **Ninguna diferencia supera la nula de la dimensión.** El mayor Q observado es {n(H['Q'].max(), 1)}; el percentil 95 del máximo Q bajo la nula es {n(m['nula_p95_max_Q'], 1)}. El menor p ajustado es {p_(H['p_ajustado_dimension'].min())}.

**Comparaciones con mayor heterogeneidad** (no redundantes):

{tabla_comp(H, dim)}

**Cómo leer la tabla:**
- **DR:** la diferencia de riesgo, es decir, el porcentaje de severas con el antecedente menos el porcentaje sin él, dentro de cada estrato.
- **Rango DR:** cuánto difiere esa asociación entre estratos.
- **Lectura de las primeras filas:** en varias, el antecedente va con más síntomas severos en un estrato y con menos en otro. Pero diferencias de este tamaño aparecen igual al permutar la severidad dentro de los estratos, así que **no hay evidencia de que la asociación cambie según {NOM(dim).lower()}**.
"""
    return txt


for k, dim in zip(('07', '08', '09', '10'), N.DIMENSIONES):
    docs[f'{k}_reglas_por_{dim}'] = (f'Reglas por {NOM(dim).lower()}', informe_dim(dim))

# ---------- 11 nulas
docs['11_referencias_nulas_estrato'] = ('Referencias nulas por estrato', f"""
# Método

{SINT}

**Dentro de cada estrato:**
- **Permutaciones:** {e(N.N_PERM)} de la severidad, solo entre las participantes del estrato, con la semilla [42, 39, número del estrato]. Así se conserva su número de severas y no se mezclan estratos con basales distintas.
- **Búsqueda:** en cada permutación se repite la búsqueda completa sobre los mismos antecedentes.
- **p ajustado de Westfall-Young:** la proporción de permutaciones en que la regla más fuerte **de toda la búsqueda del estrato** iguala o supera a la regla observada.

**Conjunto de los 9 estratos:** el máximo |z| de los 9 en cada índice de permutación. Aproxima de forma conservadora la búsqueda en todos a la vez.

**Comparación entre estratos:** {e(N.N_PERM)} permutaciones de la severidad dentro de cada estrato de la dimensión a la vez. Se registran el máximo Q y el menor p χ².
- **Qué representa:** ninguna asociación en ningún estrato. Se usa como aproximación a «sin interacción».
- **Comprobación:** la prueba 13 simula una asociación común no nula sin interacción. El estadístico rechaza alrededor del 5 % (resultado: {PRU.set_index('n').loc['p13', 'detalle'].split('rechazo ')[1].split(' ')[0].replace('.', ',')}), así que está bien calibrado.

# Resultados dentro de los estratos

{tabla(['Dimensión', 'Estrato', 'Antecedentes evaluados', 'Marcadas', 'Nula: media', 'Nula: p95', 'p de exceso', 'Máximo |z|: p95 nulo', 'Menor p ajustado', 'Superan la nula del estrato'],
       [[NOM(r.dimension), NOM(r.estrato), e(r.antecedentes_evaluados), e(r.marcadas), e(round(r.nula_media_marcadas)), e(round(r.nula_p95_marcadas)), p_(r.p_exceso_marcadas), n(r.nula_p95_max_z),
         p_(TODAS[(TODAS['dimension'] == r.dimension) & (TODAS['estrato'] == r.estrato)]['p_ajustado_estrato'].min()), e(r.supera_nula_estrato)] for r in RE.itertuples()])}

{fig('f02_marcadas_frente_a_nula.png', 'Figura 2. Reglas marcadas observadas y bajo la referencia nula.')}

**Lectura:**
- **Ninguna regla supera la nula de su estrato.** La más cercana está en «cuida» (p ajustado {p_(TODAS[TODAS['estrato'] == 'cuida']['p_ajustado_estrato'].min())}).
- **Hay más reglas marcadas que por azar en cuatro estratos:** trabaja, tiene pareja, cuida (p ≤ 0,013) y 0 días (p = 0,049, en el límite). Son estratos grandes, donde se permiten 3 condiciones.
- **No cuida no tiene exceso,** aunque también es grande (278) y admite 3 condiciones (p {p_(fila_estrato('cuidado', 'no_cuida')[0]['p_exceso_marcadas'])}).
- **En los estratos más pequeños tampoco hay exceso:** no trabaja, no tiene pareja, 1-2 días y 3 días o más.
- **Es lo mismo que en la Fase 38:** una señal difusa repartida en muchas reglas débiles, que se detecta mejor donde hay más participantes.
- **Una diferencia entre estratos en el p de exceso no prueba que la asociación sea distinta.** Refleja, sobre todo, el tamaño y el número de combinaciones posibles.

# Resultados de la comparación

{tabla(['Dimensión', 'Comparables', 'Diferencias marcadas', 'Nula: media', 'p de exceso', 'Mayor Q', 'p95 del máximo Q nulo', 'Menor p ajustado (dimensión)', 'Menor p ajustado (conjunto)'],
       [[NOM(g), e(MH.set_index('grupo').loc[g, 'comparables']), e(MH.set_index('grupo').loc[g, 'marcadas']), e(round(MH.set_index('grupo').loc[g, 'nula_media_marcadas'])),
         p_(MH.set_index('grupo').loc[g, 'p_exceso_marcadas']), n(Hs[g]['Q'].max(), 1), n(MH.set_index('grupo').loc[g, 'nula_p95_max_Q'], 1), p_(Hs[g]['p_ajustado_dimension'].min()),
         p_(Hs[g]['p_ajustado_conjunto'].min())] for g in N.DIMENSIONES])}

{fig('f03_heterogeneidad_frente_a_nula.png', 'Figura 3. Máximo Q observado frente a la referencia nula.')}

**Benjamini-Hochberg:** se aplicó a todas las comparaciones evaluadas, no solo a las seleccionadas. El menor q por dimensión es: {', '.join(f'{NOM(g).lower()} {n(Hs[g]["q_bh_dimension"].min(), 3)}' for g in N.DIMENSIONES)}. Ninguno es menor que 0,05.
""")

# ---------- 12 comparación formal
sig_txt = tabla(['Dimensión', 'Comparables', 'Significativas (p < 0,05 sin ajuste) en ambos estratos', 'Significativas en solo uno', 'De estas, interacción p < 0,05 sin ajuste', 'De estas, superan la nula'],
                [[NOM(r.dimension), e(r.comparables), e(r.nominal_en_ambos), e(r.nominal_solo_en_uno), e(r.de_ellas_interaccion_p_menor_005_sin_ajuste), e(r.de_ellas_superan_nula_dimension)] for r in SIGR.itertuples()])
docs['12_comparacion_formal_estratos'] = ('Comparación formal entre estratos', f"""
# Qué se compara

{SINT}

Hay que distinguir dos preguntas:

- **A. ¿Hay asociación dentro de un estrato?** Por ejemplo, ¿entre quienes trabajan, un hábito va con más síntomas severos? Se responde en los informes 7 a 10.
- **B. ¿Esa asociación es distinta entre estratos?** Es una pregunta de **interacción**. Que una regla sea significativa en un estrato y no en otro **no** responde B.

**Cómo se responde B:**
- **Antecedentes evaluados:** todos los de 1 y 2 condiciones comparables, no solo las reglas seleccionadas.
- **Medida en cada estrato:** la diferencia de riesgo DR = P(severo | A) − P(severo | no A), con su IC de Newcombe.
- **Heterogeneidad:** Q = Σ w(DR − DR̄)², con w = 1/varianza. Con dos estratos también se informan Δ = DR₁ − DR₂, su IC 95 % y z, con Q = z².
- **Control:** la referencia nula por dimensión (máximo Q) y la conjunta de las 4 dimensiones (menor p).
- **Estabilidad:** 200 submuestras estratificadas del 80 %.

# Resultados

{tabla(['Dimensión', 'Comparables', 'Marcadas (rango ≥ 0,10)', 'H1 sin diferencia', 'H2 redundantes', 'H3 compatibles con la nula', 'H4 inestables', 'H5 superan los controles'],
       [[NOM(g), e(len(Hs[g])), e(Hs[g]['marcada'].sum()), *[e(Hs[g]['clase'].str.startswith(h).sum()) for h in ('H1', 'H2', 'H3', 'H4', 'H5')]] for g in N.DIMENSIONES])}

**Ninguna diferencia de asociación entre estratos supera su referencia nula, en ninguna dimensión.** Tampoco hay más diferencias marcadas de las que produce el azar (p de exceso entre {p_(MH['p_exceso_marcadas'].min())} y {p_(MH['p_exceso_marcadas'].max())}).

{fig('f04_comparaciones_mayor_Q.png', 'Figura 4. Diferencias de riesgo por estrato en las comparaciones con mayor Q.')}

**Lectura de la figura:**
- **Las comparaciones más extremas parecen grandes**, con diferencias de riesgo de signos opuestos e intervalos que no se tocan.
- **Pero es justo lo que produce el azar** al buscar entre {e(sum(len(h) for h in Hs.values()))} comparaciones: el p ajustado de cada una es alto.
- **Visualmente convincentes, no son evidencia.**

# Diferencias de significación (tabla exploratoria)

La tabla del protocolo «reglas que superan la nula en un estrato y no en otro» está **vacía**, porque ninguna regla supera la nula de su estrato.

Como ilustración, agregada después del sellado y sin intervenir en la conclusión, la tabla siguiente usa la significación **nominal**: el p de Fisher sin ajuste en cada estrato.

{sig_txt}

**Lectura:**
- **Cientos de antecedentes** son «significativos» en un estrato y no en el otro.
- **Solo una parte** tiene además una interacción nominal (p < 0,05 sin ajuste).
- **Ninguno resiste** la referencia nula de la búsqueda.

Interpretar «significativo aquí, no significativo allá» como una diferencia entre contextos produciría cientos de falsos hallazgos.

# Estabilidad

{fig('f06_estabilidad_comparaciones.png', 'Figura 6. Estabilidad de las comparaciones frente a su p ajustado.')}

- **Muchas diferencias marcadas reaparecen** en más del 70 % de las submuestras: {', '.join(f'{NOM(g).lower()} {e((Hs[g]["clase"].str.startswith("H3") & Hs[g]["estable"]).sum())}' for g in N.DIMENSIONES)}.
- **Todas son compatibles con la nula.** Como en la Fase 38, las submuestras del 80 % comparten casi todos los datos, así que la estabilidad no distingue señal de azar. **No demuestra validez.**

# Composición y grupos pequeños

**Composición distinta.** Un antecedente cuya prevalencia difiere al menos 20 puntos entre estratos cambia la composición de cada comparación. Entre las diferencias marcadas hay: {', '.join(f'{NOM(g).lower()} {e((Hs[g]["marcada"] & Hs[g]["composicion_distinta"]).sum())}' for g in N.DIMENSIONES)}.

**Grupos pequeños.** {e(PEQ[PEQ['conjunto'] == 'marcadas']['con_menos_de_30_en_algun_estrato'].sum())} de las {e(PEQ[PEQ['conjunto'] == 'marcadas']['comparaciones'].sum())} diferencias marcadas se apoyan en menos de 30 participantes con el antecedente en algún estrato.

**Diferencias ligadas al estrato.** En ejercicio, {e(Hs['ejercicio']['ligada_a_estrato'].sum())} comparaciones usan frecuencias de modalidades de ejercicio. Dependen de la variable del estrato y se marcan como «ligadas».

# Conclusión de este informe

**No hay evidencia de que la asociación entre características y severidad difiera entre estratos.** Lo que se observa son, a lo sumo, diferencias de significación y diferencias de magnitud compatibles con el azar.
""")

# ---------- 13 redundancia
RR = L('redundancia/reglas_redundantes_estratos.csv')
docs['13_redundancia'] = ('Análisis de redundancia', f"""
# Criterios

{SINT}

**Dentro de un estrato.** Se aplica el criterio de la Fase 38: una regla de 2 o 3 condiciones es redundante si una regla más simple, en la misma dirección, tiene una confianza menor en menos de 5 puntos.

**Entre estratos.** Una diferencia para un antecedente de dos condiciones es redundante si una de sus condiciones, sola, produce un rango de diferencias de riesgo mayor o igual al del par menos 0,05.

**Además se marcan:**
- **Ligadas al estrato:** las frecuencias de modalidades de ejercicio dentro de la dimensión ejercicio.
- **Próximas a síntomas:** actividad sexual, distensión y evacuación.
- **Con módulos:** las preguntas laborales y la sobrecarga, que solo aparecen en S7a y S7b.

# Dentro de los estratos

{tabla(['Dimensión', 'Estrato', 'Reglas', 'Marcadas', 'Marcadas redundantes', '% redundantes', 'Marcadas con variable próxima a síntomas'],
       [[NOM(d_), NOM(x), e(len(t)), e(t['marcada'].sum()), e((t['marcada'] & t['redundante'].fillna(False).astype(bool)).sum()),
         pc((t['marcada'] & t['redundante'].fillna(False).astype(bool)).sum() / max(t['marcada'].sum(), 1), 0), e((t['marcada'] & t['proxima_a_sintomas']).sum())]
        for (d_, x), t in TODAS.groupby(['dimension', 'estrato'], sort=False)])}

En total, {e(TOT_RED)} de {e(TOT_MARC)} reglas marcadas ({pc(TOT_RED / TOT_MARC, 0)}) son redundantes: agregar una condición casi no cambia la confianza.

**Ejemplos:**

{tabla(['Estrato', 'Regla', 'Confianza', 'Regla más simple casi igual', 'Mejora'], [[NOM(r.estrato), regla_txt(r.antecedente, r.consecuente), pc(r.confianza), N.legible_regla(r.subregla_mas_cercana), f'{n(100 * r.mejora_sobre_subreglas, 1)} pts'] for r in RR.sort_values('confianza', ascending=False).head(10).itertuples()])}

# Entre estratos

{tabla(['Dimensión', 'Diferencias marcadas', 'Redundantes', 'Con variable próxima a síntomas', 'Ligadas al estrato'], [[NOM(g), e(Hs[g]['marcada'].sum()), e((Hs[g]['marcada'] & Hs[g]['redundante']).sum()), e((Hs[g]['marcada'] & Hs[g]['proxima_a_sintomas']).sum()), e(Hs[g]['ligada_a_estrato'].sum())] for g in N.DIMENSIONES])}

**Patrón típico de las diferencias redundantes:** una condición que ya difiere entre estratos, como «0 días de ejercicio» en la dimensión trabajo, más otra que casi no aporta.

**No confundir con reglas independientes.** Una diferencia entre estratos no es una regla independiente, y una regla dentro de un estrato no es una diferencia entre estratos. Las tablas los mantienen separados.
""")

# ---------- 14 sensibilidades
lec = LECT.copy()
docs['14_sensibilidades'] = ('Sensibilidades', f"""
# Resumen

{SINT}

Todas las sensibilidades se fijaron en el protocolo antes de ejecutar. Cada una repite la búsqueda en cada estrato y la comparación entre estratos, con sus propias {e(N.N_PERM)} permutaciones.

# Reglas dentro de los estratos

{tabla(['Sensibilidad', 'Cambio', 'Reglas', 'Marcadas', 'Nula: media', 'Estratos con exceso (p < 0,05)', 'Superan la nula del estrato'],
       [[s, N.SENSIBILIDADES[s], e(t['reglas'].sum()), e(t['marcadas'].sum()), e(round(t['nula_media_marcadas'].sum())), f"{e((t['p_exceso_marcadas'] < 0.05).sum())} de {len(t)}", e(t['supera_nula_estrato'].sum())]
        for s, t in SR.groupby('sensibilidad', sort=False)])}

**Reglas que superan la nula de su estrato en alguna sensibilidad:**

{tabla(['Sensibilidad', 'Estrato', 'Regla', 'n (con / antecedente)', 'Confianza', 'Basal', 'p ajustado (estrato)', 'p ajustado (conjunto)'],
       [[r.sensibilidad, NOM(r.estrato), regla_txt(r.antecedente, r.consecuente), f'{e(r.n_conjunto)} de {e(r.n_antecedente)}', pc(r.confianza), pc(r.frecuencia_basal), p_(r.p_ajustado_estrato), p_(r.p_ajustado_conjunto)] for r in SUPS.itertuples()])}

**Lectura:**
- **Cada regla aparece en una sola configuración.** No se repite en la principal ni en las demás sensibilidades.
- **Casi ninguna supera la nula conjunta.** La única excepción es la de S7b, donde la nula conjunta coincide con la del estrato, porque S7b tiene un solo estrato.
- **La regla de S7b** (quienes cuidan: sobrecarga frecuente, sin ejercicio aeróbico y 3-4 vasos de agua → severos; 31 de 34) es la misma que apareció en la S7b de la Fase 38. Incluye la sobrecarga por cuidar, que puede ser consecuencia de los síntomas, y se apoya en 34 participantes.
- **Las reglas de una condición en S4-1** (por ejemplo, ejercicio de bajo impacto frecuente → no severos, en quienes trabajan y en quienes cuidan) **coinciden con la regla simple más fuerte de la Fase 38**, que tampoco superaba la nula general.

**Ninguna de estas reglas es robusta.**

# Comparación entre estratos

{tabla(['Sensibilidad', 'Dimensión', 'Comparables', 'Marcadas', 'Nula: media', 'p de exceso', 'Superan la nula de la dimensión'],
       [[r.sensibilidad, NOM(r.grupo) if r.grupo in N.DIMENSIONES else r.grupo, e(r.comparables) if not pd.isna(r.comparables) else '—', e(r.marcadas) if not pd.isna(r.marcadas) else '—',
         e(round(r.nula_media_marcadas)) if not pd.isna(r.nula_media_marcadas) else '—', p_(r.p_exceso_marcadas) if not pd.isna(r.p_exceso_marcadas) else '—',
         e(r.supera_nula_dimension) if not pd.isna(r.supera_nula_dimension) else (r.nota if isinstance(r.nota, str) else '—')] for r in SH.itertuples()])}

**Una sola diferencia supera la nula de su dimensión, en una sola sensibilidad (S3-bajo, ejercicio):**

{tabla(['Antecedente', '0 días', '1-2 días', '3 días o más', 'p ajustado (dimensión)', 'p ajustado (conjunto)'],
       [[N.legible_regla(r['antecedente']), *[f"{e(r[f'nAC_{x}'])}/{e(r[f'nA_{x}'])} · DR {n(r[f'DR_{x}'], 2)}" for x in N.dims_de('ejercicio')], p_(r['p_ajustado_dimension']), p_(r['p_ajustado_conjunto'])] for _, r in S3B.iterrows()])}

**Por qué no es un hallazgo:**
- **Depende de un grupo mínimo:** 18 participantes del estrato de 3 días o más, **ninguna** con síntomas severos.
- **Solo aparece con el umbral bajo:** con 15 participantes por estrato es comparable; con el umbral principal de 20, no lo es.
- **No supera la nula conjunta** de las 4 dimensiones.
- **Es el tipo de resultado** que el protocolo anticipó al pedir revisar los grupos pequeños.

# Qué ocurre con las diferencias marcadas de la principal

{tabla(['Dimensión', 'Sensibilidad', 'Se mantiene', 'Se debilita', 'Cambia de dirección', 'No evaluable'], [[NOM(r.dimension), r.sensibilidad, e(getattr(r, 'se_mantiene', 0)), e(getattr(r, 'se_debilita', 0)), e(getattr(r, 'cambia_de_dirección', 0)), e(getattr(r, 'no_evaluable', 0))] for r in lec.rename(columns=lambda c: c.replace(' ', '_')).itertuples()])}

{fig('f05_sensibilidades_comparaciones.png', 'Figura 5. Diferencias marcadas de la principal en cada sensibilidad.')}

**Lectura:**
- **S3:** las diferencias se mantienen siempre que siguen siendo comparables, porque los datos son los mismos y solo cambia qué antecedentes entran. S3 sirve para ver si el umbral cambia la conclusión, y no la cambia.
- **S1 (sin imputados):**
  - las diferencias pierden casos y varias se debilitan;
  - en ejercicio, {e(LECT[(LECT['dimension'] == 'ejercicio') & (LECT['sensibilidad'] == 'S1')]['cambia de dirección'].sum())} cambian de dirección: el estrato de 3 días o más queda con muy pocos casos;
  - las comparaciones se apoyan en parte en los datos imputados.
- **S9 (sin el estrato de 3 días o más):** en ejercicio, {e(LECT[(LECT['dimension'] == 'ejercicio') & (LECT['sensibilidad'] == 'S9')]['se debilita'].sum())} diferencias marcadas se debilitan. Dependían del grupo pequeño.
- **S4-1:** con una sola condición, casi ninguna diferencia es evaluable. Las de una condición se mantienen, pero ninguna supera la nula.

**Módulos (S7a y S7b):**
- **S7a (quienes trabajan, con el módulo laboral):** hay exceso de reglas marcadas (p {p_(SR[SR['sensibilidad'] == 'S7a']['p_exceso_marcadas'].iloc[0])}), pero ninguna supera la nula. Las preguntas laborales mencionan los síntomas, así que cualquier regla con ellas sería circular.
- **S7b:** ver la regla de arriba.

**Dependencia entre antecedentes.** {e(DEP['composicion_distinta'].sum())} ítems cambian su prevalencia al menos 20 puntos entre los estratos de alguna dimensión (`sensibilidades/dependencia_items_estratos.csv`). Casi todos son de ejercicio (frecuencias de modalidades) y de trabajo (comidas fuera de casa, falta de tiempo).
""")

# ---------- 15 A/B1
docs['15_comparacion_exploratoria_A_B1'] = ('Comparación exploratoria A y B1', f"""
# Alcance

{SINT}

**Uso:** A (P2_c12_km_k4, K-means sobre PCA sin IMC) y B1 (regla de cuatro pasos sobre trabajo, pareja y ejercicio) se usan **solo como comparación exploratoria secundaria**:
- con sus etiquetas históricas, sin reajustar;
- sin presentarlas como segmentaciones naturales ni clínicamente validadas;
- sin elegir entre ellas.

**Variables excluidas:** dentro de los grupos se excluyen trabajo, pareja y días de ejercicio, porque casi determinan los grupos.

# Tamaños, basales y búsqueda dentro de cada grupo

{tabla(['Grupo', 'n', 'Severas', 'Basal (IC 95 %)', 'Largo', 'Reglas', 'Marcadas', 'Nula: media', 'p de exceso', 'Superan la nula del grupo'],
       [[r.estrato.replace('_', ' '), e(r.n), e(r.n_si), f'{pc(r.frecuencia_basal_si)} ({pc(r.ic_basal_inf, 0)}-{pc(r.ic_basal_sup, 0)})', r.largo_maximo, e(r.reglas), e(r.marcadas), e(round(r.nula_media_marcadas)), p_(r.p_exceso_marcadas), e(r.supera_nula_estrato)] for r in ABG.itertuples()])}

- **A1 y B1-1 (76 y 79 participantes):** solo admiten antecedentes de una condición y casi no tienen reglas posibles.
- **Ningún grupo** tiene reglas que superen su nula.
- **Ningún grupo** tiene más reglas marcadas que por azar (p ≥ {p_(ABG['p_exceso_marcadas'].min())}).

# Composición: A y B1 dependen de trabajo, pareja y ejercicio

{tabla(['Grupo', 'Trabaja', 'Tiene pareja', '0 días', '1-2 días', '3 días o más'],
       [[f"{g} {k}", *[pc(ABCOMP[(ABCOMP['grupo'] == g) & (ABCOMP['etiqueta'] == k) & (ABCOMP['estrato'] == x)]['proporcion_del_grupo'].iloc[0], 0) for x in ('trabaja', 'con_pareja', '0_dias', '1-2_dias', '3_o_mas_dias')]]
        for g in ('A', 'B1') for k in range(4)])}

**Coincidencia entre A y B1:** {e(sum(int(ABX.iloc[i][str(i)]) for i in range(4)))} de 529 participantes ({pc(sum(int(ABX.iloc[i][str(i)]) for i in range(4)) / 529, 0)}) caen en el grupo correspondiente de ambas.

**Qué son los grupos de B1:**
- **B1-1** son exactamente quienes hacen 3 días o más de ejercicio, igual que el estrato de la dimensión ejercicio.
- **B1-0** son quienes no tienen pareja y hacen menos de 3 días.
- **B1-2** son quienes tienen pareja, no trabajan y hacen menos de 3 días.
- **B1-3** son quienes tienen pareja, trabajan y hacen menos de 3 días.

Por eso, comparar por A o B1 repite en gran parte las comparaciones por trabajo, pareja y ejercicio.

# Comparación entre los 4 grupos

{tabla(['Clasificación', 'Comparables', 'Marcadas', 'Nula: media', 'p de exceso', 'p95 del máximo Q nulo', 'Superan la nula'], [[r.grupo, e(r.comparables), e(r.marcadas), e(round(r.nula_media_marcadas)), p_(r.p_exceso_marcadas), n(r.nula_p95_max_Q, 1), e(r.supera_nula_dimension)] for r in ABC.itertuples()])}

**Ninguna diferencia de asociación entre los grupos de A o de B1 supera la referencia nula.**

# Qué aporta

- **Basales:** confirma descriptivamente que hay grupos con basales muy distintas. A1 tiene 38 % de severas y B1-1 33 %, frente a 58-61 % en A0, A3, B1-0 y B1-3. Ese contraste es esencialmente el del ejercicio.
- **Asociaciones:** no aporta evidencia de que las asociaciones de los hábitos con la severidad cambien de un grupo a otro.
- **Valor:** como descripción del contexto, no como base de reglas.
""")

# ---------- 16 figuras y tablas
figs = sorted((B / 'figuras').glob('*.png'))
tablas = sorted(p.relative_to(B).as_posix() for d_ in ('preparacion', 'reglas', 'referencia_nula', 'estabilidad', 'comparacion', 'redundancia', 'sensibilidades', 'ab1', 'resultados')
                for p in (B / d_).rglob('*') if p.suffix in ('.csv', '.json') and not any(x.startswith('lotes') for x in p.parts) and 'matrices' not in p.parts and p.parent.name not in ('S1', 'S2a', 'S3-bajo', 'S3-alto', 'S4-1', 'S4-2', 'S5', 'S6', 'S7a', 'S7b', 'S9'))
docs['16_figuras_tablas'] = ('Figuras y tablas', f"""
# Contenido

{SINT}

- **Figuras:** {len(figs)}, generadas con `scripts/graficos_39.py` desde las tablas guardadas.
- **Tablas principales:** {len(tablas)}.
- **Otras tablas:** las matrices por estrato están en `preparacion/matrices/`; las tablas de cada sensibilidad, en `sensibilidades/reglas/` y `sensibilidades/comparacion/`.
- **Lotes reanudables:** los de permutaciones y submuestras están en las carpetas `lotes*`.

# Tablas

{tabla(['Archivo'], [[t] for t in tablas])}

# Figuras
""" + '\n'.join(fig(p.name, p.stem.replace('_', ' ')) for p in figs))

# ---------- 20 nota tablero
docs['20_nota_logica_tablero'] = ('Nota para implementar la lógica del tablero', f"""
# Alcance

Esta nota prepara la siguiente fase de implementación. **No implementa nada ni modifica Django.**

{SINT}

**Estado actual de la plataforma** (revisado sin modificarlo):
- **Tablero:** `src/apps/encuestas/tablero.py` muestra a la usuaria sus datos, el historial de rondas y el **puntaje MRS crudo** de cada una.
- **MRS:** el modelo `MRS` ya suma los 11 ítems (`puntaje_total`) y define cortes de severidad (`SEVERIDAD_TOTAL`: hasta 4 sin síntomas o muy leves, hasta 8 leve, hasta 15 moderada, 16 o más severa). El código anota que esos cortes están **pendientes de confirmación de la profesora**.
- **Pendiente:** el «grupo de caracterización» está pendiente del algoritmo del equipo de investigación (decisión del 2026-09-24).
- **Sin motor:** no hay un motor de orientaciones.

# Componente 1: asignación reproducible del segmento descriptivo

**Qué permiten los análisis 37 a 39:** si la profesora decide mostrar un segmento, solo como **etiqueta descriptiva del contexto**:
- **Cómo:** B1 es una regla de cuatro pasos sobre tres respuestas de la encuesta (ejercicio de 3 días o más; sin pareja; sin trabajo; con trabajo). Es trazable, determinista y no necesita modelos.
- **Por qué no A:** A requiere los artefactos de PCA y K-means de la Fase 37 y no aporta información adicional (el complemento de la 37C lo mostró). No se recomienda llevarla a producción.

**Qué no permiten:**
- presentar el segmento como un **perfil de riesgo**, ni decirle a una usuaria que «su grupo tiene más síntomas»;
- usar las basales de la Tabla 5 en el tablero. Vienen de datos sintéticos, son marginales y no ajustadas.

**Requisitos si se implementa:**
- función pura y probada que reciba las tres respuestas y devuelva la etiqueta;
- versión de la regla guardada junto a la asignación;
- recálculo si la usuaria cambia sus respuestas en otra ronda;
- texto neutro que describa la situación, no la severidad;
- aprobación de la profesora y, más adelante, confirmación con datos reales.

# Componente 2: cálculo y visualización individual del MRS

Esto **no depende** de ninguna asociación. Es directamente utilizable, porque es la escala misma.

- **Cálculo:** el puntaje total ya está implementado.
- **Dimensiones:** se pueden agregar la somática (ítems 1-4), la psicológica (5-8) y la urogenital (9-11), con la misma definición que el análisis.
- **Severidad:** mantener los cortes del MRS, cuando la profesora los confirme. El umbral «severo ≥ 16» del análisis coincide con la categoría «Severa» de la plataforma.
- **Visualización:** la evolución entre rondas de la misma usuaria; sin compararla con promedios sintéticos.

# Componente 3: selección de orientaciones educativas personalizadas

**Ningún resultado de las Fases 37D, 38 y 39 debe transformarse en una regla de orientación.**

- **Fase 38:** solo dejó una regla en la clase de asociación relativamente más marcada, y era frágil.
- **Fase 39:** ninguna regla supera la nula dentro de los estratos, y no hay diferencias de asociación entre estratos.
- **Las asociaciones encontradas son débiles, sintéticas, no causales** y en parte dependen de imputaciones y de variables próximas a los síntomas.

**Recomendación para el futuro motor:**
1. **Criterios explícitos:** un catálogo de orientaciones educativas en que cada entrada tenga una condición de activación clara, basada en respuestas de la encuesta (por ejemplo, «no realiza actividad física» o «consume menos de 2 vasos de agua»), y **no** en asociaciones estadísticas.
2. **Fuentes trazables:** cada orientación cita una fuente sanitaria confiable (guías del Ministerio de Salud de Chile, OMS u otras que la profesora indique), con fecha y versión.
3. **Revisión obligatoria** de la profesora antes de activar cada orientación, y registro de quién la aprobó.
4. **Tono educativo:** no clínico, sin prometer efectos sobre los síntomas, con la indicación de consultar a un profesional de salud ante síntomas severos.
5. **Separación:** el puntaje MRS puede decidir **cuándo** sugerir consultar, según los cortes de la escala aprobados. No debe decidir **qué hábito cambiar** a partir de asociaciones sintéticas.
6. **Trazabilidad técnica:** registrar qué orientación se mostró, por qué regla del catálogo y con qué versión, para poder auditarlo.
7. **Validación futura:** si se obtienen datos reales, repetir las Fases 38 y 39 con un protocolo sellado antes de considerar asociaciones como contexto, nunca como prescripción.

# Resumen

{tabla(['Resultado del análisis', '¿Puede mostrarse en el tablero?', 'Condición'], [
    ['Puntaje MRS total y por dimensión, y su evolución', 'Sí', 'Escala estándar; cortes de severidad confirmados por la profesora'],
    ['Etiqueta descriptiva B1 (trabajo, pareja, ejercicio)', 'Solo si la profesora lo decide', 'Texto neutro, sin implicar riesgo; regla versionada'],
    ['Basales por estrato o grupo', 'No', 'Datos sintéticos; no individuales'],
    ['Reglas de asociación (Fases 38 y 39)', 'No', 'Débiles o compatibles con el azar; no causales'],
    ['Diferencias entre estratos', 'No', 'No hay evidencia de que existan'],
    ['Orientaciones educativas', 'Sí, desde un catálogo explícito', 'Criterios de fuentes sanitarias y revisión de la profesora'],
])}
""")

# ---------- 19 cierre
dims_txt = {}
for dim in N.DIMENSIONES:
    partes = []
    for x in N.dims_de(dim):
        r, b = fila_estrato(dim, x)
        partes.append(f"{NOM(x).lower()}: {e(r['marcadas'])} reglas marcadas frente a {e(round(r['nula_media_marcadas']))} por azar (p {p_(r['p_exceso_marcadas'])})")
    dims_txt[dim] = '; '.join(partes)
res_txt = CONC['texto']
docs['19_informe_cierre_39'] = ('Informe metodológico de cierre de la Fase 39', f"""
# Conclusión

**Resultado {CONC['resultado']}: {res_txt}**

La conclusión se obtuvo de forma mecánica con los criterios sellados (sección 13 del protocolo):
- **Diferencias consistentes entre estratos:** ninguna; ni siquiera hay comparaciones que superen la nula de su dimensión.
- **Reglas que superan la nula de su estrato:** ninguna.

**La señal difusa de la Fase 38 se mantiene en cuatro de los estratos grandes** (trabaja, tiene pareja, 0 días y cuida): hay más reglas marcadas que por azar. Pero no se concentra en reglas puntuales ni cambia de forma demostrable según el trabajo, la pareja, el ejercicio o el cuidado.

{SINT}

# Respuestas

**1. ¿Cuántas participantes forman cada estrato?**

| Dimensión | Estratos |
|---|---|
| Trabajo | trabaja 309, no trabaja 220 |
| Pareja | tiene pareja 356, no tiene pareja 173 |
| Ejercicio | 0 días 302, 1-2 días 148, 3 días o más 79 |
| Cuidado | cuida 251, no cuida 278 |

**Grupos secundarios:** A 150/76/132/171 y B1 150/79/126/174.

**2. ¿Cuál es la frecuencia basal de MRS severo en cada uno?**

{', '.join(f"{NOM(r.estrato).lower()} {pc(r.frecuencia_basal_si)}" for r in DIC[DIC['grupo'].isin(list(N.DIMENSIONES))].itertuples())}.

- **Diferencias claras de basal:** 3 días o más de ejercicio frente a 0 días (−25,7 puntos, IC −36,5 a −13,4) y frente a 1-2 días; trabaja frente a no trabaja (+10,8, IC 2,2 a 19,2).
- **Pareja y cuidado:** sus intervalos incluyen el 0.

**3. ¿Cuántas reglas se encontraron?**
- **Total:** {e(TOT_REGLAS)} reglas en los 9 estratos, de las cuales {e(TOT_MARC)} son marcadas (al menos 10 puntos sobre la basal del estrato).
- **Estratos grandes** (largo 3): entre unas 10.800 y 11.500 reglas cada uno.
- **Estratos medianos** (largo 2): entre 1.100 y 1.500.
- **3 días o más** (largo 1): 43 reglas.

**4. ¿Cuántas superaron su referencia nula?**
- **Principal:** **ninguna**, ni dentro de su estrato ni en la nula conjunta.
- **Sensibilidades:** {len(SUPS)} reglas superan la nula de su estrato en alguna, cada una en una sola configuración.
- **Comparaciones entre estratos:** ninguna supera la nula de su dimensión en la principal. En las sensibilidades, una sola, en S3-bajo, y depende de 18 participantes.

**5. ¿Qué reglas son redundantes?**
- **Dentro de los estratos:** {e(TOT_RED)} de las {e(TOT_MARC)} reglas marcadas ({pc(TOT_RED / TOT_MARC, 0)}). Agregan una condición que casi no cambia la confianza.
- **Entre estratos:** {e(sum(int((Hs[g]['marcada'] & Hs[g]['redundante']).sum()) for g in N.DIMENSIONES))} de {e(sum(int(Hs[g]['marcada'].sum()) for g in N.DIMENSIONES))} diferencias marcadas.

**6. ¿Qué asociaciones aparecen en quienes trabajan y quienes no?**
- **Exceso de reglas marcadas:** {dims_txt['trabajo']}.
- **Ninguna regla** supera la nula de su estrato.
- **Ninguna diferencia** entre ambos estratos supera la nula (menor p ajustado {p_(Hs['trabajo']['p_ajustado_dimension'].min())}).

**7. ¿Qué ocurre según la situación de pareja?**
- **Exceso de reglas marcadas:** {dims_txt['pareja']}.
- **Sin reglas que superen la nula** ni diferencias (menor p ajustado {p_(Hs['pareja']['p_ajustado_dimension'].min())}).
- **Coincidencia con la Fase 38:** la regla más fuerte de «tiene pareja» es la misma que fue de clase 6 en la Fase 38 (trabaja, sin bajo impacto, distensión casi nunca). Aquí no supera la nula (p {p_(TODAS[(TODAS['estrato'] == 'con_pareja')]['p_ajustado_estrato'].min())}).

**8. ¿Qué ocurre según los días de ejercicio?**
- **Exceso de reglas marcadas:** {dims_txt['ejercicio']}.
- **3 días o más:** solo admite reglas de una condición, y ninguna supera la nula.
- **Comparación entre los tres estratos:** es la más débil (menor p ajustado {p_(Hs['ejercicio']['p_ajustado_dimension'].min())}). Sin el estrato pequeño (S9) tampoco aparece nada.
- **Lo único claro** es la diferencia de basal: menos severas con 3 días o más.

**9. ¿Qué ocurre según las responsabilidades de cuidado?**
- **Exceso de reglas marcadas:** {dims_txt['cuidado']}.
- **Sin reglas ni diferencias** que superen la nula (menor p ajustado {p_(Hs['cuidado']['p_ajustado_dimension'].min())}).
- **Con la sobrecarga (S7b):** reaparece una regla ya vista en la Fase 38, con 34 participantes y potencialmente circular.

**10. ¿Hay evidencia de diferencias de asociación entre estratos o solo diferencias de significación?**
- **Solo diferencias de significación.** Cientos de antecedentes son nominalmente significativos en un estrato y no en el otro (por ejemplo, 207 en trabajo). Ninguna diferencia resiste la referencia nula de la búsqueda.
- **Diferencias marcadas:** su número es el que produce el azar en todas las dimensiones (p de exceso entre {p_(MH['p_exceso_marcadas'].min())} y {p_(MH['p_exceso_marcadas'].max())}).
- **Exceso de reglas dentro de los estratos:** aparece en los estratos grandes, no en los pequeños, pero eso refleja el tamaño y no prueba una interacción.

**11. ¿Cuáles se mantienen en sensibilidades?**
- **Nada que haya superado los controles,** porque nada los superó en la principal.
- **Dirección de las diferencias marcadas** (compatibles con el azar):
  - se mantiene con categorías originales (S2a), sin frecuencias de ejercicio (S5) y sin variables próximas a síntomas (S6);
  - se debilita o cambia sin imputados (S1);
  - en ejercicio, se debilita sin el estrato pequeño (S9).
- **El exceso de reglas marcadas** en los estratos grandes se mantiene en casi todas las sensibilidades.

**12. ¿Qué resultados podrían explicarse por azar?**
- **Todas** las reglas dentro de los estratos y **todas** las diferencias entre estratos.
- **Lo que no se explica del todo por azar:** el exceso global de reglas marcadas en los estratos grandes (la señal difusa) y las diferencias de basal (sobre todo, el ejercicio).

**13. ¿Qué limitaciones presentan los estratos pequeños?**
- **3 días o más (79 participantes, 26 severas):**
  - admite solo reglas de una condición;
  - en la comparación, muchas diferencias dependen de 20 a 30 participantes;
  - la única diferencia que superó una nula (S3-bajo) se apoyaba en 18 participantes y 0 severas.
- **Estratos de 148 a 220:** tienen menos poder, sin exceso detectable.
- **Diferencias marcadas con menos de 30 casos en algún estrato:** {e(PEQ[PEQ['conjunto'] == 'marcadas']['con_menos_de_30_en_algun_estrato'].sum())} de {e(PEQ[PEQ['conjunto'] == 'marcadas']['comparaciones'].sum())}.

**14. ¿Qué aporta la comparación complementaria A/B1?**
- **Confirma descriptivamente** basales distintas, sobre todo por el ejercicio (A1 38 %, B1-1 33 %).
- **Coincidencia:** A y B1 asignan al grupo correspondiente a {pc(sum(int(ABX.iloc[i][str(i)]) for i in range(4)) / 529, 0)} de las participantes.
- **Sin evidencia nueva:** no hay reglas que superen la nula dentro de los grupos ni diferencias entre ellos.
- **No agrega información** sobre la que ya dan trabajo, pareja y ejercicio por separado.

**15. ¿Se identificaron patrones suficientemente consistentes?** **No.**

**16. ¿Qué resultados no deben utilizarse para generar recomendaciones?**
- **Ninguna regla** dentro de los estratos.
- **Ninguna diferencia** entre estratos.
- **Ninguna basal** por estrato o grupo.
- **Ninguna regla de las sensibilidades**, incluidas las de S4-1 y S7b.
- **Ningún segmento de A o B1** como perfil de riesgo.

Todo es sintético, exploratorio y compatible con el azar o frágil.

**17. ¿Qué información puede mostrar descriptivamente el tablero?**
- **MRS:** el puntaje total y por dimensión, su categoría de severidad (con cortes confirmados por la profesora) y su evolución entre rondas.
- **Respuestas propias:** las de la usuaria.
- **Etiqueta B1 opcional:** solo si la profesora la aprueba, como descripción neutra del contexto (informe 20).

**18. ¿Qué necesita el futuro motor de orientaciones personalizadas?**
- **Catálogo:** orientaciones educativas con criterios de activación explícitos sobre las respuestas, cada una con su fuente sanitaria confiable.
- **Revisión:** aprobación de la profesora.
- **Funcionamiento:** versión, registro de lo mostrado y tono no clínico.
- **Separación:** el MRS solo indica cuándo sugerir consultar a un profesional, no qué hábito cambiar.
- **No debe basarse** en las asociaciones de estas fases (informe 20).

**19. ¿Qué pruebas se ejecutaron?**
- **Pruebas:** {int((PRU['resultado'] == 'superada').sum())} de {len(PRU)} superadas.
- **Controles negativos:** {int(MUT['detectado'].sum())} de {len(MUT)} errores introducidos detectados (informe 17).
- **Cobertura:**
  - identificadores, MRS, tamaños, basales y umbrales;
  - pertenencia recalculada desde las respuestas crudas;
  - codificación idéntica a la Fase 38;
  - ausencia de ítems del MRS, de contradicciones, de la variable del estrato y de ítems constantes;
  - medidas;
  - referencias nulas dentro de los estratos y entre ellos;
  - comparación recalculada de forma independiente;
  - calibración del estadístico de interacción por simulación;
  - búsqueda múltiple e imputaciones;
  - reproducibilidad;
  - etiquetas A y B1;
  - fases anteriores, Django y sello;
  - clasificación y conclusión.

**20. ¿Permanecieron intactas las fases anteriores?**
- **Sí.** {e(MAN_INI['comparados_por_huella'].sum())} archivos de las Fases 34 a 38 coinciden con sus manifiestos al inicio{' y al final' if FIN else ''}.
- **Simulador:** los 4 archivos del simulador no se abrieron.
- **Git y Django:** HEAD sigue en 745d689, sin cambios en Django ni en los datos, y sin commit ni push.

# Decisiones para la responsable

1. **Conclusión:** confirmar que la Fase 39 se lee como resultado C.
2. **Tablero:** decidir si se muestra una etiqueta descriptiva (B1) y con qué texto.
3. **Motor de orientaciones:** definir las fuentes sanitarias y el proceso de revisión antes de diseñarlo.
4. **Siguiente fase:** autorizarla de forma expresa.
""")

# ---------- 02 protocolo (Word desde el protocolo y la nota de modificaciones)
prot = (B / 'protocolo' / '01_protocolo_39.md').read_text(encoding='utf-8')
mods = (B / 'protocolo' / '02_modificaciones_posteriores.md').read_text(encoding='utf-8')
prot_md = prot.split('\n', 1)[1] + f"\n\n# Sello\n\n- **Huella SHA-256:** `{sello['sha256']}`.\n- **Fecha:** {sello['sellado']}.\n- **Antes de los resultados:** la prueba 20 comprueba que todos los resultados son posteriores al sello.\n\n# Anexo: modificaciones posteriores al sellado\n\n" + mods.split('\n', 1)[1]

# ---------- Markdown: 01, 03, 17, 18
pru_md = f"""# Fase 39: informe de pruebas

- **Pruebas:** {int((PRU['resultado'] == 'superada').sum())} de {len(PRU)} superadas.
- **Controles negativos:** {int(MUT['detectado'].sum())} de {len(MUT)} errores introducidos en memoria detectados.
- **Cómo funcionan:** cada prueba recalcula desde el código o desde los datos de origen. Cada control introduce un error, en los datos cargados o reemplazando una función, y exige que alguna prueba que antes pasaba falle.

{tabla(['N.º', 'Prueba', 'Resultado', 'Detalle'], [[r.n, r.prueba, r.resultado, r.detalle] for r in PRU.itertuples()])}

## Controles negativos

{tabla(['Error introducido', 'Detectado', 'Pruebas que fallan'], [[r.control_negativo, 'sí' if r.detectado else 'NO', r.pruebas_que_fallan] for r in MUT.itertuples()])}

## Notas

- **Pruebas lentas:** la 16 (reproducibilidad) y la 18 (manifiestos) se ejecutan en los controles negativos solo cuando corresponden: con la semilla distinta y con el archivo histórico modificado.
- **Primera ejecución:** la prueba 16 falló porque comparaba los p ajustados como texto y el último decimal cambia al releer el CSV. Ahora compara numéricamente (`protocolo/02_modificaciones_posteriores.md`).
"""
leidos = pd.read_csv(B / 'integridad' / 'archivos_leidos.csv')['archivo_leido']
integ_ini = f"""# Fase 39: auditoría de integridad inicial

Hecha justo después de sellar el protocolo y antes de cualquier búsqueda.

- **Fecha:** {INI['fecha']}.
- **Protocolo:** sellado el {INI['protocolo_sellado']}, huella `{INI['protocolo_sha256']}`.
- **Git:** rama `{INI['rama']}`, HEAD {INI['head']}. Sin cambios en `src/` (Django), sin cambios en datos versionados y sin cambios fuera de `analisis/`.
- **`__pycache__` en fases protegidas:** {len(INI['pycache_en_fases_protegidas'])}.

{tabla(['Fase', 'Archivos', 'Comparados por huella', 'Sin verificar por nombre', 'Distintos'], [[r.fase, e(r.archivos), e(r.comparados_por_huella), e(r.sin_verificar_por_nombre), e(r.distintos)] for r in MAN_INI.itertuples()])}

**Archivos sin verificar:** los 4 del manifiesto 34-35 corresponden al simulador. Este proceso no los abre; el gancho de auditoría lo impide.

**Huellas de las entradas:** están en `integridad/huellas_entradas_inicial.csv`. Las entradas son:
- los datos limpios, la Fase 35 y la Fase 36;
- las etiquetas A y B1 y la definición de B1;
- los núcleos de las Fases 37D y 38, que se importan sin escribir en sus carpetas;
- la matriz principal de la Fase 38;
- el modelo de la encuesta, de solo lectura;
- el conversor a Word.
"""
fin_txt = ''
if FIN:
    fin_txt = f"""
## Verificación final

- **Fecha:** {FIN['fecha']}.
- **Archivos protegidos:** {e(FIN['comparados_por_huella'])} comparados por huella, {FIN['archivos_distintos']} distintos.
- **Entradas:** iguales al inicio: {'sí' if FIN.get('entradas_iguales_al_inicio') else 'NO'}.
- **Git:** HEAD {FIN['head']}; cambios en `src/`: {len(FIN['cambios_en_src'])}; cambios fuera de `analisis/`: {len(FIN['cambios_fuera_de_analisis'])}; datos versionados modificados: {len(FIN['datos_versionados_modificados'])}.
- **`__pycache__` en fases protegidas:** {len(FIN['pycache_en_fases_protegidas'])}.
"""
integ_fin = f"""# Fase 39: informe de integridad final

- **Protocolo:** huella `{sello['sha256']}`, sellado el {sello['sellado']}, antes de cualquier búsqueda (prueba 20).
- **Lecturas fuera de la carpeta:** {e(len(leidos))} archivos, casi todos para comparar huellas con los manifiestos. Registro: `integridad/archivos_leidos.csv`.
- **Simulador:** no se leyó ningún archivo del simulador.
- **Escrituras fuera de la carpeta:** {len(pd.read_csv(B / 'integridad' / 'escrituras_fuera.csv'))}.
- **Fases 37D y 38:** sus scripts se importaron con la escritura de bytecode desactivada. Sus carpetas no cambiaron y no tienen `__pycache__`.
- **Memoria:** un proceso de análisis más el vigilante, con un hilo por biblioteca. La memoria libre mínima registrada estuvo cerca de 0,73 GB, sobre el límite de 0,7 GB. Registro: `integridad/registro_memoria.csv`.
- **Manifiesto:** `integridad/manifiesto_final.csv`.
{fin_txt}
## Restricciones

Se cumplieron todas:

- **Fases y datos:** sin cambios en las Fases 34 a 38 ni en los datos originales.
- **Simulador y agrupamientos:** sin la verdad del simulador y sin recalcular ni seleccionar agrupamientos (A y B1 se usaron con sus etiquetas históricas).
- **Recomendaciones e integración:** sin recomendaciones clínicas, sin modificar Django y sin iniciar la integración del tablero.
- **Git:** sin commit ni push.
"""
filas_idx = [
    (1, 'Índice de entregables', '`informes/01_indice_entregables.md`'),
    (2, 'Protocolo sellado', '`informes/02_protocolo_39.docx`, `protocolo/01_protocolo_39.md`, `protocolo/sello_protocolo.json`, `protocolo/02_modificaciones_posteriores.md`'),
    (3, 'Integridad inicial', '`informes/03_integridad_inicial.md`, `integridad/integridad_inicial.json`'),
    (4, 'Diccionario de estratos', '`informes/04_diccionario_estratos.docx`, `preparacion/diccionario_estratos.csv`, `preparacion/pertenencia_estratos.csv`'),
    (5, 'Tamaños y frecuencias basales', '`informes/05_tamanos_frecuencias_basales.docx`, `preparacion/diferencias_basales.csv`'),
    (6, 'Preparación de las matrices condicionadas', '`informes/06_preparacion_matrices_condicionadas.docx`, `preparacion/matrices/`, `preparacion/verificacion_codificacion.json`'),
    (7, 'Reglas por trabajo', '`informes/07_reglas_por_trabajo.docx`, `reglas/trabajo/`, `comparacion/comparacion_trabajo.csv`'),
    (8, 'Reglas por pareja', '`informes/08_reglas_por_pareja.docx`, `reglas/pareja/`, `comparacion/comparacion_pareja.csv`'),
    (9, 'Reglas por ejercicio', '`informes/09_reglas_por_ejercicio.docx`, `reglas/ejercicio/`, `comparacion/comparacion_ejercicio.csv`'),
    (10, 'Reglas por cuidado', '`informes/10_reglas_por_cuidado.docx`, `reglas/cuidado/`, `comparacion/comparacion_cuidado.csv`'),
    (11, 'Referencias nulas por estrato', '`informes/11_referencias_nulas_estrato.docx`, `referencia_nula/`'),
    (12, 'Comparación formal entre estratos', '`informes/12_comparacion_formal_estratos.docx`, `comparacion/`'),
    (13, 'Análisis de redundancia', '`informes/13_redundancia.docx`, `redundancia/`'),
    (14, 'Sensibilidades', '`informes/14_sensibilidades.docx`, `sensibilidades/`'),
    (15, 'Comparación exploratoria A y B1', '`informes/15_comparacion_exploratoria_A_B1.docx`, `ab1/`'),
    (16, 'Figuras y tablas', '`informes/16_figuras_tablas.docx`, `figuras/`'),
    (17, 'Informe de pruebas', '`informes/17_informe_pruebas.md`, `pruebas/`'),
    (18, 'Integridad final', '`informes/18_informe_integridad_final.md`, `integridad/`'),
    (19, 'Informe metodológico de cierre', '`informes/19_informe_cierre_39.docx`, `resultados/conclusion_39.json`'),
    (20, 'Nota para implementar la lógica del tablero', '`informes/20_nota_logica_tablero.docx`'),
]
indice = f"""# Fase 39: índice de entregables

**Conclusión:** resultado {CONC['resultado']}. {res_txt}

{tabla(['N.º', 'Entregable', 'Archivos'], filas_idx)}

**Resumen:** `informes/resumen_39.json`.

**Scripts:** `scripts/`. Orden de ejecución:

1. `sellar_protocolo_39.py`
2. `integridad_39.py inicial`
3. `preparacion_39.py`
4. `estratos_39.py`
5. `ab1_39.py`
6. `sensibilidades_39.py`
7. `significacion_39.py` (exploratorio)
8. `graficos_39.py`
9. `pruebas_39.py --mutaciones`
10. `generar_informes_39.py`
11. `verificar_informes_39.py`
12. `integridad_39.py final`
13. `manifiesto_39.py`

Las etapas de cálculo corren bajo `vigilar_memoria.py`.
"""
for nombre, t in (('17_informe_pruebas.md', pru_md), ('03_integridad_inicial.md', integ_ini), ('18_informe_integridad_final.md', integ_fin), ('01_indice_entregables.md', indice)):
    (INF / nombre).write_text(t, encoding='utf-8', newline='\n')
N.a_json({'fase': '39', 'participantes': 529, 'estratos': {f'{d_}:{x}': int(DIC[(DIC.grupo == d_) & (DIC.estrato == x)]['participantes'].iloc[0]) for d_, x in N.ESTRATOS},
          'reglas_en_estratos': TOT_REGLAS, 'marcadas': TOT_MARC, 'superan_nula_estrato': int(TODAS['supera_nula_estrato'].sum()),
          'comparaciones': int(sum(len(h) for h in Hs.values())), 'comparaciones_superan_nula': int(sum(h['supera_nula_dimension'].sum() for h in Hs.values())),
          'resultado': CONC['resultado'], 'conclusion': res_txt, 'pruebas': f"{int((PRU['resultado'] == 'superada').sum())}/{len(PRU)}",
          'controles_negativos': f"{int(MUT['detectado'].sum())}/{len(MUT)}", 'protocolo_sha256': sello['sha256']}, INF / 'resumen_39.json')

js = N.N37.C37 / 'scripts' / 'md_a_word_37c.js'
(F / '02_protocolo_39.md').write_text(prot_md, encoding='utf-8', newline='\n')
titulos = {'02_protocolo_39': 'Protocolo de la Fase 39'}
for nombre, (titulo, md) in docs.items():
    (F / f'{nombre}.md').write_text(md.strip() + '\n', encoding='utf-8', newline='\n')
    titulos[nombre] = titulo
for nombre, titulo in titulos.items():
    r = subprocess.run(['node', str(js), str(F / f'{nombre}.md'), str(INF / f'{nombre}.docx'), titulo, 'AgingWomen · Fase 39: asociaciones condicionadas'], capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f'{nombre}: {r.stderr[:500]}')
print(len(titulos), 'informes Word')
