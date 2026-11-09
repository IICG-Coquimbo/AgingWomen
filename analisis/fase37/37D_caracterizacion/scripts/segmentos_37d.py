"""
Fase 37D, etapa 3: segmentos A (P2_c12_km_k4) y B1 (regla de tres preguntas). Correspondencia, caracterización (F6), MRS por segmento (F5, F7),
sensibilidades fijadas en el protocolo e información que se pierde al segmentar. No reajusta ninguna partición: todas se leen de artefactos guardados.

Uso, desde analisis/: python fase37/37D_caracterizacion/scripts/segmentos_37d.py
"""
import zlib

import nucleo_37d as N
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import adjusted_rand_score

S = N.BASE / 'resultados' / 'segmentos'
SEGS = ('A', 'B1')
DETALLE = []
SALIDAS = {'mrs_total': 'continua', 'mrs_somatico': 'continua', 'mrs_psicologico': 'continua', 'mrs_urogenital': 'continua', 'severidad': 'categorica', 'severo_mrs': 'categorica'}


def caracterizar(D, l, nombre):
    """F6: descripción por grupo y efecto entre grupos para las 36 características. η² sobre códigos; V² en nominales (medidas de la Fase 37C)."""
    efectos, desc = [], []
    for v in N.CARACTERISTICAS:
        t = N.tipo_de(v, D.defs)
        x = N.para_prueba(D.X, v)
        m = x.notna().to_numpy()
        xm, lm = x[m], l[m]
        if t == 'nominal':
            tab = pd.crosstab(xm.to_numpy(), lm)
            p, _, v2, prueba, aviso = N.chi2(tab)
            e, medida = v2, 'V²'
            for g in range(4):
                s = xm[lm == g].value_counts(normalize=True)
                for c, pr in s.items():
                    desc.append({'segmentacion': nombre, 'grupo': g, 'variable': v, 'categoria': c, 'pct': 100 * pr, 'n_validos': int((lm == g).sum())})
        else:
            xv = xm.astype(float).to_numpy()
            e, medida = N.eta2(xv, lm), 'η²'
            presentes = [g for g in range(4) if (lm == g).any()]
            aviso_vacio = '' if len(presentes) == 4 else f'grupos sin participantes aplicables: {sorted(set(range(4)) - set(presentes))}'
            if t == 'binaria':
                p, _, _, prueba, aviso = N.chi2(pd.crosstab(xv, lm))
            else:
                p, prueba, aviso = stats.kruskal(*[xv[lm == g] for g in presentes]).pvalue, 'Kruskal-Wallis', ''
            aviso = '; '.join(x for x in (aviso, aviso_vacio) if x)
            for g in range(4):
                z = xv[lm == g]
                if len(z) == 0:
                    desc.append({'segmentacion': nombre, 'grupo': g, 'variable': v, 'categoria': 'media', 'pct': np.nan, 'n_validos': 0})
                    continue
                desc.append({'segmentacion': nombre, 'grupo': g, 'variable': v, 'categoria': 'media', 'pct': np.nan, 'n_validos': len(z), 'media': z.mean(), 'de': z.std(ddof=1) if len(z) > 1 else np.nan, 'mediana': np.median(z),
                             'q1': np.percentile(z, 25), 'q3': np.percentile(z, 75), 'pct_si': 100 * z.mean() if t == 'binaria' else np.nan})
        efectos.append({'segmentacion': nombre, 'variable': v, 'etiqueta': N.ETIQUETA[v], 'bloque': N.BLOQUE_DE[v], 'usada_por_A': v in N.EN_A, 'en_regla_B1': v in N.TRIO, 'tipo': t,
                        'medida': medida, 'efecto': e, 'prueba': prueba, 'p': p, 'n': int(m.sum()), 'aviso': aviso})
    E = pd.DataFrame(efectos)
    E['q'] = N.bh(E['p'].to_numpy())
    E['banda'] = [N.banda(e, 'eta2') for e in E['efecto']]
    E['lectura'] = np.where(E['efecto'] >= 0.06, 'diferencia importante', np.where(E['efecto'] < 0.01, 'distribución semejante', 'diferencia pequeña'))
    return E, pd.DataFrame(desc)


def mrs_por_grupo(D, l, nombre, sub=None):
    sub = np.ones(len(l), bool) if sub is None else sub
    filas = []
    for r in list(N.RESULTADOS) + ['mrs_total_sin9']:
        y = D.M[r].to_numpy()[sub]
        for g in range(4):
            z = y[l[sub] == g]
            icm, icd = N.ic_media_mediana(z, semilla_extra=zlib.crc32(f'{nombre}|{r}|{g}'.encode()) % 100000)
            filas.append({'segmentacion': nombre, 'resultado': r, 'grupo': g, 'n': len(z), 'media': z.mean(), 'de': z.std(ddof=1), 'mediana': np.median(z), 'q1': np.percentile(z, 25), 'q3': np.percentile(z, 75),
                          'minimo': z.min(), 'maximo': z.max(), 'ic_media_inf': icm[0], 'ic_media_sup': icm[1], 'ic_mediana_inf': icd[0], 'ic_mediana_sup': icd[1]})
    sev = []
    for g in range(4):
        m = l[sub] == g
        s = D.M['severidad'].to_numpy()[sub][m]
        k = int(D.M['severo_mrs'].to_numpy()[sub][m].sum())
        w = N.wilson(k, int(m.sum()))
        sev.append({'segmentacion': nombre, 'grupo': g, 'n': int(m.sum()), **{c: 100 * (s == c).mean() for c in N.ORDEN_SEVERIDAD}, 'pct_severo': 100 * k / m.sum(), 'ic_severo_inf': 100 * w[0], 'ic_severo_sup': 100 * w[1]})
    return pd.DataFrame(filas), pd.DataFrame(sev)


def global_mrs(D, l, nombre, sub=None, con_ic=False, resultados=None):
    sub = np.ones(len(l), bool) if sub is None else sub
    filas = []
    for i, (r, t) in enumerate((resultados or SALIDAS).items()):
        y = D.M[r].to_numpy()[sub]
        a = N.segmento_frente_a(y, l[sub], t)
        if con_ic:
            a['ic_inf'], a['ic_sup'] = N.boot_segmento(y, l[sub], t, semilla_extra=10 * SEGS.index(nombre) + i if nombre in SEGS else i)
        filas.append({'segmentacion': nombre, 'resultado': r, **a})
    return pd.DataFrame(filas)


def pares(D, l, nombre):
    y = D.M['mrs_total'].to_numpy()
    filas = []
    for a in range(4):
        for b in range(a + 1, 4):
            ya, yb = y[l == a], y[l == b]
            p = stats.mannwhitneyu(ya, yb, alternative='two-sided').pvalue
            g = np.r_[np.ones(len(ya)), np.zeros(len(yb))]
            filas.append({'segmentacion': nombre, 'grupo_a': a, 'grupo_b': b, 'n_a': len(ya), 'n_b': len(yb), 'mediana_a': np.median(ya), 'mediana_b': np.median(yb), 'media_a': ya.mean(), 'media_b': yb.mean(),
                          'r_rb': N.r_biserial(np.r_[ya, yb], g), 'p': p})
    d = pd.DataFrame(filas)
    d['p_holm'] = N.holm(d['p'].to_numpy())
    d['banda'] = [N.banda(e, 'r_rb') for e in d['r_rb']]
    return d


def dentro(D, l, nombre):
    """Asociación de cada característica con el MRS total dentro de los grupos, media ponderada por n, frente a la marginal (sección 6.4)."""
    y = D.M['mrs_total'].to_numpy()
    filas = []
    for v in N.CARACTERISTICAS:
        t = N.tipo_de(v, D.defs)
        x = N.para_prueba(D.X, v).to_numpy()
        marg = N.asociacion(x, y, t)
        ef, pesos = [], []
        for g in np.unique(l):
            m = l == g
            a = N.asociacion(x[m], y[m], t)
            xs = pd.Series(x[m]).dropna()
            minoria = int(xs.value_counts().min()) if t == 'binaria' and xs.nunique() == 2 else np.nan
            DETALLE.append({'segmentacion': nombre, 'variable': v, 'grupo': int(g), 'n': a['n'], 'efecto': a['efecto'], 'p': a['p'], 'n_nivel_minoritario': minoria})
            if pd.notna(a['efecto']):
                ef.append(a['efecto'])
                pesos.append(a['n'])
        filas.append({'segmentacion': nombre, 'variable': v, 'etiqueta': N.ETIQUETA[v], 'medida': marg['medida'], 'marginal': marg['efecto'], 'dentro_ponderado': np.average(ef, weights=pesos) if ef else np.nan,
                      'grupos_con_variacion': len(ef)})
    return pd.DataFrame(filas)


def particiones_guardadas(ids):
    et = pd.read_csv(N.B37 / 'etiquetas' / 'etiquetas_principales.csv', dtype={'participante_id': str}).set_index('participante_id').reindex(ids)
    sol = pd.read_csv(N.B37 / 'sensibilidades' / 'etiquetas' / 'S-SOLAPE_P2.csv', dtype={'participante_id': str}).set_index('participante_id').reindex(ids)
    ordi = pd.read_csv(N.B37 / 'sensibilidades' / 'etiquetas' / 'S-ORD_P2.csv', dtype={'participante_id': str}).set_index('participante_id').reindex(ids)
    return {'P2_c08_km_k4': et['P2_c08_km_k4'].to_numpy(), 'P2_c16_km_k4': et['P2_c16_km_k4'].to_numpy(), 'P2_c12_km_k4 (37B)': et['P2_c12_km_k4'].to_numpy(),
            'S-SOLAPE P2_c12_km_k4': sol['P2_c12_km_k4'].to_numpy(), 'S-ORD (ridit) P2_c12_km_k4': ordi['P2_c12_km_k4'].to_numpy()}


def main():
    N.instalar_gancho()
    N.huella_sello()
    D = N.cargar()
    L = {'A': D.E['A'].to_numpy().astype(int), 'B1': D.E['B1'].to_numpy().astype(int)}
    # Correspondencia
    tab = pd.crosstab(pd.Series(L['A'], name='A'), pd.Series(L['B1'], name='B1'))
    N.a_csv(tab.reset_index(), S / 'correspondencia_A_B1.csv')
    ari, coin = N.ari_y_coincidencia(L['A'], L['B1'])
    ari_cv, coin_cv = N.ari_y_coincidencia(L['A'], D.E['B1_cv'].to_numpy())
    N.a_json({'ari_A_B1': ari, 'coincidencia_A_B1': coin, 'ari_A_B1_cv': ari_cv, 'coincidencia_A_B1_cv': coin_cv, 'tamanos_A': np.bincount(L['A']).tolist(), 'tamanos_B1': np.bincount(L['B1']).tolist(),
              'mismo_numero_mismo_grupo_pct': float(100 * (L['A'] == L['B1']).mean())}, S / 'correspondencia_resumen.json')
    # F6
    car, desc = [], []
    for s in SEGS:
        e, d = caracterizar(D, L[s], s)
        car.append(e)
        desc.append(d)
    car, desc = pd.concat(car), pd.concat(desc)
    N.a_csv(car, S / 'F6_caracterizacion_efectos.csv')
    N.a_csv(desc, S / 'F6_caracterizacion_por_grupo.csv')
    # Comparación con la Fase 37C
    v37 = pd.read_csv(N.C37 / 'seleccion' / 'variables_que_mas_separan.csv')
    v37 = v37[v37['config'] == N.CONFIG][['variable', 'efecto', 'medida']].rename(columns={'efecto': 'efecto_37C', 'medida': 'medida_37C'})
    cmp = v37.merge(car[car['segmentacion'] == 'A'][['variable', 'efecto', 'medida']], on='variable', how='left')
    cmp['diferencia'] = cmp['efecto'] - cmp['efecto_37C']
    N.a_csv(cmp, S / 'comparacion_con_37C.csv')
    # F5 y F7
    grupos, sev, glob, prs = [], [], [], []
    for s in SEGS:
        g, v = mrs_por_grupo(D, L[s], s)
        grupos.append(g)
        sev.append(v)
        glob.append(global_mrs(D, L[s], s, con_ic=True))
        prs.append(pares(D, L[s], s))
    glob = pd.concat(glob)
    glob['q'] = N.bh(glob['p'].to_numpy())
    # Protocolo, sección 8: ε² en resultados continuos; V² en las tablas de 4 × 4 y 4 × 2 (columna eta2), con los cortes 0,01, 0,06 y 0,14.
    glob['banda'] = [N.banda(e if m != 'V' else v2, 'eta2') for e, m, v2 in zip(glob['efecto'], glob['medida'], glob['eta2'])]
    N.a_csv(pd.concat(grupos), S / 'F5_mrs_por_grupo.csv')
    N.a_csv(pd.concat(sev), S / 'F5_severidad_por_grupo.csv')
    N.a_csv(glob, S / 'F5_global.csv')
    N.a_csv(pd.concat(prs), S / 'F7_pares_total.csv')
    # Sensibilidades
    sens = []
    margen = D.E['margen_A'].to_numpy()
    for c in N.CORTES_MARGEN:
        sub = margen >= c
        for s in SEGS:
            sens.append(global_mrs(D, L[s], s, sub=sub).assign(sensibilidad='S-MARGEN', detalle=f'margen ≥ {c:.2f}', n_sub=int(sub.sum()), principal=c == N.CORTE_MARGEN))
    imp = D.estado[N.EN_A].isin(['imputada', 'deducida']) | (D.heredada[N.EN_A].astype(str) == '1')
    sin3 = ~imp[list(N.TRIO)].any(axis=1).to_numpy()
    sin29 = ~imp.any(axis=1).to_numpy()
    for s in SEGS:
        sens.append(global_mrs(D, L[s], s, sub=sin3).assign(sensibilidad='S-SIN-IMP3', detalle='sin imputación en las tres preguntas', n_sub=int(sin3.sum()), principal=True))
        sens.append(global_mrs(D, L[s], s, sub=sin29).assign(sensibilidad='S-SIN-IMP29', detalle='sin ninguna imputación en las 29 variables de A', n_sub=int(sin29.sum()), principal=s == 'A'))
        sens.append(global_mrs(D, L[s], s, resultados={'mrs_total_sin9': 'continua', 'mrs_urogenital_sin9': 'continua'}).assign(sensibilidad='S-SIN9', detalle='sin el ítem 9', n_sub=529, principal=True))
    sens.append(global_mrs(D, D.E['B1_cv'].to_numpy().astype(int), 'B1_cv').assign(sensibilidad='S-B1CV', detalle='B1 con validación cruzada', n_sub=529, principal=True))
    part = particiones_guardadas(D.ids)
    ari_part = []
    for nombre, l in part.items():
        sens.append(global_mrs(D, l.astype(int), nombre).assign(sensibilidad='S-PARTICIONES', detalle='partición guardada, sin reajuste', n_sub=529, principal=True))
        ari_part.append({'particion': nombre, 'ari_con_A': adjusted_rand_score(L['A'], l), 'tamanos': ' / '.join(map(str, np.bincount(l.astype(int))))})
    sens = pd.concat(sens)
    N.a_csv(sens, S / 'sensibilidades_global.csv')
    N.a_csv(pd.DataFrame(ari_part), S / 'particiones_guardadas_ari.csv')
    g10, s10 = [], []
    for s in SEGS:
        a, b = mrs_por_grupo(D, L[s], f'{s} (margen ≥ 0,10)', sub=margen >= N.CORTE_MARGEN)
        g10.append(a)
        s10.append(b)
    N.a_csv(pd.concat(g10), S / 'S-MARGEN_mrs_por_grupo.csv')
    N.a_csv(pd.concat(s10), S / 'S-MARGEN_severidad_por_grupo.csv')
    # Desacuerdos A/B1 según margen
    bandas = pd.cut(margen, [0, 0.05, 0.10, 0.20, 1.01], right=False, labels=['< 0,05', '0,05 a 0,10', '0,10 a 0,20', '≥ 0,20'])
    al = tab.to_numpy()
    from scipy.optimize import linear_sum_assignment
    f, c = linear_sum_assignment(-al)
    mapa = dict(zip(tab.columns[c], tab.index[f]))
    acuerdo = np.array([mapa[b] for b in L['B1']]) == L['A']
    N.a_csv(pd.DataFrame({'banda_margen': bandas, 'acuerdo': acuerdo}).groupby('banda_margen', observed=False)['acuerdo'].agg(['size', 'mean']).reset_index().rename(columns={'size': 'n', 'mean': 'pct_acuerdo'}), S / 'acuerdo_por_margen.csv')
    # Información que se pierde
    celdas = (D.X['trabaja_actualmente'] * 10 + D.X['tiene_pareja'] * 5 + D.X['dias_ejercicio_semana'] - 1).astype(int).to_numpy()
    var = []
    for nombre, l in (('A', L['A']), ('B1', L['B1']), ('20 celdas de las tres preguntas', celdas)):
        for r in N.RESULTADOS:
            e2 = N.eta2(D.M[r].to_numpy(), l)
            k = len(np.unique(l))
            # η² crece con el número de grupos aunque no haya diferencias: se informa también ajustado, 1 − (1 − η²)(n − 1)/(n − k).
            var.append({'segmentacion': nombre, 'resultado': r, 'eta2': e2, 'eta2_ajustado': 1 - (1 - e2) * (len(l) - 1) / (len(l) - k), 'varianza_dentro': 1 - e2, 'grupos': k})
    N.a_csv(pd.DataFrame(var), S / 'varianza_dentro_segmentos.csv')
    N.a_csv(pd.concat([dentro(D, L[s], s) for s in SEGS]), S / 'asociacion_dentro_de_segmentos.csv')
    N.a_csv(pd.DataFrame(DETALLE), S / 'asociacion_dentro_por_grupo.csv')
    N.registrar('segmentos')
    print(tab, ari, coin, ari_cv)
    print(car.pivot(index='variable', columns='segmentacion', values='efecto').round(3).sort_values('A', ascending=False).to_string())
    print(cmp.round(4).to_string(index=False))
    print(glob[['segmentacion', 'resultado', 'prueba', 'efecto', 'ic_inf', 'ic_sup', 'eta2', 'p', 'q', 'banda']].round(4).to_string(index=False))
    print(pd.concat(grupos).query("resultado=='mrs_total'")[['segmentacion', 'grupo', 'n', 'media', 'mediana', 'ic_mediana_inf', 'ic_mediana_sup']].round(2).to_string(index=False))
    print(pd.concat(sev).round(1).to_string(index=False))
    print(pd.concat(prs)[['segmentacion', 'grupo_a', 'grupo_b', 'r_rb', 'p_holm']].round(4).to_string(index=False))
    print(sens[['sensibilidad', 'detalle', 'segmentacion', 'resultado', 'n_sub', 'efecto', 'p']].round(4).to_string(index=False))
    print(pd.DataFrame(ari_part).to_string(index=False))
    print(pd.DataFrame(var).round(4).to_string(index=False))


if __name__ == '__main__':
    main()
