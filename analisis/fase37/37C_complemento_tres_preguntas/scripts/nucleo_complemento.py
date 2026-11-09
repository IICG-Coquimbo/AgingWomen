"""
Complemento de la Fase 37C: definiciones de B1, B2 y B2-C, bloques temáticos y medidas. Importa de las Fases 36 a 37C sin modificarlas y escribe solo en su propia carpeta.
"""
import sys

sys.dont_write_bytecode = True
from pathlib import Path  # noqa: E402

AQUI = Path(__file__).resolve().parent
BASE = AQUI.parent
sys.path[:0] = [str(BASE.parent / '37C_comparacion_seleccion' / 'scripts')]

import interpretabilidad_37c as IN  # noqa: E402
import nucleo_37c as N  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

Q = N.Q
C37 = N.BASE
CONFIG = 'P2_c12_km_k4'
ESPACIO = 'P2'
K = 4
TRIO = ('trabaja_actualmente', 'tiene_pareja', 'dias_ejercicio_semana')
CODIGOS_DIAS = {'1': '0 días', '2': '1-2 días', '3': '3-4 días', '4': '5-6 días', '5': 'Todos los días'}
M_CELDAS = 20
BLOQUES = {
    'Las tres preguntas': list(TRIO),
    'Alimentación': ['quien_prepara_comidas', 'carnes_semana', 'falta_tiempo_influye', 'frecuencia_comida_fuera', 'frutas_dia', 'golosinas_semana', 'jugos_gaseosas_dia', 'lacteos_dia', 'legumbres_semana', 'panes_dia', 'pescado_semana', 'platos_verduras_dia', 'vasos_agua_dia'],
    'Actividad física adicional': ['frecuencia_aerobico', 'frecuencia_bajo_impacto', 'frecuencia_fuerza'],
    'Sedentarismo': ['horas_sedentarismo'],
    'Cuidados': ['cantidad_personas_cuida'],
    'Tabaco y alcohol': ['tabaco_frecuencia', 'alcohol_frecuencia'],
    'Otras generales': ['edad', 'operada_no_mas_hijos', 'usa_medicamentos_presion'],
    'Actividad sexual (descriptiva)': ['tiene_actividad_sexual'],
    'Digestión (descriptiva)': ['distension_abdominal', 'evacuacion_intestinal'],
}
LECTURA_PRINCIPAL = ['Alimentación', 'Actividad física adicional', 'Sedentarismo', 'Cuidados', 'Tabaco y alcohol', 'Otras generales']
BLOQUE_DE = {v: b for b, vs in BLOQUES.items() for v in vs}
VARIANTES_A = {'A': 12, 'A8': 8, 'A16': 16}
N_TRIOS_AZAR = 30


def huella():
    s = N.leer_json(BASE / 'protocolo' / 'sello_protocolo.json')
    if N.sha(BASE / 'protocolo' / s['archivo']) != s['sha256']:
        raise SystemExit('El protocolo del complemento no coincide con su sello.')
    N.huella_sello()
    return s['sha256']


def registrar(etapa, resultados):
    Q.registrar(BASE, etapa, resultados)


# ---- las tres preguntas
def celdas(tabla):
    """Código de celda (0 a 19) con las respuestas de las tres preguntas, sin puntos de corte. Solo lee esas tres columnas."""
    t = tabla['trabaja_actualmente'].map({'False': 0, 'True': 1})
    p = tabla['tiene_pareja'].map({'NO': 0, 'SI': 1})
    d = tabla['dias_ejercicio_semana'].map({str(i): i - 1 for i in range(1, 6)})
    if t.isna().any() or p.isna().any() or d.isna().any():
        raise ValueError('Respuesta fuera del instrumento en las tres preguntas')
    return (t.to_numpy() * 10 + p.to_numpy() * 5 + d.to_numpy()).astype(int)


def nombre_celda(c):
    return f"{'Trabaja' if c // 10 else 'No trabaja'} · {'Con pareja' if (c % 10) // 5 else 'Sin pareja'} · {CODIGOS_DIAS[str(c % 5 + 1)]}"


def tabla_celdas(cod, l, k=K, m=M_CELDAS):
    """B1: segmento más frecuente por celda. Empate: el segmento más grande en el entrenamiento y luego el de menor número. Celda vacía: el más grande."""
    cod, l = np.asarray(cod), np.asarray(l)
    cuenta = np.zeros((m, k), dtype=int)
    np.add.at(cuenta, (cod, l), 1)
    global_ = np.bincount(l, minlength=k)
    orden = sorted(range(k), key=lambda g: (-global_[g], g))
    mapa = np.array([orden[int(np.argmax([cuenta[c, g] for g in orden]))] for c in range(m)])
    n = cuenta.sum(axis=1)
    pureza = np.where(n > 0, cuenta.max(axis=1) / np.where(n > 0, n, 1), np.nan)
    return mapa, pureza, cuenta


def ajustar_b2(Z3, idx, semilla, k=K):
    """B2: K-means sobre las tres columnas. Las filas de `idx` conservan la etiqueta del algoritmo y las demás van al centroide más cercano, como la Fase 37C."""
    l, ajuste, centros = Q.ajustar_km(Z3[idx], k, semilla)
    et, d1, d2, margen = Q.asignar(centros, Z3)
    et[idx] = l
    return et.astype(int), margen, centros, ajuste


def ajustar_cruce(tabla, idx, semilla):
    """B2-C: pareja × trabajo × ejercicio bajo o alto. El corte de ejercicio sale de K-means con k = 2 sobre los códigos, solo con el entrenamiento."""
    cod = celdas(tabla)
    dias = (cod % 5 + 1).astype(float)
    _, _, centros = Q.ajustar_km(dias[idx].reshape(-1, 1), 2, semilla)
    corte = float(centros.mean())
    alto = (dias > corte).astype(int)
    return (cod // 10) * 4 + ((cod % 10) // 5) * 2 + alto, corte


def columnas_de(variables, columnas):
    esc = N.leer_json(N.F36 / 'artefactos' / ESPACIO / 'escaladores.json')
    return [i for i, c in enumerate(columnas) if esc[c]['variable'] in set(variables)]


def a_sin_bloque(Z, columnas, bloque, idx, semilla, comps=12):
    """Rehace la reducción y K-means sin las columnas del bloque, solo con `idx`. Devuelve la etiqueta de cada variante de componentes."""
    quitar = set(columnas_de(BLOQUES[bloque], columnas))
    usar = [i for i in range(Z.shape[1]) if i not in quitar]
    F, _ = N.coordenadas_cadena(Z[:, usar], idx)
    salida = {}
    for nombre, c in VARIANTES_A.items():
        X = F[:, :c]
        l, _, centros = Q.ajustar_km(X[idx], K, semilla)
        et = Q.asignar(centros, X)[0]
        et[idx] = l
        salida[nombre] = et.astype(int)
    return salida


# ---- variables por describir
def objetivos(cad):
    """Por variable: matriz numérica (indicadores si es nominal) y máscara de celdas observadas. Nunca usa celdas imputadas ni heredadas de una pregunta previa imputada."""
    defs, vals = IN.numericos(cad)
    salida = {}
    for v, d in defs.items():
        marca = (cad.estado[v].to_numpy() != 'imputada') & (cad.previa[v].to_numpy() != '1')
        if d['tipo'] == 'nominal':
            niveles = sorted(set(vals[v]))
            Y = np.column_stack([(vals[v] == n).astype(float) for n in niveles])
        else:
            Y = np.asarray(vals[v], dtype=float).reshape(-1, 1)
        marca &= ~np.isnan(Y).any(axis=1)
        salida[v] = {'Y': Y, 'marca': marca, 'tipo': d['tipo'], 'seccion': d['seccion']}
    return salida


def indicadores(l):
    u = np.unique(l)
    return (np.asarray(l)[:, None] == u[None, :]).astype(float)


def r2_fuera(D, Y, marca, idx, resto):
    """R² en las no usadas: coeficientes y media de referencia solo del entrenamiento. Con una sola partición equivale a las medias por segmento."""
    tr, te = idx[marca[idx]], resto[marca[resto]]
    if len(te) < 2:
        return float('nan')
    ybar, xbar = Y[tr].mean(axis=0), D[tr].mean(axis=0)
    beta = np.linalg.lstsq(D[tr] - xbar, Y[tr] - ybar, rcond=None)[0]
    pred = (D[te] - xbar) @ beta + ybar
    sst = ((Y[te] - ybar) ** 2).sum()
    return float(1 - ((Y[te] - pred) ** 2).sum() / sst) if sst > 0 else float('nan')


def r2_interno(l, Y, marca):
    """Parte de la varianza entre segmentos en las 529: η² en numéricas y su versión multivariada en indicadores."""
    Y, l = Y[marca], np.asarray(l)[marca]
    total = ((Y - Y.mean(axis=0)) ** 2).sum()
    if total == 0:
        return 0.0
    return float(sum((l == g).sum() * ((Y[l == g].mean(axis=0) - Y.mean(axis=0)) ** 2).sum() for g in np.unique(l)) / total)


def diferencia_maxima(l, Y, marca):
    """Numéricas: mayor distancia entre medias de segmentos, en desviaciones estándar. Nominales: mayor diferencia de proporción en un nivel."""
    Y, l = Y[marca], np.asarray(l)[marca]
    medias = np.vstack([Y[l == g].mean(axis=0) for g in np.unique(l)])
    rango = medias.max(axis=0) - medias.min(axis=0)
    if Y.shape[1] > 1:
        return float(rango.max())
    de = Y.std()
    return float(rango[0] / de) if de > 0 else 0.0


def varianza_retenida(X, l):
    media = X.mean(axis=0)
    tot = ((X - media) ** 2).sum()
    return float(sum((l == g).sum() * ((X[l == g].mean(axis=0) - media) ** 2).sum() for g in np.unique(l)) / tot)


def alineados(base_tr, otra_tr, otra):
    """Traduce los nombres de `otra` con la alineación calculada solo en el entrenamiento."""
    trad = dict(zip(otra_tr, N.alinear(base_tr, otra_tr)))
    return np.array([trad.get(x, -1) for x in otra])


def trios_azar():
    """Tríos de variables de una sola columna en P2, fijos para todas las repeticiones. No incluyen el trío evaluado."""
    defs = N.leer_json(N.F36 / 'artefactos' / ESPACIO / 'esquema_variables.json')['variables']
    v = sorted(d['variable'] for d in defs if d['tipo'] != 'nominal')
    rng = np.random.default_rng([Q.SEMILLA, 7300])
    salida = []
    while len(salida) < N_TRIOS_AZAR:
        t = tuple(sorted(rng.choice(v, 3, replace=False).tolist()))
        if set(t) != set(TRIO) and t not in salida:
            salida.append(t)
    return salida
