"""
Gráficos del análisis exploratorio (PNG para el informe en Markdown).

Paleta de referencia validada (skill dataviz): un solo azul para magnitudes,
rampa ordinal azul para la severidad del MRS y par divergente azul/rojo para
correlaciones (azul = menos síntomas, rojo = más síntomas). Marcas delgadas,
grilla tenue, textos en tinta neutra y etiquetas directas en las barras.
"""
import textwrap

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
    # Todas llevan su valor; el de las no significativas, más tenue.
    for b, e, p in zip(barras, t['efecto'], t['p_ajustado']):
        ax.text(e + (0.008 if e >= 0 else -0.008), b.get_y() + b.get_height() / 2, f'{e:+.2f}',
                va='center', ha='left' if e >= 0 else 'right', color=TINTA_2 if p < 0.05 else TENUE,
                fontsize=7)
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


def direccion(df, variables, ruta, columnas=3,
              titulo='Dirección de la asociación: media según la severidad (IC 95 %)', notas=None):
    """
    Media de cada variable en cada clase de severidad (IC 95 %). Se lee la
    dirección: si la línea sube, a mayor severidad mayor valor de la variable.
    `variables` = [(variable, texto del eje y[, límites del eje y o None])];
    `notas` = {variable: texto bajo el título}. Con límites, el eje muestra la escala
    completa de la pregunta, para no exagerar diferencias chicas.
    """
    mrs = df[df['mrs_completo'] == '1']
    notas = notas or {}
    filas = int(np.ceil(len(variables) / columnas))
    alto = 2.4 + (0.25 if notas else 0)
    fig, ejes = plt.subplots(filas, columnas, figsize=(10, alto * filas + 0.5), squeeze=False)
    cortas = ['Muy leve', 'Leve', 'Moderada', 'Severa']
    for ax, (v, unidad, *lim) in zip(ejes.flat, variables):
        lim = lim[0] if lim else None
        x = V.codificar(mrs, [v])[v]
        g = x.groupby(mrs['mrs_severidad']).agg(['mean', 'sem']).reindex(V.ORDEN_SEVERIDAD)
        ax.errorbar(range(4), g['mean'], yerr=1.96 * g['sem'], color=AZUL, marker='o', markersize=4,
                    linewidth=1.5, capsize=3, ecolor=TENUE)
        if lim is not None:
            margen = 0.05 * (lim[1] - lim[0])
            ax.set_ylim(lim[0] - margen, lim[1] + margen)
        ax.set_xticks(range(4), cortas, fontsize=7)
        ax.set_title(V.etiqueta(v), fontsize=9, loc='left', pad=14 if v in notas else 6)
        if v in notas:
            ax.text(0, 1.02, notas[v], transform=ax.transAxes, fontsize=7, color=TENUE, va='bottom')
        ax.set_ylabel(unidad, fontsize=7)
        ax.tick_params(axis='y', labelsize=7)
        ax.grid(axis='y', color=GRILLA, linewidth=0.8)
        ax.set_axisbelow(True)
    for ax in list(ejes.flat)[len(variables):]:
        ax.set_visible(False)
    fig.suptitle(titulo, x=0.01, ha='left',
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


# --- Fase 34C: conjunto de la usuaria ------------------------------------------

GRUPO_COLORES = ('#1c5cab', '#86b6ef')      # trabaja (oscuro) / no trabaja (claro)


def _corto(texto, largo=24):
    return texto if len(texto) <= largo else texto[:largo - 1] + '…'


def _barras_pareadas(ax, t, rotulo='{:.0f}'):
    """Barras horizontales: una por respuesta (filas de `t`) y grupo (columnas de `t`)."""
    t = t.iloc[::-1]
    y = np.arange(len(t))
    k = t.shape[1]
    alto = 0.8 / k
    for j, (g, color) in enumerate(zip(t.columns, GRUPO_COLORES if k > 1 else (GRUPO_COLORES[0],))):
        pos = y + (k - 1 - j - (k - 1) / 2) * alto
        ax.barh(pos, t[g], height=alto, color=color, label=g)
        for yy, v in zip(pos, t[g]):
            ax.text(v + 0.8, yy, rotulo.format(v), va='center', color=TINTA_2, fontsize=7.5)
    ax.set_yticks(y, [_corto(str(i), 40) for i in t.index], fontsize=8.5)
    ax.set_xlim(0, min(100, t.to_numpy().max() * 1.2 + 5))
    _grilla_x(ax)


def frecuencia_variable(t, ruta, titulo, nota, eje='% de participantes del grupo'):
    """
    Frecuencias de una variable: % de cada respuesta en cada grupo (columnas de `t`).
    `nota` va bajo el título (tamaños de grupo, prueba).
    """
    nota = textwrap.fill(nota, 70)
    lineas = nota.count('\n') + 1
    fig, ax = plt.subplots(figsize=(7, 0.42 * len(t) * max(1, t.shape[1] / 1.6) + 1.5 + 0.15 * lineas))
    _barras_pareadas(ax, t)
    ax.set_title(titulo, fontsize=11, pad=8 + 11 * lineas)
    ax.text(0, 1.02, nota, transform=ax.transAxes, fontsize=7.5, color=TENUE, va='bottom')
    ax.set_xlabel(eje, fontsize=8)
    if t.shape[1] > 1:
        ax.legend(loc='best', frameon=False, fontsize=8)
    _guardar(fig, ruta)


def perfil_sintomas(t, ruta):
    """% con cada síntoma MRS en grado moderado o más (≥ 2), por grupo (columnas de `t`)."""
    t = t.sort_values(t.columns[0], ascending=False)
    fig, ax = plt.subplots(figsize=(7.5, 0.55 * len(t) + 1.4))
    _barras_pareadas(ax, t)
    ax.set_title('Síntomas en grado moderado o mayor')
    ax.set_xlabel('% de participantes del grupo (respuesta ≥ 2 en el ítem MRS)', fontsize=8)
    ax.legend(loc='best', frameon=False, fontsize=8)
    _guardar(fig, ruta)


CORTAS_SEVERIDAD = ['Muy leve', 'Leve', 'Moderada', 'Severa']


def violin_severidad(mrs, datos, ruta, unidades, notas=None, columnas=3):
    """
    Violín + caja de cada variable numérica en cada clase de severidad del MRS.
    El violín es la densidad (KDE de matplotlib, recortada al mínimo y máximo
    observados) y la caja, mediana y cuartiles: se ve cómo se reparten los
    valores dentro de cada clase, no solo su media.
    `datos` = [(variable, valores observados con el índice de `mrs`)].
    """
    notas = notas or {}
    filas = int(np.ceil(len(datos) / columnas))
    fig, ejes = plt.subplots(filas, columnas, figsize=(10, 2.9 * filas + 0.7), squeeze=False)
    for ax, (v, x) in zip(ejes.flat, datos):
        sev = mrs.loc[x.index, 'mrs_severidad']
        grupos = [x[sev == s].to_numpy() for s in V.ORDEN_SEVERIDAD]
        partes = ax.violinplot(grupos, positions=range(4), widths=0.8, showextrema=False)
        for cuerpo, color in zip(partes['bodies'], RAMPA_SEVERIDAD):
            cuerpo.set_facecolor(color)
            cuerpo.set_edgecolor(color)
            cuerpo.set_alpha(0.55)
        ax.boxplot(grupos, positions=range(4), widths=0.16, showfliers=False, patch_artist=True,
                   boxprops={'facecolor': SUPERFICIE, 'edgecolor': TINTA, 'linewidth': 0.8},
                   medianprops={'color': TINTA, 'linewidth': 1.4},
                   whiskerprops={'color': TINTA, 'linewidth': 0.8}, capprops={'linewidth': 0})
        ax.set_xticks(range(4), [f'{c}\nn = {len(g)}' for c, g in zip(CORTAS_SEVERIDAD, grupos)], fontsize=7)
        ax.set_title(V.etiqueta(v), fontsize=9, loc='left', pad=14 if v in notas else 6)
        if v in notas:
            ax.text(0, 1.02, notas[v], transform=ax.transAxes, fontsize=7, color=TENUE, va='bottom')
        ax.set_ylabel(unidades.get(v, ''), fontsize=7)
        ax.tick_params(axis='y', labelsize=7)
        ax.grid(axis='y', color=GRILLA, linewidth=0.8)
        ax.set_axisbelow(True)
    for ax in list(ejes.flat)[len(datos):]:
        ax.set_visible(False)
    fig.suptitle('Variables numéricas según la severidad del MRS (violín y caja)', x=0.01, ha='left',
                 fontweight='bold', fontsize=11)
    _guardar(fig, ruta)


def severidad_por_respuesta(paneles, ruta, columnas=2):
    """
    Barras 100 % apiladas: % de cada clase de severidad dentro de cada respuesta,
    un panel por variable (hasta 8 por imagen). `paneles` = [(variable, tabla de
    `estadistica.severidad_por`, nota bajo el título)].
    """
    filas = int(np.ceil(len(paneles) / columnas))
    # Alto de cada fila según la variable con más respuestas en esa fila.
    alturas = [max(len(t) for _, t, _ in paneles[i * columnas:(i + 1) * columnas]) * 0.32 + 1.0
               for i in range(filas)]
    fig, ejes = plt.subplots(filas, columnas, figsize=(10, sum(alturas) + 0.8), squeeze=False,
                             gridspec_kw={'height_ratios': alturas})
    for ax, (v, tabla, nota) in zip(ejes.flat, paneles):
        t = tabla.iloc[::-1]
        etiquetas = ['\n'.join(textwrap.wrap(f'{i} (n={int(n)})', 26)) for i, n in zip(t.index, t['n'])]
        izquierda = np.zeros(len(t))
        for sev, color in zip(V.ORDEN_SEVERIDAD, RAMPA_SEVERIDAD):
            valores = t[sev].to_numpy()
            ax.barh(etiquetas, valores, left=izquierda, color=color, edgecolor=SUPERFICIE, linewidth=1.2,
                    height=0.7, label=sev)
            for k, (x0, p) in enumerate(zip(izquierda, valores)):
                if p >= 12:
                    tinta = TINTA if color == RAMPA_SEVERIDAD[0] else 'white'
                    ax.text(x0 + p / 2, k, f'{p:.0f}', ha='center', va='center', color=tinta, fontsize=6.5)
            izquierda += valores
        ax.set_xlim(0, 100)
        ax.tick_params(axis='y', labelsize=6.5)
        ax.tick_params(axis='x', labelsize=6.5)
        ax.set_title(V.etiqueta(v), fontsize=9, loc='left', pad=14)
        ax.text(0, 1.02, nota, transform=ax.transAxes, fontsize=7, color=TENUE, va='bottom')
        _grilla_x(ax)
    for ax in list(ejes.flat)[len(paneles):]:
        ax.set_visible(False)
    fig.suptitle('Severidad del MRS dentro de cada respuesta (variables significativas)', x=0.01, ha='left',
                 fontweight='bold', fontsize=11)
    manejadores, nombres = ejes.flat[0].get_legend_handles_labels()
    fig.legend(manejadores, nombres, ncol=4, loc='upper left', bbox_to_anchor=(0.01, 1 - 0.38 / sum(alturas)),
               frameon=False, fontsize=8)
    fig.tight_layout(rect=(0, 0, 1, 1 - 0.6 / sum(alturas)))
    fig.savefig(ruta, dpi=150)
    plt.close(fig)
