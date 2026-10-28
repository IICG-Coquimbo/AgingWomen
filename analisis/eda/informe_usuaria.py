"""Informe del EDA del conjunto de la usuaria en Markdown (analisis/informe_eda_usuaria.md, Fase 34C)."""
from datetime import date

import pandas as pd

from . import variables as V
from .informe import _f, _p, _tabla
from .informe_eda import RANGOS_MRS, _figura

FIG = 'figuras/eda_usuaria'


def _pct(n, total):
    return f'{100 * n / total:.1f} %'


def _rho(t):
    return f'rho = {t.efecto:+.2f}'


def _igual(p):
    """'= 0.809' o '< 0,001' (sin el signo = duplicado)."""
    return _p(p) if p < 0.001 else f'= {_p(p)}'


def _magnitud(efecto):
    e = abs(efecto)
    return 'despreciable' if e < 0.10 else 'pequeña' if e < 0.30 else 'mediana' if e < 0.50 else 'grande'


def _interpretar_grupo(v, dif):
    """Lectura en lenguaje sencillo de la prueba trabaja vs. no trabaja de una figura de la sección 3."""
    if v in V.MULTISELECCION:
        return ('Pregunta de selección múltiple: no lleva prueba. Compare a simple vista qué opciones marcan '
                'más quienes trabajan y quienes no.')
    if v not in dif.index or pd.isna(dif.at[v, 'p_ajustado']):
        return ('Solo responden quienes trabajan, así que no hay dos grupos que comparar. Mire cómo se '
                'reparten las respuestas y si alguna concentra a casi todas.')
    t = dif.loc[v]
    tam = f'{t.medida} = {t.efecto:.2f}: diferencia {_magnitud(t.efecto)}'
    if t.p_ajustado >= 0.05:
        return (f'{tam}; p ajustado {_igual(t.p_ajustado)} (0,05 o más). Quienes trabajan y quienes no '
                'responden de forma parecida: las diferencias que se ven entre las barras pueden ser azar. '
                'No dice nada sobre la relación con los síntomas.')
    if t.medida == 'r':
        mayor = 'quienes trabajan' if t.efecto > 0 else 'quienes no trabajan'
        detalle = f'{mayor} tienen valores más altos.'
    else:
        detalle = 'mire en las barras qué respuestas concentra cada grupo.'
    return (f'{tam}; p ajustado {_igual(t.p_ajustado)} (menor que 0,05). Los dos grupos **sí** responden '
            f'distinto y es poco probable que sea azar: {detalle} Esto no significa por sí solo que la variable se relacione '
            'con los síntomas.')


def generar(r):
    n, n_mrs, conteo, mrs, df = r['n'], r['n_mrs'], r['conteo'], r['mrs'], r['df']
    dif, asoc, spear, sig = r['dif'], r['asoc'], r['spear'], r['sig']
    severa = conteo['Severa']
    trabajan_mrs = int((mrs['grupo_trabajo'] == 'Trabaja').sum())
    sin_seccion = r['trabajadoras'] - int(df.loc[df['grupo_trabajo'] == 'Trabaja', 'estres_entorno_laboral'].notna().sum())
    num = iter(range(1, 1000))
    out = [
        '# Análisis exploratorio del conjunto de la usuaria común (Fase 34C)',
        '',
        f'Generado por `analisis/eda_usuaria.py` el {date.today().isoformat()}. Volver a ejecutar el script',
        'regenera este informe, las figuras (`analisis/figuras/eda_usuaria/`) y las tablas',
        '(`analisis/resultados/usuaria/`).',
        '',
        'Responde a la reunión con la profesora del 20 de octubre: el análisis se hace sobre el conjunto',
        'sintético de la usuaria común (Fase 34A, ronda 1, encuestas autoaplicadas), ya limpio (Fase 34B).',
        'El EDA del dataset de la profesora (`informe_eda.md`) queda como anexo.',
        '',
        '## 1. Conjunto analizado',
        '',
        f'- **{n} participantes** después de la limpieza; **{n_mrs}** con las 11 preguntas del MRS respondidas',
        f'  (las {n - n_mrs} restantes se describen, pero no entran a los cruces con la severidad).',
        f'- Trabajan {r["trabajadoras"]} ({_pct(r["trabajadoras"], n)}); {trabajan_mrs} de ellas tienen MRS completo.',
        f'  En {sin_seccion} el dato "trabaja" vino vacío y la limpieza lo imputó con la moda ("sí"), por eso',
        '  no tienen respondida la sección Trabajo.',
        '- **Variables incluidas:** actividad física, alimentación, sustancias, cuidado de otras personas y',
        '  trabajo (predictores); edad, etapa menopáusica, IMC, terapia hormonal, previsión de salud y',
        '  medicamentos para la diabetes (control); salud ginecológica (menstruación, sangrado, método',
        '  anticonceptivo, útero, ovarios, operada para no tener más hijos) y medicamentos para la presión,',
        '  evacuación intestinal y distensión abdominal; origen, pueblo originario, comuna, pareja y',
        '  actividad sexual (otras características).',
        '- **Variables excluidas:** las que solo registra el personal de salud (laboratorio, presión,',
        '  cintura, pérdida de talla, tamizaje), el nivel educacional, el conocimiento del sistema de salud y',
        '  la encuesta de usabilidad de la plataforma: no se relacionan con los síntomas.',
        '- **Consecuencias** de los síntomas (rendimiento, bienestar laboral, ausencias, cambio en la',
        '  pareja, antidepresivos): se analizan aparte, en la sección 8, porque son efecto del MRS.',
        '',
        '## 2. Variable objetivo: severidad del MRS en 4 clases',
        '',
        f'Cortes del puntaje MRS total confirmados por la profesora el 20-10: '
        + ', '.join(f'{s.lower()} ({c})' for s, c in zip(V.ORDEN_SEVERIDAD, RANGOS_MRS)) + '.',
        '',
        _tabla(['Severidad', 'Puntaje', 'Participantes', '%'],
               [(s, c, int(conteo[s]), _pct(conteo[s], n_mrs)) for s, c in zip(V.ORDEN_SEVERIDAD, RANGOS_MRS)]),
        '',
        *_figura(next(num), f'{FIG}/severidad_clases.png', 'Distribución de la variable objetivo',
                 f'Participantes con MRS completo (n = {n_mrs}).',
                 muestra=f'la clase severa reúne a {_pct(severa, n_mrs)} de las participantes. Las clases no '
                 'están balanceadas: hay que tenerlo en cuenta al evaluar los clústeres de la Fase 37 (por '
                 'ejemplo, comparar la composición de cada clúster con esta distribución base).'),
        *_figura(next(num), f'{FIG}/mrs_total.png', 'Puntaje MRS total y cortes de severidad',
                 'Líneas punteadas: cortes entre clases.',
                 muestra=f'media {V.numerica(mrs["mrs_total"]).mean():.1f} ± '
                 f'{V.numerica(mrs["mrs_total"]).std():.1f} puntos. El corte de "severa" (16) queda cerca '
                 'de la media, por eso cerca de la mitad cae en esa clase.'),
    ]
    out += _seccion_perfil(r, num)
    out += _seccion_frecuencias(r, num)
    out += _seccion_calidad(r, num)
    out += _seccion_edad_trabajo(r, num)
    out += _seccion_asociacion(r, num)
    out += _seccion_direccion(r, num)
    out += _seccion_consecuencias(r, num)
    out += [
        '## 9. Salida para la Fase 35',
        '',
        f'`datos/analitico/conjunto_eda_usuaria.csv`: las {n_mrs} participantes con MRS completo, con la',
        'columna `severidad` (0 = sin síntomas o muy leves … 3 = severa). Es la entrada de la selección de',
        'variables por entropía.',
        '',
        '**Para llevar a la Fase 35:**',
        '',
        f'- Variables con poca variación (una respuesta ≥ 90 %): '
        + ', '.join(V.etiqueta(v).lower() for v in dif.loc[dif['poca_variacion'], 'variable']) + '.',
        '- Pares redundantes (|rho| ≥ 0,8): '
        + ('; '.join(f'{V.etiqueta(a).lower()} y {V.etiqueta(b).lower()} ({c:+.2f})' for a, b, c in r['redundantes'])
           or 'ninguno') + '.',
        '- El IMC entra como categoría con "no informado"; el IMC numérico solo sirve en quienes lo informaron.',
        '- Las variables de trabajo solo existen para quienes trabajan: van en un análisis aparte o con un',
        '  nivel "no trabaja".',
        '',
        '**Decisiones que conviene validar con la profesora:**',
        '',
        '- Si la clase severa (cerca de la mitad) es aceptable o conviene revisar los cortes para el modelado.',
        '- Si comuna, origen y pueblo originario se mantienen: tienen muchas categorías con pocos casos.',
        '- La definición de etapa menopáusica (STRAW+10 simplificado) es nuestra: se mantiene como variable',
        '  de control (decisión 2026-10-26), pero conviene que la profesora la valide.',
        '',
    ]
    out += _anexo_direccion(r, num)
    out += _anexo_matriz(r, num)
    return '\n'.join(out)


def _anexo_matriz(r, num):
    """Anexo B: matriz de Spearman con todas las variables."""
    return [
        '## Anexo B. Matriz de Spearman con todas las variables',
        '',
        f'Las {r["n_matriz"]} variables de la sección 6.2 más la severidad (primera fila y columna), ordenadas',
        'por bloque como en la sección 3. Se calcula con las participantes que tienen MRS completo y, para',
        'cada par, con quienes tienen ambos datos. Los valores exactos están en',
        '`resultados/usuaria/matriz_spearman.csv`.',
        '',
        *_figura(next(num), f'{FIG}/matriz_completa.png', 'Matriz de Spearman con todas las variables',
                 'Azul: correlación negativa; rojo: positiva; blanco: cercana a 0.',
                 como='cada casilla es la rho entre la variable de la fila y la de la columna. La primera fila '
                 'es la correlación con la severidad (la misma de la figura de la sección 6.2). Los cuadros '
                 'de color intenso fuera de la diagonal señalan variables redundantes entre sí.'),
    ]


def _anexo_direccion(r, num):
    """Anexo A: dirección de las variables sin asociación significativa, en paneles por bloque."""
    n_vars = sum(len(vs) for _, _, vs in r['direccion_anexo'])
    out = [
        '## Anexo A. Dirección de las variables no significativas',
        '',
        f'Mismo gráfico que la figura de la sección 7, para las {n_vars} variables cuya correlación con la',
        'severidad **no** fue significativa (p ajustado ≥ 0,05), agrupadas por bloque. Sirve para comprobar',
        'que se revisaron todas y para ver tendencias cercanas al límite.',
        '',
        '**Cómo leerlas.** Cada punto es la media de la variable en una clase de severidad y la barra',
        'vertical, su intervalo de confianza del 95 %. Bajo el título de cada panel van la rho y el p',
        'ajustado de la sección 6.2. El eje vertical muestra la escala completa de cada pregunta (por',
        'ejemplo, 1 a 5, o 0 a 1 en las de sí/no), igual que en la sección 7, para no exagerar diferencias',
        'chicas; en edad, IMC y horas sentada se ajusta a los datos. Como estas asociaciones no son significativas, una línea que sube o baja',
        'no permite afirmar una relación: si los intervalos se superponen, las diferencias entre clases',
        'pueden ser azar. Las de p ajustado cercano a 0,05 son las únicas que vale la pena mirar con más',
        'atención.',
        '',
        'Las variables nominales (etapa menopáusica, IMC por categoría, previsión, comuna, entre otras) no',
        'tienen una media con sentido: se compararon con Kruskal-Wallis y no aparecen aquí.',
        '',
    ]
    for titulo, archivo, vs in r['direccion_anexo']:
        cerca = [v for v in vs if r['spear'].set_index('variable').at[v, 'p_ajustado'] < 0.10]
        out += _figura(next(num), f'{FIG}/{archivo}', titulo,
                       'Puntos: media en cada clase; barras: IC 95 %.',
                       muestra=('cerca del límite (p ajustado < 0,10): '
                                + ', '.join(V.etiqueta(v).lower() for v in cerca) + '.') if cerca else None)
    return out


def _seccion_perfil(r, num):
    p, sub = r['perfil'], r['subescalas']
    distintos = p[p['p_ajustado'] < 0.05]
    return [
        '### 2.1 Perfil de los 11 síntomas',
        '',
        'Cada ítem del MRS va de 0 (ninguna molestia) a 4 (muy intensa). Se cuenta como presente en grado',
        'moderado o mayor cuando la respuesta es 2 o más. La frecuencia de cada respuesta, ítem por ítem, está',
        f'en la sección 3.{list(r["bloques"]).index("sintomas") + 1}.',
        '',
        _tabla(['Síntoma', 'Media (0-4)', 'Moderado o más', 'Trabaja', 'No trabaja', 'p ajustado*'],
               [(t.sintoma, f'{t.media:.2f}', f'{t.pct_moderado_o_mas:.1f} %', f'{t.Trabaja:.1f} %',
                 f'{t._5:.1f} %', _p(t.p_ajustado)) for t in p.itertuples()]),
        '',
        '*Chi² entre las 5 respuestas del ítem y la situación laboral, con la corrección FDR de la sección 3.',
        '',
        *_figura(next(num), f'{FIG}/perfil_sintomas.png', 'Síntomas en grado moderado o mayor',
                 'Ordenados de más a menos frecuente; azul oscuro: trabaja; azul claro: no trabaja.',
                 muestra=f'los más frecuentes son {p["sintoma"].iloc[0].lower()} '
                 f'({p["pct_moderado_o_mas"].iloc[0]:.0f} %), {p["sintoma"].iloc[1].lower()} '
                 f'({p["pct_moderado_o_mas"].iloc[1]:.0f} %) y {p["sintoma"].iloc[2].lower()} '
                 f'({p["pct_moderado_o_mas"].iloc[2]:.0f} %); el menos frecuente es '
                 f'{p["sintoma"].iloc[-1].lower()} ({p["pct_moderado_o_mas"].iloc[-1]:.0f} %). '
                 + (f'Entre quienes trabajan y quienes no, difieren: '
                    + ', '.join(s.lower() for s in distintos['sintoma']) + '.' if len(distintos) else
                    'Ningún síntoma difiere significativamente entre quienes trabajan y quienes no.')),
        'Puntaje medio por subescala:',
        '',
        _tabla(['Grupo', 'Somática (0-16)', 'Psicológica (0-16)', 'Urogenital (0-12)', 'Total (0-44)'],
               [(g, *(f'{x:.1f}' for x in f)) for g, f in sub.iterrows()]),
        '',
    ]



def _seccion_frecuencias(r, num):
    dif = r['dif']
    con_prueba = dif[dif['p'].notna()]
    distintas = con_prueba[con_prueba['p_ajustado'] < 0.05].sort_values('p_ajustado')
    poca = dif[dif['poca_variacion']].sort_values('pct_dominante', ascending=False)
    n_figuras = sum(len(f) for _, f in r['bloques'].values())
    out = [
        '## 3. Frecuencias de todas las variables según situación laboral',
        '',
        f'Una figura por pregunta ({n_figuras} en total): el % de cada respuesta',
        'entre quienes trabajan (azul oscuro) y quienes no (azul claro). Bajo el título de cada figura se',
        'indica cuántas participantes de cada grupo tienen el dato y el resultado de la prueba de diferencia.',
        '',
        '- En las preguntas que dependen de otra (frecuencia de cada tipo de ejercicio, cuántas personas',
        '  cuida, sobrecarga), "no lo realiza" / "no cuida" es la respuesta de quien contestó "no" a la',
        '  pregunta madre. Las demás preguntas condicionales (tipo de sangrado, método anticonceptivo, a quién',
        '  cuida) se calculan solo sobre quienes las respondieron.',
        '- La edad se muestra por tramo y las horas sentada agrupadas. IMC, peso y talla, como histograma en',
        '  intervalos, solo para quienes los informaron.',
        '- A quién cuida es de selección múltiple: el % es sobre quienes cuidan y puede sumar más de 100.',
        '- Las preguntas de la sección Trabajo y las consecuencias laborales solo las responden quienes',
        '  trabajan: tienen una sola barra.',
        '- Región: las 546 participantes son de Coquimbo (región 04), por eso no se grafica.',
        '',
        '**Prueba de diferencia.** Chi² de independencia (efecto: V de Cramér) para las categóricas y',
        'ordinales, y Mann-Whitney (efecto: correlación biserial de rangos r) para edad, IMC, peso, talla y',
        'horas sentada. Los valores p se corrigen por comparaciones múltiples con Benjamini-Hochberg (FDR).',
        '',
        '**Cómo leer la prueba de cada figura.** La prueba compara a **quienes trabajan con quienes no**;',
        '**no** mide la relación con la severidad de los síntomas (eso está en la sección 6). Responde a la',
        'pregunta: ¿esta variable se reparte distinto en los dos grupos?',
        '',
        '- **V o r (tamaño de la diferencia)**, de 0 a 1: menos de 0,10 = despreciable; 0,10 a 0,30 =',
        '  pequeña; 0,30 a 0,50 = mediana; más de 0,50 = grande. En r, el signo solo indica qué grupo tiene',
        '  valores más altos (+ = quienes trabajan).',
        '- **p ajustado (¿puede ser azar?)**: menor que 0,05 = los grupos sí responden distinto; 0,05 o más =',
        '  no se puede afirmar que difieran, aunque las barras no sean idénticas.',
        '- Que una variable **no** difiera entre los grupos es un resultado normal y esperado: solo dice que',
        '  trabajar no cambia esa respuesta.',
        '',
    ]
    dif_v = dif.set_index('variable')
    for i, (titulo, figuras) in enumerate(r['bloques'].values(), 1):
        out += [f'### 3.{i} {titulo}', '']
        for v, archivo, nota in figuras:
            out += _figura(next(num), f'{FIG}/{archivo}', V.etiqueta(v), nota)
            out += [f'**Qué interpretar.** {_interpretar_grupo(v, dif_v)}', '']
    i += 1
    out += [
        f'### 3.{i} Diferencias entre quienes trabajan y quienes no',
        '',
        f'De {len(con_prueba)} variables comparadas, **{len(distintas)}** difieren con FDR < 0,05:',
        '',
        _tabla(['Variable', 'Prueba', 'Efecto', 'p ajustado'],
               [(V.etiqueta(t.variable), t.prueba, f'{t.medida} = {t.efecto:.2f}', _p(t.p_ajustado))
                for t in distintas.itertuples()]),
        '',
        'Las que trabajan comen fuera del hogar con más frecuencia y sienten más que la falta de tiempo',
        'influye en lo que comen; la sobrecarga por cuidado también es mayor (suma trabajo y cuidado). El',
        'resto de los hábitos no cambia según la situación laboral, así que las diferencias de severidad',
        'entre ambos grupos (sección 5) no se explican por un estilo de vida distinto en general.',
        '',
        f'### 3.{i + 1} Variables con poca variación',
        '',
        'Una variable donde casi todas responden lo mismo aporta poca información para separar perfiles.',
        'Se marcan las que tienen una respuesta con 90 % o más:',
        '',
        _tabla(['Variable', 'Respuesta dominante', '%'],
               [(V.etiqueta(t.variable), t.categoria_dominante, _f(t.pct_dominante)) for t in poca.itertuples()]),
        '',
        'No se eliminan aquí: la decisión se toma en la Fase 35 con la entropía, que mide justamente esa',
        'falta de variación.',
        '',
    ]
    return out


def _seccion_calidad(r, num):
    falt, atip = r['falt'], r['atip']
    altas = falt[falt['pct_faltante'] > 30]
    resto = falt[falt['pct_faltante'] <= 30]
    sev, chi, mw, perfil = r['sev_imc_info'], r['chi_imc_info'], r['mw_imc_info'], r['perfil_no_info']
    b = r['banderas']
    out = [
        '## 4. Calidad de los datos',
        '',
        '### 4.1 Datos faltantes',
        '',
        'Los vacíos de preguntas que la encuesta no mostró ("no aplica") no cuentan como faltantes. Sobre las',
        'filas donde la pregunta aplica:',
        '',
        f'- **Más del 30 %:** ' + ', '.join(f'{V.etiqueta(v).lower()} ({p:.1f} %)'
                                             for v, p in zip(altas['variable'], altas['pct_faltante']))
        + '. No se imputan ni se modelan; el IMC entra como categoría con "no informado".',
        f'- **Resto:** {len(resto)} variables entre {resto["pct_faltante"].min():.1f} % y '
        f'{resto["pct_faltante"].max():.1f} %, imputadas en la limpieza (moda o mediana; con marca',
        '  `_imputado` cuando superan el 5 %). Las más altas son las preguntas de menstruación, que quedan',
        '  sin dato cuando falta la fecha de última menstruación.',
        '',
        'El detalle por variable está en `resultados/usuaria/faltantes.csv` y en el informe de limpieza.',
        '',
        '### 4.2 Distribución y atípicos de las variables continuas',
        '',
        'Valores medidos (sin imputados); peso, talla e IMC solo de quienes los informaron.',
        '',
        _tabla(['Variable', 'n', 'Media', 'DE', 'Mediana', 'Mín.', 'Máx.', 'Asimetría'],
               [(V.etiqueta(c), len(x), _f(x.mean()), _f(x.std()), _f(x.median()), _f(x.min()), _f(x.max()),
                 f'{x.skew():+.2f}') for c, x in r['continuas'].items()]),
        '',
        *_figura(next(num), f'{FIG}/distribucion_continuas.png', 'Distribución de las variables continuas',
                 'Histogramas de 25 intervalos; n = participantes con el dato.',
                 como='la asimetría cerca de 0 indica una distribución simétrica; positiva, una cola hacia '
                 'los valores altos; negativa, hacia los bajos.'),
        'Regla de Tukey (fuera de Q1 − 1,5 × RIC o Q3 + 1,5 × RIC) sobre los valores medidos. Igual que en',
        'la Fase 34, un atípico estadístico no es un error: se conserva si es clínicamente posible.',
        '',
        _tabla(['Variable', 'n', 'Límites', 'Bajos', 'Altos', 'Valores altos', 'Decisión'],
               [(V.etiqueta(t.variable), t.n, f'{_f(t.limite_inferior)} a {_f(t.limite_superior)}',
                 t.atipicos_bajos, t.atipicos_altos, t.valores_altos or '-', t.decision)
                for t in atip.itertuples()]),
        '',
        *_figura(next(num), f'{FIG}/atipicos.png', 'Atípicos en las variables continuas',
                 'Cajas con la regla de Tukey; puntos rojos = atípicos.',
                 muestra='hay muy pocos atípicos y todos son valores posibles (un peso de 122,8 kg, tallas de '
                 '170-176 cm, 13-14 horas sentada). Ninguno se elimina.'),
        '### 4.3 ¿Las que no informaron peso y talla son distintas?',
        '',
        'Si el IMC falta por una razón relacionada con los síntomas, la categoría "no informado" estaría',
        'sesgada. Se compara la severidad de ambos grupos:',
        '',
        _tabla(['Grupo', 'n'] + V.ORDEN_SEVERIDAD + ['MRS medio'],
               [(g, int(f['n']), *[f'{f[s]:.1f} %' for s in V.ORDEN_SEVERIDAD], _f(f['mrs_medio']))
                for g, f in sev.iterrows()]),
        '',
        f'Chi² = {chi["chi2"]:.2f} (gl = {chi["gl"]}), p = {_p(chi["p"])}, V de Cramér = {chi["v"]:.2f}; '
        f'Mann-Whitney sobre el MRS total, p = {_p(mw.pvalue)}.',
        '',
        _tabla(['Rasgo', 'IMC informado', 'IMC no informado'],
               [(t.rasgo, *(f'{x:.1f}' if t.rasgo == 'Edad media' else f'{x:.1f} %'
                            for x in (t._2, t._3))) for t in perfil.itertuples()]),
        '',
        *_figura(next(num), f'{FIG}/imc_informado.png', 'Severidad según si informó peso y talla',
                 'Barras 100 % apiladas por clase de severidad.',
                 muestra='la severidad es prácticamente igual en ambos grupos. La falta de peso y talla parece '
                 'no estar relacionada con los síntomas, así que la categoría "no informado" no introduce un '
                 'sesgo evidente.' if chi['p'] >= 0.05 else
                 'la severidad difiere entre ambos grupos: la categoría "no informado" no es neutra.'),
        '### 4.4 Incoherencias marcadas en la limpieza',
        '',
        f'- Ejercicio sin tipo: {b["incoherencia_ejercicio"]} participantes dicen hacer ejercicio pero no marcan',
        '  ningún tipo. Se conservan con la marca `incoherencia_ejercicio`.',
        f'- Píldora anticonceptiva con terapia hormonal: {b["incoherencia_pildora_th"]} participantes. Se',
        '  conservan con la marca `incoherencia_pildora_th`.',
        '',
    ]
    return out


def _seccion_edad_trabajo(r, num):
    pe, pt, kw = r['pruebas_sev']['tramo_edad'], r['pruebas_sev']['grupo_trabajo'], r['kw_tramo']
    etapa = r['kruskal'].set_index('variable').loc['etapa_menopausica']
    st = r['sev_trabajo']
    return [
        '## 5. Severidad según edad y situación laboral',
        '',
        *_figura(next(num), f'{FIG}/severidad_edad.png', 'Severidad según tramo de edad',
                 'Barras 100 % apiladas; entre paréntesis, participantes por tramo.',
                 muestra=f'la distribución es parecida en todos los tramos (chi² = {pe["chi2"]:.1f}, gl = '
                 f'{pe["gl"]}, p = {_p(pe["p"])}; Kruskal-Wallis sobre el MRS total, p = {_p(kw.pvalue)}). '
                 'En este rango de edad, la edad por sí sola no ordena la severidad; la etapa menopáusica '
                 + ('tampoco' if etapa.p_ajustado >= 0.05 else 'sí') + f' se asocia con ella (sección 6, '
                 f'p ajustado = {_p(etapa.p_ajustado)}).'),
        *_figura(next(num), f'{FIG}/severidad_trabajo.png', 'Severidad según situación laboral',
                 'Barras 100 % apiladas por clase de severidad.',
                 muestra=f'las que trabajan tienen más casos severos ({st.at["Trabaja", "Severa"]:.0f} % contra '
                 f'{st.at["No trabaja", "Severa"]:.0f} %; MRS medio {st.at["Trabaja", "mrs_medio"]:.1f} contra '
                 f'{st.at["No trabaja", "mrs_medio"]:.1f}). La diferencia '
                 + ('no alcanza significación' if pt['p'] >= 0.05 else 'es significativa')
                 + f' con chi² (p = {_p(pt["p"])}, V = {pt["v"]:.2f}). En la sección 6 se ve que dentro del '
                 'trabajo pesan el estrés y la falta de comprensión del lugar de trabajo.'),
        *_figura(next(num), f'{FIG}/severidad_edad_trabajo.png', 'Severidad según edad y situación laboral',
                 'Cada barra es un tramo de edad dentro de un grupo; los tramos con pocas participantes '
                 'deben leerse con cautela.',
                 muestra='en todos los tramos las que trabajan tienen una proporción de casos severos '
                 'igual o mayor que las que no trabajan; el patrón no depende de la edad.'),
    ]


def _por_que_tantas(principal, secundaria, bloque_de):
    orden = list(dict.fromkeys(bloque_de.values()))
    por_bloque = principal.index.map(bloque_de).value_counts().reindex(orden).dropna().astype(int)
    return [
        '**Por qué se hacen tantas pruebas.** La pregunta de esta sección es qué variables se relacionan con',
        'la severidad. No se sabe de antemano cuáles importan, así que se prueba cada una por separado contra',
        'la severidad: una prueba por variable.',
        '',
        _tabla(['Bloque', 'Pruebas'], [*por_bloque.items(), ('**Total (principales)**', f'**{len(principal)}**')]),
        '',
        f'A ellas se suman {len(secundaria)} pruebas de salud ginecológica y general (ver más abajo).',
        'No se prueban solo algunas porque:',
        '',
        '- la profesora pidió revisar todas las variables relacionadas con los síntomas (reunión del 20-10),',
        '  no solo las 14 del primer análisis;',
        '- es la etapa exploratoria: el objetivo es mirarlo todo antes de elegir; probar solo las que se',
        '  cree que importan podría dejar fuera algo inesperado;',
        '- prepara la Fase 35: la selección por entropía necesita saber qué variables muestran relación con',
        '  la severidad y cuáles no.',
        '',
        'Hacer muchas pruebas no es un error: es lo normal en un análisis exploratorio. Lo importante es',
        'corregir por ello, y para eso está el p ajustado. Más adelante, en la Fase 37 (PCA y clústeres), las',
        'variables se analizan todas juntas en un solo modelo, en vez de una por una.',
        '',
    ]


def _explicacion_fdr(r):
    a = r['asoc'].set_index('variable')
    principal = a[a['familia'] == 'principal'].sort_values('p')
    secundaria = a[a['familia'] == 'secundaria']
    n_p, n_t = len(principal), len(a)
    sig_p = principal[principal['p_ajustado'] < 0.05]
    caidas = principal[(principal['p'] < 0.05) & (principal['p_ajustado'] >= 0.05)].sort_values('p')
    ejemplos = [(sig_p.index[0], 'significativa: aun corregida queda muy por debajo de 0,05'),
                (sig_p['p_ajustado'].idxmax(), 'significativa, pero cerca del límite')]
    if len(caidas):
        ejemplos.append((caidas.index[0], '**no** significativa: sin corregir lo parecía; corregida, no'))
    sensibles = [v for v in principal.index if principal.at[v, 'p_ajustado'] < 0.05 <= r['fdr_conjunta'][v]]
    out = [
        '### 6.1 Valor p, p ajustado y corrección FDR',
        '',
        '**El valor p.** Cada prueba entrega un valor p, que responde: si en realidad no hubiera ninguna',
        'relación entre la variable y la severidad, ¿qué tan probable sería ver por casualidad una asociación',
        'tan fuerte como la encontrada? Un p chico (por ejemplo, 0,001) indica que sería muy raro verla por',
        'azar, así que probablemente la relación es real; un p grande (por ejemplo, 0,60), que es fácil verla',
        'por azar y no hay evidencia de relación. El límite habitual es 0,05: bajo ese valor el resultado se',
        'llama significativo.',
        '',
        *_por_que_tantas(principal, secundaria, r['bloque_de']),
        '**El problema de hacer muchas pruebas.** El límite de 0,05 está pensado para una sola prueba: acepta',
        f'un 5 % de probabilidad de encontrar una asociación que no existe. En esta sección se hacen {n_p}',
        'pruebas principales. Es como comprar muchos boletos de lotería: aunque ninguna variable tuviera',
        f'relación real con la severidad, se esperaría que unas {n_p * 0.05:.0f} salieran "significativas" por',
        'casualidad (' + f'{n_p} × 0,05 = {n_p * 0.05:.2f}'.replace('.', ',') + ').',
        '',
        '**El p ajustado.** Es el valor p corregido para tomar en cuenta cuántas pruebas se hicieron. Se usa',
        'la corrección FDR (*False Discovery Rate*, tasa de falsos descubrimientos) de Benjamini-Hochberg: las',
        'pruebas se ordenan de menor a mayor p y a cada una se le calcula',
        '',
        '> p ajustado = p × (número total de pruebas) / (posición en el orden)',
        '',
        '(además, el p ajustado nunca baja al avanzar en el orden). Se interpreta igual que el p normal: bajo',
        '0,05 es significativo. La diferencia es que, entre todas las variables declaradas significativas, se',
        'espera que a lo más un 5 % lo sean por azar. Por eso en este informe las decisiones se toman con el',
        'p ajustado. Ejemplos:',
        '',
        _tabla(['Variable', 'p original', 'p ajustado', 'Conclusión'],
               [(V.etiqueta(v), _p(a.at[v, 'p']), _p(a.at[v, 'p_ajustado']), c) for v, c in ejemplos]),
        '',
    ]
    if len(caidas):
        v = caidas.index[0]
        out += [f'El último ejemplo ({V.etiqueta(v).lower()}) muestra para qué sirve el ajuste: con su p original',
                f'({_p(a.at[v, "p"])}) se habría concluido que se asocia con la severidad; corregido',
                f'({_p(a.at[v, "p_ajustado"])}), esa evidencia no alcanza: podría ser uno de los resultados que',
                'aparecen por azar al probar muchas variables.', '']
    out += [
        '**Por qué hay dos familias de pruebas.** Como el número total de pruebas multiplica al p, mientras más',
        f'pruebas entran en la misma corrección, más exigente se vuelve. A las {n_p} pruebas principales',
        f'(hábitos, trabajo, cuidado, control y otras características) se suman {len(secundaria)} pruebas de',
        'salud ginecológica y general, que responden otra pregunta: si la severidad depende de la situación',
        'ginecológica o de otros problemas de salud.',
    ]
    if sensibles:
        v = max(sensibles, key=lambda x: a.at[x, 'p'])
        p_v = a.at[v, 'p']
        pos_p, pos_t = int((principal['p'] <= p_v).sum()), int((a['p'] <= p_v).sum())
        out += [
            'Si se corrigieran todas juntas, estas variables dejarían de ser significativas aunque sus datos',
            'no cambien:',
            '',
            _tabla(['Variable', 'p original', f'p ajustado ({n_p} principales)', f'p ajustado (las {n_t} juntas)'],
                   [(V.etiqueta(x), _p(a.at[x, 'p']), _p(a.at[x, 'p_ajustado']), _p(r['fdr_conjunta'][x]))
                    for x in sensibles]),
            '',
            f'Por ejemplo, {V.etiqueta(v).lower()} (p = {p_v:.5f}) queda en el puesto {pos_p} con las {n_p} '
            f'principales: {p_v:.5f} × {n_p} / {pos_p} = {p_v * n_p / pos_p:.3f}. Las pruebas nuevas tienen p '
            f'grandes y quedan al final del orden, así que sigue en el puesto {pos_t}, pero ahora se multiplica '
            f'por {n_t}: {p_v:.5f} × {n_t} / {pos_t} = {p_v * n_t / pos_t:.3f}, y cruza el límite de 0,05. '
            'Agregar pruebas que no encuentran nada sube la exigencia para todas, y las primeras en caer son las '
            'que estaban cerca del borde.',
            '',
        ]
    out += [
        'Por eso cada familia se corrige por separado. Es una decisión metodológica que conviene validar con',
        'la profesora.',
        '',
        '### 6.2 Resultados',
        '',
    ]
    return out


def _seccion_asociacion(r, num):
    spear, sig, kr = r['spear'], r['sig'], r['kruskal']
    alcohol = spear.set_index('variable').loc['alcohol_frecuencia']
    return [
        '## 6. Asociación de cada variable con la severidad',
        '',
        'Ordinales, continuas y binarias: correlación de Spearman con la severidad (0-3). Categóricas de más',
        'de dos valores: Kruskal-Wallis con épsilon² como tamaño de efecto. Las preguntas que dependen de',
        'otra valen 0 cuando la madre es "no". Corrección FDR sobre las pruebas principales (sección 6.1).',
        'El IMC numérico se prueba solo en quienes lo informaron.',
        '',
        *_explicacion_fdr(r),
        *_figura(next(num), f'{FIG}/asociacion_severidad.png', 'Correlación de cada variable con la severidad',
                 'Rojo: más severidad; azul: menos severidad; gris: no significativa.',
                 como='cada barra es la rho de Spearman y su valor va al final de la barra (en gris claro si '
                 'no es significativa). Una rho de 0,2 es una asociación débil pero real con este tamaño de '
                 'muestra. Las barras grises cercanas a ±0,10 (como alcohol) quedaron cerca del límite de '
                 'significancia: su p ajustado está en la tabla siguiente.'),
        f'**{len(sig)} de {len(spear)}** correlaciones son significativas (FDR < 0,05):',
        '',
        _tabla(['Variable', 'Rol', 'n', 'rho', 'p ajustado'],
               [(V.ETIQUETAS.get(t.variable) if t.variable != 'imc' else 'IMC (solo informadas)',
                 t.rol, t.n, f'{t.efecto:+.2f}', _p(t.p_ajustado)) for t in sig.itertuples()]),
        '',
        'Las variables categóricas de más de dos valores:',
        '',
        _tabla(['Variable', 'n', 'ε²', 'p ajustado'],
               [(V.etiqueta(t.variable), t.n, f'{t.efecto:.3f}', _p(t.p_ajustado)) for t in kr.itertuples()]),
        '',
        '**Lectura.** El ejercicio (en días y en bajo impacto), el agua y un lugar de trabajo comprensivo',
        'van con menos severidad; el IMC, el estrés laboral, la diabetes y el tabaco, con más. Es lo que se',
        'esperaba del diseño del conjunto sintético (supuestos §13), con efectos débiles como en la',
        'literatura. Ningún alimento sale protector. El alcohol va en la dirección esperada '
        f'(rho = {alcohol.efecto:+.2f}) pero ' + ('no alcanza significación tras la corrección '
        f'(p ajustado = {_p(alcohol.p_ajustado)}).' if alcohol.p_ajustado >= 0.05 else 'también es significativo.'),
        '',
        '**Salud ginecológica y general.** Se agregan para ver si la severidad depende de la situación',
        'ginecológica o de otros problemas de salud. Su corrección FDR se hace aparte, por las razones de la',
        'sección 6.1. Las preguntas de menstruación, sangrado y método',
        'anticonceptivo solo las responde quien aún menstrúa, por eso su n es menor.',
        '',
        _tabla(['Variable', 'n', 'Prueba', 'Efecto', 'p ajustado'],
               [(V.etiqueta(t.variable), t.n, t.prueba, f'{t.medida} = {t.efecto:+.3f}', _p(t.p_ajustado))
                for t in r['asoc'][r['asoc']['rol'].isin(['ginecológica', 'salud'])].itertuples()]),
        '',
        'Ninguna se asocia con la severidad. Es lo esperable en este conjunto: el simulador (Fase 34A,',
        'supuestos §13) no les dio efecto sobre el MRS, porque la profesora no las validó como factores. Con',
        'datos reales podrían aparecer (por ejemplo, el sangrado abundante en la perimenopausia), así que no',
        'se descartan como variables: el resultado nulo es del diseño de la simulación, no un hallazgo.',
        '',
        *_figura(next(num), f'{FIG}/matriz_significativas.png',
                 'Matriz de Spearman entre la severidad y las variables significativas',
                 'Azul: correlación negativa; rojo: positiva.',
                 muestra='las variables significativas casi no se correlacionan entre sí: cada una aporta '
                 'información distinta.'),
        f'**Redundancia.** En la matriz completa ({r["n_matriz"]} variables, Anexo B) los pares con '
        '|rho| ≥ 0,8 son: '
        + ('; '.join(f'{V.etiqueta(a).lower()} y {V.etiqueta(b).lower()} ({c:+.2f})' for a, b, c in r['redundantes'])
           or 'ninguno')
        + '. Los del cuidado son esperables, porque valen 0 para quien no cuida. La Fase 35 debe quedarse con '
        'una variable de cada grupo redundante.',
        '',
    ]


def _seccion_direccion(r, num):
    ej = r['sev_ejercicio']
    return [
        '## 7. Dirección de las asociaciones',
        '',
        *_figura(next(num), f'{FIG}/direccion.png', 'Media de cada variable significativa según la severidad',
                 'Puntos: media en cada clase; barras: IC 95 %.',
                 como='si la línea sube, a mayor severidad mayor valor de la variable.'),
        'Las variables no significativas tienen el mismo gráfico en el Anexo A, agrupadas por bloque.',
        '',
        '### 7.1 Ejercicio',
        '',
        _tabla(['Días de ejercicio', 'n'] + V.ORDEN_SEVERIDAD + ['MRS medio'],
               [(g, int(f['n']), *[f'{f[s]:.1f} %' for s in V.ORDEN_SEVERIDAD], _f(f['mrs_medio']))
                for g, f in ej.iterrows()]),
        '',
        *_figura(next(num), f'{FIG}/ejercicio_severidad.png', 'Severidad según días de ejercicio a la semana',
                 'Barras 100 % apiladas por clase de severidad.',
                 muestra=f'de las que no hacen ejercicio, {ej["Severa"].iloc[0]:.0f} % está en la clase severa; '
                 f'con 3 días o más baja a alrededor de un tercio. Más de la mitad de la muestra '
                 f'({_pct(ej["n"].iloc[0], ej["n"].sum())}) no hace ejercicio, y los grupos de 5-6 días y todos '
                 'los días son pequeños.'),
    ]


def _seccion_consecuencias(r, num):
    c = r['conse']
    return [
        '## 8. Consecuencias de los síntomas',
        '',
        'Estas preguntas miden qué les pasa a las participantes *por* los síntomas. No se usan para explicar',
        'la severidad (sería circular), pero muestran cuánto pesa el climaterio en el trabajo y la pareja.',
        'Las preguntas laborales solo las responden quienes trabajan.',
        '',
        _tabla(['Consecuencia', 'n', 'rho con la severidad', 'p ajustado'],
               [(V.etiqueta(t.variable), t.n, f'{t.efecto:+.2f}', _p(t.p_ajustado)) for t in c.itertuples()]),
        '',
        *_figura(next(num), f'{FIG}/consecuencias.png', 'Consecuencias según la severidad',
                 'Media de cada consecuencia en cada clase (IC 95 %).',
                 muestra='todas suben con la severidad, y con correlaciones mucho más fuertes que las de los '
                 'hábitos: el rendimiento y el bienestar en el trabajo son los más afectados.'),
    ]
