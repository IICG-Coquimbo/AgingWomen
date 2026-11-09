"""
Fase 38R, fase documental: fuentes Markdown y Word corregidos. Toda cifra se lee de las tablas ya validadas de la 38R; no calcula reglas ni permuta.
Deriva de la estructura de generar_informes_38.py, que no se modifica.

Uso: python -B generar_documentos_38r.py [números de los documentos por convertir a Word, p. ej. 03 04 07]
El paquete docx se instala con «npm ci» en documentos_definitivos/herramientas_word (ver LEEME.md).
"""
import json
import re
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
AQUI = Path(__file__).resolve().parent
DOC = AQUI.parent
B = DOC.parent
sys.path.insert(0, str(B / 'scripts'))
import nucleo_38r as NR  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from entorno_word import entorno_node  # noqa: E402

N = NR.H  # solo etiquetas legibles y constantes históricas de presentación
INF = DOC / 'word'
F = DOC / 'fuentes'
INF.mkdir(parents=True, exist_ok=True)
F.mkdir(parents=True, exist_ok=True)
SINT = ('Todo el análisis usa el conjunto **sintético** de 529 participantes. Las reglas describen lo que contiene la simulación: no son hechos sobre la menopausia '
        'en mujeres reales, no son diagnósticos ni predicciones y no permiten recomendaciones de salud. Ninguna asociación indica causa. No hay validación externa: '
        'es un análisis **exploratorio** y su utilidad clínica no está demostrada.')
VERSION = ('> **Versión correctiva (Fase 38R).** Corrige la Fase 38 histórica retirando de la matriz principal `prevision` y `usa_medicamentos_diabetes`, que las decisiones de las Fases 35 y 36 '
           'excluían del modelado. Ninguna de las dos es predictora autorizada y solo se nombran para documentar ese motivo. Todas las cifras de este documento provienen de los resultados '
           'corregidos; las cifras de la versión anterior no están vigentes. Las sensibilidades se identifican siempre como tales y no sustituyen al análisis principal.')


def n(x, d=2):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return '—'
    return f'{x:,.{d}f}'.replace(',', 'X').replace('.', ',').replace('X', '.').replace('-', '−')


def e(x):
    return f'{int(x):,}'.replace(',', '.')


def pc(x, d=1):
    return n(100 * x, d) + ' %'


def p_(x):
    return '< 0,001' if x < 0.001 else (n(x, 5) if 0.0495 <= x < 0.0505 else n(x, 3))


def tabla(cab, filas):
    def celda(c):
        return str(c).replace('|', '\\|')
    s = '| ' + ' | '.join(celda(c) for c in cab) + ' |\n|' + '---|' * len(cab) + '\n'
    return s + ''.join('| ' + ' | '.join(celda(c) for c in f) + ' |\n' for f in filas)


def fig(nombre, pie):
    return f'\n![{pie}](../figuras/{nombre})\n'


L = lambda r: pd.read_csv(B / r, encoding='utf-8')  # noqa: E731
J = lambda r: json.loads((B / r).read_text(encoding='utf-8'))  # noqa: E731
sello = J('protocolo/sello_protocolo.json')
DI = L('preparacion/diccionario_items.csv')
_it = DI[DI['item'] != '(sin ítem)']
DV = _it.groupby('variable', sort=False).agg(etiqueta=('etiqueta', 'first'), bloque=('bloque', 'first'), items=('item', 'count')).reset_index()
_det = {v: '; '.join(f"{N.legible(r.item).split(': ', 1)[1]} [{r.participantes}]" for r in t.itertuples()) for v, t in _it.groupby('variable', sort=False)}
ESC = _it[_it['regla'].str.startswith('R2')].rename(columns={'item': 'resultado', 'participantes': 'participantes_resultantes'})
SINITEM = DI[DI['item'] == '(sin ítem)']
RESERVADAS = [('IMC', 'S8b'), ('Lugar de trabajo comprensivo', 'S7a y S7a-309'), ('Estrés del entorno laboral', 'S7a y S7a-309'), ('Sobrecarga física o emocional por cuidar', 'S7b y S7b-251')]
EXC = pd.DataFrame([['prevision', 'Exclusión definitiva (decisiones de las Fases 35 y 36). No es predictora autorizada: motivo de esta corrección.'],
                    ['usa_medicamentos_diabetes', 'Exclusión definitiva (decisiones de las Fases 35 y 36). No es predictora autorizada: motivo de esta corrección.'],
                    ['doble_carga', 'Exclusión definitiva en toda configuración.'],
                    ['Ítems y puntaje del MRS', 'Definen el consecuente; nunca son antecedentes.'],
                    ['Segmentos y etiquetas de agrupamiento', 'Resultado de fases anteriores; no son antecedentes.'],
                    ['Etapa menopáusica', 'Solo descriptiva.']], columns=['variable', 'motivo'])
RT, TR = L('preparacion/resumen_transacciones.csv'), L('preparacion/trazabilidad_transformaciones.csv')
EQ, EQC, ENT = L('reglas/equivalencia_algoritmos.csv'), L('reglas/equivalencia_comparaciones.csv'), J('reglas/entorno.json')
R, META, COB = L('reglas/reglas_principal.csv'), J('reglas/resumen_principal.json'), L('reglas/cobertura.csv')
DEST, TOP, RED, FAM = L('reglas/reglas_destacadas.csv'), L('reglas/reglas_no_destacadas_mayor_z.csv'), L('reglas/redundantes_marcadas.csv'), L('reglas/familias_marcadas.csv')
NULA, EST, EFAM, SUB = L('referencia_nula/nula_principal.csv'), L('estabilidad/estabilidad_reglas.csv'), L('estabilidad/estabilidad_familias.csv'), L('estabilidad/submuestras.csv')
SR, LR, LEC, SUP, CLS = L('sensibilidades/resumen_sensibilidades.csv'), L('sensibilidades/lectura_resumen.csv'), L('sensibilidades/lectura_reglas_principal.csv'), \
    L('sensibilidades/superan_nula_sensibilidades.csv'), L('sensibilidades/clases_sensibilidades.csv')
PRU, MUT = L('pruebas/resultados_pruebas.csv'), L('pruebas/control_mutaciones.csv')
FIN = J('integridad/integridad_final.json')
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
ex = {x[0]: x for x in EXC_ROWS}
DESC = {k: v['descripcion'] for k, v in NR.CONFIGS.items()}
OBS_AMP = L('comparacion/observadas_frente_a_ampliadas.csv')
ROB = L('comparacion/evaluacion_robustez.csv').iloc[0]
MARC = R[R['marcada']]
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


# ---------- tablas recuperadas en los documentos 03 y 04. Los conteos se contrastan con las matrices de la 38R y la generación se detiene si no coinciden.
H38 = B.parent / '38_reglas_asociacion_generales' / 'preparacion'
DH = pd.read_csv(H38 / 'diccionario_variables_categorias.csv').set_index('variable')
DET = pd.read_csv(H38 / 'categorias_escasas_detalle.csv')
DET = DET[DET['variable'] != 'prevision'].reset_index(drop=True)
_ids = {'participante_id': str}
MP = pd.read_csv(B / 'preparacion' / 'matriz_transaccional_principal.csv', dtype=_ids).set_index('participante_id')
MS1 = pd.read_csv(B / 'preparacion' / 'sensibilidades' / 'matriz_S1.csv', dtype=_ids).set_index('participante_id').reindex(MP.index)
MS2 = pd.read_csv(B / 'preparacion' / 'sensibilidades' / 'matriz_S2a.csv', dtype=_ids).set_index('participante_id')
PREFIJO = {r.variable: r.item.split('=')[0] for r in _it.itertuples()}
PREPARA = {'YO_MAYORIA': ('prepara=yo_la_mayoria', 'Ella prepara la mayoría'), 'COMPARTIDO': ('prepara=compartido', 'Ella y otras personas'), 'OTRA_HOGAR': ('prepara=otra_persona_hogar', 'Otra persona del hogar'),
           'COMPRO': ('prepara=compra_preparada', 'Compro comida preparada'), 'OTRO': ('prepara=otro', 'Otro')}


def norm(x):
    return re.sub(r'[^a-z0-9]+', '_', x.lower().translate(str.maketrans('áéíóú', 'aeiou'))).strip('_')


def columna_s2a(v, cat):
    if v == 'quien_prepara_comidas':
        return PREPARA[cat][0]
    c = [x for x in MS2.columns if x.startswith(PREFIJO[v] + '=') and norm(x.split('=')[1]) == norm(cat)]
    return c[0] if c else None


def categorias(v):
    """(código, nombre, n) de cada categoría original, con el n contrastado con S2a."""
    salida = []
    for parte in DH.loc[v, 'categorias_originales'].split('; '):
        m = re.fullmatch(r'(?:(\d+) = )?(.+) \((\d+)\)', parte)
        cod, nombre, cuenta = m[1], m[2], int(m[3])
        col = columna_s2a(v, nombre)
        if (int(MS2[col].sum()) if col else 0) != cuenta:
            raise SystemExit(f'Categoría sin coincidencia con S2a: {v} {nombre} {cuenta}')
        salida.append((cod, PREPARA[nombre][1] if v == 'quien_prepara_comidas' else nombre, cuenta))
    return salida


def distribucion(v):
    t_ = DH.loc[v, 'categorias_originales']
    if not t_.startswith('numérica'):
        return '; '.join(f'{nom} ({e(k)})' for _, nom, k in categorias(v))
    cols = [x for x in MS2.columns if x.startswith(PREFIJO[v] + '=')]
    if int(MS2[cols].to_numpy().sum()) != 529:
        raise SystemExit(f'Los cortes de {v} no suman 529')
    return re.sub(r' \(n = \d+\)', '', t_).replace('numérica: ', 'Numérica: ') + '. Cortes (R5): ' + '; '.join(f"{N.legible(c).split(': ', 1)[1]} ({e(MS2[c].sum())})" for c in cols)


def heredadas(v):
    m = re.match(r'(\d+) con pregunta madre', str(DH.loc[v, 'nota_imputacion']))
    return int(m[1]) if m else 0


FILAS_OBS = []
for r in DV.itertuples():
    d = DH.loc[r.variable]
    its = [i for i in _it[_it['variable'] == r.variable]['item'] if i in MP.columns]
    con_p = int(MP[its].any(axis=1).sum())
    con_s = int(MS1[[i for i in its if i in MS1.columns]].any(axis=1).sum())
    if con_p - con_s != int(d.imputadas) + int(d.deducidas) + heredadas(r.variable):
        raise SystemExit(f'Observadas/imputadas sin coincidencia con S1: {r.variable}')
    FILAS_OBS.append([r.etiqueta, e(d.observadas), e(d.imputadas), e(d.deducidas), e(heredadas(r.variable)), e(con_p), e(con_s), e(con_p - con_s)])
ADV = DH['advertencias'].fillna('—')


def items_reservados(cfg, prefijo):
    M = pd.read_csv(B / 'preparacion' / 'sensibilidades' / f'matriz_{cfg}.csv', dtype=_ids)
    cols = [c for c in M.columns if c.startswith(prefijo + '=')]
    return len(M), int(M[cols].to_numpy().sum()), '; '.join(f"{c.split('=')[1].replace('_', ' ').replace('mas', 'más').replace('29.9', '29,9')} ({e(M[c].sum())})" for c in cols)


def cat_reservada(v):
    t_ = DH.loc[v, 'categorias_originales']
    if t_.startswith('numérica'):
        return t_.replace('numérica: ', 'Numérica: ').replace('18.2', '18,2').replace('28.5', '28,5').replace('45.7', '45,7')
    return re.sub(r'\d+ = ', '', t_)


FILAS_RES = []
for v, nombre, cfg, prefijo, poblacion, motivo in (
        ('imc', 'IMC', 'S8b', 'imc', 'S8a y S8b: 267 con IMC observado', 'Solo 267 valores observados; las 262 imputaciones no se usan.'),
        ('lugar_trabajo_comprensivo', 'Lugar de trabajo comprensivo', 'S7a', 'lugar_comprensivo', 'S7a: 287. S7a-309: 309; las 22 añadidas tienen el trabajo imputado y no tienen ítem laboral', 'Solo quienes trabajan. La pregunta menciona los síntomas («frente a estos síntomas»): riesgo de circularidad.'),
        ('estres_entorno_laboral', 'Estrés del entorno laboral', 'S7a', 'estres_laboral', 'S7a: 287. S7a-309: 309; las 22 añadidas tienen el trabajo imputado y no tienen ítem laboral', 'Solo quienes trabajan. La pregunta menciona los síntomas («que intensifiquen sus síntomas»): riesgo de circularidad.'),
        ('sobrecarga_fisica_emocional', 'Sobrecarga física o emocional por cuidar', 'S7b', 'sobrecarga', 'S7b: 239 con sobrecarga observada. S7b-251: 251, incluye las 12 imputadas', 'Solo quienes cuidan. Puede ser consecuencia de los síntomas: riesgo de circularidad.')):
    d = DH.loc[v]
    n_m, n_i, txt_i = items_reservados(cfg, prefijo)
    if n_i != int(d.observadas) + (0 if v in ('imc', 'sobrecarga_fisica_emocional') else int(d.imputadas)) or n_m != n_i:
        raise SystemExit(f'Reservada sin coincidencia con la matriz: {v} {n_m} {n_i}')
    FILAS_RES.append([nombre, poblacion, f'{e(d.observadas)} / {e(d.imputadas)} / {e(heredadas(v))}', cat_reservada(v), txt_i, motivo])

FILAS_ESC, FILAS_CERO = [], []
for r in DET.itertuples():
    col = columna_s2a(r.variable, r.categoria_original)
    if (int(MS2[col].sum()) if col else 0) != r.participantes:
        raise SystemExit(f'Categoría escasa sin coincidencia: {r.variable} {r.categoria_original}')
    nombre = PREPARA[r.categoria_original][1] if r.variable == 'quien_prepara_comidas' else r.categoria_original
    if r.participantes == 0:
        item = DI[DI['item'] == r.destino].iloc[0]
        cod = next(c for c, nom, _ in categorias(r.variable) if nom == nombre)
        if cod not in str(item.codigos_originales).split(','):
            raise SystemExit(f'Código de n = 0 fuera del ítem: {r.variable} {nombre}')
        FILAS_CERO.append([N.ETIQUETA[r.variable], nombre, '0', f'Ninguna participante la eligió y S2a no tiene columna. Figura como código {cod} de «{N.legible(r.destino)}» (códigos {item.codigos_originales}), sin aportarle casos.'])
    else:
        FILAS_ESC.append([N.ETIQUETA[r.variable], nombre, e(r.participantes), pc(r.participantes / 529), 'Sin ítem (R3: nominal escasa, sin vecina compatible)' if r.destino.startswith('(sin') else N.legible(r.destino)])
if len(FILAS_ESC) != 27 or len(FILAS_CERO) != 10 or not set(DET['variable']) <= set(DV['variable']):
    raise SystemExit(f'Filas de categorías escasas inesperadas: {len(FILAS_ESC)} y {len(FILAS_CERO)}')
FILAS_R3 = [[N.ETIQUETA[r.variable], f'Sin ítem: {PREPARA[r.codigos_originales][1].lower()}', f'{PREPARA[r.codigos_originales][1]} (código {r.codigos_originales})', e(r.participantes), r.regla] for r in SINITEM.itertuples()]


def clase_sens(c):
    return 'Supera la nula de su sensibilidad (estabilidad no evaluada; no es la clase 6 del protocolo)' if c.startswith('5-6') else c[2:]


docs = {}

# ---------- 03 diccionario
docs['03_diccionario_variables_categorias'] = ('Diccionario de variables y categorías', f"""
# Alcance

{SINT}

El diccionario describe las {len(DV)} variables del análisis principal y los {len(_it)} ítems que generan. Otras {len(RESERVADAS)} variables solo entran en sensibilidades.

- **Significado de las respuestas:** viene de las definiciones de la Fase 36, del diccionario de la limpieza y del texto de cada pregunta en la encuesta. No se dedujo del nombre de las variables.
- **Detalle por ítem:** `preparacion/diccionario_items.csv`.

# Variables

{tabla(['Variable', 'Bloque', 'Ítems', 'Ítems resultantes [n]', 'Uso', 'Advertencias'], [[r.etiqueta, r.bloque, e(r.items), _det[r.variable], 'análisis principal', ADV[r.variable]] for r in DV.itertuples()])}

# Distribución de categorías originales

Número de participantes en cada categoría antes de agrupar, de las 529. Cada conteo se contrastó con la matriz S2a de la 38R, que conserva las categorías originales. En las dos variables numéricas, el resumen viene del diccionario de la Fase 38 histórica (no cambia al retirar las dos variables excluidas) y sus cortes se contrastaron con S2a.

{tabla(['Variable', 'Categorías originales (n)'], [[r.etiqueta, distribucion(r.variable)] for r in DV.itertuples()])}

# Variables observadas e imputadas

{tabla(['Variable', 'Observadas', 'Imputadas', 'Deducidas', 'Heredadas de la pregunta madre', 'Con ítem en la principal', 'Con ítem en S1', 'Pierden el ítem en S1'], FILAS_OBS)}

**Imputaciones heredadas de preguntas madre:**
- **Preguntas condicionadas:** en cuidado y en las tres frecuencias de ejercicio, observadas e imputadas cuentan solo las celdas con respuesta sustantiva. Por eso no suman 529: «no cuida» y «no lo realiza» conservan su ítem (R6) y no se incluyen.
- **Heredadas:** la celda de la pregunta condicionada existe, pero su pregunta madre (si cuida, si hace ese ejercicio) fue imputada. La lista corresponde a {sum(1 for f in FILAS_OBS if f[4] != '0')} variables.
- **Sensibilidad S1:** quita el ítem cuando la celda es imputada o deducida y también cuando su pregunta madre fue imputada. La última columna coincide en las {len(FILAS_OBS)} variables con imputadas + deducidas + heredadas; la generación del documento se detiene si no coincide.
- **Quién prepara las comidas:** observadas e imputadas suman 529, pero solo 500 tienen ítem, porque «compro comida preparada» y «otro» no lo generan (R3).

# Variables reservadas para sensibilidades

No pertenecen al análisis principal. Los ítems se leyeron de las matrices de la 38R; observadas, imputadas y heredadas se contrastaron con esas mismas matrices.

{tabla(['Variable', 'Población', 'Observadas / imputadas / heredadas', 'Categorías originales (n)', 'Ítems en la matriz 38R [n]', 'Motivo de la reserva'], FILAS_RES)}

# Advertencias metodológicas

- **Frecuencias de ejercicio:** son redundantes con los días de ejercicio; la sensibilidad S5 las quita.
- **Próximas a síntomas:** actividad sexual, distensión abdominal y evacuación intestinal pueden formar parte de la propia experiencia de síntomas; la sensibilidad S6 las quita.
- **Módulos laboral y de cuidado:** solo existen en subpoblaciones y pueden ser circulares, por lo que no entran en la matriz principal.
- **Imputaciones:** la sensibilidad S1 indica cuánto se apoya cada regla en ellas.
- **Conjunto sintético:** nada de este diccionario describe a mujeres reales.

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

Son {len(FILAS_ESC)} categorías con entre 1 y 26 participantes. El porcentaje se calcula sobre las 529 y cada n se contrastó con la matriz S2a de la 38R. No incluye variables retiradas.

{tabla(['Variable', 'Categoría original', 'n', '%', 'Destino'], FILAS_ESC)}

**Categorías con n = 0** ({len(FILAS_CERO)}): están en el formulario, pero ninguna participante las eligió.

{tabla(['Variable', 'Categoría original', 'n', 'Tratamiento'], FILAS_CERO)}

# Ítems resultantes

{tabla(['Variable', 'Ítem', 'Códigos unidos', 'Participantes', 'Regla'], [[N.ETIQUETA[r.variable], N.legible(r.resultado), r.codigos_originales, e(r.participantes_resultantes), r.regla] for r in ESC.itertuples()] + FILAS_R3)}

# Decisiones

- **Quién prepara las comidas:** {' y '.join(f'«{PREPARA[r.codigos_originales][1].lower()}» ({r.participantes})' for r in SINITEM.itertuples())} no se mezclan con ninguna otra categoría, porque sus significados son distintos. Esas {e(SINITEM['participantes'].sum())} participantes no tienen ítem en esta variable.
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
- **Participantes sin ítem en una variable:** solo por faltantes reales (en la principal, ninguno) o por la regla R3: {e(SINITEM['participantes'].sum())} en quién prepara las comidas.
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
- **Sin robustez:** conserva sus medidas descriptivas y su clase, pero se mantiene solo en {e(ROB['se_mantiene'])} de las {e(ROB['evaluables'])} sensibilidades evaluables y supera la nula en {e(ROB['supera_nula_en'])} (informe 12).
- **Lectura:** describe una combinación del conjunto sintético, no un mecanismo. No está validada clínicamente y no es una recomendación individual.
"""
docs['07_reglas_generales'] = ('Resultados de reglas generales', f"""
<!-- apaisada -->

# Resumen

{SINT}

- **Búsqueda principal:** se evaluaron **{e(META['reglas'])} reglas** de 1 a 3 condiciones, todas las combinaciones con al menos 53 participantes en el antecedente. Es el **análisis principal**; las sensibilidades se presentan aparte (informe 12).
- **Marcadas:** {e(nm)} se alejan al menos 10 puntos de la frecuencia basal. Bajo la referencia nula aparecen {e(round(NULA['reglas_marcadas'].mean()))} marcadas en promedio, con un percentil 95 de {e(round(NULA['reglas_marcadas'].quantile(0.95)))}.
- **Señal difusa:** hay más reglas marcadas de lo que produce el azar (p = {p_(NULA_P)}). La relación entre hábitos y severidad no es nula en los datos sintéticos, pero está repartida en muchas combinaciones débiles. Este exceso global no hace significativa ninguna regla individual.
- **Reglas que superan la referencia nula:** solo **{META['supera_nula']}** regla supera la nula de toda la búsqueda. Cumple además los criterios de estabilidad y no redundancia, así que es la **única de la clase 6**. No es robusta (informe 12).
- **Benjamini-Hochberg:** sobre todas las reglas, ninguna tiene q < 0,05; el mínimo es {n(R['q_bh_todas'].min(), 3)}.

# Clasificación de todas las reglas

{tabla(['Clase', 'Reglas', '→ severos', '→ no severos'], [[k[2:], e(v), e(((R['clase'] == k) & (R['consecuente'] == 'severo_mrs=SI')).sum()), e(((R['clase'] == k) & (R['consecuente'] == 'severo_mrs=NO')).sum())] for k, v in cls.sort_index().items()])}

- **Asociación débil:** la confianza está a menos de 10 puntos de la frecuencia basal.
- **Redundante:** agregar una condición mejora la confianza en menos de 5 puntos respecto de una regla más simple.
- **Compatible con la referencia nula:** su fuerza está dentro de lo que aparece al buscar entre {e(META['reglas'])} reglas sin ninguna relación real.
- **Inestables:** ninguna regla queda en esta clase.
{sol_txt}
# Reglas más fuertes que no destacan

La tabla muestra, para cada consecuente, las 10 reglas no redundantes con mayor |z|. **No son hallazgos:** salvo la primera, todas son compatibles con la referencia nula. Se muestran para que se vea qué hay y no quede oculto.

{tabla_reglas(TOP)}

**Patrones que se repiten:**
- **Con los síntomas severos:** trabajar, no hacer ejercicio (0 días o sin bajo impacto) y frecuencias intermedias de algunos alimentos.
- **Con los síntomas no severos:** no trabajar, tener pareja y algunos hábitos de alimentación.

Ninguno supera la referencia nula salvo la regla de la clase 6. Los patrones son coherentes con las asociaciones pequeñas de la Fase 37D (trabajo y ejercicio), pero esta fase no las confirma de forma independiente.

<!-- vertical -->

{fig('f07_reglas_mayor_z.png', 'Figura 7. Reglas más fuertes de la búsqueda principal.')}
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
- **Antecedentes pequeños:** la mediana de n_A entre las marcadas es {e(MARC['n_antecedente'].median())} y el 90 % tiene {e(MARC['n_antecedente'].quantile(0.9))} participantes o menos.
- **Antecedentes grandes:** ninguna regla con más de {e(MARC['n_antecedente'].max())} participantes en el antecedente se aleja 10 puntos de la basal.
- **Por qué:** es lo esperable cuando las asociaciones son pequeñas. Solo los grupos chicos, más variables por azar, alcanzan diferencias grandes.

{fig('f02_confianza_frente_a_casos.png', 'Figura 2. Confianza de cada regla según n_A, con el umbral de la referencia nula.')}

# Cobertura

La cobertura es la proporción de las 529 que cumple al menos una regla del conjunto.

{tabla(['Conjunto', 'Consecuente', 'Reglas', 'Participantes cubiertas', 'Cobertura', 'Confianza media'], [[r.conjunto, 'severos' if r.consecuente.endswith('SI') else 'no severos', e(r.reglas), e(r.participantes_cubiertas), pc(r.cobertura), pc(r.confianza_media) if not pd.isna(r.confianza_media) else '—'] for r in COB.itertuples()])}

- **Marcadas:** cubren casi a todas las participantes. Con {e(nm)} reglas, casi cualquier persona cumple alguna.
- **Clase 6:** la única regla que cumple los criterios del protocolo, sin robustez en las sensibilidades, cubre a {e(SOL['n_antecedente'])} participantes ({pc(SOL['n_antecedente'] / 529)}).

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
  - Desaparecen en promedio {e(round(SUB['desaparecidas'].mean()))} de las {e(nm)}.
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
- **Exceso global no es significancia individual.** El exceso de reglas marcadas no convierte en significativa a ninguna regla concreta; cada regla se juzga por su p ajustado.
- **En conjunto, hay más reglas que por azar.** Sin relación real aparecen unas {e(round(NULA['reglas_marcadas'].mean()))} reglas marcadas; en los datos hay {e(nm)}. La diferencia indica una asociación real en la simulación, pero repartida y débil.
- **Ninguna regla puntual sobresale con claridad.** La mayor diferencia observada ({n(100 * R['diferencia_basal'].abs().max(), 1)} puntos) es parecida a la que el azar produce en el 5 % de las búsquedas ({n(100 * META['nula_p95_max_dif'], 1)} puntos). Solo una regla supera el umbral, y por poco (p = {p_(R['p_ajustado_busqueda'].min())}).
- **Reglas que aparecen fácilmente bajo la nula:** las {e(c4)} reglas marcadas no redundantes de la clase 4, más todas las débiles y las redundantes. Su fuerza está dentro de lo que el azar produce al buscar entre {e(META['reglas'])} reglas.

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

**Lectura general (son resultados de sensibilidad, no del análisis principal):**
- **Exceso global:** en {sum(1 for x in EXC_ROWS[1:] if x[6] < 0.05)} de las {len(EXC_ROWS) - 1} sensibilidades hay más reglas marcadas que por azar (p < 0,05); no en {', '.join(x[0] for x in EXC_ROWS[1:] if x[6] >= 0.05)}. Es una señal difusa: un exceso global no hace significativa ninguna regla individual.
- **Reglas que superan su nula:** {e(len(SUP))} casos en {SUP['configuracion'].nunique()} sensibilidades. Solo se repiten la regla de la clase 6 (S2a) y la de sobrecarga, que aparece en las dos poblaciones de cuidadoras (S7b y S7b-251).
- **Ninguna regla puntual es robusta.**

{fig('f05_exceso_frente_a_nula.png', 'Figura 5. Exceso de reglas marcadas sobre la referencia nula.')}

# Qué ocurre con las {e(nm)} reglas marcadas de la principal

{tabla(['Configuración', 'Se mantiene', 'Se debilita', 'Cambia de dirección', 'Desaparece por falta de casos', 'No evaluable'], [[cfg, *fila_lec(cfg)] for cfg in lec.index])}

{fig('f06_lectura_sensibilidades.png', 'Figura 6. Reglas de la principal en cada sensibilidad.')}

- **Cambios de dirección:** son pocos y solo ocurren en las subpoblaciones (S7 y S8). Cuando una regla se pierde es porque **se debilita o le faltan casos**, no porque se invierta.
- **«No evaluable»:** la regla usa una variable retirada en esa configuración, un ítem que no existe con otra agrupación, o más condiciones de las permitidas.

# Poblaciones de S7a y S7b: observadas y ampliadas

Las sensibilidades de los módulos se analizan solo en la población a la que se aplica cada pregunta, y cada una se identifica con su tamaño:

{tabla(['Configuración', 'Población', 'n', 'Reglas', 'Marcadas', 'Superan la nula'], [[c_, d_, e(ex[c_][1]), e(ex[c_][2]), e(ex[c_][3]), e(ex[c_][7])] for c_, d_ in (('S7a', 'Trabajadoras con información laboral'), ('S7a-309', 'Población laboral ampliada'), ('S7b', 'Cuidadoras con sobrecarga observada'), ('S7b-251', 'Población de cuidadoras ampliada (12 con sobrecarga imputada)'))])}

{tabla(['Comparación', 'Marcadas en la primera', 'Marcadas en la segunda', 'Marcadas en ambas'], [[r.comparacion, e(r.marcadas_a), e(r.marcadas_b), e(r.marcadas_en_ambas)] for r in OBS_AMP.itertuples()])}

- **S7a (287):** quienes trabajan y tienen información laboral; 263 tienen ambas respuestas observadas y 24 alguna imputada. **S7a-309** amplía a todas quienes trabajan.
- **S7b (239):** cuidadoras con sobrecarga observada. **S7b-251** añade 12 con sobrecarga imputada.
- **Circularidad:** las preguntas laborales mencionan los síntomas y la sobrecarga puede ser consecuencia de ellos.

# La regla de la clase 6 en cada sensibilidad

{tabla(['Configuración', 'n_A', 'Confianza', 'Diferencia', 'Lectura', 'Supera la nula'], [[r.configuracion, e(r.n_antecedente) if not pd.isna(r.n_antecedente) else '—', pc(r.confianza) if not pd.isna(r.confianza) else '—', f'{n(100 * r.diferencia_basal, 1)} pts' if not pd.isna(r.diferencia_basal) else '—', r.lectura, {True: 'sí', False: 'no'}.get(r.supera_nula, '—') if not pd.isna(r.supera_nula) else '—'] for r in LS.itertuples()])}

La regla **mantiene sus medidas descriptivas y su clasificación en el análisis principal, pero no cumple los criterios de robustez**. De las {e(ROB['sensibilidades'])} sensibilidades, {e(ROB['evaluables'])} son evaluables:
- **Se mantiene ({e(ROB['se_mantiene'])}):** S2a, donde además supera la nula, y S3-bajo, S7b y S7b-251, donde es compatible con ella.
- **Desaparece por falta de casos ({e(ROB['desaparece'])}):** S1 (n_A {e(LS.set_index('configuracion').loc['S1', 'n_antecedente'])}), S3-alto (umbral 80), S8a y S8b (n_A 23).
- **No evaluable (7):** S2b, S4-1, S4-2, S5, S6, S7a y S7a-309. En S7a y S7a-309, «trabaja» es constante.
- **Clínicamente:** no es una regla validada ni una recomendación individual.

<!-- apaisada -->

# Reglas que superan la nula en alguna sensibilidad

{tabla(['Configuración', 'Antecedente', 'Consecuente', 'n_A (n)', 'Confianza', 'Basal', 'p ajustado', 'Redundante', 'Clase'], [[r.configuracion, N.legible_regla(r.antecedente), 'severos' if r.consecuente.endswith('SI') else 'no severos', f'{e(r.n_antecedente)} ({e(r.n)})', pc(r.confianza), pc(r.frecuencia_basal), p_(r.p_ajustado_busqueda), 'sí' if r.redundante else 'no', clase_sens(r.clase)] for r in SUP.itertuples()])}

**S2b (agrupación gruesa): dos reglas superan su referencia nula.**
- **Primera, no redundante:** comidas fuera de casa nunca o 1-2 veces por semana y 3 días o más de ejercicio → síntomas no severos (p ajustado {p_(SUP[SUP['configuracion'] == 'S2b'].iloc[0]['p_ajustado_busqueda'])}).
- **Segunda, redundante:** ejercicio de bajo impacto de rara vez a siempre, sin medicamentos para la presión y sin tabaco → síntomas no severos (p ajustado {p_(SUP[SUP['configuracion'] == 'S2b'].iloc[1]['p_ajustado_busqueda'])}).
- **Cómo leerlas:** solo existen con los ítems agrupados de S2b, no son evaluables en la principal y no se repiten en otra configuración. **No son evidencia confirmatoria.** El corte de «3 días o más» se fijó en el protocolo, sin ver resultados.

**S7b y S7b-251 (cuidadoras):** sin ejercicio aeróbico, 3-4 vasos de agua y sobrecarga frecuente o siempre → síntomas severos, con 34 participantes. La sobrecarga puede reflejar los mismos síntomas. Es exploratoria y no es una recomendación.

<!-- vertical -->

# Detalles por sensibilidad

**S1 (sin valores imputados):**
- **Qué cambia:** las celdas imputadas no generan ítem.
- **Efecto:** muchas reglas pierden casos ({e(lec.loc['S1', 'desaparece por falta de casos'])} desaparecen por esa razón), pero ninguna cambia de dirección.
- **Lectura:** las imputaciones de la limpieza no fabrican las reglas, pero sí aportan casos que las sostienen sobre el umbral.

**S2a y S2b (agrupaciones):**
- **Categorías originales:** dan resultados casi iguales a la principal.
- **Agrupación gruesa:** cambia los ítems, así que la mayoría de las reglas no es comparable.

**S3 (umbrales):**
- **Umbral del 5 %:** produce {e(ex['S3-bajo'][2])} reglas y ninguna supera la nula.
- **Umbral del 15 %:** produce {e(ex['S3-alto'][2])} reglas, también ninguna.
- **Lectura:** bajar el umbral no revela reglas más sólidas; solo agrega ruido.

**S4 (largo):**
- **Una condición:** hay {e(ex['S4-1'][3])} reglas marcadas, frente a {n(ex['S4-1'][4], 1)} en promedio bajo el azar (p = {p_(ex['S4-1'][6])}), y ninguna supera la nula.
- **Hasta dos condiciones:** {e(ex['S4-2'][3])} marcadas frente a {n(ex['S4-2'][4], 1)} (p = {p_(ex['S4-2'][6])}); tampoco aparece ninguna regla que supere la nula.

**S5 y S6 (variables excluidas de esa sensibilidad):**
- **S5:** quitar las frecuencias de ejercicio no cambia la conclusión.
- **S6:** quitar las variables próximas a síntomas tampoco la cambia; la regla de la clase 6 deja de ser evaluable.

**S8 (IMC observado, n = 267):**
- **Resultado:** con o sin las categorías de IMC, ninguna regla supera la nula.
- **Cambios de dirección:** las {e(lec.loc['S8a', 'cambia de dirección'])} reglas que cambian de dirección en S8 se deben a la subpoblación, no al IMC: son las mismas en S8a y S8b.
""")

# ---------- 13 figuras y tablas
figs = sorted((DOC / 'figuras').glob('*.png'))
tablas = sorted(p.relative_to(B).as_posix() for d in ('preparacion', 'reglas', 'estabilidad', 'referencia_nula', 'sensibilidades') for p in (B / d).rglob('*') if p.suffix in ('.csv', '.json') and 'lotes' not in p.parts)
PIES = {'f01_items_principal.png': 'Figura 1. Ítems del análisis principal, con las participantes de cada ítem y los umbrales de 27 y 53.'}
for _, md_ in docs.values():
    PIES.update({m[2]: m[1] for m in re.finditer(r'!\[(.*?)\]\(\.\./figuras/(.+?)\)', md_)})
docs['13_figuras_tablas'] = ('Figuras y tablas', f"""
# Contenido

{SINT}

Hay {len(figs)} figuras, generadas desde las tablas corregidas con `documentos_definitivos/scripts/figuras_38r.py`, y {len(tablas)} tablas de respaldo. Los lotes de permutaciones y submuestras están en `referencia_nula/` y `sensibilidades/lotes/`, y sirven para reanudar si se interrumpe la ejecución.

# Tablas

{tabla(['Archivo'], [[t] for t in tablas])}

# Figuras
""" + '\n'.join(fig(p.name, PIES[p.name]) for p in figs))

# ---------- 17 nota fase 39
MT['trabaja'] = MT['trabaja=SI']
estr = []
for nombre, cols in (('Trabajo', ['trabaja=SI', 'trabaja=NO']), ('Pareja', ['pareja=SI', 'pareja=NO']),
                     ('Días de ejercicio', ['dias_ejercicio=0_dias', 'dias_ejercicio=1-2_dias', 'dias_ejercicio=3-4_dias', 'dias_ejercicio=5-6_dias_o_todos_los_dias']),
                     ('Cuidado', ['cuida=no_cuida', 'cuida=1_persona', 'cuida=2_personas', 'cuida=3_o_mas_personas'])):
    for c in cols:
        m = MT[c] == 1
        estr.append([nombre, N.legible(c).split(': ', 1)[1], e(m.sum()), e(MT.loc[m, 'severo_mrs=SI'].sum()), pc(MT.loc[m, 'severo_mrs=SI'].mean()), e(int(np.ceil(0.10 * m.sum())))])
docs['17_nota_fase_39R'] = ('Nota sobre las subpoblaciones de la Fase 39R', f"""
# Alcance

Esta nota conserva la organización de la nota preparatoria original. **La Fase 39R ya se ejecutó con su propio protocolo sellado:** sus resultados están en `analisis/fase39/39R_asociaciones_condicionadas_corregidas/`. Esta nota no ejecuta ninguna comparación entre subpoblaciones.

{SINT}

# Punto de partida

La Fase 38R encontró una **señal difusa**: más reglas que por azar, pero ninguna regla general robusta. Los patrones que más se repiten (trabajo, ejercicio, pareja) son las mismas variables que definen las subpoblaciones. Dentro de cada estrato el n baja y el azar pesa más.

# Subpoblaciones y tamaños

{tabla(['Dimensión', 'Estrato', 'Participantes', 'Con síntomas severos', 'Basal del estrato', 'Antecedente mínimo (10 %)'], estr)}

- **Basales distintas:** varían entre estratos, así que las reglas deben compararse con la basal de **su** estrato, no con el 53,1 % general.
- **Estratos pequeños:** los de ejercicio de 3-4 días (52) y de 5 días o más (27) son demasiado chicos para buscar reglas propias. Por eso la Fase 39R usó la agrupación «3 días o más» (79), la misma de B1 y de S2b, fijada de antemano.
- **Cuidado:** por la misma razón, la Fase 39R comparó a quienes cuidan (251) con quienes no cuidan (278), sin separar por número de personas cuidadas.

# Riesgos que se mantuvieron presentes

- **Circularidad:** el módulo laboral menciona los síntomas, y la sobrecarga puede ser consecuencia de ellos.
- **Variables próximas a síntomas:** actividad sexual, distensión y evacuación.
- **Imputaciones:** muchas reglas pierden casos sin imputados.
- **Estratos y reglas pequeños:** varios estratos tienen menos de 100 participantes, lo que limita la precisión.
""")

# ---------- 16 informe metodológico de cierre (20 preguntas)
_ls6 = LS.set_index('configuracion')
if not (_ls6.loc['S1', 'lectura'] == _ls6.loc['S3-alto', 'lectura'] == 'desaparece por falta de casos' and _ls6.loc['S3-bajo', 'lectura'] == 'se mantiene' and not bool(_ls6.loc['S3-bajo', 'supera_nula'])):
    raise SystemExit('La lectura de la regla de la clase 6 en S1 y S3 no coincide con el texto del informe 16')
docs['16_informe_cierre_38'] = ('Informe metodológico de cierre de la Fase 38', f"""
# Conclusión

**La evidencia de reglas de asociación es débil.**

- **Señal difusa:** en los datos sintéticos hay más combinaciones de hábitos y contexto asociadas con la severidad de lo que produciría el azar ({e(nm)} reglas marcadas frente a {e(round(NULA['reglas_marcadas'].mean()))} esperadas). Esa señal está repartida en muchas reglas débiles.
- **Reglas puntuales:** de {e(META['reglas'])} reglas, **solo una cumple todos los criterios sellados**, y lo hace por poco. Además:
  - incluye una variable próxima a síntomas;
  - desaparece sin imputados (S1, n_A {e(_ls6.loc['S1', 'n_antecedente'])}) y con el umbral más alto (S3-alto);
  - con el umbral más bajo (S3-bajo) se mantiene, pero no supera su referencia nula.
- **Conclusión:** **no hay reglas suficientemente sólidas para destacar como hallazgos.** Los patrones que más se repiten (trabajar y no hacer ejercicio con síntomas severos; no trabajar y tener pareja con síntomas no severos) coinciden con las asociaciones pequeñas de la Fase 37D, pero esta fase no las confirma de forma independiente.

{SINT}

# Respuestas

**1. ¿Cuántas variables se utilizaron?**
- **Análisis principal:** {len(DV)} variables generales medidas en las 529 participantes.
- **Sensibilidades:** 4 más, cada una solo en su sensibilidad: el IMC, las dos preguntas laborales y la sobrecarga.
- **Excluidas:** el MRS (solo como consecuente), los segmentos, la etapa menopáusica y, de forma definitiva, las variables retiradas por esta corrección.
- **Criterio:** ninguna variable se eligió por su asociación con el MRS.

**2. ¿Cómo se agruparon las categorías poco frecuentes?**
- **Regla fija:** se aplicó la regla del protocolo, sin mirar el MRS: una categoría ordinal con menos de 27 participantes se une a su vecina de menor frecuencia.
- **Nominales:** las escasas, sin vecina compatible, no generan ítem: «compro comida» y «otro» en quién prepara.
- **Alcance:** {len(ESC)} ítems resultan de unir categorías escasas (informe 04).

**3. ¿Cuántos ítems transaccionales se generaron?**
- **Principal:** {e(RT.iloc[0]['items'])} ítems, con unos {n(RT.iloc[0]['items_por_transaccion_media'], 0)} por participante, más los dos consecuentes.
- **Sensibilidades:** entre {e(RT['items'].min())} y {e(RT['items'].max())}.

**4. ¿Qué configuraciones de búsqueda se evaluaron?**
- **Principal:** antecedentes de 1 a 3 condiciones, al menos 53 participantes con el antecedente y 27 con antecedente y consecuente.
- **15 sensibilidades:**
  - S1: sin imputados.
  - S2a y S2b: agrupaciones.
  - S3: umbrales de 27 y 80.
  - S4: largo 1 y 2.
  - S5: sin frecuencias de ejercicio.
  - S6: sin variables próximas a síntomas.
  - S7a y S7a-309: quienes trabajan (287 con información laboral y 309 ampliada).
  - S7b y S7b-251: quienes cuidan (239 con sobrecarga observada y 251 ampliada).
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
- **Marcadas:** la mediana de n_A es {e(MARC['n_antecedente'].median())} y el 90 % tiene {e(MARC['n_antecedente'].quantile(0.9))} o menos.
- **Antecedentes grandes:** ninguna regla con más de {e(MARC['n_antecedente'].max())} participantes en el antecedente se aleja 10 puntos de la basal.

**10. ¿Qué reglas son redundantes?**
- **Cuántas:** {e(c3)} de las {e(nm)} marcadas ({pc(c3 / nm, 0)}). Agregan una condición que mejora la confianza en menos de 5 puntos.
- **Patrón típico:** una regla de dos condiciones con trabajo, a la que se le suma un hábito.

**11. ¿Cuáles son estables?**
- **Cuántas:** {e(estables)} reglas marcadas reaparecen en al menos el 70 % de las submuestras con la misma dirección, incluida la de la clase 6 ({pc(SOL_EST['reaparece_marcada'], 0)}).
- **Advertencia:** la estabilidad no distingue señal de ruido. Las reglas compatibles con el azar también son estables a menudo, porque las submuestras comparten el 80 % de los datos.

**12. ¿Cuáles también aparecen bajo la referencia nula?**
- **Todas menos una.** Las {e(c4)} marcadas no redundantes, las redundantes y las débiles tienen una fuerza que el azar alcanza al buscar entre {e(META['reglas'])} reglas.

**13. ¿Cómo afectan los datos imputados?**
- **Sin imputados (S1):** ninguna regla cambia de dirección, pero muchas pierden casos ({e(lec.loc['S1', 'desaparece por falta de casos'])} quedan bajo el umbral). Entre ellas está la de la clase 6, que baja a 52 participantes.
- **Lectura:** las imputaciones no fabrican las reglas, pero ayudan a que algunas superen el umbral.
- **Señal global:** se mantiene sin imputados, con {e(ex['S1'][3])} marcadas frente a {e(round(ex['S1'][4]))} esperadas.

**14. ¿Qué pasa al cambiar agrupaciones y umbrales?**
- **Categorías originales:** dan casi lo mismo.
- **Agrupación gruesa (S2b):** dos reglas superan su nula solo ahí, una de ellas redundante (informe 12). No son evidencia confirmatoria.
- **Umbrales:** con un umbral más bajo hay muchas más reglas y ninguna supera la nula; con uno más alto, menos reglas y tampoco ninguna.
- **Conclusión:** no cambia.

**15. ¿Qué restricciones presentan los módulos laboral y de cuidado?**
- **Poblaciones parciales:** solo aplican a quienes trabajan (287 con información laboral; 309 ampliada) y a quienes cuidan (239 con sobrecarga observada; 251 ampliada), así que se analizaron por separado, con su propia basal y sus umbrales proporcionales.
- **Circularidad:** las preguntas laborales mencionan los síntomas, y la sobrecarga puede ser consecuencia de ellos.
- **Resultados:** en quienes trabajan no hay reglas que superen la nula. En quienes cuidan hay una, la misma en S7b y S7b-251, con 34 participantes y la sobrecarga como condición; es exploratoria.

**16. ¿Existen reglas suficientemente sólidas para destacar, o la evidencia es débil?**
- **La evidencia es débil.** Hay una señal global, pero ninguna regla es robusta. La única que cumple los criterios es frágil ante las sensibilidades.

**17. ¿Qué limitaciones impiden considerarlas clínicas o causales?**
- **Datos:**
  - Son sintéticos.
  - Las asociaciones son marginales, sin ajuste por otras variables.
  - No se sabe la dirección: los síntomas podrían influir en los hábitos.
  - Hay imputaciones en muchas participantes.
  - No hay validación externa.
- **Diseño:**
  - No es un análisis ciego, porque las Fases 35 y 37D ya examinaron estas asociaciones.
  - Las mismas 529 sirven para descubrir y evaluar, sin muestra de confirmación.
- **Variables:** algunas están próximas a los síntomas.
- **Estabilidad:** no implica validez.

**18. ¿Qué se exploró en la Fase 39R?**
- **Diferencias entre estratos:** se compararon trabajo, pareja, ejercicio (0, 1-2 y 3 o más días) y cuidado, con un protocolo sellado, referencia nula dentro de cada estrato y denominadores visibles. Sus resultados están en los documentos de la Fase 39R.

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
  - Sello y barreras de exclusión.
  - Clasificación.

**20. ¿Se preservaron todos los archivos históricos?**
- **Sí.** En el control final de la 38R, {e(FIN['archivos_con_huella'])} archivos con huella no cambiaron ({len(FIN['huellas_cambiadas'])} cambiados) y los manifiestos de {e(FIN['manifiestos_archivos'])} archivos solo muestran {FIN['manifiestos_distintos']} diferencias ya documentadas antes de la corrección.
- **Simulador:** sus archivos no se abrieron.
- **Git:** rama {FIN['rama']}, HEAD {FIN['head'][:7]}, sin commit ni push.
""")

# ---------- Salida
docs['16_informe_cierre_38R'] = docs.pop('16_informe_cierre_38')
prot = (B / 'protocolo' / '01_protocolo_38R.md').read_text(encoding='utf-8')
NOTA_PROT = ('> **Nota de versión (fuera del texto sellado).** Este documento reproduce sin cambios `protocolo/01_protocolo_38R.md`. Esta nota se añade solo en esta edición y no forma parte del texto sellado. '
             f"Huella SHA-256 del protocolo: `{sello['sha256']}`; sellado el {sello['sellado']}. "
             'Dentro del protocolo, «Fase 38» sin la letra R se refiere a la versión histórica que se corrige.\n\n')
(F / '01_protocolo_38R.md').write_text(NOTA_PROT + prot.rstrip() + '\n', encoding='utf-8', newline='\n')
titulos = {'01_protocolo_38R': 'Protocolo de la Fase 38R'}


def vigente(t):
    return re.sub(r'Fase 39(?!R)', 'Fase 39R', re.sub(r'Fase 38(?!R| histórica)', 'Fase 38R', t))


def corregida(t):
    """La nota de versión nombra la fase corregida a propósito: se añade después de actualizar las demás menciones."""
    t = vigente(t.strip())
    m = re.match(r'<!-- apaisada -->\s*', t)
    return ('<!-- apaisada -->\n\n' if m else '') + VERSION + '\n\n' + t[m.end() if m else 0:] + '\n'


JS = AQUI / 'md_a_word_definitivo.js'
for nombre, (titulo, md) in docs.items():
    (F / f'{nombre}.md').write_text(corregida(md), encoding='utf-8', newline='\n')
    titulos[nombre] = vigente(titulo)
FILTRO = set(sys.argv[1:])
ENTORNO = entorno_node()
for nombre, titulo in titulos.items():
    if FILTRO and nombre[:2] not in FILTRO:
        continue
    r = subprocess.run(['node', str(JS), str(F / f'{nombre}.md'), str(INF / f'{nombre}.docx'), titulo + ' (versión correctiva)', 'AgingWomen · Fase 38R: reglas de asociación generales'], capture_output=True, text=True, encoding='utf-8', env=ENTORNO)
    if r.returncode:
        raise SystemExit(f'{nombre}: {r.stderr[:800]}')
print(len(titulos), 'documentos Word')
