"""Informe de la Fase 34E en Markdown (analisis/informe_eda_multivariado.md)."""
from datetime import date

import pandas as pd

from . import multivariado as M
from . import variables as V
from .informe import _tabla

FIG = 'figuras/eda_multivariado'


def _n(x, d=2, signo=False):
    if pd.isna(x):
        return '—'
    return (f'{x:+.{d}f}' if signo else f'{x:.{d}f}').replace('.', ',')


def _p(p):
    return '< 0,001' if p < 0.001 else _n(p, 3)


def _pi(p):
    """'p = 0,028' o 'p < 0,001'."""
    return f'p {_p(p)}' if p < 0.001 else f'p = {_p(p)}'


def _min(nombre):
    """Minúscula inicial salvo siglas (IMC)."""
    return nombre if nombre[:2].isupper() else nombre[0].lower() + nombre[1:]


def _figura(numero, archivo, titulo, pie):
    return [f'**Figura {numero}. {titulo}**', '', f'![{titulo}]({FIG}/{archivo})', '', f'*{pie}*', '']


def generar(r):
    num = iter(range(1, 100))
    datos, pares, grupos, resumen = r['datos'], r['pares'], r['grupos'], r['resumen']
    n_pred = len(r['predictoras'])
    nominales = [v for v in r['predictoras'] if r['tipos'][v] == 'nominal']
    out = [
        '# Fase 34E. Análisis multivariado exploratorio',
        '',
        f'*Generado por `analisis/eda_multivariado.py` el {date.today():%d-%m-%Y}. Entradas: '
        '`datos/analitico/dataset_fase35.csv` (Fase 35A) y `datos/analitico/conjunto_eda_usuaria.csv` (Fase 34C).*',
        '',
        '## 1. Propósito',
        '',
        'Las fases anteriores miraron las variables de a una (34D) o de a dos, cada una contra la severidad (34C). '
        'Esta fase agrega dos miradas:',
        '',
        '1. **Cómo se relacionan las variables entre ellas**: una matriz de asociación de las predictoras y los '
        'grupos de variables que "dicen lo mismo". Esto importa para la selección de variables (Fase 35B) y para '
        'el PCA (Fase 37): variables muy relacionadas aportan información repetida.',
        '2. **Cómo actúan juntas sobre la severidad**: la severidad según dos variables a la vez (tríadas), para '
        'ver si el efecto de una se mantiene al tener en cuenta la otra y si el efecto de una cambia según la otra.',
        '',
        'Todo es **exploratorio**: describe y genera hipótesis; no confirma causas.',
        '',
        '## 2. Datos y decisiones de preparación',
        '',
        f'- **Participantes:** {len(datos)} con el MRS completo.',
        f'- **Variables:** las {n_pred} predictoras que dejó la Fase 35A, más la severidad del MRS en 4 clases '
        '(0 = sin síntomas o muy leves … 3 = severa) como referencia. La severidad no se agrupa con las demás: '
        'solo se muestra cuánto se asocia cada predictora con ella.',
        '- **Sin imputaciones.** Se usa lo que las participantes respondieron:',
        '  - **IMC observado** (n = '
        f'{int(datos["imc"].notna().sum())}). La Fase 35A imputó el resto con la media; aquí no se usa ese valor, '
        'porque pondría a la mitad de la muestra en un mismo IMC y crearía asociaciones falsas.',
        '  - **"No aplica" queda fuera del par.** Las preguntas de trabajo para quien no trabaja y las de '
        'menstruación para quien ya no menstrúa no tienen una respuesta en la escala: esas participantes no '
        'entran en los pares de esa pregunta.',
        '  - **Respuestas laborales originales.** Las 22 trabajadoras sin respuesta en la sección Trabajo, '
        'imputadas por mediana en la 35A, quedan fuera de esos pares.',
        '  - Las frecuencias de ejercicio y la cantidad de personas que cuida valen 0 cuando la participante no '
        'lo hace: ese 0 **sí** es un valor real de la escala ("frecuencia cero") y se conserva.',
        '',
        '## 3. Matriz de asociación',
        '',
        '### 3.1 ¿Qué es y para qué sirve?',
        '',
        f'Una **matriz de asociación** es una tabla cuadrada con las {n_pred + 1} variables en las filas y las '
        'mismas en las columnas. Cada casilla dice qué tan relacionadas están dos variables, de 0 (nada) a 1 '
        '(totalmente). Sirve para detectar variables que dicen lo mismo y para ver con qué se asocia cada una.',
        '',
        '### 3.2 Por qué no se usa la correlación de Pearson',
        '',
        'La **correlación de Pearson** mide si dos números suben juntos en línea recta. Sirve para cantidades '
        'medidas, pero no para respuestas codificadas: si a la previsión "Fonasa, Isapre, FF.AA." se le asignan '
        'los códigos 1, 2 y 3, esos números son etiquetas, no cantidades (Isapre no es "el doble" de Fonasa). '
        'Pearson trataría esos códigos como medidas y el resultado no tendría interpretación. Por eso se usa una '
        'medida distinta según el tipo de cada par.',
        '',
        '### 3.3 Las tres medidas',
        '',
        _tabla(['Par de variables', 'Medida', 'Qué mide', 'Se lee', 'Pares'],
               [['Numérica, ordinal o sí/no × numérica, ordinal o sí/no', '**ρ de Spearman**',
                 'Ordena a las participantes de menor a mayor en cada variable (**rangos**) y mide si los órdenes '
                 'coinciden. Detecta relaciones **monótonas** ("cuando una sube, la otra tiende a subir"), aunque '
                 'no sean en línea recta. Respeta el orden de las escalas sin suponer distancias iguales.',
                 '−1 a +1; el signo da la dirección', int((pares['medida'] == 'rho de Spearman').sum())],
                ['Nominal × nominal', '**V de Cramér** con corrección de sesgo (Bergsma)',
                 'Parte de la **tabla de contingencia** (cuántas hay en cada combinación de respuestas) y la '
                 'compara con lo esperable si no hubiera relación (**chi-cuadrado**). La corrección evita que '
                 'la V se infle con muchas categorías o grupos chicos.',
                 '0 a 1, sin signo', int((pares['medida'] == 'V de Cramér corregida').sum())],
                ['Nominal × numérica u ordinal', '**Razón de correlación η (eta)**, sobre rangos',
                 'Mide si los grupos de la nominal tienen valores distintos en la otra (por ejemplo, ¿cada etapa '
                 'menopáusica tiene una edad distinta?). Se calcula sobre rangos; su prueba es la de '
                 '**Kruskal-Wallis**. Usa la variable completa, sin cortarla en tramos como en la 35A.',
                 '0 a 1, sin signo', int((pares['medida'] == 'eta (rangos)').sum())]]),
        '',
        f'Las variables nominales son {len(nominales)}: ' + ', '.join(V.etiqueta(v) for v in nominales) + '.',
        '',
        '- **Pares completos.** Cada par se calcula con las participantes que respondieron **ambas** preguntas '
        '(por eso el n cambia de un par a otro; está en `pares_asociacion_mixta.csv`).',
        '- **Comparables, pero no idénticas.** Las tres medidas van de 0 a 1 en valor absoluto y se pueden mirar '
        'juntas en la matriz, pero no son exactamente la misma cosa. La η tiende a salir algo más alta con '
        'muchos grupos y pocas participantes: por eso cada par trae también su valor p.',
        f'- **Corrección FDR.** Con {len(pares)} pares, algunos saldrían "significativos" por puro azar. El '
        '**p ajustado** (Benjamini-Hochberg, igual que en la 34C) corrige eso. Como aquí se corrige sobre muchos '
        'más pares, los p ajustados de la severidad son más altos que en la 34C; para la asociación con la '
        'severidad, la referencia sigue siendo la 34C.',
        '',
        '### 3.4 Resultados',
        '',
        *_figura(next(num), 'matriz_asociacion.png', f'Matriz de asociación de las {n_pred} predictoras y la severidad',
                 'Color: |asociación|. Se anotan los valores de 0,30 o más (con signo cuando es Spearman). '
                 'Orden: el de la encuesta.'),
        '**Cómo leerla.** Cada casilla cruza la variable de su fila con la de su columna; la diagonal es la '
        'variable consigo misma (siempre 1). Cuanto más oscura, más relacionadas. La matriz es simétrica: la '
        'mitad de arriba repite la de abajo.',
        '',
        *_seccion_pares(pares),
        '## 4. Grupos de variables relacionadas',
        '',
        '### 4.1 ¿Cómo se buscan?',
        '',
        '- **Agrupamiento jerárquico** (*clustering jerárquico*) de variables: trata la asociación como cercanía. '
        'Junta primero las dos variables más cercanas, después la siguiente más cercana, y así hasta unir todas.',
        '- **Distancia = 1 − |asociación|.** Dos variables muy asociadas quedan cerca (distancia cercana a 0); '
        'dos sin relación quedan lejos (distancia 1). Un par sin valor (sin participantes en común) cuenta como '
        'sin relación.',
        '- **Enlace promedio** (*average linkage*): al unir dos grupos se usa la distancia promedio entre todos '
        'sus miembros. Así, un solo par muy asociado no arrastra a todo un grupo.',
        '- **Dendrograma:** el árbol que muestra en qué orden y a qué distancia se fueron uniendo las variables. '
        f'Se **corta** a una asociación promedio de {_n(M.CORTE_GRUPO)} (distancia {_n(1 - M.CORTE_GRUPO)}): lo '
        'que queda unido bajo esa línea es un grupo. El corte es una convención (asociación "moderada"); se '
        'puede cambiar en `eda/multivariado.py` (`CORTE_GRUPO`).',
        '',
        '### 4.2 Resultados',
        '',
        *_figura(next(num), 'grupos_variables.png', 'Grupos de variables relacionadas',
                 'Izquierda: dendrograma (línea roja: corte). Derecha: la misma matriz, con las variables en el '
                 'orden del árbol; los recuadros rojos son los grupos.'),
        '**Cómo leerla.** En el árbol, cuanto más a la derecha se unen dos ramas, más asociadas están. En la '
        'matriz reordenada, los grupos aparecen como bloques oscuros pegados a la diagonal.',
        '',
        *_seccion_grupos(grupos, n_pred),
        '## 5. Relaciones entre tres variables (tríadas)',
        '',
        '### 5.1 Conceptos',
        '',
        '- **Análisis estratificado:** en vez de mirar "IMC vs. severidad" y "ejercicio vs. severidad" por '
        'separado, se mira la severidad en **cada combinación** de las dos variables (por ejemplo, obesas que no '
        'hacen ejercicio vs. obesas que sí). Permite responder dos preguntas:',
        '  - **Ajuste (control):** ¿el efecto de una variable se mantiene cuando se tiene en cuenta la otra? Si '
        'el IMC se asociara con la severidad solo porque las de IMC alto hacen menos ejercicio, al descontar el '
        'ejercicio su efecto desaparecería.',
        '  - **Interacción:** ¿el efecto de una variable cambia según la otra? Por ejemplo, que el ejercicio '
        'proteja mucho a las mujeres con obesidad y poco a las de peso normal.',
        '- **Regresión logística ordinal** (*modelo de odds proporcionales*): un modelo que predice la clase de '
        'severidad respetando su orden (muy leve < leve < moderada < severa) a partir de las dos variables. '
        'Entrega un **odds ratio (OR)** por categoría, comparado con una **categoría de referencia** (la primera '
        'de cada variable):',
        '  - OR = 1: sin diferencia con la referencia; OR > 1: más chances de estar en una clase más severa '
        '(OR = 2, el doble); OR < 1: menos chances (efecto protector; OR = 0,5, la mitad).',
        '  - **IC 95 %** (intervalo de confianza): el rango de valores plausibles para el OR. Si incluye el 1, '
        'la diferencia puede ser azar.',
        '- **Término de interacción** y **prueba de razón de verosimilitud:** se ajusta el modelo dos veces, con '
        'y sin la combinación A × B, y se compara qué tan bien explica cada uno los datos. Si agregar la '
        'interacción no mejora el ajuste de forma significativa, los efectos simplemente se suman.',
        '- **Supuesto de odds proporcionales:** el modelo supone que cada variable tiene un efecto parecido en '
        'cada "escalón" de severidad. Se revisa ajustando tres regresiones logísticas simples (leve o más; '
        'moderada o más; severa) y comparando sus OR: si son parecidos, el supuesto es razonable (§5.7).',
        '- **Correlación parcial de Spearman:** la relación de una variable con la severidad **descontando** la '
        'otra. Si casi no cambia respecto de la ρ simple, la segunda variable no explica el efecto de la primera.',
        '- **Corrección FDR** sobre las 4 pruebas de interacción, para no encontrar efectos por azar.',
        '- **Potencia estadística** (capacidad de detectar un efecto que sí existe): con muchas combinaciones de '
        'menos de 30 participantes, es **baja**. Una interacción real pero moderada puede no salir significativa. Las '
        f'combinaciones con menos de {M.MINIMO_CELDA} participantes se muestran en gris y con asterisco.',
        '',
        '### 5.2 Categorías usadas',
        '',
        'Para que cada combinación tenga participantes suficientes, las respuestas se agrupan en pocas '
        'categorías. La primera de cada variable es la referencia de los OR.',
        '',
        _tabla(['Tríada', 'Variable A (categorías)', 'Variable B (categorías)', 'Participantes'],
               [[t['titulo'],
                 f'{t["a"][1]}: ' + ' / '.join(M.preparar_triada(datos, t)[1]),
                 f'{t["b"][1]}: ' + ' / '.join(M.preparar_triada(datos, t)[2]),
                 f'{int(s.n)} ({t["quienes"]})'] for t, s in zip(M.TRIADAS, resumen.itertuples())]),
        '',
        'El IMC sigue los cortes de la OMS (normal < 25; sobrepeso 25-29,9; obesidad ≥ 30; solo 2 participantes '
        'con bajo peso, incluidas en "normal"). La doble carga, entre trabajadoras, equivale a cuidar a otras '
        'personas.',
        '',
    ]
    for i, (t, s) in enumerate(zip(M.TRIADAS, resumen.itertuples()), start=3):
        out += _seccion_triada(i, t, s, r['estratos'], r['modelos'], num)
    out += _seccion_supuesto(r['modelos'])
    out += _seccion_resumen(pares, grupos, resumen, r['modelos'])
    return '\n'.join(out)


def _seccion_pares(pares):
    fuertes = pares[(pares['abs_valor'] >= M.CORTE_GRUPO) & (pares['variable_1'] != M.SEVERIDAD)] \
        .sort_values('abs_valor', ascending=False)
    sev = pares[pares['variable_1'] == M.SEVERIDAD].sort_values('abs_valor', ascending=False).head(10)
    nulos = pares[pares['valor'].isna()]
    debiles = (pares['abs_valor'] < 0.10).mean() * 100
    return [
        f'**Pares con asociación de 0,30 o más** ({len(fuertes)} de {len(pares)}):',
        '',
        _tabla(['Variable 1', 'Variable 2', 'Medida', 'Valor', 'n', 'p ajustado'],
               [[t.etiqueta_1, t.etiqueta_2, t.medida, _n(t.valor, signo=t.medida == 'rho de Spearman'),
                 t.n_par, _p(t.p_ajustado)] for t in fuertes.itertuples()]),
        '',
        f'**Qué muestra.** La gran mayoría de los pares tiene una asociación débil: el {_n(debiles, 0)} % está '
        'bajo 0,10. Las asociaciones fuertes se dan entre variables que miden cosas emparentadas: edad y etapa '
        'menopáusica, las cuatro preguntas de ejercicio, la doble carga con trabajar y con cuidar, pareja y '
        'actividad sexual, y los dos climas laborales (un lugar comprensivo va con menos estrés). '
        + (f'Ninguna supera 0,80 (máximo {_n(pares["abs_valor"].max())}), coherente con el filtro de redundancia de la 35A. '
           if pares['abs_valor'].max() <= 0.80 else 'Hay pares sobre 0,80: revisar el filtro de redundancia de la 35A. ')
        + 'La mayoría de los hábitos (alimentación, '
        'sustancias) son casi independientes entre sí.',
        '',
        (f'Hay {len(nulos)} pares sin valor: ' + ', '.join(f'{M.etiqueta(t.variable_1)} × {M.etiqueta(t.variable_2)}'
                                                         for t in nulos.itertuples())
         + '. Entre quienes responden las preguntas de trabajo, "trabaja actualmente" vale siempre sí: una '
         'variable constante no puede asociarse con nada.') if len(nulos) else '',
        '',
        '**Asociación de cada predictora con la severidad** (las 10 más altas):',
        '',
        _tabla(['Predictora', 'Medida', 'Valor', 'n', 'p ajustado (741 pares)'],
               [[t.etiqueta_2, t.medida, _n(t.valor, signo=t.medida == 'rho de Spearman'), t.n_par,
                 _p(t.p_ajustado)] for t in sev.itertuples()]),
        '',
        'Son las mismas que destacó la 34C (lugar comprensivo, IMC, estrés laboral, ejercicio, diabetes, tabaco, '
        'agua), todas con asociación débil (|ρ| ≤ 0,23). Las η de etapa menopáusica, quién prepara las comidas y '
        'previsión no son significativas.',
        '',
    ]


def _seccion_grupos(grupos, n_pred):
    en_grupo = int(grupos['n_variables'].sum())
    return [
        _tabla(['Grupo', 'Variables', 'Asociación promedio', 'Mínima', 'Máxima', 'Máx. con la severidad'],
               [[t.grupo, t.etiquetas, _n(t.asociacion_promedio), _n(t.asociacion_minima),
                 _n(t.asociacion_maxima), _n(t.max_asociacion_con_severidad)] for t in grupos.itertuples()]),
        '',
        f'**Qué muestra.** Se forman {len(grupos)} grupos, que reúnen a {en_grupo} de las {n_pred} predictoras; '
        f'las otras {n_pred - en_grupo} quedan solas, sin una compañera con asociación moderada. Los grupos tienen '
        'sentido temático:',
        '',
        '- **Actividad física:** los días de ejercicio y las tres frecuencias (aeróbico, bajo impacto, fuerza). '
        'Es el grupo más grande; los días de ejercicio resumen bien a las demás.',
        '- **Carga de cuidado y tiempo:** doble carga, cantidad de personas que cuida y falta de tiempo para '
        'comer bien.',
        '- **Trabajo y comidas fuera:** quienes trabajan comen más fuera del hogar.',
        '- **Etapa de la vida:** edad y etapa menopáusica (la etapa se definió en parte con la edad).',
        '- **Clima laboral:** lugar comprensivo y estrés laboral, en sentido opuesto.',
        '- **Pareja:** tener pareja y tener actividad sexual.',
        '',
        '**Qué implica para las fases siguientes.**',
        '',
        '- **Selección (35B):** dentro de cada grupo las variables comparten información; el FCBF (que descarta '
        'las redundantes con una ya elegida) probablemente se quedará con una o dos por grupo.',
        f'- **PCA (37):** con {n_pred - en_grupo} variables casi independientes, el PCA no podrá resumir los '
        'datos en pocas componentes: cada componente explicará poca varianza. Es una característica del conjunto '
        'sintético (el simulador generó la mayoría de los hábitos de forma independiente), no un error, y conviene '
        'anticiparlo al interpretar la Fase 37.',
        '',
    ]


def _seccion_triada(i, t, s, estratos, modelos, num):
    tabla = estratos[estratos['triada'] == t['clave']]
    ef = modelos[modelos['triada'] == t['clave']]
    confiables = tabla[~tabla['poco_confiable']]
    alta, baja = confiables.loc[confiables['pct_severa'].idxmax()], confiables.loc[confiables['pct_severa'].idxmin()]
    na, nb = t['a'][1], t['b'][1]
    if s.p_interaccion < 0.05 <= s.p_interaccion_ajustado:
        inter = (f'sin corregir, la interacción roza la significancia ({_pi(s.p_interaccion)}), pero tras la '
                 f'corrección FDR no lo es (p ajustado = {_p(s.p_interaccion_ajustado)}). Es una **pista** que '
                 'conviene mirar con más datos, no un hallazgo.')
    elif s.p_interaccion_ajustado < 0.05:
        inter = (f'la interacción es significativa (p ajustado = {_p(s.p_interaccion_ajustado)}): el efecto de '
                 f'una variable cambia según la otra.')
    else:
        inter = (f'no hay evidencia de interacción ({_pi(s.p_interaccion)}; p ajustado = '
                 f'{_p(s.p_interaccion_ajustado)}): los efectos de {_min(na)} y {_min(nb)} se suman, sin '
                 'potenciarse.')
    if not s.interaccion_estable:
        inter += ' Ojo: el modelo con interacción es inestable (combinaciones con muy pocas participantes).'

    def parcial(nombre, simple, par, p):
        cambio = 'casi no cambia' if abs(par - simple) < 0.03 else ('baja' if abs(par) < abs(simple) else 'sube')
        return (f'{nombre}: ρ = {_n(simple, signo=True)}; descontando la otra, ρ parcial = {_n(par, signo=True)} '
                f'({_pi(p)}): {cambio}.')

    return [
        f'### 5.{i} {t["titulo"]}',
        '',
        *_figura(next(num), f'triada_{t["clave"]}.png', f'Severidad según {t["frase"]} a la vez',
                 'Izquierda: % de participantes en la clase severa en cada combinación (n en cada casilla). '
                 'Derecha: las 4 clases de severidad en cada combinación.'),
        f'**Cómo leerla.** En el mapa, recorra una fila para ver el efecto de {_min(nb)} con {_min(na)} fijo, '
        f'y una columna para ver el efecto de {_min(na)} con {_min(nb)} fijo. Si las filas cambian de forma '
        'parecida entre sí, no hay interacción; si en una fila el cambio es mucho mayor que en otra, la hay.',
        '',
        f'**Qué muestra.** Entre las combinaciones con al menos {M.MINIMO_CELDA} participantes, la de más severas '
        f'es «{alta.A} · {alta.B}» ({_n(alta.pct_severa, 0)} %, n = {int(alta.n)}) y la de menos, «{baja.A} · '
        f'{baja.B}» ({_n(baja.pct_severa, 0)} %, n = {int(baja.n)}).',
        '',
        _tabla(['Categoría (vs. referencia)', 'Variable', 'OR', 'IC 95 %', 'p'],
               [[e.termino, na if e.variable == 'A' else nb, _n(e.OR), f'{_n(e.IC95_inf)} a {_n(e.IC95_sup)}',
                 _p(e.p)] for e in ef.itertuples()]),
        '',
        f'*Modelo ordinal aditivo (A + B), n = {int(s.n)}. Referencias: «{tabla["A"].iloc[0]}» y '
        f'«{tabla["B"].iloc[0]}».*',
        '',
        f'- **Interacción:** {inter}',
        f'- **Ajuste.** {parcial(na, s.rho_a, s.rho_a_parcial, s.p_a_parcial)} '
        f'{parcial(nb, s.rho_b, s.rho_b_parcial, s.p_b_parcial)}',
        '',
    ]


def _seccion_supuesto(modelos):
    return [
        '### 5.7 Revisión del supuesto de odds proporcionales',
        '',
        _tabla(['Tríada', 'Categoría', 'OR ordinal', 'OR leve o más', 'OR moderada o más', 'OR severa'],
               [[next(t['titulo'] for t in M.TRIADAS if t['clave'] == e.triada), e.termino, _n(e.OR),
                 _n(e.OR_corte_leve_o_mas), _n(e.OR_corte_moderada_o_mas), _n(e.OR_corte_severa)]
                for e in modelos.itertuples()]),
        '',
        '**Qué muestra.** En los cortes "moderada o más" y "severa" los OR son parecidos al del modelo ordinal: '
        'para esos escalones el supuesto es razonable. El corte "leve o más" es el que más se aparta (a veces '
        'incluso cambia de sentido), porque compara contra la clase "sin síntomas o muy leves", que es chica (56 '
        'participantes en total y aún menos dentro de cada tríada): sus OR son poco precisos. Por eso los OR del '
        'modelo ordinal se leen sobre todo como el efecto de pasar a las clases moderada y severa.',
        '',
    ]


def _resumen_triadas(resumen):
    estables = all(abs(s.rho_a_parcial - s.rho_a) < 0.03 and abs(s.rho_b_parcial - s.rho_b) < 0.03
                   for s in resumen.itertuples())
    sin_inter = (resumen['p_interaccion_ajustado'] >= 0.05).all()
    if estables and sin_inter:
        return ['- **Tríadas:** en las cuatro, cada variable conserva su efecto al descontar la otra (la ρ parcial '
                'casi no cambia) y ninguna interacción es significativa tras la corrección FDR. Es decir, los '
                'factores **se suman**: por ejemplo, la obesidad y no hacer ejercicio aumentan cada uno las '
                'chances de síntomas severos, y juntas dan el mayor % de severas.']
    return ['- **Tríadas:** ' + ('cada variable conserva su efecto al descontar la otra. ' if estables else
                                 'en alguna tríada el efecto de una variable cambia al descontar la otra (ver §5). ')
            + ('Ninguna interacción es significativa tras la corrección FDR.' if sin_inter else
               'Hay al menos una interacción significativa tras la corrección FDR (ver §5).')]


def _seccion_resumen(pares, grupos, resumen, modelos):
    return [
        '## 6. Resumen',
        '',
        '- **Matriz:** la mayoría de las predictoras se relacionan poco entre sí; las asociaciones fuertes son '
        'entre variables del mismo tema y ninguna llega a 0,80.',
        f'- **Grupos:** {len(grupos)} grupos temáticos (actividad física, carga de cuidado, trabajo y comidas '
        'fuera, etapa de la vida, clima laboral, pareja); el resto de las variables va por su cuenta.',
        *_resumen_triadas(resumen),
        '- **Pista para mirar:** IMC × ejercicio es la única con p < 0,05 sin corregir. En el mapa, hacer 3 o más '
        'días de ejercicio se asocia con muchas menos severas entre quienes tienen sobrepeso u obesidad, y no '
        'entre quienes tienen peso normal; con grupos de 14 a 16 participantes, no se puede afirmar.',
        '',
        '## 7. Limitaciones',
        '',
        '- **Conjunto sintético:** las relaciones reflejan los supuestos con que se generaron los datos (Fase 34A). '
        'Sirven para validar el método, no para concluir sobre la población.',
        '- **Potencia baja** en las tríadas, sobre todo en las que usan el IMC (267 participantes) y en la de '
        'diabetes (pocas participantes con medicamentos).',
        '- **Asociación no es causa:** que la diabetes vaya con más síntomas no dice cuál causa cuál.',
        '- **Medidas mixtas:** Spearman, V de Cramér y η se comparan en la misma escala de 0 a 1, pero no son '
        'idénticas; los grupos dependen además del corte elegido (0,30).',
        '',
        '## 8. Archivos',
        '',
        _tabla(['Archivo', 'Contenido'],
               [['`resultados/usuaria/matriz_asociacion_mixta.csv`', 'Matriz cuadrada (con signo en Spearman)'],
                ['`resultados/usuaria/pares_asociacion_mixta.csv`', 'Cada par: medida, valor, n, p y p ajustado'],
                ['`resultados/usuaria/grupos_variables.csv`', 'Grupos de variables y su asociación'],
                ['`resultados/usuaria/triadas_estratificadas.csv`', 'Cada combinación: n, % por clase, mediana MRS'],
                ['`resultados/usuaria/triadas_modelos.csv`', 'OR del modelo ordinal y de los tres cortes'],
                ['`resultados/usuaria/triadas_resumen.csv`', 'Prueba de interacción y Spearman parcial']]),
        '',
    ]
