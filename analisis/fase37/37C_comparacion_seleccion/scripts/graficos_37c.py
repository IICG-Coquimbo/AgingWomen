"""
Fase 37C: figuras leídas siempre de las tablas guardadas. No ajusta algoritmos y no usa el MRS.

Uso, desde analisis/: python fase37/37C_comparacion_seleccion/scripts/graficos_37c.py
Cada función devuelve (figura, datos): `datos` lista (tabla, columna, {clave: valor dibujado}) para que las pruebas lo comparen con la tabla.
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

B = Path(__file__).resolve().parents[1]
FIG = B / 'figuras'
AZUL, NARANJA, VERDE, GRIS, TINTA, TINTA2, REJILLA = '#2a78d6', '#eb6834', '#1baf7a', '#8a8983', '#0b0b0b', '#52514e', '#e4e3df'
CATEGORICA = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#6250d6', '#8a8983']
SECUENCIAL = LinearSegmentedColormap.from_list('azul', ['#f4f8fd', '#9cc3ef', '#2a78d6', '#0f3e7a'])
COLOR_ESTADO = {'OK': '#dbeafb', 'ADV': '#f7efd0', 'CRIT': '#f7d0bf', 'NE': '#efeeea'}
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.titlesize': 10, 'axes.titleweight': 'bold', 'axes.edgecolor': '#bdbcb6', 'axes.labelcolor': TINTA2, 'xtick.color': TINTA2, 'ytick.color': TINTA2,
                     'axes.spines.top': False, 'axes.spines.right': False, 'figure.dpi': 110, 'savefig.dpi': 170, 'savefig.bbox': 'tight', 'figure.facecolor': 'white'})


def csv(r):
    return pd.read_csv(B / r, encoding='utf-8')


def titulo(fig, t, sub=None, y=1.0):
    fig.suptitle(t, x=0.01, y=y, ha='left', fontsize=12, fontweight='bold')
    if sub:
        fig.text(0.01, y - 0.045, sub, ha='left', va='top', fontsize=8.5, color=TINTA2)


def foco():
    """Lista B, referencias k = 2 y finalistas, en un orden fijo."""
    b = csv('candidatos/lista_B_exploratoria.csv')['config'].tolist()
    f = csv('seleccion/finalistas.csv')['config'].tolist() if (B / 'seleccion' / 'finalistas.csv').exists() else []
    salida = list(b) + ['F1_c05_km_k2', 'P1_c05_km_k2']
    return salida + [c for c in f if c not in salida]


def f01_candidatos():
    t = csv('seleccion/cribado_lista_A.csv')
    b = set(csv('candidatos/lista_B_exploratoria.csv')['config'])
    t = t.dropna(subset=['S_ORD'])
    es_b = t['config'].isin(b)
    fig, ax = plt.subplots(figsize=(8.6, 5))
    ax.scatter(t.loc[~es_b, 'E3_entre_media'], t.loc[~es_b, 'S_ORD'], s=34, c=GRIS, edgecolor='white', linewidth=0.8, label='Lista A (regla previa)')
    ax.scatter(t.loc[es_b, 'E3_entre_media'], t.loc[es_b, 'S_ORD'], s=52, c=AZUL, edgecolor='white', linewidth=0.8, label='Lista B (exploratoria)')
    ax.axvline(0.65, color=NARANJA, lw=1, ls='--')
    ax.axhline(0.40, color=NARANJA, lw=1, ls='--')
    ax.text(0.655, 1.02, 'Umbral crítico', fontsize=8, color=TINTA2, va='bottom')
    ax.set(xlabel='ARI entre remuestreos, procedimiento completo (E3)', ylabel='ARI frente a S-ORD', xlim=(0.25, 1), ylim=(0, 1.08))
    ax.grid(color=REJILLA, lw=0.6)
    ax.legend(frameon=False, loc='lower left')
    titulo(fig, 'Candidatos de las Listas A y B', 'Sin punto en R0, que no tiene S-ORD en la Fase 37B. Cerca de la esquina superior derecha: resiste muestra y codificación.', y=1.04)
    muestra = t.head(10)
    return fig, [('seleccion/cribado_lista_A.csv', 'E3_entre_media', dict(zip(muestra['config'], muestra['E3_entre_media'])))]


def f02_estabilidad():
    t = csv('estabilidad/comparacion_niveles.csv').set_index('config')
    c = [x for x in foco() if x in t.index]
    d = t.loc[c].sort_values('E3_entre_media')
    fig, ax = plt.subplots(figsize=(9, 0.33 * len(d) + 1.5))
    y = np.arange(len(d))
    ax.hlines(y, d['E3_entre_min'], d['E3_entre_media'], color='#c3d9f4', lw=2)
    ax.scatter(d['E3_entre_p05'], y, marker='|', s=90, color=NARANJA, zorder=3, label='Percentil 5')
    ax.scatter(d['E3_entre_media'], y, s=46, color=AZUL, edgecolor='white', zorder=4, label='Media')
    ax.axvline(0.65, color=GRIS, lw=1, ls='--')
    ax.axvline(0.80, color=GRIS, lw=1, ls=':')
    ax.set_yticks(y, d.index)
    ax.set(xlabel='ARI entre remuestreos (línea: desde el mínimo hasta la media)', xlim=(0, 1))
    ax.grid(axis='x', color=REJILLA, lw=0.6)
    ax.legend(frameon=False, loc='lower right')
    titulo(fig, 'Estabilidad del procedimiento completo (E3)', 'Imputación, escalado, reducción y agrupamiento reajustados en cada submuestra.', y=1.05)
    return fig, [('estabilidad/comparacion_niveles.csv', 'E3_entre_media', d['E3_entre_media'].to_dict()), ('estabilidad/comparacion_niveles.csv', 'E3_entre_p05', d['E3_entre_p05'].to_dict())]


def f03_anterior_nueva():
    t = csv('estabilidad/comparacion_niveles.csv')
    a = t[t['en_lista_a']]
    fig, axs = plt.subplots(1, 2, figsize=(10.5, 4.6), sharex=True, sharey=True)
    grupos = (('K-means', a[a['algoritmo'] == 'km']), ('Ward', a[a['algoritmo'] == 'ward']))
    for ax, (n, d) in zip(axs, grupos):
        for i, (nombre, m) in enumerate((('k = 2', d['k'] == 2), ('k = 3 o 4', d['k'].isin([3, 4])), ('k ≥ 5', d['k'] >= 5))):
            ax.scatter(d.loc[m, 'E0_entre_media'], d.loc[m, 'E3_entre_media'], s=30, c=CATEGORICA[i], edgecolor='white', linewidth=0.7, label=nombre)
        ax.plot([0.2, 1], [0.2, 1], color=GRIS, lw=1)
        ax.text(0.97, 0.93, 'Sin cambio', fontsize=8, color=TINTA2, ha='right', rotation=38)
        ax.set_title(f'{n}: {len(d)} configuraciones', loc='left')
        ax.set_xlabel('Fase 37B: reducción congelada (E0)')
        ax.grid(color=REJILLA, lw=0.6)
    axs[0].set_ylabel('Procedimiento completo (E3)')
    axs[0].legend(frameon=False, loc='upper left')
    titulo(fig, 'Estabilidad anterior y nueva, Lista A', 'ARI medio entre remuestreos. Bajo la línea: la Fase 37B sobrestimaba la estabilidad.', y=1.08)
    m = a.head(8).set_index('config')
    return fig, [('estabilidad/comparacion_niveles.csv', 'E0_entre_media', m['E0_entre_media'].to_dict()), ('estabilidad/comparacion_niveles.csv', 'E3_entre_media', m['E3_entre_media'].to_dict())]


def f04_nula():
    t = csv('referencias_nulas/comparacion_por_configuracion.csv').set_index('config')
    c = [x for x in foco() if x in t.index]
    d = t.loc[c]
    fig, axs = plt.subplots(1, 2, figsize=(11, 0.33 * len(d) + 1.7), sharey=True)
    y = np.arange(len(d))
    for ax, m, tit in ((axs[0], 'silueta', 'Silueta (100 réplicas)'), (axs[1], 'E1_ari_entre_media', 'ARI entre remuestreos, E1 (20 réplicas)')):
        ax.hlines(y, d[f'{m}_nula_min'], d[f'{m}_nula_max'], color='#c9c8c2', lw=5, label='Rango de las réplicas')
        ax.scatter(d[f'{m}_obs'], y, s=44, c=AZUL, edgecolor='white', zorder=3, label='Observado')
        ax.set_title(tit, loc='left')
        ax.grid(axis='x', color=REJILLA, lw=0.6)
    axs[0].set_yticks(y, d.index)
    axs[0].invert_yaxis()
    axs[0].legend(frameon=False, loc='upper center', bbox_to_anchor=(0.5, -0.05), ncol=2)
    titulo(fig, 'Frente a la referencia correlacionada', 'Datos con las mismas marginales y correlaciones, sin grupos. Dentro de la banda: compatible con un continuo. Con 20 réplicas, p ≥ 0,048.', y=1.05)
    return fig, [('referencias_nulas/comparacion_por_configuracion.csv', 'silueta_obs', d['silueta_obs'].to_dict()), ('referencias_nulas/comparacion_por_configuracion.csv', 'silueta_nula_max', d['silueta_nula_max'].to_dict()), ('referencias_nulas/comparacion_por_configuracion.csv', 'E1_ari_entre_media_obs', d['E1_ari_entre_media_obs'].to_dict())]


def f05_s_ord():
    t = csv('sensibilidades/s_ord/descomposicion.csv').set_index('config')
    c = [x for x in foco() if x in t.index]
    d = t.loc[c]
    cols = {'H1_distancias_centroides_base': 'Solo distancias', 'H2_distancias_y_fronteras': 'Distancias y fronteras', 'H3_ejes': 'Solo ejes', 'H4_completa': 'S-ORD completa'}
    M = d[list(cols)].to_numpy()
    fig, ax = plt.subplots(figsize=(7.8, 0.33 * len(d) + 1.6))
    im = ax.imshow(M, cmap=SECUENCIAL, vmin=0, vmax=1, aspect='auto')
    ax.set_xticks(range(4), cols.values())
    ax.set_yticks(range(len(d)), d.index)
    ax.spines[:].set_visible(False)
    for i in range(M.shape[0]):
        for j in range(4):
            ax.text(j, i, f'{M[i, j]:.2f}'.replace('.', ','), ha='center', va='center', fontsize=8, color='white' if M[i, j] > 0.62 else TINTA)
    fig.colorbar(im, ax=ax, fraction=0.03, label='ARI con la partición base')
    titulo(fig, 'De dónde viene el cambio en S-ORD', 'Códigos consecutivos frente a ridit. Valores bajos: ese paso cambia a las participantes de grupo.', y=1.05)
    return fig, [('sensibilidades/s_ord/descomposicion.csv', k, d[k].to_dict()) for k in cols]


def f06_sensibilidades():
    t = csv('sensibilidades/sensibilidades_priorizadas.csv')
    c = foco()
    orden = ['S-ORD', 'S-FAMD', 'S-RARA', 'S-TRA', 'S-CUI', 'S-EJE', 'S-IMPMODA', 'S-EDAD', 'S-SOLAPE']
    M = t.pivot_table(index='config', columns='sensibilidad', values='ari_ajuste').reindex(c)[orden]
    fig, ax = plt.subplots(figsize=(9.2, 0.33 * len(c) + 1.6))
    masc = np.ma.masked_invalid(M.to_numpy())
    cm = SECUENCIAL.copy()
    cm.set_bad('#efeeea')
    im = ax.imshow(masc, cmap=cm, vmin=0, vmax=1, aspect='auto')
    ax.set_xticks(range(len(orden)), orden, rotation=30, ha='right')
    ax.set_yticks(range(len(c)), c)
    ax.spines[:].set_visible(False)
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            v = M.iat[i, j]
            ax.text(j, i, 'n/a' if pd.isna(v) else f'{v:.2f}'.replace('.', ','), ha='center', va='center', fontsize=7.5, color=TINTA2 if pd.isna(v) else ('white' if v > 0.62 else TINTA))
    fig.colorbar(im, ax=ax, fraction=0.025, label='ARI con la partición base')
    titulo(fig, 'Sensibilidades críticas', 'n/a: S-FAMD y S-RARA solo se aplican a FAMD. Las de ponderación quedan fuera: responden a otra pregunta.', y=1.05)
    datos = {tuple([('config', i), ('sensibilidad', s)]): M.loc[i, s] for i in c for s in orden if not pd.isna(M.loc[i, s])}
    return fig, [('sensibilidades/sensibilidades_priorizadas.csv', 'ari_ajuste', datos)]


def f07_tamanos():
    t = csv('sensibilidades/s_ord/descomposicion.csv').set_index('config')
    c = [x for x in foco() if x in t.index]
    fig, ax = plt.subplots(figsize=(8.6, 0.33 * len(c) + 1.4))
    menor = {}
    for i, x in enumerate(c):
        v = sorted(map(int, t.loc[x, 'tamanos_base'].split()), reverse=True)
        menor[x] = v[-1]
        izq = 0
        for j, n in enumerate(v):
            ax.barh(i, n - 2, left=izq + 1, color=['#0f3e7a', '#2a78d6', '#6ba5e7', '#c3d9f4'][min(j, 3)], height=0.72)
            ax.text(izq + n / 2, i, n, ha='center', va='center', fontsize=7.5, color='white' if j < 2 else TINTA)
            izq += n
    ax.set_yticks(range(len(c)), c)
    ax.invert_yaxis()
    ax.set(xlabel='Participantes (los tonos ordenan de mayor a menor; no indican un mismo grupo)', xlim=(0, 529))
    titulo(fig, 'Tamaños de los grupos', 'Ningún grupo de estas configuraciones se considera un nivel de severidad.', y=1.05)
    ev = {(('config', x), ('criterio', 'Grupo menor')): n for x, n in menor.items()}
    return fig, [('seleccion/evaluacion_por_etapa.csv', 'valor', ev)]


def f08_separacion():
    t = csv('referencias_nulas/comparacion_por_configuracion.csv').set_index('config')
    a = pd.read_csv(B.parent / '37B_clustering' / 'resultados' / 'tabla_completa_configuraciones.csv').set_index('config')
    c = [x for x in foco() if x in t.index]
    d = pd.DataFrame({'obs': t.loc[c, 'silueta_obs'], 'neg': a.loc[c, 'silueta_negativos'] * 100})
    fig, axs = plt.subplots(1, 2, figsize=(10.5, 0.33 * len(c) + 1.5), sharey=True)
    y = np.arange(len(c))
    axs[0].barh(y, d['obs'], color=AZUL, height=0.6)
    axs[0].set_title('Silueta media', loc='left')
    axs[1].barh(y, d['neg'], color=GRIS, height=0.6)
    axs[1].axvline(10, color=NARANJA, lw=1, ls='--')
    axs[1].set_title('Participantes con silueta negativa (%)', loc='left')
    axs[0].set_yticks(y, c)
    axs[0].invert_yaxis()
    for ax in axs:
        ax.grid(axis='x', color=REJILLA, lw=0.6)
    titulo(fig, 'Separación interna', 'Los valores absolutos no se comparan entre espacios de distinta dimensión.', y=1.05)
    return fig, [('referencias_nulas/comparacion_por_configuracion.csv', 'silueta_obs', d['obs'].to_dict())]


def f09_bloques():
    t = csv('interpretabilidad/resumen_interpretabilidad.csv').set_index('config')
    c = [x for x in foco() if x in t.index]
    cols = sorted([k for k in t.columns if k.startswith('ssb_') and k not in ('ssb_actividad_fisica', 'ssb_variable_max')], key=lambda k: -t.loc[c, k].mean())
    fig, ax = plt.subplots(figsize=(10, 0.33 * len(c) + 2.0))
    izq = np.zeros(len(c))
    y = np.arange(len(c))
    for i, k in enumerate(cols):
        v = t.loc[c, k].fillna(0).to_numpy() * 100
        ax.barh(y, np.maximum(v - 0.3, 0), left=izq + 0.15, color=CATEGORICA[i % 8], height=0.7, label=k[4:])
        izq += v
    ax.set_yticks(y, c)
    ax.invert_yaxis()
    ax.set(xlabel='Parte de la separación entre grupos (%)', xlim=(0, 100))
    ax.legend(frameon=False, ncol=3, loc='upper center', bbox_to_anchor=(0.45, -0.12), fontsize=8)
    titulo(fig, 'Contribución de los bloques temáticos', 'Qué bloques separan a los grupos. Descripción preliminar, sin interpretación clínica.', y=1.05)
    return fig, [('interpretabilidad/resumen_interpretabilidad.csv', cols[0], {x: t.loc[x, cols[0]] for x in c if not pd.isna(t.loc[x, cols[0]])})]


def f10_asignacion():
    t = csv('asignacion/evaluacion_asignacion.csv').set_index('config')
    c = [x for x in foco() if x in t.index]
    d = t.loc[c]
    fig, axs = plt.subplots(1, 2, figsize=(10.5, 0.33 * len(c) + 1.6), sharey=True)
    y = np.arange(len(c))
    axs[0].hlines(y, d['ari_fuera_min'], d['ari_fuera_media'], color='#c3d9f4', lw=2)
    axs[0].scatter(d['ari_fuera_p05'], y, marker='|', s=90, color=NARANJA, zorder=3, label='Percentil 5')
    axs[0].scatter(d['ari_fuera_media'], y, s=44, c=AZUL, edgecolor='white', zorder=4, label='Media')
    axs[0].axvline(0.65, color=GRIS, lw=1, ls='--')
    axs[0].set(xlim=(0, 1))
    axs[0].set_title('ARI fuera de muestra (E3)', loc='left')
    axs[0].legend(frameon=False, loc='lower left')
    axs[1].barh(y, d['margen_mediano_fuera'], color=GRIS, height=0.6)
    axs[1].set_title('Margen mediano frente al segundo centro', loc='left')
    axs[0].set_yticks(y, c)
    axs[0].invert_yaxis()
    for ax in axs:
        ax.grid(axis='x', color=REJILLA, lw=0.6)
    titulo(fig, 'Asignación de participantes no usadas', 'Una asignación algorítmica no es una clasificación clínica.', y=1.05)
    return fig, [('asignacion/evaluacion_asignacion.csv', 'ari_fuera_media', d['ari_fuera_media'].to_dict()), ('asignacion/evaluacion_asignacion.csv', 'margen_mediano_fuera', d['margen_mediano_fuera'].to_dict())]


def f11_finalistas():
    m = csv('seleccion/matriz_estados.csv').set_index('config')
    ev = csv('seleccion/evaluacion_por_etapa.csv')
    c = [x for x in foco() if x in m.index]
    etapas = [k for k in m.columns if k[0].isdigit()]
    fig, ax = plt.subplots(figsize=(10.8, 0.33 * len(c) + 1.9))
    for i, x in enumerate(c):
        for j, e in enumerate(etapas):
            s = m.loc[x, e]
            ax.add_patch(plt.Rectangle((j + 0.03, i + 0.05), 0.94, 0.9, color=COLOR_ESTADO[s]))
            ax.text(j + 0.5, i + 0.5, s, ha='center', va='center', fontsize=7.5, color=TINTA, fontweight='bold' if s == 'CRIT' else 'normal')
    ax.set_xlim(0, len(etapas))
    ax.set_ylim(len(c), 0)
    ax.set_xticks(np.arange(len(etapas)) + 0.5, [e.split('. ')[0] + '. ' + e.split('. ')[1].replace(' e imputación', '').replace(' correlacionada', '') for e in etapas], rotation=30, ha='right')
    ax.set_yticks(np.arange(len(c)) + 0.5, c)
    finalistas = set(csv('seleccion/finalistas.csv')['config'])
    for et in ax.get_yticklabels():
        if et.get_text() in finalistas:
            et.set_fontweight('bold')
            et.set_color(TINTA)
    ax.spines[:].set_visible(False)
    ax.tick_params(length=0)
    titulo(fig, 'Evaluación por etapa, sin puntuación compuesta', 'En negrita, las finalistas. OK, ADV (advertencia), CRIT (debilidad crítica), NE (no evaluada). Un CRIT en Variables no bloquea B (regla V).', y=1.05)
    x = ev[ev['criterio'] == 'E3 ari_entre media']
    return fig, [('seleccion/evaluacion_por_etapa.csv', 'valor', {(('config', f.config), ('criterio', 'E3 ari_entre media')): f.valor for f in x.itertuples() if f.config in c})]


def f12_decision():
    u = csv('seleccion/sensibilidad_umbrales.csv')
    d = csv('seleccion/dependencia_conclusion.csv')
    d = d[~d['es_el_protocolo']]
    filas = [('Con los umbrales desplazados', None, None)] + [(f.escenario, f.conclusion, f'{f.n_particiones_distintas} particiones finalistas') for f in u.itertuples()]
    filas += [('Con otras lecturas de las mismas evidencias (planteadas después de ver los resultados)', None, None)] + [(f.lectura, f.conclusion, 'Ninguna configuración sigue elegible' if f.siguen == 'Ninguna' else f.siguen.replace(' | ', ', ')) for f in d.itertuples()]
    fig, ax = plt.subplots(figsize=(10.5, 0.33 * len(filas) + 1.2))
    for i, (texto, concl, detalle) in enumerate(filas):
        if concl is None:
            ax.text(0, i, texto, va='center', fontsize=9.5, fontweight='bold', color=TINTA)
            continue
        ax.text(0.02, i, texto, va='center', fontsize=8.5, color=TINTA2)
        ax.add_patch(plt.Rectangle((0.585, i - 0.38), 0.05, 0.76, color=COLOR_ESTADO['OK' if concl == 'B' else 'CRIT']))
        ax.text(0.61, i, concl, ha='center', va='center', fontsize=9, fontweight='bold', color=TINTA)
        ax.text(0.65, i, detalle, va='center', fontsize=8, color=TINTA2)
    ax.set_xlim(0, 1)
    ax.set_ylim(len(filas) - 0.4, -0.6)
    ax.axis('off')
    titulo(fig, 'Qué tanto depende la conclusión de las reglas', 'B: segmentación operativa condicionada. C: no seleccionar. La regla sellada da B; ninguna lectura alternativa da A.', y=1.04)
    return fig, [('seleccion/sensibilidad_umbrales.csv', 'n_particiones_distintas', dict(zip(u['escenario'], u['n_particiones_distintas'])))]


FIGURAS = {'f01_candidatos': f01_candidatos, 'f02_estabilidad_completa': f02_estabilidad, 'f03_estabilidad_anterior_nueva': f03_anterior_nueva, 'f04_referencia_correlacionada': f04_nula, 'f05_s_ord': f05_s_ord, 'f06_sensibilidades': f06_sensibilidades,
           'f07_tamanos': f07_tamanos, 'f08_separacion': f08_separacion, 'f09_bloques': f09_bloques, 'f10_asignacion': f10_asignacion, 'f11_finalistas': f11_finalistas, 'f12_decision': f12_decision}


def main():
    FIG.mkdir(exist_ok=True)
    for n, f in FIGURAS.items():
        fig, _ = f()
        fig.savefig(FIG / f'{n}.png')
        plt.close(fig)
        print(n)


if __name__ == '__main__':
    main()
