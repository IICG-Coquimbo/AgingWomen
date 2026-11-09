"""
Corrección controlada de la Fase 34: origen de las respuestas de cada figura de la Fase 34D.

Uso, desde la raíz del proyecto:
    python analisis/revision_correctiva_fase34/origen_respuestas.py

Reconstruye la limpieza en memoria (la misma de auditoria_fase34.py) y cuenta, sobre las 529 participantes
y con el denominador de cada figura, cuántas respuestas son observadas, deducidas o imputadas. Faltantes y
no aplicables se toman del resumen histórico de la 34D, sin recalcularlos.

Solo lee. Escribe únicamente tablas/origen_respuestas_34D.csv. La verdad del simulador no se usa.
"""
import sys
from pathlib import Path

import pandas as pd

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(AQUI.parent))

import auditoria_fase34 as A  # noqa: E402
from eda import univariado as U  # noqa: E402

RESUMEN = A.RES / 'eda_univariado_resumen.csv'
SALIDA = A.TABLAS / 'origen_respuestas_34D.csv'
# Pregunta que decide si la variable aplica: si esa pregunta fue imputada, también lo fue su "aplica".
PREGUNTA_PREVIA = {
    'lugar_trabajo_comprensivo': 'trabaja_actualmente', 'estres_entorno_laboral': 'trabaja_actualmente',
    'cantidad_personas_cuida': 'cuida_otras_personas', 'a_quien_cuida': 'cuida_otras_personas',
    'sobrecarga_fisica_emocional': 'cuida_otras_personas', 'frecuencia_aerobico': 'realiza_aerobico',
    'frecuencia_bajo_impacto': 'realiza_bajo_impacto', 'frecuencia_fuerza': 'realiza_fuerza',
    'tipo_metodo_anticonceptivo': 'usa_metodo_anticonceptivo'}


def dependientes_etapa():
    """Filas cuya etapa se calculó con una entrada imputada que la regla realmente usó."""
    meses = pd.to_numeric(A.M['meses_desde_fum'], errors='coerce')
    ovario_no = A.M['tiene_ovario'] == 'NO'
    return A.imputada('tiene_ovario') | (A.imputada('menstruacion_llega') & ~ovario_no & (meses < 12)) | (
        A.imputada('tiene_utero') & ~ovario_no & meses.isna())


def derivadas():
    """Variables calculadas en el paso 10: no son respuestas; se informa si dependen de una imputada."""
    doble = A.imputada('trabaja_actualmente') | A.imputada('cuida_otras_personas')
    return {'doble_carga': int(doble.sum()), 'etapa_menopausica': int(dependientes_etapa().sum()),
            'imc': 0, 'mrs_total': 0, 'severidad_mrs_4': 0, 'severo_mrs': 0}


def base_figura(v):
    """Máscara de quienes debían responder, igual que U.describir, sobre las participantes con MRS completo."""
    condicion = U.CONDICIONES.get(v)
    if condicion is None:
        return pd.Series(True, index=A.M.index)
    datos = A.M.astype(object).where(A.M.notna(), pd.NA)
    aplica = condicion[1](datos).fillna(False).astype(bool)
    if condicion is U._MENSTRUA:
        aplica = aplica | pd.to_numeric(A.M['meses_desde_fum'], errors='coerce').isna()
    return aplica


def main():
    resumen = pd.read_csv(RESUMEN, encoding='utf-8-sig')
    calculadas = derivadas()
    filas = []
    for f in resumen.itertuples():
        v = f.variable
        if v in calculadas:
            dep = calculadas[v]
            filas.append({'variable': v, 'n_valido': f.n_valido, 'observadas': f.n_valido - dep, 'deducidas': 0, 'imputadas': 0,
                          'faltantes': f.n_faltante, 'no_aplica': f.n_no_aplica, 'derivada': True, 'dependen_de_imputada': dep,
                          'faltantes_por_previa_imputada': 0, 'no_aplica_por_previa_imputada': 0})
            continue
        aplica = base_figura(v)
        con_valor = aplica & A.M[v].notna()
        imp = int((A.imputada(v) & con_valor).sum())
        ded = int((A.deducida(v) & con_valor).sum())
        previa = A.imputada(PREGUNTA_PREVIA[v]) if v in PREGUNTA_PREVIA else pd.Series(False, index=A.M.index)
        filas.append({'variable': v, 'n_valido': f.n_valido, 'observadas': f.n_valido - imp - ded, 'deducidas': ded, 'imputadas': imp,
                      'faltantes': f.n_faltante, 'no_aplica': f.n_no_aplica, 'derivada': False, 'dependen_de_imputada': 0,
                      'faltantes_por_previa_imputada': int((previa & aplica & A.M[v].isna()).sum()),
                      'no_aplica_por_previa_imputada': int((previa & ~aplica).sum())})
        if int(con_valor.sum()) != f.n_valido:
            raise SystemExit(f'{v}: la base reconstruida ({int(con_valor.sum())}) no coincide con la figura ({f.n_valido})')
    t = pd.DataFrame(filas)
    t.to_csv(SALIDA, index=False, encoding='utf-8-sig')

    # El recuento debe coincidir con la auditoría de figuras ya entregada.
    aud = pd.read_csv(A.TABLAS / 'auditoria_figuras_34D.csv', encoding='utf-8-sig').set_index('variable')
    cruce = t[t['variable'].isin(aud.index)].set_index('variable')
    distintas = cruce.index[cruce['imputadas'] != aud.loc[cruce.index, 'imputadas_exactas_529']].tolist()
    con = cruce[cruce['imputadas'] > 0]
    print('figuras:', len(t), '| evaluadas:', len(cruce), '| con imputadas:', len(con), '| con faltante 0:', int((con['faltantes'] == 0).sum()))
    print('distintas de la auditoría:', distintas)
    print('con deducidas:', t.loc[t['deducidas'] > 0, ['variable', 'deducidas']].to_dict('records'))
    print('derivadas:', t.loc[t['derivada'], ['variable', 'n_valido', 'dependen_de_imputada']].to_dict('records'))
    print(t.set_index('variable').loc[['sobrecarga_fisica_emocional', 'lugar_trabajo_comprensivo', 'estres_entorno_laboral',
                                       'trabaja_actualmente', 'cuida_otras_personas', 'cantidad_personas_cuida',
                                       'usa_medicamentos_diabetes', 'horas_sedentarismo', 'a_quien_cuida', 'tipo_sangrado']].to_string())


if __name__ == '__main__':
    main()
