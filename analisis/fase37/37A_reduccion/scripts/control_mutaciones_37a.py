"""
Fase 37A: comprueba que las pruebas pueden fallar. Introduce errores en memoria y exige que la prueba correspondiente los detecte.

Uso, desde analisis/: python fase37/37A_reduccion/scripts/control_mutaciones_37a.py
No modifica resultados: sustituye funciones de lectura durante la ejecución. Escribe solo pruebas/control_mutaciones.csv.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.dont_write_bytecode = True
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

import pruebas_37a as PA  # noqa: E402

ORIGINAL = {k: getattr(PA, k) for k in ('coordenadas', 'modelo', 'matriz', 'tabla')}


def coord_fila_perdida(e, k):
    return ORIGINAL['coordenadas'](e, k).iloc[:-1]


def coord_desordenada(e, k):
    return ORIGINAL['coordenadas'](e, k).iloc[::-1].reset_index(drop=True)


def coord_reescalada(e, k):
    c = ORIGINAL['coordenadas'](e, k)
    c.iloc[:, 1:] = c.iloc[:, 1:] / c.iloc[:, 1:].std(ddof=0)
    return c


def coord_sin_prefijo(e, k):
    c = ORIGINAL['coordenadas'](e, k)
    if k == 5:
        c['C2'] = -c['C2']
    return c


def modelo_sin_factor(e):
    m = ORIGINAL['modelo'](e)
    m['valores_propios'] = (np.array(m['valores_propios']) * 529 / 528).tolist()
    return m


def modelo_no_ortogonal(e):
    m = ORIGINAL['modelo'](e)
    v = np.array(m['componentes'])
    v[1] = v[1] + 0.01 * v[0]
    m['componentes'] = v.tolist()
    return m


def modelo_con_mrs(e):
    m = ORIGINAL['modelo'](e)
    m['columnas'] = m['columnas'] + ['severo_mrs']
    return m


def modelo_lambda_negativa(e):
    m = ORIGINAL['modelo'](e)
    m['valores_propios'][-1] = -0.5
    return m


def imc_reescalado(e):
    m = ORIGINAL['matriz'](e)
    if 'imc' in m:
        m['imc'] = m['imc'] / m['imc'].std(ddof=0)
    return m


def tabla_alterada(n, **k):
    t = ORIGINAL['tabla'](n, **k)
    if n == 'contribucion_variables.csv':
        t['aporte_absoluto'] = t['aporte_absoluto'] * 1.01
    if n == 'famd_baricentros.csv':
        t['baricentro'] = t['baricentro'] + 0.1
    return t


MUTACIONES = [
    ('Se pierde una fila de coordenadas', {'coordenadas': coord_fila_perdida}, ['p01']),
    ('Coordenadas en otro orden', {'coordenadas': coord_desordenada}, ['p02']),
    ('Coordenadas reescaladas', {'coordenadas': coord_reescalada}, ['p04']),
    ('Un candidato no coincide con los primeros ejes', {'coordenadas': coord_sin_prefijo}, ['p17']),
    ('Valores propios sin el factor 528/529', {'modelo': modelo_sin_factor}, ['p07', 'p08']),
    ('Componentes no ortogonales', {'modelo': modelo_no_ortogonal}, ['p07', 'p09']),
    ('Entra una variable del MRS', {'modelo': modelo_con_mrs}, ['p05']),
    ('Valor propio negativo', {'modelo': modelo_lambda_negativa}, ['p06']),
    ('IMC estandarizado otra vez', {'matriz': imc_reescalado}, ['p03', 'p08']),
    ('Contribuciones alteradas', {'tabla': tabla_alterada}, ['p18']),
    ('Baricentros alterados', {'tabla': tabla_alterada}, ['p19']),
]


def main():
    filas = []
    for nombre, cambios, pruebas in MUTACIONES:
        for k, f in cambios.items():
            setattr(PA, k, f)
        for p in pruebas:
            try:
                getattr(PA, p)()
                detectada = False
            except Exception:  # noqa: BLE001
                detectada = True
            filas.append({'error_introducido': nombre, 'prueba': p, 'detectado': detectada})
        for k in cambios:
            setattr(PA, k, ORIGINAL[k])
    t = pd.DataFrame(filas)
    t.to_csv(AQUI.parent / 'pruebas' / 'control_mutaciones.csv', index=False, encoding='utf-8', lineterminator='\n')
    print(t.to_string())
    print(f'{t["detectado"].sum()} de {len(t)} detectados')
    return 0 if t['detectado'].all() else 1


if __name__ == '__main__':
    raise SystemExit(main())
