"""
Informe académico en Word de la revisión corregida de 33 variables, Fase 35B.

Solo lee resultados de reunion_2026-11-03/revision_33_variables/: no calcula permutaciones ni modifica el informe de
34 variables, que se conserva como versión histórica. Sus salidas son el .docx y las figuras de informe/figuras/.

Requiere python-docx (fuera de las dependencias del proyecto). Uso, desde analisis/: python informe_word_33.py
"""
import re

import numpy as np
import pandas as pd
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml
from docx.shared import Cm, Pt, RGBColor

import informe_integrado_35b as I
import informe_word_35b as W
import revision_33_variables as T
import revision_35b_reunion_1103 as R
import seleccionar_fase35b as P
from eda import variables as V
from informe_word_35b import (AZUL_OSCURO, CATALOGO, FIG_CORREGIDA, LOG2, M_NS, POR_NIVEL, RELACION, SOBRECARGA, Informe, categoria_legible, lista_y, m_frac, m_r, m_raiz, m_sub, m_suma, nombre, p1, p3, p4, p5, poblacion, r1, r3, rr, si)

CARPETA = T.CARPETA / 'informe'
FIGURAS = CARPETA / 'figuras'
SALIDA = CARPETA / 'informe_fase35b_33_variables.docx'
RIESGO, PROTECCION, SIN_DIRECCION = W.RIESGO, W.PROTECCION, W.SIN_DIRECCION
INDICIOS_RIESGO = [v for v in W.INDICIOS_RIESGO if v != T.EXCLUIDA]
INDICIOS_PROTECCION = W.INDICIOS_PROTECCION
CATALOGO = [f for f in CATALOGO if f[1] != T.EXCLUIDA]
EFECTOS = [(n.replace('excluida de las 34', 'excluida de las 33'), v, e, u) for n, v, e, u in W.EFECTOS]


def leer_version(carpeta):
    t = {n: pd.read_csv(carpeta / f'{n}.csv', encoding='utf-8-sig', keep_default_na=False, na_values=[''], dtype={'cat_baja': str, 'cat_alta': str, 'eliminada_por': str, 'etapa': str})
         for n in ('poblaciones', 'orientacion_escalas', 'shannon_componentes', 'relevancia_33', 'incertidumbre_monte_carlo', 'pares_relevantes', 'decisiones_fcbf', 'pares_no_eliminados', 'su_todas_las_parejas', 'direccion_resumen', 'direccion_categorias', 'sensibilidades')}
    return T.alias(t)


def cargar():
    a, b = leer_version(T.VERSIONES[10000][2]), leer_version(T.VERSIONES[50000][2])
    c = pd.read_csv(CARPETA / 'comparacion_10000_50000.csv', encoding='utf-8-sig')
    previas = pd.read_csv(CARPETA / 'versiones_previas.csv', encoding='utf-8-sig', keep_default_na=False)
    comp = {n: pd.read_csv(T.CARPETA / 'comparacion_34_33' / f'comparacion_{n}.csv', encoding='utf-8-sig', keep_default_na=False, na_values=['']) for n in (10000, 50000)}
    dom = pd.read_csv(T.CARPETA / 'fase35a' / 'diagnostico_dominancia.csv', encoding='utf-8-sig', keep_default_na=False, na_values=[''])
    return a, b, c, previas, I.leer_version(R.SALIDA), comp, dom


def comprobar(a, b, c, comp):
    """El texto interpretativo solo es válido si los archivos dicen lo mismo; si no, no se genera el informe."""
    d = b['direccion_resumen'].set_index('variable')
    esperado = {'Posible factor de riesgo': RIESGO, 'Posible factor de protección': PROTECCION, 'Asociación sin dirección clara': SIN_DIRECCION,
                'Indicio de riesgo (solo orden)': INDICIOS_RIESGO, 'Indicio de protección (solo orden)': INDICIOS_PROTECCION}
    for clase, variables in esperado.items():
        if sorted(d.index[d['clase'] == clase]) != sorted(variables):
            raise RuntimeError(f'La clase «{clase}» no coincide con el texto del informe.')
    if len(c) != 33 or c['cambia_relevancia'].any() or c['cambia_clase'].any() or not c['compatible_monte_carlo'].all():
        raise RuntimeError('La comparación no coincide con el texto del informe.')
    if (c['relevante_10000'] != c['relevante_50000']).any() or sorted(c.loc[c['relevante_50000'], 'variable']) != sorted(RIESGO + PROTECCION + SIN_DIRECCION):
        raise RuntimeError('Las variables con q < 0,10 no coinciden con el texto del informe.')
    if {v for _, v, _ in CATALOGO} != set(T.VARIABLES_33):
        raise RuntimeError('El catálogo no contiene exactamente las 33 variables.')
    r = b['relevancia_33'].sort_values('p', ignore_index=True)
    if int(r.index[r['variable'] == SOBRECARGA][0]) + 1 != 7:
        raise RuntimeError('El ejemplo de Benjamini-Hochberg de la sobrecarga cambió.')
    for n, t in comp.items():
        if t[['cambia_q_0_10', 'cambia_q_0_05', 'cambia_clase', 'cambia_fcbf']].any().any() or not (t['su_identica'].all() and t['p_identico'].all()):
            raise RuntimeError(f'La comparación de {n} no coincide con el texto del informe.')
        rango = t.sort_values(['p_34', 'variable']).reset_index(drop=True)
        if int(rango.index[rango['variable'] == T.EXCLUIDA][0]) + 1 != 7:
            raise RuntimeError('La posición de la variable excluida no coincide con el texto.')
    mc = b['incertidumbre_monte_carlo'].set_index('variable')
    if mc.loc['dias_ejercicio_semana', 'q_mc_superior'] < 0.05 or a['incertidumbre_monte_carlo']['cercana'].any() or b['incertidumbre_monte_carlo']['cercana'].any():
        raise RuntimeError('Los intervalos de Monte Carlo no coinciden con el texto del informe.')
    if R.ALFA != 0.10:
        raise RuntimeError('El criterio cambió.')


# --- Figuras --------------------------------------------------------------------------------------------------------

def figura_q_34_33(comp, ruta):
    """Dos paneles, un eje común: q con 34 pruebas (hueco) y con 33 (relleno)."""
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    I._base(1, 1)
    plt.close('all')
    fig, ejes = plt.subplots(1, 2, figsize=(7.4, 4.5), facecolor=I.SUPERFICIE, sharey=True, sharex=True)
    orden = comp[50000][comp[50000]['variable'] != T.EXCLUIDA].sort_values(['q_33', 'variable']).head(15)['variable'].tolist()[::-1]
    for ax, n, titulo in zip(ejes, (10000, 50000), ('10.000 permutaciones', '50.000 permutaciones')):
        I._ejes(ax)
        t = comp[n].set_index('variable').loc[orden]
        y = np.arange(len(orden))
        ax.hlines(y, t['q_34'], t['q_33'], color=I.GRIS, linewidth=1.4)
        ax.scatter(t['q_34'], y, s=30, facecolor=I.SUPERFICIE, edgecolor=I.GRIS, linewidth=1.3, zorder=3)
        ax.scatter(t['q_33'], y, s=30, color=I.AZUL, edgecolor=I.SUPERFICIE, linewidth=0.8, zorder=4)
        ax.axvline(0.10, color=I.TINTA, lw=1)
        ax.grid(axis='x', color=I.GRILLA, linewidth=0.7)
        I._coma_decimal(ax)
        ax.set_yticks(y, [nombre(v) for v in orden], color=I.TENUE, fontsize=7.5)
        ax.set_title(titulo, loc='left', fontsize=9.5, fontweight='bold', color=I.TINTA)
        ax.set_xlabel('q de Benjamini-Hochberg', color=I.TENUE, fontsize=8)
    ejes[1].text(0.103, -0.55, 'q = 0,10', color=I.TINTA, fontsize=7.5)
    fig.legend(handles=[Line2D([], [], color=I.GRIS, marker='o', markerfacecolor=I.SUPERFICIE, linestyle='', label='Con 34 pruebas'), Line2D([], [], color=I.AZUL, marker='o', linestyle='', label='Con 33 pruebas')],
               frameon=False, loc='upper right', ncol=2, fontsize=8, labelcolor=I.TENUE)
    fig.suptitle('La corrección mueve q muy poco', x=0.01, ha='left', fontweight='bold', color=I.TINTA, fontsize=11)
    fig.tight_layout()
    fig.savefig(ruta, dpi=220, facecolor=I.SUPERFICIE)
    plt.close('all')


def figuras(b, c, comp):
    import matplotlib.pyplot as plt
    FIGURAS.mkdir(parents=True, exist_ok=True)
    base = I._base

    def con_escala(factor):
        I._base = lambda alto, ancho=8.6: base(alto * factor, 7.0)
    try:
        con_escala(0.72)
        ruta = FIGURAS / 'su_33_variables_word.png'
        fig = I.fig_su(c, ruta)
        fig.axes[0].set_title('Entropía de Shannon: SU de las 33 variables', loc='left', fontweight='bold', color=I.TINTA, fontsize=11)
        fig.axes[0].set_xlabel('SU con la severidad (igual en ambas ejecuciones)', color=I.TENUE)
        fig.tight_layout()
        fig.savefig(ruta, dpi=220, facecolor=I.SUPERFICIE)
        ruta = FIGURAS / 'rho_33_variables_word.png'
        fig = I.fig_rho(b['direccion_resumen'], c, ruta)
        fig.axes[0].set_xlabel('ρ de Spearman con el MRS total, IC 95 % bootstrap', color=I.TENUE)
        fig.axes[0].get_legend().set_loc('upper left')
        fig.tight_layout()
        fig.savefig(ruta, dpi=220, facecolor=I.SUPERFICIE)
        con_escala(0.82)
        ruta = FIGURAS / 'q_10000_50000_word.png'
        I.fig_q(c, ruta).savefig(ruta, dpi=220, facecolor=I.SUPERFICIE)
        ruta = FIGURAS / 'su_pares_relevantes_word.png'
        I.fig_pares(b['pares_relevantes'], c, ruta).savefig(ruta, dpi=220, facecolor=I.SUPERFICIE)
    finally:
        I._base = base
    plt.close('all')
    figura_q_34_33(comp, FIGURAS / 'q_34_33_word.png')
    cat = b['direccion_categorias']
    relevantes = c[c['relevante_50000']].sort_values(['q_50000', 'variable'])['variable'].tolist()
    W.figura_categorias(cat, relevantes, 'Síntomas severos por categoría, IC 95 % de Wilson (variables con q < 0,10)', FIGURAS / 'severas_relevantes_word.png', alto=2.05)
    W.figura_categorias(cat, INDICIOS_RIESGO + INDICIOS_PROTECCION, 'Síntomas severos por categoría, IC 95 % de Wilson (solo tendencias)', FIGURAS / 'severas_tendencias.png', alto=1.85)
    W.figura_categorias(cat, ['lugar_trabajo_comprensivo', 'estres_entorno_laboral'], 'Síntomas severos según las condiciones laborales (n = 287), IC 95 % de Wilson', FIGURAS / 'severas_trabajadoras.png', alto=2.3)
    W.figura_categorias(cat, [SOBRECARGA, 'cantidad_personas_cuida'], 'Síntomas severos según las variables de cuidado, IC 95 % de Wilson', FIGURAS / 'severas_cuidadoras.png', alto=2.3)


# --- Contenido --------------------------------------------------------------------------------------------------------

def construir(a, b, c, previas, g34, comp, dom):
    D = Informe()
    D.d.sections[0].header.paragraphs[0].runs[0].text = 'AgingWomen · Fase 35B · Revisión corregida de 33 variables'
    D.d.core_properties.title = 'Fase 35B: revisión corregida de 33 variables'
    mc34 = g34['incertidumbre_monte_carlo'].set_index('variable')
    dom_i = dom.set_index('variable')
    comp10, comp50 = comp[10000].set_index('variable'), comp[50000].set_index('variable')
    d = b['direccion_resumen'].set_index('variable')
    cat = b['direccion_categorias']
    C = c.set_index('variable')
    comp = b['shannon_componentes'].set_index('variable')
    orient = b['orientacion_escalas'].set_index('variable')
    rel_a, rel_b = a['relevancia_34'].set_index('variable'), b['relevancia_34'].set_index('variable')
    mc_a, mc_b = a['incertidumbre_monte_carlo'].set_index('variable'), b['incertidumbre_monte_carlo'].set_index('variable')
    sens = b['sensibilidades'].set_index('variable')
    pares = b['pares_relevantes']
    fcbf = b['decisiones_fcbf']
    todas_parejas = b['su_todas_las_parejas']
    pob = b['poblaciones'].set_index('poblacion')['n']

    def par(x, y):
        f = pares[((pares['variable_1'] == x) & (pares['variable_2'] == y)) | ((pares['variable_1'] == y) & (pares['variable_2'] == x))].iloc[0]
        return f

    def categoria(v, etiqueta):
        return cat[(cat['variable'] == v) & (cat['categoria'] == etiqueta)].iloc[0]

    def severas_pob(v):
        t = cat[cat['variable'] == v]
        return int(t['severas'].sum()), int(t['n'].sum())

    def ficha(v):
        f = d.loc[v]
        baja, alta = categoria(v, f['cat_baja']), categoria(v, f['cat_alta'])
        return (f'ρ = {r3(f["rho_mrs"])} (IC 95 %: {r3(f["rho_ic95_inferior"])} a {r3(f["rho_ic95_superior"])}). «{categoria_legible(f["cat_baja"])}» (n = {int(baja["n"])}) tiene {p1(baja["pct_severas"])} % de síntomas severos y un MRS medio de {p1(baja["mrs_medio"])}; '
                f'«{categoria_legible(f["cat_alta"])}» (n = {int(alta["n"])}) tiene {p1(alta["pct_severas"])} % y {p1(alta["mrs_medio"])}. La diferencia es de {r1(f["dif_pct_severas"])} puntos porcentuales (IC 95 %: {r1(f["dif_pct_ic_inferior"])} a {r1(f["dif_pct_ic_superior"])}). '
                f'q de SU: {p3(C.loc[v, "q_10000"])} con 10.000 y {p3(C.loc[v, "q_50000"])} con 50.000.')

    orden_q = c.sort_values(['q_50000', 'variable'])['variable'].tolist()
    relevantes = c[c['relevante_50000']].sort_values(['q_50000', 'variable'])['variable'].tolist()
    s_a, s_b = severas_pob('edad'), severas_pob('lugar_trabajo_comprensivo')
    s_c = severas_pob(SOBRECARGA)

    # ---- Portada ----
    def centrado(texto, tam, negrita=False, antes=0, despues=6, color='000000'):
        q = D.d.add_paragraph()
        q.alignment = WD_ALIGN_PARAGRAPH.CENTER
        q.paragraph_format.space_before, q.paragraph_format.space_after = Pt(antes), Pt(despues)
        r = q.add_run(texto)
        r.font.size, r.bold, r.font.color.rgb = Pt(tam), negrita, RGBColor.from_string(color)
    centrado('Universidad Católica del Norte', 15, True, 40, 4, AZUL_OSCURO)
    centrado('Proyecto AgingWomen', 13, False, 0, 90, '404040')
    centrado('Fase 35B', 15, True, 0, 8, AZUL_OSCURO)
    centrado('Análisis entrópico de la asociación entre 33 variables y la severidad de los síntomas menopáusicos', 21, True, 0, 18, AZUL_OSCURO)
    q = D.d.add_paragraph()
    q.paragraph_format.space_after = Pt(18)
    q._p.get_or_add_pPr().append(parse_xml(f'<w:pBdr {M_NS}><w:bottom w:val="single" w:sz="10" w:space="1" w:color="{AZUL_OSCURO}"/></w:pBdr>'))
    centrado('Informe académico integrado: revisión corregida', 14, False, 0, 6)
    centrado('Entropía de Shannon, información mutua y Symmetrical Uncertainty con 10.000 y 50.000 permutaciones', 12, False, 0, 110, '404040')
    centrado('Revisión según las indicaciones de la profesora del 03-11-2026, corregida por el criterio de dominancia', 11.5, False, 0, 6)
    centrado('Conjunto de datos sintético: los resultados son exploratorios y no causales', 11.5, False, 0, 6)
    centrado('Noviembre de 2026', 11.5, False, 26, 0)
    D.salto()
    D.indice()
    D.salto()

    # ---- Resumen ----
    D.h0('Resumen')
    D.p(f'Este informe presenta la revisión de la Fase 35B del proyecto AgingWomen. Se analizó cuáles de 33 variables se asocian con una mayor o menor severidad de los síntomas menopáusicos en un conjunto de datos **sintético** de {pob["todas"]} participantes con la escala MRS completa. La severidad se definió como MRS total ≥ 16 ({s_a[0]} participantes, {p1(100 * s_a[0] / s_a[1])} %).')
    D.p('La asociación se midió con la **entropía de Shannon**, la información mutua y la Symmetrical Uncertainty (SU), y se evaluó con pruebas de permutación y la corrección de Benjamini-Hochberg sobre una única familia de 33 pruebas. Se usó el criterio exploratorio q < 0,10. El análisis principal tiene 10.000 permutaciones, y el complementario, 50.000, para evaluar la precisión numérica. Como SU no indica dirección, se agregaron la correlación de Spearman y las comparaciones por categoría.')
    D.p(f'**Ambas ejecuciones identifican las mismas seis variables y ninguna cambia de clasificación.** Son compatibles con un posible factor de riesgo el IMC y trabajar actualmente; con un posible factor protector, los días de ejercicio, el ejercicio de bajo impacto y un lugar de trabajo comprensivo. El ejercicio de fuerza supera el criterio, pero sin dirección clara. Otras siete variables, entre ellas la sobrecarga física y emocional, muestran solo una tendencia ordinal y no superan q < 0,10.')
    D.p(f'**Esta versión corrige la anterior de 34 variables.** `usa_medicamentos_diabetes` se excluyó porque «No» concentra {p1(dom_i.loc[T.EXCLUIDA, "pct_dominante_propia"])} % de las respuestas, sobre el umbral de dominancia de 85 %. No se ejecutaron permutaciones nuevas: la SU y el p de las otras 33 variables son idénticos, y solo se recalculó la corrección por comparaciones múltiples. Ninguna variable cambió su clasificación.')
    D.p(f'Las asociaciones son débiles (la SU máxima es {p4(c["su"].max())}), no permiten afirmar causalidad y reflejan en parte lo programado en la simulación. Las **33 variables se conservan como conjunto inicial de la Fase 36**: este análisis no elimina variables.')

    # ---- 1 ----
    D.h1('Introducción')
    D.p('La menopausia se acompaña de síntomas somáticos, psicológicos y urogenitales de intensidad variable. Una parte del proyecto AgingWomen busca describir qué características se asocian con síntomas más o menos severos, para orientar después la segmentación de participantes y la generación de reglas.')
    D.p('En este contexto, la Fase 35B aplica un análisis basado en la teoría de la información. Se eligió este enfoque porque puede detectar relaciones que no son lineales y porque se aplica de igual modo a variables binarias, ordinales, nominales y discretizadas.')
    D.p('En la reunión del 03-11-2026, la profesora recomendó nombrar explícitamente la **entropía de Shannon**. La revisión también incorporó a la evaluación entrópica las antiguas variables de control (`edad`, `imc` y `trabaja_actualmente`), de modo que ahora compiten en igualdad de condiciones con las demás. Además, se dejó claro que estos resultados son **informativos** y no un filtro para eliminar variables.')
    D.p('Posteriormente se detectó una inconsistencia: `usa_medicamentos_diabetes` supera el umbral de dominancia de la Fase 34D y seguía en el análisis por una excepción. **Este informe presenta la revisión corregida**, con 33 variables. El informe anterior, de 34 variables, se conserva sin cambios como versión histórica, y la sección 11 compara ambas.')
    D.p('El informe está pensado para que se comprenda sin conocer el código. Cada tabla y figura importante se acompaña de una explicación de lo que muestra y de lo que permite concluir. Los valores provienen de `analisis/reunion_2026-11-03/revision_33_variables/`; para esta corrección no se ejecutó ninguna permutación.')

    # ---- 2 ----
    D.h1('Objetivos')
    D.h2('Objetivo general')
    D.p('Analizar cuáles de las 33 variables estudiadas se asocian con una mayor o menor severidad de los síntomas menopáusicos.')
    D.h2('Objetivos específicos')
    D.lista(['Medir la asociación de cada variable con la severidad mediante la entropía de Shannon, la información mutua y SU.', 'Evaluar si cada asociación supera lo esperable por azar, con 10.000 permutaciones y corrección por comparaciones múltiples.', 'Evaluar la precisión y la consistencia numérica de esos resultados con una ejecución complementaria de 50.000 permutaciones.', 'Describir la dirección de cada asociación para distinguir posibles factores de riesgo, posibles factores protectores, asociaciones sin dirección clara y variables sin respaldo suficiente.', 'Describir la redundancia entre variables mediante FCBF, con carácter informativo.', 'Precisar la interpretación en las poblaciones específicas de trabajadoras y de cuidadoras.'])
    D.h2('Alcance')
    D.p('Este análisis **no busca eliminar automáticamente variables para la segmentación**. Tampoco demuestra causalidad ni entrega evidencia sobre una población real, porque los datos son sintéticos. Las 33 variables se conservan como conjunto inicial de la Fase 36.')

    # ---- 3 ----
    D.h1('Descripción del conjunto de datos')
    D.p('El conjunto de datos es **sintético**. Se generó para simular a las usuarias de la encuesta de la plataforma en su primera aplicación, con un simulador que programa relaciones coherentes con los factores que se querían representar. Luego se le agregaron errores a propósito, para reproducir datos reales con problemas de calidad, y se limpió con el mismo procedimiento que se aplicaría a datos reales.')
    D.tabla('Etapas del conjunto de datos, desde la generación hasta el análisis.', ['Etapa', 'Filas', 'Descripción'],
            [['Simulación («verdad»)', '550', 'Participantes generadas por el simulador.'], ['Conjunto con errores', '565', 'Incluye duplicados, respuestas imposibles y valores faltantes introducidos a propósito.'], ['Conjunto limpio', '546', 'Se excluyeron 19 filas: 8 duplicados exactos, 7 RUT repetidos, 3 personas mayores de 65 años y 1 edad no verificable.'], ['Conjunto analítico', str(pob['todas']), 'Participantes con MRS completo (`datos/analitico/dataset_fase35.csv`). No se regeneró para este análisis.']],
            [4.0, 1.5, 11.0], ['i', 'd', 'i'], tam=9, mantener=True)
    D.p(f'**Variable de severidad.** La variable `severo_mrs` vale 1 cuando el MRS total es 16 o más, y 0 en caso contrario. De las {s_a[1]} participantes, {s_a[0]} ({p1(100 * s_a[0] / s_a[1])} %) tienen síntomas severos. La SU se calcula con esta variable binaria; la correlación de Spearman se calcula con el MRS total.')
    D.h2('Poblaciones de análisis')
    D.p('Cada variable se analiza solo entre las personas a quienes les corresponde. Por eso existen tres poblaciones principales:')
    D.tabla('Poblaciones utilizadas en la familia de 33 pruebas.', ['Población', 'n', 'Severas', 'N.º de variables', 'Definición'],
            [['General', str(pob['todas']), f'{s_a[0]} ({p1(100 * s_a[0] / s_a[1])} %)', '30', 'Todas las participantes con MRS completo.'],
             ['Laboral', str(pob['laboral']), f'{s_b[0]} ({p1(100 * s_b[0] / s_b[1])} %)', '2', '`lugar_trabajo_comprensivo` y `estres_entorno_laboral`: trabajadoras con valor en ambas preguntas.'],
             ['Cuidadoras con sobrecarga observada', str(pob['sobrecarga_observada']), f'{s_c[0]} ({p1(100 * s_c[0] / s_c[1])} %)', '1', '`sobrecarga_fisica_emocional`: cuidadoras con respuesta válida registrada. Las 12 imputadas (hasta 251) se evalúan solo como sensibilidad.']],
            [3.4, 1.0, 2.2, 1.9, 8.0], ['i', 'd', 'd', 'c', 'i'], tam=9, mantener=True)
    D.p(f'Una regla importante es que **«no aplica» nunca se convierte en cero ni entra como categoría**. Quien no cuida no tiene un nivel mínimo de sobrecarga: simplemente no se le aplica la pregunta. Si se le asignara cero, la variable mezclaría dos cosas distintas, cuidar o no cuidar y el grado de sobrecarga. En cambio, algunos ceros sí tienen significado: en las frecuencias de ejercicio, 0 = no lo realiza; en `cantidad_personas_cuida`, 0 = no cuida.')
    D.h2('Valores imputados')
    D.p('La limpieza conservó imputaciones que condicionan la lectura de algunos resultados. No se modificó ningún registro para este informe.')
    D.tabla('Imputaciones que afectan directamente a la interpretación.', ['Variable', 'Imputados', 'Tratamiento', 'Efecto sobre la lectura'],
            [['`imc`', f'262 de 529 (49,5 %)', 'Media de las observadas (29,23 kg/m²)', 'Casi la mitad queda con el mismo valor, en la categoría 25-29,9. Esto reduce ρ de +0,250 (observadas, n = 267) a +0,192.'],
             ['`trabaja_actualmente`', '22 de 529', 'Moda («Sí»)', 'Estas 22 no tienen respuestas laborales. Por eso trabajan 309, pero la población laboral es de 287.'],
             ['`lugar_trabajo_comprensivo` y `estres_entorno_laboral`', f'De las 287: {pob["laborales_observadas_en_287"]} con ambas observadas', 'Mediana', 'Las 287 no son todas respuestas observadas: 271 y 277 lo son en cada pregunta.'],
             ['`sobrecarga_fisica_emocional`', '12 de 251', 'Mediana («A veces»)', 'El análisis principal usa las 239 observadas; la figura descriptiva usa las 251 (sección 15).'],
             ['`cantidad_personas_cuida`', f'{pob["cuida_imputada_no"]} ceros', '`cuida_otras_personas` imputada como «No»', 'Estos ceros provienen de una imputación y no de una respuesta observada.']],
            [4.3, 3.0, 3.5, 5.7], tam=8.5, mantener=True)

    # ---- 4 ----
    D.h1('Listado y descripción de las 33 variables')
    D.p('Las 33 variables corresponden a las 30 candidatas actualizadas más tres antiguas variables de control. Respecto de las versiones previas, hay cuatro diferencias:')
    D.lista(['**`edad`, `imc` y `trabaja_actualmente`** ya no están exentas del análisis entrópico: se evalúan y corrigen igual que las demás, y compiten en FCBF.', '**`usa_medicamentos_diabetes` queda excluida del modelado por dominancia** (sección 4.1). Se conserva en el conjunto limpio y en el EDA histórico.', '**`doble_carga` queda excluida.** La información sobre trabajo y cuidado queda representada por `trabaja_actualmente`, `cantidad_personas_cuida` y `sobrecarga_fisica_emocional`.', '**`prevision` queda excluida** del modelado. **`sobrecarga_fisica_emocional` y `cantidad_personas_cuida` sí se incluyen.**'])
    D.p('La tabla siguiente describe cada variable y sus valores. En las figuras, la sobrecarga física y emocional aparece rotulada como «Sobrecarga por trabajo y cuidado», el rótulo definido en la Fase 34.')
    filas = []
    for i, (dominio, v, pregunta) in enumerate(CATALOGO, 1):
        niveles = orient.loc[v, 'niveles']
        tipo = orient.loc[v, 'tipo']
        if tipo == 'continua':
            niveles = 'Tramos, solo para SU: ' + re.sub(r'\d+ = ', '', niveles).replace('>=', '≥').replace('<=', '≤')
        elif pd.isna(niveles) or not str(niveles):
            niveles = 'Categorías sin orden: ' + '; '.join(categoria_legible(x) for x in cat.loc[cat['variable'] == v, 'categoria'])
        filas.append([str(i), dominio, f'{nombre(v)} (`{v}`)', pregunta, f'{tipo.capitalize()}. {poblacion(rel_b.loc[v, "poblacion"])}, n = {int(rel_b.loc[v, "n"])}', niveles])
    nt = D.tabla('Las 33 variables analizadas.', ['N.º', 'Dominio', 'Variable (nombre en los datos)', 'Pregunta o definición', 'Tipo y población', 'Valores'], filas, [0.7, 2.15, 3.85, 3.9, 1.9, 4.05], ['c', 'i', 'i', 'i', 'i', 'i'], tam=7.5)
    D.explicar(nt, 'La definición, el tipo, la población y los valores de cada una de las 33 variables.', 'El conjunto cubre dimensiones sociodemográficas, de salud, trabajo, cuidado, actividad física, alimentación y sustancias. Las escalas no se interpretan todas igual: en `evacuacion_intestinal`, un valor mayor significa evacuaciones __menos__ frecuentes.')

    D.h2('Criterio de dominancia y exclusión de la diabetes')
    dx = dom_i.loc[T.EXCLUIDA]
    fz = dom_i.loc['frecuencia_fuerza']
    D.p(f'La Fase 34D estableció que una variable con **más de 85 % de las respuestas en una sola categoría** queda fuera del modelado, porque casi no distingue entre participantes. `usa_medicamentos_diabetes` tiene {int(dx["n_dominante"])} respuestas «No» de {int(dx["n_propia"])}: **{p1(dx["pct_dominante_propia"])} %** ({P._n(dx["pct_dominante_propia"], 2)} % con dos decimales). Sin sus 24 valores imputados sería {P._n(dx["pct_dominante_sin_imputados_34B"], 2)} %, de modo que también supera el umbral.')
    D.p('El 28-10-2026 se había documentado una excepción: se conservó por ser una variable de control y un factor validado por la profesora el 20-10. La revisión del 03-11 la incorporó después al análisis entrópico como una variable más. Esa condición ya no justifica tratarla distinto: **el criterio se aplica ahora sin excepciones**, y queda fuera del preprocesamiento, del análisis entrópico, de Random Forest y de la segmentación. No se elimina de los conjuntos históricos.')
    t = dom.head(6)
    nt = D.tabla('Las seis variables con mayor dominancia entre las 34 de la revisión anterior.', ['Variable', 'Población', 'n', '% dominante', 'Sin imputadas', 'Entre laborales', 'Entre cuidadoras', 'Decisión'],
                 [[nombre(f['variable']), poblacion(f['poblacion_propia']), str(int(f['n_propia'])), p1(f['pct_dominante_propia']), p1(f['pct_dominante_sin_imputados_34B']), p1(f['pct_dominante_laboral']), p1(f['pct_dominante_cuidadoras']), f['decision_corregida'].capitalize()] for _, f in t.iterrows()],
                 [3.9, 1.8, 0.8, 1.9, 1.6, 1.6, 1.9, 3.0], ['i', 'i', 'd', 'd', 'd', 'd', 'd', 'i'], tam=8.5, resaltar=[v == T.EXCLUIDA for v in t['variable']], mantener=True)
    D.explicar(nt, 'La proporción de la categoría más frecuente de cada variable, en su población y en las subpoblaciones de trabajadoras y cuidadoras.', f'Solo la diabetes supera el umbral. Ninguna de las otras 33 lo supera en su propia población. `frecuencia_fuerza` queda cerca ({P._n(fz["pct_dominante_propia"], 2)} %) y llega a {P._n(fz["pct_dominante_cuidadoras"], 2)} % entre las cuidadoras; se conserva porque la regla se mide en la población de cada variable, pero conviene tenerlo presente al interpretar los modelos de esa subpoblación.')
    D.p('**Conjunto de datos.** Se creó `dataset_fase35_33_variables.csv`, igual a `dataset_fase35.csv` sin esa columna: mismas 529 participantes, mismas reglas y mismos valores, comprobado celda a celda. No se ejecutó de nuevo la limpieza.')

    # ---- 5 ----
    D.h1('Fundamentos de entropía de Shannon e información mutua')
    D.h2('Entropía de Shannon')
    D.p('La **entropía de Shannon** mide la incertidumbre de una variable: cuán difícil es predecir su valor. Es 0 cuando la variable es constante y aumenta cuando sus categorías son más numerosas y están mejor repartidas. Con logaritmo en base 2 se expresa en bits:')
    D.ecuacion(m_r('H(X)=−') + m_suma(m_r('x'), m_r('p(x) ') + LOG2 + m_r(' p(x)')))
    D.p('Aquí, p(x) es la frecuencia observada de la categoría x, y se considera 0·log₂0 = 0. Una variable binaria repartida en partes iguales tiene 1 bit de entropía. Por ejemplo, la severidad en las 529 participantes tiene H = ' + p4(comp.loc['edad', 'h_severidad']) + ' bits, muy cerca de 1, porque está casi balanceada. La entropía conjunta aplica la misma idea a pares de valores:')
    D.ecuacion(m_r('H(X,Y)=−') + m_suma(m_r('x'), m_suma(m_r('y'), m_r('p(x,y) ') + LOG2 + m_r(' p(x,y)'))))
    D.h2('Información mutua')
    D.p('La **información mutua** mide cuánta incertidumbre sobre una variable se reduce al conocer la otra. Vale 0 si son independientes en la muestra y aumenta cuanto más información comparten:')
    D.ecuacion(m_r('I(X;Y)=H(X)+H(Y)−H(X,Y)'))
    D.p('Sin embargo, la información mutua tiende a crecer con el número de categorías y no tiene un máximo común. Por eso no permite comparar directamente variables distintas, y se necesita una medida normalizada.')

    # ---- 6 ----
    D.h1('Explicación de SU, permutaciones, p, q y FCBF')
    D.h2('Symmetrical Uncertainty (SU)')
    D.p('La **Symmetrical Uncertainty** normaliza la información mutua entre 0 (sin información compartida) y 1 (asociación perfecta):')
    D.ecuacion(m_r('SU(X,Y)=') + m_frac(m_r('2 · I(X;Y)'), m_r('H(X)+H(Y)')))
    t = comp.loc['trabaja_actualmente']
    D.p(f'**Ejemplo con `trabaja_actualmente`.** En las 529 participantes, H(X) = {p4(t["h_x"])}, H(severidad) = {p4(t["h_severidad"])} y H(X, severidad) = {p4(t["h_conjunta"])} bits. La información mutua es {p4(t["h_x"])} + {p4(t["h_severidad"])} − {p4(t["h_conjunta"])} = {p5(t["informacion_mutua"])} bits, y SU = 2 · {p5(t["informacion_mutua"])} / ({p4(t["h_x"])} + {p4(t["h_severidad"])}) = {p4(t["su"])}. El Anexo A presenta estos componentes para las 33 variables.')
    D.p('Hay dos propiedades de SU que son clave para interpretar este informe:')
    D.lista(['**SU no tiene signo.** Indica que hay una asociación, pero no si un valor mayor acompaña a más o a menos severidad. Por sí sola no determina si una variable es protectora o de riesgo.', '**SU trata las escalas como categorías sin orden.** Una tendencia ordenada y un patrón irregular reciben el mismo tratamiento. Por ello, Spearman puede detectar tendencias que SU no detecta, y al revés.'])
    D.h2('Prueba de permutación')
    D.p('Incluso entre variables independientes, la SU observada rara vez es exactamente 0. Además, el valor que el azar produce por sí solo depende del tamaño de la población y del número de categorías. La prueba de permutación estima ese valor sin asumir una distribución: se baraja aleatoriamente `severo_mrs` entre las personas de la población, lo que rompe cualquier relación real, y se recalcula SU. Esto se repite N veces (10.000 o 50.000).')
    D.h2('Significado de p')
    D.p('El **valor p** es la proporción de permutaciones en que el azar alcanzó o superó la SU observada. Sumar 1 al numerador y al denominador evita informar un p igual a 0, algo que una cantidad finita de permutaciones no puede demostrar:')
    D.ecuacion(m_r('p=') + m_frac(m_r('1+k'), m_r('N+1')))
    D.p(f'Donde k es el número de permutaciones con SU mayor o igual a la observada. Por ejemplo, con 50.000 permutaciones, el IMC tuvo k = {int(rel_b.loc["imc", "k"])}, de modo que p = {p5(rel_b.loc["imc", "p"])}. Un p pequeño indica que una SU así sería poco habitual si no hubiera asociación. No indica que la asociación sea fuerte ni causal.')
    D.h2('Significado de q y corrección de Benjamini-Hochberg')
    D.p('Al evaluar 33 variables, algunas tendrán un p bajo solo por azar. La corrección de **Benjamini-Hochberg** controla la tasa de falsos descubrimientos: la proporción esperada de resultados falsos entre los declarados relevantes. Con los p ordenados de menor a mayor, y siendo m = 33 pruebas, cada valor q se obtiene así:')
    D.ecuacion(m_sub(m_r('q'), m_r('(i)')) + m_r('=') + f'<m:limLow><m:e>{m_r("min", True)}</m:e><m:lim>{m_r("j ≥ i")}</m:lim></m:limLow>' + m_frac(m_r('m'), m_r('j')) + m_sub(m_r('p'), m_r('(j)')))
    s_p, s_q = rel_b.loc[SOBRECARGA, 'p'], rel_b.loc[SOBRECARGA, 'q']
    D.p(f'**Ejemplo.** Con 50.000 permutaciones, la sobrecarga tiene el séptimo p más bajo: {p5(s_p)}. Entonces, {p5(s_p)} × 33 / 7 = {p3(s_p * 33 / 7)}. Como la corrección toma el menor valor entre esa posición y las siguientes, su q final es {p3(s_q)}, compartido con otras variables. Por sí solo, ese p estaría bajo 0,05, pero tras considerar las 33 pruebas no supera el criterio.')
    D.p('Un **q menor que 0,10** significa que, si se declaran relevantes todas las variables con un q igual o menor, se espera que, en promedio, alrededor de 1 de cada 10 sea un falso positivo. No es la probabilidad de que esa variable en particular sea falsa, ni mide la intensidad de la asociación.')
    D.h2('Justificación del criterio exploratorio q < 0,10')
    D.lista(['**El propósito es exploratorio.** Se buscan asociaciones para describir y orientar, no confirmar hipótesis.', '**Un error tiene un costo limitado.** Ninguna variable se elimina por este resultado, de modo que un falso positivo no excluye otra variable y un falso negativo no retira la variable de la Fase 36.', '**Se esperan efectos pequeños.** Con asociaciones débiles y 33 pruebas, un criterio más estricto puede pasar por alto señales que vale la pena describir.', '**El criterio se declara con transparencia.** Se fijó conociendo resultados anteriores, por lo que no es confirmatorio. q < 0,05 se informa solo como referencia.'])
    D.h2('FCBF y evaluación de la redundancia')
    D.p('**FCBF** (__Fast Correlation-Based Filter__) ordena las variables relevantes de mayor a menor SU con la severidad. Luego marca como redundante una variable j cuando otra variable i que está antes en el orden comparte con ella al menos tanta información como la que j comparte con la severidad:')
    D.ecuacion(m_r('SU(i,j) ≥ SU(j, severidad)'))
    D.p('En este análisis, FCBF se usa con reglas validadas por cobertura para no comparar poblaciones distintas sin cuidado: la Etapa 1 evalúa las variables generales (n = 529), la Etapa 2 las laborales (n = 287) y la Etapa 3 la sobrecarga (n = 239, o 130 frente a una variable laboral). Una variable con menor cobertura no elimina a una con mayor cobertura.')
    D.tabla('Diferencias entre las variantes de FCBF.', ['Aspecto', 'FCBF estándar', 'FCBF adaptado'],
            [['Condición de redundancia', 'SU(i,j) ≥ SU(j, severidad)', 'La misma condición y, además, q del par i-j < 0,10'], ['Qué exige al par', 'Basta con superar el umbral de SU, aunque la relación entre ambas no supere el azar', 'La relación entre ambas debe superar el azar según su propia prueba de permutación'], ['Riesgo principal', 'Marcar redundancia con una relación muy pequeña', 'Conservar variables con relación débil pero real'], ['Rol en este informe', 'Referencia informativa', 'Lectura preferida, también informativa']],
            [3.8, 6.2, 6.5], tam=9, mantener=True)
    D.p('**Una variable «seleccionada» no es más protectora, más riesgosa ni clínicamente más importante.** Tampoco una «redundante» carece de valor. Son rótulos descriptivos, y ninguno saca a una variable de la Fase 36.')

    # ---- 7 ----
    D.h1('Procedimiento metodológico')
    D.h2('Pasos del análisis')
    D.lista(['**Preparación.** Se usa el conjunto analítico sin regenerarlo. Solo para SU, `edad` se agrupa en tramos, `imc` en categorías OMS y `horas_sedentarismo` en cuartiles. Spearman usa los valores originales.', '**Asociación.** Se calculan H(X), H(severidad), H(X, severidad), información mutua y SU de cada variable en su población.', '**Permutaciones.** p proviene de 10.000 (análisis principal) y de 50.000 (análisis complementario). Las permutaciones se ejecutaron en la revisión de 34 variables y se reutilizan sin repetirlas (sección 7.5).', '**Corrección.** Se aplica Benjamini-Hochberg sobre una única familia de 33 pruebas, recalculada para cada ejecución y sin reutilizar los q de la revisión de 34 variables.', '**Criterio.** Una variable es relevante si q < 0,10, con comparación estricta.', '**Redundancia.** Se aplica FCBF a las variables relevantes, en sus variantes adaptada y estándar. Los pares se evalúan con su propia familia de pruebas.', '**Dirección.** Se calculan Spearman con el MRS total y con `severo_mrs`, IC 95 % bootstrap de 2.000 remuestreos, Kruskal-Wallis y comparaciones por categoría.', '**Clasificación.** Se asigna una clase descriptiva con reglas fijadas antes de calcular.', '**Comparación.** Se comparan las dos ejecuciones variable por variable.'], numerada=True)
    D.h2('Dirección y clasificación descriptiva')
    D.tabla('Reglas de dirección de la asociación, fijadas antes de calcular.', ['Dirección', 'Condición'],
            [['Positiva', 'El IC 95 % de ρ está sobre 0 y ρ con `severo_mrs` es positiva.'], ['Negativa', 'El IC 95 % de ρ está bajo 0 y ρ con `severo_mrs` es negativa.'], ['Mixta', 'El IC excluye 0 pero el signo con `severo_mrs` es opuesto; o el IC incluye 0 y Kruskal-Wallis tiene p < 0,05; o la variable es nominal con Kruskal-Wallis p < 0,05.'], ['Poco clara', 'Las demás.']],
            [3.0, 13.5], tam=9, mantener=True)
    D.tabla('Clasificación descriptiva de las variables.', ['Clase', 'Condición', '¿Supera q < 0,10?'],
            [['Posible factor de riesgo o de protección', 'q de SU < 0,10 y dirección positiva o negativa', 'Sí'], ['Asociación sin dirección clara', 'q de SU < 0,10 y dirección mixta o poco clara', 'Sí'], ['Indicio de riesgo o de protección (solo orden)', 'q de SU ≥ 0,10, q de Spearman < 0,10 y dirección positiva o negativa', 'No'], ['Sin respaldo tras la corrección', 'Las demás', 'No']],
            [6.2, 8.0, 2.3], ['i', 'i', 'c'], tam=9, mantener=True)
    D.p('«Posible factor» es una expresión descriptiva: significa que la asociación es __compatible__ con un factor de riesgo o de protección, no que lo sea. El signo se lee según lo que significa un valor mayor en cada escala.')
    D.h2('Justificación de las dos ejecuciones')
    D.p('El valor p de una prueba de permutación es una estimación con error, que disminuye al aumentar los sorteos. Antes de calcular se fijó una regla: se recomendarían 50.000 permutaciones si el intervalo de Monte Carlo al 95 % del q de alguna variable contenía 0,10. Ese intervalo se obtiene representando cada p con una distribución Beta(k + 0,5; N − k + 0,5), con 20.000 sorteos propagados por Benjamini-Hochberg.')
    D.p(f'En la revisión de 34 variables, la regla se activó por `lugar_trabajo_comprensivo`, cuyo intervalo llegaba hasta {p5(mc34.loc["lugar_trabajo_comprensivo", "q_mc_superior"])}. Por eso se ejecutaron las 50.000, autorizadas expresamente. **Solo cambió el número de permutaciones**; no cambiaron las variables, la codificación, las poblaciones ni los demás parámetros. Con la familia corregida de 33 pruebas, ese intervalo llega a {p5(mc_a.loc["lugar_trabajo_comprensivo", "q_mc_superior"])} y la regla ya no se activaría; la ejecución complementaria se conserva porque ya existía y aporta mayor precisión.')
    D.p('Para comparar, las semillas se mantuvieron: las primeras 10.000 permutaciones de la ejecución de 50.000 son exactamente las de la primera ejecución, y las 40.000 restantes son nuevas. Como estos dos grupos de sorteos son independientes y estiman el mismo p, se comparan con:')
    D.ecuacion(m_r('z=') + m_frac(m_sub(m_r('k'), m_r('10.000')) + m_r('/10.000 − ') + m_sub(m_r('k'), m_r('40.000')) + m_r('/40.000'), m_raiz(m_r('p̂(1−p̂)(1/10.000+1/40.000)'))))
    D.p('Una diferencia se considera compatible con la precisión de Monte Carlo si |z| ≤ 3,19, límite fijado para las 34 pruebas de la revisión anterior (corrección de Bonferroni, 0,05 / 34). Se mantiene sin cambios; ningún |z| se acerca a él.')
    D.h2('Reproducibilidad')
    D.p('Antes de aceptar la ejecución de 50.000, en la revisión de 34 variables, se comprobó que: las tablas de 10.000 se reproducen byte a byte; los primeros sorteos entregan los mismos k guardados, y al sumar los siguientes se obtiene el k total; la SU es idéntica; dos corridas de 50.000 coinciden; y los resultados de 10.000, los resultados históricos y los conjuntos de datos no cambiaron. Las semillas son fijas: `SeedSequence(42, spawn_key=(1103, 0, tipo, índice))`.')

    D.h2('Reutilización de resultados en la corrección')
    D.p('**Para pasar de 34 a 33 variables no se ejecutó ninguna permutación.** Se verificó que los valores guardados siguen siendo válidos para las 33 variables: los datos, la codificación y las poblaciones son los mismos, y ninguna comparación entre pares incluye la variable excluida.')
    D.tabla('Qué se reutilizó y qué se recalculó.', ['Elemento', 'Tratamiento', 'Motivo'],
            [['SU y tamaño de la población', 'Recalculados sin azar y comparados: 33 de 33 iguales', 'Solo dependen de cada variable y de su población'], ['k y p de las variables y de los pares', 'Reutilizados', 'Provienen de los mismos datos'], ['q de las variables', 'Recalculado con 33 pruebas', 'Cambió la familia'], ['q de los pares', 'Recalculado: 15 pares, iguales', 'No cambió el grupo de relevantes'], ['Decisiones de FCBF', 'Recorridas de nuevo con las mismas funciones', 'Dependen de q; el método es determinista'], ['ρ, intervalos y categorías', 'Reutilizados', 'No dependen de la familia'], ['q de ρ', 'Recalculado con 32 pruebas', 'Cambió la familia; una variable es nominal'], ['Intervalo Monte Carlo de q', 'Recalculado, con las mismas claves de semilla', 'Propaga cada p por la corrección; no permuta datos']],
            [5.2, 5.9, 5.4], tam=9, mantener=True)
    D.p('**Las semillas dependen de la posición alfabética de cada variable.** Si se hubiera permutado de nuevo con 33 variables, `usa_medicamentos_presion` y `vasos_agua_dia` habrían recibido otra corriente de números aleatorios solo por cambiar de posición. Al reutilizar los k guardados, este efecto no existe.')

    def tabla_version(rel, mc, N):
        t = rel.join(mc[['q_mc_inferior', 'q_mc_superior', 'prob_q_bajo_umbral']]).sort_values(['q', 'p'])
        filas = [[nombre(v), poblacion(f['poblacion']), str(int(f['n'])), p4(f['su']), f'{int(f["k"]):,}'.replace(',', '.'), p5(f['p']), p5(f['q']), f'{p5(f["q_mc_inferior"])} a {p5(f["q_mc_superior"])}', p3(f['prob_q_bajo_umbral']), si(f['q_bajo_0_10']), si(f['q_bajo_0_05'])] for v, f in t.iterrows()]
        return D.tabla(f'Resultados de las 33 variables con {N} permutaciones, de menor a mayor q. En azul, las que cumplen q < 0,10.', ['Variable', 'Población', 'n', 'SU', 'k', 'p', 'q', 'IC Monte Carlo de q', 'P(q<0,10)', '<0,10', '<0,05'], filas,
                       [4.05, 1.5, 0.65, 1.0, 1.05, 1.15, 1.15, 2.7, 1.05, 0.85, 0.85], ['i', 'i', 'd', 'd', 'd', 'd', 'd', 'c', 'd', 'c', 'c'], tam=7.5, resaltar=list(t['q_bajo_0_10']))

    # ---- 8 ----
    D.h1('Resultados de 10.000 permutaciones')
    D.p(f'**Análisis principal.** Seis variables cumplen q < 0,10: {lista_y(nombre(v).lower() if v != "imc" else "IMC" for v in c[c["relevante_10000"]].sort_values(["q_10000", "variable"])["variable"])}. Ninguna cumple la referencia q < 0,05.')
    nt = tabla_version(rel_a, mc_a, '10.000')
    D.explicar(nt, f'Cada fila informa SU, el número de permutaciones que igualaron o superaron la SU observada (k), los valores p y q, y la incertidumbre de Monte Carlo de q. La columna P(q<0,10) estima la probabilidad de que q quede bajo 0,10 considerando esa incertidumbre.', f'Las seis primeras variables superan el criterio exploratorio, con q entre {p3(c["q_10000"].min())} y {p3(C.loc["lugar_trabajo_comprensivo", "q_10000"])}. Después hay una separación clara: la siguiente tiene q = {p3(c[~c["relevante_10000"]]["q_10000"].min())}. Ningún intervalo de Monte Carlo de q contiene 0,10 (el más alto de las seis llega a {p5(mc_a.loc[relevantes, "q_mc_superior"].max())}).')
    nf = D.figura(FIGURAS / 'su_33_variables_word.png', 'SU de las 33 variables con la severidad. La SU es igual en ambas ejecuciones, porque no depende de las permutaciones.', 15.0)
    D.explicar(nf, 'La magnitud de SU de cada variable, con el tamaño de su población. Las barras azules corresponden a variables con q < 0,10.', f'Todas las asociaciones son pequeñas: la mayor SU es {p4(c["su"].max())}. Además, **el orden por SU y el orden por q no coinciden**: la sobrecarga (n = 239) tiene la segunda mayor SU y no supera el criterio, mientras que `trabaja_actualmente` (binaria, n = 529) lo supera con una SU menor. Esto ocurre porque la SU observada no descuenta lo que el azar produce por sí solo, que es mayor con pocas personas y muchas categorías.')

    # ---- 9 ----
    D.h1('Resultados de 50.000 permutaciones')
    ref_b = c[c['q_bajo_0_05_50000']].sort_values('variable')['variable'].tolist()
    D.p(f'**Análisis complementario.** Cumplen q < 0,10 las mismas seis variables. Ningún intervalo de Monte Carlo de q contiene 0,10, de modo que la clasificación ya no es sensible a la incertidumbre del muestreo de permutaciones. La referencia q < 0,05 la cumplen {lista_y(nombre(v).lower() for v in ref_b)}.')
    nt = tabla_version(rel_b, mc_b, '50.000')
    D.explicar(nt, 'La misma información que la tabla de 10.000, con estimaciones más precisas: los errores estándar de p y los intervalos de q son más estrechos.', f'La ejecución complementaria respalda la clasificación de la principal. Los intervalos de las seis variables quedan bajo 0,10: el más cercano llega a {p5(mc_b.loc[relevantes, "q_mc_superior"].max())}. Días de ejercicio y bajo impacto quedan con q = {p3(C.loc["dias_ejercicio_semana", "q_50000"])} bajo la referencia de 0,05, pero sus intervalos siguen cruzándola ({p5(mc_b.loc["dias_ejercicio_semana", "q_mc_inferior"])} a {p5(mc_b.loc["dias_ejercicio_semana", "q_mc_superior"])}), por lo que esto **no debe leerse como un hallazgo más fuerte**.')

    # ---- 10 ----
    D.h1('Comparación completa de ambas versiones')
    D.p('La tabla siguiente reúne las 33 variables. La SU y el tamaño de la población son idénticos en ambas ejecuciones; solo cambian las estimaciones de p y q. **En las 33 filas, la diferencia es compatible con la precisión de Monte Carlo** (|z| ≤ 3,19) y no representa un cambio en la asociación con la severidad; «Lectura» indica si la variable se mantiene bajo o sobre el criterio.')
    def interp(f):
        return f'Sigue {"bajo" if f["relevante_50000"] else "sobre"} 0,10'
    filas = [[nombre(v), p4(C.loc[v, 'su']), p5(C.loc[v, 'p_10000']), p5(C.loc[v, 'q_10000']), p5(C.loc[v, 'p_50000']), p5(C.loc[v, 'q_50000']), si(C.loc[v, 'relevante_10000']), si(C.loc[v, 'relevante_50000']), si(C.loc[v, 'cambia_relevancia']), rr(C.loc[v, 'dif_q'], 4), rr(C.loc[v, 'z_incrementos'], 2), interp(C.loc[v])] for v in orden_q]
    nt = D.tabla('Comparación de las 33 variables entre 10.000 y 50.000 permutaciones. En azul, las que cumplen q < 0,10.', ['Variable', 'SU', 'p 10.000', 'q 10.000', 'p 50.000', 'q 50.000', '<0,10 en 10.000', '<0,10 en 50.000', '¿Cambia de lado?', 'Dif. q', 'z', 'Lectura'], filas,
                 [3.6, 0.95, 1.15, 1.15, 1.15, 1.15, 1.05, 1.05, 1.25, 1.15, 0.9, 2.05], ['i', 'd', 'd', 'd', 'd', 'd', 'c', 'c', 'c', 'd', 'd', 'i'], tam=7.5, resaltar=list(c.set_index('variable').loc[orden_q, 'relevante_50000']))
    D.explicar(nt, 'Para cada variable, SU, p y q de ambas ejecuciones, si cumple el criterio en cada una, si cambia de clasificación, la diferencia de q (50.000 menos 10.000) y el estadístico z de consistencia.', f'**Ninguna de las 33 variables cambia de clasificación.** La mayor discrepancia es |z| = {P._n(c["z_incrementos"].abs().max(), 2)}, muy por debajo del límite de 3,19.')
    nf = D.figura(FIGURAS / 'q_10000_50000_word.png', 'q de las 12 variables más cercanas al criterio, con su intervalo de Monte Carlo en cada ejecución.', 15.0)
    D.explicar(nf, 'Cada par de marcas compara el q de una variable en ambas ejecuciones, con su intervalo de incertidumbre. La línea negra marca el criterio q = 0,10.', 'Los intervalos de 50.000 son más estrechos y, para las seis variables relevantes, quedan completamente bajo 0,10. Existe una separación visible entre esas seis y la siguiente variable. Aumentar las permutaciones mejoró la precisión sin alterar el grupo identificado.')
    D.h2('Origen de las diferencias numéricas')
    D.lista([f'**Precisión de Monte Carlo.** Las diferencias se deben a que cada ejecución usa una muestra finita de permutaciones. La mayor diferencia de p es {p5(c["dif_p"].abs().max())}; la mayor de q, {p5(c["dif_q"].abs().max())} (`{c.loc[c["dif_q"].abs().idxmax(), "variable"]}`), y la mediana de la diferencia absoluta de q, {p5(c["dif_q"].abs().median())}.', '**Efecto de la familia.** En Benjamini-Hochberg, el q de una variable depende también de los p de las demás, porque se ordenan e igualan por tramos. Por eso una variable puede cambiar su q aunque su propio p casi no cambie, y varias pueden compartir el mismo q. El archivo `comparacion_10000_50000.csv` separa ambos efectos.', '**Ninguna otra causa técnica.** Las 33 diferencias están dentro del límite de compatibilidad fijado de antemano.'])
    D.h2('Efecto sobre las conclusiones')
    D.p('**Las diferencias numéricas no modifican las conclusiones.** Las variables que cumplen el criterio, sus clases descriptivas y las decisiones de FCBF son las mismas. La SU, la correlación de Spearman y las comparaciones por categoría son idénticas en ambas ejecuciones. Una diferencia pequeña de q **no representa un cambio en la relación entre la variable y la severidad**.')
    D.p('El único cambio aparente es que la referencia q < 0,05 pasa de ninguna variable a dos. Esto refleja precisión numérica y no un cambio sustantivo. Además, la comparación evalúa **precisión y consistencia numérica sobre el mismo conjunto de datos**: no equivale a reproducir el resultado en una población independiente.')
    D.h2('Resultados históricos anteriores a esta revisión')
    D.p('**Los siguientes resultados no forman parte de las dos versiones principales.** Se conservan sin cambios como versiones previas y corresponden a **otra composición de variables**, sin las cuatro antiguas de control en la familia y con `doble_carga`. Sus q no son comparables con los de esta revisión ni se reutilizan.')
    filas = [[f['version_previa'], f['estado'], f['composicion'], f'{int(f["permutaciones"]):,}'.replace(',', '.'), P._n(float(f['umbral_q']), 2), str(f['n_relevantes']), (f['seleccionadas_adaptado'] or 'ninguna').replace(';', ', ')] for f in previas.to_dict('records')]
    nt = D.tabla('Versiones previas, identificadas como tales.', ['Versión', 'Estado', 'Composición de la familia', 'Permut.', 'Umbral q', 'N.º relevantes', 'Seleccionadas por FCBF adaptado'], filas, [1.4, 2.0, 4.3, 1.4, 1.2, 1.7, 4.55], ['c', 'i', 'i', 'd', 'c', 'c', 'i'], tam=8, mantener=True)
    f30 = rel_b.loc[relevantes, 'q_familia_30']
    D.explicar(nt, 'El estado, la composición, el número de permutaciones, el umbral y el resultado de cada versión previa.', f'Sirven como registro histórico, pero no para comparar valores q. Su principal aporte es mostrar que **la composición de la familia importa**: con los mismos p de 50.000, pero solo las 30 candidatas actualizadas, `frecuencia_fuerza` y `lugar_trabajo_comprensivo` tendrían q = {p3(f30["frecuencia_fuerza"])} y dejarían de cumplir el criterio, mientras que días de ejercicio y bajo impacto quedarían en q = {p3(f30["dias_ejercicio_semana"])}.')

    # ---- 11 ----
    D.orientacion(True)  # doce columnas no caben legibles en vertical
    D.h1('Comparación metodológica entre 34 y 33 variables')
    D.p('Esta sección compara la revisión corregida con la anterior. **La SU y el p de las 33 variables son idénticos en ambas: ningún cambio de q indica un cambio en los datos ni en la asociación con la severidad.** Solo cambió la corrección por comparaciones múltiples.')
    def fc(f, s):
        corto = {'seleccionada': 'Selecc.', 'redundante': 'Redund.', 'no relevante': 'No relev.', '': '—'}
        a_, e_ = f[f'fcbf_adaptado_{s}'], f[f'fcbf_estandar_{s}']
        if not isinstance(a_, str) or not a_:
            return '—'
        return corto[a_] if a_ == e_ else f'A: {corto[a_]}; E: {corto[e_]}'
    def tabla_cmp(t, N):
        t = t.sort_values(['q_34', 'variable'])
        filas = []
        for v, f in t.iterrows():
            ex = v == T.EXCLUIDA
            filas.append([nombre(v), p4(f['su_34']), '—' if ex else p4(f['su_33']), p5(f['p_34']), '—' if ex else p5(f['p_33']), p5(f['q_34']), '—' if ex else p5(f['q_33']), si(f['q_menor_0_10_34']), '—' if ex else si(str(f['q_menor_0_10_33']) == 'True'), 'Excluida' if ex else si(f['cambia_clase']), fc(f, 34), fc(f, 33)])
        return D.tabla(f'Comparación entre 34 y 33 variables con {N} permutaciones, de menor a mayor q con 34. En azul, las que cumplen q < 0,10. FCBF: A = adaptado, E = estándar, si difieren.', ['Variable', 'SU con 34', 'SU con 33', 'p con 34', 'p con 33', 'q con 34', 'q con 33', '<0,10 con 34', '<0,10 con 33', '¿Cambia la clase?', 'FCBF con 34', 'FCBF con 33'], filas,
                       [5.0, 1.1, 1.1, 1.35, 1.35, 1.35, 1.35, 1.15, 1.15, 1.3, 3.0, 3.0], ['i', 'd', 'd', 'd', 'd', 'd', 'd', 'c', 'c', 'c', 'i', 'i'], tam=8, resaltar=[str(x) == 'True' for x in t['q_menor_0_10_34']])
    nt = tabla_cmp(comp10, '10.000')
    D.explicar(nt, 'Para cada variable, la SU, el p y el q en ambas versiones, si cumple q < 0,10 en cada una, si cambia su clase y su decisión de FCBF. La fila de la diabetes se muestra para documentar la exclusión.', 'Las mismas seis variables cumplen q < 0,10. La variable excluida tenía q = ' + p3(comp10.loc[T.EXCLUIDA, 'q_34']) + ' y no integraba ese grupo, de modo que ningún par ni decisión de FCBF dependía de ella.')
    nt = tabla_cmp(comp50, '50.000')
    D.explicar(nt, 'La misma comparación con la ejecución complementaria.', 'El resultado es el mismo: **ninguna variable cambia su clasificación respecto de q < 0,10 ni de q < 0,05, ninguna cambia de clase y ninguna decisión de FCBF cambia.**')
    D.orientacion(False)
    nf = D.figura(FIGURAS / 'q_34_33_word.png', 'q de las 15 variables con menor q al pasar de 34 a 33 pruebas, en ambas ejecuciones.', 16.0)
    baja, sube, igual = int((comp50['dif_q'] < -5e-7).sum()), int((comp50['dif_q'] > 5e-7).sum()), int((comp50['dif_q'].abs() <= 5e-7).sum())
    D.explicar(nf, 'Cada par de marcas une el q de una variable con 34 pruebas y con 33. La línea negra marca el criterio q = 0,10.', f'El cambio es pequeño y nadie cruza el criterio. Con 50.000 permutaciones, q baja en {baja} variables, sube en {sube} y no cambia en {igual}; el mayor cambio absoluto es {p4(comp50["dif_q"].abs().max())}.')
    D.h2('Por qué algunos q bajan y otros suben')
    D.p('Benjamini-Hochberg multiplica cada p por m / j, donde m es el número de pruebas y j su posición de menor a mayor p. La diabetes ocupaba la posición 7. Al retirarla ocurren dos cosas:')
    D.lista(['**Las seis variables anteriores conservan su posición, pero m baja de 34 a 33.** Su q se multiplica por 33/34 y disminuye levemente.', '**Las variables posteriores suben una posición:** su factor pasa de 34 / j a 33 / (j − 1), que es mayor. Su q aumenta levemente, sin que cambie su p.', '**Las variables con q cercano a 1 pueden quedar igual,** porque la corrección nivela por tramos y limita los valores a 1.'])
    D.p('Este comportamiento es **propio de la corrección**. Por eso no debe interpretarse como que las seis variables se hicieron más fuertes ni las demás más débiles. Del mismo modo, q depende de qué pruebas integran la familia: con solo 30 candidatas, fuerza y lugar de trabajo no cumplirían el criterio (sección 17.4).')
    D.h2('Qué cambia y qué no cambia')
    D.tabla('Resumen de los efectos de la corrección.', ['Elemento', '¿Cambia?', 'Detalle'],
            [['Participantes y poblaciones', 'No', '529, 287 y 239'], ['Valores de las 33 variables', 'No', 'Comparados celda a celda'], ['SU y p', 'No', '33 de 33 iguales en ambas ejecuciones'], ['q', 'Sí, levemente', 'Ahora la familia tiene 33 pruebas'], ['Variables con q < 0,10', 'No', 'Las mismas seis'], ['Variables con q < 0,05', 'No', 'Ninguna con 10.000; dos con 50.000'], ['Clases descriptivas', 'No', 'Riesgo, protección, sin dirección, tendencia y sin respaldo'], ['Decisiones de FCBF', 'No', 'En ambas variantes y ejecuciones'], ['Conjunto inicial de la Fase 36', 'Sí', '33 variables, sin la diabetes']],
            [6.0, 2.3, 8.2], tam=9, mantener=True)

    # ---- 12 ----
    D.h1('Resultados de relevancia y redundancia')
    D.p('**Ninguna decisión depende de la variable excluida:** tenía la clasificación «no relevante» en ambas variantes, de modo que no eliminó a ninguna otra. Los rótulos siguen siendo informativos y no retiran variables de la Fase 36.')
    D.h2('Decisiones de FCBF')
    D.p('Las decisiones son idénticas con 10.000 y con 50.000 permutaciones, en ambas variantes. La tabla informa los valores que determinan cada decisión. Las columnas de SU no dependen de las permutaciones.')
    fa = fcbf[fcbf['decision'].isin(['seleccionada', 'redundante'])].copy()
    fa['_o'] = fa['variante'].map({'adaptado': 0, 'estandar': 1})
    fa = fa.sort_values(['_o', 'su_con_severidad'], ascending=[True, False])
    filas = [[f['variante'].replace('estandar', 'Estándar').replace('adaptado', 'Adaptado'), nombre(f['variable']), f['etapa'].replace('no laboral', 'General').replace('laboral', 'Laboral'), p4(f['su_con_severidad']), f['decision'].capitalize(), nombre(f['eliminada_por']) if isinstance(f['eliminada_por'], str) and f['eliminada_por'] else '—', p4(f['su_par']) if pd.notna(f['su_par']) else '—', p5(f['q_par']) if pd.notna(f['q_par']) else '—'] for _, f in fa.iterrows()]
    nt = D.tabla('Decisiones de FCBF en las seis variables relevantes, en la ejecución de 50.000 permutaciones.', ['Variante', 'Variable', 'Grupo', 'SU con severidad', 'Decisión', 'Redundante con', 'SU del par', 'q del par'], filas, [1.5, 4.0, 1.2, 1.65, 1.8, 3.3, 1.1, 1.5], ['i', 'i', 'i', 'd', 'i', 'i', 'd', 'd'], tam=8, mantener=True)
    D.explicar(nt, 'Qué decide cada variante de FCBF y con qué valores. En la variante adaptada, la decisión requiere además q del par < 0,10.', 'La variante adaptada conserva como no redundantes a fuerza, IMC, trabajo actual y lugar de trabajo. La variante estándar marca además el IMC y el trabajo actual como redundantes con fuerza, aunque esos pares no superan el azar (q = 1,00000 y q = ' + p3(par('frecuencia_fuerza', 'trabaja_actualmente')['q']) + '). Por eso resulta preferible leer la variante adaptada.')
    D.h2('Relación entre días de ejercicio, bajo impacto y fuerza')
    p_db, p_df, p_bf = par('dias_ejercicio_semana', 'frecuencia_bajo_impacto'), par('dias_ejercicio_semana', 'frecuencia_fuerza'), par('frecuencia_bajo_impacto', 'frecuencia_fuerza')
    fu, di, ba = categoria('frecuencia_fuerza', 'Rara vez'), d.loc['dias_ejercicio_semana'], d.loc['frecuencia_bajo_impacto']
    no_fu = categoria('frecuencia_fuerza', 'No lo realiza')
    D.p('Las tres variables describen actividad física y comparten información. Sin embargo, la lectura de FCBF requiere cuidado, porque conserva a `frecuencia_fuerza` y considera redundantes a las otras dos, aunque estas muestran asociaciones negativas más claras con el MRS total.')
    D.tabla('Los tres indicadores de actividad física.', ['Variable', 'SU con severidad', 'ρ con MRS (IC 95 %)', 'Dirección', 'Decisión de FCBF'],
            [[nombre(v), p4(C.loc[v, 'su']), f'{r3(d.loc[v, "rho_mrs"])} ({r3(d.loc[v, "rho_ic95_inferior"])} a {r3(d.loc[v, "rho_ic95_superior"])})', d.loc[v, 'direccion'].capitalize(), x] for v, x in (('frecuencia_fuerza', 'Se conserva por tener la mayor SU'), ('dias_ejercicio_semana', f'Redundante: {p4(p_df["su"])} ≥ {p4(C.loc["dias_ejercicio_semana", "su"])}'), ('frecuencia_bajo_impacto', f'Redundante: {p4(p_bf["su"])} ≥ {p4(C.loc["frecuencia_bajo_impacto", "su"])}'))],
            [4.2, 1.7, 4.0, 1.8, 4.8], ['i', 'd', 'c', 'i', 'i'], tam=8.5, mantener=True)
    D.p('Este resultado se explica por cómo funciona el método, no porque fuerza sea más importante:')
    D.lista([f'**FCBF procesa primero la variable con mayor SU.** Entre las variables generales, fuerza tiene la mayor SU ({p4(C.loc["frecuencia_fuerza", "su"])}), aunque solo {P._n(C.loc["frecuencia_fuerza", "su"] - C.loc["dias_ejercicio_semana", "su"], 4)} por sobre días de ejercicio. Esa pequeña diferencia decide cuál queda primero.',
             f'**SU ignora el orden.** Premia cualquier patrón en las categorías, también uno irregular. En fuerza destaca «Rara vez» (n = {int(fu["n"])}), con {p1(fu["pct_severas"])} % de severas, frente a {p1(no_fu["pct_severas"])} % de quienes no la realizan. Spearman, en cambio, busca una tendencia ordenada y no la encuentra de forma clara: su intervalo incluye 0.',
             f'**La redundancia es alta en relación con esa SU.** Fuerza comparte con días de ejercicio una SU de {p4(p_df["su"])} y con bajo impacto de {p4(p_bf["su"])}, valores mayores que la SU de estas variables con la severidad. Días y bajo impacto también están muy relacionadas entre sí ({p4(p_db["su"])}).',
             '**La mayoría no realiza ejercicio de fuerza.** ' + f'{int(no_fu["n"])} de 529 participantes están en «No lo realiza» ({p1(100 * no_fu["n"] / 529)} %). Por eso, las demás categorías tienen pocas personas y sus porcentajes son inestables.',
             '**La simulación no apoya una lectura de fuerza como factor principal.** El simulador programa el efecto en los días de ejercicio y no le asigna a fuerza ni a bajo impacto un efecto directo propio. Esto se menciona solo para interpretar: no se usó para clasificar variables.'])
    D.p('**En consecuencia, que FCBF conserve fuerza no prueba que sea más protectora ni clínicamente más importante.** Tampoco que días y bajo impacto sean prescindibles. Para describir la dirección, días de ejercicio y bajo impacto entregan una lectura más clara. Los tres indicadores se conservan para la Fase 36.')
    D.h2('Pares entre las variables relevantes')
    nf = D.figura(FIGURAS / 'su_pares_relevantes_word.png', 'SU entre las seis variables con q < 0,10. Los pares con la variable laboral se miden con n = 287.', 14.0)
    D.explicar(nf, 'Cuánta información comparte cada par de variables relevantes. Los tonos más oscuros indican mayor redundancia.', f'La redundancia se concentra en el bloque de actividad física. Son los tres únicos pares con q < 0,10. Las demás SU son muy pequeñas, de modo que IMC, trabajo actual y lugar de trabajo aportan información en gran medida distinta. También puede verse la SU de las {len(todas_parejas)} parejas de las 33 variables en `su_todas_las_parejas.csv`.')
    filas = [[nombre(x['variable_1']), nombre(x['variable_2']), str(int(x['n'])), p4(x['su']), p5(y['q']), p5(x['q'])] for (_, x), (_, y) in zip(pares.iterrows(), a['pares_relevantes'].iterrows())]
    if not (pares[['variable_1', 'variable_2']].values == a['pares_relevantes'][['variable_1', 'variable_2']].values).all():
        raise RuntimeError('Los pares no están en el mismo orden en ambas versiones.')
    D.tabla('Pares entre las seis variables relevantes, con q de sus pruebas de permutación.', ['Variable 1', 'Variable 2', 'n', 'SU', 'q con 10.000', 'q con 50.000'], filas, [5.2, 5.2, 0.9, 1.3, 1.9, 1.9], ['i', 'i', 'd', 'd', 'd', 'd'], tam=8.5)
    if ((pares['q'] < R.ALFA).sum(), a['pares_relevantes']['q'].lt(R.ALFA).sum()) != (3, 3):
        raise RuntimeError('El número de pares con q < 0,10 no coincide con el texto.')

    D.h1('Análisis de posibles factores de riesgo y protección')
    D.p('SU indica que hay asociación. El signo viene de Spearman y de las comparaciones por categoría, que **no dependen del número de permutaciones**. Se distinguen dos niveles: las variables que **superaron q < 0,10** y las que presentan **solo tendencias descriptivas**. Ninguna asociación se interpreta como causal.')
    D.h2('Asociaciones compatibles con mayor severidad (q < 0,10)')
    D.p(f'**IMC.** {ficha("imc")} El porcentaje de severas aumenta de forma bastante ordenada con el IMC. Casi la mitad de los valores son imputados, pero con las 267 observaciones reales la asociación se mantiene: ρ = {r3(sens.loc["imc", "rho_mrs"])} y q = {p3(sens.loc["imc", "q_al_reemplazar"])} al reemplazar su p en la familia.')
    D.p(f'**Trabaja actualmente.** {ficha("trabaja_actualmente")} Debe leerse con cautela: tiene 22 valores imputados como «Sí», su SU es baja y el simulador no le programa un efecto directo. Su efecto programado ocurre solo por la doble carga de trabajo y cuidado. Por tanto, la asociación podría reflejar esa combinación, no el hecho de trabajar en sí.')
    D.h2('Asociaciones compatibles con menor severidad (q < 0,10)')
    D.p(f'**Días de ejercicio a la semana.** {ficha("dias_ejercicio_semana")} La escala empieza en 1 = 0 días. El porcentaje de severas desciende de manera ordenada, y es una de las lecturas más claras del conjunto.')
    D.p(f'**Frecuencia de ejercicio de bajo impacto.** {ficha("frecuencia_bajo_impacto")} La categoría «Siempre» tiene pocas personas y un intervalo amplio.')
    D.p(f'**Lugar de trabajo comprensivo.** {ficha("lugar_trabajo_comprensivo")} Es la correlación de mayor magnitud entre las variables relevantes y se aplica solo a la población laboral (sección 14).')
    D.h2('Asociación sin dirección clara (q < 0,10)')
    D.p(f'**Frecuencia de ejercicio de fuerza.** {ficha("frecuencia_fuerza")} Aunque los extremos sugieren menor severidad con más fuerza, el patrón no es ordenado: «Rara vez» (n = {int(fu["n"])}) tiene el mayor porcentaje de severas ({p1(fu["pct_severas"])} %). El intervalo de ρ incluye 0 y Kruskal-Wallis tiene p = {p3(d.loc["frecuencia_fuerza", "kw_p"])}, por lo que la regla la clasifica como mixta. **No se presenta como factor protector.**')
    filas = [[nombre(v), d.loc[v, 'clase'], str(int(d.loc[v, 'n'])), r3(d.loc[v, 'rho_mrs']), r1(d.loc[v, 'dif_pct_severas']), p3(C.loc[v, 'q_10000']), p3(C.loc[v, 'q_50000'])] for v in RIESGO + PROTECCION + SIN_DIRECCION]
    nf = D.figura(FIGURAS / 'rho_33_variables_word.png', 'ρ de Spearman con el MRS total. `quien_prepara_comidas` es nominal y no tiene signo, por lo que no aparece.', 15.0)
    D.explicar(nf, 'La correlación de cada variable con el MRS total y su intervalo de confianza. El color indica la dirección y el relleno indica si la variable supera q < 0,10.', 'Hay variables con correlación clara que no superan el criterio de SU, como la sobrecarga, el estrés laboral y el tabaco, y una variable que supera el criterio sin correlación clara: fuerza. Las dos medidas responden a preguntas distintas y no deben confundirse.')
    nf = D.figura(FIGURAS / 'severas_relevantes_word.png', 'Porcentaje de síntomas severos por categoría en las seis variables con q < 0,10, con IC 95 % de Wilson.', 16.0)
    D.explicar(nf, 'El porcentaje de participantes con síntomas severos en cada categoría, con el tamaño de cada grupo. Las barras de error muestran la incertidumbre.', 'Los patrones de IMC, días de ejercicio, bajo impacto y lugar de trabajo son relativamente ordenados, mientras que el de fuerza no lo es. Varias categorías tienen pocas personas (por ejemplo, IMC < 18,5 con n = 2) y sus porcentajes no deben interpretarse por separado.')
    nt = D.tabla('Resumen de las seis variables que superan q < 0,10 en ambas ejecuciones.', ['Variable', 'Clase', 'n', 'ρ con MRS', 'Dif. % severas', 'q SU 10.000', 'q SU 50.000'], filas, [5.0, 4.6, 0.9, 1.4, 1.5, 1.6, 1.6], ['i', 'i', 'd', 'd', 'd', 'd', 'd'], tam=8.5, mantener=True)
    D.explicar(nt, 'Las seis variables que superan el criterio, con su clase, su correlación y su q en ambas ejecuciones. «Dif. % severas» compara las categorías extremas con n ≥ 10.', 'Cinco tienen una dirección definida y una no. Superar el criterio y tener una dirección clara son condiciones distintas, y ninguna de ellas implica causalidad.')
    D.h2('Tendencias descriptivas (no superan q < 0,10)')
    D.p('Las siguientes siete variables tienen una correlación de Spearman con q < 0,10, pero **no superan el criterio ajustado de SU**. Por eso se describen como __indicios__ y no como posibles factores.')
    tend = INDICIOS_RIESGO + INDICIOS_PROTECCION
    filas = [[nombre(v), 'Mayor severidad' if v in INDICIOS_RIESGO else 'Menor severidad', str(int(d.loc[v, 'n'])), r3(d.loc[v, 'rho_mrs']), f'{r3(d.loc[v, "rho_ic95_inferior"])} a {r3(d.loc[v, "rho_ic95_superior"])}', p4(d.loc[v, 'rho_q']), r1(d.loc[v, 'dif_pct_severas']), p3(C.loc[v, 'q_10000']), p3(C.loc[v, 'q_50000'])] for v in tend]
    nf = D.figura(FIGURAS / 'severas_tendencias.png', 'Porcentaje de síntomas severos por categoría en las siete variables con solo tendencias descriptivas.', 16.0)
    D.explicar(nf, 'Las categorías de cada variable con tendencia, incluida la incertidumbre de cada porcentaje.', 'En varias variables, las diferencias se concentran en categorías pequeñas o en un salto entre niveles, no en un aumento gradual. Por eso SU, que no considera el orden, y Spearman pueden llegar a conclusiones distintas.')
    nt = D.tabla('Variables con solo tendencias descriptivas.', ['Variable', 'Tendencia', 'n', 'ρ con MRS', 'IC 95 % de ρ', 'q de ρ', 'Dif. % severas', 'q SU 10.000', 'q SU 50.000'], filas, [4.5, 2.1, 0.8, 1.1, 2.6, 1.2, 1.2, 1.3, 1.3], ['i', 'i', 'd', 'd', 'c', 'd', 'd', 'd', 'd'], tam=8, mantener=True)
    D.explicar(nt, 'La tendencia ordinal de cada variable, con la diferencia de porcentaje de severas entre sus categorías extremas con n ≥ 10.', f'Estas variables conviene mantenerlas a la vista, pero no presentarlas como factores respaldados por SU. La fuerza del indicio varía: `falta_tiempo_influye` casi no muestra diferencia entre extremos ({r1(d.loc["falta_tiempo_influye", "dif_pct_severas"])} puntos), y en la sobrecarga la diferencia entre extremos es imprecisa por una categoría pequeña (sección 15).')
    sin = c[(~c['relevante_50000'])].set_index('variable').index.difference(tend)
    sin = [v for v in orden_q if v in sin]
    D.h2('Variables sin suficiente respaldo')
    D.p(f'Las {len(sin)} variables restantes no superan q < 0,10 ni muestran una tendencia ordinal corregida: {lista_y(nombre(v).lower() if v != "imc" else "IMC" for v in sin)}. **Esto no prueba ausencia de asociación**; solo indica que estos datos no la respaldan con los criterios usados. La tabla completa con la dirección de las 33 variables se presenta a continuación.')
    filas = [[nombre(v), str(int(d.loc[v, 'n'])), r3(d.loc[v, 'rho_mrs']) if pd.notna(d.loc[v, 'rho_mrs']) else '—', f'{r3(d.loc[v, "rho_ic95_inferior"])} a {r3(d.loc[v, "rho_ic95_superior"])}' if pd.notna(d.loc[v, 'rho_mrs']) else '—', r3(d.loc[v, 'rho_severo']) if pd.notna(d.loc[v, 'rho_severo']) else '—', p4(d.loc[v, 'rho_q']) if pd.notna(d.loc[v, 'rho_q']) else '—', p4(d.loc[v, 'kw_p']), p4(d.loc[v, 'epsilon2']), r1(d.loc[v, 'dif_mrs']) if pd.notna(d.loc[v, 'dif_mrs']) else '—', r1(d.loc[v, 'dif_pct_severas']) if pd.notna(d.loc[v, 'dif_pct_severas']) else '—', str(d.loc[v, 'direccion']).capitalize(), d.loc[v, 'clase']] for v in orden_q]
    nt = D.tabla('Dirección y clasificación de las 33 variables, ordenadas por q de SU con 50.000. La clase es la misma en ambas ejecuciones.', ['Variable', 'n', 'ρ con MRS', 'IC 95 % de ρ', 'ρ con severo', 'q de ρ', 'p de K-W', 'ε²', 'Dif. MRS', 'Dif. % severas', 'Dirección', 'Clase'], filas, [3.05, 0.65, 0.9, 2.15, 0.9, 1.0, 1.0, 1.0, 0.75, 1.1, 1.3, 2.65], ['i', 'd', 'd', 'c', 'd', 'd', 'd', 'd', 'd', 'd', 'i', 'i'], tam=7.2, resaltar=list(c.set_index('variable').loc[orden_q, 'relevante_50000']))
    D.explicar(nt, 'Todas las medidas de dirección por variable: ρ con el MRS total y con la severidad, q de Spearman, Kruskal-Wallis con su tamaño de efecto (ε²), y las diferencias entre las categorías extremas con n ≥ 10.', 'Los tamaños de efecto son pequeños. La clase de cada variable no cambia entre ejecuciones, y las comparaciones por categoría son descriptivas: no están corregidas por multiplicidad.')

    # ---- 13 ----
    D.h1('Análisis específico de trabajadoras')
    tr_no, tr_si = categoria('trabaja_actualmente', 'No'), categoria('trabaja_actualmente', 'Sí')
    D.p(f'**Hay dos preguntas distintas.** La primera compara a toda la muestra según si trabaja o no ({int(tr_si["n"])} frente a {int(tr_no["n"])} participantes). La segunda analiza, solo entre quienes trabajan, las condiciones laborales (`lugar_trabajo_comprensivo` y `estres_entorno_laboral`), con {pob["laboral"]} participantes.')
    D.p(f'**Por qué son 287 y no 309.** De las {int(tr_si["n"])} clasificadas como trabajadoras, 22 tienen esa condición imputada y no tienen ninguna respuesta laboral. No se les asigna un valor de cero: quedan fuera de esta población. Quienes no trabajan tampoco entran, porque las preguntas no se les aplican. Por esta misma razón, `trabaja_actualmente` es constante entre las 287, y su SU con las variables laborales es 0.')
    filas = []
    for v in ('lugar_trabajo_comprensivo', 'estres_entorno_laboral'):
        f = d.loc[v]
        filas.append([nombre(v), p4(C.loc[v, 'su']), p3(C.loc[v, 'q_10000']), p3(C.loc[v, 'q_50000']), f'{r3(f["rho_mrs"])} ({r3(f["rho_ic95_inferior"])} a {r3(f["rho_ic95_superior"])})', p4(f['rho_q']), f'{r1(f["dif_pct_severas"])} ({r1(f["dif_pct_ic_inferior"])} a {r1(f["dif_pct_ic_superior"])})', f['clase']])
    nt = D.tabla(f'Variables laborales (n = {pob["laboral"]}).', ['Variable', 'SU', 'q 10.000', 'q 50.000', 'ρ con MRS (IC 95 %)', 'q de ρ', 'Dif. % severas (IC 95 %)', 'Clase'], filas, [2.9, 1.0, 1.05, 1.05, 3.3, 1.15, 3.3, 2.8], ['i', 'd', 'd', 'd', 'c', 'd', 'c', 'i'], tam=7.5, mantener=True)
    par_le = todas_parejas[(todas_parejas['variable_1'] == 'estres_entorno_laboral') & (todas_parejas['variable_2'] == 'lugar_trabajo_comprensivo')].iloc[0]
    D.explicar(nt, 'La asociación de las dos condiciones laborales con la severidad, entre las trabajadoras con valor en ambas preguntas.', f'Un lugar de trabajo percibido como comprensivo se asocia con menor severidad y supera el criterio. El estrés laboral muestra una tendencia hacia mayor severidad, pero no supera el criterio de SU. Ambas preguntas comparten poca información (SU = {p4(par_le["su"])}). Las dos mencionan los síntomas, por lo que quien tiene más síntomas podría percibir de otro modo su trabajo: la dirección de la relación no queda determinada.')
    nf = D.figura(FIGURAS / 'severas_trabajadoras.png', f'Porcentaje de síntomas severos según las condiciones laborales (n = {pob["laboral"]}).', 15.0)
    D.explicar(nf, 'La severidad en cada nivel de ambas preguntas laborales.', 'El lugar de trabajo muestra una separación entre «Neutral» o menos y «De acuerdo» o más. El estrés aumenta sobre todo en los niveles alto y extremo. Las categorías extremas de menor tamaño tienen intervalos amplios.')
    D.p(f'**Lectura cuidadosa.** Dentro de las {pob["laboral"]}, {pob["laborales_observadas_en_287"]} tienen ambas preguntas observadas. Además, `lugar_trabajo_comprensivo` supera el criterio con 33 pruebas ({p3(C.loc["lugar_trabajo_comprensivo", "q_50000"])}), pero no con 30 ({p3(rel_b.loc["lugar_trabajo_comprensivo", "q_familia_30"])}). Estos resultados describen a las trabajadoras de la muestra y no pueden extenderse a quienes no trabajan.')

    # ---- 14 ----
    D.h1('Análisis específico de cuidadoras, incluida la sobrecarga')
    D.h2('Qué significa la sobrecarga y por qué se analiza entre cuidadoras')
    D.p('La variable `sobrecarga_fisica_emocional` corresponde a la pregunta: **«¿Siente que la combinación entre su trabajo y las tareas de cuidado le genera una sobrecarga física o emocional?»**, con una escala de 1 («Nunca o casi nunca») a 5 («Siempre»). Mide una **percepción subjetiva**.')
    D.p('Se analiza específicamente entre cuidadoras porque la pregunta se aplica solo a quienes cuidan a otras personas. Para quien no cuida, no existe un grado de sobrecarga. Asignarle cero la presentaría falsamente como el nivel más bajo y, en la práctica, la variable mediría si la persona cuida o no.')
    D.h2('Población de la figura: corrección realizada')
    obs = cat[cat['variable'] == SOBRECARGA]
    D.p('La figura univariada se revisó contra los resultados. **Representa a las 251 cuidadoras, incluidas 12 respuestas imputadas**. Sus categorías coinciden con las 239 observadas, salvo «A veces», que tiene 106 en lugar de 94: las 12 imputadas están en esa categoría, porque se imputaron con la mediana. El subtítulo original indicaba «n válido = 251 · faltante = 0 (0,0 %)» y no advertía estas imputaciones. Se corrigió únicamente el subtítulo, en una copia; la figura original y sus valores no cambiaron.')
    nf = D.figura(FIG_CORREGIDA, 'Distribución de la sobrecarga física y emocional, con el subtítulo corregido. Descripción con n = 251; el análisis de asociación usa n = 239.', 10.0)
    filas_dist = []
    dist_251 = {'Nunca o casi nunca': 10, 'Rara vez': 34, 'A veces': 106, 'Frecuentemente': 69, 'Siempre': 32}
    for _, f in obs.iterrows():
        filas_dist.append([f['categoria'], str(int(f['n'])), p1(100 * f['n'] / 239), str(dist_251[f['categoria']]), p1(100 * dist_251[f['categoria']] / 251), str(dist_251[f['categoria']] - int(f['n']))])
    if [int(x) for x in obs['n']] != [10, 34, 94, 69, 32] or sum(dist_251.values()) != 251:
        raise RuntimeError('Las frecuencias de sobrecarga no coinciden con la figura.')
    D.explicar(nf, 'Con qué frecuencia las 251 cuidadoras declaran sobrecarga. «A veces» incluye las 12 respuestas imputadas.', 'La mayoría de las cuidadoras se ubica en los niveles intermedios y altos. El tamaño de «A veces» está aumentado por la imputación, por lo que el porcentaje observado de esa categoría es menor.')
    nt = D.tabla('Distribución de la sobrecarga en ambas poblaciones.', ['Categoría', 'Observadas: n', 'Observadas: %', 'Con imputadas: n', 'Con imputadas: %', 'Imputadas'], filas_dist, [5.0, 2.3, 2.3, 2.5, 2.5, 1.9], ['i', 'd', 'd', 'd', 'd', 'd'], tam=9, mantener=True)
    D.explicar(nt, 'Las dos poblaciones existentes y en qué difieren.', 'Solo difiere «A veces». Por eso, las 239 observadas son la población principal del análisis, y las 251 se informan únicamente como sensibilidad.')
    D.h2('Relación con la severidad del MRS')
    fS = d.loc[SOBRECARGA]
    filas = [[f['categoria'], str(int(f['n'])), f'{p1(f["mrs_medio"])} ({p1(f["mrs_ic95_inferior"])} a {p1(f["mrs_ic95_superior"])})', f'{p1(f["mrs_mediana"])} ({p1(f["mrs_q1"])}-{p1(f["mrs_q3"])})', str(int(f['severas'])), f'{p1(f["pct_severas"])} ({p1(f["pct_ic95_inferior"])} a {p1(f["pct_ic95_superior"])})'] for _, f in obs.iterrows()]
    nt = D.tabla('Severidad según el nivel de sobrecarga (n = 239).', ['Categoría', 'n', 'MRS medio (IC 95 %)', 'Mediana (Q1-Q3)', 'Severas', '% severas (IC 95 %)'], filas, [3.8, 0.9, 3.6, 3.0, 1.5, 3.7], ['i', 'd', 'c', 'c', 'd', 'c'], tam=9, mantener=True)
    D.explicar(nt, 'El MRS y el porcentaje de severas en cada nivel de sobrecarga.', f'El MRS medio aumenta con la sobrecarga: de {p1(obs.iloc[0]["mrs_medio"])} a {p1(obs.iloc[4]["mrs_medio"])}. ρ = {r3(fS["rho_mrs"])} (IC 95 %: {r3(fS["rho_ic95_inferior"])} a {r3(fS["rho_ic95_superior"])}), q de ρ = {p4(fS["rho_q"])} y ε² = {p3(fS["epsilon2"])}. El porcentaje de severas, sin embargo, no sube gradualmente: se mantiene cerca de 47-48 % en los niveles 2 y 3, y sube a 66-70 % en los niveles 4 y 5. El nivel 1 tiene 60 %, pero con solo 10 personas.')
    D.h2('Por qué hay asociación con el MRS, pero no supera q < 0,10')
    D.p(f'La sobrecarga presenta una **asociación positiva con el MRS total** y, al mismo tiempo, **no supera el criterio de SU**: q = {p3(C.loc[SOBRECARGA, "q_10000"])} con 10.000 y {p3(C.loc[SOBRECARGA, "q_50000"])} con 50.000. No hay contradicción, porque estas medidas evalúan cosas distintas:')
    D.lista(['**Ignorar el orden.** Spearman aprovecha que los niveles están ordenados; SU no. La misma tendencia que Spearman detecta se reparte en SU entre cinco categorías.',
             f'**Variable objetivo distinta.** Spearman usa el MRS total, con toda su variación. SU usa `severo_mrs`, un corte binario, que pierde información: con la severidad binaria, ρ baja de {r3(fS["rho_mrs"])} a {r3(fS["rho_severo"])}.',
             f'**Menor tamaño.** Con 239 personas y cinco categorías, el azar produce SU relativamente altas. Por ello, aunque la SU observada es la segunda mayor ({p4(C.loc[SOBRECARGA, "su"])}), cerca de {p1(100 * rel_b.loc[SOBRECARGA, "p"])} % de las permutaciones la igualó o superó.',
             f'**Corrección por 33 pruebas.** Su p es {p3(s_p)}, bajo 0,05 antes de corregir. Con la corrección, q es {p3(s_q)}.',
             f'**Categoría baja pequeña.** Las 10 personas del nivel 1 tienen 60 % de severas, por lo que la diferencia entre extremos es incierta: {r1(fS["dif_pct_severas"])} puntos (IC 95 %: {r1(fS["dif_pct_ic_inferior"])} a {r1(fS["dif_pct_ic_superior"])}).'])
    D.p(f'**Sensibilidad con 251.** Al incluir las 12 imputadas, ρ = {r3(sens.loc[SOBRECARGA, "rho_mrs"])} y q = {p3(sens.loc[SOBRECARGA, "q_al_reemplazar"])} al reemplazar su p en la familia. Tampoco supera el criterio. **Por lo tanto, la sobrecarga no se presenta como un factor de riesgo confirmado mediante SU, sino como un indicio de riesgo descrito por una tendencia ordinal.**')
    D.h2('Cuidadoras que no trabajan')
    niv = pd.read_csv(POR_NIVEL, encoding='utf-8-sig')
    trab, notr = niv[niv['condicion'] == 'trabaja'], niv[niv['condicion'] == 'no trabaja']
    if int(notr['n'].sum()) != 99 or int(trab['n'].sum()) != 140:
        raise RuntimeError('Los grupos de cuidadoras no coinciden con el texto.')
    et = list(obs['categoria'])
    filas = [[et[i], str(int(trab.iloc[i]['n'])), p1(trab.iloc[i]['pct_severas']), p1(trab.iloc[i]['mrs_medio']), str(int(notr.iloc[i]['n'])), p1(notr.iloc[i]['pct_severas']), p1(notr.iloc[i]['mrs_medio'])] for i in range(5)]
    nt = D.tabla('Sobrecarga y severidad según situación laboral (descriptivo; n = 239, sin prueba estadística por subgrupo).', ['Categoría', 'Trabaja: n', 'Trabaja: % severas', 'Trabaja: MRS medio', 'No trabaja: n', 'No trabaja: % severas', 'No trabaja: MRS medio'], filas, [4.1, 1.7, 2.1, 2.1, 1.9, 2.3, 2.3], ['i', 'd', 'd', 'd', 'd', 'd', 'd'], tam=9, mantener=True)
    D.explicar(nt, 'Cómo se distribuye la sobrecarga entre las 140 cuidadoras clasificadas como trabajadoras y las 99 que no trabajan. Entre las 140, 10 tienen la condición laboral imputada.', f'**La pregunta menciona «su trabajo», pero 99 de las 239 cuidadoras (41,4 %) no trabajan.** Ellas pudieron interpretar la pregunta de otra forma, por ejemplo, como sobrecarga por el trabajo doméstico o solo por el cuidado. Por lo tanto, la variable no mide exactamente lo mismo en ambos grupos. Quienes no trabajan se concentran más en los niveles bajos o intermedios, y el nivel «Siempre» tiene solo 4 personas. Esto es un **problema de validez que conviene consultar con la profesora**.')
    D.h2('Diferencia entre cantidad de personas cuidadas y sobrecarga')
    rel = pd.read_csv(RELACION, encoding='utf-8-sig')
    r_obs = rel[(rel['poblacion'] == 'población de la sobrecarga') & (rel['par'] == 'sobrecarga y cantidad')].iloc[0]
    r_cero = rel[rel['poblacion'].str.startswith('todas') & (rel['par'] == 'sobrecarga y cantidad')].iloc[0]
    fC = d.loc['cantidad_personas_cuida']
    D.tabla('Cantidad de personas cuidadas frente a sobrecarga percibida.', ['Aspecto', 'Cantidad de personas que cuida', 'Sobrecarga física y emocional'],
            [['Qué mide', 'Un hecho: a cuántas personas cuida de forma directa', 'Una percepción: cuánta sobrecarga le genera la combinación de trabajo y cuidado'], ['Población', '529 (0 = no cuida)', '239 cuidadoras con respuesta observada'], ['SU y q con 50.000', f'{p4(C.loc["cantidad_personas_cuida", "su"])}; q = {p3(C.loc["cantidad_personas_cuida", "q_50000"])}', f'{p4(C.loc[SOBRECARGA, "su"])}; q = {p3(C.loc[SOBRECARGA, "q_50000"])}'], ['ρ con MRS (IC 95 %)', f'{r3(fC["rho_mrs"])} ({r3(fC["rho_ic95_inferior"])} a {r3(fC["rho_ic95_superior"])})', f'{r3(fS["rho_mrs"])} ({r3(fS["rho_ic95_inferior"])} a {r3(fS["rho_ic95_superior"])})'], ['Dirección', f'{fC["direccion"].capitalize()} (Kruskal-Wallis p = {p3(fC["kw_p"])})', f'{fS["direccion"].capitalize()}'], ['Clase', fC['clase'], fS['clase']]],
            [3.5, 6.5, 6.5], tam=9, mantener=True)
    cc = [categoria('cantidad_personas_cuida', x) for x in ('No cuida', '1 persona', '2 personas', '3 o más personas')]
    D.p(f'**No son la misma variable.** Cuidar a más personas no implica necesariamente percibir más sobrecarga. Entre las 239, la relación es moderada: ρ = {r3(r_obs["rho_spearman"])} y SU = {p4(r_obs["su"])}. La cifra de ρ = {r3(r_cero["rho_spearman"])} que se obtiene al asignar 0 a las 529 es un **artefacto**: refleja sobre todo la diferencia entre cuidar y no cuidar, y se informa solo como referencia.')
    D.p(f'En cantidad de personas, el porcentaje de severas pasa de {p1(cc[0]["pct_severas"])} % (no cuida) a {p1(cc[1]["pct_severas"])} % (1 persona) y {p1(cc[2]["pct_severas"])} % (2 personas), pero baja a {p1(cc[3]["pct_severas"])} % con 3 o más (n = {int(cc[3]["n"])}). Este patrón no es monótono y explica por qué su ρ es prácticamente nula y su dirección es mixta. **Por eso la variable se clasifica como sin respaldo, mientras que la sobrecarga es un indicio de riesgo.**')
    nf = D.figura(FIGURAS / 'severas_cuidadoras.png', 'Porcentaje de síntomas severos según sobrecarga (n = 239) y cantidad de personas cuidadas (n = 529).', 15.0)
    D.explicar(nf, 'La severidad en cada nivel de ambas variables de cuidado.', 'La sobrecarga percibida muestra un salto en los niveles altos, mientras que la cantidad de personas no sigue una tendencia ordenada. Medir solo cuántas personas se cuida no captura la experiencia de sobrecarga.')

    # ---- 15 ----
    D.h1('Gráficos y tablas explicados')
    D.p('Cada elemento se explicó junto a su presentación. Esta sección reúne las conclusiones de los principales para facilitar la revisión.')
    D.tabla('Guía de lectura de las figuras y tablas principales.', ['Elemento', 'Qué permite concluir'], [[n, re.sub(r'\*\*|__', '', t).replace('`', '')] for n, t in D.registro], [3.0, 13.5], tam=8.5)
    D.p('**Cómo leer las medidas.** SU indica cuánta información comparten dos variables, sin dirección; p indica cuán habitual es una SU así por azar; q ajusta esa evaluación por las 33 pruebas; ρ indica si existe una tendencia ordenada y su signo; y el porcentaje de severas describe a cada categoría. Ninguna de estas medidas, por sí sola, indica causalidad.')

    # ---- 16 ----
    D.h1('Discusión')
    D.h2('Consistencia y precisión')
    D.p('El resultado metodológico principal es la estabilidad numérica de la clasificación: con 10.000 y con 50.000 permutaciones se identifican las mismas seis variables, y las diferencias son compatibles con el error de Monte Carlo. La ejecución complementaria resuelve la única duda que motivó su ejecución, la cercanía de `lugar_trabajo_comprensivo` a 0,10. Sin embargo, esta estabilidad es solo respecto del azar de las permutaciones sobre un mismo conjunto de datos.')
    D.h2('SU y Spearman son complementarias')
    D.p('Las diferencias entre ambas medidas son informativas. Fuerza supera el criterio de SU por un patrón irregular, sin una tendencia ordenada. En sentido contrario, la sobrecarga, el estrés laboral, el tabaco y otras variables muestran una tendencia ordenada, pero no superan el criterio de SU. Por eso, ninguna lista por sí sola describe bien los datos: se requieren ambas lecturas, y la clasificación descriptiva las mantiene separadas.')
    D.h2('Contraste con lo programado en la simulación')
    D.p('Como los datos son sintéticos, conviene contrastar los resultados con las relaciones programadas. Esta información se usa **solo para interpretar**: no intervino en la clasificación de las variables.')
    filas = [[n, 'Excluida por dominancia' if v == T.EXCLUIDA else nombre(v) if not n.startswith('Doble') else 'Trabaja actualmente (vía doble carga)', e, u, '—' if v == T.EXCLUIDA else 'Sí' if C.loc[v, 'relevante_50000'] else 'No', '—' if v == T.EXCLUIDA else p3(C.loc[v, 'q_50000'])] for n, v, e, u in EFECTOS]
    nt = D.tabla('Efectos directos programados en el simulador y su resultado en este análisis.', ['Efecto programado', 'Variable analizada', 'Efecto', 'Unidad', 'q<0,10', 'q SU 50.000'], filas, [4.2, 4.4, 1.1, 4.1, 1.3, 1.45], ['i', 'i', 'd', 'i', 'c', 'd'], tam=8, mantener=True)
    D.explicar(nt, 'Los efectos directos sobre los síntomas programados en `simulacion/parametros.py`, en la escala interna del generador, y lo observado en cada variable relacionada.', 'Las relaciones de IMC, días de ejercicio y lugar de trabajo coinciden con lo programado. Sin embargo, tabaco y alcohol tienen efecto programado y no superan q < 0,10, de modo que el criterio no recupera todos los efectos existentes con estos tamaños y discretizaciones. A la inversa, fuerza, bajo impacto y trabajo actual superan el criterio sin efecto directo propio, probablemente por su relación con los días de ejercicio o con la doble carga. Frutas y falta de tiempo tampoco aparecen entre los efectos directos, por lo que sus indicios deben leerse con especial cautela. La diabetes tiene un efecto programado, pero ya no se evalúa: **excluirla por baja variabilidad no significa que no se relacione con los síntomas**.')
    D.h2('Dependencia de la composición de la familia')
    D.p(f'La clasificación de `frecuencia_fuerza` y `lugar_trabajo_comprensivo` depende de qué pruebas integran la familia: con 33 pruebas, q = {p3(C.loc["lugar_trabajo_comprensivo", "q_50000"])}; con 30, q = {p3(f30["lugar_trabajo_comprensivo"])}. Esto no se contradice con su asociación con la severidad, cuya medida es idéntica. Muestra que el umbral es una convención que depende del análisis, y que estos son los dos resultados más frágiles. Días de ejercicio y bajo impacto son más robustos a este cambio.')
    D.h2('Sobre el lenguaje de riesgo y protección')
    D.p('Aunque se usen los términos «riesgo» y «protección», estos describen una compatibilidad. Las variables se midieron simultáneamente, en datos simulados, y sin ajustar por las demás. Algunas relaciones pueden ir en la dirección contraria o reflejar otra causa: quien tiene más síntomas puede hacer menos ejercicio o percibir de otro modo su trabajo, y el uso de medicamentos indica una condición de salud y no un efecto del medicamento.')

    # ---- 17 ----
    D.h1('Limitaciones')
    D.lista(['**Datos sintéticos.** Los resultados provienen de un conjunto simulado; describen lo que generó el simulador y no entregan evidencia sobre una población real.',
             '**Asociaciones no causales.** El análisis es transversal y marginal. No permite afirmar que una variable aumente o reduzca los síntomas.',
             f'**Magnitudes SU pequeñas.** La SU máxima es {p4(c["su"].max())}. Superar q < 0,10 indica una señal distinta del azar, no una asociación fuerte.',
             '**Criterio exploratorio.** q < 0,10 tolera que, en promedio, cerca de 1 de cada 10 declaradas relevantes sea un falso positivo. El umbral y la lista de variables se fijaron conociendo resultados anteriores.',
             f'**Composición de la familia.** Algunas conclusiones dependen de qué pruebas integran la familia de hipótesis: fuerza y lugar de trabajo no cumplirían el criterio con 30 candidatas (q = {p3(f30["frecuencia_fuerza"])}).',
             '**Imputación del IMC.** El 49,5 % de los valores (262 de 529) está imputado con la media. Esto reduce la variabilidad y debilita la asociación (ρ de +0,250 a +0,192).',
             '**Imputaciones de la situación laboral.** 22 valores de `trabaja_actualmente` están imputados como «Sí». Además, las 287 de la población laboral no son todas respuestas observadas (263 tienen ambas preguntas observadas). La situación laboral requiere una interpretación cuidadosa.',
             '**Relaciones programadas.** Algunas variables tienen efectos programados en la generación del conjunto sintético; otras pueden asociarse por su relación con esas variables. La asociación observada refleja en parte estas decisiones de diseño.',
             '**Spearman y SU no coinciden.** No todas las asociaciones observadas con Spearman superan el criterio ajustado de SU. Siete variables quedan solo como tendencias descriptivas.',
             '**Poblaciones específicas.** Las variables laborales describen a 287 trabajadoras y la sobrecarga a 239 cuidadoras. Sus SU no se comparan directamente con las de 529 y sus resultados no se extienden a otras participantes.',
             '**Alcance de la comparación entre ejecuciones.** Comparar 10.000 y 50.000 permutaciones evalúa precisión y consistencia numérica. **No evalúa la reproducibilidad en una población independiente.**',
             '**Pregunta de sobrecarga.** Menciona «su trabajo» y se muestra también a cuidadoras que no trabajan (99 de las 239).',
             '**SU ignora el orden.** Puede no detectar tendencias y puede responder a patrones irregulares de categorías pequeñas.',
             '**Análisis marginal.** Cada variable se evalúa por separado, sin ajustar por las demás.',
             '**Categorías pequeñas.** Varias tienen menos de 20 personas e intervalos amplios.',
             '**Pruebas descriptivas.** Kruskal-Wallis y las comparaciones por categoría no están corregidas por multiplicidad.',
             '**Exclusión por dominancia.** Retirar la diabetes aplica una regla de variabilidad. Es una decisión de método, no un hallazgo sobre su relación con la severidad, y fue tomada conociendo los resultados de la revisión de 34 variables.', '**Estabilidad de FCBF.** Esta revisión no evalúa con remuestreos la estabilidad de la selección. El orden entre fuerza y días depende de una diferencia de SU muy pequeña.'])

    # ---- 18 ----
    D.h1('Conclusiones')
    D.lista(['**Corrección.** Excluir `usa_medicamentos_diabetes` por dominancia no modifica ninguna clasificación: solo cambian levemente los q, por tratarse de una familia de 33 pruebas.', '**Consistencia.** Con 10.000 y con 50.000 permutaciones se identifican las mismas seis variables, sin cambios de clase. Las diferencias numéricas son compatibles con la precisión de Monte Carlo y no modifican las conclusiones.',
             '**Asociaciones compatibles con mayor severidad:** IMC y trabajar actualmente. La segunda requiere especial cautela.',
             '**Asociaciones compatibles con menor severidad:** días de ejercicio, ejercicio de bajo impacto y lugar de trabajo comprensivo, este último solo entre trabajadoras.',
             '**Asociación sin dirección clara:** ejercicio de fuerza. Supera el criterio, pero no se presenta como protector.',
             '**Solo tendencias descriptivas:** sobrecarga física y emocional, estrés laboral, tabaco, alcohol y falta de tiempo hacia mayor severidad; consumo de agua y de frutas hacia menor severidad.',
             '**Sobrecarga.** Tiene una asociación positiva con el MRS total, pero no supera q < 0,10 en SU. Es un indicio de riesgo, no un factor confirmado, y su pregunta presenta un problema de validez para quienes no trabajan.',
             '**Redundancia.** Se concentra en la actividad física. Que FCBF conserve fuerza no la convierte en la variable más protectora ni más importante.',
             '**Alcance.** Las asociaciones son débiles, descriptivas y provienen de datos sintéticos. No permiten afirmar causalidad.'], numerada=True)

    # ---- 19 ----
    D.h1('Implicaciones para la Fase 36')
    D.p('**Las 33 variables se conservan como conjunto inicial de la Fase 36.** Ni el criterio q < 0,10 ni FCBF eliminan variables automáticamente para la segmentación. Este informe no ejecuta la Fase 36, pero deja los siguientes aspectos identificados para considerarlos cuando corresponda:')
    D.lista(['**Actividad física.** La redundancia de días, bajo impacto y fuerza es información disponible para decidir cómo representar ese bloque. No es una decisión de retirar variables.', '**Poblaciones específicas.** Las variables laborales y de sobrecarga no se aplican a todas las participantes. Su codificación debe mantener que «no aplica» no es cero.', '**Imputaciones.** Conviene tener en cuenta la proporción de IMC imputado y las imputaciones de situación laboral, y conservar la marca de auditoría `imc_fue_imputado` fuera de las predictoras.', '**Sobrecarga.** Conviene resolver con la profesora cómo tratar la pregunta en cuidadoras que no trabajan.', '**Interpretación.** Las variables relevantes y las tendencias pueden ayudar a caracterizar los clústeres, sin presentarse como factores causales.', '**Entrada de datos.** La Fase 36 debe partir de `dataset_fase35_33_variables.csv` y de `predictores_elegibles_33.csv`. `dataset_fase35b.csv` es un producto histórico que incluye la diabetes y no debe usarse. `prevision` y `doble_carga` siguen como columnas del archivo, pero no son elegibles, y la sobrecarga se incorpora desde el conjunto limpio.'])

    # ---- Anexos ----
    D.salto()
    D.anexo('A', 'Componentes de la entropía de Shannon')
    D.p('Valores en bits, calculados en la población de cada variable. H(severidad) varía entre poblaciones porque cada una tiene otra proporción de severas.')
    t = comp.sort_index()
    filas = [[nombre(v), poblacion(f['poblacion']), str(int(f['n'])), str(int(f['k_categorias'])), p4(f['h_x']), p4(f['h_severidad']), p4(f['h_conjunta']), p5(f['informacion_mutua']), p4(f['su'])] for v, f in t.iterrows()]
    D.tabla('Componentes de Shannon de las 33 variables.', ['Variable', 'Población', 'n', 'Cat.', 'H(X)', 'H(sev.)', 'H(X, sev.)', 'I(X; sev.)', 'SU'], filas, [5.0, 1.6, 0.9, 0.8, 1.3, 1.3, 1.5, 1.6, 1.3], ['i', 'i', 'd', 'd', 'd', 'd', 'd', 'd', 'd'], tam=8)
    D.anexo('B', 'Severidad por categoría de las 33 variables')
    D.p('MRS medio con IC 95 % t, mediana con cuartiles, y porcentaje de severas con IC 95 % de Wilson. Estos valores son idénticos en ambas ejecuciones.')
    filas = [[nombre(f['variable']), categoria_legible(f['categoria']), str(int(f['n'])), f'{p1(f["mrs_medio"])} ({p1(f["mrs_ic95_inferior"])} a {p1(f["mrs_ic95_superior"])})', f'{p1(f["mrs_mediana"])} ({p1(f["mrs_q1"])}-{p1(f["mrs_q3"])})', f'{p1(f["pct_severas"])} ({p1(f["pct_ic95_inferior"])} a {p1(f["pct_ic95_superior"])})'] for _, f in cat.iterrows()]
    D.tabla('Severidad por categoría.', ['Variable', 'Categoría', 'n', 'MRS medio (IC 95 %)', 'Mediana (Q1-Q3)', '% severas (IC 95 %)'], filas, [4.6, 3.6, 0.9, 2.7, 2.1, 2.7], ['i', 'i', 'd', 'c', 'c', 'c'], tam=7.5)
    D.anexo('C', 'Trazabilidad y archivos')
    D.tabla('Ubicación de los resultados, en `analisis/reunion_2026-11-03/`.', ['Elemento', 'Ubicación'],
            [['Protocolo de la corrección', '`revision_33_variables/protocolo_revision_33.md`'], ['Corrección de la Fase 35A', '`revision_33_variables/fase35a/`; conjunto en `datos/analitico/dataset_fase35_33_variables.csv`'], ['Ejecución de 10.000', '`revision_33_variables/permutaciones_10000/`'], ['Ejecución de 50.000', '`revision_33_variables/permutaciones_50000/`'], ['Comparación entre 34 y 33', '`revision_33_variables/comparacion_34_33/`'], ['Comparación entre ejecuciones', '`revision_33_variables/informe/comparacion_10000_50000.csv`, `fcbf_10000_50000.csv`'], ['Versión histórica de 34', '`permutaciones_10000/`, `permutaciones_50000/` e `informe_integrado/informe_fase35b_integrado.docx`, sin cambios'], ['Figura corregida', '`informe_integrado/figuras/univariado_sobrecarga_fisica_emocional_corregida.png`; original sin cambios en `figuras/eda_univariado/`'], ['Programas', '`revision_33_variables.py`, `informe_word_33.py`; base: `revision_35b_reunion_1103.py`, `revision_35b_50000.py`'], ['Base del código', 'Commit `745d689`; esta corrección no tiene commit']],
            [4.0, 12.5], tam=9, mantener=True)
    D.h0('Referencias')
    for t in ['Benjamini, Y. y Hochberg, Y. (1995). Controlling the false discovery rate: a practical and powerful approach to multiple testing. __Journal of the Royal Statistical Society: Series B__, 57(1), 289-300.', 'Heinemann, K., Ruebig, A., Potthoff, P., Schneider, H. P. G., Strelow, F., Heinemann, L. A. J. y Do, M. T. (2004). The Menopause Rating Scale (MRS) scale: a methodological review. __Health and Quality of Life Outcomes__, 2, 45.', 'Phipson, B. y Smyth, G. K. (2010). Permutation P-values should never be zero: calculating exact P-values when permutations are randomly drawn. __Statistical Applications in Genetics and Molecular Biology__, 9(1), artículo 39.', 'Shannon, C. E. (1948). A mathematical theory of communication. __The Bell System Technical Journal__, 27(3), 379-423; 27(4), 623-656.', 'Yu, L. y Liu, H. (2003). Feature selection for high-dimensional data: a fast correlation-based filter solution. En __Proceedings of the 20th International Conference on Machine Learning__ (pp. 856-863).']:
        q = D.p(t, justificar=False)
        q.paragraph_format.left_indent, q.paragraph_format.first_line_indent = Cm(1), Cm(-1)
    return D


def main():
    if SALIDA.exists():
        raise FileExistsError(f'No se sobrescribe: {SALIDA}')
    vigilados = sorted({*T.archivos_vigilados(), R.CARPETA / 'informe_integrado' / 'informe_fase35b_integrado.docx'})
    antes = P.manifiesto(vigilados)
    a, b, c, previas, g34, comp, dom = cargar()
    comprobar(a, b, c, comp)
    figuras(b, c, comp)
    D = construir(a, b, c, previas, g34, comp, dom)
    D.d.save(SALIDA)
    cambiados = P.comparar_manifiestos(antes, P.manifiesto(vigilados))
    if cambiados:
        raise SystemExit('Cambiaron archivos vigilados: ' + ', '.join(cambiados))
    print(f'Guardado {SALIDA}: {len(D.d.tables)} tablas, {D.figs} figuras. Archivos vigilados sin cambios ({len(antes)}).')


if __name__ == '__main__':
    main()
