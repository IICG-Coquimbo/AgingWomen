"""
Fase 39R: pruebas específicas de las barreras. Cada control introduce un error en memoria y exige que la barrera detenga el proceso; además, todas las configuraciones correctas y todas las tablas generadas deben pasar.

Uso, desde la raíz: python -B analisis/fase39/39R_asociaciones_condicionadas_corregidas/scripts/pruebas_barreras_39r.py
"""
import copy
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import nucleo_39r as N  # noqa: E402
import pandas as pd  # noqa: E402

N.instalar_gancho()
PQ = N.cargar()
BAR, B38, v = N.BAR, N.B38, N.variable_de_item
Inc = BAR.Incumplimiento
dec = PQ.dec
d = PQ.d
T, _ = N.base_items(PQ)
masc = N.mascaras(PQ)
y = d.M['severo_mrs'].to_numpy().astype(int)
filas = []


def debe_detener(nombre, f):
    try:
        f()
    except Inc as e:
        filas.append({'control': nombre, 'esperado': 'detiene', 'resultado': 'detuvo', 'correcto': True, 'detalle': str(e)[:200]})
    else:
        filas.append({'control': nombre, 'esperado': 'detiene', 'resultado': 'NO DETUVO', 'correcto': False, 'detalle': ''})


def debe_pasar(nombre, f):
    try:
        det = f()
    except Exception as e:  # noqa: BLE001
        filas.append({'control': nombre, 'esperado': 'pasa', 'resultado': 'FALLA', 'correcto': False, 'detalle': f'{type(e).__name__}: {e}'[:200]})
    else:
        filas.append({'control': nombre, 'esperado': 'pasa', 'resultado': 'pasó', 'correcto': True, 'detalle': det or ''})


def con_columna(nombre, valores=None):
    x = T.copy()
    x[nombre] = T.iloc[:, 0].to_numpy() if valores is None else valores
    return x


def base(x, sens='principal'):
    return BAR.verificar_base(x, sens, PQ, v)


# ---- listas y matrices de las 529
L = list(N.PRINCIPAL)
debe_pasar('Lista de 29 autorizada', lambda: B38.verificar_lista_principal(L, dec))
for var in ('prevision', 'usa_medicamentos_diabetes', 'doble_carga', 'imc'):
    debe_detener(f'Lista con {var}', lambda var=var: B38.verificar_lista_principal(L + [var], dec))
debe_detener('Lista con una variable menos', lambda: B38.verificar_lista_principal(L[:-1], dec))
debe_pasar('Matriz principal correcta', lambda: base(T))
for item in ('prevision=FONASA', 'prevision=ISAPRE', 'med_diabetes=SI', 'med_diabetes=NO', 'doble_carga=SI', 'tiene_prevision=1', 'mrs_total=alto', 'severo_mrs=SI', 'pregunta_3=2', 'severidad=alta', 'B1=2', 'A_complemento=1', 'cluster=3', 'etapa_menopausica=post'):
    debe_detener(f'Ítem {item}', lambda item=item: base(con_columna(item)))
ref = T.columns[10]
for var in ('prevision', 'usa_medicamentos_diabetes'):
    cat = d.X[var].dropna().unique()[0]
    m = (d.X[var] == cat).to_numpy()
    debe_detener(f'Ítem con otro nombre que copia {var}={cat}', lambda m=m: base(T.assign(**{ref: m})))
    debe_detener(f'Ítem con otro nombre que copia el complemento de {var}={cat}', lambda m=m: base(T.assign(**{ref: ~m})))
debe_detener('Ítem con otro nombre que copia la severidad', lambda: base(T.assign(**{ref: y == 1})))
debe_detener('Ítem con otro nombre que copia la etiqueta A = 1', lambda: base(T.assign(**{ref: (d.E['A'] == 1).to_numpy()})))
debe_detener('Matriz con filas de menos', lambda: base(T.iloc[:-1]))
debe_pasar('Matriz idéntica a la de la 38R', lambda: str(BAR.verificar_matriz_38r(T, y, d.ids, N.MATRIZ_38R)))
x = T.copy()
x.iloc[0, 0] = not x.iloc[0, 0]
debe_detener('Una celda distinta de la 38R', lambda: BAR.verificar_matriz_38r(x, y, d.ids, N.MATRIZ_38R))
debe_detener('Un ítem menos que la 38R', lambda: BAR.verificar_matriz_38r(T.iloc[:, 1:], y, d.ids, N.MATRIZ_38R))
debe_detener('Ítems en otro orden', lambda: BAR.verificar_matriz_38r(T[list(T.columns[::-1])], y, d.ids, N.MATRIZ_38R))
debe_detener('Consecuente distinto de la 38R', lambda: BAR.verificar_matriz_38r(T, 1 - y, d.ids, N.MATRIZ_38R))
debe_detener('Identificadores en otro orden', lambda: BAR.verificar_matriz_38r(T, y, list(d.ids)[::-1], N.MATRIZ_38R))

# ---- estratos
ve = lambda c, sens='principal': BAR.verificar_estrato(c, sens, dec, v, N.umbrales)  # noqa: E731


def clon(g='trabajo', e='trabaja', sens='principal'):
    c = N.construir(PQ, g, e, sens, masc=masc)
    c = copy.copy(c)
    c.T = c.T.copy()
    return c


def alterar(g='trabajo', e='trabaja', **k):
    c = clon(g, e)
    c.__dict__.update(k)
    return c


def con_item(g, e, item, valores=None):
    c = clon(g, e)
    c.T[item] = c.T.iloc[:, 0].to_numpy() if valores is None else valores
    return c


debe_detener('Estrato con otro tamaño', lambda: ve(alterar(n=300)))
debe_detener('Estrato con otras severas', lambda: ve(alterar(n_si=170)))
debe_detener('Estrato no autorizado', lambda: ve(alterar(estrato='otro')))
debe_detener('Grupo A con otro tamaño', lambda: ve(alterar('A', 'A_1', n=75)))
for g, e, item in (('trabajo', 'trabaja', 'trabaja=SI'), ('pareja', 'con_pareja', 'pareja=SI'), ('ejercicio', '0_dias', T.columns[T.columns.str.startswith('dias_ejercicio=')][0]), ('cuidado', 'cuida', T.columns[T.columns.str.startswith('cuida=')][0])):
    debe_detener(f'Estrato {e} conserva su variable', lambda g=g, e=e, item=item: ve(con_item(g, e, item)))
for g, e in (('A', 'A_0'), ('B1', 'B1_3')):
    for item in ('trabaja=SI', 'pareja=SI', T.columns[T.columns.str.startswith('dias_ejercicio=')][0]):
        debe_detener(f'{e} conserva {item}', lambda g=g, e=e, item=item: ve(con_item(g, e, item)))
debe_detener('Estrato con variables excluidas alteradas', lambda: ve(alterar(excluidas=[])))
debe_detener('Estrato con prevision', lambda: ve(con_item('trabajo', 'trabaja', 'prevision=FONASA')))
debe_detener('Estrato con med_diabetes', lambda: ve(con_item('pareja', 'con_pareja', 'med_diabetes=SI')))
c0 = clon()
debe_detener('Estrato con ítem constante', lambda: ve(con_item('trabajo', 'trabaja', c0.T.columns[0], [True] * c0.n)))
c1 = clon()
debe_detener('Estrato con ítem vacío', lambda: ve(con_item('trabajo', 'trabaja', c1.T.columns[0], [False] * c1.n)))
for k, val in (('min_ant', 10), ('min_conj', 5), ('largo', 1), ('comp', 10)):
    debe_detener(f'Umbral {k} alterado', lambda k=k, val=val: ve(alterar(**{k: val})))
debe_detener('Identificadores repetidos en el estrato', lambda: ve(alterar(ids=[c0.ids[0]] * c0.n)))

# ---- módulos
Ta, _ = N.base_items(PQ, 'S7a')
Tb, _ = N.base_items(PQ, 'S7b')
ca = N.construir(PQ, 'trabajo', 'trabaja', 'S7a', T529=Ta, masc=masc)
cb = N.construir(PQ, 'cuidado', 'cuida', 'S7b', T529=Tb, masc=masc)
debe_pasar('S7a en el estrato trabaja', lambda: str(BAR.verificar_modulos(d, Ta, 'S7a', masc[('trabajo', 'trabaja')], v)))
debe_pasar('S7b en el estrato cuida', lambda: str(BAR.verificar_modulos(d, Tb, 'S7b', masc[('cuidado', 'cuida')], v)))
debe_detener('S7a en otro estrato', lambda: ve(N.H39.construir(d, 'cuidado', 'cuida', 'S7a', T529=Ta, masc=masc), 'S7a'))
debe_detener('S7b en otro estrato', lambda: ve(N.H39.construir(d, 'trabajo', 'trabaja', 'S7b', T529=Tb, masc=masc), 'S7b'))
mt = masc[('trabajo', 'trabaja')]
mc = masc[('cuidado', 'cuida')]
item_a = [c for c in Ta.columns if c.startswith('lugar_comprensivo=')][0]
item_b = [c for c in Tb.columns if c.startswith('sobrecarga=')][0]
xa = Ta.copy()
xa.loc[(~mt).nonzero()[0][0], item_a] = True
debe_detener('S7a con ítem del módulo fuera del estrato', lambda: BAR.verificar_modulos(d, xa, 'S7a', mt, v))
xb = Tb.copy()
xb.loc[(~mc).nonzero()[0][0], item_b] = True
debe_detener('S7b con ítem del módulo fuera del estrato', lambda: BAR.verificar_modulos(d, xb, 'S7b', mc, v))
debe_detener('S7a con la población de 287', lambda: BAR.verificar_modulos(d, Ta, 'S7a', mt & Ta[[c for c in Ta.columns if v(c) in BAR.MODULOS['S7a']]].any(axis=1).to_numpy(), v))
debe_detener('S7b con la población de 239', lambda: BAR.verificar_modulos(d, Tb, 'S7b', mc & d.estado['sobrecarga_fisica_emocional'].eq('observada').to_numpy(), v))
sin = Ta.copy()
sin.loc[mt, [c for c in Ta.columns if v(c) in BAR.MODULOS['S7a']]] = False
debe_detener('S7a sin ítems del módulo', lambda: BAR.verificar_modulos(d, sin.drop(columns=[c for c in Ta.columns if v(c) in BAR.MODULOS['S7a']]), 'S7a', mt, v))
debe_pasar('Autorizadas en S7a incluyen el módulo', lambda: str(sorted(BAR.autorizadas('S7a', dec) - set(dec['principal']))))
debe_detener('Módulo laboral en la configuración principal', lambda: base(con_columna(item_a)))
debe_detener('Sobrecarga en S7a', lambda: BAR.verificar_base(Ta.assign(**{item_b: Tb[item_b].to_numpy()}), 'S7a', PQ, v))

# ---- tablas de resultados
tr = lambda a, vs, g='trabajo', cons=N.CONSECUENTES[0]: pd.DataFrame({'antecedente': [a], 'variables': [vs], 'consecuente': [cons]})  # noqa: E731
tc = lambda a, vs: pd.DataFrame({'antecedente': [a], 'variables': [vs]})  # noqa: E731
vr = lambda t, g='trabajo', sens='principal': BAR.verificar_tabla_reglas(t, sens, g, dec, v, N.CONSECUENTES)  # noqa: E731
vc = lambda t, g='trabajo', sens='principal': BAR.verificar_tabla_comparacion(t, sens, g, dec, v)  # noqa: E731
it = 'edad=45-54'
for a, vs in (('prevision=FONASA', 'prevision'), ('med_diabetes=SI', 'usa_medicamentos_diabetes'), ('doble_carga=SI', 'doble_carga'), ('trabaja=SI', 'trabaja_actualmente'), ('mrs_total=alto', 'mrs_total'), ('B1=1', 'B1')):
    debe_detener(f'Regla con {a}', lambda a=a, vs=vs: vr(tr(a, vs)))
    debe_detener(f'Comparación con {a}', lambda a=a, vs=vs: vc(tc(a, vs)))
debe_detener('Regla con un antecedente correcto pero variable no autorizada', lambda: vr(tr(it, 'prevision')))
debe_detener('Comparación con un antecedente correcto pero variable no autorizada', lambda: vc(tc(it, 'doble_carga')))
debe_detener('Regla con consecuente no autorizado', lambda: vr(tr(it, 'edad', cons='otro')))
debe_detener('Regla en A con pareja', lambda: vr(tr('pareja=SI', 'tiene_pareja'), g='A'))
debe_detener('Comparación en B1 con días de ejercicio', lambda: vc(tc(T.columns[T.columns.str.startswith('dias_ejercicio=')][0], 'dias_ejercicio_semana'), g='B1'))
debe_pasar('Regla correcta', lambda: vr(tr(it, 'edad')))
debe_pasar('Comparación correcta', lambda: vc(tc(it, 'edad')))

# ---- todas las configuraciones y tablas reales
n_cfg = 0
for sens in N.SENSIBILIDADES:
    Tx, _ = N.base_items(PQ, sens)
    for dim, e in ([BAR.ESTRATO_MODULO[sens]] if sens in BAR.ESTRATO_MODULO else [] if sens == 'S9' else N.ESTRATOS):
        N.construir(PQ, dim, e, sens, T529=Tx, masc=masc)
        n_cfg += 1
debe_pasar('Todas las configuraciones por estrato pasan', lambda: f'{n_cfg} configuraciones')
for g in ('A', 'B1'):
    for e in N.dims_de(g):
        debe_pasar(f'Grupo {e}', lambda g=g, e=e: str(N.construir(PQ, g, e, T529=T, masc=masc).n))
R = pd.read_csv(N.BASE / 'reglas' / 'reglas_todos_estratos.csv')
for dim in N.DIMENSIONES:
    debe_pasar(f'Reglas reales de {dim}', lambda dim=dim: vr(R[R['dimension'] == dim], g=dim))
    debe_pasar(f'Comparaciones reales de {dim}', lambda dim=dim: vc(pd.read_csv(N.BASE / 'comparacion' / f'comparacion_{dim}.csv'), g=dim))

D = pd.DataFrame(filas)
N.a_csv(D, N.BASE / 'pruebas' / 'resultados_barreras.csv')
N.registrar('pruebas de barreras')
print(f"{int(D['correcto'].sum())}/{len(D)} controles correctos; {int((D['esperado'] == 'detiene').sum())} negativos que deben detener")
if not D['correcto'].all():
    print(D[~D['correcto']].to_string())
    sys.exit(1)
