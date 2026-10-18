"""
Gráficos del análisis exploratorio (PNG para el informe en Markdown).

Paleta de referencia validada (skill dataviz): un solo azul para magnitudes,
rampa ordinal azul para la severidad del MRS y par divergente azul/rojo para
correlaciones (azul = menos síntomas, rojo = más síntomas). Marcas delgadas,
grilla tenue, textos en tinta neutra y etiquetas directas en las barras.
"""
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from . import variables as V  # noqa: E402

SUPERFICIE = '#fcfcfb'
TINTA = '#0b0b0b'
TINTA_2 = '#52514e'
TENUE = '#898781'
GRILLA = '#e1e0d9'
EJE = '#c3c2b7'
AZUL = '#2a78d6'
ROJO = '#e34948'
RAMPA_SEVERIDAD = ['#86b6ef', '#3987e5', '#1c5cab', '#0d366b']   # pasos 250/400/550/700

plt.rcParams.update({
    'figure.facecolor': SUPERFICIE, 'axes.facecolor': SUPERFICIE, 'savefig.facecolor': SUPERFICIE,
    'font.size': 10, 'text.color': TINTA, 'axes.labelcolor': TINTA_2,
    'xtick.color': TENUE, 'ytick.color': TINTA_2, 'axes.edgecolor': EJE,
    'axes.spines.top': False, 'axes.spines.right': False,
    'axes.titlesize': 12, 'axes.titleweight': 'bold', 'axes.titlelocation': 'left',
})


def _guardar(fig, ruta):
    fig.tight_layout()
    fig.savefig(ruta, dpi=150)
    plt.close(fig)


def _grilla_x(ax):
    ax.grid(axis='x', color=GRILLA, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.spines['left'].set_visible(False)
    ax.tick_params(axis='y', length=0)


def histograma_mrs(df, ruta):
    total = V.numerica(df.loc[df['mrs_completo'] == '1', 'mrs_total'])
    fig, ax = plt.subplots(figsize=(7, 3.6))
    ax.hist(total, bins=np.arange(-0.5, 45.5, 1), color=AZUL, edgecolor=SUPERFICIE, linewidth=1)
    alto = ax.get_ylim()[1] * 1.18
    ax.set_ylim(0, alto)
    for corte in (4.5, 8.5, 15.5):
        ax.axvline(corte, color=TENUE, linewidth=1, linestyle=(0, (3, 3)))
    for x, texto in ((2, 'Sin síntomas\no muy leves'), (6.5, 'Leve'), (12, 'Moderada'), (24, 'Severa')):
        ax.text(x, alto * 0.98, texto, ha='center', va='top', color=TINTA_2, fontsize=8)
    ax.set_title('Distribución del puntaje MRS total')
    ax.set_xlabel(f'Puntaje MRS (0-44) · n = {len(total)}')
    ax.set_ylabel('Participantes')
    ax.grid(axis='y', color=GRILLA, linewidth=0.8)
    ax.set_axisbelow(True)
    _guardar(fig, ruta)


def prevalencia_sintomas(perfil, ruta):
    p = perfil.sort_values('pct_moderado_o_mas')
    fig, ax = plt.subplots(figsize=(7, 4.2))
    barras = ax.barh(p['sintoma'], p['pct_moderado_o_mas'], color=AZUL, height=0.6)
    for b, v in zip(barras, p['pct_moderado_o_mas']):
        ax.text(v + 1, b.get_y() + b.get_height() / 2, f'{v:.0f} %', va='center', color=TINTA_2, fontsize=8)
    ax.set_xlim(0, max(p['pct_moderado_o_mas']) * 1.15)
    ax.set_title('Síntomas en grado moderado o mayor')
    ax.set_xlabel('% de participantes (respuesta ≥ 2 en el ítem MRS)')
    _grilla_x(ax)
    _guardar(fig, ruta)


def severidad_apilada(tabla, titulo, ruta):
    """Barras 100 % apiladas por grupo, con la rampa ordinal azul."""
    tabla = tabla.iloc[::-1]
    fig, ax = plt.subplots(figsize=(7.5, 0.55 * len(tabla) + 1.6))
    izquierda = np.zeros(len(tabla))
    etiquetas = [f'{i} (n={int(n)})' for i, n in zip(tabla.index, tabla['n'])]
    for sev, color in zip(V.ORDEN_SEVERIDAD, RAMPA_SEVERIDAD):
        valores = tabla[sev].to_numpy()
        ax.barh(etiquetas, valores, left=izquierda, color=color, edgecolor=SUPERFICIE,
                linewidth=2, height=0.6, label=sev)
        for k,(x0, v) in enumerate(zip(izquierda, valores)):
            if v >= 8:
                tinta = TINTA if color == RAMPA_SEVERIDAD[0] else 'white'
                ax.text(x0 + v / 2, k, f'{v:.0f}', ha='center', va='center', color=tinta, fontsize=8)
        izquierda += valores
    ax.set_xlim(0, 100)
    ax.set_xlabel('% de participantes')
    ax.set_title(titulo)
    ax.legend(ncol=4, loc='upper left', bbox_to_anchor=(0, -0.28 if len(tabla) < 4 else -0.18),
              frameon=False, fontsize=8)
    _grilla_x(ax)
    _guardar(fig, ruta)


def correlaciones(cruces, ruta, maximo=20):
    """
    Rho de Spearman de predictores y variables de control con asociación
    significativa (FDR < 0,05). Las de impacto quedan fuera: son consecuencias.
    """
    t = cruces[(cruces['medida'] == 'rho') & (cruces['p_ajustado'] < 0.05)
               & cruces['rol'].isin(['predictor', 'control'])]
    t = t.reindex(t['efecto'].abs().sort_values(ascending=False).index).head(maximo)
    t = t.sort_values('efecto')
    fig, ax = plt.subplots(figsize=(7.5, 0.32 * len(t) + 1.4))
    colores = [AZUL if e < 0 else ROJO for e in t['efecto']]
    nombres = [V.etiqueta(v) for v in t['variable']]
    barras = ax.barh(nombres, t['efecto'], color=colores, height=0.6)
    for b, e in zip(barras, t['efecto']):
        ax.text(e + (0.01 if e >= 0 else -0.01), b.get_y() + b.get_height() / 2, f'{e:+.2f}',
                va='center', ha='left' if e >= 0 else 'right', color=TINTA_2, fontsize=8)
    lim = max(0.1, t['efecto'].abs().max() * 1.25)
    ax.set_xlim(-lim, lim)
    ax.axvline(0, color=EJE, linewidth=1)
    ax.set_xlabel('rho de Spearman con el MRS total\nazul: menos síntomas · rojo: más síntomas')
    ax.set_title('Hábitos y condiciones asociados al MRS', loc='center')
    _grilla_x(ax)
    _guardar(fig, ruta)


def importancia(imp, titulo, eje, ruta, minimo, maximo=15):
    t = imp.head(maximo).iloc[::-1]
    fig, ax = plt.subplots(figsize=(7.5, 0.34 * len(t) + 1.4))
    colores = [AZUL if s else GRILLA for s in t['seleccionada']]
    ax.barh([V.etiqueta(v) for v in t['variable']], t['perm_media'], xerr=t['perm_de'],
            color=colores, height=0.6, error_kw={'ecolor': TENUE, 'elinewidth': 1, 'capsize': 2})
    ax.axvline(0, color=EJE, linewidth=1)
    ax.set_xlabel(f'{eje}\nazul: útil en al menos {minimo} de 5 particiones')
    ax.set_title(titulo, loc='center')
    _grilla_x(ax)
    _guardar(fig, ruta)


# --- Fase 34: EDA completo ----------------------------------------------------

def clases_severidad(conteo, ruta):
    """Barras verticales con las 4 clases de severidad (variable objetivo)."""
    fig, ax = plt.subplots(figsize=(6.5, 3.4))
    total = int(conteo.sum())
    barras = ax.bar(conteo.index, conteo.values, color=RAMPA_SEVERIDAD, width=0.6)
    for b, n in zip(barras, conteo.values):
        ax.text(b.get_x() + b.get_width() / 2, n + total * 0.01, f'{n}  ({100 * n / total:.0f} %)',
                ha='center', va='bottom', color=TINTA_2, fontsize=8)
    ax.set_ylim(0, conteo.max() * 1.15)
    ax.set_ylabel('Participantes')
    ax.set_title(f'Variable objetivo: severidad del MRS (n = {total})')
    ax.grid(axis='y', color=GRILLA, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(axis='x', length=0, labelsize=8)
    _guardar(fig, ruta)


def cajas_atipicos(df, tabla, observados, ruta, columnas=4):
    """Una caja por variable (escala propia) con los atípicos de Tukey como puntos rojos."""
    filas = int(np.ceil(len(tabla) / columnas))
    fig, ejes = plt.subplots(filas, columnas, figsize=(10, 1.55 * filas + 0.6))
    for ax, t in zip(ejes.flat, tabla.itertuples()):
        x = observados(df, t.variable)
        ax.boxplot(x, vert=False, widths=0.5, whis=1.5, patch_artist=True,
                   boxprops={'facecolor': '#cde2fb', 'edgecolor': AZUL},
                   medianprops={'color': AZUL, 'linewidth': 1.5},
                   whiskerprops={'color': EJE}, capprops={'color': EJE},
                   flierprops={'marker': 'o', 'markersize': 3.5, 'markerfacecolor': ROJO,
                               'markeredgecolor': 'none', 'alpha': 0.8})
        ax.set_yticks([])
        ax.set_title(f'{V.etiqueta(t.variable)} · {t.atipicos_bajos + t.atipicos_altos} atípicos',
                     fontsize=8.5, loc='left')
        ax.tick_params(axis='x', labelsize=7)
        ax.spines['left'].set_visible(False)
    for ax in list(ejes.flat)[len(tabla):]:
        ax.set_visible(False)
    fig.suptitle('Detección de atípicos (regla de Tukey, 1,5 × RIC): puntos rojos', x=0.01, ha='left',
                 fontweight='bold', fontsize=11)
    _guardar(fig, ruta)


def asociacion_severidad(t, ruta, titulo):
    """
    rho de Spearman de cada variable con la severidad (0-3). Color solo para las
    significativas (FDR < 0,05): azul = menos severidad, rojo = más; gris = n.s.
    """
    t = t.sort_values('efecto')
    fig, ax = plt.subplots(figsize=(7.5, 0.24 * len(t) + 1.5))
    colores = [GRILLA if p >= 0.05 else (AZUL if e < 0 else ROJO)
               for e, p in zip(t['efecto'], t['p_ajustado'])]
    barras = ax.barh([V.etiqueta(v) for v in t['variable']], t['efecto'], color=colores, height=0.65)
    for b, e, p in zip(barras, t['efecto'], t['p_ajustado']):
        if p < 0.05:
            ax.text(e + (0.008 if e >= 0 else -0.008), b.get_y() + b.get_height() / 2, f'{e:+.2f}',
                    va='center', ha='left' if e >= 0 else 'right', color=TINTA_2, fontsize=7)
    lim = max(0.1, t['efecto'].abs().max() * 1.3)
    ax.set_xlim(-lim, lim)
    ax.axvline(0, color=EJE, linewidth=1)
    ax.tick_params(axis='y', labelsize=7.5)
    ax.set_xlabel('rho de Spearman con la severidad (0-3)\n'
                  'azul: menos severidad · rojo: más severidad\ngris: no significativa (FDR ≥ 0,05)')
    ax.set_title(titulo, loc='center')
    _grilla_x(ax)
    _guardar(fig, ruta)


def mapa_calor(matriz, ruta, titulo, anotar=True):
    """Matriz de Spearman con rampa divergente azul (−1) / blanco (0) / rojo (+1)."""
    from matplotlib.colors import LinearSegmentedColormap
    mapa = LinearSegmentedColormap.from_list('divergente', [AZUL, '#ffffff', ROJO])
    n = len(matriz)
    lado = max(6, 0.36 * n + 2.5)
    fig, ax = plt.subplots(figsize=(lado + 1, lado))
    im = ax.imshow(matriz.to_numpy(dtype=float), cmap=mapa, vmin=-1, vmax=1)
    nombres = [V.etiqueta(v) for v in matriz.columns]
    ax.set_xticks(range(n), nombres, rotation=90, fontsize=7)
    ax.set_yticks(range(n), nombres, fontsize=7)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    if anotar:
        for i in range(n):
            for j in range(n):
                v = matriz.iat[i, j]
                if i != j and not np.isnan(v):
                    ax.text(j, i, f'{v:.2f}'.replace('0.', '.'), ha='center', va='center', fontsize=5.5,
                            color='white' if abs(v) > 0.6 else TINTA_2)
    fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02, label='rho de Spearman')
    ax.set_title(titulo, loc='left')
    _guardar(fig, ruta)


def direccion(df, variables, ruta, columnas=3):
    """
    Media de cada variable en cada clase de severidad (IC 95 %). Se lee la
    dirección: si la línea sube, a mayor severidad mayor valor de la variable.
    `variables` = [(variable, texto del eje y)].
    """
    mrs = df[df['mrs_completo'] == '1']
    filas = int(np.ceil(len(variables) / columnas))
    fig, ejes = plt.subplots(filas, columnas, figsize=(10, 2.4 * filas + 0.5), squeeze=False)
    cortas = ['Muy leve', 'Leve', 'Moderada', 'Severa']
    for ax, (v, unidad) in zip(ejes.flat, variables):
        x = V.codificar(mrs, [v])[v]
        g = x.groupby(mrs['mrs_severidad']).agg(['mean', 'sem']).reindex(V.ORDEN_SEVERIDAD)
        ax.errorbar(range(4), g['mean'], yerr=1.96 * g['sem'], color=AZUL, marker='o', markersize=4,
                    linewidth=1.5, capsize=3, ecolor=TENUE)
        ax.set_xticks(range(4), cortas, fontsize=7)
        ax.set_title(V.etiqueta(v), fontsize=9, loc='left')
        ax.set_ylabel(unidad, fontsize=7)
        ax.tick_params(axis='y', labelsize=7)
        ax.grid(axis='y', color=GRILLA, linewidth=0.8)
        ax.set_axisbelow(True)
    for ax in list(ejes.flat)[len(variables):]:
        ax.set_visible(False)
    fig.suptitle('Dirección de la asociación: media según la severidad (IC 95 %)', x=0.01, ha='left',
                 fontweight='bold', fontsize=11)
    _guardar(fig, ruta)


def histogramas(series, ruta, columnas=4):
    """Anexo: distribución de cada variable continua. `series` = {variable: valores}."""
    filas = int(np.ceil(len(series) / columnas))
    fig, ejes = plt.subplots(filas, columnas, figsize=(10, 1.9 * filas + 0.5))
    for ax, (c, x) in zip(ejes.flat, series.items()):
        ax.hist(x, bins=25, color=AZUL, edgecolor=SUPERFICIE, linewidth=0.6)
        ax.set_title(f'{V.etiqueta(c)} (n = {len(x)})', fontsize=8.5, loc='left')
        ax.tick_params(labelsize=7)
        ax.grid(axis='y', color=GRILLA, linewidth=0.8)
        ax.set_axisbelow(True)
    for ax in list(ejes.flat)[len(series):]:
        ax.set_visible(False)
    fig.suptitle('Distribución de las variables continuas (valores medidos)', x=0.01, ha='left',
                 fontweight='bold', fontsize=11)
    _guardar(fig, ruta)


def faltantes(tabla, ruta):
    """Anexo: % de faltantes reales por variable (sobre las filas donde aplica)."""
    t = tabla.sort_values('pct_faltante')
    fig, ax = plt.subplots(figsize=(7.5, 0.24 * len(t) + 1.3))
    barras = ax.barh([V.etiqueta(v) for v in t['variable']], t['pct_faltante'], color=AZUL, height=0.65)
    for b, p, n in zip(barras, t['pct_faltante'], t['faltantes']):
        ax.text(p + 0.2, b.get_y() + b.get_height() / 2, f'{p:.1f} % ({n})', va='center',
                color=TINTA_2, fontsize=7)
    ax.axvline(5, color=TENUE, linewidth=1, linestyle=(0, (3, 3)))
    ax.set_xlim(0, max(t['pct_faltante'].max() * 1.25, 6))
    ax.tick_params(axis='y', labelsize=7.5)
    ax.set_xlabel('% faltante sobre las filas donde la pregunta aplica (línea: 5 %, umbral de marca)')
    ax.set_title('Datos faltantes reales por variable', loc='center')
    _grilla_x(ax)
    _guardar(fig, ruta)
