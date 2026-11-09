"""
Informe académico integrado de la revisión de la Fase 35B (reunión del 03-11-2026): versión A (10.000 permutaciones)
y versión B (50.000), con su comparación, figuras y las versiones previas identificadas como tales.

Solo lee archivos guardados: no calcula permutaciones ni modifica ningún resultado.
Uso, desde analisis/: python informe_integrado_35b.py
"""
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

import complementario_cuidados as M
import complementario_fase35b as K
import revision_35b_50000 as B
import revision_35b_reunion_1103 as R
import seleccionar_fase35b as P
from eda import variables as V
from preprocesamiento import entropia as E

CARPETA_A, CARPETA_B = R.SALIDA, B.SALIDA
SALIDA = R.CARPETA / 'informe_integrado'
Z_BONFERRONI = 3.19                # bilateral, 0,05 / 34: sección 4 de la adenda
FIGURAS = ['su_34_variables', 'q_10000_50000', 'rho_34_variables', 'severas_por_categoria', 'su_pares_relevantes']
TABLAS = ['comparacion_10000_50000', 'fcbf_10000_50000', 'versiones_previas']
GRUPOS_CLASE = ['Posible factor de riesgo', 'Indicio de riesgo (solo orden)', 'Posible factor de protección',
                'Indicio de protección (solo orden)', 'Asociación sin dirección clara', 'Sin respaldo tras la corrección']
AZUL, ROJO, GRIS, TINTA, TENUE, GRILLA, SUPERFICIE = '#2a78d6', '#e34948', '#898781', '#0b0b0b', '#52514e', '#e1e0d9', '#fcfcfb'


@dataclass(frozen=True)
class RutasInforme:
    carpeta: Path

    def csv(self, nombre):
        return self.carpeta / f'{nombre}.csv'

    def figura(self, nombre):
        return self.carpeta / 'figuras' / f'{nombre}.png'

    @property
    def informe(self):
        return self.carpeta / 'informe_fase35b_integrado.md'

    def declaradas(self):
        return {self.csv(n) for n in TABLAS} | {self.figura(n) for n in FIGURAS} | {self.informe}


# --- Comparación: sección 4 de la adenda -------------------------------------------------------------------------

def z_incrementos(k_base, k_total, n_base=B.N_BASE, n_total=B.N_TOTAL):
    """Compara los primeros sorteos con los siguientes, que son independientes y estiman el mismo p exacto."""
    k_base, k_total = np.asarray(k_base, dtype=float), np.asarray(k_total, dtype=float)
    n_resto = n_total - n_base
    p = (k_total + 1) / (n_total + 1)
    return (k_base / n_base - (k_total - k_base) / n_resto) / np.sqrt(p * (1 - p) * (1 / n_base + 1 / n_resto))


def valores_p(k, n):
    return (np.asarray(k, dtype=float) + 1) / (n + 1)


def descomponer_q(p_base, p_total):
    """Efecto propio: q con solo el p de esa variable actualizado, menos q base. Efecto del resto: lo que falta."""
    q_base, q_total = E.benjamini_hochberg(p_base), E.benjamini_hochberg(p_total)
    propio = np.empty(len(p_base))
    for i in range(len(p_base)):
        mezcla = np.array(p_base, dtype=float)
        mezcla[i] = p_total[i]
        propio[i] = E.benjamini_hochberg(mezcla)[i] - q_base[i]
    return propio, q_total - q_base - propio


def interpretar(relevante_a, relevante_b, dif_q, z):
    if abs(z) > Z_BONFERRONI:
        return 'La diferencia de p supera lo esperado por Monte Carlo: requiere revisar otra causa técnica.'
    dq = P._n(abs(dif_q), 4)
    if relevante_a != relevante_b:
        return f'Cruza q = 0,10 con una diferencia de {dq}. La SU es la misma: es precisión de Monte Carlo, no un cambio en la asociación.'
    lado = 'bajo' if relevante_a else 'sobre'
    return f'Se mantiene {lado} 0,10. Diferencia de {dq}, compatible con Monte Carlo; no es un cambio en la asociación.'


def tabla_comparacion(a, b):
    """Una fila por variable. Exige la misma SU y las mismas variables: si no, las versiones no son comparables."""
    ra, rb = a['relevancia_34'].sort_values('variable', ignore_index=True), b['relevancia_34'].sort_values('variable', ignore_index=True)
    if ra['variable'].tolist() != rb['variable'].tolist():
        raise RuntimeError('Las versiones no tienen las mismas variables.')
    if not (ra['su'] == rb['su']).all() or not (ra['n'] == rb['n']).all():
        raise RuntimeError('La SU o el tamaño difieren entre versiones.')
    pa, pb = valores_p(ra['k'], B.N_BASE), valores_p(rb['k'], B.N_TOTAL)
    for p, r in ((pa, ra), (pb, rb)):
        if np.abs(E.benjamini_hochberg(p) - r['q'].to_numpy()).max() > 1e-6:
            raise RuntimeError('Los q guardados no corresponden a una familia de 34 pruebas.')
    propio, resto = descomponer_q(pa, pb)
    z = z_incrementos(ra['k'], rb['k'])
    clases = lambda d: d['direccion_resumen'].set_index('variable')['clase']  # noqa: E731
    ca, cb = clases(a), clases(b)
    mca, mcb = (d['incertidumbre_monte_carlo'].set_index('variable') for d in (a, b))
    filas = []
    for i, f in enumerate(ra.itertuples()):
        g = rb.iloc[i]
        dif_q = g['q'] - f.q
        filas.append({'variable': f.variable, 'poblacion': f.poblacion, 'n': f.n, 'su': f.su, 'k_10000': f.k, 'p_10000': f.p, 'q_10000': f.q,
                      'relevante_10000': bool(f.q_bajo_0_10), 'k_50000': g['k'], 'p_50000': g['p'], 'q_50000': g['q'],
                      'relevante_50000': bool(g['q_bajo_0_10']), 'cambia_relevancia': bool(f.q_bajo_0_10) != bool(g['q_bajo_0_10']),
                      'q_bajo_0_05_10000': bool(f.q_bajo_0_05), 'q_bajo_0_05_50000': bool(g['q_bajo_0_05']), 'dif_p': g['p'] - f.p, 'dif_q': dif_q,
                      'dif_q_efecto_propio': propio[i], 'dif_q_efecto_resto': resto[i], 'z_incrementos': z[i],
                      'compatible_monte_carlo': bool(abs(z[i]) <= Z_BONFERRONI),
                      'q_mc_inferior_10000': mca.loc[f.variable, 'q_mc_inferior'], 'q_mc_superior_10000': mca.loc[f.variable, 'q_mc_superior'],
                      'q_mc_inferior_50000': mcb.loc[f.variable, 'q_mc_inferior'], 'q_mc_superior_50000': mcb.loc[f.variable, 'q_mc_superior'],
                      'clase_10000': ca[f.variable], 'clase_50000': cb[f.variable], 'cambia_clase': ca[f.variable] != cb[f.variable],
                      'interpretacion': interpretar(bool(f.q_bajo_0_10), bool(g['q_bajo_0_10']), dif_q, z[i])})
    return pd.DataFrame(filas)


def tabla_fcbf(a, b):
    def largo(d, nombre):
        t = d['decisiones_fcbf']
        return t[['variante', 'variable', 'etapa', 'decision', 'eliminada_por', 'su_con_severidad', 'su_par', 'q_par']].assign(version=nombre)
    t = pd.concat([largo(a, '10000'), largo(b, '50000')], ignore_index=True)
    return t.pivot(index=['variable', 'variante'], columns='version', values=['decision', 'eliminada_por', 'q_par']).pipe(_aplanar)


def _aplanar(t):
    t.columns = [f'{x}_{y}' for x, y in t.columns]
    return t.reset_index().fillna('')


def tabla_versiones_previas(previas=K.RUTAS_COMPLEMENTARIAS, cuidados=M.RUTAS_CUIDADOS):
    """Se leen sin alterarlos. Otra composición de variables: sus q no son comparables con la familia de 34."""
    filas = []
    composicion = {'previas': '30 candidatas: con doble_carga, sin sobrecarga, sin las 4 de control', 'cuidados': '31 candidatas: con doble_carga y sobrecarga, sin las 4 de control'}
    for origen, ruta, familia in (('previas', previas, 30), ('cuidados', cuidados, 31)):
        t = pd.read_csv(ruta.csv('resumen_escenarios'), encoding='utf-8-sig', keep_default_na=False)
        for f in t.to_dict('records'):
            filas.append({'version_previa': f['escenario'], 'estado': 'Oficial anterior' if f['escenario'] == 'E1' else 'Exploratoria anterior', 'composicion': composicion[origen],
                          'familia': familia, 'permutaciones': f['permutaciones'], 'umbral_q': f['umbral_q'], 'n_relevantes': f['n_relevantes'], 'relevantes': f['relevantes'],
                          'seleccionadas_adaptado': f['seleccionadas_adaptado'], 'poblacion_sobrecarga': f.get('poblacion_sobrecarga', '')})
    return pd.DataFrame(filas)


def leer_version(carpeta):
    return {n: pd.read_csv(Path(carpeta) / f'{n}.csv', encoding='utf-8-sig', keep_default_na=False,
                           na_values=[''], dtype={'cat_baja': str, 'cat_alta': str, 'eliminada_por': str, 'etapa': str})
            for n in R.ARCHIVOS_CSV}


# --- Figuras -----------------------------------------------------------------------------------------------------

def _base(alto, ancho=8.6):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family': 'sans-serif', 'font.sans-serif': ['Segoe UI', 'DejaVu Sans'], 'font.size': 9})
    fig, ax = plt.subplots(figsize=(ancho, alto), facecolor=SUPERFICIE)
    _ejes(ax)
    return fig, ax


def _ejes(ax):
    ax.set_facecolor(SUPERFICIE)
    ax.set_axisbelow(True)
    ax.tick_params(colors=TENUE, length=0)
    for lado in ('top', 'right', 'left'):
        ax.spines[lado].set_visible(False)
    ax.spines['bottom'].set_color('#c3c2b7')


def _nombre(v):
    return V.etiqueta(v)


def _coma_decimal(ax):
    from matplotlib.ticker import FuncFormatter
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f'{v:.4g}'.replace('.', ',').replace('-', '−')))


def fig_su(c, ruta):
    from matplotlib.lines import Line2D
    t = c.sort_values(['su', 'variable'], ascending=[True, True])
    fig, ax = _base(0.235 * len(t) + 1.3)
    colores = [AZUL if r else GRIS for r in t['relevante_50000']]
    ax.barh(range(len(t)), t['su'], color=colores, height=0.55)
    ax.set_yticks(range(len(t)), [f'{_nombre(f.variable)} (n = {f.n})' for f in t.itertuples()], color=TENUE, fontsize=8.5)
    ax.grid(axis='x', color=GRILLA, linewidth=0.7)
    _coma_decimal(ax)
    ax.set_xlabel('Symmetrical Uncertainty con la severidad (igual en ambas versiones)', color=TENUE)
    ax.set_title('Entropía de Shannon: SU de las 34 variables', loc='left', fontweight='bold', color=TINTA, fontsize=11)
    ax.legend(handles=[Line2D([], [], color=AZUL, lw=6, label='q < 0,10 en ambas versiones'), Line2D([], [], color=GRIS, lw=6, label='q ≥ 0,10 en ambas versiones')],
              frameon=False, loc='lower right', labelcolor=TENUE)
    fig.tight_layout()
    fig.savefig(ruta, dpi=200, facecolor=SUPERFICIE)
    return fig


def fig_q(c, ruta):
    from matplotlib.lines import Line2D
    t = c.sort_values(['q_50000', 'variable'], ascending=[False, True]).tail(12).reset_index(drop=True)
    fig, ax = _base(0.42 * len(t) + 1.4)
    for i, f in t.iterrows():
        ax.plot([f['q_mc_inferior_10000'], f['q_mc_superior_10000']], [i + 0.14, i + 0.14], color=ROJO, lw=1.6, solid_capstyle='round')
        ax.plot([f['q_mc_inferior_50000'], f['q_mc_superior_50000']], [i - 0.14, i - 0.14], color=AZUL, lw=1.6, solid_capstyle='round')
    ax.scatter(t['q_10000'], t.index + 0.14, s=34, marker='o', facecolor=SUPERFICIE, edgecolor=ROJO, linewidth=1.5, zorder=3)
    ax.scatter(t['q_50000'], t.index - 0.14, s=34, marker='D', color=AZUL, edgecolor=SUPERFICIE, linewidth=0.8, zorder=3)
    ax.axvline(0.10, color=TINTA, lw=1)
    ax.text(0.1005, len(t) - 0.42, 'q = 0,10 (criterio)', color=TINTA, fontsize=8, va='bottom')
    ax.axvline(0.05, color=GRIS, lw=0.9, ls=(0, (3, 3)))
    ax.text(0.0505, len(t) - 0.42, 'q = 0,05 (referencia)', color=TENUE, fontsize=8, va='bottom')
    ax.set_yticks(t.index, [_nombre(v) for v in t['variable']], color=TENUE)
    ax.set_ylim(-0.6, len(t) - 0.05)
    ax.grid(axis='x', color=GRILLA, linewidth=0.7)
    _coma_decimal(ax)
    ax.set_xlabel('q de Benjamini-Hochberg, con intervalo de Monte Carlo al 95 %', color=TENUE)
    ax.set_title('10.000 y 50.000 permutaciones: las 12 variables con menor q', loc='left', fontweight='bold', color=TINTA, fontsize=11, pad=14)
    ax.legend(handles=[Line2D([], [], color=ROJO, marker='o', markerfacecolor=SUPERFICIE, label='10.000 permutaciones'), Line2D([], [], color=AZUL, marker='D', label='50.000 permutaciones')],
              frameon=False, loc='upper right', bbox_to_anchor=(1, 0.93), labelcolor=TENUE)
    fig.tight_layout()
    fig.savefig(ruta, dpi=200, facecolor=SUPERFICIE)
    return fig


def fig_rho(d, c, ruta):
    from matplotlib.lines import Line2D
    q = c.set_index('variable')['q_50000']
    t = d[d['rho_mrs'].notna()].assign(q=lambda x: x['variable'].map(q)).sort_values(['rho_mrs', 'variable']).reset_index(drop=True)
    fig, ax = _base(0.235 * len(t) + 1.6)
    for i, f in t.iterrows():
        color = {'positiva': ROJO, 'negativa': AZUL}.get(f['direccion'], GRIS)
        ax.plot([f['rho_ic95_inferior'], f['rho_ic95_superior']], [i, i], color=color, lw=1.4, solid_capstyle='round')
        relevante = f['q'] < R.ALFA
        ax.scatter(f['rho_mrs'], i, s=30, color=color if relevante else SUPERFICIE, edgecolor=color, linewidth=1.3, zorder=3)
    ax.axvline(0, color='#c3c2b7', lw=1)
    ax.set_yticks(t.index, [f'{_nombre(v)} (n = {n})' for v, n in zip(t['variable'], t['n'])], color=TENUE, fontsize=8.5)
    ax.set_ylim(-0.7, len(t) - 0.3)
    ax.grid(axis='x', color=GRILLA, linewidth=0.7)
    _coma_decimal(ax)
    ax.set_xlabel('ρ de Spearman con el MRS total, IC 95 % bootstrap (orientación de las escalas: Anexo B)', color=TENUE)
    ax.set_title('Dirección de la asociación: SU no indica el signo', loc='left', fontweight='bold', color=TINTA, fontsize=11)
    ax.legend(handles=[Line2D([], [], color=ROJO, lw=2, label='Positiva: más valor, más severidad'), Line2D([], [], color=AZUL, lw=2, label='Negativa: más valor, menos severidad'),
                       Line2D([], [], color=GRIS, lw=2, label='Mixta o poco clara'), Line2D([], [], color=TENUE, lw=0, marker='o', label='q de SU < 0,10'),
                       Line2D([], [], color=TENUE, lw=0, marker='o', markerfacecolor=SUPERFICIE, label='q de SU ≥ 0,10')], frameon=False, loc='lower right', labelcolor=TENUE, fontsize=8)
    fig.tight_layout()
    fig.savefig(ruta, dpi=200, facecolor=SUPERFICIE)
    return fig


def fig_categorias(cat, c, ruta):
    import matplotlib.pyplot as plt
    variables = c[c['relevante_50000']].sort_values(['q_50000', 'variable'])['variable'].tolist()
    filas = int(np.ceil(len(variables) / 2))
    _base(1, 1)
    plt.close('all')
    fig, ejes = plt.subplots(filas, 2, figsize=(9.2, 2.75 * filas), facecolor=SUPERFICIE, sharey=True, squeeze=False)
    for ax, v in zip(ejes.ravel(), variables):
        _ejes(ax)
        t = cat[cat['variable'] == v]
        x = np.arange(len(t))
        err = [t['pct_severas'] - t['pct_ic95_inferior'], t['pct_ic95_superior'] - t['pct_severas']]
        ax.bar(x, t['pct_severas'], color=AZUL, width=0.55)
        ax.errorbar(x, t['pct_severas'], yerr=err, fmt='none', ecolor=TINTA, elinewidth=0.9)
        ax.set_xticks(x, [f'{a}\n(n = {n})' for a, n in zip(t['categoria'], t['n'])], fontsize=6.6, color=TENUE)
        ax.set_title(_nombre(v), loc='left', fontsize=9.5, fontweight='bold', color=TINTA)
        ax.grid(axis='y', color=GRILLA, linewidth=0.7)
        ax.set_ylim(0, 100)
    for ax in ejes.ravel()[len(variables):]:
        ax.axis('off')
    for fila in ejes:
        fila[0].set_ylabel('% con síntomas severos', color=TENUE, fontsize=8)
    fig.suptitle('Mujeres con síntomas severos por categoría, IC 95 % de Wilson (variables con q < 0,10)', x=0.01, ha='left', fontweight='bold', color=TINTA, fontsize=11)
    fig.tight_layout()
    fig.savefig(ruta, dpi=200, facecolor=SUPERFICIE)
    return fig


def fig_pares(pares, c, ruta):
    variables = c[c['relevante_50000']].sort_values('variable')['variable'].tolist()
    n = len(variables)
    m = np.full((n, n), np.nan)
    i = {v: k for k, v in enumerate(variables)}
    for f in pares.itertuples():
        m[i[f.variable_1], i[f.variable_2]] = m[i[f.variable_2], i[f.variable_1]] = f.su
    fig, ax = _base(0.72 * n + 1.5, 0.95 * n + 3.1)
    from matplotlib.colors import LinearSegmentedColormap
    mapa = LinearSegmentedColormap.from_list('azul', ['#f0f6fe', '#86b6ef', '#1c5cab'])
    ax.imshow(m, cmap=mapa, vmin=0, vmax=np.nanmax(m))
    for a in range(n):
        for b in range(n):
            if a != b:
                ax.text(b, a, P._n(m[a, b], 3), ha='center', va='center', fontsize=8, color='#ffffff' if m[a, b] > 0.8 * np.nanmax(m) else TINTA)
    ax.set_xticks(range(n), [_nombre(v) for v in variables], rotation=35, ha='right', color=TENUE, fontsize=8)
    ax.set_yticks(range(n), [_nombre(v) for v in variables], color=TENUE, fontsize=8)
    ax.spines['bottom'].set_visible(False)
    ax.set_title('Redundancia: SU entre las variables con q < 0,10', loc='left', fontweight='bold', color=TINTA, fontsize=11)
    fig.tight_layout()
    fig.savefig(ruta, dpi=200, facecolor=SUPERFICIE)
    return fig


# --- Informe -----------------------------------------------------------------------------------------------------

def _pv(x):
    return P._n(x, 5)


def _s(x):
    return P._n(x, 4)


def _si(x):
    return 'sí' if x else 'no'


def _vs(lista):
    return ', '.join(f'`{v}`' for v in lista) or 'ninguna'


def _ic(a, b, d=3):
    return f'{R._r(a, d)} a {R._r(b, d)}'


def _clave_tabla_factor(f, q):
    return [f'`{f.variable}`', f.mayor_valor, f.n, R._r(f.rho_mrs), _ic(f.rho_ic95_inferior, f.rho_ic95_superior),
            R._r(f.dif_pct_severas, 1) if pd.notna(f.dif_pct_severas) else '-', _pv(q[f.variable][0]), _pv(q[f.variable][1]), f.clase]


def informe(c, fcbf, previas, a, b):
    rel_a, rel_b = c[c['relevante_10000']]['variable'].tolist(), c[c['relevante_50000']]['variable'].tolist()
    orden_q = c.sort_values(['q_50000', 'variable'])
    ref_a, ref_b = c[c['q_bajo_0_05_10000']]['variable'].tolist(), c[c['q_bajo_0_05_50000']]['variable'].tolist()
    cambian_rel, cambian_clase = c[c['cambia_relevancia']]['variable'].tolist(), c[c['cambia_clase']]['variable'].tolist()
    mantienen = sorted(set(rel_a) & set(rel_b))
    cercanas_a = c[(c['q_mc_inferior_10000'] <= R.ALFA) & (c['q_mc_superior_10000'] >= R.ALFA)]['variable'].tolist()
    cercanas_b = c[(c['q_mc_inferior_50000'] <= R.ALFA) & (c['q_mc_superior_50000'] >= R.ALFA)]['variable'].tolist()
    fam = b['relevancia_34']
    dep_fam = fam[(fam['q_bajo_0_10']) & (fam['q_familia_30'] >= R.ALFA)]['variable'].tolist()
    d = b['direccion_resumen']
    q_ver = {f.variable: (f.q_10000, f.q_50000) for f in c.itertuples()}
    pa, pb = a['pares_relevantes'], b['pares_relevantes']
    pares = pa.merge(pb, on=['variable_1', 'variable_2', 'n', 'su'], suffixes=('_a', '_b'), how='outer')
    sa, sb = a['sensibilidades'], b['sensibilidades']
    adaptado = lambda t: t[(t['variante'] == 'adaptado') & (t['decision'] == 'seleccionada')]['variable'].tolist()  # noqa: E731
    estandar = lambda t: t[(t['variante'] == 'estandar') & (t['decision'] == 'seleccionada')]['variable'].tolist()  # noqa: E731
    redund = fcbf[(fcbf['variante'] == 'adaptado') & (fcbf['decision_50000'] == 'redundante')]
    de_clase = lambda clase: _vs(d[d['clase'] == clase].assign(_q=lambda x: x['variable'].map(lambda v: q_ver[v][1])).sort_values(['_q', 'variable'])['variable'])  # noqa: E731

    def tabla_version(r, mc):
        r = r.merge(mc[['variable', 'error_estandar_p', 'q_mc_inferior', 'q_mc_superior', 'prob_q_bajo_umbral']], on='variable').sort_values(['q', 'p', 'variable'])
        return K._tabla_md(['Variable', 'Población', 'n', 'SU', 'k', 'p', 'EE de p', 'q', 'IC Monte Carlo de q', 'P(q < 0,10)', 'q < 0,10', 'q < 0,05'],
                           [[f'`{f.variable}`', f.poblacion, f.n, _s(f.su), f.k, _pv(f.p), _pv(f.error_estandar_p), _pv(f.q), f'{_pv(f.q_mc_inferior)} a {_pv(f.q_mc_superior)}',
                             P._n(f.prob_q_bajo_umbral, 3), _si(f.q_bajo_0_10), _si(f.q_bajo_0_05)] for f in r.itertuples()])

    def grupo(condicion):
        t = d[condicion].assign(_q=lambda x: x['variable'].map(lambda v: q_ver[v][1])).sort_values(['_q', 'variable'])
        return (K._tabla_md(['Variable', 'Un valor mayor significa', 'n', 'ρ con MRS', 'IC 95 %', 'Dif. % severas', 'q SU 10.000', 'q SU 50.000', 'Clase'],
                            [_clave_tabla_factor(f, q_ver) for f in t.itertuples()]) if len(t) else 'Ninguna.')

    def categorias_anexo():
        t = b['direccion_categorias']
        return K._tabla_md(['Variable', 'Categoría', 'n', 'MRS medio (IC 95 %)', 'Mediana (Q1-Q3)', '% severas (IC 95 %)'],
                           [[f'`{f.variable}`', f.categoria, f.n, f'{P._n(f.mrs_medio, 1)} ({P._n(f.mrs_ic95_inferior, 1)} a {P._n(f.mrs_ic95_superior, 1)})',
                             f'{P._n(f.mrs_mediana, 1)} ({P._n(f.mrs_q1, 1)}-{P._n(f.mrs_q3, 1)})', f'{P._n(f.pct_severas, 1)} ({P._n(f.pct_ic95_inferior, 1)} a {P._n(f.pct_ic95_superior, 1)})']
                            for f in t.itertuples()])

    partes = [
        '# Fase 35B. Análisis entrópico de asociación con la severidad de los síntomas',
        f'*Informe integrado de la revisión metodológica de la reunión del 03-11-2026. Generado por `analisis/informe_integrado_35b.py` el {datetime.now():%d-%m-%Y} a partir de archivos guardados.*',
        '> **Carácter del análisis.** Los resultados son exploratorios e informativos, sobre un conjunto de datos sintético. Describen lo que generó el simulador, no evidencia sobre la población, y **ninguna asociación se interpreta como causal**. Ninguna variable se elimina: las 34 quedan como conjunto inicial de la Fase 36.',
        '## Resumen',
        f'Se evaluó la asociación de 34 variables con la severidad de los síntomas (`severo_mrs`, MRS ≥ 16) mediante la entropía de Shannon, la información mutua y la Symmetrical Uncertainty (SU), con pruebas de permutación y corrección de Benjamini-Hochberg. El análisis se hizo en dos versiones que solo difieren en el número de permutaciones: **A (10.000)** y **B (50.000)**. Con el criterio exploratorio q < 0,10, A identificó {len(rel_a)} variables y B identificó {len(rel_b)}; {"son las mismas" if set(rel_a) == set(rel_b) else "no son las mismas"}: {_vs(rel_b)}. {"Ninguna variable cambió de clasificación de relevancia ni de clase descriptiva" if not cambian_rel and not cambian_clase else "Hubo cambios de clasificación: " + _vs(sorted(set(cambian_rel) | set(cambian_clase)))}. Las diferencias entre versiones son compatibles con la precisión de Monte Carlo. Las asociaciones son débiles: la mayor SU es {P._n(c["su"].max(), 4)}.',
        '## 1. Objetivo',
        'Identificar variables asociadas con la severidad y describir la dirección de esa asociación, para distinguir posibles factores de riesgo y de protección. La fase no busca eliminar variables de forma automática. Esta revisión sigue las indicaciones de la profesora del 03-11-2026 y no reemplaza las versiones previas (sección 8).',
        '## 2. Metodología',
        '### 2.1 Variables',
        'Se analizan 34 variables: las 30 candidatas actualizadas (sin `doble_carga` y con `sobrecarga_fisica_emocional`) y las cuatro antiguas variables de control (`edad`, `imc`, `usa_medicamentos_diabetes` y `trabaja_actualmente`). `prevision` queda excluida del modelado. El conjunto de datos es `datos/analitico/dataset_fase35.csv`, sin regenerar; la sobrecarga se incorpora en memoria desde el conjunto limpio.',
        '### 2.2 Poblaciones',
        K._tabla_md(['Población', 'n', 'Variables', 'Definición'],
                    [['General', 529, 31, 'Participantes con MRS completo'], ['Laboral', 287, 2, '`lugar_trabajo_comprensivo` y `estres_entorno_laboral`: con valor en ambas preguntas'],
                     ['Cuidadoras', 239, 1, '`sobrecarga_fisica_emocional`: cuidadoras con respuesta válida observada']]),
        '### 2.3 Entropía de Shannon, información mutua y SU',
        'Con frecuencias observadas p, logaritmo en **base 2** (bits) y 0·log₂0 = 0, sin corrección de sesgo:',
        '- **Entropía de Shannon:** H(X) = −Σₓ p(x) log₂ p(x)\n- **Entropía conjunta:** H(X,Y) = −Σₓ Σᵧ p(x,y) log₂ p(x,y)\n- **Información mutua:** I(X;Y) = H(X) + H(Y) − H(X,Y)\n- **Symmetrical Uncertainty:** SU(X,Y) = 2·I(X;Y) / [H(X) + H(Y)], entre 0 y 1',
        'La implementación se verificó frente a scipy y scikit-learn, y con casos de valor conocido. El Anexo A presenta los componentes de cada variable.',
        '### 2.4 Tratamiento de los datos',
        '- **Numéricas:** para SU, `edad` usa tramos fijos, `imc` las categorías OMS y `horas_sedentarismo` sus cuartiles. Spearman usa los valores originales.\n- **Categóricas y ordinales:** SU usa sus categorías sin orden.\n- **Constantes:** si H(X) = 0 o H(Y) = 0, entonces SU = 0 y p = 1. Ocurre con `trabaja_actualmente` entre las 287.\n- **Faltantes y «no aplica»:** nunca entran como categoría ni se convierten en cero. Quien no trabaja queda fuera de las laborales, y quien no cuida o no respondió queda fuera de la sobrecarga. Las imputaciones de la Fase 34B se conservan y se declaran como limitación.\n- **Ceros con significado real:** en las frecuencias de ejercicio, 0 = no lo realiza; en `cantidad_personas_cuida`, 0 = no cuida.',
        '### 2.5 Prueba de permutación y Benjamini-Hochberg',
        'Para cada variable, `severo_mrs` se permuta entre las personas de su población. p = (1 + k) / (N + 1), donde k es el número de permutaciones con SU mayor o igual a la observada, con tolerancia numérica de 1e-12. Benjamini-Hochberg se aplica a una **única familia de 34 pruebas**, sin reutilizar valores q históricos. **Criterio exploratorio: q < 0,10.** q < 0,05 se informa solo como referencia.',
        '### 2.6 FCBF informativo',
        'Se conservan las reglas validadas por cobertura: Etapa 1 con las generales (n = 529), Etapa 2 con las laborales (n = 287) y Etapa 3 con la sobrecarga (n = 239, o 130 frente a una laboral). Una variable con menor cobertura no elimina a una con mayor cobertura. La variante adaptada exige además q del par < 0,10; la estándar, no. «Seleccionada» y «redundante» son rótulos descriptivos.',
        '### 2.7 Dirección',
        'SU mide asociación, pero **no determina si una variable es protectora o de riesgo**. Por eso se agregan Spearman con el MRS total (IC 95 % bootstrap de 2.000 remuestreos), Kruskal-Wallis, MRS y porcentaje de síntomas severos por categoría (Anexo C). La orientación de las escalas se comprobó contra el modelo de la encuesta. Dirección y clases se fijaron antes de calcular:',
        K._tabla_md(['Clase', 'Condición'], [['Posible factor de riesgo / protección', 'q de SU < 0,10 y dirección positiva / negativa'], ['Indicio de riesgo / protección (solo orden)', 'q de SU ≥ 0,10, q de Spearman < 0,10 y dirección positiva / negativa'],
                                             ['Asociación sin dirección clara', 'q de SU < 0,10 y dirección mixta o poco clara'], ['Sin respaldo tras la corrección', 'Las demás']]),
        '### 2.8 Justificación de las dos ejecuciones',
        'El valor p por permutación tiene un error de estimación que disminuye al aumentar los sorteos. Antes de ver los resultados de A se fijó una regla: recomendar 50.000 si el intervalo de Monte Carlo al 95 % de algún q contenía 0,10. Ese intervalo se obtiene con una posterior de Jeffreys para cada p y 20.000 sorteos propagados por Benjamini-Hochberg. '
        f'En A la regla se activó por {_vs(cercanas_a)}. La versión B no modifica ningún otro parámetro y **sirve para evaluar la precisión y consistencia de A, sin reemplazarla**.',
        '### 2.9 Reproducibilidad',
        'B extiende A con las mismas semillas: sus primeros 10.000 sorteos son los de A. Antes de aceptar B se comprobó que: las tablas de A se reproducen byte a byte; en las 34 variables y los pares, los primeros sorteos dan el k guardado, y el k de los primeros 10.000 más el de los 40.000 siguientes da el k total; la SU es idéntica; dos corridas de B coinciden; y A, los resultados históricos y los conjuntos de datos no cambiaron.',
        '## 3. Resultados de la versión A: 10.000 permutaciones',
        f'**q < 0,10 ({len(rel_a)}):** {_vs(c[c["relevante_10000"]].sort_values("q_10000")["variable"])}. **q < 0,05 (referencia, {len(ref_a)}):** {_vs(ref_a)}.',
        tabla_version(a['relevancia_34'], a['incertidumbre_monte_carlo']),
        f'**FCBF informativo.** Variante adaptada, no redundantes: {_vs(adaptado(a["decisiones_fcbf"]))}. Variante estándar, no redundantes: {_vs(estandar(a["decisiones_fcbf"]))}.',
        '![SU de las 34 variables](figuras/su_34_variables.png)',
        '*Figura 1. SU de las 34 variables con la severidad. La SU es igual en ambas versiones, porque no depende de las permutaciones.*',
        '**El orden por SU y el orden por q no coinciden.** La SU observada no descuenta lo que el azar produce por sí solo, y eso depende del tamaño de la población y del número de categorías. Por eso `sobrecarga_fisica_emocional` (n = 239) tiene la segunda mayor SU y no supera el criterio, mientras que `trabaja_actualmente` (binaria, n = 529) lo supera con una SU menor.',
        '## 4. Resultados de la versión B: 50.000 permutaciones',
        f'**q < 0,10 ({len(rel_b)}):** {_vs(c[c["relevante_50000"]].sort_values("q_50000")["variable"])}. **q < 0,05 (referencia, {len(ref_b)}):** {_vs(ref_b)}. **Intervalo de q que contiene 0,10:** {_vs(cercanas_b)}.',
        tabla_version(b['relevancia_34'], b['incertidumbre_monte_carlo']),
        f'**FCBF informativo.** Variante adaptada, no redundantes: {_vs(adaptado(b["decisiones_fcbf"]))}. Variante estándar, no redundantes: {_vs(estandar(b["decisiones_fcbf"]))}.',
        '## 5. Comparación de las dos versiones',
        K._tabla_md(['Variable', 'SU', 'p 10.000', 'q 10.000', 'p 50.000', 'q 50.000', '< 0,10 A', '< 0,10 B', '¿Cambia?', 'z', 'Interpretación'],
                    [[f'`{f.variable}`', _s(f.su), _pv(f.p_10000), _pv(f.q_10000), _pv(f.p_50000), _pv(f.q_50000), _si(f.relevante_10000), _si(f.relevante_50000), _si(f.cambia_relevancia), R._r(f.z_incrementos, 2), f.interpretacion]
                     for f in orden_q.itertuples()]),
        '![q en ambas versiones](figuras/q_10000_50000.png)',
        '*Figura 2. q de las 12 variables más cercanas al criterio, con su intervalo de Monte Carlo en cada versión.*',
        '### 5.1 Origen de las diferencias',
        f'- **Precisión de Monte Carlo.** Los primeros 10.000 sorteos y los 40.000 siguientes son independientes. La mayor discrepancia es |z| = {P._n(c["z_incrementos"].abs().max(), 2)} (`{c.loc[c["z_incrementos"].abs().idxmax(), "variable"]}`), y {int(c["compatible_monte_carlo"].sum())} de 34 están dentro del límite fijado de {P._n(Z_BONFERRONI, 2)}. No hay indicios de otra causa técnica.',
        f'- **Magnitud.** La mayor diferencia de p es {P._n(c["dif_p"].abs().max(), 5)} y la mayor de q es {P._n(c["dif_q"].abs().max(), 5)} (`{c.loc[c["dif_q"].abs().idxmax(), "variable"]}`). La mediana de |q₅₀.₀₀₀ − q₁₀.₀₀₀| es {P._n(c["dif_q"].abs().median(), 5)}.',
        '- **Efecto de la familia.** En Benjamini-Hochberg, q depende también de los demás valores p, porque se ordenan y se igualan por tramos. Por eso una variable puede cambiar su q aunque su propio p casi no cambie (columnas `dif_q_efecto_propio` y `dif_q_efecto_resto` de `comparacion_10000_50000.csv`).',
        '- **Asociación.** La SU, la correlación y las comparaciones por categoría son idénticas en ambas versiones. Una diferencia pequeña de q **no es un cambio en la relación entre la variable y la severidad**.',
        f'- **Referencia q < 0,05.** Pasa de {_vs(ref_a)} en A a {_vs(ref_b)} en B. Sus intervalos de Monte Carlo en B siguen cruzando 0,05, así que esto no debe leerse como un hallazgo más fuerte.' if ref_a != ref_b else '- **Referencia q < 0,05.** No cambia entre versiones.',
        '### 5.2 Asociaciones que se mantuvieron y que cambiaron',
        f'- **Se mantuvieron bajo q < 0,10:** {_vs(mantienen)}.\n- **Cambiaron de clasificación de relevancia:** {_vs(cambian_rel)}.\n- **Cambiaron de clase descriptiva:** {_vs(cambian_clase)}.',
        '### 5.3 Sensibilidades, fuera de la familia',
        K._tabla_md(['Variable', 'Versión', 'n', 'SU', 'ρ con MRS', 'p 10.000', 'q 10.000 al reemplazar', 'p 50.000', 'q 50.000 al reemplazar'],
                    [[f'`{x.variable}`', x.version, x.n, _s(x.su), R._r(x.rho_mrs), _pv(x.p), _pv(x.q_al_reemplazar), _pv(y.p), _pv(y.q_al_reemplazar)] for x, y in zip(sa.itertuples(), sb.itertuples())]),
        '## 6. Relevancia y redundancia',
        K._tabla_md(['Variable', 'Variante', 'Decisión A', 'Redundante con (A)', 'Decisión B', 'Redundante con (B)'],
                    [[f'`{f.variable}`', f.variante.replace('estandar', 'estándar'), f.decision_10000, f'`{f.eliminada_por_10000}`' if f.eliminada_por_10000 else '-', f.decision_50000, f'`{f.eliminada_por_50000}`' if f.eliminada_por_50000 else '-']
                     for f in fcbf[fcbf['decision_50000'] != 'no relevante'].sort_values(['variante', 'decision_50000', 'variable']).itertuples()]),
        '**Pares entre variables relevantes:**',
        K._tabla_md(['Variable 1', 'Variable 2', 'n', 'SU', 'q 10.000', 'q 50.000'], [[f'`{f.variable_1}`', f'`{f.variable_2}`', f.n, _s(f.su), _pv(f.q_a), _pv(f.q_b)] for f in pares.itertuples()]),
        '![Redundancia entre variables relevantes](figuras/su_pares_relevantes.png)',
        '*Figura 3. SU entre las seis variables con q < 0,10. Los pares con una variable laboral se miden con n = 287.*',
        f'**Lectura.** La redundancia se concentra en las variables de actividad física: la variante adaptada marca {_vs(redund["variable"].tolist())} como redundantes con `frecuencia_fuerza`. Esto no significa que sobren. `frecuencia_fuerza` queda por delante por una SU apenas mayor, mientras que días de ejercicio y bajo impacto muestran una dirección más clara (sección 7). La variante estándar marca además `imc` y `trabaja_actualmente`, aunque esos pares no superan el azar; por eso se prefiere leer la adaptada. Las parejas de las 34 variables están en `su_todas_las_parejas.csv`.',
        '## 7. Posibles factores de riesgo y de protección',
        'SU indica que hay asociación; el signo viene de Spearman y de las comparaciones por categoría. Ninguna de estas columnas depende del número de permutaciones, salvo q. «Dif. % severas» compara la categoría más alta con la más baja con n ≥ 10.',
        '![Dirección de la asociación](figuras/rho_34_variables.png)',
        '*Figura 4. ρ de Spearman con el MRS total. `quien_prepara_comidas` es nominal y no tiene signo.*',
        '### 7.1 Asociadas con mayor severidad',
        grupo(d['direccion'] == 'positiva'),
        '### 7.2 Asociadas con menor severidad',
        grupo(d['direccion'] == 'negativa'),
        '### 7.3 Asociaciones mixtas o poco claras',
        grupo(d['direccion'].isin(['mixta', 'poco clara']) & d['clase'].ne('Sin respaldo tras la corrección')),
        'Las demás variables mixtas o poco claras no alcanzan q < 0,10; se listan en la sección 7.4. `frecuencia_fuerza` no es monótona: quienes hacen fuerza «Rara vez» (n = 13) tienen el mayor porcentaje de severas.',
        '![Severas por categoría](figuras/severas_por_categoria.png)',
        '*Figura 5. Porcentaje de síntomas severos por categoría en las variables con q < 0,10. Las categorías con pocas personas tienen intervalos amplios.*',
        '### 7.4 Variables que no superan el criterio entrópico',
        f'En ambas versiones, {int((~c["relevante_10000"] & ~c["relevante_50000"]).sum())} variables tienen q ≥ 0,10: {_vs(c[~c["relevante_50000"]].sort_values("q_50000")["variable"])}. No alcanzar el criterio no prueba ausencia de asociación. Varias muestran una tendencia ordinal (secciones 7.1 y 7.2) que SU puede no captar, porque trata las escalas como nominales.',
        '### 7.5 Variables cuya interpretación cambia entre ejecuciones',
        (f'{_vs(cambian_clase)}.' if cambian_clase else '**Ninguna.** La clase descriptiva de las 34 variables es la misma con 10.000 y con 50.000 permutaciones.'),
        '### 7.6 Advertencias de lectura',
        '- **`lugar_trabajo_comprensivo` y la sobrecarga** describen solo a sus poblaciones (287 y 239).\n- **`trabaja_actualmente`** tiene 22 valores imputados como «sí»; su asociación puede reflejar la carga conjunta de trabajo y cuidado, y el simulador no le programa un efecto directo.\n- **`frecuencia_fuerza` y `frecuencia_bajo_impacto`** tampoco tienen efecto programado propio: el simulador programa los días de ejercicio y estas variables se relacionan con ellos.\n- **`imc`** tiene 262 de 529 valores imputados; con las 267 observadas la asociación se mantiene (sección 5.3).\n- **`usa_medicamentos_diabetes`** y otros tratamientos pueden indicar una condición de salud, no un efecto del medicamento.\n- **`falta_tiempo_influye`** tiene ρ positiva, pero el porcentaje de severas casi no difiere entre sus extremos (−0,3 puntos): su indicio es débil.\n- **`evacuacion_intestinal`** es inversa: un valor mayor significa evacuaciones menos frecuentes.\n- **Efectos del simulador:** se mencionan solo para interpretar, sin usarlos para clasificar variables. `tabaco_frecuencia` y `alcohol_frecuencia` tienen efecto programado y no superan q < 0,10, lo que muestra que este criterio no recupera todos los efectos presentes con estos tamaños y estas discretizaciones.',
        '## 8. Versiones previas',
        '**Se conservan sin cambios y corresponden a otra composición de variables**, sin las cuatro antiguas de control en la familia y con `doble_carga`. Sus q no son comparables con los de esta revisión ni se reutilizan.',
        K._tabla_md(['Versión previa', 'Estado', 'Composición', 'Familia', 'Permutaciones', 'q <', 'Relevantes', 'Seleccionadas (adaptado)'],
                    [[f.version_previa, f.estado, f.composicion, f.familia, f'{int(f.permutaciones):,}'.replace(',', '.'), P._n(f.umbral_q, 2), (f.relevantes or 'ninguna').replace(';', ', '), (f.seleccionadas_adaptado or 'ninguna').replace(';', ', ')] for f in previas.itertuples()]),
        f'**Efecto de la composición.** Con los mismos p de B, pero solo las 30 candidatas actualizadas, {_vs(dep_fam)} tendrían q ≥ 0,10 (columna `q_familia_30`). Es decir, su posición respecto del umbral depende de qué pruebas integran la familia, no solo de su asociación con la severidad. Conviene declarar esta dependencia.',
        '## 9. Limitaciones',
        '- **Datos sintéticos:** los resultados reflejan lo programado en el simulador y no evidencia poblacional.\n- **Análisis exploratorio:** la lista de variables y el umbral se fijaron conociendo resultados anteriores. q < 0,10 tolera que, en promedio, cerca de 1 de cada 10 declaradas relevantes sea un falso positivo.\n- **Asociaciones débiles:** la mayor SU es cercana a 0,02.\n- **SU ignora el orden:** puede no detectar tendencias que Spearman sí detecta.\n- **Análisis marginal:** cada variable se evalúa por separado, sin ajustar por las demás.\n- **Poblaciones distintas:** una SU con 239 o 287 personas no se compara directamente con una con 529.\n- **Imputaciones:** se conservan las de la Fase 34B. Dentro de las 287, 263 tienen ambas preguntas laborales observadas.\n- **Categorías pequeñas:** varias tienen n < 20, con intervalos amplios.\n- **Pruebas descriptivas:** Kruskal-Wallis y las comparaciones por categoría no están corregidas por multiplicidad.\n- **Pregunta de sobrecarga:** menciona «su trabajo» y se muestra también a cuidadoras que no trabajan (99 de las 239).\n- **Sin evaluación de estabilidad:** esta revisión no incluye remuestreos bootstrap de la selección.',
        '## 10. Conclusiones',
        f'1. **Consistencia.** Las versiones A y B identifican {"las mismas" if set(rel_a) == set(rel_b) else "distintas"} variables con q < 0,10, sin cambios de clase. Las diferencias son compatibles con la precisión de Monte Carlo; aumentar las permutaciones hizo más precisa la estimación sin cambiar las conclusiones.',
        f'2. **Posibles factores asociados con mayor severidad:** {de_clase("Posible factor de riesgo")}.',
        f'3. **Posibles factores asociados con menor severidad:** {de_clase("Posible factor de protección")}.',
        f'4. **Asociación sin dirección clara:** {de_clase("Asociación sin dirección clara")}.',
        f'5. **Tendencias solo ordinales, que conviene conservar a la vista:** {de_clase("Indicio de riesgo (solo orden)")} hacia mayor severidad; {de_clase("Indicio de protección (solo orden)")} hacia menor severidad.',
        '6. **Redundancia.** Se concentra en la actividad física. Por objetivo de la fase, no se usa para retirar variables.',
        '7. **Fase 36.** Las 34 variables se mantienen como conjunto inicial, sin perjuicio de los tratamientos de codificación, escalado y cobertura que correspondan.',
        '8. **Alcance.** Las asociaciones son débiles y descriptivas. No permiten afirmar causalidad.',
        '## 11. Trazabilidad',
        K._tabla_md(['Elemento', 'Ubicación'], [['Protocolo y adenda', '`reunion_2026-11-03/protocolo_revision_35b.md`, `adenda_50000_permutaciones.md`'], ['Versión A', '`reunion_2026-11-03/permutaciones_10000/`'], ['Versión B', '`reunion_2026-11-03/permutaciones_50000/`'],
                                                ['Comparación', '`reunion_2026-11-03/informe_integrado/comparacion_10000_50000.csv`, `fcbf_10000_50000.csv`, `versiones_previas.csv`'], ['Programas', '`revision_35b_reunion_1103.py`, `revision_35b_50000.py`, `informe_integrado_35b.py`'],
                                                ['Semilla', '`SeedSequence(42, spawn_key=(1103, 0, tipo, índice))`'], ['Commit de base', '`745d689`; esta revisión no tiene commit']]),
        '## Anexo A. Componentes de Shannon',
        'Bits, en la población de cada variable. H(severidad) varía porque cada población tiene otra proporción de severas.',
        K._tabla_md(['Variable', 'Población', 'n', 'Categorías', 'H(X)', 'H(severidad)', 'H(X, severidad)', 'I(X; severidad)', 'SU'],
                    [[f'`{f.variable}`', f.poblacion, f.n, f.k_categorias, _s(f.h_x), _s(f.h_severidad), _s(f.h_conjunta), P._n(f.informacion_mutua, 5), _s(f.su)] for f in b['shannon_componentes'].itertuples()]),
        '## Anexo B. Orientación de las escalas',
        K._tabla_md(['Variable', 'Tipo', 'Un valor mayor significa', 'Valores'], [[f'`{f.variable}`', f.tipo, f.mayor_valor, f.niveles if isinstance(f.niveles, str) and f.niveles else '-'] for f in b['orientacion_escalas'].itertuples()]),
        '## Anexo C. Severidad por categoría',
        categorias_anexo(),
    ]
    return '\n\n'.join(partes) + '\n'


# --- Flujo -------------------------------------------------------------------------------------------------------

def correr(rutas=RutasInforme(SALIDA), carpeta_a=CARPETA_A, carpeta_b=CARPETA_B):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    salida = P.Escritor(rutas)
    for ruta in rutas.declaradas():
        if ruta.exists():
            raise FileExistsError(f'No se sobrescribe un archivo existente: {ruta}')
    a, b = leer_version(carpeta_a), leer_version(carpeta_b)
    c, fcbf, previas = tabla_comparacion(a, b), tabla_fcbf(a, b), tabla_versiones_previas()
    texto = informe(c, fcbf, previas, a, b)
    for nombre, t in (('comparacion_10000_50000', c), ('fcbf_10000_50000', fcbf), ('versiones_previas', previas)):
        salida.tabla(rutas.csv(nombre), t)
    fig_su(c, salida.preparar(rutas.figura('su_34_variables')))
    fig_q(c, salida.preparar(rutas.figura('q_10000_50000')))
    fig_rho(b['direccion_resumen'], c, salida.preparar(rutas.figura('rho_34_variables')))
    fig_categorias(b['direccion_categorias'], c, salida.preparar(rutas.figura('severas_por_categoria')))
    fig_pares(b['pares_relevantes'], c, salida.preparar(rutas.figura('su_pares_relevantes')))
    plt.close('all')
    salida.texto(rutas.informe, texto)
    return c


def main():
    vigilados = B.archivos_vigilados() + sorted(CARPETA_B.glob('*'))
    antes = P.manifiesto(vigilados)
    c = correr()
    cambiados = P.comparar_manifiestos(antes, P.manifiesto(vigilados))
    if cambiados:
        raise SystemExit('Cambiaron archivos vigilados: ' + ', '.join(cambiados))
    print(f'Relevantes A: {int(c["relevante_10000"].sum())}; B: {int(c["relevante_50000"].sum())}; cambian: {int(c["cambia_relevancia"].sum())}. '
          f'Máximo |z| = {c["z_incrementos"].abs().max():.2f}. Archivos vigilados sin cambios ({len(antes)}).')


if __name__ == '__main__':
    main()
