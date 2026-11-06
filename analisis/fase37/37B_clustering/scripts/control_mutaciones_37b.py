"""
Fase 37B: pruebas negativas. Introduce errores en memoria y exige que la prueba correspondiente los detecte. No modifica resultados.

Uso, desde analisis/: python fase37/37B_clustering/scripts/control_mutaciones_37b.py
"""
import nucleo_37b as Q
import numpy as np
import pandas as pd
import pruebas_37b as PA

ORIG = {k: getattr(PA, k) for k in ('lote', 'tabla', 'etiquetas', 'permutar', 'X_de')}
ORIG_Q = {'subconjuntos': Q.subconjuntos}


def et_fila_perdida():
    return ORIG['etiquetas']().iloc[:-1]


def et_desordenadas():
    return ORIG['etiquetas']().iloc[::-1].reset_index(drop=True)


def et_grupo_extra():
    e = ORIG['etiquetas']()
    e.loc[0, 'P1_c02_km_k2'] = 5
    return e


def et_cambio_grupo():
    e = ORIG['etiquetas']()
    e['P1_c02_km_k2'] = 1 - e['P1_c02_km_k2']
    e.loc[:40, 'P1_c02_km_k2'] = 0
    return e


def tabla_con(ruta, cambio):
    def f(r):
        t = ORIG['tabla'](r)
        return cambio(t) if r == ruta else t
    return f


def _sumar(t, col, v):
    t[col] = t[col] + v
    return t


def lote_con(cambio):
    def f(c):
        d = dict(ORIG['lote'](c))
        return cambio(d)
    return f


def _mal_inercia(d):
    if d['algoritmo'] == 'km':
        d['inercia'] = d['inercia'] * 1.2
    d['centroides'] = (np.array(d['centroides']) * 2).tolist()
    return d


def _mal_huella(d):
    d['huella_entrada'] = '0' * 64
    return d


def _mal_protocolo(d):
    d['huella_protocolo'] = '0' * 64
    return d


def _mal_ari(d):
    d['ari_completo_rep'] = [x + 0.05 for x in d['ari_completo_rep']]
    return d


def _mal_ari_entre(d):
    d['ari_entre_media'] = d['ari_entre_media'] + 0.1
    return d


def X_reescalada(c):
    X = ORIG['X_de'](c)
    return X / X.std(axis=0)


def perm_solo_uno(p, r):
    """Mal: una sola permutación para todas las variables. Solo reordena filas y conserva las asociaciones."""
    return p.iloc[np.random.default_rng(r).permutation(len(p))].set_axis(p.index)


def perm_madre_separada(p, r):
    t = ORIG['permutar'](p, r)
    t['realiza_aerobico'] = p['realiza_aerobico'].to_numpy()
    return t


def perm_marginal_rota(p, r):
    t = ORIG['permutar'](p, r)
    t['edad'] = '50'
    return t


def subs_repetidos():
    s = ORIG_Q['subconjuntos']()
    s[1] = s[0]
    return s


def subs_tamano():
    return [x[:400] for x in ORIG_Q['subconjuntos']()]


def _lista_inflada(t):
    t['lista_37C'] = True
    return t


def _nula_recortada(t):
    return t[t['replica'] < 10]


def _sens_mal_proy(t):
    t.loc[t['sensibilidad'] == 'S-ORD', 'ari_proyeccion'] = 0.5
    return t


def _sens_mal_filas(t):
    t.loc[t['sensibilidad'] == 'S-TRA', 'filas_ajuste'] = 529
    return t


MUTACIONES = [
    ('Se pierde una fila de etiquetas', {'etiquetas': et_fila_perdida}, {}, ['p02']),
    ('Etiquetas en otro orden', {'etiquetas': et_desordenadas}, {}, ['p03']),
    ('Etiqueta fuera de los k grupos', {'etiquetas': et_grupo_extra}, {}, ['p08']),
    ('Etiquetas que no corresponden a los tamaños', {'etiquetas': et_cambio_grupo}, {}, ['p09']),
    ('Huella de entrada incorrecta', {'lote': lote_con(_mal_huella)}, {}, ['p01']),
    ('Coordenadas reescaladas', {'X_de': X_reescalada}, {}, ['p05', 'p10']),
    ('Inercia y centroides alterados', {'lote': lote_con(_mal_inercia)}, {}, ['p05', 'p19']),
    ('Silueta alterada en la tabla', {'tabla': tabla_con('resultados/metricas_calidad.csv', lambda t: _sumar(t, 'silueta', 0.05))}, {}, ['p10']),
    ('Davies-Bouldin alterado en la tabla', {'tabla': tabla_con('resultados/metricas_calidad.csv', lambda t: _sumar(t, 'davies_bouldin', 0.05))}, {}, ['p10']),
    ('ARI de remuestreo alterado', {'lote': lote_con(_mal_ari)}, {}, ['p11']),
    ('Estabilidad alterada', {'lote': lote_con(_mal_ari_entre)}, {}, ['p12', 'p23']),
    ('Subconjuntos repetidos', {}, {'subconjuntos': subs_repetidos}, ['p12']),
    ('Subconjuntos de otro tamaño', {}, {'subconjuntos': subs_tamano}, ['p12']),
    ('Nula con una sola permutación', {'permutar': perm_solo_uno}, {}, ['p14']),
    ('Nula con la madre separada de su frecuencia', {'permutar': perm_madre_separada}, {}, ['p14']),
    ('Nula con marginal alterada', {'permutar': perm_marginal_rota}, {}, ['p14']),
    ('Nula incompleta', {'tabla': tabla_con('referencia_nula/metricas_por_replica.csv', _nula_recortada)}, {}, ['p14']),
    ('Proyección donde no corresponde', {'tabla': tabla_con('sensibilidades/comparacion_sensibilidades.csv', _sens_mal_proy)}, {}, ['p16']),
    ('Filas de ajuste incorrectas', {'tabla': tabla_con('sensibilidades/comparacion_sensibilidades.csv', _sens_mal_filas)}, {}, ['p16']),
    ('Huella de protocolo incorrecta', {'lote': lote_con(_mal_protocolo)}, {}, ['p17']),
    ('Acuerdo de K-means alterado', {'tabla': tabla_con('prototipos/evaluacion_asignacion.csv', lambda t: _sumar(t, 'acuerdo_prototipo_pct', -1.0))}, {}, ['p18', 'p19']),
    ('Lista para la Fase 37C inflada', {'tabla': tabla_con('resultados/tabla_completa_configuraciones.csv', _lista_inflada)}, {}, ['p24']),
]


def main():
    filas = []
    for nombre, cambios, cambios_q, pruebas in MUTACIONES:
        for k, f in cambios.items():
            setattr(PA, k, f)
        for k, f in cambios_q.items():
            setattr(Q, k, f)
        for p in pruebas:
            try:
                getattr(PA, p)()
                detectado = False
            except Exception:  # noqa: BLE001
                detectado = True
            filas.append({'error_introducido': nombre, 'prueba': p, 'detectado': detectado})
            print(nombre, p, detectado, flush=True)
        for k in cambios:
            setattr(PA, k, ORIG[k])
        for k in cambios_q:
            setattr(Q, k, ORIG_Q[k])
    t = pd.DataFrame(filas)
    t.to_csv(Q.BASE / 'pruebas' / 'control_mutaciones.csv', index=False, encoding='utf-8', lineterminator='\n')
    print(f'{t["detectado"].sum()} de {len(t)} detectados; {t["error_introducido"].nunique()} errores')
    return 0 if t['detectado'].all() else 1


if __name__ == '__main__':
    raise SystemExit(main())
