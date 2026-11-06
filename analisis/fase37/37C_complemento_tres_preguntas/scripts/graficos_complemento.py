"""
Complemento de la Fase 37C: figuras leídas siempre de las tablas guardadas. No ajusta algoritmos.

Uso, desde analisis/: python fase37/37C_complemento_tres_preguntas/scripts/graficos_complemento.py
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
from matplotlib.ticker import FuncFormatter  # noqa: E402

B = Path(__file__).resolve().parents[1]
FIG = B / 'figuras'
FIG.mkdir(exist_ok=True)
AZUL, NARANJA, VERDE, GRIS, TINTA, TINTA2, REJILLA = '#2a78d6', '#eb6834', '#1baf7a', '#8a8983', '#0b0b0b', '#52514e', '#e4e3df'
SEG = {0: '#2a78d6', 1: '#eb6834', 2: '#1baf7a', 3: '#eda100'}
SECUENCIAL = LinearSegmentedColormap.from_list('azul', ['#f4f8fd', '#9cc3ef', '#2a78d6', '#0f3e7a'])
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.titlesize': 10, 'axes.titleweight': 'bold', 'axes.edgecolor': '#bdbcb6', 'axes.labelcolor': TINTA2, 'xtick.color': TINTA2, 'ytick.color': TINTA2, 'axes.spines.top': False, 'axes.spines.right': False, 'figure.dpi': 110, 'savefig.dpi': 170, 'savefig.bbox': 'tight', 'figure.facecolor': 'white'})
ROT = {'A': 'Modelo A', 'B1': 'B1', 'B2': 'B2', 'B2C': 'B2-C', 'B2_C': 'B2-C', 'Celdas': '20 celdas'}
DIAS = ['0 días', '1-2', '3-4', '5-6', 'Todos']
FILAS = ['Sin pareja, no trabaja', 'Con pareja, no trabaja', 'Sin pareja, trabaja', 'Con pareja, trabaja']


COMA = FuncFormatter(lambda x, _: f'{x:g}'.replace('.', ',').replace('-', '−'))


def csv(r):
    return pd.read_csv(B / r, encoding='utf-8')


def titulo(fig, t, sub, y=1.04):
    fig.suptitle(t, x=0.01, y=y, ha='left', fontsize=12, fontweight='bold')
    fig.text(0.01, y - 0.065, sub, ha='left', va='top', fontsize=8.5, color=TINTA2)


def guardar(fig, nombre):
    fig.savefig(FIG / nombre)
    plt.close(fig)


def f1():
    d = csv('reproduccion/distribucion_trios.csv')
    fig, ax = plt.subplots(figsize=(8, 3.3))
    ax.hist(d['ari_cv'], bins=60, color=AZUL, edgecolor='white', linewidth=0.4)
    m = d.iloc[0]
    ax.axvline(m['ari_cv'], color=NARANJA, lw=2)
    ax.annotate(f"Trabajo + pareja + días\nARI {m['ari_cv']:.3f}, posición 1", (m['ari_cv'], ax.get_ylim()[1] * 0.75), xytext=(-8, 0), textcoords='offset points', ha='right', color=TINTA)
    ax.set_xlabel('ARI con validación cruzada frente a las etiquetas de A')
    ax.xaxis.set_major_formatter(COMA)
    ax.set_ylabel('Combinaciones')
    ax.yaxis.grid(True, color=REJILLA)
    ax.set_axisbelow(True)
    titulo(fig, 'El trío ocupa el primer lugar entre 4.060 combinaciones', 'Se eligió mirando las etiquetas de A: es el máximo de una búsqueda, no una medida independiente.')
    guardar(fig, 'f1_distribucion_trios.png')


def f2():
    t = csv('definiciones/tabla_de_celdas.csv')
    fig, ejes = plt.subplots(1, 2, figsize=(10, 3.4))
    orden = [[0, 1, 2, 3, 4], [5, 6, 7, 8, 9], [10, 11, 12, 13, 14], [15, 16, 17, 18, 19]]
    for ax, col, nom in zip(ejes, ('B1', 'B2'), ('B1: imita a A', 'B2: K-means con tres preguntas')):
        for i, fila in enumerate(orden):
            for j, c in enumerate(fila):
                x = t.iloc[c]
                ax.add_patch(plt.Rectangle((j, 3 - i), 0.95, 0.92, color=SEG[int(float(x[col]))], alpha=0.85 if x['n'] >= 10 else 0.4))
                ax.text(j + 0.475, 3 - i + 0.46, f"S{int(float(x[col]))}\nn = {int(x['n'])}", ha='center', va='center', fontsize=7.5, color=TINTA)
        ax.set_xlim(0, 5)
        ax.set_ylim(0, 4)
        ax.set_xticks(np.arange(5) + 0.47, DIAS)
        ax.set_yticks(np.arange(4) + 0.46, FILAS[::-1] if ax is ejes[0] else [''] * 4)
        ax.tick_params(length=0)
        ax.set_title(nom, loc='left')
        for s in ax.spines.values():
            s.set_visible(False)
    titulo(fig, 'Cada alternativa asigna un segmento a cada combinación de respuestas', 'Las celdas con menos de 10 participantes se ven más claras. Los números de segmento de B2 no corresponden a los de A o B1.', y=1.1)
    guardar(fig, 'f2_mapa_de_celdas.png')


def f3():
    d = csv('asignaciones/tablas_correspondencia.csv')
    fig, ejes = plt.subplots(1, 2, figsize=(8.5, 3.2))
    for ax, n in zip(ejes, ('B1', 'B2')):
        m = d[d['comparacion'] == n].pivot(index='A', columns='alternativa', values='n')
        ax.imshow(m.to_numpy(), cmap=SECUENCIAL, vmin=0, vmax=175)
        for (i, j), v in np.ndenumerate(m.to_numpy()):
            ax.text(j, i, int(v), ha='center', va='center', color='white' if v > 95 else TINTA)
        ax.set_xticks(range(4), [f'S{x}' for x in m.columns])
        ax.set_yticks(range(4), [f'S{x}' for x in m.index])
        ax.set_xlabel(f'Segmento de {n}')
        ax.set_ylabel('Segmento de A')
        ax.set_title(f'A frente a {n}', loc='left')
        for s in ax.spines.values():
            s.set_visible(False)
    titulo(fig, 'Correspondencia entre segmentos en las 529', 'Participantes en cada combinación. B1 usa los números de A; B2 no: hay que leer la mejor correspondencia.', y=1.13)
    guardar(fig, 'f3_correspondencia.png')


def f4():
    e = csv('estabilidad/estabilidad_alternativas.csv')
    a = csv('estabilidad/referencia_trios_azar.csv')
    fig, ejes = plt.subplots(1, 2, figsize=(9, 3), sharey=True)
    orden = ['A', 'B1', 'B2', 'B2C']
    for ax, m, col, nom in zip(ejes, ('entre', 'fuera_pares'), ('entre_media', 'fuera_pares_media'), ('Entre repeticiones, compartidas', 'Entre repeticiones, no usadas')):
        for i, n in enumerate(orden):
            x = e[(e['alternativa'] == n) & (e['medida'] == m)].iloc[0]
            c = NARANJA if n == 'A' else AZUL
            ax.plot([x['p05'], x['max']], [i, i], color=c, lw=2)
            ax.plot(x['media'], i, 'o', color=c, ms=8)
            ax.text(x['media'], i - 0.2, f"{x['media']:.2f}".replace('.', ','), ha='center', fontsize=8, color=TINTA)
        ax.scatter(a[col], np.full(len(a), 4) + np.linspace(-0.12, 0.12, len(a)), s=14, color=GRIS, alpha=0.8)
        ax.set_yticks(range(5), ['Modelo A', 'B1', 'B2', 'B2-C', 'B2 con 30 tríos al azar'])
        ax.set_xlim(0.35, 1.03)
        ax.xaxis.grid(True, color=REJILLA)
        ax.set_axisbelow(True)
        ax.set_xlabel('ARI')
        ax.xaxis.set_major_formatter(COMA)
        ax.set_title(nom, loc='left')
    ejes[0].invert_yaxis()
    titulo(fig, 'Las tres preguntas son más estables, pero muchos otros tríos también', 'Punto: media. Línea: percentil 5 a máximo. Agrupar pocas respuestas discretas es estable por construcción.', y=1.17)
    guardar(fig, 'f4_estabilidad.png')


def f5():
    d = csv('fuera_de_muestra/desacuerdos_resumen.csv').set_index('alternativa')
    fig, ax = plt.subplots(figsize=(7.2, 3))
    x = np.arange(3)
    for i, (n, c) in enumerate((('B1', AZUL), ('B2', VERDE))):
        v = d.loc[n, ['discrepan_bajo_010_pct', 'discrepan_010_020_pct', 'discrepan_alto_020_pct']].to_numpy(float)
        ax.bar(x + (i - 0.5) * 0.36, v, 0.33, color=c, label=n)
        for a, b in zip(x + (i - 0.5) * 0.36, v):
            ax.text(a, b + 0.7, f'{b:.0f} %', ha='center', fontsize=8, color=TINTA)
    ax.set_xticks(x, ['Cerca de la frontera\n(margen < 0,10)', 'Intermedio\n(0,10 a 0,20)', 'Lejos de la frontera\n(≥ 0,20)'])
    ax.set_ylabel('Discrepan de A, %')
    ax.yaxis.grid(True, color=REJILLA)
    ax.set_axisbelow(True)
    ax.legend(frameon=False)
    titulo(fig, 'Los desacuerdos se concentran cerca de las fronteras de A', 'Promedio de las 30 repeticiones, en participantes no usadas.', y=1.13)
    guardar(fig, 'f5_desacuerdos_frontera.png')


def f6():
    b = csv('informacion/informacion_por_bloque.csv').set_index('bloque')
    p = csv('informacion/posterior_A_sin_variable_bloque.csv').set_index('bloque')
    orden = ['Alimentación', 'Actividad física adicional', 'Sedentarismo', 'Cuidados', 'Tabaco y alcohol', 'Otras generales', 'Actividad sexual (descriptiva)', 'Digestión (descriptiva)']
    fig, ax = plt.subplots(figsize=(8.6, 3.8))
    ser = [('A sin el bloque (medida principal)', [b.loc[x, 'dr2_A_X_sobre_celdas__media'] for x in orden], AZUL, 'o'), ('A sin la variable (posterior al sellado)', [p.loc[x, 'dr2_media'] for x in orden], VERDE, 's'), ('A completo (circular: cota favorable a A)', [b.loc[x, 'dr2_A_sobre_celdas_circular__media'] for x in orden], NARANJA, 'D')]
    for i, (nom, v, c, mk) in enumerate(ser):
        ax.scatter(v, np.arange(len(orden)) + (i - 1) * 0.22, color=c, marker=mk, s=38, label=nom, zorder=3)
    for u, t in ((0.01, '0,01'), (0.06, '0,06')):
        ax.axvline(u, color=GRIS, ls='--', lw=1)
        ax.text(u, -0.85, t, ha='center', color=TINTA2, fontsize=8)
    ax.axvline(0, color=TINTA2, lw=1)
    ax.set_yticks(range(len(orden)), orden)
    ax.invert_yaxis()
    ax.set_xlabel('ΔR² fuera de muestra frente a las 20 celdas')
    ax.xaxis.set_major_formatter(COMA)
    ax.xaxis.grid(True, color=REJILLA)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, loc='center right')
    titulo(fig, 'Sin ver la variable que describe, A no añade información a las tres preguntas', 'Solo con la propia variable como entrada (circular) supera la banda de 0,06: actividad física adicional y actividad sexual.', y=1.1)
    guardar(fig, 'f6_informacion_incremental.png')


def f7():
    v = csv('informacion/informacion_por_variable.csv').set_index('variable')
    orden = ['frecuencia_aerobico', 'frecuencia_fuerza', 'frecuencia_bajo_impacto', 'tiene_actividad_sexual', 'frecuencia_comida_fuera', 'falta_tiempo_influye', 'vasos_agua_dia', 'platos_verduras_dia', 'horas_sedentarismo', 'tabaco_frecuencia']
    fig, ax = plt.subplots(figsize=(8.6, 4))
    for i, (col, nom, c, mk) in enumerate((('A', 'Modelo A (circular)', NARANJA, 'D'), ('B1', 'B1', AZUL, 'o'), ('B2', 'B2', VERDE, 's'), ('celdas', '20 celdas', GRIS, '^'))):
        ax.scatter(v.loc[orden, col], np.arange(len(orden)) + (i - 1.5) * 0.18, color=c, marker=mk, s=32, label=nom, zorder=3)
    ax.axvline(0, color=TINTA2, lw=1)
    ax.set_yticks(range(len(orden)), orden)
    ax.invert_yaxis()
    ax.set_xlabel('R² fuera de muestra')
    ax.xaxis.set_major_formatter(COMA)
    ax.xaxis.grid(True, color=REJILLA)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, loc='lower right')
    titulo(fig, 'Lo que A conserva de más está en las variables que usa como entrada', 'Las 10 variables con más contraste. Un R² negativo significa que la partición predice peor que la media.', y=1.09)
    guardar(fig, 'f7_r2_por_variable.png')


def f8():
    d = csv('sin_segmentacion/varianza_retenida.csv').set_index('particion').loc[['A', 'B1', 'B2', 'B2_C', 'Celdas']]
    fig, ax = plt.subplots(figsize=(7.2, 2.8))
    y = np.arange(len(d))
    v = 100 * d['varianza_P2_retenida'].to_numpy()
    ax.barh(y, v, color=AZUL, height=0.55)
    for a, b in zip(y, v):
        ax.text(b + 0.4, a, f'{b:.1f} %'.replace('.', ','), va='center', fontsize=8.5)
    ax.set_yticks(y, [f"{ROT[x]} ({int(d.loc[x, 'segmentos'])})" for x in d.index])
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xlabel('Varianza de las 29 variables de P2 retenida, %. Sin segmentar: 100 %')
    ax.xaxis.grid(True, color=REJILLA)
    ax.set_axisbelow(True)
    titulo(fig, 'Cualquier partición resume poco de las características individuales', 'Entre paréntesis, la cantidad de segmentos. Medida en las 529; A la maximiza casi por construcción.', y=1.15)
    guardar(fig, 'f8_varianza_retenida.png')


if __name__ == '__main__':
    for f in (f1, f2, f3, f4, f5, f6, f7, f8):
        f()
    print(len(list(FIG.glob('*.png'))), 'figuras')
