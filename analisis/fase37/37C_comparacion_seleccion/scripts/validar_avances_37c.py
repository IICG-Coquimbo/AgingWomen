"""
Fase 37C: valida los avances antes de reutilizarlos. Comprueba sello, parámetros de la cópula, dimensiones y etiquetas de cada lote, y recalcula una métrica de cada réplica.
Un lote que no pase queda listado y se aparta como inválido para que se recalcule. Corre en un solo proceso.

Uso, desde analisis/: python fase37/37C_comparacion_seleccion/scripts/validar_avances_37c.py
"""
import sys

import nucleo_37c as N
import numpy as np
import nula_37c as NU
import pandas as pd

Q = N.Q
B = N.BASE
ESPERADAS = ['replica', 'config', 'silueta', 'silueta_negativos', 'davies_bouldin', 'calinski_harabasz', 'tam_min', 'equilibrio', 'fraccion_eje1']
EST = ['E0_ari_entre_media', 'E0_ari_completo_media', 'E1_ari_entre_media', 'E1_ari_completo_media']
CONTROL = 'F2_c05_km_k3'


def main():
    sello = N.huella_sello()
    Q.instalar_gancho()
    enm = N.leer_json(B / 'protocolo' / 'sello_enmienda_1.json')
    if N.sha(B / 'protocolo' / enm['archivo']) != enm['sha256']:
        raise SystemExit('La enmienda cambió después de sellarse.')
    alfa = NU.alfa_elegido()
    if alfa != 0.05:
        raise SystemExit(f'Alfa inesperado: {alfa}')
    cad = N.Cadena()
    cop = NU.construir(cad)
    guardado = N.leer_json(B / 'referencias_nulas' / 'parametros_copula_alpha_0.05.json')
    dif_r = float(np.abs(np.array(guardado['R_latente']) - cop.R).max())
    if guardado['contraccion'] != 0.05 or dif_r > 1e-10:
        raise SystemExit(f'Los parámetros de la cópula no coinciden: {dif_r}')
    print('Sello, enmienda y cópula correctos; diferencia máxima de R:', dif_r, flush=True)
    configs = set(N.priorizadas())
    filas = []
    carpeta = NU.S / 'lotes'
    for t in carpeta.glob('*.tmp'):
        filas.append({'archivo': t.name, 'replica': -1, 'estado': 'temporal incompleto', 'detalle': 'Se ignora', 'sha256': ''})
    for r in range(NU.N_TOTAL):
        csv, marca = carpeta / f'replica_{r:03d}.csv', carpeta / f'replica_{r:03d}.json'
        if not csv.exists() and not marca.exists():
            filas.append({'archivo': csv.name, 'replica': r, 'estado': 'pendiente', 'detalle': '', 'sha256': ''})
            continue
        problema = ''
        try:
            if not (csv.exists() and marca.exists()):
                raise ValueError('falta el lote o su marca')
            m = N.leer_json(marca)
            if m.get('huella_protocolo') != sello or m.get('replica') != r or m.get('configuraciones') != 50:
                raise ValueError(f'marca incorrecta: {m}')
            d = pd.read_csv(csv)
            faltan = [c for c in ESPERADAS + (EST if r < NU.N_EST else []) if c not in d.columns]
            if faltan or len(d) != 50 or set(d['config']) != configs or (d['replica'] != r).any():
                raise ValueError(f'dimensiones o columnas: {d.shape} {faltan}')
            if d[[c for c in ESPERADAS if c not in ('config',)] + (EST if r < NU.N_EST else [])].isna().any().any():
                raise ValueError('valores faltantes')
            esp = NU.espacios(cop.muestrear(NU.rng_replica(r)))
            i = N.info_config(CONTROL)
            X = NU.x_de(esp, i)
            s = Q.calidad(X, Q.ajustar(X, i['algoritmo'], i['k'])[0])[0]['silueta']
            esperado = float(d.set_index('config').loc[CONTROL, 'silueta'])
            if abs(s - esperado) > 1e-9:
                raise ValueError(f'no se reproduce: {s} frente a {esperado}')
        except Exception as ex:  # noqa: BLE001
            problema = f'{type(ex).__name__}: {ex}'
        if problema:
            for p in (csv, marca):
                if p.exists():
                    p.replace(p.with_name(p.name + '.invalido'))
        filas.append({'archivo': csv.name, 'replica': r, 'estado': 'inválida, se recalcula' if problema else 'recuperada', 'detalle': problema or f'50 configuraciones; silueta de control reproducida', 'sha256': '' if problema else N.sha(csv)})
        print(r, filas[-1]['estado'], flush=True)
    t = pd.DataFrame(filas)
    N.a_csv(t, B / 'integridad' / 'validacion_replicas.csv')
    # Lotes de estabilidad
    malos = []
    total = 0
    for base in Q.ESPACIOS:
        for nivel in N.NIVELES:
            for r in range(Q.N_REP):
                ruta = B / 'estabilidad' / 'lotes' / f'{base}_{nivel}_r{r:02d}.npz'
                try:
                    if N.leer_json(ruta.with_suffix('.json'))['huella_protocolo'] != sello:
                        raise ValueError('huella')
                    z = np.load(ruta)
                    if any(z[c].shape != (Q.N,) for c in z.files):
                        raise ValueError('dimensiones')
                    total += 1
                except Exception as ex:  # noqa: BLE001
                    malos.append((ruta.name, str(ex)))
    res = {'alfa': alfa, 'diferencia_R': dif_r, 'replicas': t['estado'].value_counts().to_dict(), 'lotes_estabilidad_validos': total, 'lotes_estabilidad_con_problema': malos}
    N.a_json(res, B / 'integridad' / 'validacion_avances.json')
    print(res)
    N.registrar('validacion de avances', [('validacion', 'completa', 0.0, Q.leidos())])
    return 1 if malos else 0


if __name__ == '__main__':
    sys.exit(main())
