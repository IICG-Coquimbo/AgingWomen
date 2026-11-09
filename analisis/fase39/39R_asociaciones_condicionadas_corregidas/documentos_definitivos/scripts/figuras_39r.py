"""
Fase 39R, fase documental: las seis figuras con la presentación de graficos_39.py, leídas solo de los CSV ya validados de la 39R.
f01 (poblaciones y basales) exige datos idénticos a los históricos y conserva su presentación; solo mueve al título una etiqueta que tapaba un punto. No busca reglas ni permuta.

Uso: python -B figuras_39r.py
"""
import json
import sys
import textwrap
from pathlib import Path

sys.dont_write_bytecode = True
AQUI = Path(__file__).resolve().parent
DOC = AQUI.parent
B = DOC.parent
HIST = B.parent / '39_asociaciones_condicionadas'
sys.path.insert(0, str(B / 'scripts'))
import matplotlib  # noqa: E402

matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

import nucleo_39r as N  # noqa: E402

H = N.H39
F = DOC / 'figuras'
F.mkdir(parents=True, exist_ok=True)
VAL = DOC / 'validacion'
VAL.mkdir(parents=True, exist_ok=True)
AZUL, NARANJA, GRIS, TINTA, SUAVE = '#2b6cb0', '#dd6b20', '#a0aec0', '#2d3748', '#718096'
plt.rcParams.update({'font.size': 9, 'axes.edgecolor': SUAVE, 'axes.labelcolor': TINTA, 'xtick.color': TINTA, 'ytick.color': TINTA, 'axes.spines.top': False,
                     'axes.spines.right': False, 'axes.grid': True, 'grid.color': '#e2e8f0', 'grid.linewidth': 0.6, 'axes.axisbelow': True})
REG = {}


def coma(x, d=2):
    return f'{x:.{d}f}'.replace('.', ',')


def extraer(fig):
    salida = []
    for ax in fig.axes:
        barras = [[float(p.get_x()), float(p.get_y()), float(p.get_width()), float(p.get_height())] for p in ax.patches if isinstance(p, Rectangle)]
        lineas = [[[float(v) for v in np.asarray(x, dtype=float)[:4]], [float(v) for v in np.asarray(y, dtype=float)[:4]]] for x, y in (ln.get_data() for ln in ax.lines)]
        puntos = [[[float(a), float(b)] for a, b in np.asarray(c.get_offsets())] for c in ax.collections if len(c.get_offsets())]
        salida.append({'titulo': ax.get_title() or ax.get_title(loc='left'), 'barras': barras, 'lineas': lineas, 'puntos': puntos, 'ejex': ax.get_xlabel(),
                       'etiquetas_y': [t.get_text() for t in ax.get_yticklabels()], 'etiquetas_x': [t.get_text() for t in ax.get_xticklabels()]})
    return salida


FILTRO = sys.argv[1:]  # sin argumentos guarda todas; con prefijos (f03 f04) solo esas. El registro se rehace siempre completo.


def guardar(fig, nombre):
    REG[nombre] = extraer(fig)
    REG.setdefault('_fuente_minima', {})[nombre] = min(float(x.get_fontsize()) for x in fig.findobj(matplotlib.text.Text) if x.get_text().strip() and x.get_visible())
    if not FILTRO or any(nombre.startswith(x) for x in FILTRO):
        fig.savefig(F / nombre, dpi=160, bbox_inches='tight')
    plt.close(fig)


D = pd.read_csv(B / 'preparacion' / 'diccionario_estratos.csv')
RE = pd.read_csv(B / 'reglas' / 'resumen_estratos.csv')
AB = pd.read_csv(B / 'ab1' / 'resumen_grupos_A_B1.csv')
Hs = {g: pd.read_csv(B / 'comparacion' / f'comparacion_{g}.csv') for g in N.DIMENSIONES}
NH = {g: pd.read_csv(B / 'comparacion' / f'nula_comparacion_{g}.csv') for g in N.DIMENSIONES}
L = pd.read_csv(B / 'sensibilidades' / 'lectura_comparaciones_principal.csv')
etq = lambda e: N.NOMBRE.get(e, e.replace('_', ' '))  # noqa: E731

# f01: solo poblaciones y basales. Si los datos dibujados son idénticos, se conserva la figura.
columnas = ['grupo', 'estrato', 'participantes', 'severas', 'no_severas', 'frecuencia_basal_si', 'ic_basal_inf', 'ic_basal_sup']
Dh = pd.read_csv(HIST / 'preparacion' / 'diccionario_estratos.csv')
if not D[columnas].equals(Dh[columnas]):
    raise SystemExit('f01: los datos de poblaciones cambiaron; no se puede conservar la figura')
fig, ax = plt.subplots(figsize=(8, 4.6))
t = D.reset_index(drop=True)
x = np.arange(len(t))
col = [AZUL if g in N.DIMENSIONES else GRIS for g in t['grupo']]
ax.errorbar(x, t['frecuencia_basal_si'], yerr=[t['frecuencia_basal_si'] - t['ic_basal_inf'], t['ic_basal_sup'] - t['frecuencia_basal_si']], fmt='none', ecolor=SUAVE, lw=1, capsize=2)
ax.scatter(x, t['frecuencia_basal_si'], c=col, s=36, zorder=3)
ax.axhline(281 / 529, color=NARANJA, lw=1, ls='--')
for i, r in t.iterrows():
    ax.text(i, 0.17, f"n={r['participantes']}", ha='center', fontsize=7, color=SUAVE, rotation=90)
ax.set_xticks(x, [etq(e) for e in t['estrato']], rotation=60, ha='right')
ax.set_ylim(0.1, 0.8)
ax.yaxis.set_major_formatter(lambda v, _: f'{v * 100:.0f} %')
ax.set_ylabel('Participantes con síntomas severos (IC 95 %)')
# Única diferencia con la figura histórica: la etiqueta de la basal general tapaba un punto y pasa al título.
ax.set_title('Frecuencia basal de MRS severo por estrato (azul) y por grupo A/B1 (gris)\nLínea naranja: basal general 53,1 %. Versión correctiva 39R: poblaciones y basales sin cambios.', loc='left', fontsize=10, color=TINTA)
guardar(fig, 'f01_tamanos_basales.png')
REG['f01_datos_identicos_a_historica'] = {'datos_identicos': True, 'columnas_comparadas': columnas}

# f02 reglas marcadas observadas frente a la nula
fig, ax = plt.subplots(figsize=(8, 4))
t = pd.concat([RE.rename(columns={'dimension': 'grupo'}), AB], ignore_index=True)
x = np.arange(len(t))
ax.bar(x - 0.2, t['marcadas'], width=0.38, color=AZUL, label='Reglas marcadas observadas')
ax.bar(x + 0.2, t['nula_media_marcadas'], width=0.38, color=GRIS, label='Media bajo la referencia nula')
ax.scatter(x + 0.2, t['nula_p95_marcadas'], marker='_', s=120, color=TINTA, label='Percentil 95 nulo', zorder=3)
ax.set_xticks(x, [etq(e) for e in t['estrato']], rotation=60, ha='right')
ax.set_ylabel('Reglas con |c − p₀| ≥ 0,10')
ax.legend(frameon=False, fontsize=8)
ax.set_title('Exceso de reglas marcadas dentro de cada estrato\nVersión correctiva 39R. Un exceso global no hace significativa ninguna regla individual.', loc='left', fontsize=10, color=TINTA)
guardar(fig, 'f02_marcadas_frente_a_nula.png')

# f03 máximo Q observado frente a la nula
fig, axs = plt.subplots(2, 2, figsize=(7.6, 4.6), sharey=True)
axs = axs.ravel()
for ax, g in zip(axs, N.DIMENSIONES):
    ax.hist(NH[g]['max_Q'], bins=30, color=GRIS)
    q = Hs[g]['Q'].max()
    ax.axvline(q, color=NARANJA, lw=1.5)
    ax.axvline(NH[g]['max_Q'].quantile(0.95), color=TINTA, lw=1, ls=':')
    ax.set_title(f'{etq(g)}: observado {coma(q, 1)}', fontsize=9, color=TINTA)
    ax.set_xlabel('Máximo Q de la búsqueda')
axs[0].set_ylabel('Permutaciones')
axs[2].set_ylabel('Permutaciones')
fig.suptitle('El mayor Q observado (naranja) queda dentro de la referencia nula\n(punteado: percentil 95). Versión correctiva 39R.', x=0.01, ha='left', fontsize=10, color=TINTA)
fig.tight_layout()
guardar(fig, 'f03_heterogeneidad_frente_a_nula.png')

# f04 diferencias de riesgo por estrato para las comparaciones con mayor Q
fig, axs = plt.subplots(4, 1, figsize=(7.6, 10.2))
fig.subplots_adjust(left=0.5, right=0.98, top=0.93, bottom=0.05, hspace=0.42)
for ax, g in zip(axs.ravel(), N.DIMENSIONES):
    est = N.dims_de(g)
    t = Hs[g][~Hs[g]['redundante']].sort_values('Q', ascending=False).head(6).iloc[::-1].reset_index(drop=True)
    cols = [AZUL, NARANJA, '#38a169']
    for j, e in enumerate(est):
        off = (j - (len(est) - 1) / 2) * 0.22
        yy = np.arange(len(t)) + off
        ax.errorbar(t[f'DR_{e}'], yy, xerr=[t[f'DR_{e}'] - t[f'DR_inf_{e}'], t[f'DR_sup_{e}'] - t[f'DR_{e}']], fmt='o', ms=4, color=cols[j], lw=1, label=etq(e))
    ax.axvline(0, color=SUAVE, lw=0.8)
    lab = [H.legible_regla(a) for a in t['antecedente']]
    ax.set_yticks(np.arange(len(t)), [f'{chr(10).join(textwrap.wrap(l, 66))} (p ajust. {coma(p, 2)})' for l, p in zip(lab, t['p_ajustado_dimension'])], fontsize=6.6)
    ax.tick_params(axis='x', labelsize=7.5)
    ax.set_xlabel('Diferencia de riesgo (IC 95 %)', fontsize=7.5)
    ax.set_title(etq(g), loc='left', x=-1.02, fontsize=9.5, color=TINTA)
    ax.legend(frameon=False, fontsize=7, loc='lower right', bbox_to_anchor=(1.0, 0.995), ncol=3, borderaxespad=0, handletextpad=0.2, columnspacing=0.8)
fig.suptitle('Comparaciones con mayor heterogeneidad: ninguna supera la referencia nula.\nVersión correctiva 39R.', x=0.01, y=0.985, ha='left', fontsize=10.5, color=TINTA)
guardar(fig, 'f04_comparaciones_mayor_Q.png')

# f05 lectura de las diferencias marcadas en las sensibilidades
t = L.groupby(['sensibilidad', 'lectura']).size().unstack(fill_value=0)
orden = ['se mantiene', 'se debilita', 'cambia de dirección', 'no evaluable']
t = t.reindex(columns=[c for c in orden if c in t.columns])
fig, ax = plt.subplots(figsize=(8, 3.6))
izq = np.zeros(len(t))
for c, colr in zip(t.columns, [AZUL, '#90cdf4', NARANJA, GRIS]):
    ax.barh(t.index, t[c], left=izq, color=colr, label=c, height=0.6, edgecolor='white', linewidth=1)
    izq += t[c].to_numpy()
ax.set_xlabel('Diferencias marcadas de la principal (las cuatro dimensiones)')
ax.legend(frameon=False, fontsize=8, ncol=4, loc='upper center', bbox_to_anchor=(0.5, -0.18))
ax.set_title('Qué ocurre con las diferencias marcadas en cada sensibilidad\nVersión correctiva 39R. Las sensibilidades no sustituyen al análisis principal.', loc='left', fontsize=10, color=TINTA)
guardar(fig, 'f05_sensibilidades_comparaciones.png')
tabla_f05 = t.copy()

# f06 estabilidad frente a p ajustado
fig, ax = plt.subplots(figsize=(6.5, 4))
for g, colr in zip(N.DIMENSIONES, [AZUL, NARANJA, '#38a169', '#805ad5']):
    t = Hs[g][Hs[g]['marcada'] & ~Hs[g]['redundante']]
    ax.scatter(t['p_ajustado_dimension'], t['reaparece_marcada'], s=10, alpha=0.6, color=colr, label=etq(g))
ax.axhline(H.ESTABLE_REAP, color=SUAVE, ls=':', lw=1)
ax.axvline(H.ALFA, color=SUAVE, ls=':', lw=1)
ax.set_xlabel('p ajustado de la dimensión')
ax.set_ylabel('Reaparece marcada en las submuestras')
ax.legend(frameon=False, fontsize=8)
ax.set_title('La estabilidad no distingue las diferencias del azar\nVersión correctiva 39R.', loc='left', fontsize=10, color=TINTA)
guardar(fig, 'f06_estabilidad_comparaciones.png')
(VAL / 'registro_figuras_39r.json').write_text(json.dumps(REG, ensure_ascii=False), encoding='utf-8', newline='\n')
print(sorted(p.name for p in F.glob('*.png')))
print(tabla_f05.to_string())
print({g: (round(float(Hs[g]['Q'].max()), 3), round(float(NH[g]['max_Q'].quantile(0.95)), 3)) for g in N.DIMENSIONES})
