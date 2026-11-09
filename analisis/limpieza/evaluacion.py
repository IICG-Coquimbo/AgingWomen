"""
Evaluación de la limpieza contra el conjunto verdadero (Fase 34B).

Solo es posible con el conjunto sintético: generar_sintetico.py guarda las
encuestas sin errores (dataset_usuaria_verdad.csv) y la bitácora de cada error
agregado (bitacora_suciedad.csv). Se compara la salida de la limpieza celda a
celda con la verdad para responder tres preguntas:

1. ¿Se eliminaron las filas que había que eliminar (duplicados, versiones
   antiguas, edades fuera de criterio) y solo esas?
2. Por cada tipo de error: ¿la limpieza recuperó el valor verdadero, lo imputó
   (valor estimado) o lo dejó vacío?
3. ¿Cambió celdas que estaban bien?
"""
from collections import Counter, defaultdict

import pandas as pd

# Tipos de error de la bitácora que se refieren a la fila completa.
TIPOS_FILA = {'duplicado exacto', 'RUT repetido (versión anterior)'}
# Cambios a celdas correctas que son reglas del análisis, no errores de la limpieza.
REGLAS_ANALISIS = {
    'cambio_relacion_pareja_menopausia':
        'regla del análisis: "no aplica" sin pareja (la plataforma la muestra a todas)',
}


def _igual(a, b):
    if a == b:
        return True
    try:
        return abs(float(a) - float(b)) < 0.051           # 81 = 81.0
    except ValueError:
        return False


def _texto(df):
    return df.astype(object).where(df.notna(), '').astype(str)


def evaluar(limpio, excluidas, verdad, bitacora):
    """Devuelve un dict con las tablas de la evaluación (DataFrames) y totales."""
    limpio, verdad = _texto(limpio), _texto(verdad)
    L = limpio.set_index('uuid_local')
    V = verdad.set_index('uuid_local')
    celdas = bitacora[bitacora['columna'] != '*']

    # 1. Filas
    filas_sucias = set(bitacora.loc[bitacora['columna'] == '*', 'uuid_local'])
    excl = _texto(excluidas)
    motivos = Counter()
    for _, f in excl.iterrows():
        if f['uuid_local'] in filas_sucias:
            motivos[(f['motivo_exclusion'], 'fila sucia (correcto)')] += 1
        elif f['uuid_local'] in V.index and f['uuid_local'] not in L.index:
            edad_mala = ((celdas['uuid_local'] == f['uuid_local'])
                         & celdas['tipo'].str.contains('edad')).any()
            motivos[(f['motivo_exclusion'],
                     'edad alterada por el error (correcto)' if edad_mala else 'participante válida (error)')] += 1
        else:
            motivos[(f['motivo_exclusion'], 'copia de una fila conservada (correcto)')] += 1
    tabla_filas = pd.DataFrame([{'Motivo': m, 'Evaluación': e, 'Filas': n} for (m, e), n in motivos.items()])

    # 2. Celdas ensuciadas, por tipo de error
    resultado = defaultdict(Counter)
    for b in celdas.itertuples():
        if b.uuid_local not in L.index:
            resultado[b.tipo]['fila excluida'] += 1
            continue
        valor = L.at[b.uuid_local, b.columna]
        if _igual(valor, b.valor_verdadero):
            resultado[b.tipo]['recuperado'] += 1
        elif valor == '':
            resultado[b.tipo]['vacío'] += 1
        else:
            resultado[b.tipo]['imputado'] += 1
    columnas = ['recuperado', 'imputado', 'vacío', 'fila excluida']
    tabla_tipos = pd.DataFrame([{'Tipo de error': t, **{c: r.get(c, 0) for c in columnas},
                                 'Total': sum(r.values())} for t, r in resultado.items()])
    tabla_tipos = tabla_tipos.sort_values('Total', ascending=False)

    # 3. Celdas correctas que la limpieza cambió
    sucias = set(zip(celdas['uuid_local'], celdas['columna']))
    comunes = [c for c in V.columns if c in L.columns and c != 'participante_id']
    cambios, ejemplos = Counter(), {}
    revisadas = 0
    for u in V.index.intersection(L.index):
        for c in comunes:
            if (u, c) in sucias:
                continue
            revisadas += 1
            antes, despues = V.at[u, c], L.at[u, c]
            if not _igual(despues, antes):
                cambios[c] += 1
                ejemplos.setdefault(c, f'{antes or "(vacío)"} → {despues or "(vacío)"}')
    tabla_cambios = pd.DataFrame([{'Variable': c, 'Celdas': n, 'Ejemplo': ejemplos[c],
                                   'Motivo': REGLAS_ANALISIS.get(c, '')} for c, n in cambios.most_common()])
    return {'filas': tabla_filas, 'tipos': tabla_tipos, 'cambios': tabla_cambios,
            'celdas_sucias': len(celdas), 'celdas_revisadas': revisadas,
            'cambios_error': sum(n for c, n in cambios.items() if c not in REGLAS_ANALISIS)}
