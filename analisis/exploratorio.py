"""
Fase 33 (OB2, Actividad 1): análisis exploratorio + Random Forest.

Uso:
    python analisis/exploratorio.py

Necesita el dataset limpio de la Fase 32 (python analisis/limpiar_dataset.py).
Escribe analisis/informe_exploratorio.md, analisis/resultados/ y
analisis/figuras/eda/. Con la misma entrada produce los mismos resultados
(semilla fija en eda/bosque.py).
"""
import pandas as pd

from eda import bosque, estadistica as E, graficos as G, informe
from eda import variables as V

ANALISIS = V.RAIZ / 'analisis'
FIGURAS = ANALISIS / 'figuras' / 'eda'
RESULTADOS = ANALISIS / 'resultados'


def modelo(datos, variables, significativas):
    """
    Ajusta los Random Forest de regresión y clasificación sobre `variables`.

    Selección final (decisión de la usuaria, 2026-10-11): una variable entra si
    el bosque de regresión la selecciona (útil en ≥ 4 de 5 particiones) O si
    tiene relación significativa con el MRS en el análisis bivariado
    (`significativas`, nombres base; una categórica arrastra todas sus columnas).
    Después se quitan las redundantes.
    """
    X = V.codificar(datos, variables)
    faltan = X.columns[X.isna().any()].tolist()
    if faltan:
        raise ValueError(f'Hay vacíos en las entradas del modelo: {faltan}')
    y = V.numerica(datos['mrs_total'])
    severa = (y >= V.CORTE_SEVERA).astype(int)
    met_reg, imp_reg = bosque.evaluar(X, y, 'regresion')
    met_cla, imp_cla = bosque.evaluar(X, severa, 'clasificacion')

    por_bosque = set(imp_reg.loc[imp_reg['seleccionada'], 'variable'])
    por_cruce = {c for c in X.columns if c.split('=')[0] in significativas}
    motivo = {c: ' + '.join(m for m, s in (('Random Forest', por_bosque), ('bivariado', por_cruce)) if c in s)
              for c in por_bosque | por_cruce}
    elegidas = [v for v in imp_reg['variable'] if v in motivo]       # orden de importancia
    importancia = dict(zip(imp_reg['variable'], imp_reg['perm_media']))
    pares, descartadas = E.redundantes(X[elegidas], importancia) if elegidas else (pd.DataFrame(), set())
    return {'n': len(datos), 'X': X, 'prop_severa': 100 * severa.mean(),
            'met_reg': met_reg, 'imp_reg': imp_reg, 'met_cla': met_cla, 'imp_cla': imp_cla,
            'redundantes': pares, 'final': [v for v in elegidas if v not in descartadas],
            'motivo': motivo}


def rol_de(variable):
    base = variable.split('=')[0]
    for rol, grupo in (('predictor', V.PREDICTORES), ('predictor (trabajo)', V.PREDICTORES_TRABAJO),
                       ('control', V.CONTROL)):
        if base in grupo:
            return rol
    return ''


def main():
    df, _ = V.cargar()
    FIGURAS.mkdir(parents=True, exist_ok=True)
    RESULTADOS.mkdir(parents=True, exist_ok=True)

    mrs = df[df['mrs_completo'] == '1']
    profesional = df[df['origen_registro'] != 'AUTO']
    trabajan = mrs[mrs['trabaja_actualmente'] == 'True']
    # Quien dejó "¿trabaja?" en blanco recibió "sí" por imputación (Fase 32), pero su
    # sección Trabajo quedó como "no aplica": sin esas respuestas no entra a este modelo.
    sin_trabajo = trabajan[list(V.PREDICTORES_TRABAJO)].isna().any(axis=1)
    trabajan = trabajan[~sin_trabajo]

    cruces = pd.concat([
        E.cruce_con_mrs(df, list(V.PREDICTORES) + list(V.PREDICTORES_TRABAJO), 'predictor'),
        E.cruce_con_mrs(df, list(V.CONTROL), 'control'),
        E.cruce_con_mrs(df, list(V.IMPACTO), 'impacto'),
        E.cruce_con_mrs(df, list(V.OTRAS), 'otra'),
    ])
    r = {
        'n': len(df), 'n_mrs': len(mrs), 'n_profesional': len(profesional), 'n_trabajan': len(trabajan),
        'trabajan_sin_seccion': sorted(mrs.loc[mrs.index.isin(sin_trabajo[sin_trabajo].index),
                                               'participante_id']),
        'continuas': E.descriptivos_continuos(df, V.CONTINUAS),
        'continuas_prof': E.descriptivos_continuos(profesional, V.CONTINUAS_PROFESIONAL),
        'perfil': E.perfil_mrs(df),
        'sev_etapa': E.severidad_por(df, 'etapa_menopausica', V.ORDEN_ETAPA),
        'sev_edad': E.severidad_por(df, 'tramo_edad', sorted(df['tramo_edad'].dropna().unique(),
                                                            key=lambda t: (t != '<40', t))),
        'sev_trabaja': E.severidad_por(df, 'trabaja_actualmente'),
        'cruces': E.corregir_fdr(cruces),
        'cruces_prof': E.corregir_fdr(E.cruce_con_mrs(profesional, list(V.SUBGRUPO_PROFESIONAL),
                                                      'subgrupo profesional')),
        'atipicos': E.atipicos(df, V.CONTINUAS),
    }
    c = r['cruces']
    significativas = set(c.loc[(c['p_ajustado'] < 0.05) & c['rol'].isin(['predictor', 'control']),
                               'variable'])
    print('Ajustando Random Forest (general)...')
    general = list(V.PREDICTORES) + list(V.CONTROL)
    r['modelos'] = {'general': modelo(mrs, general, significativas)}
    print('Ajustando Random Forest (trabajadoras)...')
    de_trabajo = list(V.PREDICTORES) + list(V.PREDICTORES_TRABAJO) + \
        [v for v in V.CONTROL if v != 'trabaja_actualmente']
    r['modelos']['trabajadoras'] = modelo(trabajan, de_trabajo, significativas)

    # Figuras
    G.histograma_mrs(df, FIGURAS / 'mrs_total.png')
    G.prevalencia_sintomas(r['perfil'], FIGURAS / 'sintomas.png')
    G.severidad_apilada(r['sev_etapa'], 'Severidad del MRS según etapa menopáusica',
                        FIGURAS / 'severidad_etapa.png')
    G.correlaciones(r['cruces'], FIGURAS / 'correlaciones.png')
    for clave, titulo in (('general', 'Importancia de variables — modelo general'),
                          ('trabajadoras', 'Importancia de variables — trabajadoras')):
        G.importancia(r['modelos'][clave]['imp_reg'], titulo, 'Caída del R² al permutar',
                      FIGURAS / f'importancia_{clave}.png', bosque.MINIMO_PARTICIONES)

    # Resultados tabulares para las fases siguientes
    filas = []
    for clave, m in r['modelos'].items():
        for tarea, imp in (('regresion', m['imp_reg']), ('clasificacion', m['imp_cla'])):
            t = imp.assign(modelo=clave, tarea=tarea, etiqueta=imp['variable'].map(V.etiqueta),
                           rol=imp['variable'].map(rol_de))
            if tarea == 'regresion':
                t['seleccion_final'] = t['variable'].isin(m['final'])
                t['motivo_seleccion'] = t['variable'].map(m['motivo']).fillna('')
            filas.append(t)
    columnas = ['modelo', 'tarea', 'variable', 'etiqueta', 'rol', 'perm_media', 'perm_de',
                'perm_positiva_en', 'impureza_media', 'seleccionada', 'seleccion_final',
                'motivo_seleccion']
    pd.concat(filas)[columnas].to_csv(RESULTADOS / 'importancia_variables.csv', index=False,
                                      encoding='utf-8-sig', float_format='%.5f')
    r['cruces'].to_csv(RESULTADOS / 'cruces_mrs.csv', index=False, encoding='utf-8-sig',
                       float_format='%.5f')
    frec = E.frecuencias(df, [v for v in {**V.PREDICTORES, **V.PREDICTORES_TRABAJO, **V.CONTROL,
                                          **V.IMPACTO, **V.OTRAS} if v not in V.CONTINUAS
                              and v not in ('imc', 'horas_sedentarismo')] + ['mrs_severidad'])
    (RESULTADOS / 'frecuencias.md').write_text(informe.frecuencias_md(frec), encoding='utf-8')
    (ANALISIS / 'informe_exploratorio.md').write_text(informe.generar(r), encoding='utf-8')
    print('Informe: analisis/informe_exploratorio.md')


if __name__ == '__main__':
    main()
