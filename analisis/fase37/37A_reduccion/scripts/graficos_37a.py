"""
Fase 37A: gráficos, leídos siempre de las tablas y coordenadas guardadas. No ajusta nada y no lee el MRS.

Uso, desde analisis/: python fase37/37A_reduccion/scripts/graficos_37a.py
Cada función devuelve la figura, para que las pruebas comparen lo dibujado con las tablas.
"""
import sys
from pathlib import Path

sys.dont_write_bytecode = True

import matplotlib  # noqa: E402

matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

BASE = Path(__file__).resolve().parents[1]
T = BASE / 'tablas'
FIG = BASE / 'figuras'
AZUL, NARANJA, GRIS, TINTA, TINTA2, REJILLA = '#2a78d6', '#eb6834', '#8a8983', '#0b0b0b', '#52514e', '#e4e3df'
COLOR = {'P1': AZUL, 'P2': AZUL, 'F1': NARANJA, 'F2': NARANJA}
LINEA = {'P1': '-', 'P2': '--', 'F1': '-', 'F2': '--'}
NOMBRE = {'P1': 'PCA con IMC (P1)', 'P2': 'PCA sin IMC (P2)', 'F1': 'FAMD con IMC (F1)', 'F2': 'FAMD sin IMC (F2)'}
SECUENCIAL = LinearSegmentedColormap.from_list('azul', ['#f4f8fd', '#9cc3ef', '#2a78d6', '#0f3e7a'])
DIVERGENTE = LinearSegmentedColormap.from_list('div', ['#2a78d6', '#f1f1ee', '#eb6834'])
ESC = ['P1', 'P2', 'F1', 'F2']
CORTO = {'Etapa reproductiva y salud ginecológica': 'Etapa reproductiva', 'Medicamentos y digestión': 'Medicamentos y digestión', 'Medidas autodeclaradas': 'Medidas (IMC)', 'Cuidado de otras personas': 'Cuidado'}
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.titlesize': 10, 'axes.titleweight': 'bold', 'axes.edgecolor': '#bdbcb6', 'axes.labelcolor': TINTA2, 'xtick.color': TINTA2, 'ytick.color': TINTA2,
                     'axes.spines.top': False, 'axes.spines.right': False, 'axes.grid': False, 'figure.dpi': 110, 'savefig.dpi': 170, 'savefig.bbox': 'tight', 'legend.frameon': False})


def leer(n, **k):
    return pd.read_csv(T / n, encoding='utf-8', **k)


def rejilla(ax, eje='y'):
    ax.grid(True, axis=eje, color=REJILLA, lw=0.7)
    ax.set_axisbelow(True)


def titular(fig, titulo, sub=None):
    fig.suptitle(titulo, x=0.01, ha='left', fontsize=12, fontweight='bold', color=TINTA, y=1.0)
    if sub:
        fig.text(0.01, 0.955, sub, ha='left', va='top', fontsize=8.5, color=TINTA2)


def f01_sedimentacion():
    v = leer('valores_propios.csv')
    fig, axs = plt.subplots(2, 2, figsize=(10, 6.6), sharey=True)
    for ax, e in zip(axs.ravel(), ESC):
        g = v[v['escenario'] == e]
        total = g['valor_propio'].sum()
        ax.plot(g['componente'], g['pct'], color=COLOR[e], lw=2, marker='o', ms=4, label='Observado')
        ax.plot(g['componente'], 100 * g['referencia_ruido_p95'] / total, color=GRIS, lw=1.5, ls='--', label='Percentil 95 con variables permutadas')
        n = int(g['supera_ruido'].cumprod().sum())
        ax.set_title(f'{NOMBRE[e]}: {n} ejes sobre la referencia', loc='left')
        ax.set_xlabel('Componente')
        ax.set_ylabel('% de la inercia total')
        rejilla(ax)
    axs[0, 0].legend(loc='upper right')
    titular(fig, 'Gráfico de sedimentación: un primer eje claro y una caída gradual', 'La referencia es descriptiva: no selecciona componentes.')
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    return fig


def f02_acumulada():
    v = leer('valores_propios.csv')
    fig, ax = plt.subplots(figsize=(9, 5.2))
    for u in (50, 60, 70, 80, 90):
        ax.axhline(u, color=REJILLA, lw=0.9, zorder=0)
    for e in ESC:
        g = v[v['escenario'] == e]
        ax.plot(g['componente'], g['pct_acumulado'], color=COLOR[e], ls=LINEA[e], lw=2, label=NOMBRE[e])
    for k in (2, 3, 5, 8, 12, 16, 20):
        ax.axvline(k, color=REJILLA, lw=0.6, ls=':', zorder=0)
    ax.set_xticks([1, 2, 3, 5, 8, 12, 16, 20, 25, 30, 35, 39])
    ax.set_xlabel('Número de componentes (líneas punteadas: candidatos)')
    ax.set_ylabel('% acumulado de la inercia')
    ax.set_ylim(0, 102)
    ax.legend(loc='lower right')
    ax.set_title('Inercia acumulada: FAMD reparte su inercia en más ejes', loc='left', fontsize=12)
    fig.tight_layout()
    return fig


def f03_cargas(e, ejes=5):
    c = leer('cargas_columnas.csv')
    c = c[(c['escenario'] == e) & (c['componente'] <= ejes)]
    orden = c[c['componente'] == 1].sort_values(['bloque', 'columna'])['columna'].tolist()
    M = c.pivot(index='columna', columns='componente', values='correlacion').loc[orden]
    fig, ax = plt.subplots(figsize=(7.6, max(5.5, 0.21 * len(M))))
    im = ax.imshow(M.to_numpy(), cmap=DIVERGENTE, vmin=-0.9, vmax=0.9, aspect='auto')
    ax.set_xticks(range(ejes), [f'C{i + 1}' for i in range(ejes)])
    ax.set_yticks(range(len(M)), M.index, fontsize=7.5)
    ax.xaxis.tick_top()
    ax.spines[:].set_visible(False)
    bloques = c[c['componente'] == 1].set_index('columna').loc[orden, 'bloque'].to_numpy()
    for i in np.flatnonzero(bloques[1:] != bloques[:-1]):
        ax.axhline(i + 0.5, color='white', lw=2.5)
    for (i, j), x in np.ndenumerate(M.to_numpy()):
        if abs(x) >= 0.3:
            ax.text(j, i, f'{x:.2f}'.replace('.', ','), ha='center', va='center', fontsize=7, color='white' if abs(x) > 0.6 else TINTA)
    fig.colorbar(im, ax=ax, shrink=0.45, label='Correlación entre columna y eje', pad=0.02)
    ax.set_title(f'{NOMBRE[e]}: correlación de cada columna con los cinco primeros ejes', loc='left', pad=22, fontsize=10)
    fig.tight_layout()
    return fig


def f04_contribucion(e, ejes=3, top=10):
    c = leer('contribucion_variables.csv')
    c = c[c['escenario'] == e]
    n_var = c['variable'].nunique()
    fig, axs = plt.subplots(1, ejes, figsize=(11, 3.9), sharex=True)
    for a, ax in enumerate(axs):
        g = c[c['componente'] == a + 1].sort_values('contribucion_pct', ascending=False).head(top)[::-1]
        ax.barh(g['variable'], g['contribucion_pct'], color=COLOR[e], height=0.55)
        ax.axvline(100 / n_var, color=GRIS, ls='--', lw=1)
        ax.set_title(f'Eje {a + 1}', loc='left')
        ax.tick_params(axis='y', labelsize=7.5, length=0)
        ax.set_xlabel('% del eje')
        rejilla(ax, 'x')
    titular(fig, f'{NOMBRE[e]}: variables que más contribuyen', f'Línea gris: reparto uniforme entre {n_var} variables.')
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    return fig


def f05_bloques(ejes=8):
    b = leer('contribucion_bloques.csv')
    fig, axs = plt.subplots(2, 2, figsize=(11, 6.8))
    for ax, e in zip(axs.ravel(), ESC):
        g = b[(b['escenario'] == e) & (b['componente'] <= ejes)]
        M = g.pivot(index='bloque', columns='componente', values='contribucion_pct')
        M = M.reindex(g[g['componente'] == 1]['bloque'])
        ax.imshow(M.to_numpy(), cmap=SECUENCIAL, vmin=0, vmax=100, aspect='auto')
        ax.set_xticks(range(ejes), [f'C{i + 1}' for i in range(ejes)])
        ax.set_yticks(range(len(M)), [CORTO.get(x, x) for x in M.index], fontsize=8)
        ax.tick_params(length=0)
        ax.spines[:].set_visible(False)
        for (i, j), x in np.ndenumerate(M.to_numpy()):
            ax.text(j, i, f'{x:.0f}', ha='center', va='center', fontsize=7.5, color='white' if x > 45 else TINTA)
        ax.set_title(NOMBRE[e], loc='left')
    titular(fig, 'Contribución de los bloques del cuestionario a cada eje (% del eje)', 'Actividad física domina el eje 1; Alimentación crece desde el eje 3.')
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    return fig


def f06_proyeccion():
    v = leer('valores_propios.csv')
    fig, axs = plt.subplots(2, 2, figsize=(10, 7.2))
    for ax, e in zip(axs.ravel(), ESC):
        c = pd.read_csv(BASE / 'coordenadas' / e / 'coordenadas_k02.csv')
        g = v[v['escenario'] == e]
        ax.scatter(c['C1'], c['C2'], s=11, color=COLOR[e], alpha=0.5, linewidths=0)
        ax.axhline(0, color=REJILLA, lw=0.8, zorder=0)
        ax.axvline(0, color=REJILLA, lw=0.8, zorder=0)
        ax.set_xlabel(f'Eje 1 ({g["pct"].iloc[0]:.1f} %)'.replace('.', ','))
        ax.set_ylabel(f'Eje 2 ({g["pct"].iloc[1]:.1f} %)'.replace('.', ','))
        ax.set_title(NOMBRE[e], loc='left')
    titular(fig, 'Proyección de las 529 participantes en los dos primeros ejes', 'Solo describe el 11 % al 14 % de la inercia. No prueba que existan clústeres, y los puntos no están coloreados por ninguna variable clínica.')
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    return fig


def f07_imc():
    i = leer('imc_por_eje.csv')
    s = leer('comparacion_subespacios.csv')
    fig, axs = plt.subplots(1, 2, figsize=(11, 4.2))
    ax = axs[0]
    for e in ('P1', 'F1'):
        g = i[(i['variante'] == 'principal') & (i['base'] == e)]
        ax.plot(g['componente'], g['contribucion_pct'], color=COLOR[e], lw=2, marker='o', ms=3, label=NOMBRE[e])
    ax.set_xlabel('Componente')
    ax.set_ylabel('Contribución del IMC al eje (%)')
    ax.axvline(20, color=GRIS, ls=':', lw=1)
    ax.text(19.6, 30, 'Último candidato (20)', ha='right', fontsize=8.5, color=TINTA2)
    ax.set_title('El IMC casi no aporta a los ejes candidatos', loc='left')
    ax.legend(loc='upper left')
    rejilla(ax)
    ax = axs[1]
    for c, e, n in (('Con y sin IMC, PCA', 'P1', 'PCA: P1 frente a P2'), ('Con y sin IMC, FAMD', 'F1', 'FAMD: F1 frente a F2')):
        g = s[s['comparacion'] == c]
        ax.plot(g['k'], g['similitud_subespacio'], color=COLOR[e], lw=2, marker='o', ms=4, label=n)
    ax.set_ylim(0.9, 1.005)
    ax.set_xticks([2, 3, 5, 8, 12, 16, 20])
    ax.set_xlabel('Número de componentes')
    ax.set_ylabel('Similitud de subespacio (1 = igual)')
    ax.set_title('Con y sin IMC, las coordenadas casi coinciden', loc='left')
    ax.legend(loc='lower left')
    rejilla(ax)
    fig.tight_layout()
    return fig


def f08_metodos():
    u = leer('componentes_para_umbral.csv').set_index('id')
    s = leer('comparacion_subespacios.csv')
    fig, axs = plt.subplots(1, 2, figsize=(11, 4.2))
    ax = axs[0]
    umb = [50, 60, 70, 80, 90]
    for e in ESC:
        ax.plot(umb, [u.loc[e, f'c{x}'] for x in umb], color=COLOR[e], ls=LINEA[e], lw=2, marker='o', ms=4, label=NOMBRE[e])
    ax.set_xticks(umb)
    ax.set_xlabel('% de inercia acumulada (referencia descriptiva)')
    ax.set_ylabel('Componentes necesarios')
    ax.set_title('Componentes para cada nivel de inercia', loc='left')
    ax.legend(loc='upper left')
    rejilla(ax)
    ax = axs[1]
    for c, ls, n in (('PCA frente a FAMD, con IMC', '-', 'Con IMC: P1 frente a F1'), ('PCA frente a FAMD, sin IMC', '--', 'Sin IMC: P2 frente a F2')):
        g = s[s['comparacion'] == c]
        ax.plot(g['k'], g['similitud_subespacio'], color=TINTA2, ls=ls, lw=2, marker='o', ms=4, label=n)
    ax.set_ylim(0.6, 1)
    ax.set_xticks([2, 3, 5, 8, 12, 16, 20])
    ax.set_xlabel('Número de componentes')
    ax.set_ylabel('Similitud de subespacio (1 = igual)')
    ax.set_title('PCA y FAMD se parecen más en los primeros ejes', loc='left')
    ax.legend(loc='lower left')
    rejilla(ax)
    fig.tight_layout()
    return fig


def f09_orden(e='F1'):
    o = leer('famd_orden_niveles.csv')
    b = leer('famd_baricentros.csv', dtype={'nivel': str})
    vs = list(dict.fromkeys(o['variable']))
    fig, axs = plt.subplots(1, 5, figsize=(13, 3.5))
    for ax, v in zip(axs, vs):
        p = o[(o['escenario'] == e) & (o['variable'] == v) & o['eje_principal']].iloc[0]
        g = b[(b['escenario'] == e) & (b['variable'] == v) & (b['tipo_nivel'] == 'grupo activo') & (b['componente'] == p['componente'])]
        ax.plot(range(len(g)), g['baricentro'], color=NARANJA, lw=2, marker='o', ms=6)
        ax.set_xticks(range(len(g)), [x.replace(' + ', '+') for x in g['nivel']], fontsize=7.5)
        ax.axhline(0, color=REJILLA, lw=0.8, zorder=0)
        mono = 'monótono' if p['monotono_grupos'] else 'no monótono'
        nombre = {'frecuencia_aerobico': 'Frecuencia aeróbico', 'frecuencia_bajo_impacto': 'Frecuencia bajo impacto', 'frecuencia_fuerza': 'Frecuencia fuerza', 'cantidad_personas_cuida': 'Personas que cuida', 'tabaco_frecuencia': 'Tabaco'}[v]
        ax.set_title(nombre, loc='left', fontsize=9)
        ax.set_xlabel(f'Nivel (orden del instrumento)\nEje {int(p["componente"])}; η² = {p["eta2"]:.2f}; {mono}'.replace('0.', '0,'), fontsize=7.5)
    axs[0].set_ylabel('Baricentro en el eje')
    titular(fig, f'{NOMBRE[e]}: posición de los niveles de las ordinales categóricas en el eje principal de cada una', None)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    return fig


def f10_sensibilidades():
    s = leer('sens_similitud.csv')
    ids = list(dict.fromkeys(s['sensibilidad']))
    ks = [2, 3, 5, 8, 12, 16, 20]
    fig, axs = plt.subplots(1, 2, figsize=(11, 4.6))
    for ax, e in zip(axs, ('P1', 'F1')):
        M = s[s['base'] == e].pivot(index='sensibilidad', columns='k', values='similitud_subespacio').reindex(index=[i for i in ids if i in set(s[s['base'] == e]['sensibilidad'])], columns=ks)
        ax.imshow(M.to_numpy(), cmap=SECUENCIAL, vmin=0, vmax=1, aspect='auto')
        ax.set_xticks(range(len(ks)), ks)
        ax.set_yticks(range(len(M)), M.index, fontsize=8)
        ax.tick_params(length=0)
        ax.spines[:].set_visible(False)
        ax.set_xlabel('Número de componentes')
        for (i, j), x in np.ndenumerate(M.to_numpy()):
            ax.text(j, i, f'{x:.2f}'.replace('.', ','), ha='center', va='center', fontsize=7.5, color='white' if x > 0.6 else TINTA, fontweight='bold' if (x < 0.8 and ks[j] in (5, 8, 12)) else 'normal')
        ax.set_title(f'Base {NOMBRE[e]}', loc='left')
    titular(fig, 'Similitud de subespacio entre cada sensibilidad y su base', 'Negrita: bajo 0,80 en k = 5, 8 o 12, el umbral fijado para revisión. Compara filas, no varianza absoluta.')
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    return fig


FIGURAS = {'f01_sedimentacion': f01_sedimentacion, 'f02_inercia_acumulada': f02_acumulada, 'f05_contribucion_bloques': f05_bloques, 'f06_proyeccion_2d': f06_proyeccion, 'f07_con_sin_imc': f07_imc,
           'f08_comparacion_pca_famd': f08_metodos, 'f09_orden_niveles_F1': f09_orden, 'f10_sensibilidades': f10_sensibilidades,
           **{f'f03_cargas_{e}': (lambda e=e: f03_cargas(e)) for e in ESC}, **{f'f04_contribucion_variables_{e}': (lambda e=e: f04_contribucion(e)) for e in ESC}}


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    for n, f in FIGURAS.items():
        fig = f()
        fig.savefig(FIG / f'{n}.png', metadata={'Software': None})
        plt.close(fig)
    print(len(FIGURAS), 'figuras')


if __name__ == '__main__':
    main()
