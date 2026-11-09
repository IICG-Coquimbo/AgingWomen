"""
Fase 34 (OB2, paso previo): análisis exploratorio de datos completo.

Uso:
    python analisis/eda_completo.py

Necesita el conjunto de datos limpio de la Fase 32 (python analisis/limpiar_dataset.py).
Escribe:
  - analisis/informe_eda.md (informe con figuras en la narrativa y anexos)
  - analisis/figuras/eda_completo/ (figuras del texto) y .../anexo/
  - analisis/resultados/{asociacion_severidad,matriz_spearman,revision_atipicos,
    coherencia,correcciones_imputacion,faltantes}.csv
  - datos/analitico/conjunto_eda.csv: participantes con MRS completo + `severidad`
    (0-3), entrada de la Fase 35.

Decisiones (usuaria, 2026-10-18): los atípicos se detectan con Tukey y se
revisan; solo se elimina lo imposible o incoherente (ya lo hace la limpieza),
los extremos clínicamente posibles se conservan (incluidos los MRS de 44).
"""
import pandas as pd

from eda import estadistica as E, graficos as G, informe_eda, revision
from eda import variables as V
from limpieza import catalogo

ANALISIS = V.RAIZ / 'analisis'
FIGURAS = ANALISIS / 'figuras' / 'eda_completo'
ANEXO = FIGURAS / 'anexo'
RESULTADOS = ANALISIS / 'resultados'
ANALITICO = V.RAIZ / 'datos' / 'analitico'

GRUPOS = (
    (V.PREDICTORES, 'predictor'), (V.PREDICTORES_TRABAJO, 'predictor (trabajo)'),
    (V.CONTROL, 'control'), (V.SUBGRUPO_PROFESIONAL, 'subgrupo profesional'),
    (V.OTRAS, 'otra'), (V.IMPACTO, 'impacto'),
)
# Roles que pueden explicar la severidad (las de impacto son consecuencias).
EXPLICATIVOS = ('predictor', 'predictor (trabajo)', 'control', 'subgrupo profesional', 'otra')


def eje_y(variable, campos):
    """Texto del eje y en la figura de dirección: unidad o escala de la pregunta."""
    opciones = campos.get(variable, {}).get('opciones')
    if variable in V.BINARIAS or (opciones and set(opciones) <= {'SI', 'NO'}):
        return 'proporción "sí"'
    if opciones and all(isinstance(k, int) for k in opciones):
        claves = sorted(opciones)
        return f'nivel medio\n{claves[0]} = {opciones[claves[0]]} … {claves[-1]} = {opciones[claves[-1]]}'
    return {'imc': 'kg/m²', 'edad': 'años', 'horas_sedentarismo': 'horas'}.get(variable, 'valor medio')


def main():
    df, diccionario = V.cargar()
    campos, _ = catalogo.leer_modelos()
    for carpeta in (FIGURAS, ANEXO, RESULTADOS, ANALITICO):
        carpeta.mkdir(parents=True, exist_ok=True)

    df['severidad'] = E.severidad_codigo(df)
    mrs = df[df['mrs_completo'] == '1']

    # 1. Faltantes (diccionario de la limpieza): reales vs. "no aplica".
    falt = diccionario[diccionario['faltantes'] > 0].copy()
    falt['no_aplica'] = len(df) - falt['filas_aplica']
    falt = falt.sort_values('pct_faltante', ascending=False)

    # 2. Atípicos y coherencia.
    atip = revision.atipicos(df)
    coher = revision.coherencia(df)
    corr = revision.correcciones(df)

    # 3. Asociación de TODAS las variables con la severidad (FDR sobre todas las pruebas).
    asoc = E.corregir_fdr(pd.concat([E.cruce_con_mrs(df, list(g), rol, resultado='severidad')
                                     for g, rol in GRUPOS]))
    spear = asoc[(asoc['prueba'] == 'Spearman') & asoc['rol'].isin(EXPLICATIVOS)]
    sig = spear[spear['p_ajustado'] < 0.05]
    modelables = [v for v in spear['variable'] if v not in V.SUBGRUPO_PROFESIONAL and v not in V.OTRAS]
    matriz = E.matriz_spearman(df, modelables)
    orden_sig = sig.reindex(sig['efecto'].abs().sort_values(ascending=False).index)['variable'].tolist()
    matriz_sig = E.matriz_spearman(df, orden_sig)
    redundantes = [(a, b, matriz.at[a, b]) for i, a in enumerate(matriz.columns[1:], 1)
                   for b in matriz.columns[i + 1:] if abs(matriz.at[a, b]) >= 0.8]

    # 4. Dirección: variables significativas (predictores y control), las 9 de mayor |rho|.
    para_direccion = [v for v in orden_sig if v not in V.SUBGRUPO_PROFESIONAL][:9]
    etiquetas_ejercicio = campos['dias_ejercicio_semana']['opciones']
    dfx = mrs.assign(ejercicio=V.numerica(mrs['dias_ejercicio_semana']).map(etiquetas_ejercicio))
    sev_ejercicio = E.severidad_por(dfx, 'ejercicio', list(etiquetas_ejercicio.values()))

    # Figuras del texto
    conteo = mrs['mrs_severidad'].value_counts().reindex(V.ORDEN_SEVERIDAD)
    G.clases_severidad(conteo, FIGURAS / 'severidad_clases.png')
    G.histograma_mrs(df, FIGURAS / 'mrs_total.png')
    G.cajas_atipicos(df, atip, revision._observados, FIGURAS / 'atipicos.png')
    G.asociacion_severidad(spear, FIGURAS / 'asociacion_severidad.png',
                           'Correlación de cada variable con la severidad')
    G.mapa_calor(matriz_sig, FIGURAS / 'matriz_significativas.png',
                 'Matriz de Spearman: severidad y variables significativas')
    G.direccion(df, [(v, eje_y(v, campos)) for v in para_direccion], FIGURAS / 'direccion.png')
    G.severidad_apilada(sev_ejercicio, 'Severidad según días de ejercicio a la semana',
                        FIGURAS / 'ejercicio_severidad.png')
    # Anexo
    G.mapa_calor(matriz, ANEXO / 'matriz_completa.png',
                 'Matriz de Spearman completa (predictores, trabajo y control)', anotar=False)
    G.histogramas({c: revision._observados(df, c) for c in revision.VARIABLES},
                  ANEXO / 'histogramas.png')
    G.faltantes(falt[~falt['variable'].isin(list(V.MRS_ITEMS))], ANEXO / 'faltantes.png')

    # Resultados tabulares
    guardar = dict(index=False, encoding='utf-8-sig', float_format='%.5f')
    asoc.assign(etiqueta=asoc['variable'].map(V.etiqueta)).to_csv(RESULTADOS / 'asociacion_severidad.csv', **guardar)
    matriz.to_csv(RESULTADOS / 'matriz_spearman.csv', encoding='utf-8-sig', float_format='%.4f')
    atip.to_csv(RESULTADOS / 'revision_atipicos.csv', **guardar)
    coher.to_csv(RESULTADOS / 'coherencia.csv', **guardar)
    corr.to_csv(RESULTADOS / 'correcciones_imputacion.csv', **guardar)
    falt.to_csv(RESULTADOS / 'faltantes.csv', **guardar)
    mrs.to_csv(ANALITICO / 'conjunto_eda.csv', index=False, encoding='utf-8-sig')

    habitos = {v: E.severidad_por(mrs.assign(nivel=V.numerica(mrs[v]).map(campos[v]['opciones'])), 'nivel',
                                  list(campos[v]['opciones'].values()))
               for v in informe_eda.HABITOS}
    imc_clase = V.numerica(mrs['imc']).groupby(mrs['mrs_severidad']).mean().reindex(V.ORDEN_SEVERIDAD)

    r = {'habitos': habitos, 'imc_clase': imc_clase, 'n': len(df), 'n_mrs': len(mrs), 'conteo': conteo, 'falt': falt, 'atip': atip,
         'coher': coher, 'corr': corr, 'asoc': asoc, 'spear': spear, 'sig': sig,
         'orden_sig': orden_sig, 'redundantes': redundantes, 'sev_ejercicio': sev_ejercicio,
         'n_matriz': len(matriz) - 1, 'diccionario': diccionario, 'para_direccion': para_direccion}
    (ANALISIS / 'informe_eda.md').write_text(informe_eda.generar(r), encoding='utf-8')
    print(f'{len(df)} participantes, {len(mrs)} con MRS completo; {len(sig)} asociaciones significativas')
    print('Informe: analisis/informe_eda.md')


if __name__ == '__main__':
    main()
