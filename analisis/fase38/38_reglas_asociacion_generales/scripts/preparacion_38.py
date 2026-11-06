"""
Fase 38: preparación. Diccionario de variables y categorías, justificación de agrupaciones, matrices transaccionales (principal y sensibilidades),
trazabilidad y verificaciones. No usa el MRS salvo para construir y verificar el consecuente.

Uso, desde la carpeta scripts: python preparacion_38.py
"""
import sys

import nucleo_38 as N
import numpy as np
import pandas as pd

sys.dont_write_bytecode = True
N.instalar_gancho()
N.huella_sello()
P = N.BASE / 'preparacion'
d = N.cargar()
X, est = d.X, d.estado
ids = d.ids
assert len(ids) == 529 and len(set(ids)) == 529
y = d.M['severo_mrs'].to_numpy()
assert int(y.sum()) == 281 and (d.M['severo_mrs'].to_numpy() == (d.M['mrs_total'].to_numpy() >= 16)).all()

JUSTIF = {
    'R1': 'Categoría con 27 participantes o más: se conserva.',
    'R2 unión de escasas': 'Incluye una categoría ordinal con menos de 27; se unió a su vecina adyacente de menor frecuencia (R2).',
    'R3 sin ítem (nominal escasa, sin vecina compatible)': 'Nominal con menos de 27 y sin categoría de significado compatible: no genera ítem (R3).',
    'R4 binaria': 'Binaria: «sí» y «no».',
    'R5 corte fijado': 'Numérica: corte fijado en el protocolo por su significado (R5).',
    'Grupo fijado en el protocolo (S7)': 'Escala de 5 puntos del módulo agrupada en tres niveles según el protocolo (solo S7).',
    'R1/R2': 'Categoría con 27 participantes o más: se conserva.',
}
POB = {'lugar_trabajo_comprensivo': 'Solo quienes trabajan (S7a)', 'estres_entorno_laboral': 'Solo quienes trabajan (S7a)',
       'sobrecarga_fisica_emocional': 'Solo quienes cuidan (S7b)', 'imc': 'Solo IMC observado (S8b)'}
PREGUNTA = {'lugar_trabajo_comprensivo': '¿Considera que su lugar de trabajo es comprensivo o flexible frente a estos síntomas?',
            'estres_entorno_laboral': '¿Su entorno laboral le genera niveles de estrés que intensifiquen sus síntomas?',
            'sobrecarga_fisica_emocional': '¿Siente que la combinación entre su trabajo y las tareas de cuidado le genera una sobrecarga física o emocional?'}


def estado_var(v):
    if v in N.SIN_MARCA:
        return {'observadas': np.nan, 'imputadas': np.nan, 'deducidas': np.nan, 'nota_imputacion': 'Sin marca por participante (Fase 34D: diabetes 23 imputadas; previsión 19 imputadas y 2 deducidas)'}
    if v not in est.columns:
        return {'observadas': np.nan, 'imputadas': np.nan, 'deducidas': np.nan, 'nota_imputacion': ''}
    s = est[v].value_counts()
    her = int((d.heredada[v].astype(str) == '1').sum()) if v in d.heredada.columns else 0
    return {'observadas': int(s.get('observada', 0)), 'imputadas': int(s.get('imputada', 0)), 'deducidas': int(s.get('deducida', 0)),
            'nota_imputacion': f'{her} con pregunta madre imputada' if her else ''}


todas = N.PRINCIPAL + ['imc', 'lugar_trabajo_comprensivo', 'estres_entorno_laboral', 'sobrecarga_fisica_emocional']
esq = N.esquema(X[todas], d.defs, 'principal')
filas, dic_items = [], []
for v in todas:
    s = X[v]
    if v in N.CORTES_NUM:
        orig = f'numérica: mín. {s.min():g}, mediana {s.median():g}, máx. {s.max():g} (n = {int(s.notna().sum())})'
    elif v in ('quien_prepara_comidas', 'prevision'):
        orig = '; '.join(f'{k} ({n})' for k, n in s.value_counts().items())
    elif v in N.ESCALAS_MODULOS:
        orig = '; '.join(f'{k} = {t} ({int((s == k).sum())})' for k, t in N.ESCALAS_MODULOS[v].items())
    else:
        orig = '; '.join(f'{c:g} = {t} ({int((s == c).sum())})' for c, t in N.niveles(v, d.defs))
    e = estado_var(v)
    uso = 'Principal' if v in N.PRINCIPAL else POB[v].split('(')[1].rstrip(')')
    marca = []
    if v in N.PROXIMAS:
        marca.append('Próxima a síntomas (excluida en S6)')
    if v in N.SIN_MARCA:
        marca.append('Sin marca de imputación (excluida en S1)')
    if v in N.FRECUENCIAS_EJERCICIO:
        marca.append('Redundante con días de ejercicio (excluida en S5)')
    if v in PREGUNTA:
        marca.append('La pregunta menciona los síntomas: riesgo de circularidad')
    for f in esq[v]:
        dic_items.append({'variable': v, 'etiqueta': N.ETIQUETA[v], 'bloque': N.BLOQUE[v], 'item': f['item'] or '(sin ítem)', 'codigos_originales': f['codigos'],
                          'regla': f['regla'], 'justificacion': JUSTIF.get(f['regla'], ''), 'participantes': int(f['mascara'].sum())})
    filas.append({'variable': v, 'etiqueta': N.ETIQUETA[v], 'bloque': N.BLOQUE[v], 'pregunta': PREGUNTA.get(v, ''), 'categorias_originales': orig,
                  'categorias_agrupadas': ' | '.join(f"{f['item'] or '(sin ítem)'} [{int(f['mascara'].sum())}]" for f in esq[v]),
                  'reglas_aplicadas': ', '.join(sorted({f['regla'] for f in esq[v]})), 'participantes_con_item': int(np.any([f['mascara'] for f in esq[v] if f['item']], axis=0).sum()),
                  'poblacion': POB.get(v, 'Las 529'), 'uso': uso, 'advertencias': '; '.join(marca), **e,
                  'no_aplica_estructural': {'frecuencia_aerobico': 'No realiza = respuesta sustantiva (R6)', 'frecuencia_bajo_impacto': 'No realiza = respuesta sustantiva (R6)',
                                            'frecuencia_fuerza': 'No realiza = respuesta sustantiva (R6)', 'cantidad_personas_cuida': 'No cuida = respuesta sustantiva (R6)'}.get(v, '')})
DV = pd.DataFrame(filas)
DI = pd.DataFrame(dic_items)
N.a_csv(DV, P / 'diccionario_variables_categorias.csv')
N.a_csv(DI, P / 'diccionario_items.csv')
excl = pd.DataFrame([
    {'variable': 'mrs_total, mrs_somatico, mrs_psicologico, mrs_urogenital, pregunta_1 a pregunta_11, mrs_severidad', 'motivo': 'Resultado: solo el consecuente severo_mrs'},
    {'variable': 'Segmentos A, B1 y demás etiquetas', 'motivo': 'Restricción de la fase; solo nota para la Fase 39'},
    {'variable': 'imc', 'motivo': 'Solo 267 observados; sensibilidad S8'},
    {'variable': 'lugar_trabajo_comprensivo, estres_entorno_laboral', 'motivo': 'Solo quienes trabajan y la pregunta menciona los síntomas; sensibilidad S7a'},
    {'variable': 'sobrecarga_fisica_emocional', 'motivo': 'Solo quienes cuidan; sensibilidad S7b'},
    {'variable': 'etapa_menopausica', 'motivo': 'Decisión del 01-11: solo descriptiva; depende de preguntas menstruales excluidas'},
])
N.a_csv(excl, P / 'variables_excluidas.csv')

# justificación de categorías poco frecuentes
esc = []
for v in todas:
    for f in esq[v]:
        if f['regla'].startswith(('R2', 'R3')):
            esc.append({'variable': v, 'etiqueta': N.ETIQUETA[v], 'resultado': f['item'] or '(sin ítem)', 'codigos_originales': f['codigos'],
                        'participantes_resultantes': int(f['mascara'].sum()), 'regla': f['regla'], 'justificacion': JUSTIF[f['regla']]})
ESC = pd.DataFrame(esc)
# detalle por código original de las categorías escasas
det = []
for v in todas:
    if v in N.CORTES_NUM or v in N.ESCALAS_MODULOS:
        continue
    if v in ('quien_prepara_comidas', 'prevision'):
        for k, n in X[v].value_counts().items():
            if n < N.MIN_CAT:
                det.append({'variable': v, 'categoria_original': k, 'participantes': int(n), 'pct': 100 * n / 529, 'destino': '(sin ítem, R3)'})
        continue
    for c_, t in N.niveles(v, d.defs):
        n = int((X[v] == c_).sum())
        if n < N.MIN_CAT:
            destino = next(f['item'] for f in esq[v] if c_ in [float(x) for x in f['codigos'].split(',')])
            det.append({'variable': v, 'categoria_original': t, 'participantes': n, 'pct': 100 * n / 529, 'destino': destino})
N.a_csv(ESC, P / 'agrupaciones_escasas.csv')
N.a_csv(pd.DataFrame(det), P / 'categorias_escasas_detalle.csv')

# transacciones
resumen = []
for nombre in N.CONFIGS:
    if nombre.startswith(('S3', 'S4')):
        continue
    c = N.construir(d, nombre)
    M = c.T.astype(int)
    M.insert(0, 'participante_id', c.ids)
    M['severo_mrs=SI'] = c.y
    M['severo_mrs=NO'] = 1 - c.y
    ruta = P / ('matriz_transaccional_principal.csv' if nombre == 'principal' else f'sensibilidades/matriz_{nombre}.csv')
    N.a_csv(M, ruta)
    # una participante, un estado por variable
    por_var = pd.DataFrame({it: c.T[it] for it in c.T.columns}).T.groupby(lambda it: N.variable_de_item(it)).sum().T
    assert (por_var.to_numpy() <= 1).all(), f'{nombre}: dos estados de una misma variable'
    assert not any(i.startswith(('mrs', 'pregunta', 'severo', 'severidad')) for i in c.T.columns)
    resumen.append({'configuracion': nombre, 'descripcion': c.descripcion, 'participantes': c.n, 'severo_si': c.n_si, 'frecuencia_basal_si': c.n_si / c.n,
                    'variables': len(c.variables), 'items': c.T.shape[1], 'items_constantes_quitados': '; '.join(c.constantes),
                    'items_por_transaccion_media': float(c.T.sum(axis=1).mean()), 'items_por_transaccion_min': int(c.T.sum(axis=1).min()),
                    'umbral_antecedente': c.min_ant, 'umbral_conjunto': c.min_conj, 'pares_determinados': len(N.pares_determinados(c.T))})
    if nombre == 'principal':
        tr = c.traza.copy()
        tr['participantes_sin_item_en_variable'] = [529 - int(np.any([f['mascara'] for f in esq[v] if f['item']], axis=0).sum()) if v in esq else np.nan for v in tr['variable']]
        N.a_csv(tr, P / 'trazabilidad_transformaciones.csv')
        with open(P / 'transacciones_principal.txt', 'w', encoding='utf-8', newline='\n') as f:
            for pid, t in zip(c.ids, N.transacciones(c.T, c.y)):
                f.write(pid + '\t' + ' '.join(sorted(t)) + '\n')
N.a_csv(pd.DataFrame(resumen), P / 'resumen_transacciones.csv')
ver = {'participantes': 529, 'identificadores_unicos': True, 'orden': 'fase36/matrices/identificadores.csv', 'severo_si': 281, 'severo_no': 248,
       'mrs_recalculado_coincide_con_limpieza_y_fase35': True, 'items_principal': int(resumen[0]['items']), 'variables_principal': len(N.PRINCIPAL),
       'categorias_escasas': len(det), 'sin_item_por_R3': int(sum(1 for f in esq['quien_prepara_comidas'] + esq['prevision'] if f['item'] is None))}
N.a_json(ver, P / 'verificacion_preparacion.json')
N.registrar('preparacion')
print(pd.DataFrame(resumen).drop(columns=['descripcion', 'items_constantes_quitados']).to_string(index=False))
print(ver)
