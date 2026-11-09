"""
Fase 38R, etapa A: matriz principal corregida, trazabilidad variable-ítem, participantes y consecuentes, y comparación celda a celda con la matriz histórica.

Uso, desde la carpeta scripts: python -B etapa_a_preparacion.py
"""
import sys

sys.dont_write_bytecode = True
import nucleo_38r as N  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

N.instalar_gancho()
sello = N.huella_sello()
P = N.BASE / 'preparacion'
pq = N.cargar()
d = pq.d
ids = d.ids
y = d.M['severo_mrs'].to_numpy()
if len(ids) != 529 or len(set(ids)) != 529 or int(y.sum()) != 281 or int((1 - y).sum()) != 248:
    raise N.B.Incumplimiento('Participantes o consecuentes distintos de 529 (281 y 248)')
if not (y == (d.M['mrs_total'].to_numpy() >= 16)).all() or d.M[[f'pregunta_{i}' for i in range(1, 12)]].isna().any().any():
    raise N.B.Incumplimiento('severo_mrs no reproduce MRS ≥ 16 o hay ítems del MRS incompletos')

c = N.construir(pq, 'principal')
if len(c.variables) != 29 or c.T.shape[1] != 90:
    raise N.B.Incumplimiento(f'Se esperaban 29 variables y 90 ítems: {len(c.variables)} y {c.T.shape[1]}')
resumen, poblaciones = [], []
for nombre in N.CONFIGS:
    x = N.construir(pq, nombre)
    if not nombre.startswith(('S3', 'S4')):
        M = x.T.astype(int)
        M.insert(0, 'participante_id', x.ids)
        M['severo_mrs=SI'] = x.y
        M['severo_mrs=NO'] = 1 - x.y
        N.a_csv(M, P / ('matriz_transaccional_principal.csv' if nombre == 'principal' else f'sensibilidades/matriz_{nombre}.csv'))
    por_var = pd.DataFrame({it: x.T[it] for it in x.T.columns}).T.groupby(lambda it: N.variable_de_item(it)).sum().T
    if (por_var.to_numpy() > 1).any():
        raise N.B.Incumplimiento(f'{nombre}: dos estados de una misma variable')
    resumen.append({'configuracion': nombre, 'descripcion': x.descripcion, 'participantes': x.n, 'severo_si': x.n_si, 'severo_no': x.n - x.n_si, 'frecuencia_basal_si': x.n_si / x.n, 'variables': len(x.variables),
                    'items': x.T.shape[1], 'items_constantes_quitados': '; '.join(x.constantes), 'umbral_antecedente': x.min_ant, 'umbral_conjunto': x.min_conj, 'largo_maximo': x.largo,
                    'items_por_transaccion_media': float(x.T.sum(axis=1).mean()), 'pares_determinados': len(N.H.pares_determinados(x.T)), 'historica_equivalente': N.HISTORICA[nombre] or 'sin equivalente (cambia la población)'})
    poblaciones.append({'configuracion': nombre, 'esperada': N.B.POBLACION[nombre], 'obtenida': x.n, 'coincide': x.n == N.B.POBLACION[nombre]})
N.a_csv(pd.DataFrame(resumen), P / 'resumen_transacciones.csv')
N.a_csv(pd.DataFrame(poblaciones), P / 'poblaciones_verificadas.csv')

# trazabilidad completa variable - ítem
filas = []
for v, grupos in c.esquema.items():
    for f in grupos:
        filas.append({'variable': v, 'etiqueta': N.H.ETIQUETA[v], 'bloque': N.H.BLOQUE[v], 'item': f['item'] or '(sin ítem)', 'codigos_originales': f['codigos'], 'regla': f['regla'], 'participantes': int(f['mascara'].sum())})
DI = pd.DataFrame(filas)
N.a_csv(DI, P / 'diccionario_items.csv')
N.a_csv(c.traza, P / 'trazabilidad_transformaciones.csv')
with open(P / 'transacciones_principal.txt', 'w', encoding='utf-8', newline='\n') as f:
    for pid, t in zip(c.ids, N.H.transacciones(c.T, c.y)):
        f.write(pid + '\t' + ' '.join(sorted(t)) + '\n')

# comparación con la matriz histórica
Hm = pd.read_csv(N.D38 / 'preparacion' / 'matriz_transaccional_principal.csv', dtype={'participante_id': str})
retirar = [i for i in Hm.columns if i.split('=')[0] in ('med_diabetes', 'prevision')]
Rm = pd.read_csv(P / 'matriz_transaccional_principal.csv', dtype={'participante_id': str})
if retirar != ['med_diabetes=NO', 'med_diabetes=SI', 'prevision=FONASA', 'prevision=ISAPRE'] and sorted(retirar) != sorted(['med_diabetes=NO', 'med_diabetes=SI', 'prevision=FONASA', 'prevision=ISAPRE']):
    raise N.B.Incumplimiento(f'Ítems históricos a retirar inesperados: {retirar}')
igual = Hm.drop(columns=retirar).equals(Rm)
if not igual:
    raise N.B.Incumplimiento('La matriz corregida no es la histórica menos los cuatro ítems')
ver = {'participantes': 529, 'identificadores_unicos': True, 'severo_si': 281, 'severo_no': 248, 'variables_principal': len(c.variables), 'items_principal': c.T.shape[1], 'items_historicos_retirados': retirar,
       'matriz_igual_a_historica_menos_4_items': bool(igual), 'filas_comparadas': len(Rm), 'columnas_comparadas': int(Rm.shape[1]), 'sello_protocolo': sello['sha256'], 'decisiones_contrastadas': pq.dec['huellas']}
N.a_json(ver, P / 'verificacion_preparacion.json')
N.registrar('etapa A preparacion')
print(pd.DataFrame(resumen)[['configuracion', 'participantes', 'severo_si', 'variables', 'items', 'umbral_antecedente', 'umbral_conjunto']].to_string(index=False))
print({k: v for k, v in ver.items() if k != 'decisiones_contrastadas'})
print('participantes por variable (ítems sin ítem):', int((DI['item'] == '(sin ítem)').sum()))
print(np.array(c.T.sum()).min())
