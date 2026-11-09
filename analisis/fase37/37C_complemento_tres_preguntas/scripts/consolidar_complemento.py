"""
Complemento de la Fase 37C: consolida las 30 repeticiones. Imitación, estabilidad, tamaños, información por bloque y desacuerdos fuera de muestra. Solo lee los lotes propios y las etiquetas selladas.

Uso, desde analisis/: python fase37/37C_complemento_tres_preguntas/scripts/consolidar_complemento.py
"""
import sys
import time

import nucleo_complemento as C
import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score

N, Q = C.N, C.Q
B = C.BASE
L = B / 'fuera_de_muestra' / 'lotes'
ALT = ('B1', 'B1N', 'B2', 'B2C')


def res(v, p=''):
    v = np.asarray(v, float)
    return {f'{p}media': float(np.nanmean(v)), f'{p}mediana': float(np.nanmedian(v)), f'{p}p05': float(np.nanpercentile(v, 5)), f'{p}min': float(np.nanmin(v)), f'{p}max': float(np.nanmax(v))}


def equilibrio(l):
    t = np.bincount(l)
    t = t[t > 0]
    if len(t) < 2:
        return 0.0
    p = t / t.sum()
    return float(-(p * np.log(p)).sum() / np.log(len(t)))


def main():
    t0 = time.time()
    C.huella()
    Q.instalar_gancho()
    subs = Q.subconjuntos()
    lot = [np.load(L / f'r{r:02d}.npz') for r in range(len(subs))]
    meta = [N.leer_json(L / f'r{r:02d}.json') for r in range(len(subs))]
    sello = N.leer_json(B / 'protocolo' / 'sello_protocolo.json')['sha256']
    if any(m['huella_protocolo'] != sello for m in meta):
        raise SystemExit('Hay lotes con otra huella de protocolo')
    oficial = N.etiquetas_37b()[C.CONFIG].to_numpy()
    et = pd.read_csv(B / 'asignaciones' / 'etiquetas_alternativas.csv', dtype={'participante_id': str})
    base = {'A': oficial, 'B1': et['B1_doble_uso'].to_numpy(), 'B2': et['B2'].to_numpy(), 'B2C': et['B2_C'].to_numpy(), 'B1N': et['B1_doble_uso'].to_numpy()}
    usadas = np.zeros((len(subs), Q.N), bool)
    for r, idx in enumerate(subs):
        usadas[r, idx] = True
    # Imitación y tamaños por repetición
    filas, tamanos, dis = [], [], []
    for r, idx in enumerate(subs):
        resto = np.setdiff1d(np.arange(Q.N), idx)
        Ar = lot[r]['A'].astype(int)
        for n in ALT:
            l = lot[r][n].astype(int)
            al = C.alineados(Ar[idx], l[idx], l)
            ofi = C.alineados(oficial[idx], l[idx], l)
            filas.append({'alternativa': n, 'repeticion': r, 'ari_con_A_r': adjusted_rand_score(Ar[resto], l[resto]), 'coincidencia_A_r_pct': float(100 * (al[resto] == Ar[resto]).mean()), 'ari_con_A_oficial': adjusted_rand_score(oficial[resto], l[resto]), 'coincidencia_A_oficial_pct': float(100 * (ofi[resto] == oficial[resto]).mean())})
            m = lot[r]['margen_A'][resto]
            ok = al[resto] == Ar[resto]
            dis.append({'alternativa': n, 'repeticion': r, 'auc_margen': N.auc(m[ok], m[~ok]) if (~ok).any() else np.nan, 'discrepan_bajo_010_pct': float(100 * (~ok)[m < 0.10].mean()) if (m < 0.10).any() else np.nan, 'discrepan_010_020_pct': float(100 * (~ok)[(m >= 0.10) & (m < 0.20)].mean()) if ((m >= 0.10) & (m < 0.20)).any() else np.nan, 'discrepan_alto_020_pct': float(100 * (~ok)[m >= 0.20].mean()) if (m >= 0.20).any() else np.nan})
        for n in ('A', *ALT):
            l = lot[r][n].astype(int)
            t = np.bincount(l[idx])
            tamanos.append({'alternativa': n, 'repeticion': r, 'segmentos': int((t > 0).sum()), 'tam_min_entrenamiento': int(t[t > 0].min()), 'tam_max_entrenamiento': int(t.max()), 'equilibrio': equilibrio(l[idx]), 'tamanos_entrenamiento': ' '.join(map(str, t))})
    d = pd.DataFrame(filas)
    N.a_csv(d, B / 'fuera_de_muestra' / 'imitacion_por_repeticion.csv')
    N.a_csv(pd.DataFrame(tamanos), B / 'fuera_de_muestra' / 'tamanos_por_repeticion.csv')
    N.a_csv(pd.DataFrame(dis), B / 'fuera_de_muestra' / 'desacuerdos_por_repeticion.csv')
    imit = [{'alternativa': n, **{f'{m}_{k}': x for m in ('ari_con_A_r', 'coincidencia_A_r_pct', 'ari_con_A_oficial', 'coincidencia_A_oficial_pct') for k, x in res(g[m]).items()}} for n, g in d.groupby('alternativa')]
    N.a_csv(pd.DataFrame(imit), B / 'fuera_de_muestra' / 'imitacion_resumen.csv')
    tam = pd.DataFrame(tamanos).groupby('alternativa').agg(segmentos_min=('segmentos', 'min'), segmentos_max=('segmentos', 'max'), tam_min_menor=('tam_min_entrenamiento', 'min'), tam_min_mediano=('tam_min_entrenamiento', 'median'), equilibrio_medio=('equilibrio', 'mean'), equilibrio_min=('equilibrio', 'min')).reset_index()
    N.a_csv(tam, B / 'fuera_de_muestra' / 'tamanos_resumen.csv')
    N.a_csv(pd.DataFrame(dis).groupby('alternativa').mean(numeric_only=True).drop(columns='repeticion').reset_index(), B / 'fuera_de_muestra' / 'desacuerdos_resumen.csv')
    # Trío de la búsqueda anidada
    tr = pd.Series([' + '.join(m['trio_anidado']) for m in meta]).value_counts().rename_axis('trio').reset_index(name='repeticiones')
    N.a_csv(tr, B / 'fuera_de_muestra' / 'trios_busqueda_anidada.csv')
    N.a_csv(pd.DataFrame({'repeticion': range(len(meta)), 'trio': [' + '.join(m['trio_anidado']) for m in meta], 'valor_interno': [m['valor_interno_anidado'] for m in meta], 'corte_ejercicio': [m['corte_ejercicio'] for m in meta], 'pureza_media_b1': [np.nanmean(np.array(m['pureza_b1'], float)) for m in meta]}), B / 'fuera_de_muestra' / 'parametros_por_repeticion.csv')
    # Forma de B1 en cada repetición: se traduce cada mapa a los nombres oficiales con la alineación del entrenamiento y se compara con la tabla de las 529.
    mapa_base = np.array(N.leer_json(B / 'definiciones' / 'definicion_B1_B2.json')['B1']['mapa'])
    formas = []
    for r, idx in enumerate(subs):
        mapa = np.array(meta[r]['mapa_b1'])
        Ar = lot[r]['A'].astype(int)
        trad = dict(zip(Ar[idx], N.alinear(oficial[idx], Ar[idx])))
        tr_mapa = np.array([trad[x] for x in mapa])
        formas.append({'repeticion': r, 'celdas_distintas_a_la_regla_529': int((tr_mapa != mapa_base).sum()), 'celdas_distintas': ' '.join(map(str, np.flatnonzero(tr_mapa != mapa_base))), 'b1_igual_a_b1_anidada': bool((lot[r]['B1'] == lot[r]['B1N']).all())})
    N.a_csv(pd.DataFrame(formas), B / 'fuera_de_muestra' / 'forma_de_B1_por_repeticion.csv')
    # Estabilidad, con las medidas de la Fase 37C
    est = []
    for n in ('A', 'B1', 'B1N', 'B2', 'B2C'):
        todas = np.vstack([lot[r][n] for r in range(len(subs))]).astype(int)
        frente = [adjusted_rand_score(base[n][usadas[r]], todas[r][usadas[r]]) for r in range(len(subs))]
        fuera = [adjusted_rand_score(base[n][~usadas[r]], todas[r][~usadas[r]]) for r in range(len(subs))]
        entre = N.ari_pares_compartidos(todas, usadas)
        fp = N.ari_pares_fuera(todas, usadas)
        for medida, v in (('completo', frente), ('fuera', fuera), ('entre', entre), ('fuera_pares', fp)):
            est.append({'alternativa': n, 'medida': medida, 'n_valores': len(v), **res(v)})
    est = pd.DataFrame(est)
    N.a_csv(est, B / 'estabilidad' / 'estabilidad_alternativas.csv')
    # Tríos al azar
    az = []
    trios = C.trios_azar()
    for i, t in enumerate(trios):
        todas = np.vstack([lot[r][f'T{i:02d}'] for r in range(len(subs))]).astype(int)
        az.append({'trio': ' + '.join(t), 'entre_media': float(np.mean(N.ari_pares_compartidos(todas, usadas))), 'fuera_pares_media': float(np.mean(N.ari_pares_fuera(todas, usadas)))})
    N.a_csv(pd.DataFrame(az), B / 'estabilidad' / 'referencia_trios_azar.csv')
    # Información por variable y bloque
    info = pd.concat([pd.read_csv(L / f'r{r:02d}_info.csv') for r in range(len(subs))], ignore_index=True)
    pv = info.pivot_table(index=['repeticion', 'variable', 'bloque'], columns='particion', values='r2_fuera').reset_index()
    for x, b, n in (('celdas+A-X', 'celdas', 'dr2_A_X_sobre_celdas'), ('celdas+A', 'celdas', 'dr2_A_sobre_celdas_circular'), ('celdas+A8-X', 'celdas', 'dr2_A8_X_sobre_celdas'), ('celdas+A16-X', 'celdas', 'dr2_A16_X_sobre_celdas'), ('A-X', 'B1', 'dif_A_X_menos_B1'), ('A-X', 'B2', 'dif_A_X_menos_B2')):
        pv[n] = pv[x] - pv[b]
    medidas = [c for c in pv.columns if c not in ('repeticion', 'variable', 'bloque')]
    por_var = pv.groupby(['bloque', 'variable'])[medidas].mean().reset_index()
    N.a_csv(por_var, B / 'informacion' / 'informacion_por_variable.csv')
    bl_rep = pv.groupby(['repeticion', 'bloque'])[medidas].mean().reset_index()
    N.a_csv(bl_rep, B / 'informacion' / 'informacion_bloque_por_repeticion.csv')
    filas = []
    for b, g in bl_rep.groupby('bloque'):
        fila = {'bloque': b, 'lectura_principal': b in C.LECTURA_PRINCIPAL, 'n_variables': pv[pv['bloque'] == b]['variable'].nunique()}
        for m in medidas:
            fila[f'{m}__media'] = float(g[m].mean())
            fila[f'{m}__p05'] = float(np.percentile(g[m], 5))
        filas.append(fila)
    N.a_csv(pd.DataFrame(filas), B / 'informacion' / 'informacion_por_bloque.csv')
    C.registrar('consolidar', [('consolidar', 'completa', time.time() - t0, Q.leidos())])
    pd.set_option('display.width', 220, 'display.max_columns', 30, 'display.max_colwidth', 70)
    print(pd.DataFrame(imit)[['alternativa', 'ari_con_A_r_media', 'ari_con_A_r_p05', 'ari_con_A_r_min', 'coincidencia_A_r_pct_media', 'ari_con_A_oficial_media']].round(3).to_string())
    print(est.pivot(index='alternativa', columns='medida', values='media').round(3).to_string())
    print(est.pivot(index='alternativa', columns='medida', values='p05').round(3).to_string())
    print(tam.round(2).to_string())
    print(tr.to_string())
    print(pd.DataFrame(az)[['entre_media', 'fuera_pares_media']].describe().round(3).to_string())
    x = pd.DataFrame(filas).set_index('bloque')
    print(x[[c for c in x.columns if c.split('__')[0] in ('A', 'A-X', 'B1', 'B2', 'celdas', 'dr2_A_X_sobre_celdas')]].round(3).to_string())
    return 0


if __name__ == '__main__':
    sys.exit(main())
