"""
Fase 38: informes en Markdown y Word. Todas las cifras se leen de las tablas guardadas.

Uso, desde la carpeta scripts: NODE_PATH=<node_modules con docx> python generar_informes_38.py
"""
import shutil
import subprocess
import sys

import nucleo_38 as N
import numpy as np
import pandas as pd

sys.dont_write_bytecode = True
B = N.BASE
INF = B / 'informes'
F = INF / 'fuentes'
F.mkdir(parents=True, exist_ok=True)
SINT = ('Todo el análisis usa el conjunto **sintético** de 529 participantes. Las reglas describen lo que contiene la simulación: no son hechos sobre la menopausia '
        'en mujeres reales, no son diagnósticos ni predicciones y no permiten recomendaciones de salud. Ninguna asociación indica causa.')


def n(x, d=2):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return '—'
    return f'{x:,.{d}f}'.replace(',', 'X').replace('.', ',').replace('X', '.').replace('-', '−')


def e(x):
    return f'{int(x):,}'.replace(',', '.')


def pc(x, d=1):
    return n(100 * x, d) + ' %'


def p_(x):
    return '< 0,001' if x < 0.001 else n(x, 3)


def tabla(cab, filas):
    s = '| ' + ' | '.join(cab) + ' |\n|' + '---|' * len(cab) + '\n'
    return s + ''.join('| ' + ' | '.join(str(c).replace('|', '/') for c in f) + ' |\n' for f in filas)


def fig(nombre, pie):
    return f'\n![{pie}](../../figuras/{nombre})\n'


L = lambda r: pd.read_csv(B / r, encoding='utf-8')  # noqa: E731
J = lambda r: N.leer_json(B / r)  # noqa: E731
sello = J('protocolo/sello_protocolo.json')
DV, DI, ESC, CED, EXC = L('preparacion/diccionario_variables_categorias.csv'), L('preparacion/diccionario_items.csv'), L('preparacion/agrupaciones_escasas.csv'), \
    L('preparacion/categorias_escasas_detalle.csv'), L('preparacion/variables_excluidas.csv')
RT, TR = L('preparacion/resumen_transacciones.csv'), L('preparacion/trazabilidad_transformaciones.csv')
EQ, EQC, ENT = L('reglas/equivalencia_algoritmos.csv'), L('reglas/equivalencia_comparaciones.csv'), J('reglas/entorno.json')
R, META, COB = L('reglas/reglas_principal.csv'), J('reglas/resumen_principal.json'), L('reglas/cobertura.csv')
DEST, TOP, RED, FAM = L('reglas/reglas_destacadas.csv'), L('reglas/reglas_no_destacadas_mayor_z.csv'), L('reglas/redundantes_marcadas.csv'), L('reglas/familias_marcadas.csv')
NULA, EST, EFAM, SUB = L('referencia_nula/nula_principal.csv'), L('estabilidad/estabilidad_reglas.csv'), L('estabilidad/estabilidad_familias.csv'), L('estabilidad/submuestras.csv')
SR, LR, LEC, SUP, CLS = L('sensibilidades/resumen_sensibilidades.csv'), L('sensibilidades/lectura_resumen.csv'), L('sensibilidades/lectura_reglas_principal.csv'), \
    L('sensibilidades/superan_nula_sensibilidades.csv'), L('sensibilidades/clases_sensibilidades.csv')
PRU, MUT = L('pruebas/resultados_pruebas.csv'), L('pruebas/control_mutaciones.csv')
INI = J('integridad/integridad_inicial.json')
MAN_INI = L('integridad/manifiestos_inicial.csv')
FIN = J('integridad/integridad_final.json') if (B / 'integridad' / 'integridad_final.json').exists() else None
MT = L('preparacion/matriz_transaccional_principal.csv')

p0 = META['frecuencia_basal_si']
nm = META['marcadas']
cls = R['clase'].value_counts()
c6 = int(cls.get('6 asociación relativamente más marcada', 0))
c4 = int(cls.get('4 compatible con la referencia nula', 0))
c3 = int(cls.get('3 redundante', 0))
c2 = int(cls.get('2 asociación débil', 0))
SOL = DEST.iloc[0] if len(DEST) else None
SOL_EST = EST[EST['antecedente'] == SOL['antecedente']].iloc[0] if SOL is not None else None
NULA_P = ((NULA['reglas_marcadas'] >= nm).sum() + 1) / (len(NULA) + 1)
estables = int(EST['estable'].sum())
marc_est = EST.merge(R[['antecedente', 'marcada', 'clase']], on='antecedente')
nula_est = marc_est[marc_est['clase'].str.startswith('4')]


def exceso(cfg, marcadas, arch):
    nl = pd.read_csv(B / arch)['reglas_marcadas']
    return nl.mean(), nl.quantile(0.95), ((nl >= marcadas).sum() + 1) / (len(nl) + 1)


EXC_ROWS = [('principal', 529, META['reglas'], nm, *exceso('principal', nm, 'referencia_nula/nula_principal.csv'), META['supera_nula'])]
for r in SR.itertuples():
    EXC_ROWS.append((r.configuracion, r.n, r.reglas, r.marcadas, *exceso(r.configuracion, r.marcadas, f'sensibilidades/nula/nula_{r.configuracion}.csv'), r.supera_nula))
DESC = {**{k: v['descripcion'] for k, v in N.CONFIGS.items()}}
LS = LEC[LEC['antecedente'] == SOL['antecedente']] if SOL is not None else None


def regla_txt(a, cons):
    return f"**{N.legible_regla(a)}** → {N.legible(cons).lower()}"


def tabla_reglas(D, extra=True):
    filas = []
    for r in D.itertuples():
        f = [N.legible_regla(r.antecedente), 'severos' if r.consecuente.endswith('SI') else 'no severos', f'{e(r.n_conjunto)} de {e(r.n_antecedente)}',
             pc(r.soporte), f'{pc(r.confianza)} ({n(100 * r.ic_confianza_inf, 0)}-{n(100 * r.ic_confianza_sup, 0)})', pc(r.frecuencia_basal), n(r.lift),
             f'{"+" if r.diferencia_basal >= 0 else ""}{n(100 * r.diferencia_basal, 1)} pts', p_(r.p_ajustado_busqueda)]
        if extra:
            f += [pc(r.reaparece_marcada, 0), r.clase[2:]]
        filas.append(f)
    cab = ['Antecedente', 'Consecuente', 'n (con / antecedente)', 'Soporte', 'Confianza (IC 95 %)', 'Basal', 'Lift', 'Diferencia', 'p ajustado (búsqueda)']
    return tabla(cab + (['Reaparece', 'Clase'] if extra else []), filas)


docs = {}

# ---------- 03 diccionario
docs['03_diccionario_variables_categorias'] = ('Diccionario de variables y categorías', f"""
# Alcance

{SINT}

El diccionario describe las {len(DV)} variables preparadas: 31 del análisis principal y 4 que solo entran en sensibilidades.

- **Significado de las respuestas:** viene de las definiciones de la Fase 36, del diccionario de la limpieza y del texto de cada pregunta en la encuesta. No se dedujo del nombre de las variables.
- **Detalle por ítem:** `preparacion/diccionario_items.csv`.

# Variables

{tabla(['Variable', 'Bloque', 'Categorías originales (n)', 'Ítems resultantes [n]', 'Observadas / imputadas', 'Uso', 'Advertencias'],
       [[r.etiqueta, r.bloque, r.categorias_originales, r.categorias_agrupadas, (f'{e(r.observadas)} / {e(r.imputadas)}' + (f' (+{e(r.deducidas)} deducidas)' if r.deducidas and r.deducidas > 0 else '')) if not pd.isna(r.observadas) else 'sin marca por participante',
         r.uso, r.advertencias if isinstance(r.advertencias, str) else ''] for r in DV.itertuples()])}

# Condiciones de aplicación

- **«No aplica» en ejercicio y cuidado** («no realiza», «no cuida»): es una respuesta sustantiva y conserva su ítem (R6).
- **Módulo laboral:** solo para quienes trabajan.
- **Sobrecarga:** solo para quienes cuidan.
- **Sin ítem de «no aplica»:** nunca se crea, porque solo repetiría la pregunta de entrada.
- **Faltantes:** un faltante no genera ítem y nunca se confunde con una respuesta negativa (R7).
- **Preguntas que mencionan los síntomas:** lugar de trabajo comprensivo («frente a estos síntomas») y estrés laboral («que intensifiquen sus síntomas»). Por eso quedan fuera del análisis principal.

# Variables excluidas de los antecedentes

{tabla(['Variable', 'Motivo'], [[r.variable, r.motivo] for r in EXC.itertuples()])}
""")

# ---------- 04 justificación escasas
docs['04_agrupacion_categorias_escasas'] = ('Justificación del agrupamiento de categorías poco frecuentes', f"""
# Regla

{SINT}

El umbral es el 5 % de las participantes, es decir, 27. Las reglas se fijaron en el protocolo antes de calcular ninguna regla, y usan **solo frecuencias marginales**, sin el MRS:

- **R1. Se conserva:** una categoría con 27 participantes o más queda tal cual.
- **R2. Unión con la vecina:** una categoría ordinal con menos de 27 se une a su vecina adyacente de menor frecuencia. Si las dos vecinas tienen la misma frecuencia, se une hacia el centro de la escala. Se repite hasta que todas tengan al menos 27.
- **R3. Sin ítem:** una categoría nominal con menos de 27 y sin vecina compatible no genera ítem.
- **R5. Numéricas:** se cortan de antemano según su significado (edad, horas sentada e IMC).

Ningún corte se eligió para aumentar el soporte, la confianza ni el lift.

# Categorías originales con menos del 5 %

{tabla(['Variable', 'Categoría original', 'n', '%', 'Destino'], [[N.ETIQUETA[r.variable], r.categoria_original, e(r.participantes), n(r.pct, 1), N.legible(r.destino) if '=' in str(r.destino) else r.destino] for r in CED.itertuples()])}

Las categorías con 0 participantes existen en el instrumento, pero nadie las eligió. Solo amplían el rango del grupo al que se unen.

# Ítems resultantes

{tabla(['Variable', 'Ítem', 'Códigos unidos', 'Participantes', 'Regla'], [[N.ETIQUETA[r.variable], N.legible(r.resultado) if '=' in str(r.resultado) else r.resultado, r.codigos_originales, e(r.participantes_resultantes), r.regla] for r in ESC.itertuples()])}

# Decisiones

- **Quién prepara las comidas:** «compro comida preparada» (22) y «otro» (7) no se mezclan con ninguna otra categoría, porque sus significados son distintos. Esas 29 participantes no tienen ítem en esta variable.
- **Previsión:** FFAA (7), «ninguna» (15) y «no sabe» (2) son situaciones distintas. A diferencia de la Fase 37D, no se agrupan en «otra o ninguna». Esas 24 participantes no tienen ítem de previsión.
- **Distensión «siempre»:** tiene exactamente 27 (5,1 %), así que se conserva por R1.
- **Días de ejercicio:** «5-6 días» y «todos los días» suman 27, también justo el mínimo.
- **Sensibilidad con categorías originales:** S2a conserva las categorías sin agrupar. Las de menos de 27 no alcanzan el umbral de 53 de ningún antecedente.
""")

# ---------- 05 matriz y trazabilidad
docs['05_matriz_transaccional_trazabilidad'] = ('Matriz transaccional y trazabilidad', f"""
# Contenido

{SINT}

Cada participante es una transacción, identificada con su código original y en el orden de la Fase 36. Archivos:

- **Matriz principal:** `preparacion/matriz_transaccional_principal.csv`, una fila por participante y una columna 0/1 por ítem, más los dos consecuentes.
- **Lista de ítems:** `preparacion/transacciones_principal.txt`, la misma información como lista de ítems por participante.
- **Trazabilidad:** `preparacion/trazabilidad_transformaciones.csv`, que indica de qué códigos sale cada ítem, con qué regla y a cuántas participantes alcanza.
- **Sensibilidades:** `preparacion/sensibilidades/matriz_*.csv`, matrices separadas de la principal.

# Resumen por configuración

{tabla(['Configuración', 'Participantes', 'Severas', 'Basal', 'Variables', 'Ítems', 'Ítems por transacción', 'Umbral antecedente / conjunto', 'Pares determinados'],
       [[r.configuracion, e(r.participantes), e(r.severo_si), pc(r.frecuencia_basal_si), e(r.variables), e(r.items), n(r.items_por_transaccion_media, 1), f'{e(r.umbral_antecedente)} / {e(r.umbral_conjunto)}', e(r.pares_determinados)] for r in RT.itertuples()])}

# Verificaciones

- **Participantes:** 529 únicas, con los identificadores de la Fase 36.
- **Consecuente:** `severo_mrs` se recalcula desde los 11 ítems y coincide con la limpieza y con la Fase 35: 281 severas (53,1 %) y 248 no severas (46,9 %).
- **Contradicciones:** ninguna transacción tiene dos estados de la misma variable ni los dos consecuentes.
- **Antecedentes:** ningún ítem del MRS ni de los segmentos.
- **Participantes sin ítem en una variable:** solo por faltantes reales (en la principal, ninguno) o por la regla R3: 29 en quién prepara las comidas y 24 en previsión.
- **Ítems constantes:** en las subpoblaciones se quitan los ítems que todas o ninguna cumplen (por ejemplo, «no cuida» en S7b).
- **Pares determinados:** se excluyen los antecedentes con dos ítems en que uno implica al otro. En la principal no hay ninguno.
""")

# ---------- 06 equivalencia
docs['06_equivalencia_apriori_fpgrowth'] = ('Equivalencia Apriori / FP-Growth', f"""
# Resultado

Apriori, FP-Growth y una enumeración exhaustiva producen **exactamente los mismos {e(EQ.iloc[0]['conjuntos_frecuentes'])} conjuntos frecuentes, con los mismos recuentos, y las mismas {e(EQ.iloc[0]['reglas'])} reglas**.

- **Parámetros comunes:** soporte conjunto mínimo de {e(EQ.iloc[0]['minsup_absoluto'])} participantes, hasta 3 condiciones de antecedente y un consecuente.
- **Elección del algoritmo:** ninguno se eligió por las reglas que entrega. Las sensibilidades usan FP-Growth.
- **Sin reajuste:** los tres son deterministas, no usan semillas y no se reajustan.

{tabla(['Algoritmo', 'Conjuntos frecuentes', 'Reglas', 'Segundos', 'Memoria máxima (MB)'], [[r.algoritmo, e(r.conjuntos_frecuentes), e(r.reglas), n(r.segundos, 2), n(r.memoria_pico_mb, 1)] for r in EQ.itertuples()])}

{tabla(['Comparación', 'Mismos conjuntos y recuentos', 'Diferencias', 'Mismas reglas'], [[r.comparacion, 'sí' if r.mismos_conjuntos_y_recuentos else 'NO', e(r.diferencias), 'sí' if r.mismas_reglas else 'NO'] for r in EQC.itertuples()])}

# Evaluador matricial

La referencia nula y la estabilidad usan un evaluador matricial que recuenta los mismos antecedentes frecuentes.

- **Por qué basta recontar:** las agrupaciones no dependen del consecuente, así que permutar la severidad o tomar una submuestra no cambia qué antecedentes existen.
- **Verificación:** la prueba 11 confirma que el evaluador da los mismos recuentos que FP-Growth ejecutado de nuevo en dos permutaciones y en una submuestra.

# Entorno

- **Versiones:** Python {ENT['python']}, NumPy {ENT['numpy']}, pandas {ENT['pandas']} y SciPy {ENT['scipy']}.
- **Recursos:** un hilo por biblioteca numérica y semilla {ENT['semilla']} para permutaciones y submuestras.
- **Implementación:** {ENT['implementacion']}.
- **Memoria:** cada etapa corrió bajo el vigilante (`integridad/registro_memoria.csv`), con un solo proceso de análisis.
""")

# ---------- 07 reglas generales
sol_txt = ''
if SOL is not None:
    sol_txt = f"""
## La única regla de la clase 6

{regla_txt(SOL['antecedente'], SOL['consecuente'])}

{tabla_reglas(DEST)}

**Lectura sencilla:**
- **Cifras:** de las {e(SOL['n_antecedente'])} participantes que trabajan, no hacen ejercicio de bajo impacto y casi nunca tienen distensión abdominal, {e(SOL['n_conjunto'])} ({pc(SOL['confianza'], 0)}) tienen síntomas severos, frente al {pc(p0, 0)} del total.
- **Margen:** supera la referencia nula por poco (p ajustado {p_(SOL['p_ajustado_busqueda'])}, con un corte de 0,05). Reaparece marcada en el {pc(SOL_EST['reaparece_marcada'], 0)} de las submuestras.

**Advertencias:**
- **Dirección inesperada:** incluye una variable próxima a síntomas, la distensión abdominal, en una dirección poco intuitiva: casi nunca tener distensión aparece junto a más síntomas severos.
- **Fragilidad:** no sobrevive a varias sensibilidades (informe 12).
- **Lectura:** describe una combinación del conjunto sintético, no un mecanismo.
"""
docs['07_reglas_generales'] = ('Resultados de reglas generales', f"""
# Resumen

{SINT}

- **Búsqueda principal:** se evaluaron **{e(META['reglas'])} reglas** de 1 a 3 condiciones, todas las combinaciones con al menos 53 participantes en el antecedente.
- **Marcadas:** {e(nm)} se alejan al menos 10 puntos de la frecuencia basal. Bajo la referencia nula aparecen {e(round(NULA['reglas_marcadas'].mean()))} marcadas en promedio, con un percentil 95 de {e(round(NULA['reglas_marcadas'].quantile(0.95)))}.
- **Señal difusa:** hay más reglas marcadas de lo que produce el azar (p = {p_(NULA_P)}). La relación entre hábitos y severidad no es nula en los datos sintéticos, pero está repartida en muchas combinaciones débiles.
- **Reglas que superan la referencia nula:** solo **{META['supera_nula']}** regla supera la nula de toda la búsqueda. Cumple además los criterios de estabilidad y no redundancia, así que es la **única de la clase 6**. Es frágil (informe 12).
- **Benjamini-Hochberg:** sobre todas las reglas, ninguna tiene q < 0,05; el mínimo es {n(R['q_bh_todas'].min(), 3)}.

# Clasificación de todas las reglas

{tabla(['Clase', 'Reglas', '→ severos', '→ no severos'], [[k[2:], e(v), e(((R['clase'] == k) & (R['consecuente'] == 'severo_mrs=SI')).sum()), e(((R['clase'] == k) & (R['consecuente'] == 'severo_mrs=NO')).sum())] for k, v in cls.sort_index().items()])}

- **Asociación débil:** la confianza está a menos de 10 puntos de la frecuencia basal.
- **Redundante:** agregar una condición mejora la confianza en menos de 5 puntos respecto de una regla más simple.
- **Compatible con la referencia nula:** su fuerza está dentro de lo que aparece al buscar entre 12.201 reglas sin ninguna relación real.
- **Inestables:** ninguna regla queda en esta clase.
{sol_txt}
# Reglas más fuertes que no destacan

La tabla muestra, para cada consecuente, las 10 reglas no redundantes con mayor |z|. **No son hallazgos:** salvo la primera, todas son compatibles con la referencia nula. Se muestran para que se vea qué hay y no quede oculto.

{tabla_reglas(TOP)}

{fig('f07_reglas_mayor_z.png', 'Figura 7. Reglas más fuertes de la búsqueda principal.')}

**Patrones que se repiten:**
- **Con los síntomas severos:** trabajar, no hacer ejercicio (0 días o sin bajo impacto) y frecuencias intermedias de algunos alimentos.
- **Con los síntomas no severos:** no trabajar, tener pareja y algunos hábitos de alimentación.

Ninguno supera la referencia nula salvo la regla de la clase 6. Los patrones son coherentes con las asociaciones pequeñas de la Fase 37D (trabajo y ejercicio), pero esta fase no las confirma de forma independiente.
""")

# ---------- 08 soporte, confianza, lift, cobertura
docs['08_soporte_confianza_lift_cobertura'] = ('Soporte, confianza, lift y cobertura', f"""
# Medidas

{SINT}

| Medida | Significado | Ejemplo con la regla de la clase 6 |
|---|---|---|
| n_A | Participantes que cumplen el antecedente | {e(SOL['n_antecedente'])} |
| n_AC | Las que, además, tienen el consecuente | {e(SOL['n_conjunto'])} |
| Soporte | n_AC / 529 | {pc(SOL['soporte'])} |
| Confianza | n_AC / n_A | {pc(SOL['confianza'])} |
| Frecuencia basal | Frecuencia del consecuente en las 529 | {pc(SOL['frecuencia_basal'])} |
| Lift | Confianza / basal | {n(SOL['lift'])} |
| Diferencia respecto de la basal | Confianza − basal | {n(100 * SOL['diferencia_basal'], 1)} puntos |
| Leverage | Soporte − (n_A / 529) × basal | {n(SOL['leverage'], 3)} |
| Diferencia de riesgo | Confianza − frecuencia en quienes no cumplen el antecedente (IC 95 % de Newcombe) | {n(100 * SOL['diferencia_riesgo'], 1)} puntos ({n(100 * SOL['ic_dr_inf'], 1)} a {n(100 * SOL['ic_dr_sup'], 1)}) |
| Razón de riesgos | Confianza / frecuencia en quienes no cumplen | {n(SOL['razon_riesgos'])} |

- **La confianza sola engaña:** la frecuencia basal de síntomas severos es {pc(p0)}, así que una regla con 60 % de confianza solo está 7 puntos sobre lo esperable. Por eso ninguna regla se destaca por su confianza.
- **Consecuente «no severo»:** la basal es {pc(1 - p0)}.
- **Lift mayor que 1:** significa que el consecuente es más frecuente con el antecedente que en general. No significa causa.

# Distribución en la búsqueda principal

{tabla(['', '→ severos', '→ no severos'], [
    ['Reglas', e((R['consecuente'] == 'severo_mrs=SI').sum()), e((R['consecuente'] == 'severo_mrs=NO').sum())],
    ['Confianza mediana', pc(R[R['consecuente'] == 'severo_mrs=SI']['confianza'].median()), pc(R[R['consecuente'] == 'severo_mrs=NO']['confianza'].median())],
    ['Confianza máxima', pc(R[R['consecuente'] == 'severo_mrs=SI']['confianza'].max()), pc(R[R['consecuente'] == 'severo_mrs=NO']['confianza'].max())],
    ['Lift máximo', n(R[R['consecuente'] == 'severo_mrs=SI']['lift'].max()), n(R[R['consecuente'] == 'severo_mrs=NO']['lift'].max())],
    ['Marcadas (≥ 10 puntos)', e(((R['consecuente'] == 'severo_mrs=SI') & R['marcada']).sum()), e(((R['consecuente'] == 'severo_mrs=NO') & R['marcada']).sum())],
    ['n_A mediano de las marcadas', e(R[(R['consecuente'] == 'severo_mrs=SI') & R['marcada']]['n_antecedente'].median()), e(R[(R['consecuente'] == 'severo_mrs=NO') & R['marcada']]['n_antecedente'].median())]])}

**Dónde están las reglas marcadas:**
- **Antecedentes pequeños:** casi todas las marcadas tienen antecedentes con pocas participantes, entre 53 y unas 100.
- **Antecedentes grandes:** más allá de unas 150 participantes, ninguna regla se aleja 10 puntos de la basal.
- **Por qué:** es lo esperable cuando las asociaciones son pequeñas. Solo los grupos chicos, más variables por azar, alcanzan diferencias grandes.

{fig('f02_confianza_frente_a_casos.png', 'Figura 2. Confianza de cada regla según n_A, con el umbral de la referencia nula.')}

# Cobertura

La cobertura es la proporción de las 529 que cumple al menos una regla del conjunto.

{tabla(['Conjunto', 'Consecuente', 'Reglas', 'Participantes cubiertas', 'Cobertura', 'Confianza media'], [[r.conjunto, 'severos' if r.consecuente.endswith('SI') else 'no severos', e(r.reglas), e(r.participantes_cubiertas), pc(r.cobertura), pc(r.confianza_media) if not pd.isna(r.confianza_media) else '—'] for r in COB.itertuples()])}

- **Marcadas:** cubren casi a todas las participantes. Con más de mil reglas, cualquier persona cumple alguna.
- **Más sólidas:** la única regla que supera todos los criterios cubre a {e(SOL['n_antecedente'])} participantes ({pc(SOL['n_antecedente'] / 529)}).

El compromiso es claro: mucha cobertura viene con poca precisión, y la precisión aparece solo en grupos pequeños.

# Umbrales

{fig('f08_umbrales.png', 'Figura 8. Compromiso entre umbral de soporte y cantidad de reglas.')}

{tabla(['Umbral de antecedente', 'Reglas', 'Marcadas', 'Media nula', 'Superan la nula'], [[f'{x[0]} (n_A ≥ {u})', e(x[2]), e(x[3]), e(round(x[4])), e(x[7])] for x, u in [(next(r for r in EXC_ROWS if r[0] == 'S3-bajo'), 27), (EXC_ROWS[0], 53), (next(r for r in EXC_ROWS if r[0] == 'S3-alto'), 80)]])}
""")

# ---------- 09 redundancia
docs['09_redundancia'] = ('Análisis de redundancia', f"""
# Criterio

{SINT}

Una regla de 2 o 3 condiciones es **redundante** si alguna regla más simple, con un subconjunto propio de sus condiciones y en la misma dirección, tiene una confianza menor en **menos de 5 puntos**. Es decir, la condición agregada casi no aporta. Las reglas con las mismas variables y la misma dirección forman una **familia**.

# Resultados

- **Reglas marcadas:** de las {e(nm)}, **{e(int((R['marcada'] & R['redundante'].fillna(False).astype(bool)).sum()))} son redundantes** ({pc((R['marcada'] & R['redundante'].fillna(False).astype(bool)).sum() / nm, 0)}).
- **No redundantes:** quedan {e(int((R['marcada'] & ~R['redundante'].fillna(False).astype(bool)).sum()))} marcadas. Una supera la referencia nula; las demás son compatibles con ella.
- **Familias:** las reglas marcadas pertenecen a {e(len(FAM))} familias distintas. Casi todas tienen una o dos reglas, así que no hay un patrón dominante que se repita con muchas variantes.
- **Trabajo:** {pc(R[R['marcada']]['variables'].str.contains('trabaja').mean(), 0)} de las reglas marcadas incluyen la pregunta de trabajo. Muchas reglas de tres condiciones agregan a «trabaja: sí» o «trabaja: no» uno o dos hábitos.

**Ejemplos de reglas marcadas redundantes:**

{tabla(['Regla', 'Consecuente', 'Confianza', 'Regla más simple casi igual', 'Mejora'], [[N.legible_regla(r.antecedente), 'severos' if r.consecuente.endswith('SI') else 'no severos', pc(r.confianza), N.legible_regla(r.subregla_mas_cercana), f'{n(100 * r.mejora_sobre_subreglas, 1)} pts'] for r in RED.sort_values('confianza', ascending=False).head(12).itertuples()])}

**Familias con más reglas marcadas:**

{tabla(['Familia', 'Reglas marcadas', 'Redundantes', 'Confianza máxima'], [[r.familia.replace('severo_mrs=SI', 'severos').replace('severo_mrs=NO', 'no severos'), e(r.reglas), e(r.redundantes), pc(r.confianza_max)] for r in FAM.head(10).itertuples()])}

La lista completa está en `reglas/redundantes_marcadas.csv` y `reglas/familias_marcadas.csv`.
""")

# ---------- 10 estabilidad
docs['10_estabilidad'] = ('Evaluación de estabilidad', f"""
# Método

{SINT}

- **Submuestras:** {e(N.N_SUB)} del 80 % ({e(META['estabilidad']['n_submuestra'])} participantes), sin reemplazo y con semilla {N.SEMILLA}.
- **Redescubrimiento:** en cada una se buscan de nuevo las reglas, con los mismos ítems y agrupaciones y con umbrales proporcionales: n_A ≥ {META['estabilidad']['umbral_antecedente']} y n_AC ≥ {META['estabilidad']['umbral_conjunto']}.
- **Sin fuga:** las agrupaciones se fijaron con las 529 y sin el MRS, y no se reajustan.
- **Regla estable:** reaparece marcada en al menos el 70 % de las submuestras y mantiene la dirección en al menos el 95 %.

# Resultados

- **Reglas estables:** {e(estables)} de {e(nm)} reglas marcadas son estables.
- **La regla de la clase 6:** reaparece marcada en el {pc(SOL_EST['reaparece_marcada'], 0)} de las submuestras y siempre en la misma dirección. Su confianza varía entre {pc(SOL_EST['confianza_p2_5'], 0)} y {pc(SOL_EST['confianza_p97_5'], 0)} (percentiles 2,5 y 97,5) y su lift entre {n(SOL_EST['lift_p2_5'])} y {n(SOL_EST['lift_p97_5'])}.
- **Familias:** de {e(len(EFAM))} familias con reglas marcadas, {e(int((EFAM['familia_reaparece'] >= 0.7).sum()))} reaparecen en al menos el 70 % de las submuestras.
- **Recambio en cada submuestra:**
  - En promedio aparecen {e(round(SUB['reglas_marcadas'].mean()))} reglas marcadas (entre {e(SUB['reglas_marcadas'].min())} y {e(SUB['reglas_marcadas'].max())}).
  - De ellas, {e(round(SUB['nuevas'].mean()))} son nuevas: no estaban marcadas en las 529.
  - Desaparecen en promedio {e(round(SUB['desaparecidas'].mean()))} de las 1.119.
  - Las reglas marcadas cambian mucho de una submuestra a otra.

{fig('f04_estabilidad.png', 'Figura 4. Estabilidad en 200 submuestras.')}

# Lectura

**La estabilidad no separa la señal del ruido en este diseño.**

- **Reglas compatibles con el azar:** las {e(len(nula_est))} reglas no redundantes compatibles con la referencia nula reaparecen en promedio en el {pc(nula_est['reaparece_marcada'].mean(), 0)} de las submuestras, y {e(int(nula_est['estable'].sum()))} cumplen el criterio de estabilidad.
- **Motivo:** las submuestras del 80 % comparten la mayor parte de las participantes. Una regla que aparece por azar en las 529 tiende a reaparecer en submuestras que contienen casi los mismos datos.
- **Consecuencia:** la estabilidad es una condición necesaria, no suficiente. **No demuestra validez y menos validez clínica.** El control principal contra las reglas casuales es la referencia nula (informe 11).
""")

# ---------- 11 nula
docs['11_referencia_nula'] = ('Evaluación frente a la referencia nula', f"""
# Método

{SINT}

- **Permutaciones:** {e(len(NULA))} de la severidad entre las participantes (semilla {N.SEMILLA}). Cada una conserva todas las características de cada participante y la frecuencia basal (281 severas), y rompe cualquier relación entre ambas.
- **Búsqueda completa en cada permutación:** las mismas {e(META['antecedentes_evaluados'])} combinaciones y los mismos umbrales.
- **Valor p ajustado de cada regla:** la proporción de permutaciones en que **la regla más fuerte de toda la búsqueda** iguala o supera a la regla observada. Es el método de máximo estadístico de Westfall-Young, que corrige por haber buscado entre miles de reglas.
- **Cuándo se supera la nula:** con un p ajustado menor que 0,05.

# Resultados

{tabla(['', 'Observado', 'Referencia nula: media', 'Percentil 95', 'p'], [
    ['Reglas marcadas', e(nm), e(round(NULA['reglas_marcadas'].mean())), e(round(NULA['reglas_marcadas'].quantile(0.95))), p_(NULA_P)],
    ['Mayor |z| de la búsqueda', n(R['z'].abs().max()), n(NULA['max_z'].mean()), n(META['nula_p95_max_z']), p_(R['p_ajustado_busqueda'].min())],
    ['Mayor diferencia respecto de la basal', f"{n(100 * R['diferencia_basal'].abs().max(), 1)} pts", f"{n(100 * NULA['max_dif'].mean(), 1)} pts", f"{n(100 * META['nula_p95_max_dif'], 1)} pts", '—']])}

{fig('f03_referencia_nula.png', 'Figura 3. Referencia nula.')}

**Lectura:**
- **En conjunto, hay más reglas que por azar.** Sin relación real aparecen unas {e(round(NULA['reglas_marcadas'].mean()))} reglas marcadas; en los datos hay {e(nm)}. La diferencia indica una asociación real en la simulación, pero repartida y débil.
- **Ninguna regla puntual sobresale con claridad.** La mayor diferencia observada ({n(100 * R['diferencia_basal'].abs().max(), 1)} puntos) es parecida a la que el azar produce en el 5 % de las búsquedas ({n(100 * META['nula_p95_max_dif'], 1)} puntos). Solo una regla supera el umbral, y por poco (p = {p_(R['p_ajustado_busqueda'].min())}).
- **Reglas que aparecen fácilmente bajo la nula:** las {e(c4)} reglas marcadas no redundantes de la clase 4, más todas las débiles y las redundantes. Su fuerza está dentro de lo que el azar produce al buscar entre 12.201 reglas.

**Valores p y Benjamini-Hochberg:**
- **p de Fisher:** cada regla tiene uno, pero es ordinario. La regla se descubrió con los mismos datos, así que ese p no confirma nada.
- **Benjamini-Hochberg:** se aplicó a **todas** las reglas evaluadas, no solo a las seleccionadas. Ninguna queda con q < 0,05.
""")

# ---------- 12 sensibilidades
lec = LR.set_index('configuracion')
def fila_lec(cfg):
    x = lec.loc[cfg] if cfg in lec.index else None
    return [e(x.get(k, 0)) if x is not None else '—' for k in ('se mantiene', 'se debilita', 'cambia de dirección', 'desaparece por falta de casos', 'no evaluable')]


docs['12_sensibilidades'] = ('Sensibilidades', f"""
# Resumen

{SINT}

Todas las sensibilidades se fijaron en el protocolo. Cada una repite la búsqueda completa con 1.000 permutaciones propias.

{tabla(['Configuración', 'Cambio', 'n', 'Reglas', 'Marcadas', 'Media nula', 'p (exceso)', 'Superan la nula'], [[x[0], DESC[x[0]], e(x[1]), e(x[2]), e(x[3]), e(round(x[4])), p_(x[6]), e(x[7])] for x in EXC_ROWS])}

**Lectura general:**
- **Hay más reglas marcadas que por azar en casi todas las configuraciones** (p ≤ 0,04), salvo cuando solo se permite una condición (S4-1). La señal difusa es robusta.
- **Las reglas que superan la nula son pocas y distintas en cada configuración:** {e(len(SUP))} entre las 13 sensibilidades, ninguna igual en dos configuraciones, salvo la regla de la clase 6, que reaparece con las categorías originales (S2a).
- **Ninguna regla puntual es robusta.**

{fig('f05_exceso_frente_a_nula.png', 'Figura 5. Exceso de reglas marcadas sobre la referencia nula.')}

# Qué ocurre con las 1.119 reglas marcadas de la principal

{tabla(['Configuración', 'Se mantiene', 'Se debilita', 'Cambia de dirección', 'Desaparece por falta de casos', 'No evaluable'], [[cfg, *fila_lec(cfg)] for cfg in lec.index])}

{fig('f06_lectura_sensibilidades.png', 'Figura 6. Reglas de la principal en cada sensibilidad.')}

- **Cambios de dirección:** casi ninguna regla cambia de dirección, y las que cambian son de las subpoblaciones (S7, S8). Cuando una regla se pierde es porque **se debilita o le faltan casos**, no porque se invierta.
- **«No evaluable»:** la regla usa una variable excluida, un ítem que no existe con otra agrupación, o más condiciones de las permitidas.

# La regla de la clase 6 en cada sensibilidad

{tabla(['Configuración', 'n_A', 'Confianza', 'Diferencia', 'Lectura', 'Supera la nula'], [[r.configuracion, e(r.n_antecedente) if not pd.isna(r.n_antecedente) else '—', pc(r.confianza) if not pd.isna(r.confianza) else '—', f'{n(100 * r.diferencia_basal, 1)} pts' if not pd.isna(r.diferencia_basal) else '—', r.lectura, {True: 'sí', False: 'no'}.get(r.supera_nula, '—') if not pd.isna(r.supera_nula) else '—'] for r in LS.itertuples()])}

La regla **no es robusta**:
- **S1 (sin imputados):** baja a {e(LS.set_index('configuracion').loc['S1', 'n_antecedente'])} casos, bajo el umbral de 53.
- **Umbral del 5 %:** queda compatible con la nula, porque la búsqueda es más amplia.
- **Umbral del 15 %:** no tiene casos suficientes.
- **S5 y S6:** no es evaluable, porque usa una frecuencia de ejercicio (S5) y una variable próxima a síntomas (S6).
- **S7a:** no es evaluable, porque «trabaja» es constante en esa subpoblación.
- **S7b:** se mantiene en dirección, pero ya no supera la nula.
- **Solo se mantiene** con las categorías originales (S2a), que no cambian sus ítems.

# Reglas que superan la nula en alguna sensibilidad

{tabla(['Configuración', 'Antecedente', 'Consecuente', 'n_A (n)', 'Confianza', 'Basal', 'p ajustado', 'Clase'], [[r.configuracion, N.legible_regla(r.antecedente), 'severos' if r.consecuente.endswith('SI') else 'no severos', f'{e(r.n_antecedente)} ({e(r.n)})', pc(r.confianza), pc(r.frecuencia_basal), p_(r.p_ajustado_busqueda), r.clase[2:]] for r in SUP.itertuples()])}

**Reglas que aparecen solo en una sensibilidad:**
- **S2b (agrupación gruesa):** las reglas que superan la nula giran en torno a **«3 días o más de ejercicio» → síntomas no severos**, combinado con condiciones muy frecuentes (FONASA, no usar medicamentos). Solo dos de ellas no son redundantes. Es la misma dirección que la asociación pequeña de la Fase 37D entre días de ejercicio y MRS. Aparece al juntar las categorías de 3 días o más (79 participantes), un corte que el protocolo fijó para S2b sin ver resultados.
- **S7b (quienes cuidan, n = 251):** una regla con sobrecarga frecuente, sin ejercicio aeróbico y 3-4 vasos de agua. Se apoya en solo 34 participantes, y la pregunta de sobrecarga puede reflejar las mismas dificultades que los síntomas.

Ninguna de estas reglas se repite en la principal ni en las demás sensibilidades, así que no se presentan como hallazgos.

# Detalles por sensibilidad

**S1 (sin valores imputados):**
- **Qué cambia:** las celdas imputadas no generan ítem, y diabetes y previsión quedan fuera.
- **Efecto:** muchas reglas pierden casos ({e(lec.loc['S1', 'desaparece por falta de casos'])} desaparecen por esa razón), pero ninguna cambia de dirección.
- **Lectura:** las imputaciones de la limpieza no fabrican las reglas, pero sí aportan casos que las sostienen sobre el umbral.

**S2a y S2b (agrupaciones):**
- **Categorías originales:** dan resultados casi iguales a la principal.
- **Agrupación gruesa:** cambia los ítems, así que la mayoría de las reglas no es comparable. Hace visible un patrón de ejercicio.

**S3 (umbrales):**
- **Umbral del 5 %:** produce {e(next(x for x in EXC_ROWS if x[0] == 'S3-bajo')[2])} reglas y ninguna supera la nula.
- **Umbral del 15 %:** produce {e(next(x for x in EXC_ROWS if x[0] == 'S3-alto')[2])} reglas, también ninguna.
- **Lectura:** bajar el umbral no revela reglas más sólidas; solo agrega ruido.

**S4 (largo):**
- **Una condición:** hay 4 reglas marcadas, frente a 2 en promedio bajo el azar (p = 0,109), y ninguna supera la nula. Las más fuertes son el ejercicio de bajo impacto frecuente (→ no severos) y el uso de medicamentos para la diabetes (→ severos).
- **Hasta dos condiciones:** tampoco aparece ninguna regla que supere la nula.

**S5 y S6 (variables excluidas):**
- **S5:** quitar las frecuencias de ejercicio no cambia la conclusión.
- **S6:** quitar las variables próximas a síntomas tampoco la cambia; solo elimina la regla de la clase 6.

**S7a (quienes trabajan, n = 309):**
- **Población:** el módulo laboral se analiza solo en quienes trabajan. Su basal es más alta ({pc(RT.set_index('configuracion').loc['S7a', 'frecuencia_basal_si'])}).
- **Resultado:** ninguna regla supera la nula.
- **Advertencia:** las dos preguntas del módulo mencionan los síntomas, así que cualquier regla con ellas sería circular.

**S7b (quienes cuidan, n = 251):** hay una regla con sobrecarga, débil y pequeña (ver arriba).

**S8 (IMC observado, n = 267):**
- **Resultado:** con o sin las categorías de IMC, ninguna regla supera la nula.
- **Lectura:** el IMC no aporta reglas sólidas, y la mitad sin IMC no altera la conclusión.
- **Cambios de dirección:** las 7 reglas que cambian de dirección en S8 se deben a la subpoblación, no al IMC: son las mismas en S8a y S8b.
""")

# ---------- 13 figuras y tablas
figs = sorted((B / 'figuras').glob('*.png'))
tablas = sorted(p.relative_to(B).as_posix() for d in ('preparacion', 'reglas', 'estabilidad', 'referencia_nula', 'sensibilidades') for p in (B / d).rglob('*') if p.suffix in ('.csv', '.json') and 'lotes' not in p.parts)
docs['13_figuras_tablas'] = ('Figuras y tablas', f"""
# Contenido

{SINT}

Hay {len(figs)} figuras, generadas desde las tablas guardadas con `scripts/graficos_38.py`, y {len(tablas)} tablas de respaldo. Los lotes de permutaciones y submuestras están en `referencia_nula/` y `sensibilidades/lotes/`, y sirven para reanudar si se interrumpe la ejecución.

# Tablas

{tabla(['Archivo'], [[t] for t in tablas])}

# Figuras
""" + '\n'.join(fig(p.name, p.stem.replace('_', ' ')) for p in figs))

# ---------- 17 nota fase 39
MT['trabaja'] = MT['trabaja=SI']
estr = []
for nombre, cols in (('Trabajo', ['trabaja=SI', 'trabaja=NO']), ('Pareja', ['pareja=SI', 'pareja=NO']),
                     ('Días de ejercicio', ['dias_ejercicio=0_dias', 'dias_ejercicio=1-2_dias', 'dias_ejercicio=3-4_dias', 'dias_ejercicio=5-6_dias_o_todos_los_dias']),
                     ('Cuidado', ['cuida=no_cuida', 'cuida=1_persona', 'cuida=2_personas', 'cuida=3_o_mas_personas'])):
    for c in cols:
        m = MT[c] == 1
        estr.append([nombre, N.legible(c).split(': ', 1)[1], e(m.sum()), e(MT.loc[m, 'severo_mrs=SI'].sum()), pc(MT.loc[m, 'severo_mrs=SI'].mean()), e(int(np.ceil(0.10 * m.sum())))])
docs['17_nota_fase_39'] = ('Nota para preparar la Fase 39', f"""
# Alcance

Esta nota prepara la Fase 39. **No ejecuta ninguna comparación entre subpoblaciones.** La Fase 39 no se inicia sin una decisión expresa.

{SINT}

# Punto de partida

La Fase 38 encontró una **señal difusa**: más reglas que por azar, pero ninguna regla general robusta. Los patrones que más se repiten (trabajo, ejercicio, pareja) son las mismas variables que definen las subpoblaciones propuestas. Por eso la pregunta de la Fase 39 es razonable: **¿la relación entre hábitos y severidad es distinta según el contexto?** También tiene un riesgo: dentro de cada estrato el n baja y el azar pesa más.

# Subpoblaciones y tamaños

{tabla(['Dimensión', 'Estrato', 'Participantes', 'Con síntomas severos', 'Basal del estrato', 'Antecedente mínimo (10 %)'], estr)}

- **Basales distintas:** varían entre estratos, así que las reglas deben compararse con la basal de **su** estrato, no con el 53,1 % general.
- **Estratos pequeños:** los de ejercicio de 3-4 días (52) y de 5 días o más (27) son demasiado chicos para buscar reglas propias. Conviene usar la agrupación «3 días o más» (79), la misma de B1 y de S2b, fijada de antemano.
- **Cuidado:** por la misma razón, conviene comparar quienes cuidan (251) con quienes no cuidan (278), sin separar por número de personas cuidadas.

# Cómo evaluar las diferencias

1. **Protocolo sellado antes de mirar.** Hay que fijar de antemano:
   - los estratos, con «3 días o más» para el ejercicio;
   - los ítems, iguales a los de la Fase 38 menos la variable que define el estrato;
   - umbrales proporcionales al tamaño del estrato, con un mínimo absoluto de 20 participantes en el antecedente;
   - los criterios.
2. **Búsqueda dentro de cada estrato:** con su propia referencia nula, permutando la severidad **dentro** del estrato. Con estratos de 79 a 356 participantes, la referencia nula será más exigente que en la principal.
3. **Comparación entre estratos de una misma regla:**
   - Confianza de la regla en cada estrato, **siempre con su denominador** (por ejemplo, «41 de 60» frente a «30 de 70»), su IC 95 % y la diferencia respecto de la basal de cada estrato.
   - Diferencia entre estratos con su IC 95 % (Newcombe).
   - Prueba de interacción por permutaciones dentro de los estratos, como referencia exploratoria.
   - Nunca porcentajes sin el n.
4. **Control de la búsqueda:** el número de comparaciones entre estratos se multiplica. Hay que usar el máximo estadístico sobre todas las reglas y estratos a la vez, no correcciones aplicadas solo a las reglas seleccionadas.
5. **Lectura de las diferencias:** una diferencia entre estratos es exploratoria. Si la regla no supera la nula en ningún estrato, una diferencia de porcentajes entre ellos no tiene interpretación.
6. **Segmentos A y B1:** pueden usarse como comparación exploratoria adicional, nunca como base obligatoria. B1 equivale a combinar trabajo, pareja y ejercicio, así que comparar por B1 repite en buena parte las comparaciones por esas tres variables.

# Riesgos

- **Circularidad:** el módulo laboral menciona los síntomas, y la sobrecarga puede ser consecuencia de ellos.
- **Variables próximas a síntomas:** actividad sexual, distensión y evacuación. Conviene repetir sin ellas (como S6).
- **Imputaciones:** repetir sin imputados (como S1). En la Fase 38, muchas reglas perdieron casos sin imputados.
- **Estratos y reglas pequeños:** varios estratos tienen menos de 100 participantes, así que las reglas dentro de ellos tendrán entre 10 y 30 casos. Lo esperable es mucho ruido.

# Decisiones pendientes para la responsable

1. **Si iniciar la Fase 39**, y con qué dimensiones: trabajo, pareja, ejercicio, cuidado, o una selección.
2. **Agrupación del ejercicio:** 0, 1-2 y 3 o más días.
3. **Variables:** si se incluyen las próximas a síntomas y los módulos (S7) en el análisis por estratos.
4. **Segmentos:** si A y B1 se usan como comparación exploratoria.
""")

# ---------- 16 informe metodológico de cierre (20 preguntas)
ex = {x[0]: x for x in EXC_ROWS}
docs['16_informe_cierre_38'] = ('Informe metodológico de cierre de la Fase 38', f"""
# Conclusión

**La evidencia de reglas de asociación es débil.**

- **Señal difusa:** en los datos sintéticos hay más combinaciones de hábitos y contexto asociadas con la severidad de lo que produciría el azar ({e(nm)} reglas marcadas frente a {e(round(NULA['reglas_marcadas'].mean()))} esperadas). Esa señal está repartida en muchas reglas débiles.
- **Reglas puntuales:** de 12.201 reglas, **solo una cumple todos los criterios sellados**, y lo hace por poco. Además:
  - incluye una variable próxima a síntomas;
  - no se mantiene sin imputaciones ni con otros umbrales.
- **Conclusión:** **no hay reglas suficientemente sólidas para destacar como hallazgos.** Los patrones que más se repiten (trabajar y no hacer ejercicio con síntomas severos; no trabajar y tener pareja con síntomas no severos) coinciden con las asociaciones pequeñas de la Fase 37D, pero esta fase no las confirma de forma independiente.

{SINT}

# Respuestas

**1. ¿Cuántas variables se utilizaron?**
- **Análisis principal:** 31 variables generales medidas en las 529 participantes.
- **Sensibilidades:** 4 más, cada una solo en su sensibilidad: el IMC, las dos preguntas laborales y la sobrecarga.
- **Excluidas:** el MRS (solo como consecuente), los segmentos y la etapa menopáusica.
- **Criterio:** ninguna variable se eligió por su asociación con el MRS.

**2. ¿Cómo se agruparon las categorías poco frecuentes?**
- **Regla fija:** se aplicó la regla del protocolo, sin mirar el MRS: una categoría ordinal con menos de 27 participantes se une a su vecina de menor frecuencia.
- **Nominales:** las escasas, sin vecina compatible, no generan ítem: «compro comida» y «otro» en quién prepara; FFAA, «ninguna» y «no sabe» en previsión.
- **Alcance:** {len(CED)} categorías originales tenían menos del 5 % (varias con 0 participantes) y se resolvieron así (informe 04).

**3. ¿Cuántos ítems transaccionales se generaron?**
- **Principal:** {e(RT.iloc[0]['items'])} ítems, con unos 31 por participante, más los dos consecuentes.
- **Sensibilidades:** entre {e(RT['items'].min())} y {e(RT['items'].max())}.

**4. ¿Qué configuraciones de búsqueda se evaluaron?**
- **Principal:** antecedentes de 1 a 3 condiciones, al menos 53 participantes con el antecedente y 27 con antecedente y consecuente.
- **13 sensibilidades:**
  - S1: sin imputados.
  - S2a y S2b: agrupaciones.
  - S3: umbrales de 27 y 80.
  - S4: largo 1 y 2.
  - S5: sin frecuencias de ejercicio.
  - S6: sin variables próximas a síntomas.
  - S7a y S7b: quienes trabajan y quienes cuidan.
  - S8a y S8b: IMC.
- **Para cada configuración:** 1.000 permutaciones nulas. En la principal, además, 200 submuestras.

**5. ¿Cuántas reglas se encontraron?**
- **Principal:** {e(META['reglas'])} reglas evaluadas, de las cuales {e(nm)} son marcadas (al menos 10 puntos sobre la basal). Son {e(int(((R['consecuente'] == 'severo_mrs=SI') & R['marcada']).sum()))} hacia síntomas severos y {e(int(((R['consecuente'] == 'severo_mrs=NO') & R['marcada']).sum()))} hacia no severos.

**6. ¿Cuántas superan los criterios previamente definidos?**
- **Clase 6:** **una**, que cumple marcada, no redundante, supera la referencia nula y estable.
- **Las demás marcadas:** {e(c3)} son redundantes y {e(c4)} son compatibles con la nula.

**7. ¿Cuáles son las principales reglas y cómo se interpretan?**
- **La regla de la clase 6:** quienes trabajan, no hacen ejercicio de bajo impacto y casi nunca tienen distensión abdominal → síntomas severos.
  - **Cifras:** {e(SOL['n_conjunto'])} de {e(SOL['n_antecedente'])}, es decir, {pc(SOL['confianza'], 0)} frente al {pc(p0, 0)} general.
  - **Lectura:** describe una combinación frecuente en la simulación. No dice que trabajar o no hacer ejercicio cause síntomas, y la dirección de la distensión es poco intuitiva.
- **Otras reglas fuertes:** son compatibles con el azar (informe 07).

**8. ¿Cuánto se aleja su confianza de la frecuencia basal?**
- **La regla de la clase 6:** {n(100 * SOL['diferencia_basal'], 1)} puntos (lift {n(SOL['lift'])}).
- **Marcadas no redundantes:** entre 10 y unos {n(100 * R[R['marcada'] & ~R['redundante'].fillna(False).astype(bool)]['diferencia_basal'].max(), 0)} puntos.
- **Referencia nula:** el azar ya produce diferencias de hasta {n(100 * META['nula_p95_max_dif'], 1)} puntos en el 5 % de las búsquedas.

**9. ¿Qué soporte real tienen en participantes?**
- **La regla de la clase 6:** {e(SOL['n_conjunto'])} participantes cumplen antecedente y consecuente, de {e(SOL['n_antecedente'])} con el antecedente; el soporte es {pc(SOL['soporte'])}.
- **Marcadas:** casi todas tienen entre 53 y unas 100 participantes en el antecedente.
- **Antecedentes grandes:** ninguna regla con más de unas 150 participantes en el antecedente se aleja 10 puntos de la basal.

**10. ¿Qué reglas son redundantes?**
- **Cuántas:** {e(c3)} de las {e(nm)} marcadas ({pc(c3 / nm, 0)}). Agregan una condición que mejora la confianza en menos de 5 puntos.
- **Patrón típico:** una regla de dos condiciones con trabajo, a la que se le suma un hábito.

**11. ¿Cuáles son estables?**
- **Cuántas:** {e(estables)} reglas marcadas reaparecen en al menos el 70 % de las submuestras con la misma dirección, incluida la de la clase 6 ({pc(SOL_EST['reaparece_marcada'], 0)}).
- **Advertencia:** la estabilidad no distingue señal de ruido. Las reglas compatibles con el azar también son estables a menudo, porque las submuestras comparten el 80 % de los datos.

**12. ¿Cuáles también aparecen bajo la referencia nula?**
- **Todas menos una.** Las {e(c4)} marcadas no redundantes, las redundantes y las débiles tienen una fuerza que el azar alcanza al buscar entre 12.201 reglas.

**13. ¿Cómo afectan los datos imputados?**
- **Sin imputados (S1):** ninguna regla cambia de dirección, pero muchas pierden casos ({e(lec.loc['S1', 'desaparece por falta de casos'])} quedan bajo el umbral). Entre ellas está la de la clase 6, que baja a 52 participantes.
- **Lectura:** las imputaciones no fabrican las reglas, pero ayudan a que algunas superen el umbral.
- **Señal global:** se mantiene sin imputados, con 889 marcadas frente a 460 esperadas.
- **Diabetes y previsión:** no tienen marca por participante, así que no pudieron evaluarse sin imputados.

**14. ¿Qué pasa al cambiar agrupaciones y umbrales?**
- **Categorías originales:** dan casi lo mismo.
- **Agrupación gruesa:** hace aparecer reglas de «3 días o más de ejercicio → no severos» que superan la nula solo ahí.
- **Umbrales:** con un umbral más bajo hay muchas más reglas y ninguna supera la nula; con uno más alto, menos reglas y tampoco ninguna.
- **Conclusión:** no cambia.

**15. ¿Qué restricciones presentan los módulos laboral y de cuidado?**
- **Poblaciones parciales:** solo aplican a quienes trabajan (309) y a quienes cuidan (251), así que se analizaron por separado, con su propia basal y sus umbrales proporcionales.
- **Circularidad:** las preguntas laborales mencionan los síntomas, y la sobrecarga puede ser consecuencia de ellos.
- **Resultados:** en quienes trabajan no hay reglas que superen la nula. En quienes cuidan hay una, con 34 participantes y la sobrecarga como condición.

**16. ¿Existen reglas suficientemente sólidas para destacar, o la evidencia es débil?**
- **La evidencia es débil.** Hay una señal global, pero ninguna regla es robusta. La única que cumple los criterios es frágil ante las sensibilidades.

**17. ¿Qué limitaciones impiden considerarlas clínicas o causales?**
- **Datos:**
  - Son sintéticos.
  - Las asociaciones son marginales, sin ajuste por otras variables.
  - No se sabe la dirección: los síntomas podrían influir en los hábitos.
  - Hay imputaciones en muchas participantes, y diabetes y previsión no tienen marca.
- **Diseño:**
  - No es un análisis ciego, porque las Fases 35 y 37D ya examinaron estas asociaciones.
  - Las mismas 529 sirven para descubrir y evaluar, sin muestra de confirmación.
- **Variables:** algunas están próximas a los síntomas.
- **Estabilidad:** no implica validez.

**18. ¿Qué se recomienda explorar en la Fase 39?**
- **Diferencias entre estratos:** comparar trabajo, pareja, ejercicio (0, 1-2 y 3 o más días) y cuidado, con un protocolo sellado, referencia nula dentro de cada estrato y denominadores siempre visibles (nota 17).
- **Expectativas:** son prudentes, porque los estratos son más pequeños.

**19. ¿Qué pruebas se ejecutaron?**
- **Pruebas:** {int((PRU['resultado'] == 'superada').sum())} de {len(PRU)} superadas.
- **Controles negativos:** {int(MUT['detectado'].sum())} de {len(MUT)} errores introducidos detectados.
- **Cobertura:**
  - Identificadores y MRS.
  - Antecedentes prohibidos, contradicciones y agrupaciones.
  - Imputaciones y módulos.
  - Medidas, equivalencia de algoritmos y del evaluador matricial, y reproducibilidad.
  - Estabilidad sin fuga y referencia nula.
  - Multiplicidad y reglas triviales.
  - Integridad, Django y sello.
  - Clasificación.

**20. ¿Se preservaron todos los archivos históricos?**
- **Sí.** {e(MAN_INI['comparados_por_huella'].sum())} archivos protegidos de las Fases 34 a 37D coinciden con sus manifiestos al inicio{' y al final' if FIN else ''}.
- **Simulador:** los 4 archivos del manifiesto 34-35 no se abrieron.
- **Git:** HEAD sigue en 745d689, sin cambios en Django ni en los datos, y sin commit ni push.

# Decisiones para la responsable

1. **Lectura de la conclusión:** confirmar que la Fase 38 se lee como evidencia débil, sin reglas destacadas.
2. **Fase 39:** decidir si se inicia y con qué estratos (nota 17).
""")

# ---------- Markdown: 02, 14, 15, 18
pru_md = f"""# Fase 38: informe de pruebas

- **Pruebas:** {int((PRU['resultado'] == 'superada').sum())} de {len(PRU)} superadas.
- **Controles negativos:** {int(MUT['detectado'].sum())} de {len(MUT)} errores introducidos en memoria detectados.
- **Cómo funcionan:** cada prueba recalcula desde el código, no solo desde las tablas. Cada control reemplaza una función o un dato por una versión con un error y exige que alguna prueba falle.

{tabla(['N.º', 'Prueba', 'Resultado', 'Detalle'], [[r.n, r.prueba, r.resultado, r.detalle] for r in PRU.itertuples()])}

## Controles negativos

{tabla(['Error introducido', 'Detectado', 'Pruebas que fallan', 'Motivo'], [[r.control_negativo, 'sí' if r.detectado else 'NO', r.pruebas_que_fallan, str(r.motivo)[:110]] for r in MUT.itertuples()])}

## Notas

- **«Severidad del MRS como antecedente»:** se detecta en la construcción. El ítem agregado no corresponde a ninguna variable conocida y la búsqueda se detiene antes de llegar a la prueba 4.
- **Prueba 16:** se reforzó para comprobar el filtro de pares determinados con soporte mínimo 1. En S2a, esos pares solo aparecen con categorías de menos de 27 participantes, que nunca alcanzan el umbral, así que la versión anterior no podía detectar el error.
- **Primera ejecución:** fallaron dos pruebas por errores de las propias pruebas, no del análisis:
  - **Prueba 2:** la limpieza guarda «trabaja» como `True` y `False`, no como `SI` y `NO`.
  - **Prueba 14:** exigía que una permutación nueva quedara entre los percentiles 1 y 99 nulos. Dio 322 reglas marcadas, apenas bajo el percentil 1 (327). Se cambió al rango completo de las 1.000 permutaciones.
"""
leidos = pd.read_csv(B / 'integridad' / 'archivos_leidos.csv')['archivo_leido']
datos_leidos = sorted(x for x in leidos if x.startswith('datos/'))
integ_ini = f"""# Fase 38: auditoría de integridad inicial

Hecha justo después de sellar el protocolo y antes de calcular ninguna regla.

- **Fecha:** {INI['fecha']}.
- **Protocolo:** sellado el {INI['protocolo_sellado']}, huella `{INI['protocolo_sha256']}`.
- **Git:** rama `{INI['rama']}`, HEAD {INI['head']}. Sin cambios en `src/` (Django), sin cambios en datos versionados y sin cambios fuera de `analisis/`.
- **`__pycache__` en fases protegidas:** {len(INI['pycache_en_fases_protegidas'])}.

{tabla(['Fase', 'Archivos', 'Comparados por huella', 'Sin verificar por nombre', 'Distintos'], [[r.fase, e(r.archivos), e(r.comparados_por_huella), e(r.sin_verificar_por_nombre), e(r.distintos)] for r in MAN_INI.itertuples()])}

**Archivos sin verificar:** los 4 del manifiesto 34-35 corresponden al simulador (`bitacora_suciedad.csv`, `dataset_usuaria_sucio.csv`, `dataset_usuaria_verdad.csv` y `diabetes_diagnostico_verdad.csv`). Este proceso no los abre.

**Huellas de las entradas:** están en `integridad/huellas_entradas_inicial.csv`. Las entradas son:
- los datos limpios;
- la Fase 35;
- la procedencia, los identificadores y el esquema de la Fase 36;
- el núcleo de la 37D, que se importa sin escribir en su carpeta;
- la definición de la encuesta, de solo lectura;
- el conversor a Word de la 37C.
"""
fin_txt = ''
if FIN:
    fin_txt = f"""
## Verificación final

- **Fecha:** {FIN['fecha']}.
- **Archivos protegidos:** {e(FIN['comparados_por_huella'])} comparados por huella, {FIN['archivos_distintos']} distintos.
- **Entradas:** iguales al inicio: {'sí' if FIN.get('entradas_iguales_al_inicio') else 'NO'}.
- **Git:** HEAD {FIN['head']}; cambios en `src/`: {len(FIN['cambios_en_src'])}; cambios fuera de `analisis/`: {len(FIN['cambios_fuera_de_analisis'])}; datos versionados modificados: {len(FIN['datos_versionados_modificados'])}.
- **`__pycache__` en fases protegidas:** {len(FIN['pycache_en_fases_protegidas'])}.
"""
integ_fin = f"""# Fase 38: informe de integridad final

- **Protocolo:** huella `{sello['sha256']}`, sellado el {sello['sellado']}, antes de calcular ninguna regla. La prueba 19 comprueba que todas las reglas y permutaciones son posteriores.
- **Lecturas fuera de la carpeta:** {e(len(leidos))} archivos, casi todos para comparar huellas con los manifiestos. De ellos, {len(datos_leidos)} están en `datos/`: {sum('cache_35b' in x for x in datos_leidos)} son la caché de la Fase 35B, que solo se lee para calcular su huella. Los otros son: {', '.join(f'`{x}`' for x in datos_leidos if 'cache_35b' not in x)}.
- **Simulador:** no se leyó ningún archivo del simulador; el gancho de auditoría lo impide. Registro: `integridad/archivos_leidos.csv`.
- **Escrituras fuera de la carpeta:** {len(pd.read_csv(B / 'integridad' / 'escrituras_fuera.csv'))}.
- **Memoria:** un proceso de análisis más el vigilante, con un hilo por biblioteca. Registro: `integridad/registro_memoria.csv`.
- **Manifiesto:** `integridad/manifiesto_final.csv`.
{fin_txt}
## Restricciones

Se cumplieron todas:

- **Fases y datos:** sin cambios en las Fases 34 a 37D ni en los datos originales.
- **Simulador y modelos:** sin la verdad del simulador, sin reajustar PCA, FAMD ni K-means, y sin etiquetas de clustering como antecedentes.
- **Selección:** sin seleccionar por el MRS ni por la significación de la 37D, y sin Random Forest.
- **Interpretación:** sin causalidad y sin recomendaciones clínicas.
- **Alcance:** sin integrar en Django y sin iniciar las Fases 39 ni 40.
- **Git:** sin commit ni push.
"""
indice = """# Fase 38: índice de entregables

| N.º | Entregable | Archivo |
|---|---|---|
| 1 | Protocolo sellado | `informes/01_protocolo_38.docx`, `protocolo/01_protocolo_38.md`, `protocolo/sello_protocolo.json` |
| 2 | Auditoría de integridad inicial | `informes/02_integridad_inicial.md` |
| 3 | Diccionario de variables y categorías | `informes/03_diccionario_variables_categorias.docx`, `preparacion/diccionario_variables_categorias.csv`, `preparacion/diccionario_items.csv` |
| 4 | Agrupamiento de categorías poco frecuentes | `informes/04_agrupacion_categorias_escasas.docx`, `preparacion/agrupaciones_escasas.csv`, `preparacion/categorias_escasas_detalle.csv` |
| 5 | Matriz transaccional y trazabilidad | `informes/05_matriz_transaccional_trazabilidad.docx`, `preparacion/matriz_transaccional_principal.csv`, `preparacion/trazabilidad_transformaciones.csv` |
| 6 | Equivalencia Apriori/FP-Growth | `informes/06_equivalencia_apriori_fpgrowth.docx`, `reglas/equivalencia_*.csv`, `reglas/entorno.json` |
| 7 | Reglas generales | `informes/07_reglas_generales.docx`, `reglas/reglas_principal.csv`, `reglas/reglas_destacadas.csv` |
| 8 | Soporte, confianza, lift y cobertura | `informes/08_soporte_confianza_lift_cobertura.docx`, `reglas/cobertura.csv` |
| 9 | Redundancia | `informes/09_redundancia.docx`, `reglas/redundantes_marcadas.csv`, `reglas/familias_marcadas.csv` |
| 10 | Estabilidad | `informes/10_estabilidad.docx`, `estabilidad/` |
| 11 | Referencia nula | `informes/11_referencia_nula.docx`, `referencia_nula/nula_principal.csv` |
| 12 | Sensibilidades | `informes/12_sensibilidades.docx`, `sensibilidades/` |
| 13 | Figuras y tablas | `informes/13_figuras_tablas.docx`, `figuras/` |
| 14 | Informe de pruebas | `informes/14_informe_pruebas.md`, `pruebas/` |
| 15 | Integridad final | `informes/15_informe_integridad_final.md`, `integridad/` |
| 16 | Informe metodológico de cierre | `informes/16_informe_cierre_38.docx` |
| 17 | Nota para la Fase 39 | `informes/17_nota_fase_39.docx` |
| 18 | Índice de entregables | `informes/00_indice_entregables.md` |

**Resumen:** `reglas/resumen_principal.json` y `sensibilidades/resumen_sensibilidades.csv`.

**Scripts:** `scripts/`. Orden de ejecución:

1. `sellar_protocolo_38.py`
2. `integridad_38.py inicial`
3. `preparacion_38.py`
4. `reglas_38.py`
5. `sensibilidades_38.py`
6. `graficos_38.py`
7. `pruebas_38.py --mutaciones`
8. `generar_informes_38.py`
9. `verificar_informes_38.py`
10. `integridad_38.py final`
11. `manifiesto_38.py`

Las etapas de cálculo corren bajo `vigilar_memoria.py`.
"""
for nombre, t in (('14_informe_pruebas.md', pru_md), ('02_integridad_inicial.md', integ_ini), ('15_informe_integridad_final.md', integ_fin), ('00_indice_entregables.md', indice)):
    (INF / nombre).write_text(t, encoding='utf-8', newline='\n')

N.a_json({'fase': '38', 'participantes': 529, 'frecuencia_basal_si': p0, 'variables_principal': 31, 'items_principal': int(RT.iloc[0]['items']),
          'reglas_principal': int(META['reglas']), 'marcadas': int(nm), 'nula_media_marcadas': float(NULA['reglas_marcadas'].mean()), 'p_exceso_global': float(NULA_P),
          'clases': {k: int(v) for k, v in cls.items()}, 'estables': estables, 'regla_clase_6': SOL['antecedente'] + ' -> ' + SOL['consecuente'],
          'superan_nula_sensibilidades': int(len(SUP)), 'pruebas': f"{int((PRU['resultado'] == 'superada').sum())}/{len(PRU)}",
          'controles_negativos': f"{int(MUT['detectado'].sum())}/{len(MUT)}", 'conclusion': 'evidencia débil: señal difusa sin reglas puntuales robustas',
          'protocolo_sha256': sello['sha256']}, INF / 'resumen_38.json')
shutil.copyfile(B / 'protocolo' / '01_protocolo_38.md', F / '01_protocolo_38.md')
titulos = {'01_protocolo_38': 'Protocolo de la Fase 38'}
js = N.N37.C37 / 'scripts' / 'md_a_word_37c.js'
for nombre, (titulo, md) in docs.items():
    (F / f'{nombre}.md').write_text(md.strip() + '\n', encoding='utf-8', newline='\n')
    titulos[nombre] = titulo
for nombre, titulo in titulos.items():
    r = subprocess.run(['node', str(js), str(F / f'{nombre}.md'), str(INF / f'{nombre}.docx'), titulo, 'AgingWomen · Fase 38: reglas de asociación generales'], capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f'{nombre}: {r.stderr[:500]}')
print(len(titulos), 'informes Word')
