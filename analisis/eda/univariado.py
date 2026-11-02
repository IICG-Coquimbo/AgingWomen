"""
Fase 34D: análisis univariado variable por variable (reunión 2026-10-27).

Cada variable de la encuesta autoaplicada se describe sobre las participantes
con MRS completo, sin imputar nada nuevo. Los porcentajes usan como
denominador a quienes debían responder la pregunta:
  - preguntas generales: todas las participantes;
  - preguntas condicionales: solo quienes cumplen la condición (por ejemplo,
    frecuencia de fuerza solo entre quienes hacen fuerza);
  - selección múltiple: quienes respondieron (los % pueden sumar más de 100).

La baja variabilidad se marca cuando una categoría reúne el 80 % o más de las
respuestas válidas (criterio de la profesora). La decisión de eliminar (más
del 85 %, decisión de la usuaria 2026-10-28) se toma en la Fase 35A.
"""
import textwrap

import numpy as np
import pandas as pd

from . import graficos as G
from . import variables as V

UMBRAL_BAJA_VARIABILIDAD = 80

SECCIONES = {
    'identificacion': 'Identificación',
    'ginecologica': 'Etapa reproductiva y salud ginecológica',
    'salud': 'Medicamentos y digestión',
    'medidas': 'Medidas autodeclaradas',
    'prevision': 'Previsión de salud',
    'trabajo': 'Trabajo (solo quienes trabajan)',
    'cuidado': 'Cuidado de otras personas',
    'actividad': 'Actividad física',
    'alimentacion': 'Alimentación',
    'sustancias': 'Sustancias',
    'mrs': 'Síntomas (MRS) y variable objetivo',
}

# Condiciones de aplicación: (texto para la nota, función df -> máscara booleana).
_MENSTRUA = ('quienes aún menstrúan (última menstruación hace menos de 12 meses)',
             lambda d: V.numerica(d['meses_desde_fum']) < 12)
CONDICIONES = {
    'menstruacion_llega': _MENSTRUA, 'tipo_sangrado': _MENSTRUA, 'usa_metodo_anticonceptivo': _MENSTRUA,
    'tipo_metodo_anticonceptivo': ('quienes usan método anticonceptivo',
                                   lambda d: d['usa_metodo_anticonceptivo'] == 'SI'),
    'lugar_trabajo_comprensivo': ('quienes trabajan', lambda d: d['trabaja_actualmente'] == 'True'),
    'estres_entorno_laboral': ('quienes trabajan', lambda d: d['trabaja_actualmente'] == 'True'),
    'cantidad_personas_cuida': ('quienes cuidan a otras personas', lambda d: d['cuida_otras_personas'] == 'SI'),
    'a_quien_cuida': ('quienes cuidan a otras personas', lambda d: d['cuida_otras_personas'] == 'SI'),
    'sobrecarga_fisica_emocional': ('quienes cuidan a otras personas',
                                    lambda d: d['cuida_otras_personas'] == 'SI'),
    'frecuencia_aerobico': ('quienes realizan ejercicio aeróbico', lambda d: d['realiza_aerobico'] == 'SI'),
    'frecuencia_bajo_impacto': ('quienes realizan ejercicio de bajo impacto',
                                lambda d: d['realiza_bajo_impacto'] == 'SI'),
    'frecuencia_fuerza': ('quienes realizan ejercicio de fuerza', lambda d: d['realiza_fuerza'] == 'SI'),
}

# Intervalos de las numéricas: lista de (desde, hasta, nombre), ambos incluidos.
INTERVALOS = {
    'edad': [(0, 39, 'Menos de 40'), (40, 44, '40-44'), (45, 49, '45-49'), (50, 54, '50-54'),
             (55, 59, '55-59'), (60, 120, '60 o más')],
    # Clasificación OMS del IMC (TRS 894, 2000).
    'imc': [(0, 18.49, 'Menor a 18,5'), (18.5, 24.99, '18,5-24,9'), (25, 29.99, '25-29,9'),
            (30, 34.99, '30-34,9'), (35, 39.99, '35-39,9'), (40, 100, '40 o más')],
    'peso_kg': [(0, 49.9, 'Menos de 50'), (50, 59.9, '50-59'), (60, 69.9, '60-69'), (70, 79.9, '70-79'),
                (80, 89.9, '80-89'), (90, 99.9, '90-99'), (100, 300, '100 o más')],
    'talla_actual_cm': [(0, 144.9, 'Menos de 145'), (145, 149.9, '145-149'), (150, 154.9, '150-154'),
                        (155, 159.9, '155-159'), (160, 164.9, '160-164'), (165, 169.9, '165-169'),
                        (170, 250, '170 o más')],
    'horas_sedentarismo': [(0, 3, '0-3 h'), (4, 6, '4-6 h'), (7, 9, '7-9 h'), (10, 24, '10 h o más')],
    'mrs_total': [(a, a + 4, f'{a}-{a + 4}') for a in range(0, 40, 5)] + [(40, 44, '40-44')],
}
UNIDADES = {'edad': 'años', 'imc': 'kg/m²', 'peso_kg': 'kg', 'talla_actual_cm': 'cm',
            'horas_sedentarismo': 'horas al día', 'mrs_total': 'puntos (0-44)'}

ETIQUETAS_SI_NO = {'SI': 'Sí', 'NO': 'No', 'True': 'Sí', 'False': 'No', '1': 'Sí', '0': 'No'}
ETAPAS = {'premenopausia': 'Premenopausia', 'perimenopausia': 'Perimenopausia',
          'posmenopausia': 'Posmenopausia', 'quirurgica': 'Quirúrgica',
          'indeterminada': 'Indeterminada', 'indeterminada (histerectomía)': 'Indeterminada (histerectomía)'}
ABREVIAR = {'No se identifica con ningún pueblo originario/afro': 'Ninguno',
            'Afrodescendiente chileno/latinoamericano': 'Afrodescendiente',
            'Yo preparo algunas y otras personas otras': 'Compartido',
            'Otra persona de mi hogar prepara la mayoría': 'Otra persona del hogar',
            'Generalmente compro comida preparada': 'Compra comida preparada',
            'FF.AA. y de Orden (Capredena, Dipreca)': 'FF.AA. y de Orden',
            'Lickanantay / Atacameño': 'Lickanantay'}
ETIQUETAS_EXTRA = {'severidad_mrs_4': 'Severidad MRS (4 clases)',
                   'severo_mrs': 'MRS severo (16 puntos o más)', 'comuna': 'Comuna de residencia',
                   'doble_carga': 'Doble carga (trabaja y cuida)'}


def _v(seccion, tipo, *variables):
    return [(v, seccion, tipo) for v in variables]


# (variable, sección, tipo). Orden = orden del informe.
VARIABLES = [
    *_v('identificacion', 'numérica continua', 'edad'),
    *_v('identificacion', 'categórica nominal', 'comuna', 'origen_procedencia', 'pueblo_originario_afro',
        'genero'),
    *_v('identificacion', 'binaria', 'trabaja_actualmente'),
    *_v('ginecologica', 'categórica nominal', 'etapa_menopausica', 'menstruacion_llega'),
    *_v('ginecologica', 'ordinal', 'tipo_sangrado'),
    *_v('ginecologica', 'binaria', 'usa_metodo_anticonceptivo'),
    *_v('ginecologica', 'categórica nominal', 'tipo_metodo_anticonceptivo'),
    *_v('ginecologica', 'binaria', 'usa_terapia_hormonal', 'operada_no_mas_hijos', 'tiene_utero',
        'tiene_ovario', 'tiene_pareja', 'tiene_actividad_sexual'),
    *_v('salud', 'binaria', 'usa_medicamentos_diabetes', 'usa_medicamentos_presion'),
    *_v('salud', 'ordinal', 'evacuacion_intestinal', 'distension_abdominal'),
    *_v('medidas', 'numérica continua', 'peso_kg', 'talla_actual_cm', 'imc'),
    *_v('prevision', 'categórica nominal', 'prevision'),
    *_v('trabajo', 'ordinal', 'lugar_trabajo_comprensivo', 'estres_entorno_laboral'),
    *_v('cuidado', 'binaria', 'cuida_otras_personas'),
    *_v('cuidado', 'ordinal', 'cantidad_personas_cuida'),
    *_v('cuidado', 'selección múltiple', 'a_quien_cuida'),
    *_v('cuidado', 'ordinal', 'sobrecarga_fisica_emocional'),
    *_v('cuidado', 'binaria', 'doble_carga'),
    *_v('actividad', 'ordinal', 'dias_ejercicio_semana'),
    *_v('actividad', 'binaria', 'realiza_aerobico'), *_v('actividad', 'ordinal', 'frecuencia_aerobico'),
    *_v('actividad', 'binaria', 'realiza_bajo_impacto'), *_v('actividad', 'ordinal', 'frecuencia_bajo_impacto'),
    *_v('actividad', 'binaria', 'realiza_fuerza'), *_v('actividad', 'ordinal', 'frecuencia_fuerza'),
    *_v('actividad', 'numérica discreta', 'horas_sedentarismo'),
    *_v('alimentacion', 'categórica nominal', 'quien_prepara_comidas'),
    *_v('alimentacion', 'ordinal', 'frecuencia_comida_fuera', 'falta_tiempo_influye', 'vasos_agua_dia',
        'platos_verduras_dia', 'frutas_dia', 'panes_dia', 'lacteos_dia', 'jugos_gaseosas_dia',
        'bebidas_energeticas_dia', 'pescado_semana', 'legumbres_semana', 'carnes_semana',
        'golosinas_semana'),
    *_v('sustancias', 'ordinal', 'tabaco_frecuencia', 'alcohol_frecuencia', 'marihuana_frecuencia'),
    *_v('mrs', 'ordinal', *V.MRS_ITEMS),
    *_v('mrs', 'numérica discreta', 'mrs_total'),
    *_v('mrs', 'ordinal', 'severidad_mrs_4'),
    *_v('mrs', 'binaria', 'severo_mrs'),
]

# Excluidas del univariado y motivo (quedan en el log y en el informe).
EXCLUIDAS = {
    'identificadores y control de registro': ['participante_id', 'uuid_local', 'rut_hash', 'usuario_id', 'ronda',
                                              'ronda_actual', 'origen_registro', 'excepcion_edad'],
    'fechas administrativas o de origen': ['sincronizado_en', 'creado_en', 'ultima_finalizacion_en',
                                           'fecha_evaluacion', 'fecha_nacimiento', 'fecha_registro',
                                           'fecha_ultimo_empa', 'fecha_ultima_menstruacion (se usa vía etapa)'],
    'solo personal de salud (reunión 2026-10-20)': ['talla_maxima_cm', 'circunferencia_cintura_cm',
                                                    'presion_sistolica', 'presion_diastolica',
                                                    'colesterol_total_mg_dl', 'colesterol_hdl_mg_dl',
                                                    'trigliceridos_mg_dl', 'glicemia_mg_dl', 'vdrl_rpr',
                                                    'riesgo_cv_atp3', 'fecha_ultimo_pap', 'resultado_pap',
                                                    'fecha_mamografia', 'resultado_birads',
                                                    'fecha_ecotomografia_mamaria', 'perdida_talla_cm',
                                                    'presion_elevada'],
    'consecuencias del MRS (módulo aparte)': list(V.IMPACTO),
    'decisión del equipo (nivel educacional, ConocimientoSistema, satisfacción)': [
        'nivel_educacion', 'conoce_sistema_publico_climaterio', '… (ConocimientoSistema completo salvo previsión)',
        'facilidad_uso', 'fatiga_mental', 'comodidad_diseno', 'recomendaria', 'incomodidad'],
    'constante en el conjunto': ['region_residencia (100 % Coquimbo)'],
    'texto libre de "otro"': ['tipo_metodo_anticonceptivo_otro', 'a_quien_cuida_otro', 'quien_prepara_comidas_otro',
                              'comentario_incomodidad'],
    'derivadas repetidas o marcas de limpieza': ['tramo_edad (= intervalos de edad)', 'imc_categoria (= intervalos OMS)',
                                                 'mrs_somatico', 'mrs_psicologico', 'mrs_urogenital', 'mrs_completo',
                                                 'meses_desde_fum', 'incoherencia_*', '*_imputado'],
}


def etiqueta(v):
    return ETIQUETAS_EXTRA.get(v) or V.etiqueta(v)


def preparar(df):
    """Participantes con MRS completo + variables objetivo nuevas."""
    mrs = df[df['mrs_completo'] == '1'].copy()
    total = V.numerica(mrs['mrs_total'])
    mrs['severidad_mrs_4'] = mrs['mrs_severidad']
    mrs['severo_mrs'] = (total >= V.CORTE_SEVERA).astype(int).astype(str)
    return mrs


def _opciones(v, campos):
    opciones = campos.get(v, {}).get('opciones') or {}
    return {str(k): ABREVIAR.get(o, o.split(' o de origen')[0]) for k, o in opciones.items()}


def _en_intervalos(x, tramos):
    r = pd.Series(np.nan, index=x.index, dtype=object)
    for a, b, nombre in tramos:
        r[x.between(a, b)] = nombre
    return r, [n for *_, n in tramos]


def respuestas(df, v, tipo, campos, comunas):
    """(serie de respuestas legibles, orden de las categorías a mostrar)."""
    s = df[v]
    if v in INTERVALOS:
        return _en_intervalos(V.numerica(s), INTERVALOS[v])
    if tipo == 'binaria':
        return s.map(ETIQUETAS_SI_NO), ['Sí', 'No']
    if v == 'etapa_menopausica':
        return s.map(ETAPAS), list(ETAPAS.values())
    if v == 'severidad_mrs_4':
        return s, V.ORDEN_SEVERIDAD
    if v == 'comuna':
        return s, comunas
    etiquetas = _opciones(v, campos)
    return s.map(lambda x: etiquetas.get(x, x) if pd.notna(x) else x), list(etiquetas.values())


def describir(mrs, campos, comunas, diccionario):
    """
    Una fila por variable (resumen) + frecuencias largas. Las figuras se
    dibujan aparte con `figura`, a partir de las mismas frecuencias.
    """
    dicc = diccionario.set_index('variable')
    filas, largas = [], []
    for v, seccion, tipo in VARIABLES:
        nota_aplica, aplica = CONDICIONES.get(v, (None, None))
        aplica = aplica(mrs) if aplica else pd.Series(True, index=mrs.index)
        if CONDICIONES.get(v) is _MENSTRUA:
            sin_fum = V.numerica(mrs['meses_desde_fum']).isna()
            aplica = aplica | sin_fum        # sin fecha: no se sabe si aplica → cuenta como faltante
        base = mrs[aplica]
        if tipo == 'selección múltiple':
            validas = base[v].dropna()
            marcadas = validas.str.split(', ').explode()
            conteo = marcadas.value_counts()
            n_valido = len(validas)
        else:
            s, orden = respuestas(base, v, tipo, campos, comunas)
            validas = s.dropna()
            n_valido = len(validas)
            conteo = validas.value_counts().reindex(orden, fill_value=0)
            if tipo == 'categórica nominal' and v != 'etapa_menopausica':
                conteo = conteo.sort_values(ascending=False, kind='stable')
            # Valores fuera del catálogo (no deberían quedar tras la limpieza): se agregan al final.
            extra = validas[~validas.isin(orden)].value_counts()
            conteo = pd.concat([conteo, extra])
        n_faltante = int(aplica.sum() - n_valido)
        pct = 100 * conteo / n_valido if n_valido else conteo * 0
        p = conteo[conteo > 0] / conteo.sum()
        entropia = float(-(p * np.log2(p)).sum()) if tipo != 'selección múltiple' else np.nan
        dominante = conteo.idxmax()
        pct_dom = float(pct.max())
        # Imputación de la Fase 34B (por moda/mediana): cota de la dominancia sin esos valores.
        tratamiento = dicc.at[v, 'tratamiento'] if v in dicc.index else ''
        imputados = 0
        marca = f'{v}_imputado'
        if marca in mrs:
            imputados = int((base[marca] == '1').sum())
        elif isinstance(tratamiento, str) and tratamiento.startswith('imputada'):
            imputados = int(dicc.at[v, 'faltantes'])     # cota superior (diccionario cuenta sobre 546)
        cota = (100 * max(conteo.max() - imputados, 0) / (n_valido - imputados)
                if imputados and tipo != 'selección múltiple' and n_valido > imputados else np.nan)
        forma = forma_distribucion(V.numerica(base[v]).dropna()) if tipo.startswith('numérica') else {}
        filas.append({
            'variable': v, 'etiqueta': etiqueta(v), 'seccion_encuesta': SECCIONES[seccion], 'tipo': tipo,
            'unidad': UNIDADES.get(v, ''), 'denominador': nota_aplica or 'todas las participantes con MRS completo',
            'n_aplica': int(aplica.sum()), 'n_no_aplica': int((~aplica).sum()), 'n_valido': n_valido,
            'n_faltante': n_faltante, 'porcentaje_faltante': 100 * n_faltante / aplica.sum(),
            'n_categorias': len(conteo), 'categoria_dominante': dominante, 'porcentaje_dominante': pct_dom,
            'entropia_shannon_bits': entropia,
            'entropia_normalizada': entropia / np.log2(len(conteo)) if len(conteo) > 1 else np.nan,
            'baja_variabilidad': 'sí' if pct_dom >= UMBRAL_BAJA_VARIABILIDAD and tipo != 'selección múltiple'
            else 'no',
            'imputados_34B': imputados, 'pct_dominante_sin_imputados_34B': cota,
            'tratamiento_34B': tratamiento if isinstance(tratamiento, str) else '',
            'ruta_figura': f'figuras/eda_univariado/univariado_{v}.png',
            **{k: forma.get(k, np.nan) for k in FORMA},
        })
        largas += [{'variable': v, 'categoria': c, 'n': int(conteo[c]), 'pct': float(pct[c])} for c in conteo.index]
    resumen = pd.DataFrame(filas)
    resumen['comentario'] = resumen.apply(comentario, axis=1)
    return resumen, pd.DataFrame(largas)


def _pct(x):
    return f'{x:.1f}'.replace('.', ',') + ' %'


# Estadísticos de forma de las numéricas (columnas del resumen; NaN en las demás).
FORMA = ['media', 'desviacion_estandar', 'mediana', 'minimo', 'maximo', 'asimetria', 'curtosis',
         'atipicos_tukey']


def limites_tukey(x):
    q1, q3 = x.quantile(0.25), x.quantile(0.75)
    return q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)


def forma_distribucion(x):
    """
    Asimetría = coeficiente de Fisher-Pearson ajustado (G1, `Series.skew`);
    curtosis = exceso de curtosis ajustado (G2, `Series.kurt`; 0 = normal).
    """
    bajo, alto = limites_tukey(x)
    return {'media': x.mean(), 'desviacion_estandar': x.std(), 'mediana': x.median(), 'minimo': x.min(),
            'maximo': x.max(), 'asimetria': x.skew(), 'curtosis': x.kurt(),
            'atipicos_tukey': int((~x.between(bajo, alto)).sum())}


def leer_asimetria(g1):
    """Lectura habitual del coeficiente: |G1| < 0,5 simétrica; 0,5-1 moderada; > 1 marcada."""
    if abs(g1) < 0.5:
        return 'aproximadamente simétrica'
    lado = 'cola hacia valores altos' if g1 > 0 else 'cola hacia valores bajos'
    return f'asimetría {"moderada" if abs(g1) <= 1 else "marcada"} ({lado})'


def leer_curtosis(g2):
    """Exceso de curtosis: |G2| < 1 similar a la normal; > 1 colas pesadas; < −1 achatada."""
    if abs(g2) < 1:
        return 'colas similares a la normal'
    return 'colas pesadas (más valores extremos)' if g2 > 0 else 'achatada (pocos valores extremos)'


def comentario(f):
    partes = []
    if f.tipo == 'selección múltiple':
        partes.append(f'Selección múltiple: la opción más marcada es «{f.categoria_dominante}» '
                      f'({_pct(f.porcentaje_dominante)} de quienes respondieron); los % pueden sumar más de 100.')
    elif f.baja_variabilidad == 'sí':
        partes.append(f'Baja variabilidad: «{f.categoria_dominante}» concentra {_pct(f.porcentaje_dominante)} '
                      f'de las respuestas válidas.')
        if f.porcentaje_dominante > 85:
            partes.append('Supera el 85 %: candidata a eliminación en la Fase 35A.')
        else:
            partes.append('Entre 80 % y 85 %: se conserva (decisión de la usuaria 2026-10-28).')
    elif f.entropia_normalizada >= 0.8:
        partes.append(f'Respuestas repartidas entre {f.n_categorias} categorías '
                      f'(entropía normalizada {f.entropia_normalizada:.2f}).')
    else:
        partes.append(f'Predomina «{f.categoria_dominante}» ({_pct(f.porcentaje_dominante)}), '
                      f'sin llegar al 80 %.')
    if f.n_no_aplica:
        partes.append(f'Condicional: % sobre {f.denominador} (n = {f.n_aplica}).')
    if f.porcentaje_faltante >= 5:
        partes.append(f'Faltante {_pct(f.porcentaje_faltante)} (n = {f.n_faltante}).')
    if f.imputados_34B and pd.notna(f.pct_dominante_sin_imputados_34B):
        cruza = (f.porcentaje_dominante >= 80) != (f.pct_dominante_sin_imputados_34B >= 80) or \
                (f.porcentaje_dominante > 85) != (f.pct_dominante_sin_imputados_34B > 85)
        if cruza:
            partes.append(f'Ojo: sin los {f.imputados_34B} valores imputados en 34B la dominancia baja a '
                          f'{_pct(f.pct_dominante_sin_imputados_34B)} y cambia de tramo.')
    return ' '.join(partes)


# --- Figuras ------------------------------------------------------------------

def _rotulo(p, n):
    return f'{p:.1f}'.replace('.', ',') + f'%\n(n = {n})'


def figura(frec, f, ruta):
    """Barras verticales: % de respuestas válidas, rotuladas con % y n (incluye categorías con 0 casos)."""
    import matplotlib.pyplot as plt
    k = len(frec)
    largo = max(len(str(c)) for c in frec['categoria'])
    girar = k > 7 or (k > 4 and largo > 14)
    ancho = min(11, max(5.5, 0.85 * k + 2))
    fig, ax = plt.subplots(figsize=(ancho, 4.4 + (0.6 if girar else 0)))
    x = np.arange(k)
    color = G.AZUL
    barras = ax.bar(x, frec['pct'], color=color, width=0.62)
    tope = max(frec['pct'].max(), 1)
    for b, p, n in zip(barras, frec['pct'], frec['n']):
        ax.text(b.get_x() + b.get_width() / 2, p + tope * 0.015, _rotulo(p, n), ha='center', va='bottom',
                fontsize=7 if k > 8 else 8, color=G.TINTA_2 if n else G.TENUE)
    nombres = [textwrap.fill(str(c), 12 if not girar else 22, break_long_words=False) for c in frec['categoria']]
    if girar:
        ax.set_xticks(x, nombres, rotation=40, ha='right', fontsize=7.5)
    else:
        ax.set_xticks(x, nombres, fontsize=8)
    ax.set_ylim(0, min(100, tope * 1.25) if tope < 80 else tope * 1.2)
    ax.set_ylabel('% de respuestas válidas' + (' (puede sumar > 100)' if f.tipo == 'selección múltiple' else ''),
                  fontsize=8)
    ax.grid(axis='y', color=G.GRILLA, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(axis='x', length=0)
    subtitulo = (f'n válido = {f.n_valido} · faltante = {f.n_faltante} '
                 f'({_pct(f.porcentaje_faltante)}) · {f.tipo}')
    if f.n_no_aplica:
        subtitulo += f'\n% sobre {f.denominador}'
    lineas = subtitulo.count('\n') + 1
    ax.set_title(f.etiqueta, fontsize=11, pad=8 + 11 * lineas)
    ax.text(0, 1.02, subtitulo, transform=ax.transAxes, fontsize=7.5, color=G.TENUE, va='bottom')
    fig.tight_layout()
    fig.savefig(ruta, dpi=300)
    plt.close(fig)


def figura_distribucion(x, f, ruta):
    """
    Apoyo para numéricas: histograma con curva de densidad (KDE) y diagrama de
    caja de los valores observados. La KDE es gaussiana con ancho de banda de
    Scott y se escala a participantes por intervalo (n × ancho del intervalo)
    para leerla sobre el mismo eje que las barras.
    """
    import matplotlib.pyplot as plt
    from scipy.stats import gaussian_kde
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6.5, 4.6), sharex=True,
                                   gridspec_kw={'height_ratios': [3, 1]})
    discreta = f.tipo == 'numérica discreta'
    bins = (np.arange(x.min() - 0.5, x.max() + 1.5, 1) if discreta and x.max() - x.min() < 50
            else np.histogram_bin_edges(x, 25))
    ax1.hist(x, bins=bins, color=G.AZUL, edgecolor=G.SUPERFICIE, linewidth=0.6)
    malla = np.linspace(bins[0], bins[-1], 300)
    ax1.plot(malla, gaussian_kde(x, bw_method='scott')(malla) * len(x) * (bins[1] - bins[0]),
             color=G.RAMPA_SEVERIDAD[3], linewidth=1.6)
    ax1.set_ylabel('Participantes', fontsize=8)
    ax1.grid(axis='y', color=G.GRILLA, linewidth=0.8)
    ax1.set_axisbelow(True)
    media, mediana = x.mean(), x.median()
    ax1.axvline(media, color=G.ROJO, linewidth=1, linestyle=(0, (3, 3)))
    ax1.text(0.99, 0.95, f'media {media:.1f} · mediana {mediana:.1f} · DE {x.std():.1f}\n'
                         f'asimetría {x.skew():+.2f} · curtosis {x.kurt():+.2f}'.replace('.', ','),
             transform=ax1.transAxes, ha='right', va='top', fontsize=7.5, color=G.TINTA_2,
             linespacing=1.4)
    ax2.boxplot(x, vert=False, widths=0.6, whis=1.5, patch_artist=True,
                boxprops={'facecolor': '#cde2fb', 'edgecolor': G.AZUL},
                medianprops={'color': G.AZUL, 'linewidth': 1.5},
                whiskerprops={'color': G.EJE}, capprops={'color': G.EJE},
                flierprops={'marker': 'o', 'markersize': 3, 'markerfacecolor': G.ROJO,
                            'markeredgecolor': 'none'})
    ax2.set_yticks([])
    ax2.spines['left'].set_visible(False)
    ax2.set_xlabel(f.unidad, fontsize=8)
    ax1.set_title(f'{f.etiqueta}: distribución (valores observados)', fontsize=11, pad=18)
    ax1.text(0, 1.02, f'n = {len(x)} · curva: densidad KDE · línea roja: media · caja: regla de Tukey (1,5 × RIC)',
             transform=ax1.transAxes, fontsize=7.5, color=G.TENUE, va='bottom')
    fig.tight_layout()
    fig.savefig(ruta, dpi=300)
    plt.close(fig)


def figura_puntos(numericas, ruta, semilla=42):
    """
    Swarm plot de las numéricas en una sola imagen (2 columnas): un punto por
    participante sobre su valor, con un desplazamiento vertical aleatorio
    (jitter, semilla fija) para que no se tapen; caja de Tukey superpuesta y
    atípicos en rojo. Se usa jitter y no un enjambre exacto porque con valores
    enteros repetidos (edad, MRS) el enjambre se vuelve demasiado ancho.
    `numericas` = lista de (valores observados, fila del resumen).
    """
    import matplotlib.pyplot as plt
    azar = np.random.default_rng(semilla)
    filas = -(-len(numericas) // 2)
    fig, ejes = plt.subplots(filas, 2, figsize=(9, 2.3 * filas))
    for ax, (x, f) in zip(ejes.flat, numericas):
        bajo, alto = limites_tukey(x)
        fuera = ~x.between(bajo, alto)
        y = azar.uniform(-0.3, 0.3, len(x))
        ax.scatter(x[~fuera], y[~fuera.to_numpy()], s=5, color=G.AZUL, alpha=0.45, linewidths=0)
        ax.scatter(x[fuera], y[fuera.to_numpy()], s=9, color=G.ROJO, linewidths=0)
        ax.boxplot(x, vert=False, positions=[0], widths=0.75, whis=1.5, showfliers=False,
                   boxprops={'color': G.TINTA, 'linewidth': 0.9}, medianprops={'color': G.TINTA, 'linewidth': 1.4},
                   whiskerprops={'color': G.TINTA, 'linewidth': 0.9}, capprops={'color': G.TINTA, 'linewidth': 0.9})
        ax.set_yticks([])
        ax.set_ylim(-0.6, 0.6)
        for lado in ('left', 'right', 'top'):
            ax.spines[lado].set_visible(False)
        ax.spines['bottom'].set_color(G.EJE)
        ax.tick_params(axis='x', labelsize=7.5, colors=G.TINTA_2)
        ax.set_xlabel(f.unidad, fontsize=7.5, color=G.TINTA_2)
        ax.set_title(f'{f.etiqueta} (n = {len(x)}; atípicos: {int(fuera.sum())})', fontsize=9, loc='left')
    for ax in list(ejes.flat)[len(numericas):]:
        ax.set_visible(False)
    fig.suptitle('Variables numéricas: un punto por participante', fontsize=11, x=0.01, y=0.995, ha='left',
                 va='top', fontweight='bold')
    fig.text(0.01, 0.958, 'caja: mediana y cuartiles · bigotes y puntos rojos: regla de Tukey (1,5 × RIC) · '
             'la altura de cada punto es aleatoria, solo para separarlos', fontsize=7.5, color=G.TENUE, va='top')
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(ruta, dpi=300)
    plt.close(fig)
