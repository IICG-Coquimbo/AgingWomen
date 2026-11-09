"""Fase 39: figuras, generadas solo desde las tablas guardadas. Uso, desde la carpeta scripts: python graficos_39.py"""
import sys

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import nucleo_39 as N  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.dont_write_bytecode = True
N.instalar_gancho()
B = N.BASE
F = B / 'figuras'
F.mkdir(parents=True, exist_ok=True)
AZUL, NARANJA, GRIS, TINTA, SUAVE = '#2b6cb0', '#dd6b20', '#a0aec0', '#2d3748', '#718096'
plt.rcParams.update({'font.size': 9, 'axes.edgecolor': SUAVE, 'axes.labelcolor': TINTA, 'xtick.color': TINTA, 'ytick.color': TINTA, 'axes.spines.top': False,
                     'axes.spines.right': False, 'axes.grid': True, 'grid.color': '#e2e8f0', 'grid.linewidth': 0.6, 'axes.axisbelow': True})


def coma(x, d=2):
    return f'{x:.{d}f}'.replace('.', ',')


def guardar(fig, nombre):
    fig.savefig(F / nombre, dpi=160, bbox_inches='tight')
    plt.close(fig)


D = pd.read_csv(B / 'preparacion' / 'diccionario_estratos.csv')
RE = pd.read_csv(B / 'reglas' / 'resumen_estratos.csv')
AB = pd.read_csv(B / 'ab1' / 'resumen_grupos_A_B1.csv')
Hs = {g: pd.read_csv(B / 'comparacion' / f'comparacion_{g}.csv') for g in N.DIMENSIONES}
NH = {g: pd.read_csv(B / 'comparacion' / f'nula_comparacion_{g}.csv') for g in N.DIMENSIONES}
L = pd.read_csv(B / 'sensibilidades' / 'lectura_comparaciones_principal.csv')
etq = lambda e: N.NOMBRE.get(e, e.replace('_', ' '))  # noqa: E731

# f01 tamaños y basales
fig, ax = plt.subplots(figsize=(8, 4.6))
t = D.reset_index(drop=True)
x = np.arange(len(t))
col = [AZUL if g in N.DIMENSIONES else GRIS for g in t['grupo']]
ax.errorbar(x, t['frecuencia_basal_si'], yerr=[t['frecuencia_basal_si'] - t['ic_basal_inf'], t['ic_basal_sup'] - t['frecuencia_basal_si']], fmt='none', ecolor=SUAVE, lw=1, capsize=2)
ax.scatter(x, t['frecuencia_basal_si'], c=col, s=36, zorder=3)
ax.axhline(281 / 529, color=NARANJA, lw=1, ls='--')
ax.text(-0.4, 281 / 529 - 0.035, 'basal general 53,1 %', color=TINTA, ha='left', fontsize=8)
for i, r in t.iterrows():
    ax.text(i, 0.17, f"n={r['participantes']}", ha='center', fontsize=7, color=SUAVE, rotation=90)
ax.set_xticks(x, [etq(e) for e in t['estrato']], rotation=60, ha='right')
ax.set_ylim(0.1, 0.8)
ax.yaxis.set_major_formatter(lambda v, _: f'{v * 100:.0f} %')
ax.set_ylabel('Participantes con síntomas severos (IC 95 %)')
ax.set_title('Frecuencia basal de MRS severo por estrato (azul) y por grupo A/B1 (gris)', loc='left', fontsize=10, color=TINTA)
guardar(fig, 'f01_tamanos_basales.png')

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
ax.set_title('Exceso de reglas marcadas dentro de cada estrato', loc='left', fontsize=10, color=TINTA)
guardar(fig, 'f02_marcadas_frente_a_nula.png')

# f03 máximo Q observado frente a la nula
fig, axs = plt.subplots(1, 4, figsize=(10, 2.8), sharey=True)
for ax, g in zip(axs, N.DIMENSIONES):
    ax.hist(NH[g]['max_Q'], bins=30, color=GRIS)
    q = Hs[g]['Q'].max()
    ax.axvline(q, color=NARANJA, lw=1.5)
    ax.axvline(NH[g]['max_Q'].quantile(0.95), color=TINTA, lw=1, ls=':')
    ax.set_title(f'{etq(g)}: observado {coma(q, 1)}', fontsize=9, color=TINTA)
    ax.set_xlabel('Máximo Q de la búsqueda')
axs[0].set_ylabel('Permutaciones')
fig.suptitle('El mayor Q observado (naranja) queda dentro de la referencia nula (punteado: percentil 95)', x=0.01, ha='left', fontsize=10, color=TINTA)
fig.tight_layout()
guardar(fig, 'f03_heterogeneidad_frente_a_nula.png')

# f04 diferencias de riesgo por estrato para las comparaciones con mayor Q
fig, axs = plt.subplots(2, 2, figsize=(10, 7.2))
for ax, g in zip(axs.ravel(), N.DIMENSIONES):
    est = N.dims_de(g)
    t = Hs[g][~Hs[g]['redundante']].sort_values('Q', ascending=False).head(6).iloc[::-1].reset_index(drop=True)
    cols = [AZUL, NARANJA, '#38a169']
    for j, e in enumerate(est):
        off = (j - (len(est) - 1) / 2) * 0.22
        yy = np.arange(len(t)) + off
        ax.errorbar(t[f'DR_{e}'], yy, xerr=[t[f'DR_{e}'] - t[f'DR_inf_{e}'], t[f'DR_sup_{e}'] - t[f'DR_{e}']], fmt='o', ms=4, color=cols[j], lw=1, label=etq(e))
    ax.axvline(0, color=SUAVE, lw=0.8)
    lab = [N.legible_regla(a).replace(' y ', '\ny ') for a in t['antecedente']]
    ax.set_yticks(np.arange(len(t)), [f'{l}\n(p ajust. {coma(p, 2)})' for l, p in zip(lab, t['p_ajustado_dimension'])], fontsize=6)
    ax.set_xlabel('Diferencia de riesgo (IC 95 %)')
    ax.set_title(etq(g), loc='left', fontsize=10, color=TINTA)
    ax.legend(frameon=True, framealpha=0.9, edgecolor='none', fontsize=7, loc='upper center', bbox_to_anchor=(0.5, -0.2), ncol=3)
fig.suptitle('Comparaciones con mayor heterogeneidad: ninguna supera la referencia nula', x=0.01, ha='left', fontsize=11, color=TINTA)
fig.tight_layout()
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
ax.set_title('Qué ocurre con las diferencias marcadas en cada sensibilidad', loc='left', fontsize=10, color=TINTA)
guardar(fig, 'f05_sensibilidades_comparaciones.png')

# f06 estabilidad frente a p ajustado
fig, ax = plt.subplots(figsize=(6.5, 4))
for g, colr in zip(N.DIMENSIONES, [AZUL, NARANJA, '#38a169', '#805ad5']):
    t = Hs[g][Hs[g]['marcada'] & ~Hs[g]['redundante']]
    ax.scatter(t['p_ajustado_dimension'], t['reaparece_marcada'], s=10, alpha=0.6, color=colr, label=etq(g))
ax.axhline(N.ESTABLE_REAP, color=SUAVE, ls=':', lw=1)
ax.axvline(N.ALFA, color=SUAVE, ls=':', lw=1)
ax.set_xlabel('p ajustado de la dimensión')
ax.set_ylabel('Reaparece marcada en las submuestras')
ax.legend(frameon=False, fontsize=8)
ax.set_title('La estabilidad no distingue las diferencias del azar', loc='left', fontsize=10, color=TINTA)
guardar(fig, 'f06_estabilidad_comparaciones.png')
N.registrar('figuras')
print(sorted(p.name for p in F.glob('*.png')))
