"""
Complemento de la Fase 37C: las 30 repeticiones fuera de muestra. Cada una ajusta todo con su submuestra (cadena E3 de la Fase 37C), congela y evalúa en las 106 no usadas. Guarda cada repetición y omite las ya válidas al reanudar.

Uso, desde analisis/: python fase37/37C_complemento_tres_preguntas/scripts/repeticiones_complemento.py [--procesos 2] [--reps 30]
"""
import argparse
import json
import multiprocessing as mp
import sys
import time
from itertools import combinations
from pathlib import Path
from types import SimpleNamespace

import nucleo_complemento as C
import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score

N, Q, IN = C.N, C.Q, C.IN
CAD = None
OBJ = None
AZAR = None


def iniciar():
    global CAD, OBJ, AZAR
    Q.instalar_gancho()
    CAD = N.Cadena()
    OBJ = C.objetivos(CAD)
    AZAR = C.trios_azar()


def codificar_en_entrenamiento(tabla, idx):
    """Celdas para la búsqueda anidada: como en la Fase 37C, pero con los cuartiles fijados solo en el entrenamiento."""
    defs, vals = IN.numericos(SimpleNamespace(defs=CAD.defs, tabla=tabla))
    enc = {}
    for v, d in defs.items():
        x = vals[v]
        if d['tipo'] == 'cuantitativa':
            x = np.asarray(x, dtype=float)
            cortes = np.nanquantile(x[idx], [0.25, 0.5, 0.75])
            q = np.digitize(x, cortes, right=True)
            q[np.isnan(x)] = 4
            enc[v] = q
        else:
            enc[v] = pd.factorize(x, sort=True)[0]
    return enc


def busqueda_anidada(tabla, idx, l, r):
    """Mejor trío usando solo el entrenamiento y sus etiquetas. Devuelve el trío y su predicción para las 529."""
    enc = codificar_en_entrenamiento(tabla, idx)
    pliegues = IN.particiones_cv(len(idx), (42, 500 + r))
    mejor, trio = -1.0, None
    for a, b, e in combinations(list(enc), 3):
        cod = pd.factorize(enc[a] * 10000 + enc[b] * 100 + enc[e])[0]
        s = IN.reconstruir(pd.factorize(cod[idx])[0], l, pliegues, C.K)
        if s > mejor:
            mejor, trio = s, (a, b, e)
    cod = pd.factorize(enc[trio[0]] * 10000 + enc[trio[1]] * 100 + enc[trio[2]])[0]
    mapa = C.tabla_celdas(cod[idx], l, C.K, cod.max() + 1)[0]
    return trio, mejor, mapa[cod]


def informacion(r, idx, resto, part):
    filas = []
    for v, o in OBJ.items():
        bloque = C.BLOQUE_DE.get(v, 'IMC observado')
        X = bloque if bloque in part['sin_bloque'] else None
        sb = part['sin_bloque'][X] if X else {k: part[k] for k in C.VARIANTES_A}
        D = {x: C.indicadores(part[x]) for x in ('A', 'B1', 'B2', 'B2C', 'celdas')}
        D['A-X'] = C.indicadores(sb['A'])
        D['A8-X'] = C.indicadores(sb['A8'])
        D['A16-X'] = C.indicadores(sb['A16'])
        D['celdas+A'] = np.hstack([D['celdas'], D['A']])
        D['celdas+A-X'] = np.hstack([D['celdas'], D['A-X']])
        D['celdas+A8-X'] = np.hstack([D['celdas'], D['A8-X']])
        D['celdas+A16-X'] = np.hstack([D['celdas'], D['A16-X']])
        for nombre, m in D.items():
            filas.append({'repeticion': r, 'variable': v, 'bloque': bloque, 'particion': nombre, 'r2_fuera': C.r2_fuera(m, o['Y'], o['marca'], idx, resto)})
    return filas


def trabajo(arg):
    r, idx, sello, salida = arg
    nombre = f'r{r:02d}'
    carpeta = Path(salida) / 'fuera_de_muestra' / 'lotes'
    destino, marca, tabla_info = carpeta / f'{nombre}.npz', carpeta / f'{nombre}.json', carpeta / f'{nombre}_info.csv'
    if destino.exists() and marca.exists() and tabla_info.exists() and N.leer_json(marca).get('huella_protocolo') == sello:
        return nombre, 'omitida', 0.0, Q.leidos()
    t0 = time.time()
    try:
        resto = np.setdiff1d(np.arange(Q.N), idx)
        semilla = Q.semilla_rep(r)
        tabla, imputaciones = CAD.tabla_imputada(idx)
        Zd = CAD.calibrada(C.ESPACIO, tabla, idx)
        columnas, Z = list(Zd.columns), Zd.to_numpy()
        F, _ = N.coordenadas_cadena(Z, idx)
        part = {}
        margenes = {}
        for n, c in C.VARIANTES_A.items():
            X = F[:, :c]
            l, _, centros = Q.ajustar_km(X[idx], C.K, semilla)
            et, _, _, m = Q.asignar(centros, X)
            et[idx] = l
            part[n], margenes[n] = et.astype(int), m
        cod = C.celdas(tabla)
        part['celdas'] = cod
        mapa, pureza, _ = C.tabla_celdas(cod[idx], part['A'][idx])
        part['B1'] = mapa[cod]
        Z3 = Z[:, [columnas.index(v) for v in C.TRIO]]
        part['B2'], margen_b2, centros_b2, _ = C.ajustar_b2(Z3, idx, semilla)
        part['B2C'], corte = C.ajustar_cruce(tabla, idx, semilla)
        trio_n, valor_n, part['B1N'] = busqueda_anidada(tabla, idx, part['A'][idx], r)
        part['sin_bloque'] = {b: C.a_sin_bloque(Z, columnas, b, idx, semilla) for b in C.BLOQUES}
        azar = {}
        for i, t in enumerate(AZAR):
            azar[f'T{i:02d}'] = C.ajustar_b2(Z[:, [columnas.index(v) for v in t]], idx, semilla)[0].astype(np.int8)
        info = pd.DataFrame(informacion(r, idx, resto, part))
        etiquetas = {k: part[k].astype(np.int16) for k in ('A', 'A8', 'A16', 'B1', 'B2', 'B2C', 'B1N', 'celdas')}
        etiquetas.update(azar)
        etiquetas.update({f'AX__{b}': part['sin_bloque'][b]['A'].astype(np.int8) for b in C.BLOQUES})
        carpeta.mkdir(parents=True, exist_ok=True)
        tmp = destino.with_name(destino.stem + '_tmp.npz')
        np.savez_compressed(tmp, margen_A=margenes['A'], margen_B2=margen_b2, **etiquetas)
        tmp.replace(destino)
        info.to_csv(tabla_info, index=False, encoding='utf-8', lineterminator='\n')
        marca.write_text(json.dumps({'huella_protocolo': sello, 'repeticion': r, 'mapa_b1': mapa.tolist(), 'pureza_b1': [None if np.isnan(x) else float(x) for x in pureza], 'centros_b2': centros_b2.tolist(), 'corte_ejercicio': corte, 'trio_anidado': list(trio_n), 'valor_interno_anidado': valor_n, 'imputaciones': imputaciones}, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')
        return nombre, 'completa', time.time() - t0, Q.leidos()
    except Exception as ex:  # noqa: BLE001
        return nombre, f'error: {type(ex).__name__}: {ex}', time.time() - t0, Q.leidos()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--procesos', type=int, default=2)
    ap.add_argument('--reps', type=int, default=Q.N_REP)
    ap.add_argument('--salida', default=str(C.BASE))
    a = ap.parse_args()
    if a.procesos > 2:
        raise SystemExit('El protocolo limita a 2 procesos.')
    sello = C.huella()
    subs = Q.subconjuntos()[:a.reps]
    trabajos = [(r, subs[r], sello, a.salida) for r in range(len(subs))]
    t0 = time.time()
    with mp.Pool(a.procesos, initializer=iniciar) as pool:
        res = []
        for x in pool.imap_unordered(trabajo, trabajos, chunksize=1):
            res.append(x)
            print(x[0], x[1], round(x[2]), 's', flush=True)
    if Path(a.salida).resolve() == C.BASE:
        C.registrar('repeticiones', res)
    malos = [x for x in res if x[1] not in ('completa', 'omitida')]
    print('Trabajos', len(res), '| con error', len(malos), f'| {time.time() - t0:.0f} s')
    for m in malos[:3]:
        print(m[:2])
    return 1 if malos else 0


if __name__ == '__main__':
    sys.exit(main())
