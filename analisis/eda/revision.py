"""
Revisión de atípicos y de coherencia entre mediciones (Fase 34).

Criterio aprobado por la usuaria (2026-10-18): la regla de Tukey (1,5 × RIC)
DETECTA atípicos, pero un atípico estadístico no es un error. Se elimina solo
lo imposible o incoherente (eso ya lo hace la limpieza, pasos 5 y 9); los
valores extremos clínicamente posibles se conservan y se justifica por qué,
variable por variable.
"""
import pandas as pd

from limpieza import reglas as R

from . import variables as V

# Variable → (umbral clínico de "valor alto", texto del criterio). Los atípicos
# altos que caen en estas categorías describen condiciones reales y frecuentes.
CRITERIO_CLINICO = {
    'imc': (lambda x: x >= 40, 'IMC ≥ 40: obesidad grado III (OMS)'),
    'peso_kg': (None, 'acompaña al IMC; se juzga con él'),
    'talla_actual_cm': (None, 'estatura adulta dentro del rango poblacional'),
    'circunferencia_cintura_cm': (lambda x: x >= 88, 'cintura ≥ 88 cm: obesidad abdominal (ATP III, mujer)'),
    'edad': (None, 'criterio de inclusión de la encuesta (40-65, excepción quirúrgica)'),
    'horas_sedentarismo': (None, 'horas sentada al día (0-24)'),
    'presion_sistolica': (lambda x: x >= 140, 'sistólica ≥ 140: hipertensión (MINSAL)'),
    'presion_diastolica': (lambda x: x >= 90, 'diastólica ≥ 90: hipertensión (MINSAL)'),
    'colesterol_total_mg_dl': (lambda x: x >= 240, 'colesterol ≥ 240: alto (ATP III)'),
    'colesterol_hdl_mg_dl': (lambda x: x < 50, 'HDL < 50: bajo en mujer (ATP III)'),
    'trigliceridos_mg_dl': (lambda x: x >= 200, 'triglicéridos ≥ 200: altos (ATP III)'),
    'glicemia_mg_dl': (lambda x: x >= 126, 'glicemia ≥ 126: rango de diabetes (ADA/MINSAL)'),
    'mrs_total': (lambda x: x >= 16, 'MRS ≥ 16: síntomas severos'),
}
VARIABLES = list(CRITERIO_CLINICO)


def _observados(df, c):
    """Valores medidos de `c` (sin los imputados, que no son observaciones)."""
    x = V.numerica(df[c])
    marca = 'peso_kg_imputado' if c == 'imc' else f'{c}_imputado'   # IMC con peso imputado no es medido
    if marca in df:
        x = x[df[marca] != '1']
    return x.dropna()


def atipicos(df):
    """Tabla de detección (Tukey) + decisión para cada variable continua."""
    filas = []
    for c in VARIABLES:
        x = _observados(df, c)
        q1, q3 = x.quantile([.25, .75])
        ric = q3 - q1
        bajo, alto = q1 - 1.5 * ric, q3 + 1.5 * ric
        inf, sup = x[x < bajo], x[x > alto]
        regla, texto = CRITERIO_CLINICO[c]
        rango = R.RANGOS.get(c)
        filas.append({
            'variable': c, 'n': len(x), 'q1': q1, 'q3': q3,
            'limite_inferior': bajo, 'limite_superior': alto,
            'atipicos_bajos': len(inf), 'atipicos_altos': len(sup),
            'valores_bajos': ', '.join(f'{v:g}' for v in sorted(inf.unique())),
            'valores_altos': ', '.join(f'{v:g}' for v in sorted(sup.unique())),
            'rango_plausible': f'{rango[0]}-{rango[1]}' if rango else
            ('0-44' if c == 'mrs_total' else '40-65' if c == 'edad' else ''),
            'altos_en_categoria_clinica': int(regla(sup).sum()) if regla and len(sup) else 0,
            'criterio_clinico': texto,
            'decision': 'se conserva',
        })
    return pd.DataFrame(filas)


def coherencia(df):
    """
    Controles de coherencia entre mediciones sobre el conjunto limpio, con el
    tratamiento que aplica la limpieza. Los que la limpieza vacía o reimputa
    deben dar 0 casos; "talla actual > máxima" se conserva y solo anula la pérdida de talla.
    """
    pas, pad = V.numerica(df['presion_sistolica']), V.numerica(df['presion_diastolica'])
    talla, cintura = V.numerica(df['talla_actual_cm']), V.numerica(df['circunferencia_cintura_cm'])
    imc = V.numerica(df['imc'])
    ict = cintura / talla
    sin_tratar = 'no quedan casos'
    controles = [
        ('Diastólica ≥ sistólica', 'fisiológicamente imposible', (pad >= pas).sum(),
         'limpieza paso 5: ambas presiones vacías; paso 9: la que faltaba se imputa desde la otra'),
        (f'Cintura incoherente con el IMC (|z robusto| > {R.Z_CINTURA:g})',
         'la cintura sigue al IMC (r ≈ 0,9); un residuo tan grande indica error de registro',
         R.cintura_incoherente(df).sum(),
         'limpieza paso 5: cintura vacía; paso 9: imputada desde el IMC'),
        ('IMC fuera de 15-60', 'fuera de lo compatible con una adulta ambulatoria',
         (~imc.between(15, 60)).sum(), sin_tratar),
        ('Índice cintura/talla fuera de 0,30-0,90', 'proporción corporal imposible',
         (~ict.between(0.30, 0.90) & ict.notna()).sum(), sin_tratar),
        ('Talla actual > talla máxima', 'la talla máxima es la mayor alcanzada',
         (talla > V.numerica(df['talla_maxima_cm'])).sum(),
         'limpieza paso 10: la pérdida de talla queda sin dato (las tallas se conservan)'),
    ]
    return pd.DataFrame([{'control': c, 'por_que': p, 'casos': int(n), 'tratamiento': t}
                         for c, p, n, t in controles])


def correcciones(df):
    """
    Casos corregidos por la imputación por relación de la Fase 34 (antes se
    imputaba con la mediana y quedaban combinaciones incoherentes).
    """
    filas = []
    peso = df['peso_kg_imputado'] == '1' if 'peso_kg_imputado' in df else pd.Series(False, df.index)
    for _, f in df[peso].iterrows():
        filas.append({'participante_id': f['participante_id'], 'variable': 'peso_kg',
                      'valor_imputado': f['peso_kg'],
                      'contexto': (f"talla {f['talla_actual_cm']} cm, cintura {f['circunferencia_cintura_cm']} cm "
                                   f"→ IMC {f['imc']}") if f.get('circunferencia_cintura_cm_imputado') != '1'
                      else f"sin cintura medida: mediana; la cintura se imputa después desde el IMC ({f['imc']})"})
    for c, otra in (('presion_sistolica', 'presion_diastolica'), ('presion_diastolica', 'presion_sistolica')):
        marca, marca_otra = f'{c}_imputado', f'{otra}_imputado'
        sola = (df[marca] == '1') & (df[marca_otra] != '1') & df[otra].notna()
        for _, f in df[sola].iterrows():
            filas.append({'participante_id': f['participante_id'], 'variable': c, 'valor_imputado': f[c],
                          'contexto': f"{V.etiqueta(otra).lower()} medida = {f[otra]}"})
    return pd.DataFrame(filas)
