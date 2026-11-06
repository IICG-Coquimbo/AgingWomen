"""
Fase 38: figuras, leídas siempre de las tablas guardadas. No calcula reglas.

Uso, desde la carpeta scripts: python graficos_38.py
"""
import sys
import textwrap

sys.dont_write_bytecode = True
import matplotlib  # noqa: E402

matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

import nucleo_38 as N  # noqa: E402

B = N.BASE
FIG = B / 'figuras'
FIG.mkdir(exist_ok=True)
AZUL, NARANJA, GRIS, TINTA, TINTA2, REJILLA = '#2a78d6', '#eb6834', '#8a8983', '#0b0b0b', '#52514e', '#e4e3df'
CLASE = {'2 asociación débil': ('#d3d2cd', 'Asociación débil'), '3 redundante': ('#9cc3ef', 'Redundante'),
         '4 compatible con la referencia nula': ('#eda100', 'Compatible con la referencia nula'), '5 inestable': ('#eb6834', 'Inestable'),
         '6 asociación relativamente más marcada': ('#0f3e7a', 'Supera todos los criterios'), '1 soporte insuficiente': ('#f2f1ee', 'Soporte insuficiente'),
         '5-6 supera la nula (estabilidad no evaluada)': ('#0f3e7a', 'Supera la nula')}
LECT = {'se mantiene': '#2a78d6', 'se debilita': '#9cc3ef', 'cambia de dirección': '#c4501f', 'desaparece por falta de casos': '#eda100', 'no evaluable': '#d3d2cd'}
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.titlesize': 10, 'axes.titleweight': 'bold', 'axes.edgecolor': '#bdbcb6', 'axes.labelcolor': TINTA2,
                     'xtick.color': TINTA2, 'ytick.color': TINTA2, 'axes.spines.top': False, 'axes.spines.right': False, 'figure.dpi': 110, 'savefig.dpi': 170,
                     'savefig.bbox': 'tight', 'figure.facecolor': 'white'})
COMA = FuncFormatter(lambda x, _: f'{x:g}'.replace('.', ',').replace('-', '−'))
PCT = FuncFormatter(lambda x, _: f'{100 * x:.0f} %')


def c(x, d=2):
    return f'{x:.{d}f}'.replace('.', ',').replace('-', '−')


def titulo(fig, t, sub, y=1.0):
    fig.suptitle(t, x=0.01, y=y + 0.07, ha='left', fontsize=12, fontweight='bold')
    fig.text(0.01, y + 0.02, sub, ha='left', va='top', fontsize=8.5, color=TINTA2)


def guardar(fig, nombre):
    fig.savefig(FIG / nombre)
    plt.close(fig)


R = pd.read_csv(B / 'reglas' / 'reglas_principal.csv')
nula = pd.read_csv(B / 'referencia_nula' / 'nula_principal.csv')
meta = N.leer_json(B / 'reglas' / 'resumen_principal.json')
E = pd.read_csv(B / 'estabilidad' / 'estabilidad_reglas.csv')
Sb = pd.read_csv(B / 'estabilidad' / 'submuestras.csv')
DI = pd.read_csv(B / 'preparacion' / 'diccionario_items.csv')
res = pd.read_csv(B / 'sensibilidades' / 'resumen_sensibilidades.csv')
lect = pd.read_csv(B / 'sensibilidades' / 'lectura_resumen.csv')
top = pd.read_csv(B / 'reglas' / 'reglas_no_destacadas_mayor_z.csv')
dest = pd.read_csv(B / 'reglas' / 'reglas_destacadas.csv')
p0 = meta['frecuencia_basal_si']

# f01 ítems
it = DI[(DI['item'] != '(sin ítem)') & DI['variable'].isin(N.PRINCIPAL)].copy()
it['orden'] = it['variable'].map({v: i for i, v in enumerate(N.PRINCIPAL)})
it = it.sort_values(['orden'], kind='stable').reset_index(drop=True)
fig, ax = plt.subplots(figsize=(8.5, 17))
ypos, etiquetas, y, prev = [], [], 0, None
for r in it.itertuples():
    if prev is not None and r.variable != prev:
        y += 0.6
    ypos.append(y)
    etiquetas.append(N.legible(r.item))
    prev = r.variable
    y += 1
colores = [NARANJA if r.startswith('R2 unión') else AZUL for r in it['regla']]
ax.barh(ypos, it['participantes'], color=colores, height=0.75)
for yy, v in zip(ypos, it['participantes']):
    ax.text(v + 4, yy, str(v), va='center', fontsize=7, color=TINTA2)
ax.axvline(27, color=TINTA2, lw=0.8, ls='--')
ax.axvline(53, color=TINTA2, lw=0.8, ls=':')
ax.set_yticks(ypos)
ax.set_yticklabels(etiquetas, fontsize=7)
ax.invert_yaxis()
ax.set_xlabel('Participantes con el ítem')
ax.xaxis.grid(True, color=REJILLA, lw=0.7)
ax.set_axisbelow(True)
ax.legend(handles=[Patch(color=AZUL, label='Categoría original'), Patch(color=NARANJA, label='Unión de categorías escasas (R2)'),
                   Line2D([], [], color=TINTA2, lw=0.8, ls='--', label='27 participantes (5 %)'), Line2D([], [], color=TINTA2, lw=0.8, ls=':', label='53 participantes (10 %)')],
          loc='lower right', frameon=False)
titulo(fig, 'Figura 1. Ítems del análisis principal', '94 ítems de 31 variables en las 529 participantes. Cada barra es una respuesta (o grupo de respuestas).', y=0.905)
guardar(fig, 'f01_items_principal.png')

# f02 confianza frente a casos
zq = meta['nula_p95_max_z']
fig, axs = plt.subplots(1, 2, figsize=(11, 4.6))
orden = ['2 asociación débil', '3 redundante', '4 compatible con la referencia nula', '6 asociación relativamente más marcada']
for ax, cons, base, nombre in zip(axs, N.CONSECUENTES, (p0, 1 - p0), ('severo_mrs = SI', 'severo_mrs = NO')):
    sub = R[R['consecuente'] == cons]
    for k in orden:
        s = sub[sub['clase'] == k]
        ax.scatter(s['n_antecedente'], s['confianza'], s=6 if k.startswith('2') else 12, color=CLASE[k][0], lw=0, alpha=0.8 if k.startswith('2') else 1, zorder=2 + orden.index(k))
    xs = np.linspace(53, 530, 300)
    ax.plot(xs, base + zq * np.sqrt(base * (1 - base) / xs), color=TINTA, lw=1.2, zorder=6)
    ax.axhline(base, color=TINTA2, lw=0.9, ls='--')
    ax.axhline(base + N.DIF_MARCADA, color=TINTA2, lw=0.8, ls=':')
    ax.text(525, base + 0.006, f'basal {c(100 * base, 1)} %', ha='right', fontsize=7.5, color=TINTA2)
    ax.text(525, base + N.DIF_MARCADA + 0.006, 'basal + 10 puntos', ha='right', fontsize=7.5, color=TINTA2)
    ax.set_xscale('log')
    ax.set_xticks([53, 100, 200, 300, 500])
    ax.xaxis.set_major_formatter(COMA)
    ax.yaxis.set_major_formatter(PCT)
    ax.set_xlabel('Participantes con el antecedente (n_A, escala logarítmica)')
    ax.set_ylabel(f'Confianza: % con {nombre}')
    ax.set_title(f'Reglas → {nombre} ({len(sub):,} reglas)'.replace(',', '.'))
    ax.set_ylim(base - 0.02, 0.86)
    ax.yaxis.grid(True, color=REJILLA, lw=0.7)
    ax.set_axisbelow(True)
h = [Line2D([], [], marker='o', ls='', color=CLASE[k][0], label=CLASE[k][1]) for k in orden] + [Line2D([], [], color=TINTA, lw=1.2, label='Umbral de la referencia nula (p ajustado = 0,05)')]
fig.legend(handles=h, loc='lower center', ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.1))
fig.subplots_adjust(wspace=0.25)
titulo(fig, 'Figura 2. Confianza de cada regla según el número de participantes que cumple el antecedente',
       'Solo las reglas sobre la curva negra superan lo que la búsqueda produce por azar. Las demás están dentro de lo esperable con 12.201 reglas.')
guardar(fig, 'f02_confianza_frente_a_casos.png')

# f03 referencia nula
fig, axs = plt.subplots(1, 2, figsize=(11, 3.8))
ax = axs[0]
ax.hist(nula['max_z'], bins=40, color='#9cc3ef')
zo = R['z'].abs().max()
ax.axvline(zo, color=NARANJA, lw=1.6)
ax.axvline(zq, color=TINTA, lw=1, ls='--')
ax.text(zo, ax.get_ylim()[1] * 0.92, f' observado\n {c(zo)}', color=NARANJA, fontsize=8, va='top')
ax.text(zq, ax.get_ylim()[1] * 0.6, f'percentil 95 nulo {c(zq)} ', color=TINTA, fontsize=8, ha='right')
ax.set_xlabel('Mayor |z| entre todas las reglas de la búsqueda')
ax.xaxis.set_major_formatter(COMA)
ax.set_ylabel('Permutaciones')
ax.set_title('Regla más fuerte: observada frente a 1.000 permutaciones')
ax = axs[1]
ax.hist(nula['reglas_marcadas'], bins=40, color='#9cc3ef')
ax.axvline(meta['marcadas'], color=NARANJA, lw=1.6)
ax.text(meta['marcadas'], ax.get_ylim()[1] * 0.92, f' observadas\n {meta["marcadas"]:,}'.replace(',', '.'), color=NARANJA, fontsize=8, va='top')
ax.axvline(nula['reglas_marcadas'].mean(), color=TINTA, lw=1, ls='--')
ax.text(nula['reglas_marcadas'].mean(), ax.get_ylim()[1] * 0.6, f'media nula {nula["reglas_marcadas"].mean():.0f} ', color=TINTA, fontsize=8, ha='right')
ax.set_xlabel('Reglas marcadas (|confianza − basal| ≥ 10 puntos)')
ax.set_title('Número de reglas marcadas')
for a in axs:
    a.yaxis.grid(True, color=REJILLA, lw=0.7)
    a.set_axisbelow(True)
fig.subplots_adjust(wspace=0.3)
titulo(fig, 'Figura 3. Referencia nula: lo que aparece al romper la relación con la severidad',
       'En cada permutación se repite la búsqueda completa con el consecuente mezclado al azar. Hay más reglas marcadas que por azar, pero casi ninguna sobresale.')
guardar(fig, 'f03_referencia_nula.png')

# f04 estabilidad
M = R[R['marcada']]
fig, axs = plt.subplots(1, 2, figsize=(11, 3.8))
ax = axs[0]
bins = np.linspace(0, 1, 21)
for k in ['3 redundante', '4 compatible con la referencia nula']:
    s = M[M['clase'] == k]['reaparece_marcada']
    ax.hist(s, bins=bins, histtype='step', lw=1.6, color=CLASE[k][0], label=f'{CLASE[k][1]} ({len(s)})')
for r in M[M['clase'].str.startswith('6')].itertuples():
    ax.axvline(r.reaparece_marcada, color=CLASE['6 asociación relativamente más marcada'][0], lw=1.6, label='Supera todos los criterios (1)')
ax.axvline(N.ESTABLE_REAP, color=TINTA2, lw=0.9, ls=':')
ax.text(N.ESTABLE_REAP, ax.get_ylim()[1] * 0.97, ' criterio 70 %', fontsize=7.5, color=TINTA2, va='top')
ax.xaxis.set_major_formatter(PCT)
ax.set_xlabel('Submuestras en que la regla reaparece marcada')
ax.set_ylabel('Reglas marcadas')
ax.set_title('Reaparición de las 1.119 reglas marcadas')
ax.legend(frameon=False, fontsize=7.5, loc='upper left')
ax = axs[1]
ax.hist(Sb['nuevas'], bins=30, color='#eda100', alpha=0.8, label='Nuevas (marcadas solo en la submuestra)')
ax.hist(Sb['desaparecidas'], bins=30, color='#2a78d6', alpha=0.7, label='Desaparecidas (marcadas solo en las 529)')
ax.set_xlabel('Reglas por submuestra')
ax.set_ylabel('Submuestras')
ax.set_title('Reglas nuevas y desaparecidas por submuestra')
ax.legend(frameon=False, fontsize=7.5)
for a in axs:
    a.yaxis.grid(True, color=REJILLA, lw=0.7)
    a.set_axisbelow(True)
fig.subplots_adjust(wspace=0.3)
titulo(fig, 'Figura 4. Estabilidad en 200 submuestras del 80 %',
       'Las reglas compatibles con el azar también reaparecen a menudo: las submuestras comparten la mayor parte de los datos. Estabilidad no es validez.')
guardar(fig, 'f04_estabilidad.png')

# f05 exceso frente a la nula por configuración
conf_orden = ['principal'] + list(res['configuracion'])
filas = [{'configuracion': 'principal', 'marcadas': meta['marcadas'], 'arch': B / 'referencia_nula' / 'nula_principal.csv', 'n': 529}] + \
        [{'configuracion': r.configuracion, 'marcadas': r.marcadas, 'arch': B / 'sensibilidades' / 'nula' / f'nula_{r.configuracion}.csv', 'n': r.n} for r in res.itertuples()]
fig, ax = plt.subplots(figsize=(9, 5))
for i, f in enumerate(filas):
    nl = pd.read_csv(f['arch'])['reglas_marcadas']
    m = nl.mean()
    lo, hi = np.percentile(nl, [5, 95]) / m
    ax.plot([lo, hi], [i, i], color='#9cc3ef', lw=5, solid_capstyle='round')
    ax.plot(1, i, '|', color=TINTA2, ms=10)
    ax.plot(f['marcadas'] / m, i, 'o', color=NARANJA, ms=6)
    ax.text(max(hi, f['marcadas'] / m) + 0.04, i, f"{f['marcadas']:,} frente a {m:,.0f}".replace(',', '.'), va='center', fontsize=7.5, color=TINTA2)
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
       'Un valor de 1 es lo esperado sin ninguna relación. Casi todas las configuraciones muestran algo más de reglas que el azar: una señal difusa, no reglas puntuales.')
guardar(fig, 'f05_exceso_frente_a_nula.png')

# f06 lectura de las reglas marcadas de la principal
L = lect.set_index('configuracion')
cats = ['se mantiene', 'se debilita', 'cambia de dirección', 'desaparece por falta de casos', 'no evaluable']
L = L.reindex(columns=cats, fill_value=0)
fig, ax = plt.subplots(figsize=(9.5, 4.8))
izq = np.zeros(len(L))
for k in cats:
    ax.barh(range(len(L)), L[k], left=izq, color=LECT[k], label=k[0].upper() + k[1:], height=0.7, edgecolor='white', lw=0.8)
    izq += L[k].to_numpy()
ax.set_yticks(range(len(L)))
ax.set_yticklabels(L.index)
ax.invert_yaxis()
ax.set_xlabel('Reglas marcadas de la principal (1.119)')
ax.legend(frameon=False, ncol=3, loc='lower center', bbox_to_anchor=(0.45, -0.32), fontsize=8)
titulo(fig, 'Figura 6. Qué ocurre con las 1.119 reglas marcadas de la principal en cada sensibilidad',
       '«No evaluable»: la regla usa una variable excluida, un ítem distinto o más condiciones de las permitidas. Casi ninguna cambia de dirección.')
guardar(fig, 'f06_lectura_sensibilidades.png')

# f07 reglas con mayor |z|
fig, axs = plt.subplots(2, 1, figsize=(10, 10.5), gridspec_kw={'hspace': 0.45})
for ax, cons, base, nombre in zip(axs, N.CONSECUENTES, (p0, 1 - p0), ('severos (MRS ≥ 16)', 'no severos (MRS < 16)')):
    s = top[top['consecuente'] == cons].reset_index(drop=True)
    for i, r in s.iterrows():
        col = CLASE[r['clase']][0]
        ax.plot([r['ic_confianza_inf'], r['ic_confianza_sup']], [i, i], color=col, lw=2)
        ax.plot(r['confianza'], i, 'o', color=col, ms=6)
        ax.text(0.995, i, f"n_A = {r['n_antecedente']}", va='center', ha='right', fontsize=7, color=TINTA2, transform=ax.get_yaxis_transform())
    ax.axvline(base, color=TINTA2, ls='--', lw=0.9)
    ax.set_yticks(range(len(s)))
    ax.set_yticklabels(['\n'.join(textwrap.wrap(N.legible_regla(a), 70)) for a in s['antecedente']], fontsize=6.6)
    ax.invert_yaxis()
    ax.xaxis.set_major_formatter(PCT)
    ax.set_xlim(base - 0.12, 1.0)
    ax.set_xlabel(f'% con síntomas {nombre} entre quienes cumplen el antecedente (IC 95 %)')
    ax.set_title(f'Diez reglas no redundantes con mayor |z| → síntomas {nombre}; línea: frecuencia basal {c(100 * base, 1)} %', loc='left', fontsize=9.5)
    ax.xaxis.grid(True, color=REJILLA, lw=0.7)
    ax.set_axisbelow(True)
h = [Line2D([], [], marker='o', color=CLASE[k][0], label=CLASE[k][1]) for k in ['4 compatible con la referencia nula', '6 asociación relativamente más marcada']]
fig.legend(handles=h, loc='lower center', ncol=2, frameon=False, bbox_to_anchor=(0.5, 0.0))
titulo(fig, 'Figura 7. Las reglas más fuertes de la búsqueda principal', 'Se muestran para ver qué hay, no como hallazgos: solo una supera todos los criterios del protocolo.', y=0.925)
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
fig, axs = plt.subplots(1, 2, figsize=(10, 3.6))
x = np.arange(len(fil))
axs[0].bar(x, [f[1] for f in fil], color='#9cc3ef', width=0.6)
for i, f in enumerate(fil):
    axs[0].text(i, f[1], f'{f[1]:,}'.replace(',', '.'), ha='center', va='bottom', fontsize=8)
axs[0].set_title('Reglas evaluadas')
axs[1].bar(x - 0.18, [f[2] for f in fil], width=0.34, color=NARANJA, label='Marcadas observadas')
axs[1].bar(x + 0.18, [f[3] for f in fil], width=0.34, color='#9cc3ef', label='Media bajo la nula')
for i, f in enumerate(fil):
    axs[1].text(i, max(f[2], f[3]) * 1.03, f'superan la nula: {f[4]}', ha='center', fontsize=7.5, color=TINTA2)
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
       'Bajar el umbral multiplica las reglas y también las que aparecen por azar; ninguna configuración entrega reglas que superen la nula con claridad.')
guardar(fig, 'f08_umbrales.png')
print('figuras:', len(list(FIG.glob('*.png'))))
