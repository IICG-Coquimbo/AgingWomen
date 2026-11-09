"""
Fase 38R, fase documental: las ocho figuras con la presentación de graficos_38.py, leídas solo de los CSV ya validados de la 38R.
No busca reglas ni permuta. Escribe únicamente en documentos_definitivos/figuras y documentos_definitivos/validacion.

Uso: python -B figuras_38r.py [prefijos de las figuras por regenerar]
"""
import json
import sys
import textwrap
from pathlib import Path

sys.dont_write_bytecode = True
AQUI = Path(__file__).resolve().parent
DOC = AQUI.parent
B = DOC.parent
sys.path.insert(0, str(B / 'scripts'))
import matplotlib  # noqa: E402

matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch, Rectangle  # noqa: E402
from matplotlib.text import Text  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

import nucleo_38r as N  # noqa: E402

H = N.H
FIG = DOC / 'figuras'
FIG.mkdir(parents=True, exist_ok=True)
VAL = DOC / 'validacion'
AZUL, NARANJA, GRIS, TINTA, TINTA2, REJILLA = '#2a78d6', '#eb6834', '#8a8983', '#0b0b0b', '#52514e', '#e4e3df'
CLASE = {'2 asociación débil': ('#d3d2cd', 'Asociación débil'), '3 redundante': ('#9cc3ef', 'Redundante'),
         '4 compatible con la referencia nula': ('#eda100', 'Compatible con la referencia nula'),
         '6 asociación relativamente más marcada': ('#0f3e7a', 'Clase 6 del protocolo (no robusta)')}
LECT = {'se mantiene': '#2a78d6', 'se debilita': '#9cc3ef', 'cambia de dirección': '#c4501f', 'desaparece por falta de casos': '#eda100', 'no evaluable': '#d3d2cd'}
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.titlesize': 9, 'axes.titleweight': 'bold', 'axes.edgecolor': '#bdbcb6', 'axes.labelcolor': TINTA2,
                     'xtick.color': TINTA2, 'ytick.color': TINTA2, 'axes.spines.top': False, 'axes.spines.right': False, 'figure.dpi': 110, 'savefig.dpi': 170,
                     'savefig.bbox': 'tight', 'figure.facecolor': 'white'})
COMA = FuncFormatter(lambda x, _: f'{x:g}'.replace('.', ',').replace('-', '−'))
PCT = FuncFormatter(lambda x, _: f'{100 * x:.0f} %')
REG = {}
FILTRO = sys.argv[1:]  # sin argumentos guarda todas; con prefijos (f01 f07) solo esas. El registro se rehace siempre completo.
VERSION = ' Versión correctiva 38R.'


def c(x, d=2):
    return f'{x:.{d}f}'.replace('.', ',').replace('-', '−')


def e(x):
    return f'{int(round(x)):,}'.replace(',', '.')


def titulo(fig, t, sub, y=1.0):
    """Título y subtítulo ajustados al ancho de la figura, para que el recorte final no amplíe la imagen y encoja el texto."""
    ancho, alto = fig.get_figwidth() * 72, fig.get_figheight() * 72
    sub_l = textwrap.wrap(sub + VERSION, int(ancho / (8.5 * 0.5)))
    tit_l = textwrap.wrap(t, int(ancho / (12 * 0.6)))
    fig.text(0.01, y, chr(10).join(sub_l), ha='left', va='bottom', fontsize=8.5, color=TINTA2)
    fig.suptitle(chr(10).join(tit_l), x=0.01, y=y + (len(sub_l) * 8.5 * 1.25 + 4) / alto, ha='left', va='bottom', fontsize=12, fontweight='bold')


def extraer(fig):
    """Lo que realmente quedó dibujado, para contrastarlo después con los CSV."""
    salida = []
    for ax in fig.axes:
        barras = [[float(p.get_x()), float(p.get_y()), float(p.get_width()), float(p.get_height())] for p in ax.patches if isinstance(p, Rectangle)]
        lineas = [[[float(v) for v in np.asarray(x, dtype=float)[:4]], [float(v) for v in np.asarray(y, dtype=float)[:4]]] for x, y in (ln.get_data() for ln in ax.lines)]
        puntos = [len(col.get_offsets()) for col in ax.collections]
        salida.append({'titulo': ax.get_title() or ax.get_title(loc='left'), 'barras': barras, 'lineas': lineas, 'puntos': puntos, 'textos': [t.get_text() for t in ax.texts],
                       'ejex': ax.get_xlabel(), 'etiquetas_y': [t.get_text() for t in ax.get_yticklabels()], 'etiquetas_x': [t.get_text() for t in ax.get_xticklabels()]})
    return salida


def guardar(fig, nombre):
    REG[nombre] = extraer(fig)
    REG.setdefault('_fuente_minima', {})[nombre] = min(float(x.get_fontsize()) for x in fig.findobj(Text) if x.get_text().strip() and x.get_visible())
    if not FILTRO or any(nombre.startswith(x) for x in FILTRO):
        fig.savefig(FIG / nombre)
    plt.close(fig)


R = pd.read_csv(B / 'reglas' / 'reglas_principal.csv')
nula = pd.read_csv(B / 'referencia_nula' / 'nula_principal.csv')
meta = json.loads((B / 'reglas' / 'resumen_principal.json').read_text(encoding='utf-8'))
Sb = pd.read_csv(B / 'estabilidad' / 'submuestras.csv')
DI = pd.read_csv(B / 'preparacion' / 'diccionario_items.csv')
res = pd.read_csv(B / 'sensibilidades' / 'resumen_sensibilidades.csv')
lect = pd.read_csv(B / 'sensibilidades' / 'lectura_resumen.csv')
top = pd.read_csv(B / 'reglas' / 'reglas_no_destacadas_mayor_z.csv')
p0 = meta['frecuencia_basal_si']
nm = int(meta['marcadas'])
nr = int(meta['reglas'])

# f01 ítems
it = DI[(DI['item'] != '(sin ítem)') & DI['variable'].isin(N.PRINCIPAL)].copy()
it['orden'] = it['variable'].map({v: i for i, v in enumerate(N.PRINCIPAL)})
it = it.sort_values(['orden'], kind='stable').reset_index(drop=True)
grupos = [(v, g) for v, g in it.groupby('variable', sort=False)]
filas_grupo = np.array([len(g) + 1 for _, g in grupos])
corte = int(np.argmin(np.abs(np.cumsum(filas_grupo) - filas_grupo.sum() / 2))) + 1
filas_max = max(filas_grupo[:corte].sum(), filas_grupo[corte:].sum())
fig, axs = plt.subplots(1, 2, figsize=(7.6, 9.8), sharex=True)
fig.subplots_adjust(left=0.29, right=0.985, wspace=1.1, top=0.945, bottom=0.075)
for ax, bloque in zip(axs, (grupos[:corte], grupos[corte:])):
    y, ypos, etiquetas, valores, colores = 0, [], [], [], []
    for v, g in bloque:
        ax.text(-1.25 if ax is axs[0] else -1.12, y, N.H.ETIQUETA[v], transform=ax.get_yaxis_transform(), fontsize=6.8, fontweight='bold', color=TINTA, va='center', ha='left', zorder=6, bbox=dict(fc='white', ec='none', pad=0.5))
        y += 1
        for r in g.itertuples():
            ypos.append(y)
            etiquetas.append(H.legible(r.item).split(': ', 1)[1])
            valores.append(r.participantes)
            colores.append(NARANJA if r.regla.startswith('R2 unión') else AZUL)
            y += 1
    ax.barh(ypos, valores, color=colores, height=0.72)
    for yy, v in zip(ypos, valores):
        ax.text(v + 6, yy, str(v), va='center', fontsize=6.5, color=TINTA2)
    ax.axvline(27, color=TINTA2, lw=0.8, ls='--')
    ax.axvline(53, color=TINTA2, lw=0.8, ls=':')
    ax.set_yticks(ypos)
    ax.set_yticklabels(etiquetas, fontsize=6.5)
    ax.set_ylim(filas_max - 0.4, -0.7)
    ax.set_xlim(0, 520)
    ax.tick_params(axis='y', length=0)
    ax.tick_params(axis='x', labelsize=7)
    ax.set_xlabel('Participantes con el ítem', fontsize=7.5)
    ax.xaxis.grid(True, color=REJILLA, lw=0.7)
    ax.set_axisbelow(True)
fig.legend(handles=[Patch(color=AZUL, label='Categoría original'), Patch(color=NARANJA, label='Unión de categorías escasas (R2)'),
                    Line2D([], [], color=TINTA2, lw=0.8, ls='--', label='27 participantes (5 %)'), Line2D([], [], color=TINTA2, lw=0.8, ls=':', label='53 participantes (10 %)')],
           loc='lower center', ncol=4, frameon=False, fontsize=7, bbox_to_anchor=(0.5, 0.0))
titulo(fig, 'Figura 1. Ítems del análisis principal', f'{len(it)} ítems de {it["variable"].nunique()} variables en las 529 participantes. Cada barra es una respuesta (o grupo de respuestas).', y=0.955)
guardar(fig, 'f01_items_principal.png')

# f02 confianza frente a casos
zq = meta['nula_p95_max_z']
fig, axs = plt.subplots(1, 2, figsize=(9, 4.2))
orden = ['2 asociación débil', '3 redundante', '4 compatible con la referencia nula', '6 asociación relativamente más marcada']
for ax, cons, base, nombre in zip(axs, N.CONSECUENTES, (p0, 1 - p0), ('severo_mrs = SI', 'severo_mrs = NO')):
    sub = R[R['consecuente'] == cons]
    for k in orden:
        s = sub[sub['clase'] == k]
        ax.scatter(s['n_antecedente'], s['confianza'], s=6 if k.startswith('2') else 12, color=CLASE[k][0], lw=0, alpha=0.8 if k.startswith('2') else 1, zorder=2 + orden.index(k))
    xs = np.linspace(53, 530, 300)
    ax.plot(xs, base + zq * np.sqrt(base * (1 - base) / xs), color=TINTA, lw=1.2, zorder=6)
    ax.axhline(base, color=TINTA2, lw=0.9, ls='--')
    ax.axhline(base + H.DIF_MARCADA, color=TINTA2, lw=0.8, ls=':')
    ax.text(525, base + 0.006, f'basal {c(100 * base, 1)} %', ha='right', fontsize=7.5, color=TINTA2)
    ax.text(525, base + H.DIF_MARCADA + 0.006, 'basal + 10 puntos', ha='right', fontsize=7.5, color=TINTA2, zorder=7, bbox={'fc': 'white', 'ec': 'none', 'pad': 0.6})
    ax.set_xscale('log')
    ax.set_xticks([53, 100, 200, 300, 500])
    ax.xaxis.set_major_formatter(COMA)
    ax.yaxis.set_major_formatter(PCT)
    ax.set_xlabel('Participantes con el antecedente (n_A, escala log.)', fontsize=8)
    ax.set_ylabel(f'Confianza: % con {nombre}')
    ax.set_title(f'Reglas → {nombre} ({e(len(sub))} reglas)')
    ax.set_ylim(base - 0.02, 0.86)
    ax.yaxis.grid(True, color=REJILLA, lw=0.7)
    ax.set_axisbelow(True)
h = [Line2D([], [], marker='o', ls='', color=CLASE[k][0], label=CLASE[k][1]) for k in orden] + [Line2D([], [], color=TINTA, lw=1.2, label='Umbral de la referencia nula (p ajustado = 0,05)')]
fig.legend(handles=h, loc='lower center', ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.1))
fig.subplots_adjust(wspace=0.25)
titulo(fig, 'Figura 2. Confianza de cada regla según el número de participantes que cumple el antecedente',
       f'Solo las reglas sobre la curva negra superan lo que la búsqueda produce por azar. Las demás están dentro de lo esperable con {e(nr)} reglas.')
guardar(fig, 'f02_confianza_frente_a_casos.png')

# f03 referencia nula
fig, axs = plt.subplots(1, 2, figsize=(9, 3.7))
ax = axs[0]
ax.hist(nula['max_z'], bins=40, color='#9cc3ef')
zo = R['z'].abs().max()
ax.axvline(zo, color=NARANJA, lw=1.6)
ax.axvline(zq, color=TINTA, lw=1, ls='--')
ax.text(zo, ax.get_ylim()[1] * 0.92, f' observado\n {c(zo)}', color=NARANJA, fontsize=8, va='top')
ax.text(zq, ax.get_ylim()[1] * 0.6, f'percentil 95 nulo {c(zq)} ', color=TINTA, fontsize=8, ha='right')
ax.set_xlabel('Mayor |z| entre todas las reglas de la búsqueda', fontsize=8)
ax.xaxis.set_major_formatter(COMA)
ax.set_ylabel('Permutaciones')
ax.set_title('Regla más fuerte frente a 1.000 permutaciones')
ax = axs[1]
ax.hist(nula['reglas_marcadas'], bins=40, color='#9cc3ef')
ax.axvline(nm, color=NARANJA, lw=1.6)
ax.text(nm, ax.get_ylim()[1] * 0.92, f' observadas\n {e(nm)}', color=NARANJA, fontsize=8, va='top')
ax.axvline(nula['reglas_marcadas'].mean(), color=TINTA, lw=1, ls='--')
ax.text(nula['reglas_marcadas'].mean(), ax.get_ylim()[1] * 0.6, f'media nula {c(nula["reglas_marcadas"].mean())} ', color=TINTA, fontsize=8, ha='right')
ax.set_xlabel('Reglas marcadas (|confianza − basal| ≥ 10 puntos)', fontsize=8)
ax.set_title('Número de reglas marcadas')
for a in axs:
    a.yaxis.grid(True, color=REJILLA, lw=0.7)
    a.set_axisbelow(True)
fig.subplots_adjust(wspace=0.3)
titulo(fig, 'Figura 3. Referencia nula: lo que aparece al romper la relación con la severidad',
       'En cada permutación se repite la búsqueda completa con el consecuente mezclado al azar. Un exceso global de reglas marcadas no hace significativa ninguna regla individual.')
guardar(fig, 'f03_referencia_nula.png')

# f04 estabilidad
M = R[R['marcada']]
fig, axs = plt.subplots(1, 2, figsize=(9, 3.7))
ax = axs[0]
bins = np.linspace(0, 1, 21)
for k in ['3 redundante', '4 compatible con la referencia nula']:
    s = M[M['clase'] == k]['reaparece_marcada']
    ax.hist(s, bins=bins, histtype='step', lw=1.6, color=CLASE[k][0], label=f'{CLASE[k][1]} ({len(s)})')
for r in M[M['clase'].str.startswith('6')].itertuples():
    ax.axvline(r.reaparece_marcada, color=CLASE['6 asociación relativamente más marcada'][0], lw=1.6, label='Clase 6 del protocolo (1, no robusta)')
ax.axvline(H.ESTABLE_REAP, color=TINTA2, lw=0.9, ls=':')
ax.text(H.ESTABLE_REAP, ax.get_ylim()[1] * 0.97, ' criterio\n 70 %', fontsize=7.5, color=TINTA2, va='top')
ax.xaxis.set_major_formatter(PCT)
ax.set_xlabel('Submuestras en que la regla reaparece marcada')
ax.set_ylabel('Reglas marcadas')
ax.set_title(f'Reaparición de las {e(nm)} reglas marcadas')
ax.legend(frameon=False, fontsize=7.5, loc='upper center', bbox_to_anchor=(0.5, -0.2), ncol=1)
ax = axs[1]
ax.hist(Sb['nuevas'], bins=30, color='#eda100', alpha=0.8, label='Nuevas (marcadas solo en la submuestra)')
ax.hist(Sb['desaparecidas'], bins=30, color='#2a78d6', alpha=0.7, label='Desaparecidas (marcadas solo en las 529)')
ax.set_xlabel('Reglas por submuestra')
ax.set_ylabel('Submuestras')
ax.set_title('Reglas nuevas y desaparecidas por submuestra')
ax.legend(frameon=False, fontsize=7.5, loc='upper center', bbox_to_anchor=(0.5, -0.2), ncol=1)
for a in axs:
    a.yaxis.grid(True, color=REJILLA, lw=0.7)
    a.set_axisbelow(True)
fig.subplots_adjust(wspace=0.3)
titulo(fig, 'Figura 4. Estabilidad en 200 submuestras del 80 %',
       'Las reglas compatibles con el azar también reaparecen a menudo: las submuestras comparten la mayor parte de los datos. Estabilidad no es validez.')
guardar(fig, 'f04_estabilidad.png')

# f05 exceso frente a la nula por configuración
filas = [{'configuracion': 'principal', 'marcadas': nm, 'arch': B / 'referencia_nula' / 'nula_principal.csv', 'n': 529}] + \
        [{'configuracion': r.configuracion, 'marcadas': r.marcadas, 'arch': B / 'sensibilidades' / 'nula' / f'nula_{r.configuracion}.csv', 'n': r.n} for r in res.itertuples()]
fig, ax = plt.subplots(figsize=(9, 5.6))
for i, f in enumerate(filas):
    nl = pd.read_csv(f['arch'])['reglas_marcadas']
    m = nl.mean()
    lo, hi = np.percentile(nl, [5, 95]) / m
    ax.plot([lo, hi], [i, i], color='#9cc3ef', lw=5, solid_capstyle='round')
    ax.plot(1, i, '|', color=TINTA2, ms=10)
    ax.plot(f['marcadas'] / m, i, 'o', color=NARANJA, ms=6)
    ax.text(max(hi, f['marcadas'] / m) + 0.04, i, f"{e(f['marcadas'])} frente a {e(m)}", va='center', fontsize=7.5, color=TINTA2)
ax.set_yticks(range(len(filas)))
ax.set_yticklabels([f"{f['configuracion']} (n = {f['n']})" for f in filas])
ax.invert_yaxis()
ax.xaxis.set_major_formatter(COMA)
ax.set_xlabel('Reglas marcadas observadas ÷ media bajo la referencia nula')
ax.set_xlim(0, 3.3)
ax.xaxis.grid(True, color=REJILLA, lw=0.7)
ax.set_axisbelow(True)
ax.legend(handles=[Line2D([], [], marker='o', ls='', color=NARANJA, label='Observado'), Line2D([], [], color='#9cc3ef', lw=5, label='Nula: percentiles 5 a 95')],
          frameon=False, loc='lower right')
titulo(fig, 'Figura 5. Exceso de reglas marcadas sobre el azar, por configuración',
       'Un valor de 1 es lo esperado sin ninguna relación. Un exceso indica una señal difusa, no reglas puntuales: no hace significativa ninguna regla individual.')
guardar(fig, 'f05_exceso_frente_a_nula.png')

# f06 lectura de las reglas marcadas de la principal
L = lect.set_index('configuracion')
cats = ['se mantiene', 'se debilita', 'cambia de dirección', 'desaparece por falta de casos', 'no evaluable']
L = L.reindex(columns=cats, fill_value=0)
fig, ax = plt.subplots(figsize=(9, 5))
izq = np.zeros(len(L))
for k in cats:
    ax.barh(range(len(L)), L[k], left=izq, color=LECT[k], label=k[0].upper() + k[1:], height=0.7, edgecolor='white', lw=0.8)
    izq += L[k].to_numpy()
ax.set_yticks(range(len(L)))
ax.set_yticklabels(L.index)
ax.invert_yaxis()
ax.set_xlabel(f'Reglas marcadas de la principal ({e(nm)})')
ax.legend(frameon=False, ncol=3, loc='lower center', bbox_to_anchor=(0.45, -0.3), fontsize=8)
titulo(fig, f'Figura 6. Qué ocurre con las {e(nm)} reglas marcadas de la principal en cada sensibilidad',
       '«No evaluable»: la regla usa una variable excluida, un ítem distinto o más condiciones de las permitidas. Las sensibilidades no sustituyen al análisis principal.')
guardar(fig, 'f06_lectura_sensibilidades.png')

# f07 reglas con mayor |z|
fig, axs = plt.subplots(2, 1, figsize=(7.6, 9.6))
fig.subplots_adjust(left=0.395, right=0.975, top=0.93, bottom=0.085, hspace=0.3)
for ax, cons, base, nombre in zip(axs, N.CONSECUENTES, (p0, 1 - p0), ('severos (MRS ≥ 16)', 'no severos (MRS < 16)')):
    s = top[top['consecuente'] == cons].reset_index(drop=True)
    for i, r in s.iterrows():
        col = CLASE[r['clase']][0]
        ax.plot([r['ic_confianza_inf'], r['ic_confianza_sup']], [i, i], color=col, lw=2)
        ax.plot(r['confianza'], i, 'o', color=col, ms=6)
        ax.text(0.995, i, f"n_A = {r['n_antecedente']}", va='center', ha='right', fontsize=7, color=TINTA2, transform=ax.get_yaxis_transform())
    ax.axvline(base, color=TINTA2, ls='--', lw=0.9)
    ax.set_yticks(range(len(s)))
    ax.set_yticklabels(['\n'.join(textwrap.wrap(H.legible_regla(a), 52)) for a in s['antecedente']], fontsize=6.8)
    ax.invert_yaxis()
    ax.xaxis.set_major_formatter(PCT)
    ax.set_xlim(base - 0.12, 1.0)
    ax.set_xlabel(f'% con síntomas {nombre} (IC 95 %)', fontsize=8)
    ax.set_title(f'Diez reglas no redundantes con mayor |z| → síntomas {nombre}; línea: basal {c(100 * base, 1)} %', loc='left', x=-0.665, fontsize=9)
    ax.xaxis.grid(True, color=REJILLA, lw=0.7)
    ax.set_axisbelow(True)
h = [Line2D([], [], marker='o', color=CLASE[k][0], label=CLASE[k][1]) for k in ['4 compatible con la referencia nula', '6 asociación relativamente más marcada']]
fig.legend(handles=h, loc='lower center', ncol=2, frameon=False, bbox_to_anchor=(0.5, 0.0))
titulo(fig, 'Figura 7. Las reglas más fuertes de la búsqueda principal',
       'Se muestran para ver qué hay, no como hallazgos. Solo una cumple los criterios del protocolo; no es robusta, ni está validada clínicamente, ni es una recomendación individual.', y=0.955)
guardar(fig, 'f07_reglas_mayor_z.png')

# f08 umbrales
th = [('S3-bajo', 27), ('principal', 53), ('S3-alto', 80)]
fil = []
for nombre, u in th:
    if nombre == 'principal':
        fil.append((f'≥ {u} (principal)', meta['reglas'], meta['marcadas'], meta['nula_media_marcadas'], meta['supera_nula']))
    else:
        r = res.set_index('configuracion').loc[nombre]
        fil.append((f'≥ {u}', r['reglas'], r['marcadas'], r['nula_media_marcadas'], r['supera_nula']))
fig, axs = plt.subplots(1, 2, figsize=(9, 3.4))
x = np.arange(len(fil))
axs[0].bar(x, [f[1] for f in fil], color='#9cc3ef', width=0.6)
for i, f in enumerate(fil):
    axs[0].text(i, f[1], e(f[1]), ha='center', va='bottom', fontsize=8)
axs[0].set_title('Reglas evaluadas')
axs[1].bar(x - 0.18, [f[2] for f in fil], width=0.34, color=NARANJA, label='Marcadas observadas')
axs[1].bar(x + 0.18, [f[3] for f in fil], width=0.34, color='#9cc3ef', label='Media bajo la nula')
for i, f in enumerate(fil):
    axs[1].text(i, max(f[2], f[3]) + 110, f'superan la nula: {f[4]}', ha='center', fontsize=7.5, color=TINTA2)
axs[1].set_title('Reglas marcadas')
axs[1].set_ylim(0, max(f[2] for f in fil) * 1.25)
axs[1].legend(frameon=False, fontsize=7.5, loc='upper right')
for a in axs:
    a.set_xticks(x)
    a.set_xticklabels([f[0] for f in fil])
    a.set_xlabel('Participantes mínimas con el antecedente')
    a.yaxis.grid(True, color=REJILLA, lw=0.7)
    a.set_axisbelow(True)
fig.subplots_adjust(wspace=0.3)
titulo(fig, 'Figura 8. Compromiso entre umbral de soporte y cantidad de reglas',
       'Bajar el umbral multiplica las reglas y también las que aparecen por azar. La única regla que supera la nula está en el umbral principal y no es robusta.')
guardar(fig, 'f08_umbrales.png')
(VAL / 'registro_figuras_38r.json').write_text(json.dumps(REG, ensure_ascii=False), encoding='utf-8', newline='\n')
print('figuras:', len(list(FIG.glob('*.png'))))
print('fuera de ylim f02:', int((R['confianza'] > 0.86).sum()), 'razón máx f05:', max(f['marcadas'] / pd.read_csv(f['arch'])['reglas_marcadas'].mean() for f in filas))
print(L.sum().to_dict())
print(R.groupby('consecuente')['confianza'].max().to_dict(), top['clase'].value_counts().to_dict())
