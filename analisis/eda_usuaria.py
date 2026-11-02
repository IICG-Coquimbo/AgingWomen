"""
Fase 34C (OB2): análisis exploratorio del conjunto sintético de la usuaria común.

Uso:
    python analisis/eda_usuaria.py

Necesita el conjunto limpio de la Fase 34B (python analisis/limpiar_dataset.py).
Escribe:
  - analisis/informe_eda_usuaria.md
  - analisis/figuras/eda_usuaria/ (frecuencias/: una figura por variable)
  - analisis/resultados/usuaria/{frecuencias,diferencias_trabajo,atipicos,faltantes,
    asociacion_severidad,consecuencias,matriz_spearman,perfil_sintomas,
    severidad_por_respuesta}.csv
  - datos/analitico/conjunto_eda_usuaria.csv: participantes con MRS completo +
    `severidad` (0-3), entrada de la Fase 35.

El EDA de la profesora (eda_completo.py, informe_eda.md) queda como anexo y no
se toca. Plan aprobado por la usuaria el 2026-10-24: todas las variables se
describen comparando a quienes trabajan y quienes no; la previsión entra como
control; las consecuencias de los síntomas se analizan aparte (son efecto del
MRS, no causa); no se entrena Random Forest.
"""
import re

import numpy as np
import pandas as pd
from scipy import stats

from eda import estadistica as E, graficos as G, informe_usuaria, revision
from eda import variables as V
from limpieza import catalogo

ANALISIS = V.RAIZ / 'analisis'
FIGURAS = ANALISIS / 'figuras' / 'eda_usuaria'
RESULTADOS = ANALISIS / 'resultados' / 'usuaria'
ANALITICO = V.RAIZ / 'datos' / 'analitico'
GRUPO = 'grupo_trabajo'
NOMBRES_GRUPO = ['Trabaja', 'No trabaja']

# Bloques de la sección 3 (una figura por variable; ajuste aprobado 2026-10-24/26).
BLOQUES = {
    'control': ('Variables de control', ['edad', 'etapa_menopausica', 'imc_categoria', 'imc', 'peso_kg',
                                         'talla_actual_cm', 'usa_terapia_hormonal', 'prevision',
                                         'usa_medicamentos_diabetes']),
    'actividad': ('Actividad física', ['dias_ejercicio_semana', 'realiza_aerobico', 'frecuencia_aerobico',
                                       'realiza_bajo_impacto', 'frecuencia_bajo_impacto', 'realiza_fuerza',
                                       'frecuencia_fuerza', 'horas_sedentarismo']),
    'alimentacion_contexto': ('Alimentación (contexto)', ['quien_prepara_comidas', 'frecuencia_comida_fuera',
                                                         'falta_tiempo_influye']),
    'alimentacion_consumo': ('Alimentación (consumo)', [
        'vasos_agua_dia', 'platos_verduras_dia', 'frutas_dia', 'panes_dia', 'lacteos_dia',
        'jugos_gaseosas_dia', 'bebidas_energeticas_dia', 'pescado_semana', 'legumbres_semana',
        'carnes_semana', 'golosinas_semana']),
    'sustancias': ('Sustancias', ['tabaco_frecuencia', 'alcohol_frecuencia', 'marihuana_frecuencia']),
    'cuidado': ('Cuidado de otras personas', ['cuida_otras_personas', 'cantidad_personas_cuida',
                                              'a_quien_cuida', 'sobrecarga_fisica_emocional']),
    'trabajo': ('Trabajo (solo quienes trabajan)', list(V.PREDICTORES_TRABAJO)),
    'ginecologicas': ('Salud ginecológica', list(V.GINECOLOGICAS)),
    'salud': ('Medicamentos y digestión', list(V.SALUD_USUARIA)),
    'otras': ('Otras características', ['genero', *V.OTRAS_USUARIA]),
    'sintomas': ('Síntomas del MRS', list(V.MRS_ITEMS)),
    'consecuencias': ('Consecuencias de los síntomas', list(V.IMPACTO)),
}
# Solo existen para quienes trabajan: se describen en un grupo.
SOLO_TRABAJO = [*V.PREDICTORES_TRABAJO, 'rendimiento_afectado', 'bienestar_trabajo_afectado',
                'frecuencia_ausencias']
# Para la variable de control "edad" se muestra el tramo; las horas sentada se agrupan.
TRAMOS_HORAS = [(0, 3, '0-3 h'), (4, 6, '4-6 h'), (7, 9, '7-9 h'), (10, 24, '10 h o más')]
# Continuas autodeclaradas: histograma en intervalos de (ancho, unidad).
INTERVALOS = {'imc': (5, ' kg/m²'), 'peso_kg': (10, ' kg'), 'talla_actual_cm': (5, ' cm')}
EMOJI = re.compile(r'[\U0001F000-\U0001FAFF]\s*')
ABREVIAR = {'No se identifica con ningún pueblo originario/afro': 'Ninguno',
            'Afrodescendiente chileno/latinoamericano': 'Afrodescendiente',
            'Yo preparo algunas y otras personas otras': 'Compartido',
            'Otra persona de mi hogar prepara la mayoría': 'Otra persona del hogar',
            'Generalmente compro comida preparada': 'Compra comida preparada',
            'FF.AA. y de Orden (Capredena, Dipreca)': 'FF.AA. y de Orden'}
SIN_ACTIVIDAD = {'realiza_aerobico': 'No lo realiza', 'realiza_bajo_impacto': 'No lo realiza',
                 'realiza_fuerza': 'No lo realiza', 'cuida_otras_personas': 'No cuida'}
GRUPOS_ASOCIACION = ((V.PREDICTORES, 'predictor'), (V.PREDICTORES_TRABAJO, 'predictor (trabajo)'),
                     (V.CONTROL_USUARIA, 'control'), (V.OTRAS_USUARIA, 'otra'))
# Ajuste 34C: familia FDR aparte, para que agregarlas no cambie la corrección de las principales.
GRUPOS_SECUNDARIOS = ((V.GINECOLOGICAS, 'ginecológica'), (V.SALUD_USUARIA, 'salud'))
CONTROL_GRUPO = [v for v in V.CONTROL_USUARIA if v not in ('imc', 'trabaja_actualmente')]


def respuestas(df, v, campos):
    """Respuesta legible (para frecuencias), en el orden de la pregunta."""
    s = df[v]
    if v == 'edad':
        return df['tramo_edad'], sorted(df['tramo_edad'].dropna().unique(), key=lambda t: (t != '<40', t))
    if v == 'horas_sedentarismo':
        x = V.numerica(s)
        r = pd.Series(np.nan, index=s.index, dtype=object)
        for a, b, nombre in TRAMOS_HORAS:
            r[x.between(a, b)] = nombre
        return r, [n for *_, n in TRAMOS_HORAS]
    if v in INTERVALOS:
        ancho, unidad = INTERVALOS[v]
        inicio = np.floor(V.numerica(s) / ancho) * ancho
        nombres = {i: f'{i:g}-{i + ancho:g}{unidad}' for i in sorted(inicio.dropna().unique())}
        return inicio.map(nombres), list(nombres.values())
    if v in ('trabaja_actualmente', 'doble_carga'):
        s = s.map({'True': 'Sí', 'False': 'No', '1': 'Sí', '0': 'No'})
        return s, ['Sí', 'No']
    if v == 'imc_categoria':
        return s, V.ORDEN_IMC
    if v == 'etapa_menopausica':
        return s, [e for e in dict.fromkeys(V.ORDEN_ETAPA + sorted(s.dropna().unique())) if e in set(s.dropna())]
    opciones = campos.get(v, {}).get('opciones') or {}
    etiquetas = {str(k): EMOJI.sub('', ABREVIAR.get(o, o.split(' o de origen')[0])) for k, o in opciones.items()}
    orden = list(etiquetas.values())
    if v in V.CERO_SI_NO:
        madre = V.CERO_SI_NO[v]
        s = s.where(df[madre] != 'NO', '0')
        etiquetas['0'] = SIN_ACTIVIDAD[madre]
        orden = [SIN_ACTIVIDAD[madre]] + orden
    s = s.map(lambda x: etiquetas.get(x, x) if pd.notna(x) else x)
    if not orden:
        orden = s.value_counts().index.tolist()
    return s, [o for o in orden if o in set(s.dropna())]


def por_grupo(df, v, campos, grupos=NOMBRES_GRUPO):
    """
    % de cada respuesta dentro de cada grupo (columnas), conteos y participantes
    con dato en cada grupo. En las de selección múltiple, % de quienes
    respondieron que marcó cada opción (puede sumar más de 100).
    """
    if v in V.MULTISELECCION:
        marcadas = df[v].dropna().str.split(', ').explode()
        t = pd.crosstab(marcadas.values, df.loc[marcadas.index, GRUPO].values).reindex(columns=grupos).fillna(0)
        t = t.loc[t.sum(axis=1).sort_values(ascending=False).index]
        base = df.loc[df[v].notna(), GRUPO].value_counts().reindex(grupos).fillna(0)
        return 100 * t / base, t, base
    s, orden = respuestas(df, v, campos)
    t = pd.crosstab(s, df[GRUPO]).reindex(index=orden, columns=grupos).fillna(0)
    return 100 * t / t.sum(), t, t.sum()


def nota_figura(base, v, dif):
    """Texto bajo el título: participantes con dato en cada grupo y prueba de diferencia (si la hay)."""
    partes = [f'n {g.lower()} = {int(n)}' for g, n in base.items()]
    if v in V.MULTISELECCION:
        partes.append('selección múltiple: % de quienes respondieron')
    elif dif is not None and v in dif.index and pd.notna(dif.at[v, 'p_ajustado']):
        t = dif.loc[v]
        p = '< 0.001' if t.p_ajustado < 0.001 else f'= {t.p_ajustado:.3f}'
        partes.append(f'trabaja vs. no trabaja, {t.prueba}: {t.medida} = {t.efecto:.2f}, p ajustado {p}')
    return ' · '.join(partes)


def prueba(df, v):
    """Columna con la que se prueba la diferencia: código crudo, 0 si la madre es "No"."""
    s = df[v]
    if v in V.CERO_SI_NO:
        s = s.where(df[V.CERO_SI_NO[v]] != 'NO', '0')
    return s


def atipicos_usuaria(df):
    """Tukey (1,5 × RIC) sobre los valores medidos; mismo criterio de decisión que la Fase 34."""
    filas = []
    for c in V.CONTINUAS_USUARIA:
        x = revision._observados(df, c)
        q1, q3 = x.quantile([.25, .75])
        ric = q3 - q1
        bajo, alto = q1 - 1.5 * ric, q3 + 1.5 * ric
        inf, sup = x[x < bajo], x[x > alto]
        regla, texto = revision.CRITERIO_CLINICO[c]
        filas.append({'variable': c, 'n': len(x), 'q1': q1, 'q3': q3, 'limite_inferior': bajo,
                      'limite_superior': alto, 'atipicos_bajos': len(inf), 'atipicos_altos': len(sup),
                      'valores_bajos': ', '.join(f'{v:g}' for v in sorted(inf.unique())),
                      'valores_altos': ', '.join(f'{v:g}' for v in sorted(sup.unique())),
                      'altos_en_categoria_clinica': int(regla(sup).sum()) if regla and len(sup) else 0,
                      'criterio_clinico': texto, 'decision': 'se conserva'})
    return pd.DataFrame(filas)


def main():
    df, diccionario = V.cargar(V.LIMPIO_USUARIA, 'dataset_usuaria_limpio.csv')
    df = df.copy()
    campos, _ = catalogo.leer_modelos()
    for carpeta in (FIGURAS, RESULTADOS, ANALITICO):
        carpeta.mkdir(parents=True, exist_ok=True)
    df['severidad'] = E.severidad_codigo(df)
    df[GRUPO] = df['trabaja_actualmente'].map({'True': 'Trabaja', 'False': 'No trabaja'})
    mrs = df[df['mrs_completo'] == '1']
    guardar = dict(index=False, encoding='utf-8-sig', float_format='%.5f')

    # 2. Variable objetivo
    conteo = mrs['mrs_severidad'].value_counts().reindex(V.ORDEN_SEVERIDAD).fillna(0).astype(int)
    G.clases_severidad(conteo, FIGURAS / 'severidad_clases.png')
    G.histograma_mrs(df, FIGURAS / 'mrs_total.png')

    # 3. Frecuencias de todas las variables, trabaja vs. no trabaja (una figura por variable)
    trabajadoras = df[df[GRUPO] == 'Trabaja']
    variables_grupo = [v for _, vs in BLOQUES.values() for v in vs
                       if v not in SOLO_TRABAJO and v not in V.MULTISELECCION]
    prueba_df = pd.DataFrame({v: prueba(df, v) for v in variables_grupo}).assign(**{GRUPO: df[GRUPO]})
    dif = E.diferencia_grupos(prueba_df, variables_grupo, GRUPO)
    # Las de trabajo solo tienen un grupo: se informa solo la concentración.
    dif = pd.concat([dif, E.diferencia_grupos(trabajadoras.assign(**{GRUPO: 'Trabaja'}), SOLO_TRABAJO, GRUPO)])
    dif['bloque'] = dif['variable'].map({v: t for t, vs in BLOQUES.values() for v in vs})
    # Respuesta más frecuente en texto legible (edad y horas son continuas: no aplica).
    dif['categoria_dominante'] = [
        '' if v in V.CONTINUAS_USUARIA else
        respuestas(trabajadoras if v in SOLO_TRABAJO else df, v, campos)[0].value_counts().idxmax()
        for v in dif['variable']]
    dif_v = dif.set_index('variable')

    carpeta_frec = FIGURAS / 'frecuencias'
    carpeta_frec.mkdir(exist_ok=True)
    # Se borran las figuras de una corrida anterior (variables que ya no se grafican).
    for viejo in [*FIGURAS.glob('frecuencias_*.png'), *carpeta_frec.glob('*.png')]:
        viejo.unlink()
    largas, bloques = [], {}
    for clave, (titulo, variables) in BLOQUES.items():
        figuras = []
        for v in variables:
            solo = v in SOLO_TRABAJO
            pct, n, base = por_grupo(trabajadoras if solo else df, v, campos,
                                     grupos=['Trabaja'] if solo else NOMBRES_GRUPO)
            nota = nota_figura(base, v, dif_v)
            G.frecuencia_variable(pct, carpeta_frec / f'{v}.png', V.etiqueta(v), nota)
            figuras.append((v, f'frecuencias/{v}.png', nota))
            largas += [{'bloque': titulo, 'variable': v, 'respuesta': r, 'grupo': g,
                        'n': int(n.at[r, g]), 'pct': pct.at[r, g]} for r in pct.index for g in pct.columns]
        bloques[clave] = (titulo, figuras)
    frec = pd.DataFrame(largas)

    # 2.1 Perfil de los 11 síntomas del MRS
    items = mrs[list(V.MRS_ITEMS)].apply(V.numerica)
    perfil = pd.DataFrame({
        'sintoma': list(V.MRS_ITEMS.values()),
        'media': items.mean().values,
        'pct_moderado_o_mas': 100 * (items >= 2).mean().values,
        **{g: 100 * (items[mrs[GRUPO] == g] >= 2).mean().values for g in NOMBRES_GRUPO},
        'p_ajustado': dif_v.loc[list(V.MRS_ITEMS), 'p_ajustado'].values,
    }, index=list(V.MRS_ITEMS)).sort_values('pct_moderado_o_mas', ascending=False)
    G.perfil_sintomas(perfil.set_index('sintoma')[NOMBRES_GRUPO], FIGURAS / 'perfil_sintomas.png')
    subescalas = mrs.groupby(GRUPO)[['mrs_somatico', 'mrs_psicologico', 'mrs_urogenital', 'mrs_total']] \
        .agg(lambda x: V.numerica(x).mean()).reindex(NOMBRES_GRUPO)

    # 4. Faltantes, atípicos e IMC no informado
    falt = diccionario[(diccionario['faltantes'] > 0) & ~diccionario['variable'].isin(list(V.MRS_ITEMS))].copy()
    falt = falt.sort_values('pct_faltante', ascending=False)
    atip = atipicos_usuaria(df)
    G.cajas_atipicos(df, atip, revision._observados, FIGURAS / 'atipicos.png', columnas=3)
    continuas = {c: revision._observados(df, c) for c in V.CONTINUAS_USUARIA}
    G.histogramas(continuas, FIGURAS / 'distribucion_continuas.png', columnas=3)
    mrs = mrs.assign(imc_info=np.where(mrs['imc_categoria'] == 'no informado', 'IMC no informado',
                                       'IMC informado'))
    sev_imc_info = E.severidad_por(mrs, 'imc_info', ['IMC informado', 'IMC no informado'])
    chi_imc_info = E.severidad_independencia(mrs, 'imc_info')
    y = V.numerica(mrs['mrs_total'])
    mw_imc_info = stats.mannwhitneyu(y[mrs['imc_info'] == 'IMC informado'], y[mrs['imc_info'] == 'IMC no informado'])
    no_info = df['imc_categoria'] == 'no informado'
    perfil_no_info = pd.DataFrame({
        'rasgo': ['Trabaja', 'Usa terapia hormonal', 'Medicamentos para la diabetes', 'Edad media'],
        'IMC informado': [100 * (df.loc[~no_info, 'trabaja_actualmente'] == 'True').mean(),
                          100 * (df.loc[~no_info, 'usa_terapia_hormonal'] == 'SI').mean(),
                          100 * (df.loc[~no_info, 'usa_medicamentos_diabetes'] == 'SI').mean(),
                          V.numerica(df.loc[~no_info, 'edad']).mean()],
        'IMC no informado': [100 * (df.loc[no_info, 'trabaja_actualmente'] == 'True').mean(),
                             100 * (df.loc[no_info, 'usa_terapia_hormonal'] == 'SI').mean(),
                             100 * (df.loc[no_info, 'usa_medicamentos_diabetes'] == 'SI').mean(),
                             V.numerica(df.loc[no_info, 'edad']).mean()]})
    G.severidad_apilada(sev_imc_info, 'Severidad según si informó peso y talla', FIGURAS / 'imc_informado.png')
    banderas = {'incoherencia_ejercicio': int((df['incoherencia_ejercicio'] == '1').sum()),
                'incoherencia_pildora_th': int((df['incoherencia_pildora_th'] == '1').sum())}

    # 5. Severidad por edad y por situación laboral
    orden_tramos = sorted(mrs['tramo_edad'].dropna().unique(), key=lambda t: (t != '<40', t))
    sev_tramo = E.severidad_por(mrs, 'tramo_edad', orden_tramos)
    sev_trabajo = E.severidad_por(mrs, GRUPO, NOMBRES_GRUPO)
    mrs = mrs.assign(tramo_trabajo=mrs['tramo_edad'] + ' · ' + mrs[GRUPO].str.lower())
    sev_cruce = E.severidad_por(mrs, 'tramo_trabajo', [f'{t} · {g.lower()}' for t in orden_tramos
                                                       for g in NOMBRES_GRUPO])
    pruebas_sev = {'tramo_edad': E.severidad_independencia(mrs, 'tramo_edad'),
                   GRUPO: E.severidad_independencia(mrs, GRUPO)}
    kw_tramo = stats.kruskal(*[y[mrs['tramo_edad'] == t] for t in orden_tramos])
    G.severidad_apilada(sev_tramo, 'Severidad según tramo de edad', FIGURAS / 'severidad_edad.png')
    G.severidad_apilada(sev_trabajo, 'Severidad según situación laboral', FIGURAS / 'severidad_trabajo.png')
    G.severidad_apilada(sev_cruce, 'Severidad según tramo de edad y situación laboral',
                        FIGURAS / 'severidad_edad_trabajo.png')

    # 6. Asociación con la severidad (FDR sobre todas las pruebas explicativas)
    asoc = pd.concat([E.corregir_fdr(pd.concat([E.cruce_con_mrs(df, list(g), rol, resultado='severidad')
                                                for g, rol in grupos])).assign(familia=familia)
                      for grupos, familia in ((GRUPOS_ASOCIACION, 'principal'),
                                              (GRUPOS_SECUNDARIOS, 'secundaria'))],
                     ignore_index=True).sort_values('p_ajustado', ignore_index=True)
    # Solo para explicar en el informe por qué las familias van separadas.
    fdr_conjunta = E.corregir_fdr(asoc.drop(columns=['p_ajustado', 'familia'])).set_index('variable')['p_ajustado']
    spear = asoc[asoc['prueba'] == 'Spearman']
    kruskal = asoc[asoc['prueba'] == 'Kruskal-Wallis']
    sig = spear[spear['p_ajustado'] < 0.05]
    bloque_de = {**{v: t for t, vs in BLOQUES.values() for v in vs},
                 'doble_carga': BLOQUES['cuidado'][0], 'trabaja_actualmente': BLOQUES['control'][0]}
    titulos = [t for t, _ in BLOQUES.values()]
    # Matriz con todas las variables de Spearman, ordenadas por bloque (como en la sección 3).
    todas = sorted(spear['variable'], key=lambda v: titulos.index(bloque_de.get(v, BLOQUES['otras'][0])))
    matriz = E.matriz_spearman(df, todas)
    orden_sig = sig.reindex(sig['efecto'].abs().sort_values(ascending=False).index)['variable'].tolist()
    matriz_sig = E.matriz_spearman(df, [v for v in orden_sig if v != 'imc'])
    redundantes = [(a, b, matriz.at[a, b]) for i, a in enumerate(matriz.columns[1:], 1)
                   for b in matriz.columns[i + 1:] if abs(matriz.at[a, b]) >= 0.8]
    G.asociacion_severidad(spear, FIGURAS / 'asociacion_severidad.png',
                           'Correlación de cada variable con la severidad')
    G.mapa_calor(matriz_sig, FIGURAS / 'matriz_significativas.png',
                 'Matriz de Spearman: severidad y variables significativas')
    G.mapa_calor(matriz, FIGURAS / 'matriz_completa.png',
                 'Matriz de Spearman completa (todas las variables, por bloque)', anotar=False)

    # 7. Dirección y detalle del ejercicio
    para_direccion = orden_sig[:9]
    # Eje y en la escala completa de cada pregunta (no se exageran diferencias chicas).
    def ejes_y(variables):
        return [(v, _eje_y(v, campos), _limites_y(mrs, v, campos)) for v in variables]

    G.direccion(df, ejes_y(para_direccion), FIGURAS / 'direccion.png')
    # 7.1 Numéricas: violín + caja por clase de severidad (valores medidos, sin imputados).
    spear_v = spear.set_index('variable')

    def nota_rho(v):
        if v not in spear_v.index:
            return 'sin prueba: la representa el IMC'
        t = spear_v.loc[v]
        return f'rho = {t.efecto:+.2f} · p ajustado = {t.p_ajustado:.3f}'

    violin = [(v, revision._observados(mrs, v)) for v in V.CONTINUAS_USUARIA]
    G.violin_severidad(mrs, violin, FIGURAS / 'violin_severidad.png',
                       {**{v: _eje_y(v, campos) for v in V.CONTINUAS_USUARIA},
                        'peso_kg': 'kg', 'talla_actual_cm': 'cm'},
                       notas={v: nota_rho(v) for v in V.CONTINUAS_USUARIA})
    medianas_sev = pd.DataFrame({v: x.groupby(mrs.loc[x.index, 'mrs_severidad']).median()
                                 .reindex(V.ORDEN_SEVERIDAD) for v, x in violin}).T
    # 7.2 Significativas no numéricas: % de severidad dentro de cada respuesta (hasta 8 paneles).
    apiladas = []
    for v in [v for v in orden_sig if v not in V.CONTINUAS_USUARIA][:8]:
        s, orden = respuestas(mrs, v, campos)
        apiladas.append((v, E.severidad_por(mrs.assign(respuesta=s), 'respuesta', orden), nota_rho(v)))
    G.severidad_por_respuesta(apiladas, FIGURAS / 'severidad_por_respuesta.png')
    # Anexo: las no significativas, en paneles por bloque (mismo orden que la sección 3).
    no_sig = spear[spear['p_ajustado'] >= 0.05].set_index('variable')
    carpeta_dir = FIGURAS / 'direccion_anexo'
    carpeta_dir.mkdir(exist_ok=True)
    for viejo in carpeta_dir.glob('*.png'):
        viejo.unlink()
    direccion_anexo = []
    for clave, (titulo, _) in BLOQUES.items():
        vs = [v for v in no_sig.index if bloque_de.get(v, BLOQUES['otras'][0]) == titulo]
        if not vs:
            continue
        notas = {v: f'rho = {no_sig.at[v, "efecto"]:+.2f} · p ajustado = {no_sig.at[v, "p_ajustado"]:.3f}'
                 for v in vs}
        G.direccion(df, ejes_y(vs), carpeta_dir / f'{clave}.png',
                    titulo=f'{titulo}: media según la severidad (IC 95 %)', notas=notas)
        direccion_anexo.append((titulo, f'direccion_anexo/{clave}.png', vs))
    etiquetas_ejercicio = campos['dias_ejercicio_semana']['opciones']
    sev_ejercicio = E.severidad_por(mrs.assign(ejercicio=V.numerica(mrs['dias_ejercicio_semana'])
                                               .map(etiquetas_ejercicio)),
                                    'ejercicio', list(etiquetas_ejercicio.values()))
    G.severidad_apilada(sev_ejercicio, 'Severidad según días de ejercicio a la semana',
                        FIGURAS / 'ejercicio_severidad.png')

    # 8. Consecuencias de los síntomas (efecto del MRS, no predictores)
    conse = E.corregir_fdr(E.cruce_con_mrs(df, list(V.IMPACTO), 'impacto', resultado='severidad'))
    G.direccion(df, ejes_y(V.IMPACTO), FIGURAS / 'consecuencias.png',
                titulo='Consecuencias de los síntomas: media según la severidad (IC 95 %)')

    # 9. Salidas
    frec.to_csv(RESULTADOS / 'frecuencias.csv', **guardar)
    dif.assign(etiqueta=dif['variable'].map(V.etiqueta)).to_csv(RESULTADOS / 'diferencias_trabajo.csv', **guardar)
    atip.to_csv(RESULTADOS / 'atipicos.csv', **guardar)
    falt.to_csv(RESULTADOS / 'faltantes.csv', **guardar)
    asoc.assign(etiqueta=asoc['variable'].map(V.etiqueta)).to_csv(RESULTADOS / 'asociacion_severidad.csv', **guardar)
    conse.assign(etiqueta=conse['variable'].map(V.etiqueta)).to_csv(RESULTADOS / 'consecuencias.csv', **guardar)
    matriz.to_csv(RESULTADOS / 'matriz_spearman.csv', encoding='utf-8-sig', float_format='%.4f')
    salida = mrs.drop(columns=['imc_info', 'tramo_trabajo'])
    salida.to_csv(ANALITICO / 'conjunto_eda_usuaria.csv', index=False, encoding='utf-8-sig')

    perfil.to_csv(RESULTADOS / 'perfil_sintomas.csv', **guardar)
    pd.concat([t.rename_axis('respuesta').reset_index().assign(variable=v, etiqueta=V.etiqueta(v))
               for v, t, _ in apiladas]).to_csv(RESULTADOS / 'severidad_por_respuesta.csv', **guardar)
    r = {'n': len(df), 'n_mrs': len(mrs), 'mrs': mrs, 'df': df, 'conteo': conteo, 'bloques': bloques,
         'perfil': perfil, 'fdr_conjunta': fdr_conjunta,
         'bloque_de': bloque_de, 'subescalas': subescalas, 'direccion_anexo': direccion_anexo, 'continuas': continuas,
         'dif': dif, 'falt': falt, 'atip': atip, 'sev_imc_info': sev_imc_info, 'chi_imc_info': chi_imc_info,
         'mw_imc_info': mw_imc_info, 'perfil_no_info': perfil_no_info, 'banderas': banderas,
         'sev_tramo': sev_tramo, 'sev_trabajo': sev_trabajo, 'sev_cruce': sev_cruce,
         'pruebas_sev': pruebas_sev, 'kw_tramo': kw_tramo, 'asoc': asoc, 'spear': spear,
         'kruskal': kruskal, 'sig': sig, 'orden_sig': orden_sig, 'redundantes': redundantes,
         'n_matriz': len(matriz) - 1, 'para_direccion': para_direccion, 'sev_ejercicio': sev_ejercicio,
         'conse': conse, 'trabajadoras': len(trabajadoras), 'violin': violin, 'medianas_sev': medianas_sev,
         'apiladas': apiladas}
    (ANALISIS / 'informe_eda_usuaria.md').write_text(informe_usuaria.generar(r), encoding='utf-8')
    print(f'{len(df)} participantes, {len(mrs)} con MRS completo; {len(sig)} correlaciones significativas')
    print('Informe: analisis/informe_eda_usuaria.md')


def _eje_y(variable, campos):
    """Texto del eje y en la figura de dirección: unidad o escala de la pregunta."""
    opciones = campos.get(variable, {}).get('opciones')
    if variable in ('trabaja_actualmente', 'doble_carga') or (opciones and set(opciones) <= {'SI', 'NO'}):
        return 'proporción "sí"'
    if opciones and all(isinstance(k, int) for k in opciones):
        claves = sorted(opciones)
        return f'nivel medio\n{claves[0]} = {opciones[claves[0]]} … {claves[-1]} = {opciones[claves[-1]]}'
    return {'imc': 'kg/m²', 'edad': 'años', 'horas_sedentarismo': 'horas'}.get(variable, 'valor medio')


def _limites_y(df, v, campos):
    """Escala completa de la pregunta para el eje y (None en las continuas: se ajusta a los datos)."""
    if v in V.CONTINUAS_USUARIA:
        return None
    x = V.codificar(df, [v]).get(v)
    if x is None:
        return None
    x = x.dropna()
    if set(x.unique()) <= {0, 1}:
        return 0, 1
    if v in V.ORDEN_TEXTO:
        return 0, len(V.ORDEN_TEXTO[v]) - 1
    opciones = campos.get(v, {}).get('opciones')
    if opciones and all(isinstance(k, int) for k in opciones):
        return min(min(opciones), x.min()), max(opciones)
    return None


if __name__ == '__main__':
    main()
