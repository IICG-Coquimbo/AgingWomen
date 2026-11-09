"""
Fase 38: núcleo compartido. Auditoría de lecturas, carga verificada (a través de la Fase 37D, sin escribir en su carpeta), agrupaciones R1-R7 y transacciones.
Un hilo por biblioteca numérica.
"""
import os
import sys

sys.dont_write_bytecode = True
for _v in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_v] = '1'
import hashlib  # noqa: E402
import importlib.util  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
from datetime import datetime  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

AQUI = Path(__file__).resolve().parent
BASE = AQUI.parent
ANALISIS = BASE.parents[1]
RAIZ = ANALISIS.parent
D37 = ANALISIS / 'fase37' / '37D_caracterizacion'
PROHIBIDOS = ('verdad', 'bitacora', 'dataset_usuaria_sucio')
SEMILLA = 42
N_PERM = 1000
N_SUB = 200
FRAC_SUB = 0.8
MIN_CAT = 27          # 5 % de 529, redondeado hacia arriba
DIF_MARCADA = 0.10
MEJORA_MIN = 0.05
ESTABLE_REAP = 0.70
ESTABLE_DIR = 0.95
ALFA = 0.05
MAX_LARGO = 3
CONSECUENTES = ('severo_mrs=SI', 'severo_mrs=NO')


def _cargar_37d():
    spec = importlib.util.spec_from_file_location('nucleo_37d_lectura', D37 / 'scripts' / 'nucleo_37d.py')
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


N37 = _cargar_37d()

PRINCIPAL = ['trabaja_actualmente', 'tiene_pareja', 'cantidad_personas_cuida',
             'dias_ejercicio_semana', 'frecuencia_aerobico', 'frecuencia_bajo_impacto', 'frecuencia_fuerza', 'horas_sedentarismo',
             'quien_prepara_comidas', 'carnes_semana', 'falta_tiempo_influye', 'frecuencia_comida_fuera', 'frutas_dia', 'golosinas_semana', 'jugos_gaseosas_dia',
             'lacteos_dia', 'legumbres_semana', 'panes_dia', 'pescado_semana', 'platos_verduras_dia', 'vasos_agua_dia',
             'tabaco_frecuencia', 'alcohol_frecuencia',
             'edad', 'operada_no_mas_hijos', 'usa_medicamentos_presion', 'usa_medicamentos_diabetes', 'prevision',
             'tiene_actividad_sexual', 'distension_abdominal', 'evacuacion_intestinal']
BLOQUE = {**{v: 'Contexto' for v in PRINCIPAL[:3]}, **{v: 'Actividad física' for v in PRINCIPAL[3:8]}, **{v: 'Alimentación e hidratación' for v in PRINCIPAL[8:21]},
          **{v: 'Tabaco y alcohol' for v in PRINCIPAL[21:23]}, **{v: 'Generales y salud' for v in PRINCIPAL[23:28]}, **{v: 'Próximas a síntomas' for v in PRINCIPAL[28:31]},
          'imc': 'Salud (solo S8)', 'lugar_trabajo_comprensivo': 'Módulo laboral (solo S7a)', 'estres_entorno_laboral': 'Módulo laboral (solo S7a)',
          'sobrecarga_fisica_emocional': 'Módulo de cuidados (solo S7b)'}
PROXIMAS = ['tiene_actividad_sexual', 'distension_abdominal', 'evacuacion_intestinal']
SIN_MARCA = ['usa_medicamentos_diabetes', 'prevision']
FRECUENCIAS_EJERCICIO = ['frecuencia_aerobico', 'frecuencia_bajo_impacto', 'frecuencia_fuerza']
CORTOS = {'trabaja_actualmente': 'trabaja', 'tiene_pareja': 'pareja', 'cantidad_personas_cuida': 'cuida', 'dias_ejercicio_semana': 'dias_ejercicio',
          'frecuencia_aerobico': 'aerobico', 'frecuencia_bajo_impacto': 'bajo_impacto', 'frecuencia_fuerza': 'fuerza', 'horas_sedentarismo': 'horas_sentada',
          'quien_prepara_comidas': 'prepara', 'carnes_semana': 'carnes', 'falta_tiempo_influye': 'falta_tiempo', 'frecuencia_comida_fuera': 'comida_fuera',
          'frutas_dia': 'frutas', 'golosinas_semana': 'golosinas', 'jugos_gaseosas_dia': 'jugos', 'lacteos_dia': 'lacteos', 'legumbres_semana': 'legumbres',
          'panes_dia': 'panes', 'pescado_semana': 'pescado', 'platos_verduras_dia': 'verduras', 'vasos_agua_dia': 'agua', 'tabaco_frecuencia': 'tabaco',
          'alcohol_frecuencia': 'alcohol', 'edad': 'edad', 'operada_no_mas_hijos': 'operada', 'usa_medicamentos_presion': 'med_presion',
          'usa_medicamentos_diabetes': 'med_diabetes', 'prevision': 'prevision', 'tiene_actividad_sexual': 'actividad_sexual',
          'distension_abdominal': 'distension', 'evacuacion_intestinal': 'evacuacion', 'imc': 'imc', 'lugar_trabajo_comprensivo': 'lugar_comprensivo',
          'estres_entorno_laboral': 'estres_laboral', 'sobrecarga_fisica_emocional': 'sobrecarga'}
VAR_DE_CORTO = {c: v for v, c in CORTOS.items()}
ETIQUETA = {**N37.ETIQUETA, 'imc': 'IMC'}

ESCALAS_MODULOS = {
    'lugar_trabajo_comprensivo': {1: 'Muy en desacuerdo', 2: 'En desacuerdo', 3: 'Neutral', 4: 'De acuerdo', 5: 'Muy de acuerdo'},
    'estres_entorno_laboral': {1: 'Nada de estrés', 2: 'Estrés leve', 3: 'Estrés moderado', 4: 'Estrés alto', 5: 'Estrés extremo'},
    'sobrecarga_fisica_emocional': {1: 'Nunca o casi nunca', 2: 'Rara vez', 3: 'A veces', 4: 'Frecuentemente', 5: 'Siempre'},
}
GRUPOS_MODULOS = {
    'lugar_trabajo_comprensivo': [((1, 2), 'desacuerdo'), ((3,), 'neutral'), ((4, 5), 'acuerdo')],
    'estres_entorno_laboral': [((1, 2), 'nada_o_leve'), ((3,), 'moderado'), ((4, 5), 'alto_o_extremo')],
    'sobrecarga_fisica_emocional': [((1, 2), 'nunca_o_rara_vez'), ((3,), 'a_veces'), ((4, 5), 'frecuente_o_siempre')],
}
CORTES_NUM = {'edad': [(36, 44, '36-44'), (45, 54, '45-54'), (55, 65, '55-65')],
              'horas_sedentarismo': [(-np.inf, 5.999, 'menos_de_6'), (6, 7.999, '6-7'), (8, np.inf, '8_o_mas')],
              'imc': [(-np.inf, 24.999, 'menos_de_25'), (25, 29.999, '25-29.9'), (30, np.inf, '30_o_mas')]}
CORTES_GRUESA_NUM = {'edad': [(-np.inf, 49.999, 'menos_de_50'), (50, np.inf, '50_o_mas')],
                     'horas_sedentarismo': [(-np.inf, 7.999, 'menos_de_8'), (8, np.inf, '8_o_mas')]}

# ---- auditoría
_LEIDOS, _ESCRITOS = set(), set()


def _gancho(evento, args):
    if evento == 'open' and isinstance(args[0], (str, Path)):
        modo, banderas = args[1], args[2] if len(args) > 2 else 0
        escribe = (isinstance(modo, str) and any(x in modo for x in 'wax+')) or (not isinstance(modo, str) and isinstance(banderas, int) and bool(banderas & (os.O_WRONLY | os.O_RDWR)))
        nombre = Path(str(args[0])).name.lower()
        if not escribe and any(p in nombre for p in PROHIBIDOS):
            raise PermissionError(f'Lectura prohibida: {args[0]}')
        (_ESCRITOS if escribe else _LEIDOS).add(str(args[0]))


_INSTALADO = False


def instalar_gancho():
    global _INSTALADO
    if not _INSTALADO:
        sys.addaudithook(_gancho)
        _INSTALADO = True


def registrar(etapa):
    d = BASE / 'integridad'
    d.mkdir(parents=True, exist_ok=True)
    raiz, base = RAIZ.resolve(), BASE.resolve()
    leidos, fuera = set(), set()
    for x in list(_LEIDOS):
        a = Path(x).resolve()
        if a.is_relative_to(raiz) and a.is_file() and a.suffix not in ('.py', '.pyc') and '.git' not in a.parts and not a.is_relative_to(base):
            leidos.add(a.relative_to(raiz).as_posix())
    for x in list(_ESCRITOS):
        a = Path(x).resolve()
        if not a.is_relative_to(base) and a.suffix != '.pyc' and 'Temp' not in a.parts:
            fuera.add(str(a))
    for nombre, col, valores in (('archivos_leidos.csv', 'archivo_leido', leidos), ('escrituras_fuera.csv', 'escritura_fuera', fuera)):
        ruta = d / nombre
        previos = set(pd.read_csv(ruta)[col].astype(str)) if ruta.exists() and ruta.stat().st_size > 20 else set()
        pd.DataFrame({col: sorted(previos | valores)}, dtype=str).to_csv(ruta, index=False, encoding='utf-8', lineterminator='\n')
    ruta = d / 'registro_ejecucion.csv'
    pd.DataFrame([{'momento': datetime.now().isoformat(timespec='seconds'), 'etapa': etapa, 'archivos_leidos': len(leidos), 'escrituras_fuera': len(fuera)}]).to_csv(
        ruta, mode='a', header=not ruta.exists(), index=False, encoding='utf-8', lineterminator='\n')
    malos = [x for x in leidos if any(p in x.lower() for p in PROHIBIDOS)]
    if malos or fuera:
        raise SystemExit(f'Lectura prohibida o escritura fuera de la carpeta: {malos} {sorted(fuera)[:5]}')


# ---- utilidades
def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def huella_sello():
    s = json.loads((BASE / 'protocolo' / 'sello_protocolo.json').read_text(encoding='utf-8'))
    if sha(BASE / 'protocolo' / s['archivo']) != s['sha256']:
        raise SystemExit('El protocolo de la Fase 38 no coincide con su sello.')
    return s


def a_csv(t, ruta):
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    t.to_csv(ruta, index=False, encoding='utf-8', lineterminator='\n')


def a_json(o, ruta):
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(o, ensure_ascii=False, indent=1, default=lambda x: x.item() if hasattr(x, 'item') else str(x)) + '\n', encoding='utf-8', newline='\n')


def leer_json(ruta):
    return json.loads(Path(ruta).read_text(encoding='utf-8'))


# ---- carga
def cargar():
    """Carga verificada de la 37D (MRS recalculado y comparado con la limpieza y la Fase 35) más el IMC observado y los módulos."""
    d = N37.cargar()
    return d


def niveles(v, defs):
    """Lista ordenada (código, significado) de una variable ordinal o binaria, desde las definiciones de la Fase 36."""
    if v == 'usa_medicamentos_diabetes':
        return [(0.0, 'No'), (1.0, 'Sí')]
    nv = defs[v]['niveles']
    sig = {}
    for nombre, x in nv.items():
        sig.setdefault(float(x['codigo']), []).append(x.get('significado') or nombre)
    return [(c, ' o '.join(s)) for c, s in sorted(sig.items())]


def agrupar_ordinal(conteos, minimo=MIN_CAT):
    """R2: une la categoría con menos de `minimo` a su vecina adyacente de menor frecuencia (empate: hacia el centro); repite. Entrada y salida: listas de
    (lista de códigos, n)."""
    g = [([c], n) for c, n in conteos]
    while len(g) > 2:
        chicas = [i for i, (_, n) in enumerate(g) if n < minimo]
        if not chicas:
            break
        i = min(chicas, key=lambda j: (g[j][1], j))
        vec = [j for j in (i - 1, i + 1) if 0 <= j < len(g)]
        if len(vec) == 2 and g[vec[0]][1] == g[vec[1]][1]:
            centro = (len(g) - 1) / 2
            j = min(vec, key=lambda k: abs(k - centro))
        else:
            j = min(vec, key=lambda k: g[k][1])
        a, b = sorted((i, j))
        g[a:b + 1] = [(g[a][0] + g[b][0], g[a][1] + g[b][1])]
    return g


def _nombre_nivel(sig):
    import unicodedata
    s = unicodedata.normalize('NFKD', str(sig).lower()).encode('ascii', 'ignore').decode('ascii')
    s = s.replace(' ', '_').replace(',', '').replace('(', '').replace(')', '')
    return s.replace('incluye_0_estructural', '').strip('_')


def esquema_principal(X, defs, modo='principal'):
    """Diccionario de transformación: para cada variable, lista de (ítem, función que marca a las participantes). modo: principal | original | gruesa."""
    esq = {}
    for v in X.columns:
        s = X[v]
        filas = []
        if v in CORTES_NUM or v in CORTES_GRUESA_NUM:
            cortes = CORTES_GRUESA_NUM[v] if (modo == 'gruesa' and v in CORTES_GRUESA_NUM) else CORTES_NUM[v]
            for a, b, nombre in cortes:
                filas.append({'item': f'{CORTOS[v]}={nombre}', 'codigos': f'[{a}, {b}]', 'mascara': ((s >= a) & (s <= b)).to_numpy(), 'regla': 'R5 corte fijado'})
        elif v in ('quien_prepara_comidas', 'prevision'):
            cats = s.dropna().value_counts()
            for c, n in cats.items():
                nombre = {'COMPARTIDO': 'compartido', 'COMPRO': 'compra_preparada', 'OTRA_HOGAR': 'otra_persona_hogar', 'OTRO': 'otro', 'YO_MAYORIA': 'yo_la_mayoria'}.get(c, str(c))
                if n >= MIN_CAT or modo == 'original':
                    filas.append({'item': f'{CORTOS[v]}={nombre}', 'codigos': str(c), 'mascara': (s == c).to_numpy(), 'regla': 'R1' if n >= MIN_CAT else 'R1 (original, bajo umbral)'})
                else:
                    filas.append({'item': None, 'codigos': str(c), 'mascara': (s == c).to_numpy(), 'regla': 'R3 sin ítem (nominal escasa, sin vecina compatible)'})
        elif v in GRUPOS_MODULOS:
            for cods, nombre in GRUPOS_MODULOS[v]:
                filas.append({'item': f'{CORTOS[v]}={nombre}', 'codigos': ','.join(map(str, cods)), 'mascara': s.isin(cods).to_numpy(), 'regla': 'Grupo fijado en el protocolo (S7)'})
        else:
            nv = niveles(v, defs)
            conteos = [(c, int((s == c).sum())) for c, _ in nv]
            sig = dict(nv)
            if len(nv) == 2:
                grupos = [([c], n) for c, n in conteos]
                regla = 'R4 binaria'
            elif modo == 'original':
                grupos = [([c], n) for c, n in conteos]
                regla = 'S2a original'
            elif modo == 'gruesa' and v in GRUESA:
                grupos = [([c for c, _ in conteos if GRUESA[v](c)], 0), ([c for c, _ in conteos if not GRUESA[v](c)], 0)]
                regla = 'S2b gruesa'
            else:
                grupos = agrupar_ordinal(conteos)
                regla = 'R1/R2'
            n_de = dict(conteos)
            for cods, _ in grupos:
                con_casos = [c for c in cods if n_de.get(c, 0) > 0] or cods
                if len(con_casos) == 1:
                    nombre = _nombre_nivel(sig[con_casos[0]])
                else:
                    nombre = _nombre_nivel(sig[con_casos[0]]) + ('_o_' if len(con_casos) == 2 else '_a_') + _nombre_nivel(sig[con_casos[-1]])
                if regla == 'R4 binaria':
                    nombre = 'SI' if cods[0] == 1 else 'NO'
                filas.append({'item': f'{CORTOS[v]}={nombre}', 'codigos': ','.join(f'{c:g}' for c in cods), 'mascara': s.isin(cods).to_numpy(),
                              'regla': regla if len(cods) == 1 else ('R2 unión de escasas' if regla == 'R1/R2' else regla)})
        esq[v] = filas
    return esq


# Agrupación gruesa S2b: función que devuelve True para el primer grupo (por códigos del instrumento de la Fase 36).
GRUESA = {
    'dias_ejercicio_semana': None,  # se trata aparte: 0 / 1-2 / 3 o más
    'frecuencia_aerobico': lambda c: c == 0, 'frecuencia_bajo_impacto': lambda c: c == 0, 'frecuencia_fuerza': lambda c: c == 0,
    'cantidad_personas_cuida': lambda c: c == 0,
}


def completar_gruesa(defs):
    """Fija los cortes gruesos por significado (sección 10 del protocolo) usando los significados de los niveles."""
    for v in ('carnes_semana', 'golosinas_semana', 'legumbres_semana', 'pescado_semana', 'frecuencia_comida_fuera'):
        bajos = {c for c, s in niveles(v, defs) if s.lower().startswith(('nunca', '1-2'))}
        GRUESA[v] = (lambda b: (lambda c: c in b))(bajos)
    for v in ('frutas_dia', 'jugos_gaseosas_dia', 'lacteos_dia', 'panes_dia', 'platos_verduras_dia', 'vasos_agua_dia'):
        bajos = {c for c, s in niveles(v, defs) if s.lower().startswith(('no consumo', '1-2'))}
        GRUESA[v] = (lambda b: (lambda c: c in b))(bajos)
    for v in ('falta_tiempo_influye', 'distension_abdominal'):
        altos = {c for c, s in niveles(v, defs) if s.lower().startswith(('frecuentemente', 'siempre'))}
        GRUESA[v] = (lambda a: (lambda c: c not in a))(altos)
    for v in ('tabaco_frecuencia', 'alcohol_frecuencia'):
        nunca = {c for c, s in niveles(v, defs) if s.lower().startswith('nunca')}
        GRUESA[v] = (lambda b: (lambda c: c in b))(nunca)
    diaria = {c for c, s in niveles('evacuacion_intestinal', defs) if 'al día' in s.lower()}
    GRUESA['evacuacion_intestinal'] = lambda c: c in diaria
    GRUESA.pop('dias_ejercicio_semana', None)


def esquema(X, defs, modo='principal'):
    if modo == 'gruesa':
        completar_gruesa(defs)
    esq = esquema_principal(X, defs, modo)
    if modo == 'gruesa' and 'dias_ejercicio_semana' in X:
        s = X['dias_ejercicio_semana']
        sig = dict(niveles('dias_ejercicio_semana', defs))
        cero = [c for c, t in sig.items() if t.startswith('0')]
        uno = [c for c, t in sig.items() if t.startswith('1-2')]
        resto = [c for c in sig if c not in cero + uno]
        esq['dias_ejercicio_semana'] = [{'item': f'dias_ejercicio={n}', 'codigos': ','.join(f'{c:g}' for c in cods), 'mascara': s.isin(cods).to_numpy(), 'regla': 'S2b gruesa'}
                                        for cods, n in ((cero, '0_dias'), (uno, '1-2_dias'), (resto, '3_o_mas_dias'))]
    return esq


def matriz_items(esq, n):
    """Matriz booleana participante × ítem (solo ítems con nombre). Devuelve (DataFrame bool, tabla de trazabilidad)."""
    cols, traza = {}, []
    for v, filas in esq.items():
        for f in filas:
            traza.append({'variable': v, 'item': f['item'], 'codigos': f['codigos'], 'regla': f['regla'], 'n': int(f['mascara'].sum())})
            if f['item'] is not None:
                cols[f['item']] = f['mascara'].astype(bool)
    return pd.DataFrame(cols), pd.DataFrame(traza)


def transacciones(T, y):
    """Lista de conjuntos de ítems por participante, con el consecuente."""
    nombres = np.array(T.columns)
    V = T.to_numpy()
    return [frozenset(nombres[V[i]].tolist()) | {CONSECUENTES[0] if y[i] == 1 else CONSECUENTES[1]} for i in range(len(V))]


def variable_de_item(item):
    return VAR_DE_CORTO[item.split('=')[0]]


# ---- estadística de reglas
def wilson(k, n, z=1.959963984540054):
    k, n = np.asarray(k, float), np.asarray(n, float)
    p = np.where(n > 0, k / np.maximum(n, 1), np.nan)
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return c - h, c + h


def newcombe(k1, n1, k2, n2):
    """IC 95 % de la diferencia p1 − p2 (Newcombe, método 10, híbrido de Wilson)."""
    p1, p2 = np.asarray(k1, float) / n1, np.asarray(k2, float) / n2
    l1, u1 = wilson(k1, n1)
    l2, u2 = wilson(k2, n2)
    d = p1 - p2
    return d - np.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2), d + np.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2)


def katz(k1, n1, k2, n2, z=1.959963984540054):
    k1, n1, k2, n2 = (np.asarray(x, float) for x in (k1, n1, k2, n2))
    with np.errstate(divide='ignore', invalid='ignore'):
        rr = (k1 / n1) / (k2 / n2)
        se = np.sqrt(1 / k1 - 1 / n1 + 1 / k2 - 1 / n2)
        return rr, rr * np.exp(-z * se), rr * np.exp(z * se)


def bh(p):
    p = np.asarray(p, float)
    o = np.argsort(p)
    m = len(p)
    q = np.empty(m)
    q[o] = np.minimum.accumulate((p[o] * m / np.arange(1, m + 1))[::-1])[::-1]
    return np.minimum(q, 1)


def medidas(n_A, n_AC_si, n, n_si):
    """Medidas de la dirección con lift > 1 para cada antecedente. n_AC_si: participantes con el antecedente y severo = SI."""
    from scipy.stats import fisher_exact
    n_A = np.asarray(n_A, float)
    k = np.asarray(n_AC_si, float)
    p0 = n_si / n
    c_si = k / n_A
    si = c_si >= p0
    cons = np.where(si, CONSECUENTES[0], CONSECUENTES[1])
    base = np.where(si, p0, 1 - p0)
    kk = np.where(si, k, n_A - k)
    n_c = np.where(si, n_si, n - n_si)
    c = kk / n_A
    k_no, n_no = n_c - kk, n - n_A
    lo, hi = wilson(kk, n_A)
    with np.errstate(divide='ignore', invalid='ignore'):
        c_no = np.where(n_no > 0, k_no / np.maximum(n_no, 1), np.nan)
    dl, dh = newcombe(kk, n_A, k_no, n_no)
    rr, rl, rh = katz(kk, n_A, k_no, n_no)
    z = (c - base) / np.sqrt(base * (1 - base) / n_A)
    pf = np.array([fisher_exact([[int(a), int(b - a)], [int(cn), int(nn - cn)]])[1] if nn > 0 else np.nan for a, b, cn, nn in zip(kk, n_A, k_no, n_no)])
    return pd.DataFrame({'consecuente': cons, 'n_antecedente': n_A.astype(int), 'n_conjunto': kk.astype(int), 'n': n, 'frecuencia_basal': base,
                         'soporte_antecedente': n_A / n, 'soporte': kk / n, 'confianza': c, 'ic_confianza_inf': lo, 'ic_confianza_sup': hi, 'lift': c / base,
                         'diferencia_basal': c - base, 'leverage': kk / n - (n_A / n) * base, 'confianza_sin_antecedente': c_no,
                         'diferencia_riesgo': c - c_no, 'ic_dr_inf': dl, 'ic_dr_sup': dh, 'razon_riesgos': rr, 'ic_rr_inf': rl, 'ic_rr_sup': rh,
                         'z': z, 'p_fisher': pf})


# ---- configuraciones
CONFIGS = {
    'principal': {'descripcion': 'Análisis principal', 'min_ant': 0.10, 'min_conj': 0.05, 'largo': 3},
    'S1': {'descripcion': 'Sin valores imputados (sin diabetes ni previsión)', 'min_ant': 0.10, 'min_conj': 0.05, 'largo': 3},
    'S2a': {'descripcion': 'Categorías originales sin agrupar', 'min_ant': 0.10, 'min_conj': 0.05, 'largo': 3},
    'S2b': {'descripcion': 'Agrupación gruesa', 'min_ant': 0.10, 'min_conj': 0.05, 'largo': 3},
    'S3-bajo': {'descripcion': 'Umbral 5 % (antecedente ≥ 27, conjunto ≥ 14)', 'min_ant': 27, 'min_conj': 14, 'largo': 3},
    'S3-alto': {'descripcion': 'Umbral 15 % (antecedente ≥ 80, conjunto ≥ 40)', 'min_ant': 80, 'min_conj': 40, 'largo': 3},
    'S4-1': {'descripcion': 'Antecedentes de una condición', 'min_ant': 0.10, 'min_conj': 0.05, 'largo': 1},
    'S4-2': {'descripcion': 'Antecedentes de hasta dos condiciones', 'min_ant': 0.10, 'min_conj': 0.05, 'largo': 2},
    'S5': {'descripcion': 'Sin frecuencias de ejercicio aeróbico, bajo impacto y fuerza', 'min_ant': 0.10, 'min_conj': 0.05, 'largo': 3},
    'S6': {'descripcion': 'Sin variables próximas a síntomas', 'min_ant': 0.10, 'min_conj': 0.05, 'largo': 3},
    'S7a': {'descripcion': 'Quienes trabajan, con módulo laboral', 'min_ant': 0.10, 'min_conj': 0.05, 'largo': 3},
    'S7b': {'descripcion': 'Quienes cuidan, con sobrecarga', 'min_ant': 0.10, 'min_conj': 0.05, 'largo': 3},
    'S8a': {'descripcion': 'Con IMC observado, sin IMC', 'min_ant': 0.10, 'min_conj': 0.05, 'largo': 3},
    'S8b': {'descripcion': 'Con IMC observado, con IMC', 'min_ant': 0.10, 'min_conj': 0.05, 'largo': 3},
}


def umbrales(nombre, n):
    c = CONFIGS[nombre]
    a = c['min_ant'] if isinstance(c['min_ant'], int) else math.ceil(round(c['min_ant'] * n, 9))
    b = c['min_conj'] if isinstance(c['min_conj'], int) else math.ceil(round(c['min_conj'] * n, 9))
    return a, b, c['largo']


class Config:
    def __init__(self, **k):
        self.__dict__.update(k)


def construir(d, nombre):
    """Transacciones de una configuración. Las agrupaciones se fijan con las 529 (sin el MRS) y luego se restringe la población."""
    X = d.X.copy()
    ids = np.array(d.ids)
    y = d.M['severo_mrs'].to_numpy().astype(int)
    pob = np.ones(len(X), bool)
    variables = list(PRINCIPAL)
    modo = {'S2a': 'original', 'S2b': 'gruesa'}.get(nombre, 'principal')
    if nombre == 'S1':
        X = N37.solo_observado(X, d.estado, d.heredada)
        variables = [v for v in variables if v not in SIN_MARCA]
    if nombre == 'S5':
        variables = [v for v in variables if v not in FRECUENCIAS_EJERCICIO]
    if nombre == 'S6':
        variables = [v for v in variables if v not in PROXIMAS]
    if nombre == 'S7a':
        pob = (X['trabaja_actualmente'] == 1).to_numpy()
        variables = [v for v in variables if v != 'trabaja_actualmente'] + ['lugar_trabajo_comprensivo', 'estres_entorno_laboral']
    if nombre == 'S7b':
        pob = (X['cantidad_personas_cuida'] > 0).to_numpy()
        variables = variables + ['sobrecarga_fisica_emocional']
    if nombre in ('S8a', 'S8b'):
        pob = X['imc'].notna().to_numpy()
        if nombre == 'S8b':
            variables = variables + ['imc']
    esq = esquema(X[variables], d.defs, modo)
    T, traza = matriz_items(esq, len(X))
    T.index = ids
    T, ids_p, y_p = T[pob], ids[pob], y[pob]
    n = int(pob.sum())
    tam = T.sum(axis=0)
    constantes = tam.index[(tam == 0) | (tam == n)].tolist()
    T = T.drop(columns=constantes)
    a, b, largo = umbrales(nombre, n)
    return Config(nombre=nombre, T=T.reset_index(drop=True), ids=ids_p, y=y_p, n=n, n_si=int(y_p.sum()), min_ant=a, min_conj=b, largo=largo, traza=traza,
                  constantes=constantes, variables=variables, modo=modo, descripcion=CONFIGS[nombre]['descripcion'])


def pares_determinados(T):
    """Pares (a, b) de ítems de variables distintas en que toda participante con a tiene b. Calculado solo con los antecedentes."""
    V = T.to_numpy().astype(np.int32)
    co = V.T @ V
    sup = np.diag(co)
    cols = list(T.columns)
    out = set()
    for i in range(len(cols)):
        for j in range(len(cols)):
            if i != j and sup[i] > 0 and co[i, j] == sup[i] and variable_de_item(cols[i]) != variable_de_item(cols[j]):
                out.add((cols[i], cols[j]))
    return out


# ---- textos legibles
_ACENTOS = {'dias': 'días', 'mas': 'más', 'dia': 'día', 'vez al dia': 'vez al día', 'si': 'sí', 'estres': 'estrés', 'otra persona hogar': 'otra persona del hogar',
            'yo la mayoria': 'ella prepara la mayoría', 'compartido': 'ella y otras personas', 'no lo realiza o nunca': 'no realiza o nunca'}


def legible(item):
    """«trabaja=SI» → «Trabaja actualmente: sí». Solo para mostrar; los nombres de ítem siguen siendo la clave."""
    if item in CONSECUENTES:
        return 'Síntomas severos (MRS ≥ 16)' if item.endswith('SI') else 'Síntomas no severos (MRS < 16)'
    v = variable_de_item(item)
    nivel = item.split('=', 1)[1].replace('_', ' ')
    nivel = {'SI': 'sí', 'NO': 'no'}.get(nivel, nivel)
    palabras = ' '.join(_ACENTOS.get(w, w) for w in nivel.split(' '))
    for a, b in _ACENTOS.items():
        if ' ' in a:
            palabras = palabras.replace(a, b)
    return f'{ETIQUETA[v]}: {palabras}'


def legible_regla(antecedente):
    return ' y '.join(legible(i) for i in antecedente.split(' & '))
