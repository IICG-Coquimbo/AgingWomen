"""
Fase 36B: procedencia por celda de las 33 variables, reconstruida en memoria.

Repite la limpieza 34B sobre el conjunto sucio, solo para saber qué celdas estaban vacías antes de los pasos 8 y 9. No abre la
verdad del simulador ni la bitácora, no importa `auditoria_fase34` (que sí las carga) y no escribe nada de la limpieza.
Exige que la limpieza en memoria sea idéntica al archivo: si no lo es, las máscaras no valdrían y se detiene.
"""
import numpy as np
import pandas as pd

import configuracion_fase36 as C
from limpieza import reglas

ESTADOS = ['observada', 'deducida', 'imputada', 'no_aplicable', 'faltante']


def _leer(ruta):
    return pd.read_csv(ruta, dtype=str, keep_default_na=False, encoding='utf-8-sig')


def reconstruir():
    """Devuelve (L, P8, P9): conjunto limpio y su estado justo antes de los pasos 8 y 9, indexados por participante."""
    crudo = _leer(C.SUCIO)
    captura = {}
    o8, o9 = reglas.p8_condicionales, reglas.p9_imputacion

    def c8(df, *a, **k):
        captura['pre8'] = df.copy()
        return o8(df, *a, **k)

    def c9(df, *a, **k):
        captura['pre9'] = df.copy()
        return o9(df, *a, **k)

    reglas.p8_condicionales, reglas.p9_imputacion = c8, c9
    try:
        limpio = reglas.limpiar(crudo)[0]
    finally:
        reglas.p8_condicionales, reglas.p9_imputacion = o8, o9
    disco = _leer(C.LIMPIO)
    memoria = limpio.astype(object).where(limpio.notna(), '').astype(str)
    distintas = int((memoria[disco.columns].to_numpy() != disco.to_numpy()).sum())
    if distintas:
        raise SystemExit(f'La limpieza en memoria difiere del archivo en {distintas} celdas: se detiene la procedencia.')
    L = disco.where(disco != '', np.nan).set_index('participante_id')
    return L, captura['pre8'].set_index('participante_id').reindex(L.index), captura['pre9'].set_index('participante_id').reindex(L.index)


def tabla_celdas(ids):
    """Una fila por participante y variable. `valor_original` es el valor del conjunto limpio, nunca el código transformado."""
    L, P8, P9 = reconstruir()
    filas = []
    previa_imputada = {}
    for c in sorted(set(C.PREGUNTA_PREVIA.values())):
        previa_imputada[c] = (P9[c].isna() & L[c].notna()).reindex(ids)
    for v in C.GENERALES + C.MODULOS:
        valor = L[v].reindex(ids)
        if v in P9.columns:
            imputada = (P9[v].isna() & L[v].notna()).reindex(ids)
            deducida = (P8[v].isna() & P9[v].notna()).reindex(ids)
        else:
            # Derivada en el paso 10 (IMC): aún no existe en los pasos 8 y 9; su vacío se trata abajo.
            imputada = deducida = pd.Series(False, index=ids)
        previa = previa_imputada[C.PREGUNTA_PREVIA[v]] if v in C.PREGUNTA_PREVIA else pd.Series(False, index=ids)
        if v == 'imc':
            vacio_estado = 'imputada'  # IMC: faltaba en el limpio y la Fase 35A le asignó la media.
        elif v in C.LABORALES:
            trabaja = L['trabaja_actualmente'].reindex(ids)
            vacio_estado = trabaja.map(lambda t: 'faltante' if t == 'True' else 'no_aplicable')
        else:
            vacio_estado = 'no_aplicable'
        estado = pd.Series('observada', index=ids, dtype=object)
        estado[deducida.fillna(False)] = 'deducida'
        estado[imputada.fillna(False)] = 'imputada'
        vacio = valor.isna()
        estado[vacio] = vacio_estado[vacio] if isinstance(vacio_estado, pd.Series) else vacio_estado
        filas.append(pd.DataFrame({'participante_id': ids, 'variable': v, 'valor_original': valor.fillna('').to_numpy(),
                                   'estado': estado.to_numpy(), 'pregunta_previa_imputada': previa.astype(int).to_numpy()}))
    return pd.concat(filas, ignore_index=True), L


def resumen(celdas):
    t = celdas.pivot_table(index='variable', columns='estado', values='participante_id', aggfunc='count', fill_value=0)
    for e in ESTADOS:
        if e not in t:
            t[e] = 0
    t = t[ESTADOS].astype(int)
    t['heredadas'] = celdas[(celdas['valor_original'] == '') & (celdas['pregunta_previa_imputada'] == 1)].groupby('variable').size()
    t['heredadas'] = t['heredadas'].fillna(0).astype(int)
    return t.reindex(C.GENERALES + C.MODULOS)


def contrastar(res, limpio):
    """Compara cada recuento con las auditorías históricas. Devuelve una fila por comparación."""
    origen = pd.read_csv(C.ORIGEN, encoding='utf-8-sig').set_index('variable')
    figuras = pd.read_csv(C.AUDITORIA_FIGURAS, encoding='utf-8-sig').set_index('variable')
    filas = []

    def anotar(v, fuente, medida, actual, esperado):
        filas.append({'variable': v, 'fuente': fuente, 'medida': medida, 'esperado': int(esperado), 'reconstruido': int(actual),
                      'coincide': int(actual) == int(esperado)})

    for v in res.index:
        r, o = res.loc[v], origen.loc[v]
        if v == 'imc':
            anotar(v, 'origen_respuestas_34D', 'observadas', r['observada'], o['observadas'])
            anotar(v, 'origen_respuestas_34D', 'imputadas en 35A = faltantes de la figura', r['imputada'], o['faltantes'])
            continue
        anotar(v, 'origen_respuestas_34D', 'observadas', r['observada'], o['observadas'])
        anotar(v, 'origen_respuestas_34D', 'deducidas', r['deducida'], o['deducidas'])
        anotar(v, 'origen_respuestas_34D', 'imputadas', r['imputada'], o['imputadas'])
        anotar(v, 'origen_respuestas_34D', 'no aplicables y faltantes', r['no_aplicable'] + r['faltante'], o['no_aplica'] + o['faltantes'])
        anotar(v, 'origen_respuestas_34D', 'vacías por previa imputada', r['heredadas'], o['faltantes_por_previa_imputada'] + o['no_aplica_por_previa_imputada'])
        if v in figuras.index:
            anotar(v, 'auditoria_figuras_34D', 'imputadas', r['imputada'], figuras.loc[v, 'imputadas_exactas_529'])
        marca = f'{v}_imputado'
        if marca in limpio.columns:
            # La marca del limpio cuenta las 546 filas; aquí solo importan las 529.
            ids = limpio.index[limpio['mrs_completo'] == '1']
            anotar(v, 'marca _imputado del conjunto limpio', 'imputadas', r['imputada'], (limpio.loc[ids, marca] == '1').sum())
    return pd.DataFrame(filas)
