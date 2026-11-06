"""
Fase 34D (OB2): análisis univariado variable por variable (reunión 2026-10-27).

Uso:
    python analisis/eda_univariado.py

Necesita el conjunto limpio de la Fase 34B (python analisis/limpiar_dataset.py).
Escribe:
  - analisis/figuras/eda_univariado/univariado_<variable>.png (barras verticales,
    300 dpi) y, en las numéricas, univariado_<variable>_distribucion.png
    (histograma + KDE + caja, con asimetría y curtosis) y una sola
    univariado_numericas_puntos.png (swarm plot de las 6 numéricas)
  - analisis/resultados/usuaria/{eda_univariado_resumen,frecuencias_univariado,
    faltantes_por_variable}.csv
  - analisis/informe_eda_univariado.md

No imputa nada nuevo: describe los datos tal como quedaron tras la limpieza, con las imputaciones de la 34B.
Cuidado: borra las figuras de FIGURAS antes de redibujarlas; conserve una copia de las históricas. El
conjunto verdadero y la bitácora de suciedad no se leen.
"""
from datetime import date

import pandas as pd

from eda import univariado as U
from eda import variables as V
from eda.informe import _tabla
from limpieza import catalogo

ANALISIS = V.RAIZ / 'analisis'
FIGURAS = ANALISIS / 'figuras' / 'eda_univariado'
RESULTADOS = ANALISIS / 'resultados' / 'usuaria'
GUARDAR = dict(index=False, encoding='utf-8-sig', float_format='%.4f')


def main():
    df, diccionario = V.cargar(V.LIMPIO_USUARIA, 'dataset_usuaria_limpio.csv')
    campos, _ = catalogo.leer_modelos()
    comunas = catalogo.leer_comunas()['04']
    mrs = U.preparar(df)
    FIGURAS.mkdir(parents=True, exist_ok=True)
    RESULTADOS.mkdir(parents=True, exist_ok=True)
    for viejo in FIGURAS.glob('*.png'):
        viejo.unlink()

    resumen, frec = U.describir(mrs, campos, comunas, diccionario)
    numericas = []
    for f in resumen.itertuples():
        U.figura(frec[frec['variable'] == f.variable], f, FIGURAS / f'univariado_{f.variable}.png')
        if f.tipo.startswith('numérica'):
            x = V.numerica(mrs[f.variable]).dropna()
            U.figura_distribucion(x, f, FIGURAS / f'univariado_{f.variable}_distribucion.png')
            numericas.append((x, f))
    U.figura_puntos(numericas, FIGURAS / 'univariado_numericas_puntos.png')

    columnas = ['variable', 'etiqueta', 'seccion_encuesta', 'tipo', 'unidad', 'n_valido', 'n_faltante',
                'porcentaje_faltante', 'n_categorias', 'categoria_dominante', 'porcentaje_dominante',
                'entropia_shannon_bits', 'baja_variabilidad', 'ruta_figura', 'comentario']
    extra = ['denominador', 'n_aplica', 'n_no_aplica', 'entropia_normalizada', 'imputados_34B',
             'pct_dominante_sin_imputados_34B', *U.FORMA]
    resumen[columnas + extra].to_csv(RESULTADOS / 'eda_univariado_resumen.csv', **GUARDAR)
    frec.to_csv(RESULTADOS / 'frecuencias_univariado.csv', **GUARDAR)
    falt = resumen[['variable', 'etiqueta', 'seccion_encuesta', 'denominador', 'n_aplica', 'n_no_aplica',
                    'n_valido', 'n_faltante', 'porcentaje_faltante', 'imputados_34B', 'tratamiento_34B']]
    falt.sort_values('porcentaje_faltante', ascending=False).to_csv(
        RESULTADOS / 'faltantes_por_variable.csv', **GUARDAR)

    (ANALISIS / 'informe_eda_univariado.md').write_text(informe(resumen, len(df), len(mrs)), encoding='utf-8')
    print(f'{len(resumen)} variables descritas sobre {len(mrs)} participantes; '
          f'{(resumen["baja_variabilidad"] == "sí").sum()} con baja variabilidad (≥ 80 %)')
    print('Informe: analisis/informe_eda_univariado.md')


def _pct(x):
    return f'{x:.1f}'.replace('.', ',') + ' %'


def _num(x, signo=True):
    return (f'{x:+.2f}' if signo else f'{x:.1f}').replace('.', ',')


def distribucion_numericas(resumen):
    """Sección 4: tabla de forma (asimetría y curtosis) de las variables numéricas."""
    num = resumen[resumen['tipo'].str.startswith('numérica')]
    return [
        '## 4. Distribución de variables numéricas y asimetría',
        '',
        'Las variables numéricas (edad, peso, talla, IMC, horas sentada al día y puntaje MRS total) se muestran '
        'en intervalos en su figura principal y, además, en una figura de distribución con tres elementos:',
        '',
        '- **Histograma** de los valores observados (intervalos de 1 unidad en las discretas; 25 intervalos '
        'iguales en las continuas).',
        '- **Curva de densidad (KDE)**: estimación de densidad por núcleo gaussiano (`scipy.stats.gaussian_kde`, '
        'ancho de banda de Scott). Suaviza el histograma para ver la forma sin depender de dónde caen los cortes '
        'de los intervalos. Se escala a participantes por intervalo (n × ancho) para leerla sobre el mismo eje. '
        'En el MRS total y las horas sentada (valores enteros) la curva es una aproximación continua de una '
        'variable discreta. No se dibuja KDE en las preguntas ordinales con pocas opciones (por ejemplo, días de '
        'ejercicio), porque inventaría valores intermedios que no existen.',
        '- **Diagrama de caja** con la regla de Tukey (Q1 − 1,5 × RIC, Q3 + 1,5 × RIC) para ubicar posibles '
        'atípicos. Como en la Fase 34, un atípico estadístico no es un error: se conserva si es clínicamente '
        'posible.',
        '',
        '**Cómo se calculan.** *Asimetría*: coeficiente de Fisher-Pearson ajustado por tamaño muestral (G1, '
        '`pandas.Series.skew`). *Curtosis*: exceso de curtosis ajustado (G2, `pandas.Series.kurt`), que vale 0 '
        'en una distribución normal. Se calculan sobre los valores disponibles tras la limpieza: en peso, talla e IMC, '
        'solo de quienes los informaron; en horas sentada se incluyen los valores imputados en la Fase 34B.',
        '',
        _tabla(['Variable', 'n', 'Media', 'DE', 'Mediana', 'Mín.', 'Máx.', 'Asimetría', 'Curtosis',
                'Atípicos (Tukey)', 'Lectura'],
               [[t.etiqueta, t.n_valido, _num(t.media, False), _num(t.desviacion_estandar, False),
                 _num(t.mediana, False), _num(t.minimo, False), _num(t.maximo, False), _num(t.asimetria),
                 _num(t.curtosis), int(t.atipicos_tukey),
                 f'{U.leer_asimetria(t.asimetria)}; {U.leer_curtosis(t.curtosis)}']
                for t in num.itertuples()]),
        '',
        '**Cómo leerla.** Asimetría: |G1| < 0,5 = aproximadamente simétrica; entre 0,5 y 1 = moderada; > 1 = '
        'marcada. Positiva = cola hacia los valores altos (la media queda sobre la mediana); negativa = cola hacia '
        'los bajos. Curtosis: |G2| < 1 = colas parecidas a la normal; > 1 = colas pesadas (más valores extremos); '
        '< −1 = distribución achatada. Estos criterios son orientativos y sirven para elegir el escalado de la '
        'Fase 36: con asimetría marcada o colas pesadas conviene el escalado robusto (mediana y RIC) en vez de '
        'media y DE.',
        '',
        '**Figura 4.1. Variables numéricas: un punto por participante (swarm plot)**',
        '',
        '![Swarm plot de las variables numéricas](figuras/eda_univariado/univariado_numericas_puntos.png)',
        '',
        '**Qué muestra.** Cada punto es una participante, ubicada según su valor. Así se ven todas las '
        'observaciones (no solo su resumen): dónde se concentran, si hay huecos y cuáles quedan lejos del resto. '
        'La caja marca la mediana y los cuartiles; los puntos rojos están fuera de la regla de Tukey '
        '(1,5 × RIC) y son los posibles atípicos que cuenta la tabla. La altura de cada punto es aleatoria '
        '(semilla 42) y solo sirve para que no se tapen entre sí: el eje vertical no significa nada. Se usa este '
        'desplazamiento aleatorio en vez de un enjambre exacto porque con valores enteros repetidos (edad, MRS) '
        'el enjambre se vuelve demasiado ancho para leerse.',
        '',
        '**Por qué solo estas seis.** Son las únicas variables numéricas. El resto son categóricas (sí/no, '
        'escalas de pocas opciones u opciones sin orden): en ellas todos los puntos se apilarían en unas pocas '
        'columnas, repitiendo el gráfico de barras, y el concepto de atípico no aplica, porque toda respuesta es '
        'una opción válida de la encuesta. Para ellas lo relevante es si una categoría es rara o dominante, y '
        'eso lo muestran las barras de la sección 5.',
        '',
    ]


def informe(resumen, n_total, n_mrs):
    baja = resumen[resumen['baja_variabilidad'] == 'sí'].sort_values('porcentaje_dominante', ascending=False)
    falt = resumen[resumen['n_faltante'] > 0].sort_values('porcentaje_faltante', ascending=False)
    out = [
        '# Fase 34D. Análisis univariado variable por variable',
        '',
        f'*Generado por `analisis/eda_univariado.py` el {date.today():%d-%m-%Y}. Conjunto: '
        '`datos/limpio_usuaria/dataset_usuaria_limpio.csv` (Fase 34B).*',
        '',
        '## 1. Propósito y criterios',
        '',
        'Acordado en la reunión del 27-10-2026: antes del análisis multivariado se describe cada variable por '
        'separado, con un gráfico de barras verticales que muestra el porcentaje y la frecuencia absoluta de cada '
        'respuesta. El objetivo es ver qué variables tienen una respuesta que domina (80 % o más) y dónde hay '
        'vacíos, antes de filtrar e imputar en la Fase 35A.',
        '',
        f'- **Participantes.** Se describen las {n_mrs} participantes con las 11 preguntas del MRS completas '
        f'(de {n_total} tras la limpieza). Las {n_total - n_mrs} restantes no entran a los análisis con la '
        'variable objetivo.',
        '- **Sin imputaciones nuevas.** Los gráficos muestran los datos tal como quedaron tras la limpieza, que ya '
        'incluyen las imputaciones de la Fase 34B, y sus subtítulos las separan. El IMC se muestra solo para quienes informaron peso y talla, en los '
        'intervalos de la OMS, sin una categoría "no informado".',
        '- **Denominadores.** Preguntas generales: todas las participantes. Preguntas condicionales: solo quienes '
        'debían responder (por ejemplo, la frecuencia de fuerza solo entre quienes hacen fuerza; las preguntas de '
        'trabajo solo entre quienes trabajan; las de menstruación solo entre quienes aún menstrúan). Selección '
        'múltiple: quienes respondieron; los porcentajes pueden sumar más de 100.',
        '- **Faltante.** Participante que debía responder y no tiene dato. Quien no debía responder ("no aplica") '
        'no cuenta como faltante.',
        '- **Orden de las barras.** Escalas en su orden lógico; categorías nominales de mayor a menor frecuencia. '
        'Las categorías sin casos se muestran con "0,0 % (n = 0)".',
        f'- **Baja variabilidad.** Una categoría reúne el {U.UMBRAL_BAJA_VARIABILIDAD} % o más de las respuestas '
        'válidas (criterio de la profesora). Decisión de la usuaria (28-10-2026): solo se eliminan en la Fase 35A '
        'las que **superan el 85 %**; entre 80 % y 85 % se conservan por su relevancia.',
        '- **Entropía de Shannon** (bits): H = −Σ p·log₂(p) sobre las respuestas válidas. Vale 0 si todas '
        'responden lo mismo y log₂(k) si las k categorías se reparten igual; la entropía normalizada (H / log₂ k) '
        'va de 0 a 1.',
        '- **Imputación de la Fase 34B.** La limpieza imputó por moda o mediana hasta un 7 % de algunas '
        'preguntas. Para no esconder ese efecto, el resumen trae la dominancia que quedaría sin esos valores '
        '(`pct_dominante_sin_imputados_34B`) y el comentario avisa si cambia de tramo.',
        '',
        '## 2. Variables con baja variabilidad',
        '',
        _tabla(['Variable', 'Sección', 'Categoría dominante', '% dominante', 'Entropía (bits)', 'Tramo'],
               [[t.etiqueta, t.seccion_encuesta, t.categoria_dominante, _pct(t.porcentaje_dominante),
                 f'{t.entropia_shannon_bits:.2f}',
                 '> 85 %: candidata a eliminar' if t.porcentaje_dominante > 85 else '80-85 %: se conserva']
                for t in baja.itertuples()]),
        '',
        'La decisión final de cada una (con las excepciones justificadas) está en la Fase 35A '
        '(`resultados/usuaria/variables_baja_variabilidad.csv`). Las de la sección MRS y la variable objetivo '
        'no se filtran: se describen como referencia.',
        '',
        '## 3. Faltantes',
        '',
        _tabla(['Variable', 'Debían responder', 'Faltantes', '% faltante'],
               [[t.etiqueta, t.n_aplica, t.n_faltante, _pct(t.porcentaje_faltante)] for t in falt.itertuples()]),
        '',
        'Peso, talla e IMC concentran los vacíos (muchas participantes no informan sus medidas). Las preguntas de '
        'menstruación tienen como faltantes a las participantes sin fecha de última menstruación: no se sabe si '
        'les correspondía responder.',
        '',
        *distribucion_numericas(resumen),
        '## 5. Una figura por variable',
        '',
    ]
    numero = 1
    for seccion in U.SECCIONES.values():
        bloque = resumen[resumen['seccion_encuesta'] == seccion]
        if bloque.empty:
            continue
        out += [f'### 5.{list(U.SECCIONES.values()).index(seccion) + 1}. {seccion}', '']
        for t in bloque.itertuples():
            out += [f'**Figura {numero}. {t.etiqueta}** (`{t.variable}`)', '',
                    f'![{t.etiqueta}]({t.ruta_figura})', '', t.comentario, '']
            numero += 1
            if t.tipo.startswith('numérica'):
                ruta = t.ruta_figura.replace('.png', '_distribucion.png')
                out += [f'**Figura {numero}. {t.etiqueta}: distribución**', '',
                        f'![{t.etiqueta}: distribución]({ruta})', '',
                        f'Histograma con curva de densidad (KDE) y caja de los valores observados (apoyo para la '
                        f'versión en intervalos). Asimetría {_num(t.asimetria)}: {U.leer_asimetria(t.asimetria)}; '
                        f'curtosis {_num(t.curtosis)}: {U.leer_curtosis(t.curtosis)}.', '']
                numero += 1
    out += ['## 6. Variables que no se describen', '',
            _tabla(['Motivo', 'Variables'], [[m, ', '.join(f'`{v}`' for v in vs)] for m, vs in U.EXCLUIDAS.items()]),
            '']
    return '\n'.join(out)


if __name__ == '__main__':
    main()
