"""
Fase 37D: figuras, leídas siempre de las tablas guardadas. No calcula pruebas ni ajusta modelos.

Uso, desde analisis/: python fase37/37D_caracterizacion/scripts/graficos_37d.py
"""
import sys
from pathlib import Path

sys.dont_write_bytecode = True

import matplotlib  # noqa: E402

matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

import nucleo_37d as N  # noqa: E402

B = N.BASE
R = B / 'resultados'
FIG = B / 'figuras'
FIG.mkdir(exist_ok=True)
AZUL, NARANJA, GRIS, TINTA, TINTA2, REJILLA = '#2a78d6', '#eb6834', '#8a8983', '#0b0b0b', '#52514e', '#e4e3df'
SEG = {0: '#2a78d6', 1: '#eb6834', 2: '#1baf7a', 3: '#eda100'}
RAMPA = ['#dbe8f8', '#9cc3ef', '#5c9ae3', '#2a78d6', '#1a5aa8', '#0f3e7a']
SEV = ['#dbe8f8', '#9cc3ef', '#2a78d6', '#0f3e7a']
DIVERGENTE = LinearSegmentedColormap.from_list('div', ['#1a5aa8', '#9cc3ef', '#f2f1ee', '#f6b08f', '#c4501f'])
SECUENCIAL = LinearSegmentedColormap.from_list('azul', ['#f4f8fd', '#9cc3ef', '#2a78d6', '#0f3e7a'])
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.titlesize': 10, 'axes.titleweight': 'bold', 'axes.edgecolor': '#bdbcb6', 'axes.labelcolor': TINTA2, 'xtick.color': TINTA2,
                     'ytick.color': TINTA2, 'axes.spines.top': False, 'axes.spines.right': False, 'figure.dpi': 110, 'savefig.dpi': 170, 'savefig.bbox': 'tight', 'figure.facecolor': 'white'})
COMA = FuncFormatter(lambda x, _: f'{x:g}'.replace('.', ',').replace('-', '−'))
PCT = FuncFormatter(lambda x, _: f'{x:.0f} %')
NOMBRE_SEG = {'A': 'Modelo A (PCA + K-means)', 'B1': 'B1 (regla de tres preguntas)'}


def c(x, d=2):
    return f'{x:.{d}f}'.replace('.', ',').replace('-', '−')


def csv(r):
    return pd.read_csv(R / r, encoding='utf-8')


def titulo(fig, t, sub, y=1.0):
    fig.suptitle(t, x=0.01, y=y + 0.06, ha='left', fontsize=12, fontweight='bold')
    fig.text(0.01, y + 0.015, sub, ha='left', va='top', fontsize=8.5, color=TINTA2)


def guardar(fig, nombre):
    fig.savefig(FIG / nombre)
    plt.close(fig)


def rejilla(ax, eje='x'):
    (ax.xaxis if eje == 'x' else ax.yaxis).grid(True, color=REJILLA, lw=0.7)
    ax.set_axisbelow(True)


def f01():
    num = csv('descripcion/caracteristicas_numericas.csv')
    cat = csv('descripcion/caracteristicas_categorias.csv')
    bins = num[num['tipo'] == 'binaria'].sort_values('media')
    ords = num[num['tipo'] == 'ordinal']
    fig = plt.figure(figsize=(10, 9.6))
    ax1 = fig.add_axes([0.30, 0.71, 0.62, 0.18])
    y = np.arange(len(bins))
    ax1.barh(y, 100 * bins['media'], color=AZUL, height=0.62)
    for i, r in enumerate(bins.itertuples()):
        ax1.text(100 * r.media + 1, i, f'{100 * r.media:.1f} %  (n = {r.n})'.replace('.', ','), va='center', fontsize=8, color=TINTA)
    ax1.set_yticks(y, [N.ETIQUETA[v] for v in bins['variable']])
    ax1.set_xlim(0, 100)
    ax1.xaxis.set_major_formatter(PCT)
    ax1.set_title('Preguntas de sí o no: porcentaje que responde «sí»', loc='left')
    rejilla(ax1)
    ax2 = fig.add_axes([0.30, 0.04, 0.62, 0.59])
    orden = list(ords.sort_values('bloque')['variable'])
    for i, v in enumerate(orden):
        d = cat[cat['variable'] == v].copy()
        d['k'] = pd.to_numeric(d['categoria'])
        d = d.sort_values('k')
        izq = 0
        niveles = len(d)
        paleta = [RAMPA[int(round(j * (len(RAMPA) - 1) / max(niveles - 1, 1)))] for j in range(niveles)]
        for j, r in enumerate(d.itertuples()):
            ax2.barh(i, r.pct, left=izq, color=paleta[j], height=0.7, edgecolor='white', linewidth=1)
            if r.pct >= 9:
                ax2.text(izq + r.pct / 2, i, f'{r.pct:.0f}', ha='center', va='center', fontsize=7, color='white' if j >= niveles / 2 else TINTA)
            izq += r.pct
    ax2.set_yticks(range(len(orden)), [f'{N.ETIQUETA[v]} (n = {int(ords.set_index("variable").loc[v, "n"])})' for v in orden])
    ax2.invert_yaxis()
    ax2.set_xlim(0, 100)
    ax2.xaxis.set_major_formatter(PCT)
    ax2.set_title('Preguntas ordinales: reparto de respuestas, del nivel más bajo (claro) al más alto (oscuro)', loc='left')
    ax2.spines['left'].set_visible(False)
    titulo(fig, 'Características generales de las 529 participantes sintéticas', 'Valores de la Fase 36 (observados más imputados en la limpieza). Los módulos laboral y de cuidados solo incluyen a quienes trabajan o cuidan.\nLas cifras dentro de las barras son porcentajes; los niveles de cada pregunta están en el diccionario de variables.', y=0.97)
    guardar(fig, 'f01_caracteristicas_generales.png')


def f02():
    from nucleo_37d import cargar
    D = cargar()
    fig, axs = plt.subplots(1, 3, figsize=(10, 3.0))
    for ax, v, xl in zip(axs, ['edad', 'horas_sedentarismo', 'imc'], ['Años', 'Horas al día', 'kg/m²']):
        x = D.X[v].dropna()
        ax.hist(x, bins=20 if v != 'horas_sedentarismo' else np.arange(-0.5, x.max() + 1.5, 1), color=AZUL, edgecolor='white', linewidth=0.6)
        ax.axvline(x.median(), color=NARANJA, lw=1.8)
        ax.set_title(f'{N.ETIQUETA[v]}\nn = {len(x)}; mediana {c(x.median(), 1)}', loc='left', fontsize=9)
        ax.set_xlabel(xl)
        ax.xaxis.set_major_formatter(COMA)
        rejilla(ax, 'y')
    axs[0].set_ylabel('Participantes')
    titulo(fig, 'Variables numéricas', 'La línea naranja marca la mediana. El IMC solo se muestra cuando fue observado: falta en 262 participantes y no se usa la imputación por la media.', y=1.02)
    guardar(fig, 'f02_variables_numericas.png')


def f03():
    from nucleo_37d import cargar
    D = cargar()
    t = D.M['mrs_total']
    sev = csv('descripcion/mrs_severidad.csv')
    fig, ax = plt.subplots(figsize=(9, 3.6))
    cortes = [(-0.5, 4.5), (4.5, 8.5), (8.5, 15.5), (15.5, 44.5)]
    for (a, b), col, r in zip(cortes, SEV, sev.itertuples()):
        ax.axvspan(a, b, color=col, alpha=0.35, lw=0)
        nombre = {'Sin síntomas o muy leves': 'Sin síntomas\no muy leves'}.get(r.severidad, r.severidad)
        ax.text((a + min(b, 40)) / 2, 38.5, f'{nombre}\n{r.n}\n({r.pct:.1f} %)'.replace('.', ','), ha='center', va='top', fontsize=7.5, color=TINTA)
    ax.hist(t, bins=np.arange(-0.5, 45.5, 1), color=AZUL, edgecolor='white', linewidth=0.5)
    ax.set_xlim(-0.5, 44.5)
    ax.set_ylim(0, 40)
    ax.set_xlabel('Puntaje MRS total (0 a 44)')
    ax.set_ylabel('Participantes')
    rejilla(ax, 'y')
    titulo(fig, 'Distribución del MRS total', f'Media {c(t.mean(), 1)} (DE {c(t.std(), 1)}); mediana {c(t.median(), 0)}. Las franjas son las categorías de severidad del proyecto; 16 o más puntos es «severa».', y=1.02)
    guardar(fig, 'f03_mrs_total.png')


def f04():
    from nucleo_37d import cargar
    D = cargar()
    it = csv('descripcion/mrs_items_niveles.csv')
    fig = plt.figure(figsize=(10, 7.4))
    for i, (r, nm) in enumerate([('mrs_somatico', 'Somática (ítems 1-4)'), ('mrs_psicologico', 'Psicológica (ítems 5-8)'), ('mrs_urogenital', 'Urogenital (ítems 9-11)')]):
        ax = fig.add_axes([0.06 + i * 0.32, 0.60, 0.27, 0.25])
        x = D.M[r]
        ax.hist(x, bins=np.arange(-0.5, N.MAXIMO[r] + 1.5, 1), color=AZUL, edgecolor='white', linewidth=0.5)
        ax.set_title(f'{nm}\nmedia {c(x.mean(), 1)}, mediana {c(x.median(), 0)}, máximo posible {N.MAXIMO[r]}', loc='left', fontsize=9)
        ax.set_xlabel('Puntaje')
        ax.set_ylim(0, 85)
        rejilla(ax, 'y')
        if i == 0:
            ax.set_ylabel('Participantes')
    ax = fig.add_axes([0.30, 0.05, 0.64, 0.46])
    nombres = ['Ninguna', 'Leve', 'Moderada', 'Intensa', 'Muy intensa']
    paleta = ['#eeeeea', '#9cc3ef', '#5c9ae3', '#1a5aa8', '#0f3e7a']
    for i, item in enumerate(N.ITEMS):
        d = it[it['item'] == item].sort_values('nivel')
        izq = 0
        for j, r in enumerate(d.itertuples()):
            ax.barh(i, r.pct, left=izq, color=paleta[j], height=0.7, edgecolor='white', linewidth=1)
            if r.pct >= 7:
                ax.text(izq + r.pct / 2, i, f'{r.pct:.0f}', ha='center', va='center', fontsize=7, color='white' if j >= 3 else TINTA)
            izq += r.pct
    ax.set_yticks(range(11), [f'{k}. {N.NOMBRE_ITEM[k]}' for k in N.ITEMS])
    ax.set_yticklabels([f'{k.split("_")[1]}. {N.NOMBRE_ITEM[k]}' for k in N.ITEMS])
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.xaxis.set_major_formatter(PCT)
    ax.legend(handles=[Patch(color=p, label=n) for p, n in zip(paleta, nombres)], ncol=5, loc='upper left', bbox_to_anchor=(0, -0.07), frameon=False, fontsize=8)
    ax.set_title('Intensidad declarada en cada ítem (porcentaje de las 529)', loc='left')
    ax.spines['left'].set_visible(False)
    titulo(fig, 'Dimensiones e ítems del MRS', 'Cada dimensión tiene su propia escala máxima. Los ítems siguen el orden del proyecto, no el de la publicación original.', y=0.93)
    guardar(fig, 'f04_mrs_dimensiones_items.png')


def forest(ax, d, titulo_ax):
    d = d.sort_values('efecto')
    y = np.arange(len(d))
    for i, r in enumerate(d.itertuples()):
        col = NARANJA if r.destacada else GRIS
        ax.plot([r.ic_inf, r.ic_sup], [i, i], color=col, lw=1.6, solid_capstyle='round')
        ax.plot(r.efecto, i, 'o' if r.medida == 'rho' else 's', color=col, ms=5.5, mec='white', mew=0.8)
    ax.set_yticks(y, [f'{N.ETIQUETA[v]}  (n = {n})' for v, n in zip(d['variable'], d['n'])])
    ax.axvline(0, color=TINTA2, lw=0.8)
    for x in (-0.1, 0.1):
        ax.axvline(x, color=GRIS, lw=0.7, ls=':')
    ax.xaxis.set_major_formatter(COMA)
    ax.set_title(titulo_ax, loc='left')
    rejilla(ax)


def f05():
    d = csv('individual/F1_total.csv')
    nom = d[d['medida'] == 'epsilon2']
    d = d[d['medida'] != 'epsilon2']
    fig, ax = plt.subplots(figsize=(9, 9.5))
    forest(ax, d, '')
    ax.set_xlabel('Efecto con el MRS total: ρ de Spearman (círculos) o r biserial de rangos (cuadrados), con IC bootstrap del 95 %')
    ax.legend(handles=[Line2D([], [], color=NARANJA, marker='o', lw=1.6, label='Destacada: q < 0,05 y efecto al menos pequeño'), Line2D([], [], color=GRIS, marker='o', lw=1.6, label='No destacada')],
              loc='lower right', frameon=False, fontsize=8)
    txt = '; '.join(f'{N.ETIQUETA[r.variable]} ε² = {c(r.efecto, 3)} (q = {c(r.q, 2)})' for r in nom.itertuples())
    titulo(fig, 'Características individuales frente al MRS total (familia principal F1, 36 pruebas)', f'Positivo: a mayor valor de la característica (o en quienes responden «sí»), mayor MRS.\nLas líneas punteadas marcan ±0,10, el límite de un efecto pequeño. Ninguna asociación implica causalidad; los datos son sintéticos.\nNominales (Kruskal-Wallis, efecto ε²): {txt}', y=0.95)
    guardar(fig, 'f05_asociaciones_mrs_total.png')


def f06():
    f1, f2, f3 = csv('individual/F1_total.csv'), csv('individual/F2_dimensiones.csv'), csv('individual/F3_severo.csv')
    d = pd.concat([f1, f2, f3])
    d = d[~d['variable'].isin(d.loc[d['medida'] == 'epsilon2', 'variable'])]
    cols = [('mrs_total', 'Total (F1)'), ('mrs_somatico', 'Somática (F2)'), ('mrs_psicologico', 'Psicológica (F2)'), ('mrs_urogenital', 'Urogenital (F2)'), ('severo_mrs', 'Severo ≥ 16 (F3)')]
    piv = d.pivot(index='variable', columns='resultado', values='efecto')[[k for k, _ in cols]]
    q = d.pivot(index='variable', columns='resultado', values='destacada')[[k for k, _ in cols]]
    orden = piv['mrs_total'].sort_values().index
    piv, q = piv.loc[orden], q.loc[orden]
    fig, ax = plt.subplots(figsize=(8.2, 10))
    im = ax.imshow(piv.to_numpy(), cmap=DIVERGENTE, norm=TwoSlopeNorm(0, -0.35, 0.35), aspect='auto')
    for i in range(piv.shape[0]):
        for j in range(piv.shape[1]):
            v = piv.iat[i, j]
            ax.text(j, i, c(v, 2) + (' *' if q.iat[i, j] else ''), ha='center', va='center', fontsize=7, color='white' if abs(v) > 0.25 else TINTA, fontweight='bold' if q.iat[i, j] else 'normal')
    ax.set_xticks(range(len(cols)), [n for _, n in cols])
    ax.xaxis.tick_top()
    ax.set_yticks(range(len(orden)), [N.ETIQUETA[v] for v in orden])
    for s in ax.spines.values():
        s.set_visible(False)
    cb = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    cb.set_label('ρ o r biserial de rangos (azul: menor MRS; naranja: mayor MRS)')
    cb.ax.yaxis.set_major_formatter(COMA)
    titulo(fig, 'Asociaciones con el total, las dimensiones y la severidad', '* destacada: q < 0,05 dentro de su familia (Benjamini-Hochberg) y efecto de al menos 0,10. \nEn la columna de severo, el efecto compara la característica entre quienes tienen 16 puntos o más y el resto. Se omiten las 3 nominales (ver figura 5).', y=0.95)
    guardar(fig, 'f06_mapa_dimensiones.png')


def f07():
    d = csv('individual/F4_items.csv')
    d = d[d['medida'] != 'epsilon2']
    piv = d.pivot(index='variable', columns='resultado', values='efecto')[N.ITEMS]
    q = d.pivot(index='variable', columns='resultado', values='destacada')[N.ITEMS]
    orden = csv('individual/F1_total.csv').query("medida != 'epsilon2'").sort_values('efecto')['variable']
    piv, q = piv.loc[orden], q.loc[orden]
    fig, ax = plt.subplots(figsize=(10, 10))
    im = ax.imshow(piv.to_numpy(), cmap=DIVERGENTE, norm=TwoSlopeNorm(0, -0.35, 0.35), aspect='auto')
    for i in range(piv.shape[0]):
        for j in range(piv.shape[1]):
            if q.iat[i, j]:
                ax.text(j, i, '*', ha='center', va='center', fontsize=10, color=TINTA, fontweight='bold')
    ax.set_xticks(range(11), [f'{k.split("_")[1]}. {N.NOMBRE_ITEM[k]}' for k in N.ITEMS], rotation=40, ha='left')
    ax.xaxis.tick_top()
    ax.set_yticks(range(len(orden)), [N.ETIQUETA[v] for v in orden])
    for s in ax.spines.values():
        s.set_visible(False)
    cb = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    cb.ax.yaxis.set_major_formatter(COMA)
    titulo(fig, 'Asociaciones con cada ítem del MRS (familia exploratoria F4, 396 pruebas)', '* destacada dentro de la familia F4. Es exploratoria: con tantas pruebas, algunas pueden ser casuales aun con la corrección.', y=1.08)
    guardar(fig, 'f07_mapa_items.png')


def f08():
    cor = csv('segmentos/correspondencia_A_B1.csv').set_index('A')
    res = N.leer_json(R / 'segmentos' / 'correspondencia_resumen.json')
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 3.6), gridspec_kw={'width_ratios': [1.25, 1]})
    x = np.arange(4)
    for k, (s, tam) in enumerate((('A', res['tamanos_A']), ('B1', res['tamanos_B1']))):
        b = a1.bar(x + (k - 0.5) * 0.38, tam, width=0.36, color=[SEG[g] for g in range(4)], alpha=1 if s == 'A' else 0.55, edgecolor='white')
        for xi, t in zip(x + (k - 0.5) * 0.38, tam):
            a1.text(xi, t + 3, str(t), ha='center', fontsize=8)
    a1.set_xticks(x, [f'Grupo {g}' for g in range(4)])
    a1.set_ylabel('Participantes')
    a1.legend(handles=[Patch(color=GRIS, label='A (tono pleno)'), Patch(color=GRIS, alpha=0.55, label='B1 (tono claro)')], frameon=False, fontsize=8, loc='upper left')
    a1.set_title('Tamaño de cada grupo', loc='left')
    rejilla(a1, 'y')
    t = cor.to_numpy()
    a2.imshow(t, cmap=SECUENCIAL, aspect='auto')
    for i in range(4):
        for j in range(4):
            a2.text(j, i, str(t[i, j]), ha='center', va='center', fontsize=9, color='white' if t[i, j] > 60 else TINTA)
    a2.set_xticks(range(4), [f'B1 {g}' for g in range(4)])
    a2.set_yticks(range(4), [f'A {g}' for g in range(4)])
    a2.set_title(f'Correspondencia: {c(100 * res["coincidencia_A_B1"], 1)} % coincide (ARI {c(res["ari_A_B1"], 2)})', loc='left')
    for s in a2.spines.values():
        s.set_visible(False)
    titulo(fig, 'Segmentos A y B1: tamaños y correspondencia', 'La numeración de B1 sigue la de A. Un ARI de 0,69 no es un porcentaje de aciertos. Las 529 participantes son las mismas en ambos.', y=1.04)
    guardar(fig, 'f08_tamanos_correspondencia.png')


def f09(seg='A'):
    e = csv('segmentos/F6_caracterizacion_efectos.csv').query('segmentacion == @seg')
    g = csv('segmentos/F6_caracterizacion_por_grupo.csv').query("segmentacion == @seg and categoria == 'media'")
    num = csv('descripcion/caracteristicas_numericas.csv').set_index('variable')
    e = e[e['medida'] == 'η²'].copy()
    e['grupo_tipo'] = np.where(e['usada_por_A'], 0, 1)
    e = e.sort_values(['grupo_tipo', 'efecto'], ascending=[True, False])
    filas = list(e['variable'])
    z = np.full((len(filas), 4), np.nan)
    for i, v in enumerate(filas):
        for k in range(4):
            r = g[(g['variable'] == v) & (g['grupo'] == k)]
            if len(r) and pd.notna(r['media'].iloc[0]):
                z[i, k] = (r['media'].iloc[0] - num.loc[v, 'media']) / num.loc[v, 'de']
    fig = plt.figure(figsize=(9.5, 11))
    ax = fig.add_axes([0.36, 0.04, 0.38, 0.84])
    ax.imshow(z, cmap=DIVERGENTE, norm=TwoSlopeNorm(0, -1.6, 1.6), aspect='auto')
    for i in range(len(filas)):
        for k in range(4):
            if not np.isnan(z[i, k]):
                ax.text(k, i, c(z[i, k], 1), ha='center', va='center', fontsize=6.5, color='white' if abs(z[i, k]) > 1.1 else TINTA)
            else:
                ax.text(k, i, 'sin datos', ha='center', va='center', fontsize=6, color=GRIS)
    corte = int((e['grupo_tipo'] == 0).sum())
    ax.axhline(corte - 0.5, color=TINTA, lw=1.2)
    tam = N.TAMANOS_A if seg == 'A' else N.TAMANOS_B1
    ax.set_xticks(range(4), [f'Grupo {k}\nn = {tam[k]}' for k in range(4)])
    ax.xaxis.tick_top()
    ax.set_yticks(range(len(filas)), [N.ETIQUETA[v] + ('' if v in N.EN_A else '  [externa]') for v in filas], fontsize=7.5)
    for s in ax.spines.values():
        s.set_visible(False)
    ax2 = fig.add_axes([0.77, 0.04, 0.2, 0.84], sharey=ax)
    ax2.barh(range(len(filas)), e['efecto'], color=[NARANJA if x >= 0.06 else '#9cc3ef' if x >= 0.01 else '#d9d8d3' for x in e['efecto']], height=0.7)
    for i, x in enumerate(e['efecto']):
        ax2.text(x + 0.01, i, c(x, 3), va='center', fontsize=6.5)
    ax2.axvline(0.06, color=GRIS, ls=':', lw=0.8)
    ax2.set_xlim(0, 1.0)
    ax2.tick_params(labelleft=False)
    ax2.axhline(corte - 0.5, color=TINTA, lw=1.2)
    ax2.set_title('η² entre grupos', loc='left', fontsize=9)
    ax2.xaxis.set_major_formatter(COMA)
    extra = 'Las variables de A diferencian a los grupos por construcción; no es una validación.' if seg == 'A' else 'Trabajo, pareja y días de ejercicio definen B1: sus diferencias son una consecuencia de la regla.'
    titulo(fig, f'Caracterización de los cuatro grupos de {NOMBRE_SEG[seg]}', f'Cada celda: media del grupo menos media general, en desviaciones estándar (azul: menor; naranja: mayor). Barra naranja: η² ≥ 0,06,\ndiferencia importante. {extra} Se omiten las 3 nominales (ver tablas).\nSobre la línea negra, variables usadas por A; bajo ella, externas.', y=0.95)
    guardar(fig, f'f{"09" if seg == "A" else "10"}_caracterizacion_{seg}.png')


def f11():
    e = csv('segmentos/F6_caracterizacion_efectos.csv')
    p = e.pivot(index='variable', columns='segmentacion', values='efecto')
    p = p.loc[p.max(axis=1).sort_values().index]
    fig, ax = plt.subplots(figsize=(8.5, 9.5))
    y = np.arange(len(p))
    for i, (v, r) in enumerate(p.iterrows()):
        ax.plot([r['A'], r['B1']], [i, i], color=REJILLA, lw=2)
    ax.scatter(p['A'], y, color=AZUL, s=28, zorder=3, label='A', edgecolor='white', lw=0.6)
    ax.scatter(p['B1'], y, color=NARANJA, s=28, zorder=3, label='B1', marker='D', edgecolor='white', lw=0.6)
    ax.set_yticks(y, [N.ETIQUETA[v] + ('  [A]' if v in N.EN_A else '  [externa]') for v in p.index], fontsize=7.5)
    for x, t in ((0.01, 'semejante < 0,01'), (0.06, 'importante ≥ 0,06')):
        ax.axvline(x, color=GRIS, ls=':', lw=0.8)
    ax.set_xscale('symlog', linthresh=0.01)
    ax.set_xlim(0, 1)
    ax.set_xticks([0, 0.01, 0.06, 0.14, 0.3, 0.6, 1], ['0', '0,01', '0,06', '0,14', '0,3', '0,6', '1'])
    ax.set_xlabel('Efecto entre grupos (η²; V² en nominales). Escala comprimida bajo 0,01')
    ax.legend(frameon=False, loc='lower right')
    rejilla(ax)
    titulo(fig, 'Qué tanto diferencian los grupos de A y de B1 cada característica', 'Líneas punteadas: 0,01 (bajo esto, distribución semejante) y 0,06 (diferencia importante). Comparación descriptiva: no se elige un modelo con ella.', y=0.94)
    guardar(fig, 'f11_efectos_A_B1.png')


def f12():
    from nucleo_37d import cargar
    D = cargar()
    fig, axs = plt.subplots(1, 2, figsize=(10, 4), sharey=True)
    rng = np.random.default_rng(42)
    m = csv('segmentos/F5_mrs_por_grupo.csv').query("resultado == 'mrs_total'")
    gl = csv('segmentos/F5_global.csv').query("resultado == 'mrs_total'").set_index('segmentacion')
    for ax, s in zip(axs, ('A', 'B1')):
        l = D.E[s].to_numpy()
        y = D.M['mrs_total'].to_numpy()
        for g in range(4):
            v = y[l == g]
            ax.scatter(g + rng.uniform(-0.18, 0.18, len(v)), v, s=6, color=SEG[g], alpha=0.35, lw=0)
            ax.boxplot(v, positions=[g], widths=0.5, showfliers=False, medianprops={'color': TINTA, 'lw': 1.8}, boxprops={'color': TINTA2}, whiskerprops={'color': TINTA2}, capprops={'color': TINTA2})
            r = m[(m['segmentacion'] == s) & (m['grupo'] == g)].iloc[0]
            ax.text(g, 46, f'n = {r.n}\nmediana {c(r.mediana, 1)}', ha='center', fontsize=7.5)
        ax.axhline(16, color=NARANJA, ls='--', lw=0.9)
        ax.set_xticks(range(4), [f'Grupo {g}' for g in range(4)])
        ax.set_ylim(-1, 51)
        r = gl.loc[s]
        ax.set_title(f'{NOMBRE_SEG[s]}\nε² = {c(r.efecto, 3)} [IC {c(r.ic_inf, 3)} a {c(r.ic_sup, 3)}], q = {c(r.q, 3)}', loc='left', fontsize=9)
        rejilla(ax, 'y')
    axs[0].set_ylabel('MRS total')
    titulo(fig, 'MRS total por segmento, en la misma escala', 'Cajas: mediana y cuartiles; puntos: cada participante. La línea naranja marca 16 puntos (severa). Las diferencias son pequeñas y no validan ninguna segmentación.', y=1.05)
    guardar(fig, 'f12_mrs_total_segmentos.png')


def f13():
    m = csv('segmentos/F5_mrs_por_grupo.csv')
    gl = csv('segmentos/F5_global.csv').set_index(['segmentacion', 'resultado'])
    dims = [('mrs_somatico', 'Somática', 16), ('mrs_psicologico', 'Psicológica', 16), ('mrs_urogenital', 'Urogenital', 12)]
    fig, axs = plt.subplots(1, 3, figsize=(10, 3.6))
    for ax, (r, nm, mx) in zip(axs, dims):
        for k, s in enumerate(('A', 'B1')):
            d = m[(m['segmentacion'] == s) & (m['resultado'] == r)]
            x = np.arange(4) + (k - 0.5) * 0.3
            for xi, row in zip(x, d.itertuples()):
                ax.plot([xi, xi], [row.ic_media_inf, row.ic_media_sup], color=SEG[row.grupo], lw=1.8)
                ax.plot(xi, row.media, 'o' if s == 'A' else 'D', color=SEG[row.grupo], mec='white', ms=6)
        ea, eb = gl.loc[('A', r), 'efecto'], gl.loc[('B1', r), 'efecto']
        ax.set_title(f'{nm} (0 a {mx})\nε²: A {c(ea, 3)}; B1 {c(eb, 3)}', loc='left', fontsize=9)
        ax.set_xticks(range(4), [f'G{g}' for g in range(4)])
        ax.set_ylim(0, 10)
        rejilla(ax, 'y')
    axs[0].set_ylabel('Media e IC bootstrap del 95 %')
    axs[2].legend(handles=[Line2D([], [], color=GRIS, marker='o', ls='', label='A'), Line2D([], [], color=GRIS, marker='D', ls='', label='B1')], frameon=False, loc='upper right')
    titulo(fig, 'Dimensiones del MRS por segmento', 'Misma escala vertical en los tres paneles. A la izquierda de cada grupo, A (círculo); a la derecha, B1 (rombo). G0 a G3 son los grupos 0 a 3.', y=1.06)
    guardar(fig, 'f13_dimensiones_segmentos.png')


def f14():
    s = csv('segmentos/F5_severidad_por_grupo.csv')
    gl = csv('segmentos/F5_global.csv').query("resultado == 'severidad'").set_index('segmentacion')
    fig, axs = plt.subplots(1, 2, figsize=(11, 3.4), gridspec_kw={'wspace': 0.45})
    for ax, seg in zip(axs, ('A', 'B1')):
        d = s[s['segmentacion'] == seg]
        for i, r in enumerate(d.itertuples()):
            izq = 0
            for j, cat in enumerate(N.ORDEN_SEVERIDAD):
                v = getattr(r, cat.replace(' ', '_'), None) if False else d.iloc[i][cat]
                ax.barh(i, v, left=izq, color=SEV[j], edgecolor='white', height=0.68)
                if v >= 8:
                    ax.text(izq + v / 2, i, f'{v:.0f}', ha='center', va='center', fontsize=7.5, color='white' if j >= 2 else TINTA)
                izq += v
        ax.set_yticks(range(4), [f'Grupo {g} (n = {n})' for g, n in zip(d['grupo'], d['n'])])
        ax.invert_yaxis()
        ax.set_xlim(0, 100)
        ax.xaxis.set_major_formatter(PCT)
        V = gl.loc[seg]
        ax.set_title(f'{NOMBRE_SEG[seg]}\nV = {c(V.efecto, 3)} (V² = {c(V.eta2, 3)}), q = {c(V.q, 3)}', loc='left', fontsize=9)
        ax.spines['left'].set_visible(False)
    axs[0].legend(handles=[Patch(color=SEV[j], label=n) for j, n in enumerate(N.ORDEN_SEVERIDAD)], ncol=4, frameon=False, loc='upper left', bbox_to_anchor=(0, -0.12), fontsize=8)
    titulo(fig, 'Severidad del MRS por segmento', 'Porcentaje de cada grupo en las cuatro categorías de severidad del proyecto.', y=1.07)
    guardar(fig, 'f14_severidad_segmentos.png')


def f15():
    s = csv('segmentos/sensibilidades_global.csv')
    s = s[s['sensibilidad'] == 'S-MARGEN'].copy()
    s['corte'] = s['detalle'].str.extract(r'(\d\.\d+)').astype(float)
    base = csv('segmentos/F5_global.csv').assign(corte=0.0, n_sub=529)
    s = pd.concat([base, s])
    fig, axs = plt.subplots(1, 3, figsize=(10, 3.3), sharey=True)
    for ax, (r, nm) in zip(axs, [('mrs_total', 'MRS total (ε²)'), ('mrs_psicologico', 'Psicológica (ε²)'), ('severo_mrs', 'Severo ≥ 16 (V²)')]):
        for seg, col, mk in (('A', AZUL, 'o'), ('B1', NARANJA, 'D')):
            d = s[(s['segmentacion'] == seg) & (s['resultado'] == r)].sort_values('corte')
            y = d['eta2'] if r == 'severo_mrs' else d['efecto']
            ax.plot(d['corte'], y, marker=mk, color=col, label=seg, lw=1.6)
        ns = s[(s['segmentacion'] == 'A') & (s['resultado'] == r)].sort_values('corte')
        ax.set_xticks(ns['corte'], [f'{"todas" if x == 0 else "≥ " + c(x, 2)}\nn = {n}' for x, n in zip(ns['corte'], ns['n_sub'])], fontsize=7)
        ax.axvline(0.10, color=GRIS, ls=':', lw=0.8)
        ax.axhline(0, color=TINTA2, lw=0.6)
        ax.set_title(nm, loc='left', fontsize=9)
        ax.yaxis.set_major_formatter(COMA)
        rejilla(ax, 'y')
    axs[0].set_ylabel('Efecto entre grupos')
    axs[0].legend(frameon=False)
    titulo(fig, 'Sensibilidad a las participantes cercanas a las fronteras de A', '\nSe excluye a quienes tienen margen de A menor que el corte; A y B1 se evalúan sobre el mismo subconjunto. La línea punteada es el corte principal (0,10).\nAl subir el corte, el n baja mucho: la pérdida de diferencias puede deberse en parte a menor precisión.', y=1.08)
    guardar(fig, 'f15_sensibilidad_margen.png')


def f16():
    d = csv('segmentos/asociacion_dentro_de_segmentos.csv')
    d = d[d['medida'] != 'epsilon2']
    p = d.pivot(index='variable', columns='segmentacion', values='dentro_ponderado')
    marg = d.drop_duplicates('variable').set_index('variable')['marginal']
    orden = marg.sort_values().index
    fig, ax = plt.subplots(figsize=(8.5, 9.5))
    y = np.arange(len(orden))
    ax.scatter(marg.loc[orden], y, color=TINTA, s=26, label='Sin segmentar (marginal)', zorder=3)
    ax.scatter(p.loc[orden, 'A'], y, color=AZUL, s=24, marker='o', facecolor='none', lw=1.3, label='Dentro de los grupos de A', zorder=3)
    ax.scatter(p.loc[orden, 'B1'], y, color=NARANJA, s=24, marker='D', facecolor='none', lw=1.3, label='Dentro de los grupos de B1', zorder=3)
    ax.set_yticks(y, [N.ETIQUETA[v] for v in orden], fontsize=7.5)
    ax.axvline(0, color=TINTA2, lw=0.8)
    ax.xaxis.set_major_formatter(COMA)
    ax.set_xlabel('ρ o r biserial de rangos con el MRS total (dentro: media de los grupos ponderada por n)')
    ax.legend(frameon=False, loc='lower right', fontsize=8)
    rejilla(ax)
    titulo(fig, 'Qué se pierde al resumir con segmentos', 'Si la asociación dentro de los grupos es parecida a la marginal, el segmento no la absorbe: describir solo por segmentos la perdería.\nEn binarias con un nivel casi ausente dentro de un grupo, el valor dentro es inestable (ver tabla).', y=0.94)
    guardar(fig, 'f16_asociacion_dentro_segmentos.png')


if __name__ == '__main__':
    N.instalar_gancho()
    for f in (f01, f02, f03, f04, f05, f06, f07, f08, f09, lambda: f09('B1'), f11, f12, f13, f14, f15, f16):
        f()
    N.registrar('figuras')
    print(len(list(FIG.glob('*.png'))), 'figuras')
