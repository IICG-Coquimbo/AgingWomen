"""
Fase 39R, etapa A: verifica fuentes y sellos, audita las dependencias históricas, construye las matrices corregidas de cada estrato y grupo, las compara con la 38R y con la Fase 39
menos las variables excluidas, y escribe tamaños, frecuencias basales y umbrales. No busca reglas.

Uso, desde la raíz: python -B analisis/fase39/39R_asociaciones_condicionadas_corregidas/scripts/etapa_a_preparacion.py
"""
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import nucleo_39r as N  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy.stats import fisher_exact  # noqa: E402

N.instalar_gancho()
sello = N.huella_sello()
N.R38.huella_sello()
P = N.BASE / 'preparacion'
pq = N.cargar()
d = pq.d
y = d.M['severo_mrs'].to_numpy().astype(int)

# 1. auditoría de dependencias: toda ruta del código histórico hacia la lista o las matrices de 31 variables debe tener un destino declarado
PATRONES = {
    r'N38\.PRINCIPAL': 'Sustituida: base_items usa la lista de 29 de la 38R (R38.PRINCIPAL), verificada contra las Fases 35 y 36.',
    r'N38\.construir\(': 'Sustituida: base_items llama a R38.construir, que construye desde las 29.',
    r'N38\.esquema\(': 'Se conserva la función, llamada con las 29 más el módulo (S7a y S7b).',
    r'N38\.matriz_items\(': 'Se conserva la función; recibe el esquema corregido.',
    r'N38\.cargar\(': 'Se conserva, vía R38.cargar: solo carga datos; no fija variables de modelado.',
    r'matriz_transaccional_principal': 'Sustituida: la verificación se hace contra la matriz de 90 ítems de la 38R. En integridad_39.py es solo una huella de archivo; ese control lo reemplaza integridad_39r.py.',
    r'base_items\(': 'Sustituida en todas las etapas por nucleo_39r.base_items.',
}
USO_EXPLICADO = {'preparacion_39.py', 'estratos_39.py', 'sensibilidades_39.py', 'ab1_39.py', 'pruebas_39.py', 'nucleo_39.py', 'integridad_39.py'}
aud = []
for s in sorted((N.D39 / 'scripts').glob('*.py')):
    for i, l in enumerate(s.read_text(encoding='utf-8').splitlines(), 1):
        for pat, destino in PATRONES.items():
            if re.search(pat, l):
                aud.append({'archivo': s.name, 'linea': i, 'patron': pat.replace('\\', ''), 'codigo': l.strip()[:140], 'destino_en_39R': destino})
A = pd.DataFrame(aud)
if set(A['archivo']) - USO_EXPLICADO:
    raise SystemExit(f'Dependencia sin revisar en: {set(A["archivo"]) - USO_EXPLICADO}')
N.a_csv(A, P / 'auditoria_dependencias.csv')

# 2. matriz principal idéntica a la 38R
T529, traza = N.base_items(pq)
n_items = N.BAR.verificar_matriz_38r(T529, None if N.HUMO else y, d.ids, N.MATRIZ_38R)
masc = N.mascaras(pq)

# 3. cada configuración es la histórica menos las variables retiradas, y nada más
ver = []
for sens in ('principal', 'S1', 'S2a', 'S5', 'S6', 'S7a', 'S7b'):
    Tc, _ = N.base_items(pq, sens)
    Th, _ = N.H39.base_items(d, sens)
    quitar = [c for c in Th.columns if N.variable_de_item(c) in N.RETIRADAS]
    resto = Th.drop(columns=quitar)
    igual = list(resto.columns) == list(Tc.columns) and bool((resto.to_numpy() == Tc.to_numpy()).all())
    if not igual:
        raise SystemExit(f'{sens}: la matriz corregida no es la histórica menos las variables retiradas')
    ver.append({'configuracion': sens, 'items_fase39': Th.shape[1], 'items_retirados': len(quitar), 'items_39R': Tc.shape[1], 'identica_a_historica_sin_retiradas': igual, 'retirados': ', '.join(quitar)})
N.a_csv(pd.DataFrame(ver), P / 'verificacion_configuraciones.csv')

# 4. pertenencia y estratos (criterios históricos)
pert = pd.DataFrame({'participante_id': d.ids, 'severo_mrs': y})
for dim in N.DIMENSIONES:
    lab = np.full(len(y), '', object)
    for e in N.dims_de(dim):
        lab[masc[(dim, e)]] = e
    if (lab == '').any():
        raise SystemExit(f'Participantes sin estrato en {dim}')
    pert[dim] = lab
pert['A'] = d.E['A'].to_numpy()
pert['B1'] = d.E['B1'].to_numpy()
N.a_csv(pert, P / 'pertenencia_estratos.csv')
hist = pd.read_csv(N.D39 / 'preparacion' / 'pertenencia_estratos.csv', dtype={'participante_id': str})
if not N.HUMO and not pert.astype(str).equals(hist.astype(str)):
    raise SystemExit('La pertenencia a estratos o a A/B1 difiere de la histórica')
defin = {('trabajo', 'trabaja'): 'trabaja_actualmente = 1', ('trabajo', 'no_trabaja'): 'trabaja_actualmente = 0', ('pareja', 'con_pareja'): 'tiene_pareja = 1',
         ('pareja', 'sin_pareja'): 'tiene_pareja = 0', ('ejercicio', '0_dias'): 'dias_ejercicio_semana = 1 (0 días)', ('ejercicio', '1-2_dias'): 'dias_ejercicio_semana = 2 (1-2 días)',
         ('ejercicio', '3_o_mas_dias'): 'dias_ejercicio_semana ≥ 3 (3-4, 5-6 o todos los días)', ('cuidado', 'cuida'): 'cantidad_personas_cuida ≥ 1',
         ('cuidado', 'no_cuida'): 'cantidad_personas_cuida = 0'}
filas, items_estr = [], []
for (g, e), m in masc.items():
    c = N.construir(pq, g, e, T529=T529, masc=masc)
    lo, hi = N.N38.wilson(c.n_si, c.n)
    filas.append({'grupo': g, 'estrato': e, 'nombre': N.NOMBRE.get(e, e), 'definicion': defin.get((g, e), f'etiqueta histórica {g} = {e.split("_")[-1]}'),
                  'participantes': c.n, 'severas': c.n_si, 'no_severas': c.n - c.n_si, 'frecuencia_basal_si': c.n_si / c.n, 'ic_basal_inf': float(lo), 'ic_basal_sup': float(hi),
                  'largo_maximo': c.largo, 'umbral_antecedente': c.min_ant, 'umbral_conjunto': c.min_conj, 'comparabilidad_minima': c.comp,
                  'variables_excluidas': ', '.join(c.excluidas), 'items': c.T.shape[1], 'items_constantes_quitados': len(c.constantes),
                  'busqueda': 'búsqueda de reglas' if c.largo > 0 else 'solo descripción', 'uso': 'principal' if g in N.DIMENSIONES else 'exploratorio secundario'})
    for it in T529.columns:
        if N.variable_de_item(it) in c.excluidas:
            continue
        items_estr.append({'grupo': g, 'estrato': e, 'item': it, 'participantes': int(T529.loc[m, it].sum()), 'prevalencia': float(T529.loc[m, it].mean()), 'en_estrato': it in c.T.columns})
    Mx = c.T.astype(int)
    Mx.insert(0, 'participante_id', c.ids)
    Mx['severo_mrs=SI'] = c.y
    Mx['severo_mrs=NO'] = 1 - c.y
    N.a_csv(Mx, P / 'matrices' / f'matriz_{g}_{e}.csv')
D = pd.DataFrame(filas)
N.a_csv(D, P / 'diccionario_estratos.csv')
N.a_csv(pd.DataFrame(items_estr), P / 'items_por_estrato.csv')
Dh = pd.read_csv(N.D39 / 'preparacion' / 'diccionario_estratos.csv')
cols = ['grupo', 'estrato', 'participantes', 'severas', 'largo_maximo', 'umbral_antecedente', 'umbral_conjunto', 'comparabilidad_minima']
if not N.HUMO and not D[cols].astype(str).reset_index(drop=True).equals(Dh[cols].astype(str).reset_index(drop=True)):
    raise SystemExit('Tamaños, severas o umbrales difieren de los históricos')

# 5. diferencias de frecuencia basal (descriptivo) y superposición entre dimensiones
dif = []
for g in list(N.DIMENSIONES) + ['A', 'B1']:
    t = D[D['grupo'] == g].reset_index(drop=True)
    for i in range(len(t)):
        for j in range(i + 1, len(t)):
            a, b = t.loc[i], t.loc[j]
            lo, hi = N.N38.newcombe(a['severas'], a['participantes'], b['severas'], b['participantes'])
            p = fisher_exact([[a['severas'], a['no_severas']], [b['severas'], b['no_severas']]])[1]
            dif.append({'grupo': g, 'estrato_1': a['estrato'], 'estrato_2': b['estrato'], 'basal_1': a['frecuencia_basal_si'], 'basal_2': b['frecuencia_basal_si'],
                        'diferencia': a['frecuencia_basal_si'] - b['frecuencia_basal_si'], 'ic_inf': float(lo), 'ic_sup': float(hi), 'p_fisher': p})
N.a_csv(pd.DataFrame(dif), P / 'diferencias_basales.csv')
cr = []
for a in N.DIMENSIONES:
    for b in N.DIMENSIONES:
        if a < b:
            t = pd.crosstab(pert[a], pert[b])
            for i in t.index:
                for j in t.columns:
                    cr.append({'dimension_1': a, 'estrato_1': i, 'dimension_2': b, 'estrato_2': j, 'participantes': int(t.loc[i, j])})
N.a_csv(pd.DataFrame(cr), P / 'superposicion_dimensiones.csv')
N.a_csv(traza, P / 'trazabilidad_items.csv')

# 6. barreras por configuración y estrato; módulos de S7a y S7b
reg, modulos = [], []
for sens in N.SENSIBILIDADES:
    T, _ = N.base_items(pq, sens)
    estratos = [N.BAR.ESTRATO_MODULO[sens]] if sens in N.BAR.ESTRATO_MODULO else [] if sens == 'S9' else N.ESTRATOS
    for dim, e in estratos:
        c = N.construir(pq, dim, e, sens, T529=T, masc=masc)
        reg.append({'configuracion': sens, 'dimension': dim, 'estrato': e, 'n': c.n, 'items': c.T.shape[1], 'umbral_antecedente': c.min_ant, 'umbral_conjunto': c.min_conj, 'largo_maximo': c.largo, 'barreras': 'superadas'})
        if sens in N.BAR.MODULOS:
            modulos.append(N.BAR.verificar_modulos(d, T, sens, masc[(dim, e)], N.variable_de_item))
N.a_csv(pd.DataFrame(reg), P / 'barreras_por_configuracion.csv')
N.a_csv(pd.DataFrame(modulos), P / 'modulos_S7a_S7b.csv')
verif = {'participantes': len(d.ids), 'ids_unicos': len(set(d.ids)), 'severos': int(y.sum()), 'no_severos': int(len(y) - y.sum()), 'variables': len(N.PRINCIPAL), 'items': n_items,
         'matriz_identica_38R': True, 'B1_igual_a_regla': bool((d.E['B1'] == d.E['B1_regla']).all()), 'sello_39R': sello['sha256'], 'modo_humo': N.HUMO}
if verif['participantes'] != 529 or verif['severos'] != 281 or verif['variables'] != 29 or verif['items'] != 90:
    raise SystemExit(f'Verificación fallida: {verif}')
N.a_json(verif, P / 'verificacion_preparacion.json')
N.registrar('etapa A preparacion')
print(verif)
print(pd.DataFrame(ver)[['configuracion', 'items_fase39', 'items_retirados', 'items_39R', 'identica_a_historica_sin_retiradas']].to_string(index=False))
print(pd.DataFrame(modulos).to_string(index=False))
print(D[['grupo', 'estrato', 'participantes', 'severas', 'frecuencia_basal_si', 'largo_maximo', 'umbral_antecedente', 'umbral_conjunto', 'items']].to_string(index=False))
print('Referencias históricas revisadas:', len(A), '; configuraciones por estrato con barreras superadas:', len(reg))
