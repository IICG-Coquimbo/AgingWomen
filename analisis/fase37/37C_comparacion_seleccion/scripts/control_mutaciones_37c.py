"""
Fase 37C: controles negativos. Introduce errores deliberados en memoria y exige que la prueba correspondiente falle. No modifica resultados.

Uso, desde analisis/: python fase37/37C_comparacion_seleccion/scripts/control_mutaciones_37c.py
"""
import sys

import nucleo_37c as N
import numpy as np
import pandas as pd
import pruebas_37c as P

Q = N.Q
ORIG = {k: getattr(P, k) for k in ('tabla', 'cadena', 'calibrada', 'coords_cadena', 'ari', 'pares', 'replica', 'manifiesto_filas', 'head', 'ramas_remotas', 'estado_git', 'tabla_etiquetas')}


def tabla_con(ruta, cambio):
    def f(r):
        t = ORIG['tabla'](r)
        return cambio(t) if r == ruta else t
    return f


def _sumar(t, col, v):
    t[col] = t[col] + v
    return t


def _con_fila(t, cambio):
    t = t.copy()
    cambio(t)
    return t


def _quitar_ultima(t):
    return t.iloc[:-1]


def _cambiar_b(t):
    t.loc[0, 'config'] = 'P1_c08_km_k3'
    return t


def _sin_rotulo(t):
    t['caracter'] = 'Confirmatoria'
    return t


def manifiesto_alterado(nombre, base, ruta):
    f = ORIG['manifiesto_filas'](nombre, base, ruta)
    if nombre == '37B':
        f[0] = (f[0][0], '0' * 64)
    return f


def etiquetas_desordenadas():
    return ORIG['tabla_etiquetas']().iloc[::-1]


def calibrada_con_todas(cad, e, t, idx, modo='consecutivo'):
    """Error: calibra con todas las filas, ignorando la submuestra."""
    return cad.calibrada(e, t, np.arange(Q.N), modo)


def reduccion_con_todas(Z, idx):
    """Error: ajusta la reducción con todas las filas."""
    return N.coordenadas_cadena(Z, np.arange(len(Z)))


def ari_coincidencia(a, b):
    """Error: porcentaje de coincidencia directa, sin corregir ni ignorar los nombres."""
    return float((np.asarray(a) == np.asarray(b)).mean())


def pares_todas(todas, usadas):
    """Error: compara también a quienes no fueron usadas."""
    from sklearn.metrics import adjusted_rand_score
    return [adjusted_rand_score(todas[i], todas[j]) for i in range(len(todas)) for j in range(i + 1, len(todas))]


def replica_sin_semilla(r):
    """Error: semilla no controlada."""
    return P.copula().muestrear(np.random.default_rng())


def replica_marginal_rota(r):
    """Error: altera una marginal."""
    t = ORIG['replica'](r).copy()
    t.iloc[0:40, t.columns.get_loc('edad')] = '40'
    return t


def replica_salto_roto(r):
    """Error: rompe la lógica madre-hija."""
    t = ORIG['replica'](r).copy()
    t['realiza_fuerza'] = 'SI'
    return t


class CadenaConMRS:
    def __init__(self, c):
        self.__dict__.update(c.__dict__)
        self.tabla = c.tabla.assign(mrs_total='10')
        self.celdas = c.celdas
        self.ids = c.ids

    def __getattr__(self, n):
        return getattr(ORIG['cadena'](), n)


MUTACIONES = [
    ('Manifiesto histórico alterado', 1, {'manifiesto_filas': manifiesto_alterado}),
    ('Etiquetas en otro orden', 2, {'tabla_etiquetas': etiquetas_desordenadas}),
    ('Lista A sin una configuración', 3, {'tabla': tabla_con('candidatos/lista_A_completa.csv', _quitar_ultima)}),
    ('Lista B con un identificador sustituido', 3, {'tabla': tabla_con('candidatos/lista_B_exploratoria.csv', _cambiar_b)}),
    ('Variable MRS en la tabla de entrada', 4, {'cadena': lambda: CadenaConMRS(ORIG['cadena']())}),
    ('Parámetros calibrados con todas las filas', 6, {'calibrada': calibrada_con_todas}),
    ('Reducción ajustada con todas las filas (contaminación)', 6, {'coords_cadena': reduccion_con_todas}),
    ('Reducción ajustada con todas las filas (reajuste)', 7, {'coords_cadena': reduccion_con_todas}),
    ('Recalibración con todas las filas', 8, {'calibrada': calibrada_con_todas}),
    ('ARI reemplazado por coincidencia directa', 10, {'ari': ari_coincidencia}),
    ('ARI de pares con filas no compartidas', 11, {'pares': pares_todas}),
    ('Réplica sin semilla', 12, {'replica': replica_sin_semilla}),
    ('Marginal alterada en la referencia', 13, {'replica': replica_marginal_rota}),
    ('Lógica de salto rota en la referencia', 13, {'replica': replica_salto_roto}),
    ('Lista B rotulada como confirmatoria', 14, {'tabla': tabla_con('candidatos/lista_B_exploratoria.csv', _sin_rotulo)}),
    ('Tamaños alterados en una repetición', 16, {'tabla': tabla_con('estabilidad/tamanos_por_repeticion.csv', lambda t: t.assign(tamanos_submuestra=t['tamanos_submuestra'].map(lambda s: '1 ' + s)))}),
    ('Valor de una figura distinto de la tabla', 20, {'tabla': tabla_con('estabilidad/comparacion_niveles.csv', lambda t: _sumar(t, 'E3_entre_media', 0.2))}),
    ('Cambio en la plataforma', 21, {'estado_git': lambda: ' M encuestas/models.py'}),
    ('Commit nuevo', 22, {'head': lambda: 'abc1234'}),
    ('Rama publicada', 22, {'ramas_remotas': lambda: '  origin/datos-simulados'}),
    ('Estado de un criterio distinto de la regla', 23, {'tabla': tabla_con('seleccion/evaluacion_por_etapa.csv', lambda t: t.assign(estado=np.where(t['criterio'] == 'E3 ari_entre media', 'OK', t['estado'])))}),
    ('Finalista con debilidad crítica', 23, {'tabla': tabla_con('seleccion/finalistas.csv', lambda t: pd.concat([t, t.iloc[:1].assign(config='F2_c03_km_k3')]) if len(t) else pd.DataFrame({'config': ['F2_c03_km_k3'], 'clase': ['x']}))}),
    ('Niveles E1 y E0 sin distinguir en las referencias', 25, {'tabla': tabla_con('estabilidad/comparacion_niveles.csv', lambda t: _sumar(t, 'E1_entre_media', -0.1))}),
]


def main():
    N.huella_sello()
    Q_ = {n: f for n, _, f in P.PRUEBAS}
    filas = []
    for nombre, n, cambios in MUTACIONES:
        for k, v in cambios.items():
            setattr(P, k, v)
        try:
            Q_[n]()
            detectada, detalle = False, 'La prueba no falló'
        except Exception as ex:  # noqa: BLE001
            detectada, detalle = True, f'{type(ex).__name__}: {str(ex)[:110]}'
        for k in cambios:
            setattr(P, k, ORIG[k])
        filas.append({'mutacion': nombre, 'prueba': n, 'detectada': detectada, 'detalle': detalle})
        print(('OK  ' if detectada else 'NO  '), nombre, '->', detalle[:90], flush=True)
    t = pd.DataFrame(filas)
    N.a_csv(t, N.BASE / 'pruebas' / 'control_mutaciones.csv')
    print(f'{int(t["detectada"].sum())} de {len(t)} errores detectados')
    return 0 if t['detectada'].all() else 1


if __name__ == '__main__':
    sys.exit(main())
