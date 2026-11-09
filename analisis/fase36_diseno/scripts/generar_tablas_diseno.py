"""
Fase 36A (diseño): genera el diccionario de codificación y la matriz de decisiones de las 33 variables.

Solo lee conjuntos, diccionarios y resultados históricos. Calcula descriptivos por columna para justificar el diseño,
pero no construye matrices de modelado, no ajusta escaladores ni modelos, y no guarda valores por participante.
No usa la verdad del simulador.
Uso, desde analisis/: python fase36_diseno/scripts/generar_tablas_diseno.py
Escribe en fase36_diseno/: diccionario_codificacion_fase36.csv, matriz_decisiones_variables.csv y apoyo/.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ANALISIS = Path(__file__).resolve().parents[2]
RAIZ = ANALISIS.parent
sys.path.insert(0, str(ANALISIS))

from limpieza import catalogo  # noqa: E402

SALIDA = ANALISIS / 'fase36_diseno'
APOYO = SALIDA / 'apoyo'
RELEVANCIA = ANALISIS / 'reunion_2026-11-03' / 'revision_33_variables' / 'permutaciones_50000' / 'relevancia_33.csv'
F35 = RAIZ / 'datos' / 'analitico' / 'dataset_fase35.csv'
LIMPIO = RAIZ / 'datos' / 'limpio_usuaria' / 'dataset_usuaria_limpio.csv'
RESUMEN = ANALISIS / 'resultados' / 'usuaria' / 'eda_univariado_resumen.csv'
ORIGEN = ANALISIS / 'revision_correctiva_fase34' / 'tablas' / 'origen_respuestas_34D.csv'
DICC35 = ANALISIS / 'resultados' / 'usuaria' / 'diccionario_datos_fase35.csv'

CONTINUAS = {'edad': 'años', 'imc': 'kg/m²', 'horas_sedentarismo': 'horas al día'}
BINARIAS = {'trabaja_actualmente': ('True', 'False'), 'tiene_pareja': ('SI', 'NO'), 'tiene_actividad_sexual': ('SI', 'NO'),
            'operada_no_mas_hijos': ('SI', 'NO'), 'usa_medicamentos_presion': ('SI', 'NO')}
NOMINALES = {'quien_prepara_comidas'}
LABORALES = ['lugar_trabajo_comprensivo', 'estres_entorno_laboral']
SOBRECARGA = 'sobrecarga_fisica_emocional'
# Nivel estructural: la pregunta no se mostró porque la madre vale NO; el conjunto de la Fase 35 lo codifica como 0.
ESTRUCTURAL = {'frecuencia_aerobico': ('realiza_aerobico', 'No lo realiza'), 'frecuencia_bajo_impacto': ('realiza_bajo_impacto', 'No lo realiza'),
               'frecuencia_fuerza': ('realiza_fuerza', 'No lo realiza'), 'cantidad_personas_cuida': ('cuida_otras_personas', 'No cuida')}
# Niveles cuyo significado es «cero de exposición», aunque su código no sea 0.
CERO_SEMANTICO = {'dias_ejercicio_semana': 1, 'frecuencia_comida_fuera': 1, 'vasos_agua_dia': 1, 'platos_verduras_dia': 1, 'frutas_dia': 1,
                  'panes_dia': 1, 'lacteos_dia': 1, 'jugos_gaseosas_dia': 1, 'pescado_semana': 1, 'legumbres_semana': 1, 'carnes_semana': 1,
                  'golosinas_semana': 1, 'tabaco_frecuencia': 1, 'alcohol_frecuencia': 1}
UMBRAL_RARO = 5.0
NOTAS = {
    'edad': 'Sin imputaciones. Rango 36-65: 22 menores de 40 y 77 mayores de 60. La plataforma admite 40-65 y bajo 40 con excepción. La Fase 37 compara con y sin edad.',
    'imc': '262 de 529 (49,5 %) imputados por la media 29,23. Sus parámetros de escala salen de las 267 observadas, para no comprimir su escala por la imputación. Escenarios con y sin IMC.',
    'horas_sedentarismo': 'Numérica discreta. 27 imputadas: su asimetría y curtosis históricas incluyen esas imputadas (limitación A1).',
    'trabaja_actualmente': '22 imputadas como Sí permanecen en la capa general. Tienen procedencia propia, no son respuesta observada. Sensibilidad S-TRA.',
    'tiene_pareja': 'Pregunta madre de una consecuencia excluida (cambio en la relación), que no entra.',
    'tiene_actividad_sexual': 'No es condicional a tener pareja (21 sin pareja responden Sí). Revisar solapamiento conceptual con el ítem sexual del MRS (D-10).',
    'operada_no_mas_hijos': 'Dominancia de 80,3 %.',
    'usa_medicamentos_presion': 'Dominancia de 83,2 %.',
    'quien_prepara_comidas': 'COMPRO (22) y OTRO (7) están bajo 5 %. PCA: se conservan, porque la codificación no los amplifica. FAMD: se agrupan, porque el método pondera por 1/p.',
    'evacuacion_intestinal': 'Mayor código significa menor frecuencia, y 1 no es necesariamente mejor que 2: orden de frecuencia, no de salud.',
    'distension_abdominal': 'Podría solaparse con síntomas según advertencias de Random Forest; no es un ítem del MRS.',
    'frecuencia_aerobico': 'Código 1 «Nunca» admitido y nunca observado. Cero estructural: 424, de los cuales 29 dependen de realiza_aerobico imputado como No. Sensibilidad S-EJE.',
    'frecuencia_bajo_impacto': 'Código 1 «Nunca» admitido y nunca observado. Cero estructural: 305, de los cuales 22 dependen de realiza_bajo_impacto imputado como No. Sensibilidad S-EJE.',
    'frecuencia_fuerza': 'Código 1 «Nunca» admitido y nunca observado. Cero estructural: 448 (84,7 %), de los cuales 28 dependen de realiza_fuerza imputado como No. Sensibilidad S-EJE.',
    'cantidad_personas_cuida': 'El 0 es un cero válido de cuidado; no significa falta de sobrecarga. 21 ceros dependen de cuida_otras_personas imputado como No. Sensibilidad S-CUI.',
    'tabaco_frecuencia': 'Distribución bimodal: Nunca 75,4 % y Diariamente 15,5 %. El paso entre niveles no es homogéneo; se trata como categórica en FAMD.',
    'dias_ejercicio_semana': 'Asociada con bajo impacto (rho = 0,64), aeróbico (0,51) y fuerza (0,42): el bloque de ejercicio aporta correlación a PCA.',
    'lugar_trabajo_comprensivo': 'No entra a la capa general. Se excluyen los 0 de quienes no trabajan y los 3 de las 22. Dentro de las 287 hay 16 imputadas; 263 tienen ambas respuestas laborales observadas.',
    'estres_entorno_laboral': 'No entra a la capa general. Se excluyen los 0 de quienes no trabajan y los 3 de las 22. Dentro de las 287 hay 10 imputadas; 263 tienen ambas respuestas laborales observadas.',
    'sobrecarga_fisica_emocional': 'No entra a la capa general. No está en dataset_fase35: se toma del conjunto limpio. 239 observadas y 12 imputadas; 99 de las 239 no trabajan, aunque la pregunta menciona el trabajo.',
}


def leer(ruta):
    return pd.read_csv(ruta, encoding='utf-8-sig')


def agrupar_adyacentes(niveles, conteos, protegidos=()):
    """Une el nivel menor bajo el umbral con su vecino menor; un nivel protegido no se une. Mantiene el orden."""
    grupos = [[n] for n in niveles]
    total = sum(conteos.get(n, 0) for n in niveles)
    tam = lambda g: sum(conteos.get(n, 0) for n in g)  # noqa: E731
    while True:
        candidatos = [i for i, g in enumerate(grupos) if 100 * tam(g) / total < UMBRAL_RARO and not set(g) & set(protegidos)]
        if not candidatos or len(grupos) <= 2:
            return grupos
        i = min(candidatos, key=lambda k: (tam(grupos[k]), k))
        vecinos = [j for j in (i - 1, i + 1) if 0 <= j < len(grupos) and not set(grupos[j]) & set(protegidos)]
        if not vecinos:
            return grupos
        j = min(vecinos, key=lambda k: (tam(grupos[k]), k))
        a, b = sorted((i, j))
        grupos[a:b + 1] = [grupos[a] + grupos[b]]


def bimodal(conteos, niveles):
    """Modo interno o extremo separado del principal por niveles menores, con al menos 5 % en ambos."""
    f = np.array([conteos.get(n, 0) for n in niveles], float)
    p = 100 * f / f.sum()
    modos = [i for i in range(len(f)) if (i == 0 or f[i] > f[i - 1]) and (i == len(f) - 1 or f[i] > f[i + 1]) and p[i] >= UMBRAL_RARO]
    return len(modos) >= 2


def main():
    APOYO.mkdir(parents=True, exist_ok=True)
    r = leer(RELEVANCIA)
    orden = {'general': 0, 'laboral': 1, 'cuidadoras': 2}
    r = r.assign(o=r['poblacion'].map(orden)).sort_values(['o', 'variable'])
    a = pd.read_csv(F35, encoding='utf-8-sig', dtype=str).set_index('participante_id')
    l = pd.read_csv(LIMPIO, encoding='utf-8-sig', dtype=str, keep_default_na=False).set_index('participante_id').reindex(a.index)
    res = leer(RESUMEN).set_index('variable')
    ori = leer(ORIGEN).set_index('variable')
    d35 = leer(DICC35).set_index('variable')
    campos, _ = catalogo.leer_modelos()
    regl, _ = catalogo.leer_condicionales()
    reglas = {k: v for x in regl.values() for k, v in x.items()}
    assert len(a) == 529 and len(r) == 33

    filas_dic, filas_mat, filas_esc = [], [], []
    for f in r.itertuples():
        v, pob = f.variable, f.poblacion
        general = pob == 'general'
        s_l = l[v].replace('', np.nan)
        s_a = a[v] if v in a.columns else None
        opciones = (campos.get(v) or {}).get('opciones') or {}
        tipo = ('cuantitativa' if v in CONTINUAS else 'binaria' if v in BINARIAS else 'nominal' if v in NOMINALES else 'ordinal')
        o = ori.loc[v]
        marca = f'{v}_imputado' in l.columns
        # Niveles analíticos
        conteos, estructura, grupos, rol_famd, mapa = {}, False, None, '', {}
        if tipo == 'ordinal':
            niveles = sorted(opciones)
            valores = pd.to_numeric(s_l, errors='coerce')
            conteos = {int(k): int(n) for k, n in valores.value_counts().items()}
            if v in ESTRUCTURAL:
                estructura = True
                conteos[0] = int(valores.isna().sum())
                niveles = [0, *niveles]
            if estructura and v != 'cantidad_personas_cuida':
                mapa = {0: 0, 1: 0, 2: 1, 3: 2, 4: 3, 5: 4}          # «Nunca» y «No lo realiza» comparten nivel (D-02)
            else:
                mapa = {n: n for n in niveles}
            if general:
                if estructura or bimodal(conteos, niveles):
                    rol_famd = 'categórica'
                    utiles = [n for n in niveles if not (estructura and v != 'cantidad_personas_cuida' and n == 1)]
                    grupos = agrupar_adyacentes(utiles, conteos, protegidos=(0,) if estructura else ())
                else:
                    rol_famd = 'cuantitativa'
        elif tipo == 'binaria':
            si, no = BINARIAS[v]
            conteos = {1: int((s_l == si).sum()), 0: int((s_l == no).sum())}
            niveles = [0, 1]
            mapa = {0: 0, 1: 1}
            rol_famd = 'categórica' if general else ''
        elif tipo == 'nominal':
            niveles = list(opciones)
            conteos = {k: int((s_l == k).sum()) for k in niveles}
            rol_famd = 'categórica'
            grupos = [['YO_MAYORIA'], ['COMPARTIDO'], ['OTRA_HOGAR'], ['COMPRO', 'OTRO']]
        else:
            rol_famd = 'cuantitativa'

        # Diccionario por nivel
        if tipo != 'cuantitativa':
            n_ref = sum(conteos.values())
            acum = 0.0
            ridit_cero = None
            for n in niveles:
                c_ = conteos.get(n, 0)
                if tipo == 'binaria':
                    sig = 'Sí' if n == 1 else 'No'
                    cod = BINARIAS[v][0 if n == 1 else 1]
                elif estructura and n == 0:
                    sig = ESTRUCTURAL[v][1]
                    cod = f'(vacío; {ESTRUCTURAL[v][0]} = NO)'
                else:
                    sig = opciones[n]
                    cod = n
                grupo = next((' + '.join(str(x) for x in g) for g in (grupos or []) if n in g), '')
                if grupos and not grupo and n == 1:
                    grupo = '0'
                no_ap = 'no aplica (fuera de su módulo)' if not general else ''
                nota = ''
                if estructura and n == 1 and v != 'cantidad_personas_cuida':
                    nota = 'Admitido por el instrumento y no observado. Si llega en la Fase 40, se une a «No lo realiza» (D-02).'
                elif c_ == 0:
                    nota = 'Admitido por el instrumento y no observado en las 529.'
                filas_dic.append({
                    'variable': v, 'capa': pob, 'nivel_instrumento': cod, 'codigo_en_dataset_fase35': n if v in a.columns else 'no incluida',
                    'significado': sig, 'n': c_, 'porcentaje': round(100 * c_ / n_ref, 2) if n_ref else 0,
                    'orden': (mapa.get(n, '') if tipo == 'ordinal' else ''),
                    'cero_valido': 'sí' if ((estructura and n == 0) or CERO_SEMANTICO.get(v) == n) else 'no',
                    'codificacion_pca': (mapa.get(n, '') if tipo in ('ordinal', 'binaria') else f'indicadora {n}') if general else 'no entra a la matriz general',
                    'grupo_famd': (grupo if rol_famd == 'categórica' and tipo != 'binaria' else ('nivel propio' if tipo == 'binaria' else ('cuantitativa' if rol_famd == 'cuantitativa' else ''))) if general else 'no entra a la matriz general',
                    'ridit_sensibilidad': (ridit_cero if estructura and n == 1 and v != 'cantidad_personas_cuida' else round((acum + c_ / 2) / n_ref, 4)) if tipo == 'ordinal' and n_ref and general else '',
                    'estado_modulo': no_ap, 'nota': nota})
                if estructura and n == 0:
                    ridit_cero = round((acum + c_ / 2) / n_ref, 4)
                acum += c_
            if v in LABORALES:
                filas_dic.append({'variable': v, 'capa': pob, 'nivel_instrumento': '(vacío; no trabaja)', 'codigo_en_dataset_fase35': 0, 'significado': 'No aplica: no trabaja',
                                  'n': int((a['trabaja_actualmente'] == '0').sum()), 'porcentaje': '', 'orden': '', 'cero_valido': 'no', 'codificacion_pca': 'no entra a la matriz general',
                                  'grupo_famd': 'no entra a la matriz general', 'ridit_sensibilidad': '', 'estado_modulo': 'excluido del módulo', 'nota': 'El 0 no es un valor de la escala.'})
                filas_dic.append({'variable': v, 'capa': pob, 'nivel_instrumento': '(vacío; situación laboral imputada)', 'codigo_en_dataset_fase35': 3, 'significado': 'Relleno de la Fase 35: no es una opinión',
                                  'n': 22, 'porcentaje': '', 'orden': '', 'cero_valido': 'no', 'codificacion_pca': 'no entra a la matriz general',
                                  'grupo_famd': 'no entra a la matriz general', 'ridit_sensibilidad': '', 'estado_modulo': 'excluido del módulo', 'nota': 'Los otros valores 3 de la columna sí son respuestas.'})
            if v == SOBRECARGA:
                filas_dic.append({'variable': v, 'capa': pob, 'nivel_instrumento': '(vacío; no cuida)', 'codigo_en_dataset_fase35': 'no incluida', 'significado': 'No aplica: no cuida',
                                  'n': int((s_l.isna()).sum()), 'porcentaje': '', 'orden': '', 'cero_valido': 'no', 'codificacion_pca': 'no entra a la matriz general',
                                  'grupo_famd': 'no entra a la matriz general', 'ridit_sensibilidad': '', 'estado_modulo': 'excluido del módulo', 'nota': 'Ausencia de respuesta, no sobrecarga cero.'})
        else:
            x = pd.to_numeric(a[v])
            ob = pd.to_numeric(s_l, errors='coerce').dropna()
            filas_dic.append({'variable': v, 'capa': pob, 'nivel_instrumento': 'numérico', 'codigo_en_dataset_fase35': 'valor', 'significado': f'{CONTINUAS[v]}; observado de {ob.min():g} a {ob.max():g}',
                              'n': len(ob), 'porcentaje': round(100 * len(ob) / 529, 2), 'orden': 'numérico', 'cero_valido': 'no', 'codificacion_pca': 'valor numérico', 'grupo_famd': 'cuantitativa',
                              'ridit_sensibilidad': '', 'estado_modulo': '', 'nota': ''})

        # Descriptivos de la representación numérica de la capa general
        if general and tipo in ('cuantitativa', 'ordinal', 'binaria'):
            if tipo == 'cuantitativa':
                x = pd.to_numeric(a[v]).astype(float)
            elif tipo == 'binaria':
                x = pd.to_numeric(a[v]).astype(float)
            else:
                x = pd.to_numeric(a[v]).astype(float).map(lambda z: mapa[int(z)]).astype(float)
            forma = x
            media, de = x.mean(), x.std(ddof=0)
            if v == 'imc':                       # la forma y los parámetros se miden sin los valores imputados
                forma = pd.to_numeric(s_l, errors='coerce').dropna()
                media, de = forma.mean(), forma.std(ddof=0)
            q1, q3 = forma.quantile([.25, .75])
            iqr = q3 - q1
            z = (x - media) / de
            filas_esc.append({'variable': v, 'tipo': tipo, 'minimo': x.min(), 'maximo': x.max(), 'media_referencia': round(media, 4), 'de_referencia': round(de, 4),
                              'n_forma': len(forma), 'asimetria': round(forma.skew(), 3), 'curtosis_exceso': round(forma.kurt(), 3), 'q1': q1, 'q3': q3, 'iqr': iqr,
                              'atipicos_tukey': int(((forma < q1 - 1.5 * iqr) | (forma > q3 + 1.5 * iqr)).sum()) if tipo == 'cuantitativa' else 'no corresponde',
                              'dominancia_pct': round(100 * x.value_counts(normalize=True).max(), 1), 'iqr_cero': bool(iqr == 0), 'z_max_abs': round(z.abs().max(), 2), 'varianza_z': round(z.var(ddof=0), 3)})

        # Matriz de decisiones
        admitidos = ('; '.join(f'{k} = {t}' for k, t in opciones.items()) if opciones else
                     ('SI / NO' if tipo == 'binaria' and BINARIAS[v][0] == 'SI' else 'True / False' if tipo == 'binaria' else str(d35.at[v, 'valores_permitidos']) if v in d35.index else ''))
        regla = reglas.get(v)
        if v in LABORALES:
            regla_txt = 'Sección Trabajo: se muestra si trabaja_actualmente = True'
        elif regla:
            regla_txt = f"Se muestra si {regla['campo']} = {regla['valor']}"
        else:
            regla_txt = 'Sin condición'
        if tipo == 'cuantitativa':
            pca = 'Valor numérico; estandarizado'
            famd = 'Cuantitativa: estandarizada'
        elif tipo == 'binaria':
            pca = 'Una columna 0/1; estandarizada'
            famd = 'Categórica de 2 niveles (inercia 1, equivale a la columna estandarizada)'
        elif tipo == 'nominal':
            pca = 'Indicadoras de 5 categorías, centradas, con varianza total del bloque = 1'
            famd = 'Categórica de 4 niveles (COMPRO + OTRO), indicadoras (I − p)/√p'
        elif not general:
            pca = 'No entra a la matriz general; caracteriza clústeres'
            famd = 'No entra a la matriz general; caracteriza clústeres'
        else:
            pca = ('Orden consecutivo: ' + ', '.join(f'{k}→{w}' for k, w in mapa.items() if k != 1) + ' (1→0 si aparece); estandarizado') if estructura and v != 'cantidad_personas_cuida' else 'Orden del instrumento; estandarizado'
            if rol_famd == 'categórica':
                famd = 'Categórica con niveles: ' + ' | '.join('+'.join(str(x) for x in g) for g in grupos)
            else:
                famd = 'Cuantitativa con el mismo orden: estandarizada'
        if tipo == 'cuantitativa':
            just = 'Cuantitativa real; StandardScaler porque la asimetría es baja y los extremos son plausibles.'
        elif tipo == 'binaria':
            just = 'Dos niveles: la columna estandarizada es equivalente al bloque de indicadoras con varianza total 1, y al tratamiento en FAMD.'
        elif tipo == 'nominal':
            just = 'Sin orden: no admite un código numérico único. La codificación deja igual distancia entre categorías distintas y limita el peso de la variable.'
        elif not general:
            just = 'Ordinal condicional: su ausencia no es un valor de escala y no puede formar clústeres generales.'
        elif rol_famd == 'categórica':
            just = 'Ordinal con quiebre cualitativo entre niveles (no realiza/realiza, o bimodalidad): un paso numérico único sería discutible. El orden se comprueba después con las coordenadas.'
        else:
            just = 'Ordinal sin quiebre estructural: el orden se conserva y la equidistancia es un supuesto de trabajo, contrastado con la sensibilidad ridit.'
        sens = {'imc': 'E-IMC', 'edad': 'S-EDAD', 'trabaja_actualmente': 'S-TRA', 'cantidad_personas_cuida': 'S-CUI', 'frecuencia_aerobico': 'S-EJE; S-ORD',
                'frecuencia_bajo_impacto': 'S-EJE; S-ORD', 'frecuencia_fuerza': 'S-EJE; S-ORD', 'quien_prepara_comidas': 'S-RARA', 'tabaco_frecuencia': 'S-ORD; S-FAMD'}.get(v, 'S-ORD; S-FAMD' if tipo == 'ordinal' and general else '')
        if v in LABORALES:
            sens = 'Módulo: 263 con ambas respuestas observadas'
        if v == SOBRECARGA:
            sens = 'Módulo: 251 cuidadoras'
        filas_mat.append({
            'variable': v, 'nombre_legible': res.at[v, 'etiqueta'], 'seccion_encuesta': res.at[v, 'seccion_encuesta'], 'capa': pob, 'n_capa': int(f.n),
            'tipo_original': tipo, 'valores_admitidos': admitidos, 'orden_natural': ('numérico' if tipo == 'cuantitativa' else 'no' if tipo in ('nominal', 'binaria') else 'sí; ascendente según el código'),
            'cero_valido': ('sí: ' + ESTRUCTURAL[v][1] if v in ESTRUCTURAL else f'sí, semántico: código {CERO_SEMANTICO[v]} = {opciones[CERO_SEMANTICO[v]]}' if v in CERO_SEMANTICO else 'no'),
            'codigo_no_aplica': ('0 en dataset_fase35; excluido del módulo' if v in LABORALES else 'vacío en el conjunto limpio; excluido del módulo' if v == SOBRECARGA else 'ninguno en la capa general'),
            'regla_condicional': regla_txt, 'observadas': int(o['observadas']), 'deducidas': int(o['deducidas']), 'imputadas': int(o['imputadas']),
            'faltantes_tras_limpieza': int(o['faltantes']), 'no_aplica': int(o['no_aplica']), 'no_aplica_por_pregunta_previa_imputada': int(o['no_aplica_por_previa_imputada']),
            'marca_imputado_en_limpio': 'sí' if marca else 'no', 'transformacion_previa': 'Código numérico según el diccionario' if tipo in ('binaria', 'ordinal') else ('Sin transformación' if tipo == 'cuantitativa' else 'Indicadoras'),
            'propuesta_pca': pca, 'rol_famd': rol_famd or 'no participa', 'propuesta_famd': famd, 'escalado': ('Sin escalado para caracterizar' if not general else 'Parámetros de las 267 observadas' if v == 'imc' else 'Específico: ver estrategia_escalado.md' if tipo == 'nominal' else 'StandardScaler'),
            'sensibilidades': sens or 'Sin sensibilidad específica', 'justificacion': just, 'nota': NOTAS.get(v, '')})

    mat = pd.DataFrame(filas_mat)
    dic = pd.DataFrame(filas_dic)
    esc = pd.DataFrame(filas_esc)
    mat.to_csv(SALIDA / 'matriz_decisiones_variables.csv', index=False, encoding='utf-8-sig')
    dic.to_csv(SALIDA / 'diccionario_codificacion_fase36.csv', index=False, encoding='utf-8-sig')
    esc.to_csv(APOYO / 'distribuciones_para_escalado.csv', index=False, encoding='utf-8-sig')
    gen = mat[mat['capa'] == 'general']
    q = {'tipos_33': mat['tipo_original'].value_counts().to_dict(), 'tipos_general': gen['tipo_original'].value_counts().to_dict(), 'rol_famd': gen['rol_famd'].value_counts().to_dict(),
         'seccion_general': gen['seccion_encuesta'].value_counts().to_dict(), 'celdas_imputadas_general': int(gen['imputadas'].sum()), 'previas_general': int(gen['no_aplica_por_pregunta_previa_imputada'].sum()),
         'marca_general': int((gen['marca_imputado_en_limpio'] == 'sí').sum()), 'marca_33': int((mat['marca_imputado_en_limpio'] == 'sí').sum())}
    props = dic[dic['variable'] == 'quien_prepara_comidas']['porcentaje'].astype(float) / 100
    q['nominal_suma_pq'] = round(float((props * (1 - props)).sum()), 4)
    q['nominal_distancia2_entre_categorias'] = round(2 / q['nominal_suma_pq'], 4)
    pares = pd.read_csv(ANALISIS / 'resultados' / 'usuaria' / 'pares_asociacion_todos.csv', encoding='utf-8-sig')
    gen_v = set(gen['variable'])
    pares = pares[pares['variable_1'].isin(gen_v) & pares['variable_2'].isin(gen_v)]
    q['pares_general'] = len(pares)
    q['pares_abs_menor_0_2'] = int((pares['valor'].abs() < 0.2).sum())
    q['pares_abs_mayor_0_4'] = int((pares['valor'].abs() > 0.4).sum())
    q['iqr_cero'] = esc.loc[esc['iqr_cero'], 'variable'].tolist()
    (APOYO / 'resumen_diseno.json').write_text(json.dumps(q, ensure_ascii=False, indent=1), encoding='utf-8')
    print(json.dumps(q, ensure_ascii=False))
    pd.set_option('display.width', 250, 'display.max_columns', 30, 'display.max_rows', 60, 'display.max_colwidth', 70)
    print(esc.to_string())
    print(gen[gen['rol_famd'] == 'categórica'][['variable', 'propuesta_famd']].to_string())
    print(dic[dic['variable'].isin(['frecuencia_fuerza', 'quien_prepara_comidas', 'tabaco_frecuencia'])][['variable', 'nivel_instrumento', 'n', 'porcentaje', 'codificacion_pca', 'grupo_famd', 'ridit_sensibilidad']].to_string())


if __name__ == '__main__':
    main()
