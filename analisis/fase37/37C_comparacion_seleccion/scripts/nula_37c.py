"""
Fase 37C: evalúa el conjunto priorizado frente a la referencia correlacionada, primero comprueba sus propiedades declaradas y sus controles sintéticos.

Pasos (uso, desde analisis/: python fase37/37C_comparacion_seleccion/scripts/nula_37c.py --paso propiedades|controles|replicas|consolidar [--procesos N]):
  propiedades  calibra, guarda parámetros y mide conservación con 20 réplicas.
  controles    tabla sin grupos y tabla con grupos sembrados.
  replicas     réplicas 0-19 con estabilidad E0 y E1; 20-99 solo separación.
  consolidar   comparación por configuración y control de búsqueda múltiple.
"""
import argparse
import json
import multiprocessing as mp
import sys
import time
from pathlib import Path

import nucleo_37c as N
import numpy as np
import pandas as pd
import referencia_correlacionada as RC
from sklearn.metrics import adjusted_rand_score

Q = N.Q
S = N.BASE / 'referencias_nulas'
N_EST, N_TOTAL = 20, 100
METRICAS = ['silueta', 'davies_bouldin', 'calinski_harabasz', 'fraccion_eje1']
METRICAS_EST = ['E0_ari_entre_media', 'E0_ari_completo_media', 'E1_ari_entre_media', 'E1_ari_completo_media']
CAD = None
COP = None


GRILLA_ALFA = [0.025, 0.05, 0.075, 0.10, 0.125, 0.15, 0.20]
RUTA_ALFA = S / 'contraccion_elegida.json'


def alfa_elegido():
    return N.leer_json(RUTA_ALFA)['alfa_elegido']


def construir(cad, alfa=None):
    return RC.Copula(cad.tabla, cad.defs['P1'][0], Q.MADRES, contraccion=alfa_elegido() if alfa is None else alfa)


def iniciar(alfa=None):
    global CAD, COP
    Q.instalar_gancho()
    CAD = N.Cadena()
    COP = construir(CAD, alfa)


def rng_replica(r):
    return np.random.default_rng(np.random.SeedSequence([Q.SEMILLA, 3700, r]))


def espacios(t):
    salida = {}
    for e in Q.ESPACIOS:
        Z = N.TF.Transformador.cargar(N.F36 / 'artefactos' / e).transformar(t)[0].to_numpy()
        m = N.R.ajustar(Z, [f'x{i}' for i in range(Z.shape[1])])
        salida[e] = (Z, N.R.proyectar(m, Z, 20), m)
    return salida


def x_de(esp, cfg):
    Z, F, _ = esp[cfg['base']]
    return Z if cfg['componentes'] == 0 else F[:, :cfg['componentes']]


def estabilidad_config(X_por_rep, cfg, l_completo, subs):
    """Ajusta en cada submuestra sobre las coordenadas dadas. `X_por_rep`: coordenadas (529 filas) o lista por repetición."""
    et = []
    usadas = np.zeros((len(subs), Q.N), bool)
    frente = []
    for r, idx in enumerate(subs):
        X = X_por_rep[r] if isinstance(X_por_rep, list) else X_por_rep
        l, _, _ = Q.ajustar(X[idx], cfg['algoritmo'], cfg['k'], Q.semilla_rep(r))
        comp = np.full(Q.N, -1)
        comp[idx] = l
        et.append(comp)
        usadas[r, idx] = True
        frente.append(adjusted_rand_score(l_completo[idx], l))
    return float(np.mean(N.ari_pares_compartidos(np.vstack(et), usadas))), float(np.mean(frente))


def trabajo(arg):
    r, cfgs, subs, sello, carpeta = arg
    destino = S / carpeta / f'replica_{r:03d}.csv'
    marca = destino.with_suffix('.json')
    if destino.exists() and marca.exists() and N.leer_json(marca).get('huella_protocolo') == sello:
        return f'replica_{r:03d}', 'omitida', 0.0, Q.leidos()
    t0 = time.time()
    try:
        t = COP.muestrear(rng_replica(r))
        esp = espacios(t)
        filas = []
        rep_e1 = {}
        if r < N_EST:
            for e in Q.ESPACIOS:
                Z = esp[e][0]
                rep_e1[e] = [N.coordenadas_cadena(Z, idx)[0] for idx in subs]
        for cfg in cfgs:
            X = x_de(esp, cfg)
            l, _, _ = Q.ajustar(X, cfg['algoritmo'], cfg['k'])
            cal, _ = Q.calidad(X, l)
            tam = Q.tamanos(l, cfg['k'])
            c1 = esp[cfg['base']][1][:, 0]
            fila = {'replica': r, 'config': cfg['config'], **{m: cal[m] for m in ('silueta', 'silueta_negativos', 'davies_bouldin', 'calinski_harabasz')}, 'tam_min': tam['tam_min'], 'equilibrio': tam['equilibrio'], 'fraccion_eje1': Q.fraccion_eje1(X, l, c1)}
            if r < N_EST:
                fila['E0_ari_entre_media'], fila['E0_ari_completo_media'] = estabilidad_config(X, cfg, l, subs)
                por_rep = esp[cfg['base']][0] if cfg['componentes'] == 0 else [x[:, :cfg['componentes']] for x in rep_e1[cfg['base']]]
                fila['E1_ari_entre_media'], fila['E1_ari_completo_media'] = estabilidad_config(por_rep, cfg, l, subs)
            filas.append(fila)
        destino.parent.mkdir(parents=True, exist_ok=True)
        tmp = destino.with_suffix('.tmp')
        pd.DataFrame(filas).to_csv(tmp, index=False, encoding='utf-8', lineterminator='\n')
        tmp.replace(destino)
        marca.write_text(json.dumps({'replica': r, 'huella_protocolo': sello, 'configuraciones': len(filas)}) + '\n', encoding='utf-8', newline='\n')
        return f'replica_{r:03d}', 'completa', time.time() - t0, Q.leidos()
    except Exception as ex:  # noqa: BLE001
        return f'replica_{r:03d}', f'error: {type(ex).__name__}: {ex}', time.time() - t0, Q.leidos()


def propiedades():
    """Enmienda 1: prueba la grilla de contracción y elige el menor alfa que cumple todos los criterios. Solo usa propiedades."""
    Q.instalar_gancho()
    cad = N.Cadena()
    filas = []
    for alfa in GRILLA_ALFA:
        res = propiedades_alfa(cad, alfa)
        filas.append({'alfa': alfa, 'spearman_max': res['error_max_spearman_media_replicas'], 'vp_P1_1a3': max(res['error_relativo_vp_P1_1a3']), 'vp_F1_1a3': max(res['error_relativo_vp_F1_1a3']), **res['criterios'], 'cumple': all(res['criterios'].values()) and res['marginales_exactas'] and res['logica_madre_hija']})
        print(filas[-1], flush=True)
    t = pd.DataFrame(filas)
    N.a_csv(t, S / 'grilla_contraccion.csv')
    validos = t[t['cumple']]
    alfa = float(validos['alfa'].min()) if len(validos) else None
    N.a_json({'alfa_elegido': alfa, 'regla': 'Menor alfa de la grilla que cumple todos los criterios de la sección 5.4 (enmienda 1)', 'valida': alfa is not None}, RUTA_ALFA)
    print('Alfa elegido:', alfa)
    if alfa is not None:
        res = N.leer_json(S / f'propiedades_alpha_{alfa:g}.json')
        N.a_json(res, S / 'propiedades_referencia.json')


def propiedades_alfa(cad, alfa):
    t0 = time.time()
    cop = construir(cad, alfa)
    print('Calibración', round(time.time() - t0), 's; error máximo por iteración (primero, último):', round(cop.historial[0], 4), round(cop.historial[-1], 4))
    N.a_json({'hipotesis': 'Marginales y asociaciones monótonas conservadas; una sola nube latente unimodal, sin grupos.', 'nombres': cop.nombres, 'contraccion': alfa, 'R_latente': cop.R.tolist(), 'spearman_objetivo': cop.objetivo.tolist(), 'error_calibracion_por_iteracion': cop.historial,
              'n_simulado': RC.N_SIM, 'iteraciones': RC.ITERACIONES, 'semilla': [42, 37]}, S / f'parametros_copula_alpha_{alfa:g}.json')
    defs = {d['variable']: d for d in cad.defs['P1'][0]}
    obs = cad.tabla
    Zo = cad.congelada('P1').to_numpy()
    vp_o = np.linalg.svd(Zo - Zo.mean(axis=0), compute_uv=False) ** 2 / len(Zo)
    Zf = cad.congelada('F1').to_numpy()
    vpf_o = np.linalg.svd(Zf - Zf.mean(axis=0), compute_uv=False) ** 2 / len(Zf)
    nombres = cop.nombres
    Ss, vps, vpsf, marg, v_rep, logica = [], [], [], [], [], []
    vars_todas = list(defs)
    pares = [(a, b) for i, a in enumerate(vars_todas) for b in vars_todas[i + 1:]]

    def vc(t, a, b):
        x, y = t[a].astype(str).to_numpy(), t[b].astype(str).to_numpy()
        m = (x != '') & (y != '') if 'imc' in (a, b) else np.ones(len(x), bool)
        if a == 'imc':
            x = pd.qcut(pd.to_numeric(pd.Series(x[m])), 4, labels=False, duplicates='drop').astype(str).to_numpy()
            y = y[m]
        elif b == 'imc':
            y = pd.qcut(pd.to_numeric(pd.Series(y[m])), 4, labels=False, duplicates='drop').astype(str).to_numpy()
            x = x[m]
        return RC.v_cramer(x, y)
    pares_v = [(a, b) for a, b in pares if a not in ('edad', 'horas_sedentarismo') and b not in ('edad', 'horas_sedentarismo')]
    v_obs = np.array([vc(obs, a, b) for a, b in pares_v])

    def incoh(t):
        d0 = t['dias_ejercicio_semana'].astype(str) == '1'
        return int((d0 & ((t['frecuencia_aerobico'].astype(str) != '') | (t['frecuencia_bajo_impacto'].astype(str) != '') | (t['frecuencia_fuerza'].astype(str) != ''))).sum())
    for r in range(N_EST):
        t = cop.muestrear(rng_replica(r))
        Ss.append(cop.spearman_tabla(t))
        Z = N.TF.Transformador.cargar(N.F36 / 'artefactos' / 'P1').transformar(t)[0].to_numpy()
        vps.append(np.linalg.svd(Z - Z.mean(axis=0), compute_uv=False) ** 2 / len(Z))
        Z = N.TF.Transformador.cargar(N.F36 / 'artefactos' / 'F1').transformar(t)[0].to_numpy()
        vpsf.append(np.linalg.svd(Z - Z.mean(axis=0), compute_uv=False) ** 2 / len(Z))
        for v in vars_todas:
            marg.append({'replica': r, 'variable': v, 'iguales': sorted(t[v].astype(str)) == sorted(obs[v].astype(str))})
        for h, m in Q.MADRES.items():
            ok = ((t[h].astype(str) == '') == (t[m] == 'NO')).all()
            logica.append({'replica': r, 'hija': h, 'madre': m, 'coherente': bool(ok)})
        v_rep.append([vc(t, a, b) for a, b in pares_v])
    S_media = np.mean(Ss, axis=0)
    iu = np.triu_indices(len(nombres), 1)
    S_rep_err = [float(np.abs(s - cop.objetivo)[iu].max()) for s in Ss]
    err = np.abs(S_media - cop.objetivo)
    pares_s = pd.DataFrame({'a': [nombres[i] for i in iu[0]], 'b': [nombres[j] for j in iu[1]], 'observado': cop.objetivo[iu], 'media_replicas': S_media[iu], 'error_absoluto': err[iu]})
    pares_s = pares_s.sort_values('error_absoluto', ascending=False)
    N.a_csv(pares_s, S / f'propiedades_spearman_pares_alpha_{alfa:g}.csv')
    vp_tab = pd.DataFrame({'componente': range(1, 11), 'P1_observado': vp_o[:10], 'P1_replicas_media': np.mean(vps, axis=0)[:10], 'P1_replicas_de': np.std(vps, axis=0, ddof=1)[:10], 'F1_observado': vpf_o[:10], 'F1_replicas_media': np.mean(vpsf, axis=0)[:10], 'F1_replicas_de': np.std(vpsf, axis=0, ddof=1)[:10]})
    N.a_csv(vp_tab, S / f'propiedades_valores_propios_alpha_{alfa:g}.csv')
    v_m = np.mean(v_rep, axis=0)
    N.a_csv(pd.DataFrame({'a': [a for a, _ in pares_v], 'b': [b for _, b in pares_v], 'v_observado': v_obs, 'v_replicas_media': v_m, 'diferencia': v_obs - v_m}).sort_values('diferencia', ascending=False), S / f'propiedades_v_cramer_alpha_{alfa:g}.csv')
    marg = pd.DataFrame(marg)
    logica = pd.DataFrame(logica)
    err_vp = np.abs(np.mean(vps, axis=0)[:3] / vp_o[:3] - 1)
    err_vpf = np.abs(np.mean(vpsf, axis=0)[:3] / vpf_o[:3] - 1)
    resumen = {'marginales_exactas': bool(marg['iguales'].all()), 'logica_madre_hija': bool(logica['coherente'].all()), 'error_max_spearman_media_replicas': float(err[iu].max()), 'error_medio_spearman_media_replicas': float(err[iu].mean()),
               'error_max_spearman_por_replica_mediana': float(np.median(S_rep_err)), 'error_calibracion_final': cop.historial[-1],
               'error_relativo_vp_P1_1a3': err_vp.tolist(), 'error_relativo_vp_F1_1a3': err_vpf.tolist(), 'v_cramer_media_observado': float(v_obs.mean()), 'v_cramer_media_replicas': float(v_m.mean()),
               'v_cramer_pares_observado_mayor_que_0_2': int((v_obs > 0.2).sum()), 'v_cramer_pares_replicas_mayor_que_0_2': float((np.array(v_rep) > 0.2).sum(axis=1).mean()),
               'dias_1_con_frecuencia_observado': incoh(obs), 'nota_incoherencia': 'Código 1 de dias_ejercicio_semana y alguna frecuencia con respuesta. Se mide, no se impone.',
               'criterios': {'spearman_max_0_05': bool(err[iu].max() <= 0.05), 'valores_propios_10pct': bool((err_vp < 0.10).all() and (err_vpf < 0.10).all())}}
    resumen['dias_1_con_frecuencia_replicas_media'] = float(np.mean([incoh(cop.muestrear(rng_replica(r))) for r in range(5)]))
    resumen['contraccion'] = alfa
    N.a_json(resumen, S / f'propiedades_alpha_{alfa:g}.json')
    return resumen


def tabla_sembrada(cad, cop, rng, grupos=3, efecto=1.0):
    """Tabla de prueba con grupos latentes sembrados: desplaza un bloque de variables en cada grupo y asigna valores por rangos, conservando las marginales."""
    n = len(cad.tabla)
    L = rng.standard_normal((n, len(cop.nombres))) @ np.linalg.cholesky(cop.R).T
    g = rng.integers(0, grupos, n)
    centros = rng.normal(0, efecto, (grupos, len(cop.nombres)))
    L = L + 1.5 * centros[g]
    t = cop.muestrear(np.random.default_rng(rng.integers(1 << 31)))
    for j, v in enumerate(cop.nombres):
        if v in ('imc', '__imc_ausente'):
            continue
        t[v] = cop.valores[v][np.argsort(np.argsort(L[:, j]))]
    for h, m in Q.MADRES.items():
        e = cop.defs[h]['madre']['estructural']
        s = t[h].astype(str) == e
        t[m] = np.where(s, 'NO', 'SI')
        t.loc[s, h] = ''
    return t


def controles():
    """Aplica la referencia a dos tablas de prueba. Cada tabla recibe su propia cópula."""
    Q.instalar_gancho()
    cad = N.Cadena()
    cop = construir(cad)
    casos = {'sin_grupos': cop.muestrear(np.random.default_rng([42, 900])), 'con_grupos_sembrados': tabla_sembrada(cad, cop, np.random.default_rng([42, 901]))}
    cfgs = [N.info_config(c) for c in ('F2_c05_km_k3', 'P2_c05_km_k3', 'F2_c03_km_k3', 'F2_c08_km_k4')]
    subs = Q.subconjuntos()[:10]
    filas = []
    for nombre, tabla in casos.items():
        c2 = RC.Copula(tabla, cad.defs['P1'][0], Q.MADRES, semilla=(42, 38), contraccion=cop.contraccion)
        esp = espacios(tabla)
        for cfg in cfgs:
            X = x_de(esp, cfg)
            l, _, _ = Q.ajustar(X, cfg['algoritmo'], cfg['k'])
            sil = Q.calidad(X, l)[0]['silueta']
            est = estabilidad_config(X, cfg, l, subs)[0]
            nul_s, nul_e = [], []
            for r in range(20):
                e2 = espacios(c2.muestrear(np.random.default_rng([42, 950, r])))
                X2 = x_de(e2, cfg)
                l2, _, _ = Q.ajustar(X2, cfg['algoritmo'], cfg['k'])
                nul_s.append(Q.calidad(X2, l2)[0]['silueta'])
                nul_e.append(estabilidad_config(X2, cfg, l2, subs)[0])
            filas.append({'caso': nombre, 'config': cfg['config'], 'silueta_obs': sil, 'silueta_nula_media': np.mean(nul_s), 'silueta_nula_max': np.max(nul_s), 'silueta_p': (1 + np.sum(np.array(nul_s) >= sil)) / 21, 'silueta_z': (sil - np.mean(nul_s)) / np.std(nul_s, ddof=1),
                          'ari_entre_obs': est, 'ari_entre_nula_media': np.mean(nul_e), 'ari_entre_nula_max': np.max(nul_e), 'ari_entre_p': (1 + np.sum(np.array(nul_e) >= est)) / 21})
            print(nombre, cfg['config'], {k: round(v, 3) for k, v in filas[-1].items() if isinstance(v, float)}, flush=True)
    t = pd.DataFrame(filas)
    N.a_csv(t, S / 'controles_sinteticos.csv')
    ok = {'sin_grupos_no_supera': bool((t[t['caso'] == 'sin_grupos']['silueta_p'] > 0.05).sum() >= 3), 'con_grupos_supera': bool((t[t['caso'] == 'con_grupos_sembrados']['silueta_p'] < 0.05).all())}
    N.a_json(ok, S / 'controles_sinteticos.json')
    print(ok)


def replicas(procesos, alfa=None, carpeta='lotes', total=N_TOTAL):
    sello = N.huella_sello()
    prop = N.leer_json(S / 'propiedades_referencia.json')
    ctrl = N.leer_json(S / 'controles_sinteticos.json')
    if alfa is None and not (all(prop['criterios'].values()) and prop['marginales_exactas'] and prop['logica_madre_hija'] and all(ctrl.values())):
        raise SystemExit(f'La referencia no cumple el criterio de validez: {prop["criterios"]} {ctrl}. No se ejecuta; se documenta la limitación.')
    cfgs = [N.info_config(c) for c in N.priorizadas()]
    subs = Q.subconjuntos()
    trabajos = [(r, cfgs, subs, sello, carpeta) for r in range(total)]
    t0 = time.time()
    with mp.Pool(procesos, initializer=iniciar, initargs=(alfa,)) as pool:
        res = list(pool.imap_unordered(trabajo, trabajos, chunksize=1))
    N.registrar('referencia correlacionada', res)
    malos = [r for r in res if r[1] not in ('completa', 'omitida')]
    print('Réplicas:', len(res), '| nuevas:', sum(r[1] == 'completa' for r in res), '| con error:', len(malos), f'| {time.time() - t0:.0f} s')
    for r in malos[:5]:
        print(r[:2])
    return 1 if malos else 0


def observados():
    """Métricas observadas de la Fase 37B y estabilidad E1 con la reducción reajustada en los datos reales."""
    t = N.tabla_37b()
    comp = pd.read_csv(N.BASE / 'estabilidad' / 'comparacion_niveles.csv').set_index('config')
    filas = []
    for c in N.priorizadas():
        filas.append({'config': c, 'silueta': t.loc[c, 'silueta'], 'davies_bouldin': t.loc[c, 'davies_bouldin'], 'calinski_harabasz': t.loc[c, 'calinski_harabasz'], 'fraccion_eje1': t.loc[c, 'fraccion_eje1'],
                      'E0_ari_entre_media': t.loc[c, 'ari_entre_media'], 'E0_ari_completo_media': t.loc[c, 'ari_completo_media'], 'E1_ari_entre_media': comp.loc[c, 'E1_entre_media'], 'E1_ari_completo_media': comp.loc[c, 'E1_completo_media']})
    return pd.DataFrame(filas).set_index('config')


def consolidar_alfa0():
    """Contraste informativo de la enmienda 1: versión sin contracción, que NO cumple el criterio de validez. No entra en la decisión."""
    rep = pd.concat([pd.read_csv(S / 'lotes_alpha0' / f'replica_{r:03d}.csv') for r in range(N_EST)], ignore_index=True)
    obs = observados()
    filas = []
    for c in obs.index:
        d = rep[rep['config'] == c]
        fila = {'config': c, 'nota': 'No válida según el criterio; solo informativa'}
        for m in ('silueta', 'E0_ari_entre_media', 'E1_ari_entre_media'):
            v = d[m].to_numpy()
            fila.update({f'{m}_obs': float(obs.loc[c, m]), f'{m}_nula_media': v.mean(), f'{m}_nula_max': v.max(), f'{m}_supera_todas': bool(obs.loc[c, m] > v.max())})
        filas.append(fila)
    N.a_csv(pd.DataFrame(filas), S / 'contraste_sin_contraccion.csv')


def consolidar():
    consolidar_alfa0()
    rep = pd.concat([pd.read_csv(S / 'lotes' / f'replica_{r:03d}.csv') for r in range(N_TOTAL)], ignore_index=True)
    N.a_csv(rep, S / 'metricas_por_replica.csv')
    obs = observados()
    filas = []
    for c in obs.index:
        d = rep[rep['config'] == c]
        fila = {'config': c}
        for m in METRICAS + METRICAS_EST:
            v = d[m].dropna().to_numpy()
            o = float(obs.loc[c, m])
            signo = -1 if m == 'davies_bouldin' else 1
            mejores = int(np.sum(signo * v >= signo * o))
            fila.update({f'{m}_obs': o, f'{m}_nula_media': v.mean(), f'{m}_nula_de': v.std(ddof=1), f'{m}_nula_min': v.min(), f'{m}_nula_max': v.max(), f'{m}_z': signo * (o - v.mean()) / v.std(ddof=1) if v.std(ddof=1) > 0 else np.nan, f'{m}_p': (1 + mejores) / (len(v) + 1), f'{m}_supera_todas': mejores == 0, f'{m}_n_replicas': len(v)})
        filas.append(fila)
    comp = pd.DataFrame(filas)
    N.a_csv(comp, S / 'comparacion_por_configuracion.csv')
    # Búsqueda múltiple, con z de cada réplica calculado con media y DE de las demás
    busq = []
    for m in METRICAS[:3] + METRICAS_EST:
        piv = rep.pivot(index='replica', columns='config', values=m).dropna(how='all')
        signo = -1 if m == 'davies_bouldin' else 1
        A = signo * piv[obs.index].to_numpy()
        o = signo * obs[m].to_numpy()
        z_obs = (o - A.mean(axis=0)) / A.std(axis=0, ddof=1)
        z_rep, conteo_rep = [], []
        for i in range(len(A)):
            resto = np.delete(A, i, axis=0)
            z_rep.append(((A[i] - resto.mean(axis=0)) / resto.std(axis=0, ddof=1)).max())
            conteo_rep.append(int((A[i] > resto.max(axis=0)).sum()))
        busq.append({'metrica': m, 'replicas': len(A), 'configuraciones': len(o), 'superan_todas_obs': int((o > A.max(axis=0)).sum()), 'superan_todas_replicas_mediana': float(np.median(conteo_rep)), 'superan_todas_replicas_max': int(np.max(conteo_rep)),
                     'z_max_obs': float(z_obs.max()), 'config_z_max': obs.index[int(z_obs.argmax())], 'z_max_replicas_mediana': float(np.median(z_rep)), 'z_max_replicas_max': float(np.max(z_rep)), 'p_max': (1 + int(np.sum(np.array(z_rep) >= z_obs.max()))) / (len(A) + 1)})
    b = pd.DataFrame(busq)
    N.a_csv(b, S / 'busqueda_multiple.csv')
    print(b.round(3).to_string())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--paso', required=True, choices=['propiedades', 'controles', 'replicas', 'replicas_alpha0', 'consolidar'])
    ap.add_argument('--procesos', type=int, default=10)
    a = ap.parse_args()
    N.huella_sello()
    S.mkdir(parents=True, exist_ok=True)
    if a.paso == 'propiedades':
        propiedades()
    elif a.paso == 'controles':
        controles()
    elif a.paso == 'replicas':
        return replicas(a.procesos)
    elif a.paso == 'replicas_alpha0':
        return replicas(a.procesos, 0.0, 'lotes_alpha0', N_EST)
    else:
        consolidar()
    return 0


if __name__ == '__main__':
    sys.exit(main())
