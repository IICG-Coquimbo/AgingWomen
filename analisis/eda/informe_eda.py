"""Informe del EDA completo en Markdown (analisis/informe_eda.md, Fase 34)."""
from datetime import date

import pandas as pd

from limpieza import reglas as R

from . import revision
from . import variables as V
from .informe import _f, _p, _tabla

FIG = 'figuras/eda_completo'
RANGOS_MRS = ['0-4', '5-8', '9-15', '16-44']


def _figura(numero, archivo, titulo, pie, como=None, muestra=None):
    """Figura con título, pie y, opcionalmente, cómo leerla y qué muestra."""
    out = [f'**Figura {numero}. {titulo}**', '', f'![{titulo}]({archivo})', '', f'*{pie}*', '']
    if como:
        out += [f'**Cómo leerla.** {como[0].upper()}{como[1:]}', '']
    if muestra:
        out += [f'**Qué muestra.** {muestra[0].upper()}{muestra[1:]}', '']
    return out


def _top_rf(k=5):
    """Las k variables más importantes del Random Forest general (Fase 33), si existe."""
    ruta = V.RAIZ / 'analisis' / 'resultados' / 'importancia_variables.csv'
    if not ruta.exists():
        return 'las de mayor importancia'
    imp = pd.read_csv(ruta, encoding='utf-8-sig')
    t = imp[(imp['modelo'] == 'general') & (imp['tarea'] == 'regresion')].head(k)
    return ', '.join(t['etiqueta'])


# Alimentación y sustancias que se muestran en la sección 6.1 (por qué no se asocian).
HABITOS = ['tabaco_frecuencia', 'alcohol_frecuencia', 'marihuana_frecuencia', 'platos_verduras_dia',
           'frutas_dia']


def _seccion_habitos(habitos, asoc):
    """Subsección 6.1: % de severas por nivel de consumo y por qué no hay asociación."""
    p = asoc.set_index('variable')
    filas = []
    for v in HABITOS:
        t = habitos[v]
        niveles = ' · '.join(f'{nivel}: {t.at[nivel, "Severa"]:.0f} % (n={int(t.at[nivel, "n"])})'
                             for nivel in t.index)
        filas.append((V.etiqueta(v), niveles, f'{p.at[v, "efecto"]:+.2f}', _p(p.at[v, 'p_ajustado'])))
    nunca = {v: 100 * habitos[v]['n'].iloc[0] / habitos[v]['n'].sum() for v in HABITOS[:3]}
    alc = habitos['alcohol_frecuencia']['Severa']
    return [
        '### 6.1 ¿Por qué alimentación y sustancias no se asocian con la severidad?',
        '',
        'En este conjunto de datos, quienes comen o consumen distinto tienen casi la **misma proporción de',
        'síntomas severos** (alrededor del 40 %, que es el promedio general). Porcentaje de mujeres con',
        'síntomas severos en cada nivel de consumo:',
        '',
        _tabla(['Variable', '% con síntomas severos por nivel', 'rho', 'p ajustado'], filas),
        '',
        'Hay cinco razones que lo explican:',
        '',
        f'1. **Casi nadie consume algunas sustancias.** El {nunca["marihuana_frecuencia"]:.0f} % nunca usa '
        f'marihuana y el {nunca["tabaco_frecuencia"]:.0f} % nunca fuma.',
        '   Con tan pocas consumidoras los grupos son demasiado pequeños para detectar una diferencia, aunque exista.',
        '2. **Spearman solo detecta relaciones en una dirección.** El alcohol tiene forma de **U**: más',
        f'   severidad en quienes nunca beben ({alc.iloc[0]:.0f} %) y en quienes beben a diario ({alc.iloc[-1]:.0f} %),',
        f'   y menos en quienes beben 1-2 veces por semana ({alc.iloc[1]:.0f} %). Spearman mide si "más consumo',
        '   → más (o menos) severidad", así que una U le da casi cero. El grupo diario es pequeño, por lo',
        '   que también puede ser azar.',
        '3. **Los extremos pequeños solo agregan ruido.** Las frutas parecen ir "al revés" (más fruta, más',
        '   severidad), pero eso depende de grupos muy pequeños en los extremos y no es significativo.',
        '4. **Probablemente el conjunto de datos no trae esa relación.** Es la explicación más importante.',
        '   El conjunto es **sintético**: una relación solo aparece si la simulación la incluyó. Las',
        '   variables que sí se asocian (IMC, cuidado, estrés laboral, ejercicio) muestran un patrón',
        '   ordenado; alimentación y sustancias se ven planas, como si se hubieran generado sin relación',
        '   con el MRS. Queda pendiente confirmarlo con la profesora.',
        '5. **Las preguntas son gruesas.** Se mide por porciones o frecuencia en categorías amplias, lo que',
        '   capta mal la calidad de la dieta y diluye efectos pequeños.',
        '',
        '**Cómo se reporta.** No se fuerza el resultado: un hallazgo nulo también es un resultado. La',
        'redacción correcta es "en este conjunto de datos no se observó asociación", **no** "la alimentación',
        'no influye en los síntomas". Además, la **ganancia de información** de la Fase 35 sí detecta',
        'relaciones en forma de U como la del alcohol, porque no exige una dirección: ahí se volverá a',
        'evaluar si estas variables aportan algo.',
        '',
    ]


def _rf_anexo():
    """Resumen del Random Forest (Fase 33) para el Anexo B, si ya se ejecutó."""
    ruta = V.RAIZ / 'analisis' / 'resultados' / 'importancia_variables.csv'
    informe = V.RAIZ / 'analisis' / 'informe_exploratorio.md'
    if not ruta.exists() or not informe.exists():
        return ['*Falta ejecutar `python analisis/exploratorio.py` para completar este anexo.*', '']
    imp = pd.read_csv(ruta, encoding='utf-8-sig')
    metricas = [l for l in informe.read_text(encoding='utf-8').splitlines()
                if l.startswith(('### Modelo', '- Regresión sobre', '- Clasificación severa'))]
    out = ['Métricas de validación cruzada (5 particiones), tomadas de `informe_exploratorio.md`:', '']
    out += [l.replace('### ', '- **') + '**' if l.startswith('###') else '  ' + l for l in metricas]
    general = imp[(imp['modelo'] == 'general') & (imp['tarea'] == 'regresion')].head(10)
    out += ['', 'Diez variables más importantes del modelo general (regresión, importancia por permutación):', '',
            _tabla(['Variable', 'Importancia', 'Positiva en', 'Selección final'],
                   [(r.etiqueta, f'{r.perm_media:.4f}', f'{r.perm_positiva_en}/5',
                     'sí' if r.seleccion_final else 'no') for r in general.itertuples()]), '']
    return out


def generar(r):
    n, n_mrs, conteo = r['n'], r['n_mrs'], r['conteo']
    atip, coher, corr, falt = r['atip'], r['coher'], r['corr'], r['falt']
    spear, sig, asoc = r['spear'], r['sig'], r['asoc']
    reales = falt[~falt['variable'].isin(list(V.MRS_ITEMS))]
    imputadas = reales[reales['tratamiento'].str.startswith('imputada')]
    no_sig = spear[spear['p_ajustado'] >= 0.05]
    nominales = asoc[(asoc['prueba'] == 'Kruskal-Wallis')]
    impacto = asoc[asoc['rol'] == 'impacto']
    nom_sig = nominales[(nominales['p_ajustado'] < 0.05) & nominales['rol'].isin(
        ('predictor', 'predictor (trabajo)', 'control', 'subgrupo profesional', 'otra'))]
    ej = r['sev_ejercicio']
    fila_ej = asoc.set_index('variable').loc['dias_ejercicio_semana']
    sev_0 = ej['Severa'].iloc[0]
    sev_resto = (ej['Severa'].iloc[1:] * ej['n'].iloc[1:]).sum() / ej['n'].iloc[1:].sum()
    sev_56, n_56 = ej.loc['5-6 días', 'Severa'], int(ej.loc['5-6 días', 'n'])
    total_atip = int((atip['atipicos_bajos'] + atip['atipicos_altos']).sum())
    pas_pad = corr[corr['variable'].str.startswith('presion')]
    pesos = corr[corr['variable'] == 'peso_kg']
    n_44 = int(atip.set_index('variable').at['mrs_total', 'atipicos_altos'])
    rho_max = sig['efecto'].abs().max()

    out = [
        '# Análisis exploratorio de datos completo (Fase 34)',
        '',
        f'Generado por `analisis/eda_completo.py` el {date.today().isoformat()}. Responde a la reunión con la',
        'profesora del 16 de octubre: antes de seleccionar variables hay que terminar el EDA (purificar los',
        'datos, revisar atípicos y faltantes, y revisar con la matriz de correlación qué variables se',
        'relacionan con la severidad). Es el paso previo del Objetivo 2.',
        '',
        '> **Sobre el conjunto de datos.** A partir del Objetivo 2 se trabaja con un **conjunto de datos',
        '> sintético**: la profesora lo generó a partir del dataset "menopausia" y llenó por simulación las',
        '> variables que faltaban, porque en ese momento aún no se había hecho la recolección con la',
        '> encuesta. Tiene el mismo esquema que la encuesta de la plataforma. En este informe se habla de',
        '> "conjunto de datos" y no de "base de datos".',
        '',
        '## Resumen de decisiones',
        '',
        _tabla(['Tema', 'Decisión', 'Sección'], [
            ('Variable objetivo', 'severidad del MRS en 4 clases (0 a 3)', '2'),
            ('MRS de 44 puntos', f'se conservan ({n_44} participantes): síntomas severos posibles', '2 y 4'),
            ('Faltantes estructurales ("no aplica")', 'no se imputan: la pregunta no se mostró', '3'),
            ('Faltantes reales', 'se imputan (mediana/moda o desde una variable relacionada) y se marcan', '3'),
            ('Atípicos estadísticos (Tukey)', f'se detectan ({total_atip}) y se revisan; los clínicamente posibles '
             'se conservan', '4'),
            ('Valores imposibles o incoherentes', 'se vacían y se reimputan; ninguna participante se elimina', '5'),
            ('Random Forest (Fase 33)', 'pasa a complemento, en el Anexo B', 'Anexo B'),
        ]),
        '',
        '## 1. Conjunto de datos analizado',
        '',
        f'- Entrada: `datos/limpio/dataset_menopausia_limpio.csv` (Fase 32): **{n} participantes** tras',
        '  quitar duplicados, RUT repetidos y edades fuera de criterio (ver `informe_limpieza.md`).',
        f'- Con las 11 preguntas del MRS respondidas: **{n_mrs}**. Son las que entran al análisis de severidad',
        '  y forman el conjunto de salida `datos/analitico/conjunto_eda.csv` (entrada de la Fase 35).',
        '- Laboratorio y presión arterial solo existen en las 259 encuestas aplicadas por personal de salud',
        '  (subgrupo profesional); en las autoaplicadas esas preguntas no se muestran.',
        '',
        '## 2. Variable objetivo: severidad de los síntomas',
        '',
        'El puntaje MRS total (0 a 44) se convierte en una variable de **severidad con cuatro clases**, que es',
        'la variable objetivo del análisis. Los cortes son los de `MRS.SEVERIDAD_TOTAL` en la plataforma:',
        '',
        _tabla(['Código', 'Clase', 'Puntaje MRS', 'Participantes', '%'],
               [(i, s, RANGOS_MRS[i], int(conteo[s]), _f(100 * conteo[s] / n_mrs))
                for i, s in enumerate(V.ORDEN_SEVERIDAD)]),
        '',
        *_figura(1, f'{FIG}/severidad_clases.png', 'Distribución de la variable objetivo',
                 'Cuatro clases ordenadas; la clase severa es la más frecuente, por lo que las clases no están '
                 'balanceadas (se tendrá en cuenta al evaluar modelos).',
                 'cada barra es una clase de severidad y su altura es el número de mujeres en ella; el azul más '
                 'oscuro indica más severidad. Sobre cada barra está el número y el porcentaje.',
                 f'el grupo más grande es "Severa" ({int(conteo["Severa"])} mujeres, '
                 f'{100 * conteo["Severa"] / n_mrs:.0f} %), y los más pequeños son "Sin síntomas o muy leves" y '
                 '"Leve" (alrededor del 15 % cada uno). Las clases no están balanceadas, y eso hay que tenerlo en '
                 'cuenta en los modelos.'),
        *_figura(2, f'{FIG}/mrs_total.png', 'Puntaje MRS total y cortes de severidad',
                 'Las líneas punteadas marcan los cortes 4/5, 8/9 y 15/16.',
                 'es un histograma: cada barra es un puntaje MRS (0 a 44) y su altura es cuántas mujeres lo '
                 'obtuvieron. Las líneas punteadas separan las cuatro clases.',
                 'cómo se reparten los puntajes y de dónde salen las clases de la Figura 1. Las participantes con '
                 '44 puntos aparecen solas en el extremo derecho.'),
        f'{n_44} participantes tienen **44 puntos**, el máximo posible (todos los síntomas en grado 4). La regla',
        'de Tukey las marca como atípicas (límite superior 42), pero **se conservan**: una mujer puede tener',
        'todos los síntomas en grado muy severo, y eliminarlas sacaría del análisis justamente a quienes',
        'más necesitan la caracterización.',
        '',
        '## 3. Datos faltantes',
        '',
        'Se distinguen dos tipos de vacío:',
        '',
        '- **Estructural ("no aplica")**: la encuesta no mostró la pregunta por su lógica condicional (por',
        '  ejemplo, la sección Trabajo a quien no trabaja, o el laboratorio en encuestas autoaplicadas). No',
        '  es un dato perdido y **no se imputa**.',
        '- **Real**: la pregunta se mostró y quedó en blanco o con un valor inválido. Se imputa:',
        f'  menos de {R.UMBRAL_IMPUTAR:g} % → mediana (ordinales y continuas) o moda (categóricas);',
        f'  {R.UMBRAL_IMPUTAR:g}-{R.UMBRAL_EXCLUIR:g} % → igual, y además se agrega la columna `<variable>_imputado`;',
        f'  más de {R.UMBRAL_EXCLUIR:g} % → no se modela. Peso, cintura y presiones se imputan **desde una variable',
        '  relacionada** (sección 5) para no crear combinaciones imposibles.',
        '- Los ítems del MRS no se imputan: son la variable resultado. Quien no completó el MRS queda fuera',
        f'  del análisis de severidad ({n - n_mrs} participantes).',
        '',
        f'{len(reales)} variables tienen algún faltante real; ninguna supera el {R.UMBRAL_EXCLUIR:g} %. El detalle',
        'completo está en `resultados/faltantes.csv` y en la Figura A2 (Anexo A).',
        '',
        _tabla(['Variable', 'Ámbito', 'Aplica', 'No aplica', 'Faltantes', '%', 'Tratamiento'],
               [(V.etiqueta(x.variable), x.ambito, x.filas_aplica, x.no_aplica, x.faltantes,
                 _f(x.pct_faltante), x.tratamiento) for x in imputadas.head(15).itertuples()]),
        '',
        f'*Se muestran las 15 variables con más faltantes reales, de {len(imputadas)} imputadas.*',
        '',
        '## 4. Valores atípicos',
        '',
        '**Criterio.** La regla de Tukey marca como atípico todo valor bajo Q1 − 1,5·RIC o sobre',
        'Q3 + 1,5·RIC. Se calcula solo sobre valores **medidos** (los imputados no son observaciones).',
        'Un atípico estadístico **no es lo mismo que un error**: solo dice que el valor se aleja del resto',
        'del grupo. Por eso cada variable se revisa contra dos referencias:',
        '',
        '1. **Rango fisiológico plausible** (limpieza, paso 5). Lo que cae fuera, como peso de 994 kg,',
        '   talla de 1620 cm o glicemia de 9999, ya se trató como error en la limpieza.',
        '2. **Categorías clínicas reconocidas.** Si los atípicos altos corresponden a una condición real y',
        '   frecuente en mujeres de 40-65 años (obesidad, hipertensión, diabetes, dislipidemia), se',
        '   conservan: eliminarlos sacaría del análisis a los grupos de riesgo que interesa caracterizar.',
        '',
        *_figura(3, f'{FIG}/atipicos.png', 'Detección de atípicos por variable',
                 'Cada caja va de Q1 a Q3; los bigotes llegan hasta 1,5·RIC y los puntos rojos son los atípicos. '
                 'Cada panel tiene su propia escala.',
                 'hay un diagrama de caja por variable. La caja contiene al 50 % central de las mujeres y la línea '
                 'dentro de ella es la mediana. Los bigotes marcan hasta dónde llegan los valores "normales" para el '
                 'grupo, y los puntos rojos son los atípicos, es decir, los valores que se alejan del resto.',
                 'cuántos atípicos tiene cada variable. La mayoría están en '
                 + ' y '.join(f'{V.etiqueta(x.variable).lower()} ({x.t})'
                              for x in atip.assign(t=atip['atipicos_bajos'] + atip['atipicos_altos'])
                              .nlargest(2, 't').itertuples())
                 + ', que corresponden a mujeres con diabetes o triglicéridos altos. Son valores reales, por eso '
                 'no se eliminan.'),
        _tabla(['Variable', 'n medidos', 'Límites Tukey', 'Atípicos bajos', 'Atípicos altos',
                'Rango plausible', 'Altos en categoría clínica', 'Decisión'],
               [(V.etiqueta(x.variable), x.n, f'{_f(x.limite_inferior)} a {_f(x.limite_superior)}',
                 f'{x.atipicos_bajos}' + (f' ({x.valores_bajos})' if x.atipicos_bajos else ''),
                 x.atipicos_altos, x.rango_plausible,
                 f'{x.altos_en_categoria_clinica} de {x.atipicos_altos}' if x.atipicos_altos else '-',
                 x.decision) for x in atip.itertuples()]),
        '',
        '**Justificación por variable:**',
        '',
    ]
    for x in atip.itertuples():
        if x.atipicos_bajos + x.atipicos_altos == 0:
            continue
        out.append(f'- **{V.etiqueta(x.variable)}**: {x.criterio_clinico}.'
                   + (f' Altos: {x.valores_altos}.' if x.atipicos_altos else '')
                   + (f' Bajos: {x.valores_bajos}.' if x.atipicos_bajos else ''))
    out += [
        '',
        'Detalles que conviene destacar:',
        '',
        '- **Glicemia y triglicéridos** concentran la mayoría de los atípicos porque su distribución es',
        '  asimétrica: casi todas las mujeres tienen valores normales y un grupo tiene valores de diabetes o',
        '  hipertrigliceridemia. Es el patrón esperado en esta población, no un error.',
        '- **Edad 34**: participantes con menopausia quirúrgica, que la encuesta admite como excepción de edad.',
        '- **Cintura de 53-57,5 cm**: mujeres delgadas (IMC bajo); ver el caso 441 en la sección 5.',
        '',
        f'**Resultado:** de {total_atip} atípicos detectados no se elimina ninguno. Todos están dentro del rango',
        'fisiológico, y los altos corresponden a condiciones clínicas reconocidas. Los análisis siguientes no se',
        'ven distorsionados por mantenerlos: la Fase 35 (entropía) y la Fase 38 (reglas) agrupan las variables',
        'en categorías clínicas, donde un extremo queda en la categoría más alta; para K-Means (Fase 37) se',
        'usará un escalado robusto en la Fase 36.',
        '',
        '## 5. Coherencia entre mediciones',
        '',
        'Un valor puede estar dentro de su rango y aun así ser imposible **en combinación** con otro. Durante',
        'esta fase se revisaron las combinaciones y se encontró que el problema no estaba en los datos',
        'originales sino en la **imputación con la mediana** de la limpieza:',
        '',
        f'- **Peso** ({len(pesos)} faltantes reales; venían como -1, "N/A" o fuera de rango). Imputar 71 kg a',
        '  todas producía IMC incoherentes con la cintura medida. El caso más claro: participante 441, de',
        '  1,75 m y 53 cm de cintura, a quien se le asignaban 71 kg (IMC 23,2), incompatible con esa cintura.',
        '  Ahora el peso se estima desde la cintura (recta IMC ~ cintura, r ≈ 0,9) y la talla: 47,4 kg,',
        '  IMC 15,5. Por eso la cintura de 53 cm parecía un error y no lo era: el dato faltante era el peso.',
        f'- **Presión arterial** ({len(pas_pad)} casos con una sola presión medida). Imputar la mediana',
        '  producía, por ejemplo, 120/126 mmHg (diastólica mayor que sistólica, imposible). Ahora la presión',
        '  que falta se estima desde la otra ± la presión de pulso mediana (45 mmHg): 171/126.',
        '- **Cintura** (75 faltantes): antes se imputaba 92,5 cm a todas; ahora se estima desde el IMC.',
        '',
        'Estos cambios se hicieron en la limpieza (`analisis/limpieza/reglas.py`, pasos 5 y 9) para que el',
        'conjunto de datos limpio sea reproducible. Casos corregidos:',
        '',
        _tabla(['Participante', 'Variable', 'Valor imputado', 'Contexto'],
               [(x.participante_id, V.etiqueta(x.variable), x.valor_imputado, x.contexto)
                for x in corr.itertuples()]),
        '',
        'Controles de coherencia sobre el conjunto limpio final:',
        '',
        _tabla(['Control', 'Por qué', 'Casos', 'Tratamiento'],
               [(x.control, x.por_que, x.casos, x.tratamiento) for x in coher.itertuples()]),
        '',
        '## 6. Correlación con la severidad',
        '',
        f'Se evaluaron **todas** las variables de la encuesta ({len(asoc)} pruebas) contra la severidad (0-3):',
        '',
        '- Variables ordinales, continuas y binarias → **correlación de Spearman** (rho). Un rho positivo',
        '  significa que a mayor valor de la variable, mayor severidad; uno negativo, menor severidad.',
        f'- Categóricas sin orden ({", ".join(V.etiqueta(v) for v in nominales["variable"])}) →',
        '  **Kruskal-Wallis**, con ε² como tamaño de efecto.',
        '- Los valores p se ajustan por comparaciones múltiples (Benjamini-Hochberg, FDR) sobre todas las',
        '  pruebas a la vez.',
        '- Las variables de rol **impacto** (rendimiento laboral, ausencias, relación de pareja,',
        '  antidepresivos) son **consecuencias** de los síntomas y no causas. Se informan, pero no son',
        '  candidatas a predictor.',
        '',
        *_figura(4, f'{FIG}/asociacion_severidad.png', 'Correlación de cada variable con la severidad',
                 'Todas las variables con prueba de Spearman (excepto las de impacto). En color, las significativas '
                 '(FDR < 0,05); en gris, las que no lo son.',
                 'cada barra es una variable y su largo es la correlación (rho) con la severidad. Una barra **roja '
                 'hacia la derecha** indica que a mayor valor de esa variable hay más severidad (por ejemplo, más '
                 'estrés laboral, más síntomas). Una barra **azul hacia la izquierda** indica que a mayor valor hay '
                 'menos severidad (por ejemplo, más días de ejercicio, menos síntomas). Una barra **gris** no es '
                 'significativa: esa relación podría deberse al azar.',
                 f'qué variables de toda la encuesta se relacionan con la severidad. Todas las barras son cortas '
                 f'(la mayor es {rho_max:.2f}, sobre un máximo posible de 1): son relaciones débiles.'),
        f'**{len(sig)} variables explicativas tienen correlación significativa** con la severidad:',
        '',
        _tabla(['Variable', 'Rol', 'n', 'rho', 'Dirección', 'p ajustado'],
               [(V.etiqueta(x.variable), x.rol, x.n, f'{x.efecto:+.2f}',
                 'más severidad' if x.efecto > 0 else 'menos severidad', _p(x.p_ajustado))
                for x in sig.reindex(sig['efecto'].abs().sort_values(ascending=False).index).itertuples()]),
        '',
        *_figura(5, f'{FIG}/matriz_significativas.png', 'Matriz de correlación de Spearman',
                 'Primera fila y columna: correlación de cada variable significativa con la severidad. El resto de '
                 'la matriz muestra cuánto se parecen entre sí (por ejemplo, el grupo de cuidado).',
                 'es una tabla de colores donde cada cuadro cruza dos variables. El rojo indica relación positiva, '
                 'el azul relación negativa y el blanco ausencia de relación; mientras más intenso el color, más '
                 'fuerte la relación. La diagonal es siempre roja porque es cada variable consigo misma.',
                 'en la primera fila y columna, la relación de cada variable con la severidad, que aparece en '
                 'colores suaves (relaciones débiles). En el resto del cuadro, cuánto se parecen las variables entre '
                 'sí: destacan los cuadros rojos intensos entre "Cuida a otras personas", "Cantidad de personas que '
                 'cuida" y "Sobrecarga" (0,93 a 0,96), que miden casi lo mismo, y entre IMC y cintura (0,92). En la '
                 'Fase 35 basta con conservar una variable de cada grupo.'),
        *(['Variables categóricas sin orden con diferencias significativas entre sus grupos (Kruskal-Wallis):', '',
            _tabla(['Variable', 'Rol', 'n', 'ε²', 'p ajustado'],
                   [(V.etiqueta(x.variable), x.rol, x.n, f'{x.efecto:.3f}', _p(x.p_ajustado))
                    for x in nom_sig.itertuples()]), ''] if len(nom_sig) else []),
        f'**Lectura.** Todas las correlaciones son **débiles** (la mayor es |rho| = {rho_max:.2f}). Por sí sola, ninguna variable',
        'explica la severidad; lo que se espera es que la **combinación** de varias (clústeres y reglas de',
        'asociación) describa perfiles. Las variables de cuidado están muy correlacionadas entre sí: en la',
        'Fase 35 se escogerá una por grupo. La **terapia hormonal** aparece asociada a más severidad, pero',
        'lo más probable es la causalidad inversa: se indica justamente a quienes tienen síntomas intensos.',
        '',
    ]
    if r['redundantes']:
        out += ['Pares muy correlacionados (|rho| ≥ 0,8) en la matriz completa:', '',
                _tabla(['Variable A', 'Variable B', 'rho'],
                       [(V.etiqueta(a), V.etiqueta(b), f'{v:+.2f}') for a, b, v in r['redundantes']]), '']
    out += [
        f'**Sin correlación significativa** ({len(no_sig)}): '
        + ', '.join(V.etiqueta(v) for v in no_sig['variable']) + '.',
        '',
        'Destaca que **alimentación y sustancias** (tabaco, alcohol, marihuana) no se asocian con la',
        'severidad en este conjunto de datos (sección 6.1).',
        '',
        f'Variables de impacto (consecuencias, rho de {impacto["efecto"].min():+.2f} a {impacto["efecto"].max():+.2f}):',
        'confirman que la severidad afecta el trabajo y la vida de pareja.',
        '',
        *_seccion_habitos(r['habitos'], asoc),
        '## 7. Dirección de las asociaciones',
        '',
        'Para que la dirección no quede ambigua, la Figura 6 muestra el valor medio de cada variable',
        'significativa en cada clase de severidad. Si la línea sube, las mujeres con síntomas más severos',
        'tienen valores más altos de esa variable.',
        '',
        *_figura(6, f'{FIG}/direccion.png', 'Media de cada variable según la clase de severidad',
                 'Barras: intervalo de confianza del 95 %. En las preguntas ordinales el eje muestra el código de '
                 'la respuesta (su significado está bajo cada eje).',
                 'hay un panel por variable. El eje horizontal muestra las cuatro clases de severidad, de "Muy leve" '
                 'a "Severa", y cada punto es el promedio de la variable en esa clase. Las barritas verticales son el '
                 'margen de error (intervalo de confianza del 95 %).',
                 f'si la línea **sube**, las mujeres con más síntomas tienen valores más altos de esa variable; por '
                 f'ejemplo, el IMC promedio pasa de {r["imc_clase"].iloc[0]:.1f} en "Muy leve" a '
                 f'{r["imc_clase"].iloc[-1]:.1f} en "Severa". Si la línea **baja**, ocurre lo contrario: "siente que '
                 'toman en serio sus síntomas" disminuye a medida que aumenta la severidad. Esta figura resuelve la '
                 'pregunta de la dirección de cada asociación.'),
        '### Días de ejercicio a la semana',
        '',
        'En la reunión esta variable quedó ambigua. Hay dos fuentes de confusión:',
        '',
        '1. **La variable no cuenta días.** Es una pregunta de alternativas con códigos 1 a 5: 1 = 0 días,',
        '   2 = 1-2 días, 3 = 3-4 días, 4 = 5-6 días, 5 = todos los días. El rho se calcula sobre ese orden.',
        f'2. **El signo es negativo** (rho = {fila_ej["efecto"]:+.2f}, p ajustado = {_p(fila_ej["p_ajustado"])}):',
        '   **a más días de ejercicio, menor severidad**. La Figura 7 lo muestra directamente.',
        '',
        f'La diferencia principal está entre **no hacer ejercicio** ({sev_0:.0f} % con síntomas severos) y',
        f'**hacerlo al menos un día** ({sev_resto:.0f} %). Entre quienes sí hacen ejercicio la tendencia no es',
        f'perfectamente pareja: el grupo de 5-6 días ({sev_56:.0f} % severas) es pequeño (n = {n_56}) y su',
        'porcentaje fluctúa más. Por eso conviene presentar el resultado como contraste "sin ejercicio vs.',
        'con ejercicio", más que como un efecto día a día.',
        '',
        *_figura(7, f'{FIG}/ejercicio_severidad.png', 'Severidad según los días de ejercicio a la semana',
                 'Cada barra suma 100 %. Las mujeres que no hacen ejercicio tienen la mayor proporción de síntomas '
                 'severos.',
                 'cada barra horizontal es un grupo según cuántos días hace ejercicio a la semana, y suma 100 %. Los '
                 'colores muestran qué parte de ese grupo está en cada clase de severidad; el azul más oscuro es '
                 '"Severa".',
                 f'las mujeres que **no hacen ejercicio** tienen la mayor parte en "Severa" ({sev_0:.0f} %, el '
                 'tramo azul oscuro más largo). En las que sí hacen ejercicio esa parte baja a '
                 f'{ej["Severa"].iloc[1:].min():.0f}-{ej["Severa"].iloc[1:].max():.0f} %. La diferencia principal está '
                 'entre hacer y no hacer ejercicio.'),
        _tabla(['Días de ejercicio', 'n', 'MRS medio'] + V.ORDEN_SEVERIDAD,
               [(i, int(f['n']), _f(f['mrs_medio'])) + tuple(f'{f[s]:.0f} %' for s in V.ORDEN_SEVERIDAD)
                for i, f in ej.iterrows()]),
        '',
        '**Cuidado al redactar:** el diseño es transversal (una sola medición), así que no se puede afirmar',
        'que el ejercicio *disminuya* los síntomas. También puede ocurrir al revés: las mujeres con síntomas',
        'severos (dolor, cansancio) hacen menos ejercicio. La redacción correcta es "las mujeres que se',
        'ejercitan más días presentan menor severidad".',
        '',
        '## 8. Qué pasa a la Fase 35',
        '',
        '- Conjunto de datos: `datos/analitico/conjunto_eda.csv` '
        f'({n_mrs} participantes, columna `severidad` 0-3).',
        '- Variable objetivo: `severidad`.',
        '- Candidatas a predictor: todas las de rol predictor y control (no solo las significativas).',
        '  La **selección por análisis entrópico** (entropía de Shannon y ganancia de información) decidirá',
        '  cuáles se quedan, y este EDA servirá para contrastar esa selección.',
        '- Las variables de impacto no entran como predictores.',
        '',
        '## 9. Limitaciones',
        '',
        '- Diseño transversal: las asociaciones no prueban causalidad.',
        '- El conjunto de datos es sintético: los resultados describen el conjunto, no la población real.',
        '- Los cortes de severidad (0-4 / 5-8 / 9-15 / 16+) y la definición de etapa menopáusica están',
        '  pendientes de validar con la profesora.',
        '- Las variables de laboratorio solo existen en el subgrupo profesional (n = 259), por eso tienen',
        '  menos poder estadístico.',
        '',
        '---',
        '',
        '## Anexo A. Figuras secundarias del EDA',
        '',
        'Estas figuras respaldan el análisis, pero no aportan al argumento central; por eso van en el anexo',
        'y no en el texto.',
        '',
        *_figura('A1', f'{FIG}/anexo/histogramas.png', 'Distribución de las variables continuas',
                 'Valores medidos (sin imputados). Va al anexo porque la Figura 3 ya resume lo relevante (centro, '
                 'dispersión y atípicos); los histogramas solo muestran además la forma de cada distribución.',
                 'un histograma por variable continua (edad, IMC, presión, laboratorio, etc.): cada barra es un rango '
                 'de valores y su altura es cuántas mujeres caen en él.',
                 'la forma de cada distribución. Por ejemplo, la glicemia se concentra en valores normales y tiene '
                 'una "cola" hacia valores altos, que es donde están sus atípicos.'),
        *_figura('A2', f'{FIG}/anexo/faltantes.png', 'Faltantes reales por variable',
                 'Va al anexo porque ninguna variable supera el 30 % y el tratamiento ya se explica en la sección 3; '
                 'la figura solo documenta el detalle.',
                 'cada barra es una pregunta y su largo es el porcentaje de respuestas que faltaban, contado solo entre '
                 'las mujeres a quienes se les mostró esa pregunta. La línea punteada marca el 5 %.',
                 'qué preguntas tenían más datos faltantes. Ninguna supera el 30 %, así que todas se pueden usar.'),
        *_figura('A3', f'{FIG}/anexo/matriz_completa.png', 'Matriz de Spearman completa',
                 f'Todas las variables de predictor, trabajo y control ({r["n_matriz"]}). Va al anexo porque la '
                 'mayoría de las correlaciones son cercanas a cero y no son legibles en el texto; la Figura 5 muestra '
                 'la parte relevante.',
                 'igual que la Figura 5, pero con todas las variables candidatas a predictor.',
                 'casi todo el cuadro es blanco o muy pálido: la mayoría de las variables no se relacionan entre '
                 'sí. Los únicos bloques intensos son el grupo de cuidado y los tipos de ejercicio entre sí.'),
        '',
        '## Anexo B. Random Forest como complemento (Fase 33)',
        '',
        'En la Fase 33 se estimó la importancia de las variables con Random Forest (regresión sobre el MRS',
        'total y clasificación severa/no severa). Por indicación de la profesora, la selección de variables',
        'se hará por **análisis entrópico** (Fase 35), y este análisis queda como **complemento**: sirve para',
        'contrastar si ambos métodos coinciden en las variables importantes. El detalle completo está en',
        '`analisis/informe_exploratorio.md`.',
        '',
        *_figura('B1', 'figuras/eda/importancia_general.png', 'Importancia de variables: modelo general',
                 'Caída del R² al permutar cada variable. En azul, las útiles en al menos 4 de 5 particiones.',
                 'cada barra es una variable y su largo indica cuánto empeora la predicción del MRS si esa variable '
                 'se desordena al azar: mientras más larga, más aporta. En azul, las que resultaron útiles en al menos '
                 '4 de las 5 pruebas.',
                 f'las variables que más aportan son {_top_rf()}, que coinciden en gran parte con el análisis de '
                 'correlación de la sección 6.'),
        *_figura('B2', 'figuras/eda/importancia_trabajadoras.png', 'Importancia de variables: trabajadoras',
                 'Mismo análisis en el subgrupo que trabaja (incluye estrés laboral y lugar de trabajo comprensivo).',
                 'igual que la Figura B1, solo con las mujeres que trabajan.',
                 'en este grupo las barras son aún más cortas: el modelo predice muy poco.'),
        *_rf_anexo(),
        'El poder predictivo del bosque es bajo, lo que es coherente con las correlaciones débiles de la',
        'sección 6.',
        '',
        '## Anexo C. Archivos generados',
        '',
        '- `resultados/asociacion_severidad.csv`: todas las pruebas de la sección 6.',
        '- `resultados/matriz_spearman.csv`: matriz completa (Figura A3).',
        '- `resultados/revision_atipicos.csv`: detección y decisión por variable (sección 4).',
        '- `resultados/coherencia.csv` y `resultados/correcciones_imputacion.csv`: sección 5.',
        '- `resultados/faltantes.csv`: sección 3.',
        '- `datos/analitico/conjunto_eda.csv`: conjunto de datos para la Fase 35 (no se versiona).',
        '',
    ]
    return '\n'.join(out)
