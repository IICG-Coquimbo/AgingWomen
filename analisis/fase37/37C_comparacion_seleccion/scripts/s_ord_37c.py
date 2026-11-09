"""
Fase 37C: análisis de S-ORD. Descompone el cambio entre códigos consecutivos y ridit en distancias, ejes y fronteras, identifica a quién cambia y qué variables pesan,
y compara tres representaciones ordinales. No usa el MRS.

Uso, desde analisis/: python fase37/37C_comparacion_seleccion/scripts/s_ord_37c.py [--procesos N]
"""
import argparse
import multiprocessing as mp
import sys
import time

import nucleo_37c as N
import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score

Q = N.Q
S = N.BASE / 'sensibilidades' / 's_ord'
CAD = None
MODOS = ('ridit', 'normal')


def iniciar():
    global CAD
    Q.instalar_gancho()
    CAD = N.Cadena()


def matrices(e):
    base = CAD.congelada(e)
    rid = pd.read_csv(N.F36 / 'sensibilidades' / 'S-ORD' / e / 'matriz.csv')
    if list(rid.columns) != list(base.columns):
        raise ValueError(f'{e}: columnas distintas entre base y ridit')
    return base, rid


def descomposicion(cfg_s):
    """Pasos H1 a H4 de la sección 6.1 para una configuración."""
    cfg = N.info_config(cfg_s)
    e, c, a, k = cfg['base'], cfg['componentes'], cfg['algoritmo'], cfg['k']
    Zb, Zr = matrices(e)
    et = N.etiquetas_37b()[cfg_s].to_numpy()
    H4 = pd.read_csv(N.B37 / 'sensibilidades' / 'etiquetas' / f'S-ORD_{e}.csv', dtype={'participante_id': str}).set_index('participante_id').loc[CAD.ids, f'{cfg["espacio"]}_{cfg_s.split("_", 1)[1]}' if cfg['espacio'].startswith('R0') else cfg_s].to_numpy() if not cfg['espacio'].startswith('R0') else None
    fila = {'config': cfg_s}
    if c == 0:
        Xb, X_h1, X_h3, sim = Zb.to_numpy(), Zr.to_numpy(), None, np.nan
    else:
        mb = N.R.cargar(N.A37 / 'artefactos' / e / 'modelo.json')
        mr = N.R.cargar(N.A37 / 'sensibilidades' / 'S-ORD' / e / 'modelo.json')
        Xb = N.R.proyectar(mb, Zb.to_numpy(), c)
        X_h1 = N.R.proyectar(mb, Zr.to_numpy(), c)
        X_h3 = N.R.proyectar(mr, Zb.to_numpy(), c)
        sim = N.R.similitud_subespacio(Xb, N.R.proyectar(mr, Zr.to_numpy(), c))
    protos = Q.prototipos(Xb, et, k)
    margen = Q.asignar(protos, Xb)[3]
    l1 = Q.asignar(protos, X_h1)[0]
    l2 = Q.ajustar(X_h1, a, k)[0]
    if H4 is None:
        H4 = Q.ajustar(Zr.to_numpy(), a, k)[0]
    fila.update({'similitud_subespacio': sim, 'H1_distancias_centroides_base': adjusted_rand_score(et, l1), 'H2_distancias_y_fronteras': adjusted_rand_score(et, l2),
                 'H3_ejes': adjusted_rand_score(et, Q.ajustar(X_h3, a, k)[0]) if X_h3 is not None else np.nan, 'H4_completa': adjusted_rand_score(et, H4)})
    al = N.alinear(et, H4)
    cambia = al != et
    q1 = margen <= np.percentile(margen, 25)
    fila.update({'cambian_n': int(cambia.sum()), 'cambian_pct': float(100 * cambia.mean()), 'auc_margen_bajo_predice_cambio': N.auc(-margen[cambia], -margen[~cambia]), 'margen_mediano_cambian': float(np.median(margen[cambia])) if cambia.any() else np.nan, 'margen_mediano_quedan': float(np.median(margen[~cambia])),
                 'pct_cambios_en_cuartil_menor_margen': float(100 * q1[cambia].mean()) if cambia.any() else np.nan, 'tamanos_base': ' '.join(map(str, np.bincount(et, minlength=k))), 'tamanos_ridit': ' '.join(map(str, np.bincount(H4, minlength=k)))})
    tr = N.transicion(et, H4).stack().reset_index()
    tr.columns = ['grupo_base', 'grupo_ridit_alineado', 'n']
    tr.insert(0, 'config', cfg_s)
    return fila, tr


def ordinales_z(e):
    cod = CAD.defs[e]
    return [d['variable'] for d in cod[0] if d['tipo'] == 'ordinal' and (e[0] == 'P' or d['rol'] == 'cuantitativa')]


def por_variable(cfg_s):
    """Cada ordinal pasa a ridit sola (entrada), o todas menos ella (salida). Reajusta reducción y agrupamiento."""
    cfg = N.info_config(cfg_s)
    e, c, a, k = cfg['base'], cfg['componentes'], cfg['algoritmo'], cfg['k']
    Zb, Zr = matrices(e)
    et = N.etiquetas_37b()[cfg_s].to_numpy()
    filas = []

    def particion(Z):
        Z = Z.to_numpy()
        if c == 0:
            return Q.ajustar(Z, a, k)[0]
        m = N.R.ajustar(Z, [f'x{i}' for i in range(Z.shape[1])])
        return Q.ajustar(N.R.proyectar(m, Z, c), a, k)[0]
    for v in ordinales_z(e):
        ent, sal = Zb.copy(), Zr.copy()
        ent[v] = Zr[v].to_numpy()
        sal[v] = Zb[v].to_numpy()
        filas.append({'config': cfg_s, 'variable': v, 'ari_solo_ella_en_ridit': adjusted_rand_score(et, particion(ent)), 'ari_todas_menos_ella_en_ridit': adjusted_rand_score(et, particion(sal))})
    return filas


def distancias_variable(e):
    """Cuánto cambia cada ordinal las distancias entre pares: media de |d²ridit − d²consecutiva| en esa columna."""
    Zb, Zr = matrices(e)
    filas = []
    for v in ordinales_z(e):
        a, b = Zb[v].to_numpy(), Zr[v].to_numpy()
        db, dr = (a[:, None] - a[None]) ** 2, (b[:, None] - b[None]) ** 2
        iu = np.triu_indices(len(a), 1)
        filas.append({'base': e, 'variable': v, 'cambio_medio_d2': float(np.abs(dr[iu] - db[iu]).mean()), 'correlacion_columnas': float(np.corrcoef(a, b)[0, 1]), 'niveles_presentes': int(len(np.unique(a)))})
    return filas


def representacion(arg):
    """Estabilidad E3 y partición completa para un modo, escenario y repetición. r = -1: ajuste con las 529."""
    e, modo, r, idx, cfgs = arg
    nombre = f'{e}_{modo}_r{r}'
    t0 = time.time()
    try:
        if r < 0:
            Z = CAD.matriz_nivel(e, 'E1', None, modo).to_numpy()
            idx = np.arange(Q.N)
        else:
            Z = CAD.matriz_nivel(e, 'E3', idx, modo).to_numpy()
        F, _ = N.coordenadas_cadena(Z, idx)
        salida = {}
        for c in cfgs:
            X = Z if c['componentes'] == 0 else F[:, :c['componentes']]
            salida[c['config']] = Q.ajustar(X[idx], c['algoritmo'], c['k'], Q.SEMILLA if r < 0 else Q.semilla_rep(r))[0]
        return nombre, 'completa', time.time() - t0, Q.leidos(), (e, modo, r, salida)
    except Exception as ex:  # noqa: BLE001
        return nombre, f'error: {type(ex).__name__}: {ex}', time.time() - t0, Q.leidos(), None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--procesos', type=int, default=10)
    a = ap.parse_args()
    N.huella_sello()
    S.mkdir(parents=True, exist_ok=True)
    pri = N.priorizadas()
    t0 = time.time()
    b = N.lista_b()
    variables = b + ['F1_c05_km_k2', 'P1_c05_km_k2']
    km = [c for c in pri if '_km_' in c]
    subs = Q.subconjuntos()
    with mp.Pool(a.procesos, initializer=iniciar) as pool:
        desc = pool.map(descomposicion, list(pri), chunksize=1)
        N.a_csv(pd.DataFrame([d[0] for d in desc]), S / 'descomposicion.csv')
        N.a_csv(pd.concat([d[1] for d in desc], ignore_index=True), S / 'transiciones.csv')
        print('Descomposición lista', round(time.time() - t0), flush=True)
        var = pool.map(por_variable, variables, chunksize=1)
        N.a_csv(pd.DataFrame([x for v in var for x in v]), S / 'efecto_por_variable.csv')
        N.a_csv(pd.DataFrame([x for v in pool.map(distancias_variable, Q.ESPACIOS) for x in v]), S / 'distancias_por_variable.csv')
        print('Por variable listo', round(time.time() - t0), flush=True)
        trabajos = []
        for e in Q.ESPACIOS:
            cfgs = [N.info_config(c) for c in km if N.info_config(c)['base'] == e]
            for modo in MODOS:
                trabajos.append((e, modo, -1, None, cfgs))
                trabajos.extend((e, modo, r, subs[r], cfgs) for r in range(len(subs)))
        res = pool.map(representacion, trabajos, chunksize=1)
    malos = [r for r in res if r[1] != 'completa']
    N.registrar('s_ord', [r[:4] for r in res])
    if malos:
        print(malos[:3])
        return 1
    # Consolidación de las representaciones
    et = N.etiquetas_37b()
    completas = {}
    por_rep = {}
    for _, _, _, _, (e, modo, r, sal) in res:
        for c, l in sal.items():
            if r < 0:
                completas[(c, modo)] = l
            else:
                por_rep.setdefault((c, modo), {})[r] = l
    e3 = pd.read_csv(N.BASE / 'estabilidad' / 'comparacion_niveles.csv').set_index('config')
    filas = []
    usadas = np.zeros((len(subs), Q.N), bool)
    for r, idx in enumerate(subs):
        usadas[r, idx] = True
    for c in km:
        base = et[c].to_numpy()
        fila = {'config': c, 'ari_consecutiva_ridit': adjusted_rand_score(base, completas[(c, 'ridit')]), 'ari_consecutiva_normal': adjusted_rand_score(base, completas[(c, 'normal')]), 'ari_ridit_normal': adjusted_rand_score(completas[(c, 'ridit')], completas[(c, 'normal')]),
                'E3_entre_media_consecutiva': e3.loc[c, 'E3_entre_media'], 'E3_entre_p05_consecutiva': e3.loc[c, 'E3_entre_p05']}
        for modo in MODOS:
            todas = np.full((len(subs), Q.N), -1, dtype=int)
            for r, idx in enumerate(subs):
                todas[r, idx] = por_rep[(c, modo)][r]
            entre = N.ari_pares_compartidos(todas, usadas)
            fila[f'E3_entre_media_{modo}'] = float(np.mean(entre))
            fila[f'E3_entre_p05_{modo}'] = float(np.percentile(entre, 5))
        fila['centralidad_consecutiva'] = (fila['ari_consecutiva_ridit'] + fila['ari_consecutiva_normal']) / 2
        fila['centralidad_ridit'] = (fila['ari_consecutiva_ridit'] + fila['ari_ridit_normal']) / 2
        fila['centralidad_normal'] = (fila['ari_consecutiva_normal'] + fila['ari_ridit_normal']) / 2
        filas.append(fila)
    N.a_csv(pd.DataFrame(filas), S / 'comparacion_representaciones.csv')
    print('S-ORD completo', round(time.time() - t0), 's')
    return 0


if __name__ == '__main__':
    sys.exit(main())
