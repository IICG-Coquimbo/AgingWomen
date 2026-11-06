"""
Fase 37B: gráficos de síntesis, leídos siempre de las tablas guardadas. No ajusta algoritmos.

Uso, desde analisis/: python fase37/37B_clustering/scripts/graficos_37b.py
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
from matplotlib.colors import LinearSegmentedColormap, ListedColormap, BoundaryNorm  # noqa: E402

BASE = Path(__file__).resolve().parents[1]
A37 = BASE.parent / '37A_reduccion'
FIG = BASE / 'figuras'
AZUL, NARANJA, GRIS, TINTA, TINTA2, REJILLA = '#2a78d6', '#eb6834', '#8a8983', '#0b0b0b', '#52514e', '#e4e3df'
CATEGORICA = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#6250d6', '#8a8983']
COMP = [2, 3, 5, 8, 12, 16, 20]
K = [2, 3, 4, 5, 6, 7, 8]
ESP = ['P1', 'P2', 'F1', 'F2']
NOMBRE = {'P1': 'PCA con IMC (P1)', 'P2': 'PCA sin IMC (P2)', 'F1': 'FAMD con IMC (F1)', 'F2': 'FAMD sin IMC (F2)', 'R0P1': 'Sin reducción, con IMC', 'R0P2': 'Sin reducción, sin IMC'}
ALG = {'km': 'K-means', 'ward': 'Aglomerativo (Ward)'}
SECUENCIAL = LinearSegmentedColormap.from_list('azul', ['#f4f8fd', '#9cc3ef', '#2a78d6', '#0f3e7a'])
RAMPA = ['#c3d9f4', '#9cc3ef', '#6ba5e7', '#3f8ade', '#2a78d6', '#1b5aa8', '#0f3e7a']
TRAMOS = ListedColormap(['#f7d9cc', '#f4f1e8', '#9cc3ef'])
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.titlesize': 10, 'axes.titleweight': 'bold', 'axes.edgecolor': '#bdbcb6', 'axes.labelcolor': TINTA2, 'xtick.color': TINTA2, 'ytick.color': TINTA2,
                     'axes.spines.top': False, 'axes.spines.right': False, 'figure.dpi': 110, 'savefig.dpi': 170, 'savefig.bbox': 'tight', 'figure.facecolor': 'white'})


def tabla():
    return pd.read_csv(BASE / 'resultados' / 'tabla_completa_configuraciones.csv', encoding='utf-8')


def titulo(fig, t, sub=None, y=1.0):
    fig.suptitle(t, x=0.01, y=y, ha='left', fontsize=12, fontweight='bold')
    if sub:
        fig.text(0.01, y - 0.045, sub, ha='left', va='top', fontsize=8.5, color=TINTA2)


def f01_silueta():
    t = tabla()
    fig, axs = plt.subplots(2, 4, figsize=(12.5, 5.8), sharex=True, sharey=True)
    for i, a in enumerate(('km', 'ward')):
        for j, e in enumerate(ESP):
            ax = axs[i, j]
            for n, c in enumerate(COMP):
                x = t[(t['espacio'] == e) & (t['algoritmo'] == a) & (t['componentes'] == c)].sort_values('k')
                ax.plot(x['k'], x['silueta'], color=RAMPA[n], lw=1.8, marker='o', ms=3, label=f'{c} ejes')
            r = t[(t['espacio'] == 'R0' + e) & (t['algoritmo'] == a)].sort_values('k') if e[0] == 'P' else None
            if r is not None:
                ax.plot(r['k'], r['silueta'], color=GRIS, lw=1.6, ls='--', label='Sin reducción')
            ax.set_title(f'{ALG[a]}: {e}', loc='left', fontsize=9)
            ax.grid(True, axis='y', color=REJILLA, lw=0.7)
            if i == 1:
                ax.set_xlabel('Número de grupos')
            if j == 0:
                ax.set_ylabel('Silueta media')
    h, l = axs[0, 0].get_legend_handles_labels()
    fig.legend(h, l, loc='lower center', ncol=8, frameon=False, bbox_to_anchor=(0.5, -0.04))
    titulo(fig, 'Silueta media por número de grupos', 'Solo comparable dentro de cada panel: los espacios tienen distinta dimensión y ponderación.', y=1.03)
    fig.tight_layout()
    return fig


def _mapa(col, cmap=SECUENCIAL, decimales=2, propio=True, norm=None, tit='', sub='', etiqueta=''):
    t = tabla()
    fig, axs = plt.subplots(2, 5, figsize=(14.5, 6.0), gridspec_kw={'width_ratios': [1, 1, 1, 1, 1], 'height_ratios': [1, 1]})
    for i, a in enumerate(('km', 'ward')):
        for j, e in enumerate(ESP + ['R0']):
            ax = axs[i, j]
            if e == 'R0':
                m = pd.concat([t[(t['espacio'] == x) & (t['algoritmo'] == a)].set_index('k')[col].rename(x) for x in ('R0P1', 'R0P2')], axis=1).T
                filas = ['Con IMC', 'Sin IMC']
                ax.set_title(f'{ALG[a]}: sin reducción', loc='left', fontsize=9)
            else:
                m = t[(t['espacio'] == e) & (t['algoritmo'] == a)].pivot(index='componentes', columns='k', values=col)
                filas = m.index.tolist()
                ax.set_title(f'{ALG[a]}: {e}', loc='left', fontsize=9)
            v = m.to_numpy(dtype=float)
            kw = {'norm': norm} if norm is not None else ({'vmin': np.nanmin(v), 'vmax': np.nanmax(v)} if propio else {})
            im = ax.imshow(v, cmap=cmap, aspect='auto', **kw)
            ax.set_xticks(range(len(m.columns)), m.columns)
            ax.set_yticks(range(len(filas)), filas, fontsize=8)
            ax.tick_params(length=0)
            for s in ax.spines.values():
                s.set_visible(False)
            for y in range(v.shape[0]):
                for x in range(v.shape[1]):
                    claro = im.cmap(im.norm(v[y, x]))
                    lum = 0.2126 * claro[0] + 0.7152 * claro[1] + 0.0722 * claro[2]
                    ax.text(x, y, f'{v[y, x]:.{decimales}f}'.replace('.', ','), ha='center', va='center', fontsize=6.3, color='white' if lum < 0.45 else TINTA)
            if i == 1:
                ax.set_xlabel('Número de grupos')
            if j == 0:
                ax.set_ylabel(etiqueta or 'Componentes')
    titulo(fig, tit, sub, y=1.04)
    fig.tight_layout()
    return fig


def f02_davies_bouldin():
    return _mapa('davies_bouldin', tit='Davies-Bouldin por configuración', sub='Menor suele ser preferible. El color se normaliza en cada panel: los espacios no son comparables entre sí. Cada fila es una cantidad de componentes.')


def f03_calinski():
    return _mapa('calinski_harabasz', decimales=0, tit='Calinski-Harabasz por configuración', sub='Mayor suele ser preferible. El color se normaliza en cada panel: los espacios no son comparables entre sí. Cada fila es una cantidad de componentes.')


def f04_tamanos():
    t = tabla()
    fig, axs = plt.subplots(1, 3, figsize=(12.5, 3.8))
    ax = axs[0]
    for a, col in (('km', AZUL), ('ward', NARANJA)):
        x = t[t['algoritmo'] == a].groupby('k')['tam_min_pct'].min()
        ax.plot(x.index, x.to_numpy(), color=col, lw=2, marker='o', ms=4, label=ALG[a])
    ax.axhline(100 * 27 / 529, color=GRIS, ls=':', lw=1.2)
    ax.text(8, 100 * 27 / 529 + 0.7, 'Umbral orientativo (27)', fontsize=7.5, color=TINTA2, ha='right')
    ax.set(title='Grupo más pequeño, peor caso', xlabel='Número de grupos', ylabel='% de las participantes')
    ax.legend(frameon=False, fontsize=8)
    ax.grid(True, axis='y', color=REJILLA, lw=0.7)
    ax = axs[1]
    ax.set_axisbelow(True)
    for d, (a, col) in enumerate((('km', AZUL), ('ward', NARANJA))):
        x = t[t['algoritmo'] == a].groupby('k')['grupos_pequenos'].apply(lambda v: 100 * (v > 0).mean())
        ax.bar(x.index + (d - 0.5) * 0.36, x.to_numpy(), width=0.34, color=col, label=ALG[a])
    ax.set(title='Configuraciones con algún grupo bajo 27', xlabel='Número de grupos', ylabel='% de las configuraciones')
    ax.grid(True, axis='y', color=REJILLA, lw=0.7)
    ax.legend(frameon=False, fontsize=8)
    ax = axs[2]
    for d, (a, col) in enumerate((('km', AZUL), ('ward', NARANJA))):
        datos = [t[(t['algoritmo'] == a) & (t['k'] == k)]['equilibrio'] for k in K]
        ax.boxplot(datos, positions=[k + (d - 0.5) * 0.36 for k in K], widths=0.3, patch_artist=True, showfliers=False, boxprops={'facecolor': col, 'edgecolor': col}, medianprops={'color': 'white'}, whiskerprops={'color': col}, capprops={'color': col})
    ax.set_xticks(K, K)
    ax.set(title='Equilibrio de los tamaños', xlabel='Número de grupos', ylabel='Entropía normalizada (1 = iguales)')
    ax.grid(True, axis='y', color=REJILLA, lw=0.7)
    fig.tight_layout()
    return fig


def representativas():
    """Ejemplos para las figuras ilustrativas: siempre 5 ejes y k = 3, para no elegirlos por sus resultados. No es una selección."""
    return ['P1_c05_km_k3', 'P1_c05_ward_k3', 'F1_c05_km_k3', 'F1_c05_ward_k3']


def _partes(c):
    e, comp, a, k = c.split('_')
    return e, int(comp[1:]), a, int(k[1:])


def f05_siluetas():
    from sklearn.metrics import silhouette_samples
    et = pd.read_csv(BASE / 'etiquetas' / 'etiquetas_principales.csv', dtype={'participante_id': str}).set_index('participante_id')
    fig, axs = plt.subplots(1, 4, figsize=(13, 4.4), sharex=True)
    for ax, c in zip(axs, representativas()):
        e, comp, a, k = _partes(c)
        X = pd.read_csv(A37 / 'coordenadas' / e / f'coordenadas_k{comp:02d}.csv', dtype={'participante_id': str}).set_index('participante_id').to_numpy()
        l = et[c].to_numpy()
        s = silhouette_samples(X, l)
        y = 0
        for g in range(k):
            v = np.sort(s[l == g])
            ax.fill_betweenx(np.arange(y, y + len(v)), 0, v, color=CATEGORICA[g], lw=0)
            ax.text(ax.get_xlim()[0], y + len(v) / 2, f'{g} (n={len(v)})', fontsize=7, va='center', ha='right', color=TINTA2)
            y += len(v) + 8
        ax.axvline(s.mean(), color=TINTA, ls='--', lw=1)
        ax.axvline(0, color=GRIS, lw=0.8)
        ax.set_yticks([])
        ax.set_xlabel('Silueta individual')
        ax.set_title(f'{ALG[a]}: {e}, {comp} ejes, k = {k}', loc='left', fontsize=8.5)
        ax.spines['left'].set_visible(False)
    titulo(fig, 'Silueta individual por grupo en configuraciones de ejemplo', 'Ejemplos fijos (5 ejes, k = 3), no elegidos por sus resultados. No es una selección. La línea discontinua es la media. El número de grupo es solo un nombre.', y=1.08)
    fig.tight_layout()
    return fig


def f06_estabilidad():
    norm = BoundaryNorm([-1, 0.65, 0.80, 1.0001], 3)
    return _mapa('ari_entre_media', cmap=TRAMOS, norm=norm, tit='Estabilidad: ARI medio entre remuestreos', sub='Naranja: bajo 0,65. Crema: de 0,65 a 0,80. Azul: sobre 0,80. Tramos de trabajo, no estándares. Cada fila es una cantidad de componentes.')


def f07_km_ward():
    t = tabla()
    km = t[t['algoritmo'] == 'km'].assign(clave=lambda d: d['config'].str.replace('_km_', '_')).set_index('clave')
    wa = t[t['algoritmo'] == 'ward'].assign(clave=lambda d: d['config'].str.replace('_ward_', '_')).set_index('clave').loc[km.index]
    cmp_ = pd.read_csv(BASE / 'resultados' / 'comparaciones_ari.csv', encoding='utf-8')
    x = cmp_[cmp_['comparacion'] == 'K-means y aglomerativo']
    fig, axs = plt.subplots(1, 3, figsize=(12.5, 4))
    for ax, col, nom in ((axs[0], 'silueta', 'Silueta media'), (axs[1], 'ari_entre_media', 'ARI medio entre remuestreos')):
        for m, c in (('PCA', AZUL), ('FAMD', NARANJA), ('Sin reducción', GRIS)):
            s = km['metodo'] == m
            ax.scatter(km.loc[s, col], wa.loc[s, col], s=14, color=c, alpha=0.75, lw=0, label=m)
        lim = [min(km[col].min(), wa[col].min()), max(km[col].max(), wa[col].max())]
        ax.plot(lim, lim, color=GRIS, lw=1, ls=':')
        ax.set(title=nom, xlabel='K-means', ylabel='Aglomerativo')
        ax.grid(True, color=REJILLA, lw=0.6)
        ax.legend(frameon=False, fontsize=8)
    ax = axs[2]
    for m, c, pat in (('PCA', AZUL, 'P'), ('FAMD', NARANJA, 'F')):
        y = x[x['a'].str.startswith(pat)].groupby('k')['ari_529'].median()
        ax.plot(y.index, y.to_numpy(), color=c, lw=2, marker='o', ms=4, label=m)
    ax.set(title='¿Forman los mismos grupos?', xlabel='Número de grupos', ylabel='ARI mediano entre ambos algoritmos', ylim=(0, 1))
    ax.grid(True, axis='y', color=REJILLA, lw=0.7)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    return fig


def f08_nula():
    n = pd.read_csv(BASE / 'referencia_nula' / 'comparacion_por_configuracion.csv', encoding='utf-8')
    t = tabla()[['config', 'espacio', 'componentes', 'algoritmo', 'k']].merge(n, on='config')
    fig, axs = plt.subplots(2, 4, figsize=(13, 5.8), sharex=True)
    paneles = [('P1', 'km'), ('P1', 'ward'), ('F1', 'km'), ('F1', 'ward')]
    for i, (col, nom) in enumerate((('silueta', 'Silueta media'), ('ari_entre_media', 'ARI medio entre remuestreos'))):
        for j, (e, a) in enumerate(paneles):
            ax = axs[i, j]
            x = t[(t['espacio'] == e) & (t['algoritmo'] == a) & (t['componentes'] == 5)].sort_values('k')
            ax.fill_between(x['k'], x[f'{col}_nula_min'], x[f'{col}_nula_max'], color=GRIS, alpha=0.3, lw=0, label='Rango de las 20 réplicas')
            ax.plot(x['k'], x[f'{col}_nula_media'], color=GRIS, lw=1.2, ls='--', label='Media de las réplicas')
            ax.plot(x['k'], x[f'{col}_obs'], color=AZUL if e[0] == 'P' else NARANJA, lw=2, marker='o', ms=4, label='Observado')
            ax.set_title(f'{ALG[a]}: {e}, 5 ejes', loc='left', fontsize=9)
            ax.grid(True, axis='y', color=REJILLA, lw=0.7)
            if j == 0:
                ax.set_ylabel(nom)
            if i == 1:
                ax.set_xlabel('Número de grupos')
            if j == 3 and i == 0:
                ax.legend(frameon=False, fontsize=7.5)
    titulo(fig, 'Observado frente a la referencia nula, con 5 ejes', 'La nula rompe las asociaciones entre variables. Superarla no prueba que existan grupos naturales.', y=1.04)
    fig.tight_layout()
    return fig


def f08b_supera():
    t = tabla()
    fig, axs = plt.subplots(2, 4, figsize=(13, 5.4))
    cm = ListedColormap(['#f1f1ee', '#9cc3ef', '#f3b79e', '#2a78d6'])
    for i, a in enumerate(('km', 'ward')):
        for j, e in enumerate(ESP):
            ax = axs[i, j]
            x = t[(t['espacio'] == e) & (t['algoritmo'] == a)]
            s = x.pivot(index='componentes', columns='k', values='silueta_supera_todas').astype(bool).to_numpy().astype(int)
            r = x.pivot(index='componentes', columns='k', values='ari_entre_media_supera_todas').astype(bool).to_numpy().astype(int)
            ax.imshow(s + 2 * r, cmap=cm, vmin=0, vmax=3, aspect='auto')
            ax.set_xticks(range(7), K)
            ax.set_yticks(range(7), COMP, fontsize=8)
            ax.tick_params(length=0)
            for sp in ax.spines.values():
                sp.set_visible(False)
            for y in range(7):
                for z in range(7):
                    ax.text(z, y, {0: '', 1: 'S', 2: 'E', 3: 'S+E'}[int(s[y, z] + 2 * r[y, z])], ha='center', va='center', fontsize=6.5, color='white' if s[y, z] + 2 * r[y, z] == 3 else TINTA)
            ax.set_title(f'{ALG[a]}: {e}', loc='left', fontsize=9)
            if i == 1:
                ax.set_xlabel('Número de grupos')
            if j == 0:
                ax.set_ylabel('Componentes')
    titulo(fig, '¿Qué configuraciones superan a las 20 réplicas nulas?', 'S: silueta. E: ARI entre remuestreos. S+E: ambas. Vacío: ninguna. Con 420 configuraciones, unas 20 superarían a las réplicas por azar.', y=1.05)
    fig.tight_layout()
    return fig


def f09_imc():
    c = pd.read_csv(BASE / 'resultados' / 'comparaciones_ari.csv', encoding='utf-8')
    fig, axs = plt.subplots(2, 2, figsize=(10.5, 6.6))
    norm = BoundaryNorm([-1, 0.65, 0.80, 1.0001], 3)
    for i, a in enumerate(('km', 'ward')):
        for j, (nom, e) in enumerate((('Con y sin IMC, PCA', 'P1 y P2'), ('Con y sin IMC, FAMD', 'F1 y F2'))):
            ax = axs[i, j]
            x = c[(c['comparacion'] == nom) & (c['algoritmo'] == a)].pivot(index='componentes', columns='k', values='ari_529')
            v = x.to_numpy()
            ax.imshow(v, cmap=TRAMOS, norm=norm, aspect='auto')
            ax.set_xticks(range(7), K)
            ax.set_yticks(range(7), COMP, fontsize=8)
            ax.tick_params(length=0)
            for sp in ax.spines.values():
                sp.set_visible(False)
            for y in range(7):
                for z in range(7):
                    ax.text(z, y, f'{v[y, z]:.2f}'.replace('.', ','), ha='center', va='center', fontsize=7, color=TINTA)
            ax.set_title(f'{ALG[a]}: {e}', loc='left', fontsize=9)
            if i == 1:
                ax.set_xlabel('Número de grupos')
            if j == 0:
                ax.set_ylabel('Componentes')
    titulo(fig, 'Acuerdo entre las versiones con y sin IMC (ARI en las 529)', 'Naranja: bajo 0,65. Crema: de 0,65 a 0,80. Azul: sobre 0,80. Un acuerdo alto es esperable por el peso reducido del IMC y no prueba estabilidad.', y=1.04)
    fig.tight_layout()
    return fig


def f10_proyecciones():
    et = pd.read_csv(BASE / 'etiquetas' / 'etiquetas_principales.csv', dtype={'participante_id': str}).set_index('participante_id')
    fig, axs = plt.subplots(2, 2, figsize=(10.5, 7.2))
    for ax, c in zip(axs.ravel(), representativas()):
        e, comp, a, k = _partes(c)
        F = pd.read_csv(A37 / 'coordenadas' / e / 'coordenadas_k02.csv', dtype={'participante_id': str}).set_index('participante_id')
        l = et[c].to_numpy()
        for g in range(k):
            s = l == g
            ax.scatter(F.loc[s, 'C1'], F.loc[s, 'C2'], s=11, color=CATEGORICA[g], alpha=0.8, lw=0, label=f'Grupo {g} (n={s.sum()})')
        ax.set_title(f'{ALG[a]}: {e}, formado con {comp} ejes, k = {k}', loc='left', fontsize=9)
        ax.set(xlabel='Eje 1', ylabel='Eje 2')
        ax.legend(frameon=False, fontsize=7.5, ncol=k, loc='upper center', bbox_to_anchor=(0.5, -0.13))
        ax.grid(True, color=REJILLA, lw=0.5)
    titulo(fig, 'Proyecciones ilustrativas de grupos de ejemplo', 'Ilustrativas: estos grupos se formaron con 5 ejes, por lo que aquí, en 2 ejes, pueden verse superpuestos. Ejemplos fijos, no una selección. El número de grupo es solo un nombre.', y=1.04)
    fig.tight_layout()
    return fig


def f11_sensibilidades():
    s = pd.read_csv(BASE / 'sensibilidades' / 'comparacion_sensibilidades.csv', encoding='utf-8')
    orden = ['S-ORD', 'S-FAMD', 'S-RARA', 'S-TRA', 'S-CUI', 'S-EJE', 'S-EDAD', 'S-SOLAPE', 'S-BLOQUE', 'S-BLOQUE-SA']
    fig, axs = plt.subplots(1, 2, figsize=(11, 4.8), sharey=True)
    norm = BoundaryNorm([-1, 0.65, 0.80, 1.0001], 3)
    for ax, a in zip(axs, ('km', 'ward')):
        v = s[s['algoritmo'] == a].pivot_table(index='sensibilidad', columns='k', values='ari_ajuste', aggfunc='median').reindex(orden).to_numpy()
        ax.imshow(v, cmap=TRAMOS, norm=norm, aspect='auto')
        ax.set_xticks(range(7), K)
        ax.set_yticks(range(len(orden)), orden, fontsize=8)
        ax.tick_params(length=0)
        for sp in ax.spines.values():
            sp.set_visible(False)
        for y in range(v.shape[0]):
            for z in range(7):
                ax.text(z, y, f'{v[y, z]:.2f}'.replace('.', ','), ha='center', va='center', fontsize=7, color=TINTA)
        ax.axhline(7.5, color=TINTA2, lw=1)
        ax.set_title(ALG[a], loc='left', fontsize=10)
        ax.set_xlabel('Número de grupos')
    titulo(fig, 'Acuerdo con la configuración base: ARI mediano en filas de ajuste', 'Mediana de todas las combinaciones de componentes y escenarios. Bajo la línea, variantes de ponderación: son otra pregunta, no un fallo de robustez.', y=1.05)
    fig.tight_layout()
    return fig


def f12_asignacion():
    t = pd.read_csv(BASE / 'prototipos' / 'evaluacion_asignacion.csv', encoding='utf-8')
    fig, axs = plt.subplots(1, 2, figsize=(10.5, 3.8))
    ax = axs[0]
    w = t[t['algoritmo'] == 'ward']
    ax.boxplot([w[w['k'] == k]['acuerdo_prototipo_pct'] for k in K], positions=K, widths=0.5, patch_artist=True, showfliers=True, flierprops={'markersize': 2.5, 'markeredgecolor': NARANJA}, boxprops={'facecolor': NARANJA, 'edgecolor': NARANJA}, medianprops={'color': 'white'}, whiskerprops={'color': NARANJA}, capprops={'color': NARANJA})
    ax.set_xticks(K, K)
    ax.set(title='Aglomerativo: centroide más cercano frente a sus etiquetas', xlabel='Número de grupos', ylabel='Coincidencia (%)')
    ax.title.set_fontsize(9.5)
    ax.grid(True, axis='y', color=REJILLA, lw=0.7)
    ax = axs[1]
    for a, col in (('km', AZUL), ('ward', NARANJA)):
        y = t[t['algoritmo'] == a].groupby('k')['ari_fuera_media'].median()
        ax.plot(y.index, y.to_numpy(), color=col, lw=2, marker='o', ms=4, label=ALG[a])
    ax.set(title='Fuera de muestra: participantes no usadas en el ajuste', xlabel='Número de grupos', ylabel='ARI mediano frente al modelo principal', ylim=(0, 1))
    ax.title.set_fontsize(9.5)
    ax.legend(frameon=False, fontsize=8)
    ax.grid(True, axis='y', color=REJILLA, lw=0.7)
    fig.tight_layout()
    return fig


FIGURAS = {'f01_silueta': f01_silueta, 'f02_davies_bouldin': f02_davies_bouldin, 'f03_calinski_harabasz': f03_calinski, 'f04_tamanos': f04_tamanos, 'f05_siluetas_individuales': f05_siluetas, 'f06_estabilidad': f06_estabilidad, 'f07_kmeans_aglomerativo': f07_km_ward,
           'f08_referencia_nula': f08_nula, 'f08b_supera_nula': f08b_supera, 'f09_con_sin_imc': f09_imc, 'f10_proyecciones': f10_proyecciones, 'f11_sensibilidades': f11_sensibilidades, 'f12_asignacion': f12_asignacion}


def main():
    FIG.mkdir(exist_ok=True)
    for n, f in FIGURAS.items():
        fig = f()
        fig.savefig(FIG / f'{n}.png')
        plt.close(fig)
    print(len(FIGURAS), 'figuras')


if __name__ == '__main__':
    main()
