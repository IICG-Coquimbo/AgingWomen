"""
Fase 36B: comprueba que las pruebas pueden fallar. Introduce errores en memoria y exige que la prueba correspondiente los detecte.

Uso, desde analisis/: python fase36/control_mutaciones.py
No modifica matrices ni artefactos: sustituye funciones de lectura durante la ejecución. Escribe solo fase36/pruebas/control_mutaciones.csv.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

import pruebas_fase36 as PF  # noqa: E402

ORIGINAL = {k: getattr(PF, k) for k in ('matriz', 'tr', 'celdas', 'leer', 'limpio')}


def fila_perdida(e):
    return ORIGINAL['matriz'](e).iloc[:-1]


def doble_escalado(e):
    m = ORIGINAL['matriz'](e)
    if 'imc' in m:
        m['imc'] = m['imc'] / m['imc'].std(ddof=0)
    return m


def columna_mrs(e):
    return ORIGINAL['matriz'](e).assign(severo_mrs=0.0)


def valor_no_finito(e):
    m = ORIGINAL['matriz'](e)
    m.iloc[0, 0] = np.nan
    return m


def nominal_sin_ponderar(e):
    m = ORIGINAL['matriz'](e)
    for c in [x for x in m.columns if x.startswith('quien_prepara_comidas__')]:
        m[c] = m[c] / m[c].std(ddof=0)
    return m


def salto_en_frecuencias(e):
    t = ORIGINAL['tr'](e)
    for v in PF.C.NUNCA_UNIFICADO:
        if 'mapa' in t.p['codificadores'][v]:
            t.p['codificadores'][v]['mapa']['1'] = 1
    return t


def heredado_perdido():
    c = ORIGINAL['celdas']()
    i = c.index[(c['variable'] == 'frecuencia_fuerza') & (c['pregunta_previa_imputada'] == '1')][0]
    c.loc[i, 'pregunta_previa_imputada'] = '0'
    return c


def verdad_leida(ruta, **k):
    t = ORIGINAL['leer'](ruta, **k)
    if Path(ruta).name == 'archivos_leidos.csv':
        t = pd.concat([t, pd.DataFrame({'archivo_leido': ['datos/sintetico/dataset_usuaria_verdad.csv']})], ignore_index=True)
    return t


def cero_de_sobrecarga(ruta, **k):
    t = ORIGINAL['leer'](ruta, **k)
    if Path(ruta).name == 'modulo_cuidados.csv':
        t.loc[0, PF.C.SOBRECARGA] = '0'
    return t


def relleno_laboral(ruta, **k):
    t = ORIGINAL['leer'](ruta, **k)
    if Path(ruta).name == 'modulo_laboral.csv':
        t.loc[0, 'lugar_trabajo_comprensivo'] = '0'
    return t


MUTACIONES = [
    ('Se pierde una fila', {'matriz': fila_perdida}, ['p01']),
    ('IMC estandarizado dos veces', {'matriz': doble_escalado}, ['p11', 'p18', 'p27']),
    ('Entra una variable del MRS', {'matriz': columna_mrs}, ['p03', 'p05']),
    ('Valor no finito en una matriz', {'matriz': valor_no_finito}, ['p05']),
    ('Nominal sin ponderar en PCA', {'matriz': nominal_sin_ponderar}, ['p19']),
    ('«Nunca» deja de unificarse', {'tr': salto_en_frecuencias}, ['p16']),
    ('Se pierde una marca de cero heredado', {'celdas': heredado_perdido}, ['p25', 'p29']),
    ('Se abre la verdad del simulador', {'leer': verdad_leida}, ['p23']),
    ('Aparece sobrecarga 0', {'leer': cero_de_sobrecarga}, ['p15']),
    ('Aparece un 0 laboral de relleno', {'leer': relleno_laboral}, ['p14']),
]


def main():
    filas = []
    for nombre, cambios, pruebas in MUTACIONES:
        for k, f in cambios.items():
            setattr(PF, k, f)
        for p in pruebas:
            try:
                getattr(PF, p)()
                detectada = False
            except Exception:  # noqa: BLE001
                detectada = True
            filas.append({'error_introducido': nombre, 'prueba': p, 'detectado': detectada})
        for k in cambios:
            setattr(PF, k, ORIGINAL[k])
    t = pd.DataFrame(filas)
    t.to_csv(AQUI / 'pruebas' / 'control_mutaciones.csv', index=False, encoding='utf-8', lineterminator='\n')
    print(t.to_string())
    print(f'{t["detectado"].sum()} de {len(t)} detectados')
    return 0 if t['detectado'].all() else 1


if __name__ == '__main__':
    raise SystemExit(main())
