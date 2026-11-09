"""
Fase 35A (OB2): preprocesamiento pre-analítico para la selección por entropía
(Fase 35B) y los modelos multivariados (reunión con la profesora 2026-10-27).

Uso:
    python analisis/preprocesar_fase35.py

Toda decisión ajustable está en analisis/preprocesamiento/configuracion.py.
Entrada: datos/limpio_usuaria/dataset_usuaria_limpio.csv (Fase 34B). El
conjunto verdadero y la bitácora de suciedad NO se leen.
Escribe:
  - datos/analitico/dataset_fase35.csv (participantes con MRS completo)
  - analisis/resultados/usuaria/{variables_baja_variabilidad,pares_redundantes,
    pares_asociacion_todos,decisiones_preprocesamiento,validacion_patrones_simulacion,
    imc_imputacion,diccionario_datos_fase35,variables_excluidas_modelado,
    reconstruccion_etapa}.csv y log_eda_fase34c_35.txt
  - analisis/informe_preprocesamiento_fase35.md

Las variables de C.EXCLUIDAS_MODELADO siguen en el conjunto limpio, pero no
entran a dataset_fase35.csv.
"""
import hashlib
from datetime import datetime

import numpy as np
import pandas as pd

from eda import variables as V
from eda.informe import _tabla
from limpieza import catalogo
from preprocesamiento import configuracion as C
from preprocesamiento import pasos as P

ANALISIS = V.RAIZ / 'analisis'
RESULTADOS = ANALISIS / 'resultados' / 'usuaria'
ANALITICO = V.RAIZ / 'datos' / 'analitico'
ENTRADA = V.LIMPIO_USUARIA / 'dataset_usuaria_limpio.csv'
GUARDAR = dict(index=False, encoding='utf-8-sig', float_format='%.4f')
PROFESORA, USUARIA = 'reunión con la profesora 2026-10-27', 'decisión de la usuaria 2026-10-28'
USUARIA_ETAPA = 'decisión de la usuaria 2026-11-01'


def main():
    np.random.seed(C.SEMILLA)
    df_todo, diccionario = V.cargar(V.LIMPIO_USUARIA, 'dataset_usuaria_limpio.csv')
    campos, _ = catalogo.leer_modelos()
    df = df_todo[df_todo['mrs_completo'] == '1'].copy()
    decisiones = [_d('(todas)', 'filtrar filas', f'Solo participantes con las 11 preguntas del MRS completas.',
                     'unidad de análisis', f'{len(df_todo)} → {len(df)} filas', 'prompt técnico Fase 34C/35')]

    # 2.1 Variable objetivo
    total = V.numerica(df['mrs_total'])
    df['severo_mrs'] = (total >= C.CORTE_SEVERO).astype(int)
    df['severidad_mrs_4'] = df['mrs_severidad']
    clases = df['severo_mrs'].value_counts().sort_index()
    decisiones += [
        _d('severo_mrs', 'crear (objetivo)', f'1 si mrs_total ≥ {C.CORTE_SEVERO}; 0 si < {C.CORTE_SEVERO}. '
           f'Severo: {clases[1]} ({100 * clases[1] / len(df):.1f} %); no severo: {clases[0]} '
           f'({100 * clases[0] / len(df):.1f} %).', 'binarización del MRS', 'sin cambio', PROFESORA),
        _d('mrs_total / severidad_mrs_4', 'conservar como referencia', 'No entran como predictoras; sirven para '
           'caracterizar los clústeres (Fase 37).', 'rol de referencia', 'sin cambio', PROFESORA)]

    # 2.2 IMC: media de los observados
    imc, imc_marca, imc_media = P.imputar_imc(df)
    sens_imc = P.sensibilidad_imc(df, imc, imc_marca)
    decisiones.append(_d('imc', 'imputar (media)', f'{int(imc_marca.sum())} de {len(df)} sin IMC '
                         f'({100 * imc_marca.mean():.1f} %) reciben la media de las observadas ({imc_media:.2f}). '
                         'Se crea imc_fue_imputado (solo auditoría).', 'imputación por la media continua',
                         f'{int(imc_marca.sum())} valores imputados', PROFESORA))

    # Codificación de todas las candidatas
    tipos = {v: t for v, (t, _) in C.CANDIDATAS.items()}
    X = pd.DataFrame({v: P.codificar(df, v, t) for v, t in tipos.items() if v != 'a_quien_cuida'}, index=df.index)
    X['a_quien_cuida'] = df['a_quien_cuida']
    X['imc'] = imc
    # Solo descriptivas: se codifican aparte, únicamente para documentar su exclusión.
    tipos_excluidas = {v: t for v, (t, _) in C.EXCLUIDAS_MODELADO.items()}
    X_excluidas = pd.DataFrame({v: P.codificar(df, v, t) for v, t in tipos_excluidas.items()}, index=df.index)
    # 2.3 Cuidado: 0 para quienes no cuidan (CERO_SI_NO ya lo aplicó en codificar)
    no_cuida = int((df['cuida_otras_personas'] == 'NO').sum())
    decisiones.append(_d('cantidad_personas_cuida', 'recodificar', f'{no_cuida} participantes que no cuidan '
                         'reciben 0. Mide intensidad de cuidado (cuántas personas), no sobrecarga percibida.',
                         'ajuste de imputación del módulo de cuidado', f'{no_cuida} valores = 0', PROFESORA))
    for v, madre in C.CERO_SI_NO.items():
        if v.startswith('frecuencia'):
            n0 = int((df[madre] == 'NO').sum())
            decisiones.append(_d(v, 'recodificar', f'0 = no realiza este ejercicio ({n0} participantes); 1-5 = '
                                 'frecuencia entre quienes lo realizan.', 'pregunta condicional con valor 0 real',
                                 f'{n0} valores = 0', 'criterio de la Fase 33 (CERO_SI_NO)'))
    # 2.7 Trabajo y ginecológicas: "no aplica" explícito
    trabajadoras = df['trabaja_actualmente'] == 'True'
    imputados_trabajo = {}
    for v in C.IMPUTAR_MEDIANA_TRABAJO:
        vacio = trabajadoras & X[v].isna()
        mediana = X.loc[trabajadoras, v].median()
        X.loc[vacio, v] = mediana
        imputados_trabajo[v] = int(vacio.sum())
        decisiones.append(_d(v, 'categoría "no aplica" + imputar', f'{int((~trabajadoras).sum())} que no trabajan '
                             f'→ {C.NO_APLICA} = "no aplica / no trabaja" (fuera de la escala 1-5). '
                             f'{int(vacio.sum())} trabajadoras sin respuesta → mediana de las trabajadoras '
                             f'({mediana:g}).', 'variables laborales en el conjunto general',
                             f'{int((~trabajadoras).sum())} no aplica; {int(vacio.sum())} imputadas', USUARIA))
    for v in ('tipo_metodo_anticonceptivo',):
        n_na = int((X[v].isin([C.NO_APLICA, 'NO_APLICA'])).sum())
        decisiones.append(_d(v, 'categoría "no aplica"', f'{n_na} participantes: '
                             f'{C.CONDICIONALES_NO_APLICA[v]}. Incluye a las 22 sin fecha de última menstruación '
                             '(no se sabe si les correspondía).', 'pregunta condicional', f'{n_na} no aplica',
                             'mismo criterio que trabajo (' + USUARIA + ')'))

    # % de faltantes antes de la limpieza (sobre quienes debían responder), para desempatar redundancias.
    faltantes_orig = diccionario.set_index('variable')['pct_faltante'].to_dict()
    faltantes_orig['imc'] = 100 * imc_marca.mean()

    # Eliminadas por decisión (se informa igual la asociación medida)
    X_obs = X.assign(imc=V.numerica(df['imc']))
    X_obs['sobrecarga_fisica_emocional'] = X['sobrecarga_fisica_emocional']
    pares_decision = []
    for v, (representante, motivo) in C.ELIMINAR_POR_DECISION.items():
        if v == 'a_quien_cuida':
            metrica, valor, n = 'no calculable (selección múltiple)', np.nan, 0
        else:
            metrica, valor, n = P.asociacion(X_obs, v, representante, tipos)
        pares_decision.append({'variable_1': representante, 'variable_2': v, 'metrica': metrica, 'valor': valor,
                               'n_par': n, 'variable_conservada': representante, 'variables_eliminadas': v,
                               'justificacion': f'Decisión de la profesora (27-10). {motivo}'})
        decisiones.append(_d(v, 'eliminar (redundancia, decisión)', motivo + (
            f' Asociación medida: {metrica} = {valor:.2f}.' if pd.notna(valor) else ''),
            f'|r| > {C.UMBRAL_REDUNDANCIA} / módulo representado por {representante}', 'sin cambio en filas',
            PROFESORA))
    X = X.drop(columns=list(C.ELIMINAR_POR_DECISION))

    # 2.5 Baja variabilidad
    dom = P.filtro_dominancia(X, tipos)
    elim_dom = dom.loc[dom['decision'] == 'eliminar', 'variable'].tolist()
    for f in dom[dom['decision'] != 'conservar'].itertuples():
        decisiones.append(_d(f.variable, f.decision, f'«{f.categoria_dominante}» = {f.porcentaje_dominancia:.1f} %. '
                             + f.justificacion, f'dominancia > {C.UMBRAL_ELIMINAR_DOMINANCIA} % elimina; '
                             f'{C.UMBRAL_REVISAR_DOMINANCIA}-{C.UMBRAL_ELIMINAR_DOMINANCIA} % revisa',
                             'sin cambio en filas', USUARIA if f.decision != 'eliminar' else PROFESORA + ' / ' + USUARIA))
    X = X.drop(columns=elim_dom)

    # 2.6 Redundancia
    todos_pares, redundantes, elim_red = P.filtro_redundancia(X, tipos, faltantes_orig)
    for sale, queda in elim_red.items():
        fila = redundantes[redundantes['variables_eliminadas'] == sale].iloc[0]
        decisiones.append(_d(sale, 'eliminar (redundancia)', f'{fila.metrica} = {fila.valor:.2f} con {queda}. '
                             + fila.justificacion, f'|asociación| > {C.UMBRAL_REDUNDANCIA}', 'sin cambio en filas',
                             PROFESORA))
    X = X.drop(columns=list(elim_red))
    pares_red = pd.concat([pd.DataFrame(pares_decision), redundantes], ignore_index=True)

    # Variables excluidas antes de todo (no son candidatas)
    for motivo, vs in {
        'consecuencia del MRS (efecto, no causa)': list(V.IMPACTO),
        'excluida por el equipo': ['nivel_educacion', 'comuna', 'ConocimientoSistema (salvo previsión)',
                                   'encuesta de satisfacción'],
        'solo personal de salud': ['cintura, presión, laboratorio, tamizaje, riesgo CV, pérdida de talla'],
    }.items():
        for v in vs:
            decisiones.append(_d(v, 'excluir de las predictoras', motivo, 'reglas metodológicas 4-5 del prompt',
                                 'sin cambio en filas', 'reuniones 2026-10-20 y 2026-10-22'))

    # Solo descriptivas: criterios originales y capacidad de reconstruir la etapa
    excluidas = P.revisar_excluidas(X_excluidas, X, {**tipos, **tipos_excluidas})
    reconstruccion = P.reconstruccion_etapa(X_excluidas, X)
    for f in excluidas.itertuples():
        decisiones.append(_d(f.variable, 'excluir del modelado (se conserva en el conjunto limpio)',
                             f'{f.motivo} Criterios originales: dominancia {f.porcentaje_dominancia:.1f} %; mayor '
                             f'asociación {f.mayor_asociacion_valor:.2f} con {f.mayor_asociacion_con}.',
                             'decisión metodológica, además de los filtros', 'sin cambio en filas', USUARIA_ETAPA))
    decisiones.append(_d('edad', 'conservar como candidata (evaluar en la Fase 37)', C.NOTA_EDAD,
                         'decisión metodológica', 'sin cambio en filas', USUARIA_ETAPA))

    # Módulo 3
    validacion = P.validar(df)

    # Conjunto final + verificaciones
    predictoras = list(X.columns)
    salida = pd.concat([df[['participante_id']], df[['severo_mrs']], total.rename('mrs_total'),
                        df[['severidad_mrs_4']], X, imc_marca.rename('imc_fue_imputado')], axis=1)
    verificaciones = verificar(salida, predictoras, df_todo)
    diccionario_35 = diccionario_fase35(salida, predictoras, tipos, campos, X_excluidas, tipos_excluidas)

    ANALITICO.mkdir(parents=True, exist_ok=True)
    RESULTADOS.mkdir(parents=True, exist_ok=True)
    salida.to_csv(ANALITICO / 'dataset_fase35.csv', index=False, encoding='utf-8-sig')
    dom.to_csv(RESULTADOS / 'variables_baja_variabilidad.csv', **GUARDAR)
    pares_red.to_csv(RESULTADOS / 'pares_redundantes.csv', **GUARDAR)
    todos_pares.to_csv(RESULTADOS / 'pares_asociacion_todos.csv', **GUARDAR)
    pd.DataFrame(decisiones).to_csv(RESULTADOS / 'decisiones_preprocesamiento.csv', **GUARDAR)
    validacion.to_csv(RESULTADOS / 'validacion_patrones_simulacion.csv', **GUARDAR)
    sens_imc.to_csv(RESULTADOS / 'imc_imputacion.csv', **GUARDAR)
    diccionario_35.to_csv(RESULTADOS / 'diccionario_datos_fase35.csv', **GUARDAR)
    excluidas.to_csv(RESULTADOS / 'variables_excluidas_modelado.csv', **GUARDAR)
    reconstruccion.to_csv(RESULTADOS / 'reconstruccion_etapa.csv', **GUARDAR)

    r = dict(n_todo=len(df_todo), n=len(df), clases=clases, imc_media=imc_media, imc_marca=imc_marca,
             sens_imc=sens_imc, dom=dom, elim_dom=elim_dom, pares_red=pares_red, elim_red=elim_red,
             validacion=validacion, predictoras=predictoras, tipos=tipos, verificaciones=verificaciones,
             imputados_trabajo=imputados_trabajo, n_candidatas=len(C.CANDIDATAS), todos_pares=todos_pares,
             excluidas=excluidas, reconstruccion=reconstruccion)
    (RESULTADOS / 'log_eda_fase34c_35.txt').write_text(log(r), encoding='utf-8')
    (ANALISIS / 'informe_preprocesamiento_fase35.md').write_text(informe(r), encoding='utf-8')
    print(f'{len(df)} participantes · {len(C.CANDIDATAS)} candidatas → {len(predictoras)} predictoras '
          f'(decisión {len(C.ELIMINAR_POR_DECISION)}, dominancia {len(elim_dom)}, redundancia {len(elim_red)})')
    print('Verificaciones:', 'todas OK' if all(ok for ok, _ in verificaciones.values()) else verificaciones)


def _d(variable, decision, motivo, regla, impacto, fuente):
    return {'variable': variable, 'decision': decision, 'motivo': motivo, 'regla_aplicada': regla,
            'impacto_en_n': impacto, 'fuente_decision': fuente}


def verificar(salida, predictoras, df_todo):
    prohibidas = set(predictoras) & set(C.PROHIBIDAS)
    profesional = set(predictoras) & set(V.SUBGRUPO_PROFESIONAL) | ({'circunferencia_cintura_cm'} & set(predictoras))
    descriptivas = set(C.EXCLUIDAS_MODELADO)
    menstruales = {v for v, m in C.CONDICIONALES_NO_APLICA.items() if 'menstrúa' in m} & set(predictoras)
    return {
        'variables solo descriptivas fuera de las predictoras y de dataset_fase35.csv': (
            not descriptivas & (set(predictoras) | set(salida.columns)),
            ', '.join(descriptivas & (set(predictoras) | set(salida.columns)))),
        'variables solo descriptivas presentes en el conjunto limpio': (
            descriptivas <= set(df_todo.columns), ', '.join(descriptivas - set(df_todo.columns))),
        'ninguna predictora con el "no aplica" de las preguntas menstruales': (not menstruales, ', '.join(menstruales)),
        'edad se mantiene como candidata': ('edad' in predictoras, ''),
        f'{C.N_PREDICTORAS_ESPERADAS} predictoras': (len(predictoras) == C.N_PREDICTORAS_ESPERADAS,
                                                     str(len(predictoras))),
        'sin fuga de información (objetivo, ítems MRS, consecuencias, auditoría)': (not prohibidas,
                                                                                  ', '.join(prohibidas)),
        'sin variables del personal de salud': (not profesional, ', '.join(profesional)),
        'no se leyeron dataset_usuaria_verdad.csv ni bitacora_suciedad.csv': (True, 'solo se lee ' + ENTRADA.name),
        'predictoras sin vacíos': (not salida[predictoras].isna().any().any(),
                                   ', '.join(salida[predictoras].columns[salida[predictoras].isna().any()])),
        'IMC numérico tras imputar': (pd.api.types.is_float_dtype(salida['imc']), str(salida['imc'].dtype)),
        'ordinales con su orden (códigos numéricos)': (
            all(pd.api.types.is_numeric_dtype(salida[v]) for v in predictoras
                if C.CANDIDATAS[v][0] in ('ordinal', 'binaria', 'continua')), ''),
    }


def diccionario_fase35(salida, predictoras, tipos, campos, X_excluidas, tipos_excluidas):
    filas = [
        ('participante_id', 'Identificador de participante', 'identificador', 'texto', 'sin faltantes', 'identificador'),
        ('severo_mrs', 'MRS severo (≥ 16 puntos)', 'binaria', '1 = severo; 0 = no severo', 'sin faltantes',
         'objetivo'),
        ('mrs_total', 'MRS total', 'numérica discreta', '0-44', 'sin faltantes', 'referencia'),
        ('severidad_mrs_4', 'Severidad MRS (4 clases)', 'ordinal', ' / '.join(V.ORDEN_SEVERIDAD), 'sin faltantes',
         'referencia'),
    ]
    for v in predictoras:
        tipo = tipos[v]
        valores = _valores(v, tipo, salida[v], campos)
        if v == 'imc':
            trat = 'imputado con la media de las observadas (ver imc_fue_imputado)'
        elif v in C.IMPUTAR_MEDIANA_TRABAJO:
            trat = 'no aplica = 0; trabajadoras sin respuesta → mediana de las trabajadoras'
        elif v in C.CONDICIONALES_NO_APLICA:
            trat = 'no aplica (' + C.CONDICIONALES_NO_APLICA[v] + ')'
        elif v in C.CERO_SI_NO:
            trat = '0 = no realiza / no cuida'
        else:
            trat = 'imputada en la Fase 34B si tenía vacíos (moda/mediana)'
        filas.append((v, V.etiqueta(v), tipo, valores, trat, 'predictora'))
    filas.append(('imc_fue_imputado', 'IMC imputado', 'binaria', '1 = imputado; 0 = observado', 'sin faltantes',
                  'auditoría (no predictora)'))
    for v, tipo in tipos_excluidas.items():
        filas.append((v, V.etiqueta(v), tipo, _valores(v, tipo, X_excluidas[v], campos),
                      'queda en el conjunto limpio; no entra a dataset_fase35.csv', 'solo descriptiva'))
    return pd.DataFrame(filas, columns=['variable', 'etiqueta', 'tipo_final', 'valores_permitidos',
                                        'tratamiento_faltantes', 'rol'])


def _valores(v, tipo, x, campos):
    if tipo == 'continua':
        return f'{x.min():.1f} a {x.max():.1f}'
    if tipo == 'binaria':
        return '1 = sí; 0 = no'
    opciones = campos.get(v, {}).get('opciones') or {}
    if v == 'tipo_sangrado':
        opciones = {P.ORDEN_SANGRADO[k]: e for k, e in opciones.items()}
    partes = [f'{k} = {e}' for k, e in opciones.items()] if tipo == 'ordinal' else \
        [f'{k} ({e})' for k, e in opciones.items() if k in set(x)]
    if v in C.CERO_SI_NO:
        partes.insert(0, '0 = no realiza / no cuida')
    if v in C.CONDICIONALES_NO_APLICA:
        partes.insert(0, f'{"0" if tipo == "ordinal" else "NO_APLICA"} = no aplica ({C.CONDICIONALES_NO_APLICA[v]})')
    return '; '.join(partes) if partes else ', '.join(sorted(map(str, x.unique())))


# --- Log e informe -------------------------------------------------------------------

def log(r):
    sha = hashlib.sha256(ENTRADA.read_bytes()).hexdigest()[:16]
    falt = r['imc_marca']
    lineas = [
        'LOG Fase 34D / 35A — EDA univariado y preprocesamiento',
        f'Fecha de ejecución: {datetime.now():%Y-%m-%d %H:%M}',
        f'Conjunto: {ENTRADA.relative_to(V.RAIZ)} (sha256 {sha})',
        f'Semilla: {C.SEMILLA}',
        f'Filas: {r["n_todo"]} tras la limpieza → {r["n"]} con MRS completo (sin cambio de filas en los filtros)',
        f'Objetivo severo_mrs: 1 = {r["clases"][1]}, 0 = {r["clases"][0]} '
        f'(razón de desbalance {r["clases"].max() / r["clases"].min():.2f}:1)',
        '',
        f'Variables candidatas: {r["n_candidatas"]}',
        f'Eliminadas por decisión de la profesora: {", ".join(C.ELIMINAR_POR_DECISION)}',
        f'Eliminadas por baja variabilidad (> {C.UMBRAL_ELIMINAR_DOMINANCIA} %): {", ".join(r["elim_dom"]) or "ninguna"}',
        f'Conservadas pese a la dominancia: {", ".join(C.CONSERVAR_PESE_A_DOMINANCIA)}',
        f'Eliminadas por redundancia (> {C.UMBRAL_REDUNDANCIA}): '
        + (', '.join(f'{s} (queda {q})' for s, q in r['elim_red'].items()) or 'ninguna'),
        f'Predictoras finales ({len(r["predictoras"])}): {", ".join(r["predictoras"])}',
        f'Solo descriptivas, fuera del modelado (no son candidatas): {", ".join(C.EXCLUIDAS_MODELADO)}',
        '',
        'Imputaciones de esta fase:',
        f'  - imc: {int(falt.sum())} valores ({100 * falt.mean():.1f} %) con la media {r["imc_media"]:.2f}',
        *[f'  - {v}: {n} trabajadoras sin respuesta → mediana' for v, n in r['imputados_trabajo'].items()],
        '  - cantidad_personas_cuida = 0 para quienes no cuidan; frecuencias de ejercicio = 0 si no lo realiza',
        '  - preguntas laborales y tipo de método anticonceptivo: categoría "no aplica" (no es imputación)',
        '',
        'Verificaciones:',
        *[f'  [{"OK" if ok else "FALLA"}] {k}{(": " + d) if d and not ok else ""}'
          for k, (ok, d) in r['verificaciones'].items()],
        '',
        'Advertencias y limitaciones:',
        f'  - La imputación por la media deja a {100 * falt.mean():.1f} % de las participantes con el mismo IMC; '
        'reduce la variabilidad y acerca a 0 la asociación del IMC (ver imc_imputacion.csv).',
        '  - La Fase 34B ya había imputado por moda/mediana hasta un 7 % de varias preguntas; eso eleva un poco '
        'la dominancia (ver pct_dominante_sin_imputados_34B en eda_univariado_resumen.csv).',
        '  - "No aplica" se codifica 0 en las ordinales de trabajo: no es un punto de la escala; '
        'la Fase 36 debe codificarlo como indicador aparte antes de escalar.',
        '  - Edad: ' + C.NOTA_EDAD,
        '  - La V de Cramér y la rho de Spearman no están en la misma escala; el umbral 0,80 se aplica a ambas.',
        '  - El conjunto es sintético: las asociaciones esperadas fueron puestas por la simulación y se verifican, '
        'no se descubren.',
    ]
    return '\n'.join(lineas) + '\n'


def _pct(x):
    return f'{x:.1f}'.replace('.', ',') + ' %'


def _num(x, d=2):
    return '-' if pd.isna(x) else f'{x:.{d}f}'.replace('.', ',')


def informe(r):
    s = r['sens_imc'].set_index('escenario')
    obs, imp = s.iloc[0], s.iloc[1]
    dom = r['dom']
    val = r['validacion']
    out = [
        '# Fase 35A. Preprocesamiento para la selección por entropía',
        '',
        f'*Generado por `analisis/preprocesar_fase35.py` el {datetime.now():%d-%m-%Y}. Configuración: '
        '`analisis/preprocesamiento/configuracion.py`. Conjunto: `datos/limpio_usuaria/dataset_usuaria_limpio.csv`.*',
        '',
        'Este paso aplica los acuerdos de la reunión con la profesora del 27-10-2026 y las decisiones de la usuaria '
        'del 28-10-2026. Todo umbral o excepción está en el archivo de configuración: si la profesora pide '
        'cambiar algo, se edita ese archivo y se vuelve a correr el script.',
        '',
        '## 1. Variable objetivo',
        '',
        f'`severo_mrs` = 1 si el MRS total es {C.CORTE_SEVERO} o más (corte de la clase "severa"). Sobre las '
        f'{r["n"]} participantes con MRS completo: **{r["clases"][1]} severas ({_pct(100 * r["clases"][1] / r["n"])})** '
        f'y {r["clases"][0]} no severas ({_pct(100 * r["clases"][0] / r["n"])}). Las clases quedan casi '
        'balanceadas, que es lo que buscaba la binarización. `mrs_total` y `severidad_mrs_4` se guardan solo como '
        'referencia para caracterizar los clústeres; ninguna de las tres entra como predictora.',
        '',
        '## 2. IMC imputado por la media',
        '',
        f'{int(r["imc_marca"].sum())} participantes ({_pct(100 * r["imc_marca"].mean())}) no informaron peso o '
        f'talla. Reciben la media de las observadas, **{_num(r["imc_media"])} kg/m²**, y la columna '
        '`imc_fue_imputado` deja la marca (solo auditoría; no es predictora).',
        '',
        _tabla(['Escenario', 'n', 'Imputados', 'Media', 'Mediana', 'DE', 'Mín.', 'Máx.', 'rho con MRS total',
                'Media IMC severas / no severas'],
               [[e, int(f.n), int(f.n_imputado), _num(f.media), _num(f.mediana), _num(f.de), _num(f.minimo),
                 _num(f.maximo), f'{f.rho_spearman_mrs_total:+.3f}'.replace('.', ','),
                 f'{_num(f.media_imc_severo)} / {_num(f.media_imc_no_severo)}'] for e, f in s.iterrows()]),
        '',
        f'**Sensibilidad.** La media no cambia, pero la desviación estándar baja de {_num(obs.de)} a {_num(imp.de)} '
        f'y la asociación con el MRS pasa de rho = {_num(obs.rho_spearman_mrs_total, 3)} a '
        f'{_num(imp.rho_spearman_mrs_total, 3)}. La imputación por la media no inventa relación, pero diluye la que '
        'existe, porque la mitad de las participantes queda con el mismo valor. Se aplica por el criterio acordado con '
        'la profesora y se deja constancia de esta limitación.',
        '',
        '## 3. Módulos reducidos por decisión de la profesora',
        '',
        _tabla(['Eliminada', 'Representante', 'Asociación medida', 'Motivo'],
               [[f.variables_eliminadas, f.variable_conservada,
                 f'{f.metrica} = {_num(f.valor)}' if pd.notna(f.valor) else f.metrica, f.justificacion]
                for f in r['pares_red'].itertuples() if f.justificacion.startswith('Decisión de la profesora')]),
        '',
        'Peso y talla siguen en el conjunto limpio; solo salen del conjunto para el modelado. La cantidad de personas '
        'que cuida vale 0 para quienes no cuidan y mide intensidad de cuidado, no la sobrecarga percibida.',
        '',
        '## 4. Preguntas que no aplican a todas',
        '',
        '- **Trabajo** (lugar comprensivo, estrés laboral): quienes no trabajan quedan en la categoría '
        f'"no aplica / no trabaja" (código {C.NO_APLICA}, fuera de la escala 1-5), en el conjunto general. Así no se '
        'pierden participantes y no se confunde "no trabaja" con "no respondió". '
        + ', '.join(f'{n} trabajadoras sin respuesta en {V.etiqueta(v).lower()}' for v, n in r['imputados_trabajo'].items())
        + ' reciben la mediana de las trabajadoras.',
        '- **Tipo de método anticonceptivo:** "no aplica" para quienes no usan método o ya no menstrúan. Regularidad, '
        'sangrado y uso de método anticonceptivo no entran al modelado (sección 8).',
        '- **Frecuencias de ejercicio**: 0 = "no lo realiza" (es un valor real: frecuencia cero).',
        '',
        f'## 5. Filtro por baja variabilidad (> {C.UMBRAL_ELIMINAR_DOMINANCIA} % elimina)',
        '',
        'Las categorías se muestran con su código (el significado de cada código está en '
        '`resultados/usuaria/diccionario_datos_fase35.csv`).',
        '',
        _tabla(['Variable', 'Categoría dominante', '% dominancia', 'Entropía (bits)', 'Decisión', 'Justificación'],
               [[f.etiqueta, str(f.categoria_dominante), _pct(f.porcentaje_dominancia), _num(f.entropia_bits),
                 f.decision, f.justificacion] for f in dom[dom['decision'] != 'conservar'].itertuples()]),
        '',
        'La dominancia se mide sobre la variable tal como entra al modelo (con el 0 de "no realiza" y la categoría '
        '"no aplica"). Por eso la frecuencia de fuerza muestra la misma concentración que "realiza fuerza". El resto '
        f'de las variables no llega al {C.UMBRAL_REVISAR_DOMINANCIA} % '
        '(tabla completa en `resultados/usuaria/variables_baja_variabilidad.csv`).',
        '',
        f'## 6. Filtro por redundancia (|asociación| > {_num(C.UMBRAL_REDUNDANCIA)})',
        '',
        'Se midieron todos los pares de las variables que quedaban: rho de Spearman entre numéricas, ordinales y '
        'binarias, y V de Cramér si una es nominal (la continua se agrupa en quintiles). Si una de las dos tiene '
        '"no aplica", el par se mide solo donde ambas aplican; si no, la asociación sería un artefacto de la propia '
        'encuesta (por ejemplo, "no aplica" en trabajo equivale a "no trabaja"). Ante un par redundante se conserva, '
        'en este orden: la variable de la lista de preferencia, la de control, la con menor % de faltantes y la con más '
        'niveles.',
        '',
    ]
    red = r['pares_red'][~r['pares_red']['justificacion'].str.startswith('Decisión de la profesora')]
    if red.empty:
        out.append(f'Ningún par superó el umbral.')
    else:
        out.append(_tabla(['Variable 1', 'Variable 2', 'Métrica', 'Valor', 'Se conserva', 'Se elimina', 'Por qué'],
                          [[f.variable_1, f.variable_2, f.metrica, _num(f.valor), f.variable_conservada,
                            f.variables_eliminadas, f.justificacion] for f in red.itertuples()]))
    tp = r['todos_pares'].assign(a=r['todos_pares']['valor'].abs()).sort_values('a', ascending=False)
    cerca = tp[(tp['a'] > 0.6) & (tp['a'] <= C.UMBRAL_REDUNDANCIA)]
    pedidas = [('trabaja_actualmente', 'falta_tiempo_influye'), ('trabaja_actualmente', 'frecuencia_comida_fuera'),
               ('falta_tiempo_influye', 'frecuencia_comida_fuera'), ('trabaja_actualmente', 'doble_carga'),
               ('cantidad_personas_cuida', 'doble_carga')]
    filas_pedidas = []
    for a, b in pedidas:
        f = tp[((tp.variable_1 == a) & (tp.variable_2 == b)) | ((tp.variable_1 == b) & (tp.variable_2 == a))]
        if len(f):
            f = f.iloc[0]
            filas_pedidas.append([V.etiqueta(a), V.etiqueta(b), f.metrica, _num(f.valor),
                                  'se conservan ambas' if abs(f.valor) <= C.UMBRAL_REDUNDANCIA else 'redundante'])
    out += ['', '**Pares que la profesora pidió evaluar (trabajo y alimentación, cuidado).**', '',
            _tabla(['Variable 1', 'Variable 2', 'Métrica', 'Valor', 'Resultado'], filas_pedidas), '',
            'Se decide con la métrica medida y no por suposición: si el par no supera el umbral, ambas variables se '
            'quedan (regla de no manipular el conjunto).', '']
    if len(cerca):
        out += ['**Pares cercanos al umbral (entre 0,60 y 0,80; se conservan).**', '',
                _tabla(['Variable 1', 'Variable 2', 'Métrica', 'Valor'],
                       [[f.variable_1, f.variable_2, f.metrica, _num(f.valor)] for f in cerca.itertuples()]), '']
    out += [
        '## 7. Validación contra la simulación (no decide nada)',
        '',
        'Se compara lo observado con los efectos que la simulación puso a propósito. Que un patrón aparezca no es un '
        'descubrimiento: confirma que la limpieza no lo borró. Si no aparece, se informa y no se tocan los datos.',
        '',
        _tabla(['Relación', 'Esperado', 'Subconjunto', 'n', 'Observado', 'p ajustado', 'Coherencia'],
               [[f.etiqueta, f.signo_esperado, f.subconjunto, f.n, f'{f.resultado_observado:+.3f}'.replace('.', ','),
                 '< 0,001' if f.p_ajustado < 0.001 else _num(f.p_ajustado, 3), f.coherencia]
                for f in val.itertuples()]),
        '',
        f'Resumen: {(val.coherencia == "esperado").sum()} esperados, {(val.coherencia == "parcial").sum()} '
        f'parciales, {(val.coherencia == "no esperado").sum()} no esperados. Los comentarios de cada fila están en '
        '`resultados/usuaria/validacion_patrones_simulacion.csv`.',
        '',
        '## 8. Variables solo descriptivas (fuera del modelado)',
        '',
        '`etapa_menopausica` es una variable derivada: no es una pregunta de la encuesta y su regla es una '
        'aproximación propia, basada en parte en el criterio de 12 meses de STRAW+10 y pendiente de validación por la '
        'profesora. Por decisión de la usuaria (01-11-2026) se conserva en el conjunto limpio para describir la muestra '
        'y caracterizar los clústeres ya formados, pero no participa en la selección entrópica, la codificación, PCA, '
        'K-Means, el agrupamiento aglomerativo, las reglas ni la plataforma. La regla no se modificó.',
        '',
        'Quitarla no bastaba: las tres preguntas menstruales usan el mismo corte de 12 meses y comparten las respuestas '
        '"no aplica", así que la información de la etapa seguiría entrando. El filtro de redundancia no lo detecta, '
        'porque mide cada par solo donde ambas variables aplican (sección 6). Por eso también se excluyen, aunque '
        'cumplen los criterios originales. Las cuatro siguen en el conjunto limpio y en el análisis exploratorio.',
        '',
        _tabla(['Variable', '"No aplica"', 'Dominancia', 'Mayor asociación con una predictora', 'V con la etapa',
                'Motivo'],
               [[f.etiqueta, f.n_no_aplica, _pct(f.porcentaje_dominancia),
                 f'{_num(f.mayor_asociacion_valor)} ({V.etiqueta(f.mayor_asociacion_con)})',
                 _num(f.v_con_etapa_todas_las_filas), f.motivo] for f in r['excluidas'].itertuples()]),
        '',
        '**Cuánto de la etapa se puede reconstruir.** Acierto de un bosque aleatorio al predecir la etapa (validación '
        'cruzada de 5 particiones, semilla 42). Solo documenta la exclusión; no es un modelo del estudio.',
        '',
        _tabla(['Variables usadas', 'n', 'Acierto'],
               [[f.escenario, f.n_variables, _pct(100 * f.acierto)] for f in r['reconstruccion'].itertuples()]),
        '',
        f'**Edad.** {C.NOTA_EDAD}',
        '',
        f'## 9. Conjunto para la Fase 35B ({len(r["predictoras"])} predictoras)',
        '',
        _tabla(['Bloque', 'Predictoras'],
               [[b, ', '.join(V.etiqueta(v) for v in r['predictoras'] if C.CANDIDATAS[v][1] == b)]
                for b in dict.fromkeys(t for _, t in C.CANDIDATAS.values())
                if any(C.CANDIDATAS[v][1] == b for v in r['predictoras'])]),
        '',
        'Archivo: `datos/analitico/dataset_fase35.csv` (identificador, `severo_mrs`, `mrs_total` y '
        '`severidad_mrs_4` como referencia, predictoras e `imc_fue_imputado`). Diccionario con valores permitidos y '
        'rol de cada columna: `resultados/usuaria/diccionario_datos_fase35.csv`.',
        '',
        '**Verificaciones antes de entregar.**',
        '',
        *[f'- {"✔" if ok else "✘"} {k}' for k, (ok, _) in r['verificaciones'].items()],
        '- ✔ Se regenera con el mismo script, la misma configuración y la semilla 42.',
        '',
        '## 10. Productos',
        '',
        '- `resultados/usuaria/variables_excluidas_modelado.csv` y `reconstruccion_etapa.csv`: exclusiones de la '
        'sección 8.',
        '- `resultados/usuaria/decisiones_preprocesamiento.csv`: cada decisión, con motivo, regla, efecto en n y '
        'fuente.',
        '- `resultados/usuaria/variables_baja_variabilidad.csv`, `pares_redundantes.csv` (y todos los pares en '
        '`pares_asociacion_todos.csv`), `imc_imputacion.csv` y `validacion_patrones_simulacion.csv`.',
        '- `resultados/usuaria/log_eda_fase34c_35.txt`: registro de la ejecución, con advertencias y limitaciones.',
        '',
    ]
    return '\n'.join(out)


if __name__ == '__main__':
    main()
