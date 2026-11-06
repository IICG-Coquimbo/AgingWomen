"""
Complemento de la Fase 37C: lo que se calcula en las 529. Reproducción del 0,677, definición de B1 y B2, correspondencias, desacuerdos, descripción por bloques, sensibilidades, sin segmentación e imputación.
Toda cifra obtenida con la tabla construida y evaluada en las mismas filas queda rotulada como doble uso.

Uso, desde analisis/: python fase37/37C_complemento_tres_preguntas/scripts/completo_complemento.py
"""
import sys
import time
from itertools import combinations

import nucleo_complemento as C
import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score, silhouette_score

N, Q, IN = C.N, C.Q, C.IN
B = C.BASE


def reproduccion(cad, oficial):
    """Mismo código de la Fase 37C: codificar_para_celdas, particiones_cv y reconstruir, en el mismo orden de búsqueda."""
    defs, vals = IN.numericos(cad)
    enc = IN.codificar_para_celdas(defs, vals)
    pliegues = IN.particiones_cv(Q.N)
    filas = [{'trio': ' + '.join(t), 'ari_cv': IN.reconstruir(pd.factorize(enc[t[0]] * 10000 + enc[t[1]] * 100 + enc[t[2]])[0], oficial, pliegues, C.K)} for t in combinations(list(defs), 3)]
    d = pd.DataFrame(filas).sort_values('ari_cv', ascending=False).reset_index(drop=True)
    d.insert(0, 'posicion', d.index + 1)
    d['contiene_trabajo'] = d['trio'].str.contains('trabaja_actualmente')
    d['contiene_pareja'] = d['trio'].str.contains('tiene_pareja')
    d['contiene_ejercicio'] = d['trio'].str.contains('dias_ejercicio_semana')
    N.a_csv(d, B / 'reproduccion' / 'distribucion_trios.csv')
    guardado = pd.read_csv(C.C37 / 'seleccion' / 'reconstruccion_tres_cuatro_variables.csv').set_index('config').loc[C.CONFIG]
    fila = d[d['trio'] == guardado['mejor_trio']].iloc[0]
    res = {'n_combinaciones': len(d), 'trio_guardado': guardado['mejor_trio'], 'ari_guardado': float(guardado['ari_3']), 'trio_reproducido': d['trio'].iloc[0], 'ari_reproducido': float(d['ari_cv'].iloc[0]), 'diferencia': float(abs(d['ari_cv'].iloc[0] - guardado['ari_3'])), 'posicion': int(fila['posicion']),
           'segundo_trio': d['trio'].iloc[1], 'ari_segundo': float(d['ari_cv'].iloc[1]), 'tercero_trio': d['trio'].iloc[2], 'ari_tercero': float(d['ari_cv'].iloc[2]), 'mediana_combinaciones': float(d['ari_cv'].median()), 'p95_combinaciones': float(np.percentile(d['ari_cv'], 95)),
           'posicion_mejor_sin_trabajo': int(d[~d['contiene_trabajo']]['posicion'].iloc[0]), 'ari_mejor_sin_trabajo': float(d[~d['contiene_trabajo']]['ari_cv'].iloc[0]), 'ari_mejor_sin_pareja': float(d[~d['contiene_pareja']]['ari_cv'].iloc[0]), 'ari_mejor_sin_ejercicio': float(d[~d['contiene_ejercicio']]['ari_cv'].iloc[0]),
           'origen_codigo': 'revision_decision_37c.pocas_variables: mayoría por celda con 5 pliegues; las etiquetas oficiales de A se ajustaron con las 529, y el trío se eligió con todos los datos'}
    N.a_json(res, B / 'reproduccion' / 'reproduccion_ari.json')
    return res


def definiciones(cad, oficial):
    cod = C.celdas(cad.tabla)
    Zd = cad.congelada(C.ESPACIO)
    Z3 = Zd[list(C.TRIO)].to_numpy()
    todas = np.arange(Q.N)
    mapa, pureza, cuenta = C.tabla_celdas(cod, oficial)
    b1 = mapa[cod]
    pl = IN.particiones_cv(Q.N)
    b1cv = np.zeros(Q.N, int)
    for prueba in pl:
        en = np.setdiff1d(todas, prueba)
        b1cv[prueba] = C.tabla_celdas(cod[en], oficial[en])[0][cod[prueba]]
    b2, margen_b2, centros, _ = C.ajustar_b2(Z3, todas, Q.SEMILLA)
    b2c, corte = C.ajustar_cruce(cad.tabla, todas, Q.SEMILLA)
    filas = []
    for c in range(C.M_CELDAS):
        m = cod == c
        fila = {'celda': c, 'descripcion': C.nombre_celda(c), 'n': int(m.sum()), **{f'A_{g}': int(cuenta[c, g]) for g in range(C.K)}, 'pureza_B1': pureza[c], 'B1': int(mapa[c]), 'B2': sorted(set(b2[m]))[0] if m.any() else '', 'B2_C': sorted(set(b2c[m]))[0] if m.any() else ''}
        if m.any() and len(set(b2[m])) != 1:
            raise SystemExit('B2 separa participantes de una misma celda')
        filas.append(fila)
    N.a_csv(pd.DataFrame(filas), B / 'definiciones' / 'tabla_de_celdas.csv')
    N.a_json({'variables': list(C.TRIO), 'celdas_posibles': C.M_CELDAS, 'celdas_observadas': int((np.bincount(cod, minlength=20) > 0).sum()), 'B1': {'tipo': 'Mayoría por celda; aproximación a A, no validación independiente', 'mapa': mapa.tolist(), 'segmentos': len(set(b1))}, 'B2': {'tipo': 'K-means k = 4 sobre tres columnas z de P2; sin etiquetas de A, pero el trío se eligió antes por reproducir a A', 'centros_z': centros.tolist(), 'columnas': list(C.TRIO), 'n_init': 50, 'random_state': Q.SEMILLA}, 'B2_C': {'tipo': 'Pareja × trabajo × ejercicio bajo o alto', 'corte_en_codigo': corte}}, B / 'definiciones' / 'definicion_B1_B2.json')
    kk = []
    for k in range(2, 9):
        l, m, _, a = C.ajustar_b2(Z3, todas, Q.SEMILLA, k)
        kk.append({'k': k, 'silueta_tres_columnas': silhouette_score(Z3, l), 'inercia': a['inercia'], 'tamanos': ' '.join(map(str, np.bincount(l, minlength=k))), 'tam_min': int(np.bincount(l, minlength=k).min()), 'ari_con_A': adjusted_rand_score(oficial, l), 'margen_mediano': float(np.median(m))})
    N.a_csv(pd.DataFrame(kk), B / 'definiciones' / 'b2_cantidad_de_grupos.csv')
    return {'cod': cod, 'B1': b1, 'B1cv': b1cv, 'B2': b2, 'B2C': b2c, 'margen_b2': margen_b2, 'corte': corte, 'pureza': pureza[cod], 'mapa': mapa, 'Z': Zd, 'Z3': Z3}


def correspondencias(p, oficial):
    filas, tablas = [], []
    margen = None
    i = N.info_config(C.CONFIG)
    X = Q.coordenadas(i['espacio'], i['componentes']).to_numpy()
    modelo = N.leer_json(C.C37 / 'seleccion' / 'artefactos_provisionales' / C.CONFIG / 'modelo_segmentacion.json')
    et, _, _, margen = Q.asignar(np.array(modelo['centroides']), X)
    if not (et == oficial).all():
        raise SystemExit('Los centroides guardados no reproducen las etiquetas oficiales')
    for nombre, l, rotulo in (('B1', p['B1'], 'Doble uso: tabla construida y evaluada en las 529'), ('B1_cv', p['B1cv'], 'Validación cruzada de 5 pliegues; las etiquetas de A se ajustaron con las 529'), ('B2', p['B2'], 'Sin etiquetas de A; trío elegido antes por reproducir a A'), ('B2_C', p['B2C'], 'Sin etiquetas de A; trío elegido antes por reproducir a A')):
        al = N.alinear(oficial, l)
        ok = al == oficial
        filas.append({'alternativa': nombre, 'rotulo': rotulo, 'segmentos': len(set(l)), 'tamanos': ' '.join(map(str, np.bincount(l))), 'tam_min': int(np.bincount(l)[np.bincount(l) > 0].min()), 'equilibrio': Q.tamanos(l, len(set(l)))['equilibrio'] if set(l) == set(range(len(set(l)))) else np.nan, 'ari_con_A': adjusted_rand_score(oficial, l), 'coincidencia_alineada_pct': float(100 * ok.mean()),
                      'margen_mediano_coinciden': float(np.median(margen[ok])), 'margen_mediano_discrepan': float(np.median(margen[~ok])), 'auc_margen_coinciden_mayor': N.auc(margen[ok], margen[~ok]), 'discrepan_margen_bajo_010_pct': float(100 * (~ok)[margen < 0.10].mean()), 'discrepan_margen_010_020_pct': float(100 * (~ok)[(margen >= 0.10) & (margen < 0.20)].mean()), 'discrepan_margen_alto_020_pct': float(100 * (~ok)[margen >= 0.20].mean()), 'n_discrepan': int((~ok).sum())})
        m = pd.crosstab(pd.Series(oficial, name='A'), pd.Series(l, name='alternativa')).stack().reset_index(name='n')
        m.insert(0, 'comparacion', nombre)
        tablas.append(m)
        aciertos = pd.DataFrame({'A': oficial, 'ok': ok}).groupby('A')['ok'].mean()
        filas[-1].update({f'coincidencia_grupo_A{g}_pct': float(100 * x) for g, x in aciertos.items()})
    N.a_csv(pd.DataFrame(filas), B / 'asignaciones' / 'comparacion_asignaciones.csv')
    N.a_csv(pd.concat(tablas, ignore_index=True), B / 'asignaciones' / 'tablas_correspondencia.csv')
    return margen


def etiquetas_sin_bloque(p):
    Z = p['Z'].to_numpy()
    columnas = list(p['Z'].columns)
    return {b: C.a_sin_bloque(Z, columnas, b, np.arange(Q.N), Q.SEMILLA) for b in C.BLOQUES}


def describir(cad, obj, p, oficial, sb):
    filas = []
    part = {'A': oficial, 'B1': p['B1'], 'B2': p['B2'], 'B2_C': p['B2C'], 'Celdas': p['cod']}
    for v, o in obj.items():
        bloque = C.BLOQUE_DE.get(v, 'IMC observado')
        for n, l in {**part, 'A-X': sb[bloque]['A'] if bloque in sb else oficial}.items():
            filas.append({'variable': v, 'bloque': bloque, 'tipo': o['tipo'], 'particion': n, 'n_observadas': int(o['marca'].sum()), 'r2_interno': C.r2_interno(l, o['Y'], o['marca']), 'diferencia_maxima': C.diferencia_maxima(l, o['Y'], o['marca'])})
    d = pd.DataFrame(filas)
    N.a_csv(d, B / 'informacion' / 'descripcion_por_variable.csv')
    perfiles = []
    defs = {x['variable']: x for x in cad.defs['P1'][0]}
    for n, l in part.items():
        if n == 'Celdas':
            continue
        for g in np.unique(l):
            for v, o in obj.items():
                m = o['marca'] & (l == g)
                perfiles.append({'particion': n, 'segmento': int(g), 'n': int((l == g).sum()), 'variable': v, 'bloque': C.BLOQUE_DE.get(v, 'IMC observado'), 'media_codigo': float(o['Y'][m].mean()) if o['Y'].shape[1] == 1 and m.any() else np.nan})
    N.a_csv(pd.DataFrame(perfiles), B / 'informacion' / 'perfiles_descriptivos.csv')
    # Dominio del trío en A y varianza multivariable retenida
    Z = p['Z'].to_numpy()
    esc = N.leer_json(N.F36 / 'artefactos' / C.ESPACIO / 'escaladores.json')
    ssb = {}
    for j, c in enumerate(p['Z'].columns):
        v = esc[c]['variable']
        ssb[v] = ssb.get(v, 0.0) + sum((oficial == g).sum() * (Z[oficial == g, j].mean() - Z[:, j].mean()) ** 2 for g in range(C.K))
    tot = sum(ssb.values())
    dom = pd.DataFrame([{'variable': v, 'bloque': C.BLOQUE_DE[v], 'parte_ssb_A': x / tot} for v, x in ssb.items()]).sort_values('parte_ssb_A', ascending=False)
    N.a_csv(dom, B / 'informacion' / 'dominio_ssb_modelo_A.csv')
    fuera_trio = [j for j, c in enumerate(p['Z'].columns) if esc[c]['variable'] not in C.TRIO]
    Xpc = Q.coordenadas(C.ESPACIO, 12).to_numpy()
    ret = []
    for n, l in part.items():
        ret.append({'particion': n, 'segmentos': len(set(l)), 'varianza_P2_retenida': C.varianza_retenida(Z, l), 'varianza_P2_sin_trio_retenida': C.varianza_retenida(Z[:, fuera_trio], l), 'varianza_12_componentes_retenida': C.varianza_retenida(Xpc, l)})
    N.a_csv(pd.DataFrame(ret), B / 'sin_segmentacion' / 'varianza_retenida.csv')
    ari = [{'bloque_quitado': b, **{f'ari_con_{k}': adjusted_rand_score(oficial, sb[b][k]) for k in C.VARIANTES_A}, 'tamanos_A_X': ' '.join(map(str, np.bincount(sb[b]['A'], minlength=C.K)))} for b in C.BLOQUES]
    N.a_csv(pd.DataFrame(ari), B / 'informacion' / 'a_sin_bloque_frente_a_A.csv')
    # Correlación entre bloques, con pares observados y sin la nominal
    v = [x for x, o in obj.items() if o['tipo'] != 'nominal' and x in C.BLOQUE_DE]
    tb = pd.DataFrame({x: pd.Series(obj[x]['Y'][:, 0]).where(obj[x]['marca']) for x in v})
    corr = tb.corr(method='spearman', min_periods=30)
    fila = []
    bl = list(C.BLOQUES)
    for i, a in enumerate(bl):
        for b in bl[i:]:
            va = [x for x in C.BLOQUES[a] if x in v]
            vb = [x for x in C.BLOQUES[b] if x in v]
            s = corr.loc[va, vb].abs().to_numpy()
            if a == b:
                s = s[np.triu_indices_from(s, 1)] if s.shape[0] > 1 else np.array([np.nan])
            fila.append({'bloque_a': a, 'bloque_b': b, 'corr_abs_media': float(np.nanmean(s)) if s.size else np.nan, 'corr_abs_max': float(np.nanmax(s)) if s.size else np.nan})
    N.a_csv(pd.DataFrame(fila), B / 'sin_segmentacion' / 'correlacion_entre_bloques.csv')
    pares = corr.abs().where(np.triu(np.ones(corr.shape, bool), 1)).stack().sort_values(ascending=False).reset_index()
    pares.columns = ['variable_a', 'variable_b', 'spearman_abs']
    N.a_csv(pares, B / 'sin_segmentacion' / 'correlacion_por_par.csv')
    return d


def sensibilidades(cad, p, oficial):
    """Reutiliza las etiquetas selladas de las variantes de A; nada se reajusta en A. B2 se reajusta con su propia variante."""
    filas = []
    hist = pd.read_csv(C.C37 / 'sensibilidades' / 'sensibilidades_priorizadas.csv')
    hist = hist[hist['config'] == C.CONFIG].set_index('sensibilidad')
    cod = p['cod']
    for sid in ('S-ORD', 'S-SOLAPE', 'S-EDAD', 'S-BLOQUE', 'S-TRA', 'S-CUI', 'S-EJE'):
        d = pd.read_csv(N.B37 / 'sensibilidades' / 'etiquetas' / f'{sid}_{C.ESPACIO}.csv', dtype={'participante_id': str}).set_index('participante_id').reindex(cad.ids)
        aj = (d['rol'] == 'ajuste').to_numpy()
        var = d[C.CONFIG].to_numpy().astype(int)
        mapa = C.tabla_celdas(cod[aj], var[aj])[0]
        filas.append({'sensibilidad': sid, 'ari_A_sellado': hist.loc[sid, 'ari_ajuste'], 'ari_B1': adjusted_rand_score(p['B1'][aj], mapa[cod][aj]), 'ari_B1_con_A_variante': adjusted_rand_score(var[aj], mapa[cod][aj]), 'segmentos_B1': len(set(mapa[cod])), 'filas_ajuste': int(aj.sum())})
    imp = pd.read_csv(C.C37 / 'sensibilidades' / 's_impmoda_etiquetas.csv', dtype={'participante_id': str}).set_index('participante_id').reindex(cad.ids)[C.CONFIG].to_numpy().astype(int)
    mapa = C.tabla_celdas(cod, imp)[0]
    filas.append({'sensibilidad': 'S-IMPMODA', 'ari_A_sellado': hist.loc['S-IMPMODA', 'ari_ajuste'], 'ari_B1': adjusted_rand_score(p['B1'], mapa[cod]), 'ari_B1_con_A_variante': adjusted_rand_score(imp, mapa[cod]), 'segmentos_B1': len(set(mapa[cod])), 'filas_ajuste': Q.N})
    N.a_csv(pd.DataFrame(filas), B / 'complejidad' / 'sensibilidad_B1.csv')
    b2 = []
    todas = np.arange(Q.N)
    base = p['B2']
    for modo in ('ridit', 'normal'):
        Z = cad.matriz_nivel(C.ESPACIO, 'E1', None, modo)[list(C.TRIO)].to_numpy()
        b2.append({'variante': f'Días como {modo}', 'grupo': 'Codificación', 'ari_con_B2': adjusted_rand_score(base, C.ajustar_b2(Z, todas, Q.SEMILLA)[0]), 'por_construccion': False, 'filas_ajuste': Q.N})
    for w in (0.5, 2.0):
        Z = p['Z3'].copy()
        Z[:, 2] *= w
        b2.append({'variante': f'Peso de ejercicio × {w:g}', 'grupo': 'Ponderación', 'ari_con_B2': adjusted_rand_score(base, C.ajustar_b2(Z, todas, Q.SEMILLA)[0]), 'por_construccion': False, 'filas_ajuste': Q.N})
    imputadas = cad.imputadas[list(C.TRIO)].to_numpy()
    for j, v in enumerate(C.TRIO):
        en = np.flatnonzero(~imputadas[:, j])
        b2.append({'variante': f'Ajuste sin imputadas de {v}', 'grupo': 'Población', 'ari_con_B2': adjusted_rand_score(base, C.ajustar_b2(p['Z3'], en, Q.SEMILLA)[0]), 'por_construccion': False, 'filas_ajuste': len(en)})
    en = np.flatnonzero(~imputadas.any(axis=1))
    b2.append({'variante': 'Ajuste sin imputadas en ninguna de las tres', 'grupo': 'Población', 'ari_con_B2': adjusted_rand_score(base, C.ajustar_b2(p['Z3'], en, Q.SEMILLA)[0]), 'por_construccion': False, 'filas_ajuste': len(en)})
    # Variantes de A que no tocan las tres preguntas: se comprueba, no se presume.
    t, _ = cad.tabla_imputada()
    igual = (C.celdas(t) == cod).all()
    b2.append({'variante': 'S-IMPMODA: no cambia las tres preguntas', 'grupo': 'Por construcción', 'ari_con_B2': 1.0 if igual else float('nan'), 'por_construccion': True, 'filas_ajuste': Q.N})
    for sid in ('S-SOLAPE', 'S-EDAD'):
        b2.append({'variante': f'{sid}: quita variables que B2 no usa', 'grupo': 'Por construcción', 'ari_con_B2': 1.0, 'por_construccion': True, 'filas_ajuste': Q.N})
    N.a_csv(pd.DataFrame(b2), B / 'complejidad' / 'sensibilidad_B2.csv')


def imputacion(cad, p, oficial, margen):
    imp = cad.imputadas[list(C.TRIO)]
    alguna = imp.any(axis=1).to_numpy()
    vals = cad.tabla
    filas = []
    for v in C.TRIO:
        m = imp[v].to_numpy()
        filas.append({'variable': v, 'n_imputadas': int(m.sum()), 'valor_imputado': ' | '.join(sorted(set(vals.loc[m, v]))), 'n_deducidas': int((cad.estado[v].to_numpy() == 'deducida').sum())})
    N.a_csv(pd.DataFrame(filas), B / 'imputacion' / 'imputadas_tres_preguntas.csv')
    entrada_a = [v for v in C.BLOQUE_DE]
    expuesta_a = (cad.imputadas[entrada_a].any(axis=1).to_numpy() | (cad.previa[entrada_a] == '1').any(axis=1).to_numpy())
    res = {'participantes_con_alguna_imputada': int(alguna.sum()), 'pct': float(100 * alguna.mean()), 'con_dos_o_mas': int((imp.sum(axis=1) >= 2).sum()), 'modelo_A_con_alguna_imputada': int(expuesta_a.sum()), 'modelo_A_pct': float(100 * expuesta_a.mean()), 'modelo_A_variables': len(entrada_a)}
    for n, l in (('B1_cv', p['B1cv']), ('B2', p['B2'])):
        ok = N.alinear(oficial, l) == oficial
        res[f'{n}_discrepan_imputadas_pct'] = float(100 * (~ok)[alguna].mean())
        res[f'{n}_discrepan_observadas_pct'] = float(100 * (~ok)[~alguna].mean())
    s = cad.imputadas['tiene_actividad_sexual'].to_numpy()
    va = pd.read_csv(C.C37 / 'sensibilidades' / 's_impmoda_etiquetas.csv', dtype={'participante_id': str}).set_index('participante_id').reindex(cad.ids)[C.CONFIG].to_numpy().astype(int)
    alin = N.alinear(oficial, va)
    obs = pd.Series(cad.valor['tiene_actividad_sexual'].to_numpy()[~s]).value_counts().to_dict()
    res.update({'sexual_imputadas': int(s.sum()), 'sexual_observadas': {k: int(x) for k, x in obs.items()}, 'sexual_valor_imputado': sorted(set(cad.tabla.loc[s, 'tiene_actividad_sexual']))[0], 'sexual_ari_A_con_moda_529': adjusted_rand_score(oficial, va), 'sexual_A_cambian_entre_imputadas_pct': float(100 * (alin != oficial)[s].mean()), 'sexual_A_cambian_entre_no_imputadas_pct': float(100 * (alin != oficial)[~s].mean()), 'sexual_B_cambian_celda': int((C.celdas(cad.tabla_imputada()[0]) != p['cod']).sum())})
    # Etiqueta B1 si el objetivo fuera A con la otra moda
    mapa = C.tabla_celdas(p['cod'], va)[0]
    res['sexual_ari_B1_con_moda_529'] = adjusted_rand_score(p['B1'], mapa[p['cod']])
    res['sexual_celdas_B1_cambian_de_segmento_alineado'] = int((N.alinear(p['mapa'], mapa) != p['mapa']).sum())
    N.a_json(res, B / 'imputacion' / 'efecto_imputacion.json')


def main():
    t0 = time.time()
    C.huella()
    Q.instalar_gancho()
    cad = N.Cadena()
    oficial = pd.read_csv(C.C37 / 'seleccion' / 'artefactos_provisionales' / C.CONFIG / 'etiquetas.csv', dtype={'participante_id': str}).set_index('participante_id').reindex(cad.ids)['grupo'].to_numpy()
    if not (oficial == N.etiquetas_37b()[C.CONFIG].to_numpy()).all():
        raise SystemExit('Las etiquetas guardadas no coinciden con las de la Fase 37B')
    print(reproduccion(cad, oficial))
    p = definiciones(cad, oficial)
    margen = correspondencias(p, oficial)
    obj = C.objetivos(cad)
    sb = etiquetas_sin_bloque(p)
    describir(cad, obj, p, oficial, sb)
    sensibilidades(cad, p, oficial)
    imputacion(cad, p, oficial, margen)
    N.a_csv(pd.DataFrame({'participante_id': cad.ids, 'A': oficial, 'celda': p['cod'], 'B1_doble_uso': p['B1'], 'B1_cv': p['B1cv'], 'B2': p['B2'], 'B2_C': p['B2C'], 'margen_A': margen, 'margen_B2': p['margen_b2'], 'pureza_B1': p['pureza']}), B / 'asignaciones' / 'etiquetas_alternativas.csv')
    C.registrar('completo', [('completo', 'completa', time.time() - t0, Q.leidos())])
    print('Listo', round(time.time() - t0), 's')


if __name__ == '__main__':
    sys.exit(main())
