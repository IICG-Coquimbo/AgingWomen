"""
Informe académico en Word de Random Forest con 33 variables, Fase 35B.

Solo lee resultados ya calculados en esta carpeta y los de Shannon: no entrena modelos ni modifica nada anterior.
Requiere python-docx (fuera de las dependencias del proyecto). Uso, desde analisis/:
    python -m random_forest_revision_35b_33_variables.informe_word_rf_33
"""
import numpy as np
import pandas as pd
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml
from docx.shared import Cm, Pt, RGBColor
from scipy import stats

import informe_word_35b as W
import seleccionar_fase35b as P
from informe_word_35b import AZUL_OSCURO, M_NS, Informe, m_frac, m_r, m_raiz, m_sub, nombre, p1, p3, p4, p5, r3, si

from . import rf_33_variables as RV

RESULTADOS = RV.CARPETA / 'resultados'
FIGURAS = RV.CARPETA / 'figuras'
SALIDA = RV.CARPETA / 'informe' / 'informe_random_forest_33_variables.docx'
ETIQ_POB = {RV.TODAS: 'General', RV.TRABAJADORAS: 'Laboral', RV.CUIDADORAS: 'Cuidadoras'}
SEIS = RV.SEIS_SHANNON
SOB = RV.SOBRECARGA


def leer(nombre_csv):
    return pd.read_csv(RESULTADOS / f'{nombre_csv}.csv', encoding='utf-8-sig', keep_default_na=False, na_values=[''])


def cargar():
    return {n: leer(n) for n in ('modelos', 'rendimiento_modelos', 'comparacion_modelos', 'matrices_confusion', 'importancia_variables', 'importancia_grupos', 'pruebas_azar', 'shannon_vs_rf',
                                 'sensibilidad_imc_importancia', 'revision_imputaciones_34B', 'imc_faltante_y_severidad')}


def f4(x):
    return f'{x:+.4f}'.replace('.', ',').replace('-', '−')


def filas_cmp(t):
    return t.set_index(['modelo', 'referencia', 'metrica'])


def comprobar(T):
    """El texto interpretativo solo es válido si los archivos dicen lo mismo; si no, no se genera el informe."""
    c = filas_cmp(T['comparacion_modelos'])
    lee = lambda a, b, m: c.loc[(a, b, m), 'lectura']
    esperado = {('B', 'A', 'roc_auc'): 'Mejora respaldada', ('B', 'A', 'balanced_accuracy'): 'Sin diferencia clara', ('C1', 'C0', 'roc_auc'): 'Sin diferencia clara', ('C1', 'C0', 'balanced_accuracy'): 'Sin diferencia clara',
                ('D1', 'D0', 'roc_auc'): 'Sin diferencia clara', ('D1', 'D0', 'balanced_accuracy'): 'Sin diferencia clara', ('B', 'B_sin_imc', 'roc_auc'): 'Mejora respaldada', ('B', 'B_shannon', 'balanced_accuracy'): 'Mejora respaldada',
                ('B', 'B_shannon', 'roc_auc'): 'Sin diferencia clara', ('B_resto', 'Ref_general', 'roc_auc'): 'Mejora respaldada', ('B_sin_imc', 'A_sin_imc', 'roc_auc'): 'Sin diferencia clara', ('B_sin_imc', 'A_sin_imc', 'balanced_accuracy'): 'Mejora respaldada',
                ('C1_sin_imc', 'C0_sin_imc', 'roc_auc'): 'Sin diferencia clara', ('D1_sin_imc', 'D0_sin_imc', 'roc_auc'): 'Sin diferencia clara'}
    for clave, valor in esperado.items():
        if lee(*clave) != valor:
            raise RuntimeError(f'{clave}: el texto dice {valor}.')
    for r in ('B_sin_dias', 'B_sin_fuerza', 'B_sin_bajo_impacto', 'B_sin_dias_bajo_impacto', 'B_sin_actividad'):
        if lee('B', r, 'roc_auc') != 'Sin diferencia clara':
            raise RuntimeError(r)
    if (T['comparacion_modelos'].query("tipo == 'imputación en partición'")['lectura'] != 'Sin diferencia clara').any():
        raise RuntimeError('La sensibilidad de imputación cambió una lectura.')
    az = T['pruebas_azar'].set_index(['modelo', 'metrica'])
    if az.loc[('A', 'roc_auc'), 'p'] < 0.05 or any(az.loc[(m, medida), 'k_mayores_o_iguales'] != 0 for m in ('B', 'C0', 'C1', 'D0', 'D1') for medida in ('roc_auc', 'balanced_accuracy')):
        raise RuntimeError('Las pruebas contra el azar no coinciden con el texto.')
    s = T['shannon_vs_rf'].set_index('variable')
    grupos = {'Coinciden ambos métodos': {'imc', 'trabaja_actualmente', 'dias_ejercicio_semana', 'frecuencia_bajo_impacto', 'lugar_trabajo_comprensivo'}, 'Solo Shannon': {'frecuencia_fuerza'},
              'Solo Random Forest': {'tabaco_frecuencia', 'vasos_agua_dia', 'distension_abdominal', 'falta_tiempo_influye', 'estres_entorno_laboral', SOB}}
    for clase, variables in grupos.items():
        if set(s.index[s['consistencia'] == clase]) != variables:
            raise RuntimeError(f'La clase «{clase}» no coincide con el texto.')
    if len(s) != 33:
        raise RuntimeError('La tabla de Shannon no tiene 33 filas.')
    i = T['importancia_variables'].set_index(['modelo', 'nombre'])
    for clave, valor in {('B', 'imc'): 1, ('C1', 'lugar_trabajo_comprensivo'): 1, ('D1', 'dias_ejercicio_semana'): 1}.items():
        if i.loc[clave, 'orden_en_modelo'] != valor:
            raise RuntimeError(f'{clave} no ocupa el lugar que dice el texto.')
    for m in ('B', 'C1', 'D1'):
        if i.loc[(m, 'tabaco_frecuencia'), 'aporte'] != 'Aporte consistente' or i.loc[(m, 'distension_abdominal'), 'aporte'] != 'Aporte consistente':
            raise RuntimeError('Tabaco o distensión cambiaron de clase.')
    if (i.loc[('B', 'alcohol_frecuencia'), 'aporte'], i.loc[('C1', 'alcohol_frecuencia'), 'aporte'], i.loc[('D1', 'alcohol_frecuencia'), 'aporte']) != ('Aporte inestable', 'Aporte consistente', 'Nulo o negativo'):
        raise RuntimeError('Alcohol cambió de clase.')
    if (T['revision_imputaciones_34B']['particiones_con_otro_valor'] > 0).sum() != 5 or len(T['revision_imputaciones_34B']) != 28:
        raise RuntimeError('La revisión de imputaciones no coincide con el texto.')


def construir(T):
    D = Informe()
    D.d.sections[0].header.paragraphs[0].runs[0].text = 'AgingWomen · Fase 35B · Random Forest con 33 variables'
    D.d.core_properties.title = 'Fase 35B: Random Forest con 33 variables'
    R = T['rendimiento_modelos'].set_index('modelo')
    C = filas_cmp(T['comparacion_modelos'])
    I = T['importancia_variables'].set_index(['modelo', 'nombre'])
    G = T['importancia_grupos'].set_index(['modelo', 'nombre'])
    Z = T['pruebas_azar'].set_index(['modelo', 'metrica'])
    S = T['shannon_vs_rf'].set_index('variable')
    Mod = T['modelos'].set_index('modelo')
    imc = T['imc_faltante_y_severidad'].iloc[0]
    PRIN = list(RV.PRINCIPALES)
    gen = T['shannon_vs_rf'][T['shannon_vs_rf']['modelo_rf'] == 'B']
    rho_su = stats.spearmanr(gen['su'], gen['auc_media']).statistic
    piso = T['importancia_variables'].query("modelo == 'B'")['auc_media'].min()

    auc = lambda m: p3(R.loc[m, 'roc_auc_evaluacion'])
    ba = lambda m: p3(R.loc[m, 'balanced_accuracy_evaluacion'])
    d3 = lambda a, b, m='roc_auc': r3(C.loc[(a, b, m), 'diferencia'])
    ic = lambda a, b, m='roc_auc': f'{r3(C.loc[(a, b, m), "ic95_inferior"])} a {r3(C.loc[(a, b, m), "ic95_superior"])}'
    pos = lambda a, b, m='roc_auc': int(C.loc[(a, b, m), 'particiones_positivas'])
    ia = lambda m, v: p4(I.loc[(m, v), 'auc_media'])
    ip = lambda m, v: int(I.loc[(m, v), 'auc_positivas'])
    ib = lambda m, v: f4(I.loc[(m, v), 'ba_media'])
    ibp = lambda m, v: int(I.loc[(m, v), 'ba_positivas'])
    cl = lambda m, v: I.loc[(m, v), 'aporte'].lower()

    def tabla_importancia(modelo):
        t = T['importancia_variables'].query('modelo == @modelo')
        return D.tabla(f'Importancia por permutación en el modelo {modelo}, de mayor a menor pérdida de ROC-AUC, en datos de evaluación. En azul, las variables con q < 0,10 en Shannon.',
                       ['N.º', 'Variable', 'AUC: promedio', 'AUC: DE', 'AUC: positivas de 15', 'Exactitud bal.: promedio', 'Exactitud bal.: positivas', 'Clase'],
                       [[str(int(f['orden_en_modelo'])), nombre(f['nombre']), f4(f['auc_media']), p4(f['auc_de']), str(int(f['auc_positivas'])), f4(f['ba_media']), str(int(f['ba_positivas'])), f['aporte']] for _, f in t.iterrows()],
                       [0.8, 4.7, 1.6, 1.1, 1.4, 1.7, 1.4, 3.2], ['d', 'i', 'd', 'd', 'd', 'd', 'd', 'i'], tam=8, resaltar=[v in SEIS for v in t['nombre']])

    # ---- Portada ----
    def centrado(texto, tam, negrita=False, antes=0, despues=6, color='000000'):
        q = D.d.add_paragraph()
        q.alignment = WD_ALIGN_PARAGRAPH.CENTER
        q.paragraph_format.space_before, q.paragraph_format.space_after = Pt(antes), Pt(despues)
        r = q.add_run(texto)
        r.font.size, r.bold, r.font.color.rgb = Pt(tam), negrita, RGBColor.from_string(color)
    centrado('Universidad Católica del Norte', 15, True, 40, 4, AZUL_OSCURO)
    centrado('Proyecto AgingWomen', 13, False, 0, 90, '404040')
    centrado('Fase 35B', 15, True, 0, 8, AZUL_OSCURO)
    centrado('Capacidad predictiva conjunta de 33 variables sobre la severidad de los síntomas menopáusicos', 21, True, 0, 18, AZUL_OSCURO)
    q = D.d.add_paragraph()
    q.paragraph_format.space_after = Pt(18)
    q._p.get_or_add_pPr().append(parse_xml(f'<w:pBdr {M_NS}><w:bottom w:val="single" w:sz="10" w:space="1" w:color="{AZUL_OSCURO}"/></w:pBdr>'))
    centrado('Informe académico: análisis complementario con Random Forest', 14, False, 0, 6)
    centrado('Validación cruzada repetida, importancia por permutación y comparación con la entropía de Shannon', 12, False, 0, 110, '404040')
    centrado('Complementa el informe de Shannon de 33 variables; no lo reemplaza', 11.5, False, 0, 6)
    centrado('Conjunto de datos sintético: los resultados son exploratorios y no causales', 11.5, False, 0, 6)
    centrado('Noviembre de 2026', 11.5, False, 26, 0)
    D.salto()
    D.indice()
    D.salto()

    # ---- Resumen ----
    D.h0('Resumen')
    D.p('Este informe evalúa, con Random Forest, la capacidad de 33 variables para predecir en conjunto la severidad de los síntomas menopáusicos (`severo_mrs`: MRS total ≥ 16) en un conjunto de datos **sintético** de 529 participantes. Es un análisis **complementario** de la entropía de Shannon: no la reemplaza y no elimina variables de la Fase 36.')
    D.p(f'**La capacidad predictiva es modesta, aunque supera al azar.** El modelo general con 30 variables (B) alcanza un ROC-AUC de {auc("B")} y una exactitud balanceada de {ba("B")}. En trabajadoras (C1) el ROC-AUC es {auc("C1")} y en cuidadoras (D1), {auc("D1")}. Hay **sobreajuste marcado**: en entrenamiento el ROC-AUC supera 0,96 en estos modelos. El modelo de referencia A ({auc("A")}) no se distingue del azar.')
    D.p(f'**Agregar hábitos y salud mejora la predicción medida con ROC-AUC:** B supera a A en {d3("B", "A")} (IC 95 %: {ic("B", "A")}), aunque con exactitud balanceada el intervalo apenas incluye 0. **No se respalda con claridad** que las variables laborales mejoren el modelo entre trabajadoras ({d3("C1", "C0")}; IC 95 %: {ic("C1", "C0")}), ni que la sobrecarga lo haga entre cuidadoras ({d3("D1", "D0")}; IC 95 %: {ic("D1", "D0")}).')
    D.p(f'**Random Forest y Shannon coinciden en gran medida:** cinco de las seis variables con q < 0,10 también muestran un aporte consistente (IMC, trabajar actualmente, días de ejercicio, bajo impacto y lugar de trabajo comprensivo). La excepción es el ejercicio de fuerza, cuyo aporte es inestable en el modelo general. Seis variables aportan en Random Forest sin superar q < 0,10: tabaco, agua, distensión abdominal, falta de tiempo, estrés laboral y sobrecarga. El bloque de actividad física es el más importante como grupo.')
    D.p('Estas importancias no demuestran causalidad, describen un conjunto en el que algunas relaciones fueron programadas y no equivalen a validez clínica. **Las 33 variables se conservan como conjunto inicial de la Fase 36.**')

    # ---- 1 ----
    D.h1('Introducción')
    D.p('La Fase 35B analizó con entropía de Shannon, variable por variable, qué características se asocian con la severidad de los síntomas. Ese análisis, con 10.000 y 50.000 permutaciones, identificó seis variables con q < 0,10. Sin embargo, una asociación individual no indica si una variable ayuda a predecir cuando se la considera junto con las demás.')
    D.p('Random Forest aborda esa pregunta distinta: entrena un modelo con muchas variables a la vez y mide su rendimiento en participantes que no usó para aprender. También permite detectar combinaciones y relaciones no lineales que una medida individual podría no captar.')
    D.p('Este informe usa la **revisión corregida de 33 variables** y no repite ni modifica Shannon ni FCBF. Los resultados de Shannon se leen de sus archivos y se usan solo para comparar.')

    # ---- 2 ----
    D.h1('Objetivos')
    D.h2('Objetivo general')
    D.p('Evaluar la capacidad predictiva conjunta de las 33 variables respecto de la severidad de los síntomas menopáusicos, y compararla con las asociaciones identificadas mediante entropía de Shannon.')
    D.h2('Preguntas')
    D.lista(['¿Qué características ayudan más a predecir la severidad?', '¿Las seis variables destacadas por Shannon también aportan información predictiva?', '¿Existen variables que no superaron q < 0,10, pero que mejoran las predicciones?', '¿Agregar hábitos y características de salud mejora la predicción?', '¿Las variables laborales aportan información adicional entre trabajadoras?', '¿La sobrecarga física y emocional aporta información adicional entre cuidadoras?', '¿Los resultados son estables o muestran sobreajuste?'], numerada=True)
    D.h2('Alcance')
    D.p('**Random Forest no reemplaza a Shannon y no se usa para eliminar variables de la Fase 36.** Tampoco se buscaron los mejores hiperparámetros ni se eligieron semillas según el rendimiento. El protocolo se registró antes de entrenar; el análisis no es independiente de Shannon, porque esos resultados ya se conocían.')

    # ---- 3 ----
    D.h1('Conjunto de datos y variables')
    D.h2('Entrada')
    D.p('Se usó `datos/analitico/dataset_fase35_33_variables.csv`, con 529 participantes: 281 con síntomas severos (53,1 %) y 248 sin ellos. Se comprobó que `severo_mrs` vale 1 exactamente cuando el MRS total es 16 o más, y que este archivo solo difiere de `dataset_fase35.csv` en la columna excluida. No se usó `dataset_fase35b.csv`, que es una versión histórica, ni la versión verdadera del simulador.')
    D.h2('Poblaciones')
    nt = D.tabla('Poblaciones de análisis.', ['Población', 'n', 'Severas', 'Definición'],
                 [['General', '529', '281 (53,1 %)', 'Todas las participantes con MRS completo'], ['Laboral', '287', '166 (57,8 %)', 'Trabajadoras con datos laborales en la revisión entrópica; no son todas las que trabajan (309)'], ['Cuidadoras', '239', '136 (56,9 %)', 'Cuidadoras con sobrecarga observada']],
                 [2.4, 1.0, 2.4, 10.7], ['i', 'd', 'd', 'i'], mantener=True)
    D.explicar(nt, 'El tamaño de cada población y su proporción de síntomas severos.', 'Las poblaciones tienen tamaños y proporciones distintos. **Por eso no se comparan directamente valores entre modelos de distintas poblaciones.**')
    D.p('**«No aplica» no se convierte en cero ni se imputa.** Las variables laborales solo entran con las 287 trabajadoras y la sobrecarga solo con las 239 cuidadoras.')
    D.h2('Variables y exclusiones')
    D.p('Se usaron las 33 variables elegibles. Quedan fuera:')
    D.lista(['`usa_medicamentos_diabetes`: dominancia de 87,52 %, sobre el umbral de 85 %.', '`doble_carga`: por indicación de la profesora.', '`prevision`: excluida del modelado.', 'Preguntas del MRS, `mrs_total`, `severidad_mrs_4` y `severo_mrs`, que son la severidad misma.', 'Identificadores, `etapa_menopausica`, variables menstruales e indicadores de imputación.'])
    D.p('El programa se detiene si una variable prohibida entra en un modelo. Además, se comprobó sin entrenar que ningún predictor tiene una correlación de Spearman de 0,5 o más con el MRS total.')
    D.h2('Modelos')
    nt = D.tabla('Modelos principales. El listado exacto de variables está en el Anexo C.', ['Modelo', 'Población', 'n', 'Variables', 'Contenido'],
                 [[m, ETIQ_POB[Mod.loc[m, 'poblacion']], str(int(R.loc[m, 'n'])), str(int(Mod.loc[m, 'n_variables'])), x] for m, x in (('A', 'Referencia general: edad, IMC y trabajar actualmente'), ('B', 'Las 30 variables generales'), ('C0', 'Generales sin trabajar actualmente, que es constante en esta población'), ('C1', 'C0, lugar de trabajo comprensivo y estrés laboral'), ('D0', 'Las 30 variables generales, sin sobrecarga'), ('D1', 'D0 y sobrecarga física y emocional'))],
                 [1.3, 2.2, 1.0, 1.5, 10.5], ['i', 'i', 'd', 'd', 'i'], mantener=True)
    D.explicar(nt, 'Los seis modelos y las variables que los distinguen.', 'Cada comparación se hace entre modelos de la misma población: B con A, C1 con C0 y D1 con D0. D0 y D1 no incluyen variables laborales porque solo 130 de las 239 cuidadoras tienen esos datos, y usarlas obligaría a imputar «no aplica».')
    D.p('También se declararon modelos secundarios: sin IMC, sin indicadores de ejercicio, solo con las variables destacadas por Shannon, con reimputación en la partición y un clasificador sencillo de referencia.')

    # ---- 4 ----
    D.h1('Funcionamiento de Random Forest')
    D.p('Un **árbol de decisión** clasifica a una persona mediante preguntas sucesivas, por ejemplo: «¿IMC mayor que 30?», «¿hace ejercicio dos días o más?». Un solo árbol suele aprender demasiado los casos con los que se entrena.')
    D.p('**Random Forest** entrena muchos árboles distintos y promedia sus respuestas (Breiman, 2001). Los árboles se diferencian por dos fuentes de azar: cada uno aprende de una muestra aleatoria de participantes y, en cada pregunta, solo puede elegir entre un subconjunto aleatorio de variables. El promedio suele predecir mejor que un árbol aislado.')
    D.h2('Parámetros usados')
    D.tabla('Configuración del modelo, fijada antes de entrenar.', ['Parámetro', 'Valor', 'Qué significa'],
            [['n_estimators', '500', 'Número de árboles'], ['min_samples_leaf', '5', 'Cada grupo final de un árbol tiene al menos 5 personas, lo que limita la memorización'], ['max_features', 'sqrt', 'En cada pregunta se elige entre la raíz cuadrada del número de variables'], ['class_weight', 'balanced', 'Da el mismo peso total a severas y no severas'], ['random_state', '42', 'Semilla fija, no elegida según resultados']],
            [3.6, 1.8, 11.1], tam=9, mantener=True)
    D.h2('Cómo se mide el rendimiento')
    D.lista(['**ROC-AUC.** Probabilidad de que el modelo asigne un puntaje mayor a una persona severa que a una no severa, elegidas al azar. 0,5 equivale al azar y 1 a una separación perfecta. No depende de un punto de corte.', '**Exactitud balanceada.** Promedio de la sensibilidad en ambas clases. 0,5 equivale a no discriminar.', '**Sensibilidad.** De quienes realmente pertenecen a una clase, proporción que el modelo identifica.', '**Precisión.** De quienes el modelo asigna a una clase, proporción que realmente pertenece a ella.', '**F1.** Combina precisión y sensibilidad de una clase.'])
    D.h2('Importancia por permutación')
    D.p('Con un modelo ya entrenado, se baraja una variable en los datos de evaluación y se observa cuánto empeora el rendimiento. Si empeora mucho, el modelo dependía de esa variable. Si no cambia, o mejora levemente, no la usaba de forma útil. **Una importancia alta no indica causa ni dirección:** Random Forest no dice si una variable aumenta o disminuye la severidad.')
    D.p('Cuando dos variables contienen información parecida, barajar una sola puede tener poco efecto, porque el modelo se apoya en la otra. Por eso también se barajan **grupos** de variables relacionadas. Por su parte, volver a entrenar sin una variable responde otra pregunta: si el modelo puede **reemplazarla** con el resto.')

    # ---- 5 ----
    D.h1('Preprocesamiento')
    D.p('Todo lo que aprende parámetros de los datos se ajusta **solo con las participantes de entrenamiento de cada partición**. Las participantes de evaluación no influyen en esos valores; una prueba automática lo verifica.')
    D.lista(['**Imputación:** mediana de entrenamiento para los faltantes reconstruidos en memoria.', '**Nominal:** `quien_prepara_comidas` usa codificación one-hot, ajustada en entrenamiento.', '**Ordinales:** conservan sus valores y orden. Los árboles no requieren escalado.', '**Sin indicadores de imputación** entre los predictores.'])
    D.h2('Tratamiento del IMC')
    D.p(f'En la Fase 35A, 262 de los 529 IMC (49,5 %) fueron imputados con la media global. Aquí se usa `imc_fue_imputado` solo para volver a dejar esos valores vacíos en memoria e imputarlos con la mediana de entrenamiento en cada partición. **El indicador no es predictor y el conjunto de datos no se modifica.**')
    D.p(f'Faltar el IMC no se relaciona con la severidad: {p1(imc["pct_severas_faltante"])} % de severas entre quienes no lo informaron y {p1(imc["pct_severas_observado"])} % entre quienes sí (ji cuadrado, p = {p3(imc["p_ji_cuadrado"])}). Por lo tanto, el valor imputado no funciona como una señal encubierta de severidad.')
    D.p('Las variables laborales siguen el mismo tratamiento: 16 valores de `lugar_trabajo_comprensivo` y 10 de `estres_entorno_laboral` se imputan dentro de cada partición.')
    D.h2('Revisión de las demás imputaciones')
    imp = T['revision_imputaciones_34B']
    afect = imp[imp['particiones_con_otro_valor'] > 0].sort_values('particiones_con_otro_valor', ascending=False)
    D.p(f'La limpieza de la Fase 34B imputó otros faltantes con la mediana o la moda del conjunto completo, antes de particionar. **Esa imputación no usa la severidad**, de modo que no filtra el objetivo, aunque sí usa información general de personas que después quedan en evaluación. Se comparó ese valor con el que resultaría usando solo entrenamiento, en las 45 particiones de las tres poblaciones. En {int((imp["particiones_con_otro_valor"] == 0).sum())} de {len(imp)} variables, el valor es idéntico en todas.')
    nt = D.tabla('Variables cuyo valor imputado en la Fase 34B difiere del de entrenamiento en alguna partición.', ['Variable', 'Celdas imputadas', 'Identificadas', 'Valor global', 'Particiones con otro valor (de 45)'],
                 [[nombre(f['variable']), str(int(f['imputadas_34B'])), str(int(f['identificadas'])), str(f['valor_global']), str(int(f['particiones_con_otro_valor']))] for _, f in afect.iterrows()],
                 [6.5, 2.2, 2.2, 2, 3.6], ['i', 'd', 'd', 'd', 'd'], mantener=True)
    bi, c1i, d1i = (C.loc[(m, f'{m}_imp_particion', 'roc_auc')] for m in ('B', 'C1', 'D1'))
    D.explicar(nt, 'Las cinco variables en las que el valor global no coincide siempre con el de entrenamiento. La mayoría de las diferencias ocurre en las subpoblaciones. «Identificadas» es menor cuando las celdas se reconocen por estar vacías en el conjunto sucio, lo que omite respuestas inválidas.', 'Para estas cinco se agregó una sensibilidad que las reimputa dentro de cada partición (sección 7.7). Los modelos principales conservan los valores originales.')

    # ---- 6 ----
    D.h1('Entrenamiento y validación')
    D.p('Se usó **validación cruzada estratificada repetida**: las participantes se dividen en 5 partes con proporción similar de severas; se entrena con 4 y se evalúa con la restante, rotando. Esto se repite 3 veces con distinta división, lo que da **15 evaluaciones por modelo**. Cada persona se evalúa una vez por repetición.')
    D.p('Las particiones dependen solo del objetivo, de modo que los modelos de una misma población usan **exactamente las mismas particiones**. Eso permite calcular las diferencias de forma emparejada.')
    D.h2('Comparación entre modelos')
    D.p('Las 15 evaluaciones comparten datos y no son independientes. Por eso, el intervalo de 95 % de cada diferencia usa la **corrección de Nadeau y Bengio** (2003), más amplia que un intervalo ingenuo:')
    D.ecuacion(f'<m:bar><m:barPr><m:pos m:val="top"/></m:barPr><m:e>{m_r("d")}</m:e></m:bar>' + m_r(' ± ') + m_sub(m_r('t'), m_r('14; 0,975')) + m_raiz(m_r('(') + m_frac(m_r('1'), m_r('15')) + m_r(' + 0,25) ') + f'<m:sSubSup><m:e>{m_r("s")}</m:e><m:sub>{m_r("d")}</m:sub><m:sup>{m_r("2")}</m:sup></m:sSubSup>'))
    D.p('Aquí, d̄ es el promedio de las 15 diferencias, s² con subíndice d es su varianza y t es el valor crítico de la distribución t con 14 grados de libertad. El término 0,25 corresponde a la razón entre las personas de evaluación y las de entrenamiento (1/4).')
    D.p('Antes de ver resultados se fijó esta lectura: **mejora respaldada** si el límite inferior es mayor que 0; **empeora** si el superior es menor que 0; **sin diferencia clara** si el intervalo incluye 0. Es aproximada y se usa de forma descriptiva.')
    D.h2('Prueba contra el azar')
    D.p('Para los seis modelos principales se barajaron las etiquetas de severidad 200 veces y se repitió **todo** el procedimiento: particiones, imputación, codificación, entrenamiento y evaluación (Ojala y Garriga, 2010). Son 18.000 bosques; se calcularon completos, sin reducir el número de permutaciones. p = (1 + k) / 201, con un mínimo posible de 0,005. No se corrige por los seis modelos.')
    D.h2('Clasificación de la importancia')
    D.tabla('Clases de importancia, fijadas antes de ver resultados, según la pérdida de ROC-AUC en 15 particiones.', ['Clase', 'Regla'],
            [['Aporte consistente', 'Promedio ≥ 0,005 y positiva en al menos 12 de 15'], ['Aporte pequeño', 'Promedio > 0 y < 0,005, positiva en al menos 12 de 15'], ['Aporte inestable', 'Promedio > 0, positiva en menos de 12 de 15'], ['Nulo o negativo', 'Promedio ≤ 0']],
            [4.5, 12.0], mantener=True)
    D.p('Estos cortes son una **convención descriptiva, no una prueba estadística**, y no se corrigen por comparaciones múltiples. «Consistente» no significa grande.')
    D.h2('Reproducibilidad y control de memoria')
    D.p('Se usaron 4 procesos en un equipo de 7,7 GB. Dos corridas de control coincidieron, y una permutación repetida coincidió con la guardada. Los archivos anteriores (resultados de Shannon, conjuntos de datos e informes) no cambiaron, según sus huellas antes y después.')

    # ---- 7 ----
    D.h1('Resultados de los modelos')
    D.h2('Rendimiento en evaluación')
    filas_prin = [*PRIN, 'Ref_general', 'Ref_laboral', 'Ref_cuidadoras']
    nt = D.tabla('Rendimiento en evaluación: promedio y desviación estándar en 15 particiones.', ['Modelo', 'Población', 'n', 'Variables', 'ROC-AUC', 'DE', 'Mín.', 'Máx.', 'Exactitud bal.', 'DE'],
                 [[m.replace('Ref_general', 'Sencillo (general)').replace('Ref_laboral', 'Sencillo (laboral)').replace('Ref_cuidadoras', 'Sencillo (cuidadoras)'), ETIQ_POB[R.loc[m, 'poblacion']], str(int(R.loc[m, 'n'])), '—' if m.startswith('Ref') else str(int(R.loc[m, 'n_variables'])), p3(R.loc[m, 'roc_auc_evaluacion']), p3(R.loc[m, 'roc_auc_de']), p3(R.loc[m, 'roc_auc_minimo']), p3(R.loc[m, 'roc_auc_maximo']), p3(R.loc[m, 'balanced_accuracy_evaluacion']), p3(R.loc[m, 'balanced_accuracy_de'])] for m in filas_prin],
                 [3.1, 1.9, 0.9, 1.6, 1.4, 1.1, 1.1, 1.1, 1.6, 1.1], ['i', 'i', 'd', 'd', 'd', 'd', 'd', 'd', 'd', 'd'], tam=8.5, mantener=True)
    D.explicar(nt, 'Cuánto discrimina cada modelo en participantes que no usó para aprender. El clasificador sencillo (`DummyClassifier`) no usa información: predice siempre la clase más frecuente.', f'Los modelos con muchas variables superan al clasificador sencillo, pero su capacidad es **modesta**: el ROC-AUC va de {auc("B")} a {auc("C1")}. El modelo A ({auc("A")}) queda muy cerca del azar. La variación entre particiones es considerable, especialmente entre cuidadoras (DE {p3(R.loc["D1", "roc_auc_de"])}), donde hay menos personas.')
    nf = D.figura(FIGURAS / 'rendimiento_modelos.png', 'ROC-AUC y exactitud balanceada en evaluación de los seis modelos principales, con ± 1 desviación estándar.', 16)
    D.explicar(nf, 'Cada punto es el promedio de 15 evaluaciones y la línea su variación. La línea discontinua marca el clasificador sencillo.', 'A es el único modelo cuya variación incluye claramente 0,5. Los valores de distintas poblaciones no deben compararse entre sí como si fueran equivalentes.')
    D.h2('Rendimiento por clase y matrices de confusión')
    nt = D.tabla('Rendimiento por clase en evaluación.', ['Modelo', 'F1 severos', 'Precisión severos', 'Sensibilidad severos', 'F1 no severos', 'Precisión no severos', 'Sensibilidad no severos'],
                 [[m.replace('Ref_general', 'Sencillo (general)').replace('Ref_laboral', 'Sencillo (laboral)').replace('Ref_cuidadoras', 'Sencillo (cuidadoras)'), *[p3(R.loc[m, f'{x}_evaluacion']) for x in ('f1_severos', 'precision_severos', 'sensibilidad_severos', 'f1_no_severos', 'precision_no_severos', 'sensibilidad_no_severos')]] for m in filas_prin],
                 [3.5, 2.0, 2.2, 2.3, 2.0, 2.2, 2.3], ['i', 'd', 'd', 'd', 'd', 'd', 'd'], tam=8.5, mantener=True)
    D.explicar(nt, 'Precisión, sensibilidad y F1 de cada clase. Severos son quienes tienen MRS ≥ 16.', f'**El clasificador sencillo obtiene un F1 de severos mayor que todos los modelos** ({p3(R.loc["Ref_general", "f1_severos_evaluacion"])} frente a {p3(R.loc["B", "f1_severos_evaluacion"])} en B, en la población general). Esto no indica que sea mejor: identifica a todas las severas porque clasifica a todas como severas, y su F1 de no severos es 0. Por eso, F1 de una sola clase no sirve para compararlos. Los modelos identifican mejor a las severas que a las no severas: en C1, la sensibilidad es {p3(R.loc["C1", "sensibilidad_severos_evaluacion"])} para severas y {p3(R.loc["C1", "sensibilidad_no_severos_evaluacion"])} para no severas.')
    nf = D.figura(FIGURAS / 'matrices_confusion.png', 'Matrices de confusión, promedio de las tres repeticiones. Entre paréntesis, el porcentaje de cada clase real. El color usa la misma escala en los seis paneles.', 15.5)
    bm = T['matrices_confusion'].query("modelo == 'B'")[['vn', 'fp', 'fn', 'vp']].mean()
    D.explicar(nf, 'Cuántas personas de cada clase real se clasifican correctamente o no, en promedio.', f'Hay errores numerosos en ambas clases. En B, {p1(bm["fp"])} de 248 no severas se clasifican como severas y {p1(bm["fn"])} de 281 severas se clasifican como no severas. En A, los aciertos y errores son casi iguales.')
    D.h2('Entrenamiento frente a evaluación')
    nt = D.tabla('Rendimiento en entrenamiento y evaluación de los modelos principales.', ['Modelo', 'ROC-AUC entren.', 'ROC-AUC eval.', 'Diferencia', 'Exactitud bal. entren.', 'Exactitud bal. eval.', 'Diferencia'],
                 [[m, p3(R.loc[m, 'roc_auc_entrenamiento']), p3(R.loc[m, 'roc_auc_evaluacion']), p3(R.loc[m, 'roc_auc_diferencia_ent_eval']), p3(R.loc[m, 'balanced_accuracy_entrenamiento']), p3(R.loc[m, 'balanced_accuracy_evaluacion']), p3(R.loc[m, 'balanced_accuracy_diferencia_ent_eval'])] for m in PRIN],
                 [1.6, 2.5, 2.5, 2.2, 2.9, 2.6, 2.2], ['i', 'd', 'd', 'd', 'd', 'd', 'd'], mantener=True)
    D.explicar(nt, 'La diferencia entre lo que el modelo logra con las personas que conoció y con las que no conoció.', f'**Hay sobreajuste marcado.** B pasa de {p3(R.loc["B", "roc_auc_entrenamiento"])} en entrenamiento a {p3(R.loc["B", "roc_auc_evaluacion"])} en evaluación. Parte de esto es esperable en Random Forest, cuyos árboles se ajustan mucho a sus datos. Por eso, **solo los valores de evaluación indican capacidad predictiva**. No se ajustaron hiperparámetros para reducir esta diferencia, según lo acordado.')
    D.h2('Comparaciones principales')
    def filas_comparacion(pares):
        filas = []
        for a, b in pares:
            for me, et in (('roc_auc', 'ROC-AUC'), ('balanced_accuracy', 'Exactitud bal.')):
                f = C.loc[(a, b, me)]
                filas.append([f'{a} − {b}', et, p3(f['media_modelo']), p3(f['media_referencia']), r3(f['diferencia']), p3(f['de']), f'{int(f["particiones_positivas"])}/15', f'{r3(f["ic95_inferior"])} a {r3(f["ic95_superior"])}', f['lectura']])
        return filas
    enc_cmp = ['Comparación', 'Medida', 'Media modelo', 'Media ref.', 'Dif.', 'DE', 'A favor', 'IC 95 % corregido', 'Lectura']
    anch_cmp = [3.6, 1.9, 1.2, 1.1, 1.0, 0.9, 1.0, 2.7, 2.6]
    ali_cmp = ['i', 'i', 'd', 'd', 'd', 'd', 'd', 'd', 'i']
    nt = D.tabla('Comparaciones emparejadas principales, con las mismas personas y particiones.', enc_cmp, filas_comparacion(RV.COMPARACIONES['principal']), anch_cmp, ali_cmp, tam=8, mantener=True)
    D.explicar(nt, 'La mejora de cada modelo sobre su referencia, en las mismas 15 particiones.', f'**B − A:** la mejora de ROC-AUC está respaldada, mientras que con exactitud balanceada el intervalo apenas incluye 0 (límite inferior {f4(C.loc[("B", "A", "balanced_accuracy"), "ic95_inferior"])}). **C1 − C0:** la diferencia favorece a C1 en {pos("C1", "C0")} de 15 particiones, pero el intervalo incluye 0. **D1 − D0:** no hay diferencia clara, y con exactitud balanceada es prácticamente nula. Un intervalo que incluye 0 no demuestra ausencia de efecto: indica que, con estos datos y este método, no se puede afirmar una mejora.')
    nf = D.figura(FIGURAS / 'comparacion_modelos.png', 'Diferencias de ROC-AUC entre modelos, con intervalo de 95 % corregido.', 15.5)
    D.explicar(nf, 'Cada línea es el intervalo de una diferencia; si cruza la línea vertical, incluye 0.', 'Solo tres diferencias de ROC-AUC de esta figura excluyen 0: B − A, B_shannon − A y B_resto − referencia sencilla. Retirar indicadores de ejercicio, uno a uno o juntos, no cambia el rendimiento de forma clara.')
    D.h2('Comprobación contra el azar')
    nt = D.tabla('Pruebas contra el azar: 200 permutaciones de etiquetas. Sin corrección por los seis modelos.', ['Modelo', 'Medida', 'Observado', 'Promedio con azar', 'Percentil 95 con azar', 'k', 'p'],
                 [[f['modelo'], 'ROC-AUC' if f['metrica'] == 'roc_auc' else 'Exactitud bal.', p3(f['observado']), p3(f['media_azar']), p3(f['p95_azar']), str(int(f['k_mayores_o_iguales'])), p3(f['p'])] for _, f in T['pruebas_azar'].iterrows()],
                 [1.5, 2.8, 2, 2.8, 3.2, 1, 1.4], ['i', 'i', 'd', 'd', 'd', 'd', 'd'], tam=8.5, mantener=True)
    D.explicar(nt, 'Con cuánta frecuencia etiquetas barajadas igualan o superan el rendimiento real.', f'**B, C0, C1, D0 y D1 superan todas las permutaciones**, en ambas medidas (p = {p3(Z.loc[("B", "roc_auc"), "p"])}, el mínimo posible). **A no se distingue del azar** (p = {p3(Z.loc[("A", "roc_auc"), "p"])} con ROC-AUC). Esta prueba compara cada modelo con el azar; no indica cuánto mejora un modelo a otro. Con etiquetas barajadas, el promedio queda cerca de 0,5, como debe ocurrir si no hay filtración.')
    nf = D.figura(FIGURAS / 'pruebas_azar.png', 'ROC-AUC con etiquetas barajadas (barras) y con las etiquetas reales (línea azul).', 15.5)
    D.explicar(nf, 'La distribución de rendimiento si no existiera ninguna relación, frente al rendimiento real.', 'Excepto en A, la línea azul queda a la derecha de todas las barras.')
    D.h2('Sensibilidad sin IMC')
    nt = D.tabla('Efecto de retirar el IMC: modelo con IMC menos modelo sin IMC.', enc_cmp, filas_comparacion([(m, f'{m}_sin_imc') for m in PRIN]), anch_cmp, ali_cmp, tam=8)
    D.explicar(nt, 'Cuánto cambia cada modelo al retirar el IMC, con las mismas particiones.', f'**El resultado depende de la población.** En B, retirar el IMC reduce el ROC-AUC en {p3(C.loc[("B", "B_sin_imc", "roc_auc"), "diferencia"])} (IC 95 %: {ic("B", "B_sin_imc")}). En las demás poblaciones no hay diferencia clara; en D0 y D1, el rendimiento es levemente mayor sin IMC. Las comparaciones principales mantienen su lectura sin IMC en ROC-AUC, salvo B − A, cuyo intervalo pasa a incluir 0 ({ic("B_sin_imc", "A_sin_imc")}), aunque con exactitud balanceada queda respaldada.')
    nf = D.figura(FIGURAS / 'sensibilidad_imc.png', 'ROC-AUC de cada modelo principal con y sin IMC.', 13.5)
    x = T['sensibilidad_imc_importancia'].query("modelo == 'B'")
    cambio = x[x['aporte_con_imc'] != x['aporte_sin_imc']]
    D.explicar(nf, 'Cada par une el mismo modelo con IMC (azul) y sin IMC (gris).', 'Al retirar el IMC del modelo B, cambian de clase: ' + '; '.join(f'{nombre(f["variable"])} ({f["aporte_con_imc"].lower()} a {f["aporte_sin_imc"].lower()})' for _, f in cambio.iterrows()) + '. Esto muestra que los rótulos cercanos a los cortes son sensibles.')
    D.h2('Sensibilidad a la imputación en la partición')
    nt = D.tabla('Efecto de reimputar dentro de cada partición las cinco variables de la Fase 34B: modelo principal menos modelo reimputado.', enc_cmp, filas_comparacion(RV.COMPARACIONES[RV.IMPUTACION]), anch_cmp, ali_cmp, tam=8, mantener=True)
    D.explicar(nt, 'Si los resultados cambian al calcular esos valores solo con entrenamiento.', f'**No cambia ninguna lectura.** Las diferencias de ROC-AUC son mínimas ({r3(bi["diferencia"])} en B, {r3(c1i["diferencia"])} en C1 y {r3(d1i["diferencia"])} en D1), y además favorecen levemente a la versión reimputada. No hay indicios de que la imputación global haya inflado el rendimiento.')
    D.h2('Modelos secundarios')
    nt = D.tabla('Retirada de indicadores de ejercicio y uso del conjunto de Shannon.', enc_cmp, filas_comparacion([*RV.COMPARACIONES['retirada de variables'], *RV.COMPARACIONES['conjunto Shannon']]), anch_cmp, ali_cmp, tam=8)
    D.explicar(nt, 'Qué ocurre al volver a entrenar sin ciertas variables, o solo con las destacadas por Shannon. Las listas de Shannon se eligieron con todos los datos, de modo que estas comparaciones son exploratorias y potencialmente optimistas.', f'Retirar cualquier indicador de ejercicio apenas cambia el rendimiento, lo que sugiere **redundancia**. Las cinco variables generales de Shannon logran un ROC-AUC de {auc("B_shannon")}, y las otras 25, de {auc("B_resto")}, sobre el azar. Por lo tanto, las variables que no superaron q < 0,10 también contienen algo de información, aunque menos.')

    # ---- 8 ----
    D.h1('Importancia de variables')
    D.h2('Modelo general')
    nt = tabla_importancia('B')
    D.explicar(nt, 'Cuánto empeora el modelo B al barajar cada variable en evaluación. Incluye la medida complementaria, exactitud balanceada.', f'Las más importantes son IMC ({ia("B", "imc")}), tabaco ({ia("B", "tabaco_frecuencia")}), trabajar actualmente ({ia("B", "trabaja_actualmente")}) y días de ejercicio ({ia("B", "dias_ejercicio_semana")}). **Los valores son pequeños**, y la desviación estándar suele ser comparable al promedio. Las variables con valores negativos llegan a {f4(piso)}: esa magnitud da una idea del ruido, de modo que los aportes bajo 0,005 difícilmente se distinguen de él.')
    nf = D.figura(FIGURAS / 'importancia_B.png', 'Importancia de las variables en el modelo B, con ± 1 desviación estándar entre particiones.', 15.5)
    D.explicar(nf, 'Cada punto es la pérdida promedio de ROC-AUC. Azul: q < 0,10 en Shannon.', 'Las variables de Shannon tienden a ubicarse arriba, pero no todas: el ejercicio de fuerza queda cerca de cero. Tabaco y agua aportan sin haber superado q < 0,10.')
    D.h2('Grupos de variables')
    g = T['importancia_grupos'][T['importancia_grupos']['modelo'].isin(PRIN)]
    nt = D.tabla('Importancia de grupos, barajados con filas completas, en los modelos principales.', ['Modelo', 'Grupo', 'AUC: promedio', 'DE', 'Positivas', 'Exactitud bal.: promedio', 'Positivas', 'Clase'],
                 [[f['modelo'], f['nombre'], f4(f['auc_media']), p4(f['auc_de']), str(int(f['auc_positivas'])), f4(f['ba_media']), str(int(f['ba_positivas'])), f['aporte']] for _, f in g.iterrows()],
                 [1.2, 3.4, 1.6, 1.1, 1.2, 2.0, 1.2, 3.8], ['i', 'i', 'd', 'd', 'd', 'd', 'd', 'i'], tam=8.5, mantener=True)
    D.explicar(nt, 'Cuánto empeora el modelo al barajar juntas las variables relacionadas.', f'**La actividad física es el bloque más importante** en B ({p4(G.loc[("B", "Actividad física"), "auc_media"])}), y su importancia conjunta es mayor que la de cualquier indicador por separado. Ocurre lo mismo con días y bajo impacto ({p4(G.loc[("B", "Días y bajo impacto"), "auc_media"])}). El grupo Trabajo también destaca en C1 ({p4(G.loc[("C1", "Trabajo"), "auc_media"])}). En cambio, Cuidados es débil en D1 ({p4(G.loc[("D1", "Cuidados"), "auc_media"])}): su exactitud balanceada es negativa, aunque la regla lo rotule como consistente.')
    nf = D.figura(FIGURAS / 'importancia_grupos.png', 'Importancia de los grupos en los modelos principales, con ± 1 desviación estándar.', 14.5)
    D.explicar(nf, 'La pérdida de ROC-AUC al barajar cada grupo.', 'Los grupos de ejercicio aparecen en todas las poblaciones lejos de cero, con mayor variación entre cuidadoras.')
    D.h2('Advertencias sobre correlación y redundancia')
    D.p('La importancia se reparte entre variables relacionadas. Días, bajo impacto, fuerza y aeróbico miden aspectos cercanos, por lo que la importancia individual de cada una **subestima el aporte del bloque**. Barajar una sola variable también puede crear combinaciones poco realistas, como alguien sin días de ejercicio y con ejercicio diario de bajo impacto. Además, Random Forest puede favorecer variables con más categorías (Strobl et al., 2007). Por eso, las posiciones exactas no deben sobreinterpretarse.')
    D.p(f'**Las clases dependen de la medida y de cortes convencionales.** La clase se asigna con ROC-AUC, y no siempre se sostiene con exactitud balanceada: en B, días de ejercicio es positiva en {ibp("B", "dias_ejercicio_semana")} de 15 particiones y bajo impacto en {ibp("B", "frecuencia_bajo_impacto")}; en C1, distensión abdominal promedia {ib("C1", "distension_abdominal")}; en D1, bajo impacto promedia {ib("D1", "frecuencia_bajo_impacto")}. Además, bajo impacto y falta de tiempo alcanzan en B exactamente el mínimo de {ip("B", "frecuencia_bajo_impacto")} de 15, y dejan de ser consistentes al retirar el IMC.')

    # ---- 9 ----
    D.orientacion(True)
    D.h1('Comparación con Shannon')
    D.p(f'Shannon y Random Forest responden preguntas distintas. **Shannon** mide la asociación de cada variable por separado, sin indicar dirección. **Spearman** indica una tendencia ordinal y su dirección. **Random Forest** mide si una variable ayuda a predecir dentro de un modelo con las demás. **Ninguno demuestra causalidad.** Cada variable se lee en un solo modelo: las generales en B, las laborales en C1 y la sobrecarga en D1.')
    s = T['shannon_vs_rf']
    nt = D.tabla('Comparación de las 33 variables, por población y de mayor a menor importancia. Dirección según Spearman; importancia en pérdida de ROC-AUC. En azul, q < 0,10 en ambas versiones de Shannon.', ['Variable', 'Población', 'SU', 'q 10.000', 'q 50.000', 'Dirección', 'Importancia AUC', 'Positivas', 'Modelo', 'Clase RF', 'Consistencia', 'Limitaciones'],
                 [[nombre(f['variable']), f['poblacion'].capitalize(), p4(f['su']), p3(f['q_10000']), p3(f['q_50000']), f['direccion'].capitalize(), f4(f['auc_media']), str(int(f['auc_positivas'])), f['modelo_rf'], f['aporte_rf'].replace('Aporte ', '').capitalize(), f['consistencia'], f['advertencias'] if isinstance(f['advertencias'], str) and f['advertencias'] else '—'] for _, f in s.iterrows()],
                 [3.6, 1.4, 1.0, 1.0, 1.0, 1.4, 1.6, 1.3, 1.1, 1.4, 3.0, 5.0], ['i', 'i', 'd', 'd', 'd', 'i', 'd', 'd', 'i', 'i', 'i', 'i'], tam=7, resaltar=list(s['q_menor_0_10']))
    conteo = s['consistencia'].value_counts()
    D.explicar(nt, 'Para cada variable, su asociación según Shannon, su dirección, su importancia y si ambos métodos coinciden.', f'**Coinciden ambos métodos** en {conteo["Coinciden ambos métodos"]} variables; **solo Shannon**, en {conteo["Solo Shannon"]}; **solo Random Forest**, en {conteo["Solo Random Forest"]}; y **ninguno da respaldo** en {conteo["Sin respaldo en ninguno"]}. Las reglas de esta columna se fijaron antes de ver resultados.')
    D.orientacion(False)
    nf = D.figura(FIGURAS / 'shannon_vs_rf.png', 'SU con la severidad frente a la importancia en el modelo B, en las 30 variables generales.', 15.5)
    D.explicar(nf, 'Si las variables más asociadas según Shannon son también las más importantes en Random Forest.', f'**Hay una concordancia general alta entre ambos ordenamientos** (ρ de Spearman = {r3(rho_su)}, descriptivo), con excepciones claras: el ejercicio de fuerza tiene la mayor SU de este grupo y poca importancia; tabaco y agua tienen el patrón contrario.')
    D.h2('Días de ejercicio y bajo impacto')
    D.p(f'**Sus datos sugieren información en buena parte redundante.** Retirar días cambia el ROC-AUC en {d3("B", "B_sin_dias")} y retirar bajo impacto, en {d3("B", "B_sin_bajo_impacto")}. Al retirar ambas, la diferencia sube a {d3("B", "B_sin_dias_bajo_impacto")}, aunque el intervalo incluye 0 ({ic("B", "B_sin_dias_bajo_impacto")}). Al barajarlas juntas, la pérdida ({p4(G.loc[("B", "Días y bajo impacto"), "auc_media"])}) supera la suma de sus pérdidas individuales ({ia("B", "dias_ejercicio_semana")} y {ia("B", "frecuencia_bajo_impacto")}). Es decir, cada una puede sustituir en parte a la otra, y **conjuntamente aportan más que por separado**.')
    D.h2('Ejercicio de fuerza')
    D.p(f'**En el modelo general no resulta claramente útil para predecir.** Tiene la mayor SU entre las generales, pero su importancia es {ia("B", "frecuencia_fuerza")}, positiva en {ip("B", "frecuencia_fuerza")} de 15 particiones. Retirarla cambia el ROC-AUC en solo {d3("B", "B_sin_fuerza")}. Tiene un aporte consistente en C1 ({ia("C1", "frecuencia_fuerza")}), pero no en D1. Esto es coherente con lo observado en Shannon: su dirección no es clara, 84,7 % no la realiza y FCBF la usa como representante de un bloque redundante.')
    D.h2('IMC')
    D.p(f'**Sigue siendo la variable más importante en el modelo general, pese a las imputaciones,** con {ia("B", "imc")} y {ip("B", "imc")} de 15 particiones positivas. Retirarlo reduce el rendimiento de B de forma respaldada ({d3("B", "B_sin_imc")}). Este resultado debe leerse con tres cautelas: casi la mitad de los valores recibe la mediana; entre cuidadoras apenas aporta (D1: {ia("D1", "imc")}, {cl("D1", "imc")}); y el modelo A, que lo incluye, no supera al azar.')
    D.h2('Lugar de trabajo comprensivo')
    D.p(f'**Es la variable más importante entre trabajadoras** ({ia("C1", "lugar_trabajo_comprensivo")}; positiva en {ip("C1", "lugar_trabajo_comprensivo")} de 15), también con exactitud balanceada ({ib("C1", "lugar_trabajo_comprensivo")}). Sin embargo, la mejora de C1 frente a C0, que además incluye el estrés laboral, tiene un intervalo que incluye 0 ({ic("C1", "C0")}). Por lo tanto, **hay un indicio favorable, pero no una mejora respaldada**.')
    D.h2('Estrés laboral')
    D.p(f'**Aporta algo con ROC-AUC ({ia("C1", "estres_entorno_laboral")}; {ip("C1", "estres_entorno_laboral")} de 15), aunque no superó q < 0,10.** Con exactitud balanceada su aporte casi desaparece ({ib("C1", "estres_entorno_laboral")}; {ibp("C1", "estres_entorno_laboral")} de 15). Su señal es débil y depende de la medida.')
    D.h2('Sobrecarga física y emocional')
    D.p(f'**No se respalda que aporte información adicional entre cuidadoras.** Aunque su importancia es {ia("D1", SOB)} y se ubica cuarta en D1, con exactitud balanceada es {ib("D1", SOB)} (positiva en {ibp("D1", SOB)} de 15), y D1 − D0 no muestra diferencia clara ({ic("D1", "D0")}). Esto coincide con Shannon, donde tiene una tendencia ordinal, pero no supera q < 0,10.')
    D.h2('Tabaco, alcohol y agua')
    D.p(f'**Tabaco** tiene aporte consistente en los modelos B, C1 y D1 (B: {ia("B", "tabaco_frecuencia")}, positiva en {ip("B", "tabaco_frecuencia")} de 15), y es la señal más estable de las que no superaron q < 0,10. **Agua** aporta en B ({ia("B", "vasos_agua_dia")}) y D1 ({ia("D1", "vasos_agua_dia")}), pero es inestable en C1. **Alcohol** no muestra un patrón estable: {cl("B", "alcohol_frecuencia")} en B, {cl("C1", "alcohol_frecuencia")} en C1 y {cl("D1", "alcohol_frecuencia")} en D1.')

    # ---- 10 ----
    D.h1('Resultados específicos de trabajadoras y cuidadoras')
    D.h2('Trabajadoras')
    D.p('En estas 287 mujeres, `trabaja_actualmente` queda fuera por ser constante. C0 y C1 usan las mismas personas y particiones.')
    nt = tabla_importancia('C1')
    D.explicar(nt, 'La importancia de cada variable en C1.', f'Lugar de trabajo comprensivo ocupa el primer lugar, seguido de bajo impacto, tabaco y distensión abdominal. Barajar ambas variables laborales reduce el ROC-AUC en {p4(G.loc[("C1", "Trabajo"), "auc_media"])}, de forma positiva en las 15 particiones. Pero entrenar sin ellas (C0) no reduce el rendimiento de forma clara: el resto de las variables compensa parte de su información.')
    nf = D.figura(FIGURAS / 'importancia_C1.png', 'Importancia de las variables en el modelo C1, con ± 1 desviación estándar.', 15)
    D.explicar(nf, 'Cada punto es la pérdida promedio de ROC-AUC entre trabajadoras.', 'Los órdenes difieren del modelo general: días de ejercicio pierde importancia y bajo impacto gana. Estos cambios pueden deberse a la población o a la variación entre particiones.')
    D.p('Estos resultados describen a las trabajadoras de la muestra y no se extienden a quienes no trabajan.')
    D.h2('Cuidadoras')
    D.p('Las 239 cuidadoras tienen sobrecarga observada; las 12 con sobrecarga imputada no se incluyen. Es la población más pequeña y la más variable.')
    nt = tabla_importancia('D1')
    D.explicar(nt, 'La importancia de cada variable en D1.', f'Días de ejercicio, agua y tabaco superan a la sobrecarga ({ia("D1", SOB)}). `cantidad_personas_cuida` no muestra aporte útil en D1 ({f4(I.loc[("D1", "cantidad_personas_cuida"), "auc_media"])}). El grupo de cuidados es débil.')
    nf = D.figura(FIGURAS / 'importancia_D1.png', 'Importancia de las variables en el modelo D1, con ± 1 desviación estándar.', 15)
    D.explicar(nf, 'Cada punto es la pérdida promedio de ROC-AUC entre cuidadoras.', 'Los intervalos son amplios. El IMC, primero en el modelo general, aquí queda cerca de cero.')
    D.p(f'**Limitación específica.** Entre estas cuidadoras, `frecuencia_fuerza` llega a 86,61 % en «No lo realiza». Además, la pregunta de sobrecarga menciona el trabajo, y 99 de ellas no trabajan.')

    # ---- 11 ----
    D.h1('Discusión')
    D.h2('Respuesta a las preguntas')
    D.lista([f'**Qué ayuda más.** En el modelo general, el bloque de actividad física como grupo; individualmente, IMC, tabaco, trabajar actualmente y días de ejercicio. Entre trabajadoras destaca el lugar de trabajo comprensivo; entre cuidadoras, días de ejercicio, agua y tabaco.',
             '**Las seis de Shannon.** Cinco también aportan de forma consistente en su modelo de lectura. Ejercicio de fuerza es la excepción en el modelo general.',
             f'**Variables que no superaron q < 0,10.** Tabaco, agua, distensión, falta de tiempo, estrés y sobrecarga aportan en la importancia. Las 25 generales sin q < 0,10 alcanzan un ROC-AUC de {auc("B_resto")}. Agregarlas a las cinco de Shannon no mejora el ROC-AUC de forma clara ({d3("B", "B_shannon")}), pero sí la exactitud balanceada ({d3("B", "B_shannon", "balanced_accuracy")}).',
             f'**Hábitos y salud.** Sí mejoran la predicción medida con ROC-AUC ({d3("B", "A")}). Con exactitud balanceada, el resultado queda en el límite.',
             f'**Variables laborales.** Hay un indicio favorable, sin mejora respaldada ({d3("C1", "C0")}).',
             f'**Sobrecarga.** No se respalda un aporte adicional ({d3("D1", "D0")}).',
             '**Estabilidad.** Superan al azar, salvo A, pero hay sobreajuste marcado y variación considerable. Las posiciones individuales son poco estables.'], numerada=True)
    D.h2('Por qué la importancia y la comparación entre modelos pueden diferir')
    D.p('Una variable puede ser importante al barajarla y, aun así, su retirada puede no cambiar el rendimiento. Barajar evalúa un modelo ya entrenado que **dependía** de ella. Volver a entrenar permite que otras variables la **reemplacen**. Así ocurre con el trabajo entre trabajadoras y con los indicadores de ejercicio. Ambas lecturas son válidas: la primera indica que la información es útil; la segunda, que no es exclusiva de esa variable.')
    D.h2('Asociación, dirección, predicción y causalidad')
    D.tabla('Qué responde cada medida.', ['Medida', 'Responde', 'No responde'],
            [['SU y q (Shannon)', '¿Comparte información con la severidad, por sí sola?', 'Dirección, aporte conjunto, causa'], ['ρ de Spearman', '¿Hay una tendencia ordinal y en qué dirección?', 'Relaciones no monótonas, causa'], ['Importancia en Random Forest', '¿El modelo se apoya en ella para predecir?', 'Dirección, aporte exclusivo, causa'], ['Comparación entre modelos', '¿Mejora la predicción al agregarla?', 'Causa, validez clínica']],
            [4.4, 6.6, 5.5], tam=9, mantener=True)
    D.h2('Contraste con lo programado en la simulación')
    D.p('Los datos son sintéticos. El simulador define efectos directos para IMC, ejercicio, agua, tabaco, alcohol, estrés laboral, lugar de trabajo y sobrecarga, entre otros. **Solo se consultan para interpretar: no se usaron para entrenar ni evaluar.**')
    D.lista(['**Coherente con lo programado:** IMC, días de ejercicio, tabaco, agua y lugar de trabajo muestran aporte. Por eso, estos hallazgos no constituyen un descubrimiento independiente.', '**Sin efecto directo programado:** trabajar actualmente solo tiene un efecto mediante la doble carga, que está excluida. Distensión abdominal y falta de tiempo tampoco figuran entre los efectos directos, pese a su aporte consistente en B, de modo que pueden reflejar relaciones indirectas o azar.', f'**Programado, pero sin patrón estable:** el alcohol tiene el mayor coeficiente de los hábitos en la escala interna (+0,65), pero es inestable en B ({ia("B", "alcohol_frecuencia")}) y nulo en D1. Un efecto programado no garantiza una señal detectable, especialmente si la respuesta es poco frecuente o se distorsiona con la suciedad agregada.'])
    D.h2('Sobre los resultados desfavorables')
    D.p('Es importante no sobrevalorar estos modelos: su capacidad es modesta, cometen errores frecuentes en ambas clases y el rendimiento cae mucho fuera del entrenamiento. Las dos comparaciones específicas (trabajo y sobrecarga) no superan el criterio fijado. Estos resultados no se ajustaron para mejorarlos.')

    # ---- 12 ----
    D.h1('Limitaciones')
    D.lista(['**Datos sintéticos.** Algunas relaciones fueron programadas. No se generaliza a mujeres reales y la capacidad predictiva en este conjunto no es validez clínica.', '**Sin causalidad.** Las variables se miden al mismo tiempo que los síntomas.', '**Análisis no independiente de Shannon.** Sus resultados se conocían al diseñar este análisis, y las listas del conjunto Shannon se eligieron con todos los datos, lo que puede favorecerlas.', '**IMC faltante en 49,5 %.** La imputación con mediana reduce su variación y puede subestimar su aporte.', '**Otras imputaciones.** Se conservan las de la Fase 34B; solo cinco variables se revisaron en sensibilidad, y una celda de `cantidad_personas_cuida` no pudo identificarse.', '**Particiones dependientes.** El intervalo corregido es aproximado.', '**Importancia sin corrección múltiple.** Se evaluaron muchas variables; algún aporte puede deberse al azar. Los rótulos dependen de cortes convencionales y son sensibles: algunos cambian al retirar el IMC.', '**Variables correlacionadas.** La importancia individual se reparte y puede subestimar los bloques.', '**Sin ajuste de hiperparámetros ni de punto de corte.** Era lo acordado para esta primera ejecución, de modo que no representa el mejor rendimiento posible.', '**Tamaños menores.** Los modelos de trabajadoras y cuidadoras son menos precisos.', '**Poblaciones específicas.** La población laboral excluye a 22 mujeres sin ambas respuestas laborales, y `frecuencia_fuerza` llega a 86,61 % entre cuidadoras, sobre el 85 %, aunque la regla de dominancia se mide en su población general.', '**Pruebas contra el azar sin corrección.** El mínimo posible es 0,005, por lo que no distinguen valores menores.'])

    # ---- 13 ----
    D.h1('Conclusiones')
    D.lista([f'**Capacidad modesta.** Las variables superan al azar en B, C0, C1, D0 y D1, con ROC-AUC entre {auc("B")} y {auc("C1")}, y con sobreajuste marcado.', f'**Más variables, mejor predicción general.** B supera a A en ROC-AUC ({d3("B", "A")}), aunque el resultado queda en el límite con exactitud balanceada.', '**Concordancia con Shannon.** Cinco de las seis variables destacadas también aportan; ejercicio de fuerza es la excepción en el modelo general.', '**Información adicional fuera de las seis.** Tabaco y agua destacan especialmente, aunque esas señales no demuestran un efecto.', '**La actividad física importa como bloque.** Sus indicadores son en buena parte redundantes entre sí.', '**El entorno laboral es un indicio, no una mejora demostrada.** Lugar de trabajo comprensivo es la variable más importante entre trabajadoras.', '**La sobrecarga no muestra un aporte adicional claro.**', '**Resultados robustos a la imputación en partición.** El IMC importa en el modelo general, no en todas las poblaciones.', '**Sin causalidad ni validez clínica.**'], numerada=True)

    # ---- 14 ----
    D.h1('Implicaciones para la Fase 36')
    D.p('**Las 33 variables se conservan como conjunto inicial de la Fase 36.** Random Forest no elimina ninguna. Este informe aporta los siguientes elementos para considerar, sin adelantar decisiones:')
    D.lista(['**Actividad física.** Considerar cómo representar un bloque redundante para que no domine la formación de clústeres.', '**Variables con poca señal.** Una importancia baja no justifica retirarlas de forma automática: la segmentación persigue otro objetivo.', '**IMC.** Tener presente que casi la mitad de sus valores es imputada.', '**Poblaciones específicas.** Las variables laborales y la sobrecarga solo aplican a ciertas personas, de modo que requieren un tratamiento explícito.', '**Interpretación.** Las variables con aporte pueden ayudar a describir clústeres, sin presentarse como causas ni como reglas clínicas.', '**Entrada.** Usar `dataset_fase35_33_variables.csv` y `predictores_elegibles_33.csv`, no `dataset_fase35b.csv`.'])
    D.p('Esta fase no inicia la segmentación. Se espera la revisión de este informe antes de avanzar.')

    # ---- Anexos ----
    D.orientacion(True)
    D.anexo('A', 'Rendimiento de los 26 modelos')
    D.tabla('Rendimiento completo en evaluación. Incluye diferencia con entrenamiento.', ['Modelo', 'Función', 'n', 'Var.', 'ROC-AUC', 'DE', 'Entren.', 'Exact. bal.', 'DE', 'Entren.', 'F1 sev.', 'F1 no sev.'],
            [[m, f['funcion'], str(int(f['n'])), str(int(f['n_variables'])), p3(f['roc_auc_evaluacion']), p3(f['roc_auc_de']), p3(f['roc_auc_entrenamiento']), p3(f['balanced_accuracy_evaluacion']), p3(f['balanced_accuracy_de']), p3(f['balanced_accuracy_entrenamiento']), p3(f['f1_severos_evaluacion']), p3(f['f1_no_severos_evaluacion'])] for m, f in R.iterrows()],
            [4.1, 4.1, 0.8, 0.8, 1.3, 1, 1.2, 1.4, 1, 1.2, 1.2, 1.4], ['i', 'i', 'd', 'd', 'd', 'd', 'd', 'd', 'd', 'd', 'd', 'd'], tam=8)
    D.orientacion(False)
    D.anexo('B', 'Comparaciones contra el clasificador sencillo y sin IMC')
    D.tabla('Modelos frente al clasificador sencillo.', enc_cmp, filas_comparacion(RV.COMPARACIONES['referencia']), anch_cmp, ali_cmp, tam=8)
    D.tabla('Comparaciones principales, entre modelos sin IMC.', enc_cmp, filas_comparacion([('B_sin_imc', 'A_sin_imc'), ('C1_sin_imc', 'C0_sin_imc'), ('D1_sin_imc', 'D0_sin_imc')]), anch_cmp, ali_cmp, tam=8, mantener=True)
    D.anexo('C', 'Variables de cada modelo')
    D.tabla('Listado exacto de variables de cada modelo.', ['Modelo', 'n', 'Variables'],
            [[m, str(int(f['n_variables'])), f['variables'].replace(';', ', ')] for m, f in Mod.iterrows() if not m.startswith('Ref')],
            [3.8, 0.8, 11.9], ['i', 'd', 'i'], tam=7.5)
    D.anexo('D', 'Importancia en los demás modelos')
    for m in ('A', 'C0', 'D0'):
        tabla_importancia(m)
    D.anexo('E', 'Trazabilidad y archivos')
    D.tabla('Dónde encontrar cada elemento, dentro de `analisis/random_forest_revision_35b_33_variables/`.', ['Elemento', 'Archivo'],
            [['Protocolo', '`protocolo_random_forest_33.md`'], ['Programa y pruebas', '`rf_33_variables.py`, `test_rf_33_variables.py`'], ['Registro', '`registro_ejecucion.txt`'], ['Resultados por partición', '`resultados/crudos/`'], ['Rendimiento y comparaciones', '`resultados/rendimiento_modelos.csv`, `comparacion_modelos.csv`, `matrices_confusion.csv`, `pruebas_azar.csv`'], ['Importancias', '`resultados/importancia_variables.csv`, `importancia_grupos.csv`'], ['Sensibilidades', '`resultados/sensibilidad_imc.csv`, `sensibilidad_imc_importancia.csv`, `sensibilidad_imputacion.csv`, `revision_imputaciones_34B.csv`, `imc_faltante_y_severidad.csv`'], ['Comparación con Shannon', '`resultados/shannon_vs_rf.csv`'], ['Figuras', '`figuras/`'], ['Shannon, sin cambios', '`reunion_2026-11-03/revision_33_variables/`'], ['Base del código', 'Commit `745d689`; este análisis no tiene commit']],
            [4.8, 11.7], tam=8.5, mantener=True)
    D.salto()
    D.h0('Referencias')
    for t in ['Breiman, L. (2001). Random forests. __Machine Learning__, 45(1), 5-32.', 'Heinemann, K., Ruebig, A., Potthoff, P., Schneider, H. P. G., Strelow, F., Heinemann, L. A. J. y Do, M. T. (2004). The Menopause Rating Scale (MRS) scale: a methodological review. __Health and Quality of Life Outcomes__, 2, 45.', 'Nadeau, C. y Bengio, Y. (2003). Inference for the generalization error. __Machine Learning__, 52(3), 239-281.', 'Ojala, M. y Garriga, G. C. (2010). Permutation tests for studying classifier performance. __Journal of Machine Learning Research__, 11, 1833-1863.', 'Pedregosa, F., et al. (2011). Scikit-learn: machine learning in Python. __Journal of Machine Learning Research__, 12, 2825-2830.', 'Strobl, C., Boulesteix, A.-L., Zeileis, A. y Hothorn, T. (2007). Bias in random forest variable importance measures: illustrations, sources and a solution. __BMC Bioinformatics__, 8, 25.']:
        q = D.p(t, justificar=False)
        q.paragraph_format.left_indent, q.paragraph_format.first_line_indent = Cm(1), Cm(-1)
    return D


def main():
    if SALIDA.exists():
        raise FileExistsError(f'No se sobrescribe: {SALIDA}')
    vigilados = RV.archivos_vigilados()
    antes = P.manifiesto(vigilados)
    T = cargar()
    comprobar(T)
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    D = construir(T)
    D.d.save(SALIDA)
    cambiados = P.comparar_manifiestos(antes, P.manifiesto(vigilados))
    if cambiados:
        raise SystemExit('Cambiaron archivos vigilados: ' + ', '.join(cambiados))
    print(f'Guardado {SALIDA}: {len(D.d.tables)} tablas, {D.figs} figuras. Archivos vigilados sin cambios ({len(antes)}).')


if __name__ == '__main__':
    main()
