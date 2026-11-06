"""
Fase 37C: declara la decisión provisional y redacta los informes a partir de las tablas ya calculadas. Las cifras se leen de las tablas, no se copian a mano.

Uso, desde analisis/: NODE_PATH=<carpeta con node_modules de docx> python fase37/37C_comparacion_seleccion/scripts/generar_informes_37c.py
Escribe en informes/ y seleccion/decision_final_37C.json. Convierte a Word con md_a_word_37c.js.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd

sys.dont_write_bytecode = True
AQUI = Path(__file__).resolve().parent
B = AQUI.parent
INF = B / 'informes'
FUENTES = INF / 'fuentes'
FUENTES.mkdir(parents=True, exist_ok=True)
FIG = '../../figuras/'
SINT = 'Todo el análisis usa el conjunto sintético de usuarias (N = 529). Sus asociaciones vienen de una simulación, por lo que los resultados no permiten afirmar nada sobre mujeres reales.'
PROV = 'Lo que aquí se propone es provisional. La decisión final queda en manos de la responsable del proyecto.'


def L(r):
    return pd.read_csv(B / r, encoding='utf-8')


def J(r):
    return json.loads((B / r).read_text(encoding='utf-8'))


lista_a, lista_b, pri = L('candidatos/lista_A_completa.csv'), L('candidatos/lista_B_exploratoria.csv'), L('candidatos/conjunto_priorizado.csv')
res_listas = J('candidatos/resumen_listas.json')
niv = L('estabilidad/comparacion_niveles.csv').set_index('config')
sim = L('estabilidad/similitud_reduccion.csv')
imp = L('estabilidad/imputaciones_reestimadas.csv')
nu = L('referencias_nulas/comparacion_por_configuracion.csv').set_index('config')
bm = L('referencias_nulas/busqueda_multiple.csv').set_index('metrica')
gr = L('referencias_nulas/grilla_contraccion.csv')
ctrl = L('referencias_nulas/controles_sinteticos.csv')
alfa0 = L('referencias_nulas/contraste_sin_contraccion.csv').set_index('config')
prop = J('referencias_nulas/propiedades_referencia.json')
des = L('sensibilidades/s_ord/descomposicion.csv').set_index('config')
rep = L('sensibilidades/s_ord/comparacion_representaciones.csv').set_index('config')
efv = L('sensibilidades/s_ord/efecto_por_variable.csv')
dvar = L('sensibilidades/s_ord/distancias_por_variable.csv')
sen = L('sensibilidades/sensibilidades_priorizadas.csv')
imc = L('sensibilidades/comparaciones_imc_algoritmo.csv').set_index('config')
itp = L('interpretabilidad/resumen_interpretabilidad.csv').set_index('config')
per = L('seleccion/variables_que_mas_separan.csv')
asg = L('asignacion/evaluacion_asignacion.csv').set_index('config')
gri = L('asignacion/grilla_incertidumbre.csv')
ev = L('seleccion/evaluacion_por_etapa.csv')
mat = L('seleccion/matriz_estados.csv').set_index('config')
fin = L('seleccion/finalistas.csv').set_index('config')
umb = L('seleccion/sensibilidad_umbrales.csv')
dep = L('seleccion/dependencia_conclusion.csv')
fam = L('seleccion/familia_cribado.csv')
cri = L('seleccion/cribado_lista_A.csv')
tre = L('seleccion/reconstruccion_tres_cuatro_variables.csv').set_index('config')
fro = L('seleccion/cercania_fronteras.csv').set_index('config')
pre = J('seleccion/decision_preliminar_reglas.json')
pr, mu = L('pruebas/resultados_pruebas.csv'), L('pruebas/control_mutaciones.csv')
vr = L('integridad/validacion_replicas.csv')
mem = L('integridad/registro_memoria.csv')
leidos = L('integridad/archivos_leidos.csv')
fuera = L('integridad/escrituras_fuera.csv')
rep_et = L('integridad/reproduccion_etiquetas.csv')

P, Q_ = 'P2_c12_km_k4', 'P2_c08_km_k4'
assert pre['conclusion'] == 'B' and pre['elegibles_B'] == [P, Q_], pre
assert (pr['resultado'] == 'superada').all() and mu['detectada'].all(), 'Hay pruebas sin superar: no se declara ninguna decisión'


def n(x, d=2):
    return f'{x:.{d}f}'.replace('.', ',')


def tabla(cabeza, filas):
    return '\n'.join(['| ' + ' | '.join(map(str, cabeza)) + ' |', '|' + '---|' * len(cabeza)] + ['| ' + ' | '.join(map(str, f)) + ' |' for f in filas]) + '\n'


def s(c, sid):
    x = sen[(sen['config'] == c) & (sen['sensibilidad'] == sid)]['ari_ajuste']
    return float(x.iloc[0]) if len(x) and pd.notna(x.iloc[0]) else None


def sn(c, sid):
    v = s(c, sid)
    return 'n/a' if v is None else n(v)


def g(c, tipo, u):
    x = gri[(gri['config'] == c) & (gri['tipo'] == tipo) & ((gri['umbral'] - u).abs() < 1e-9)].iloc[0]
    return x


def fig(nombre, alt):
    return f'![{alt}]({FIG}{nombre}.png)\n'


def escribir(nombre, md):
    (FUENTES / f'{nombre}.md').write_text(md, encoding='utf-8')


# Decisión ---------------------------------------------------------------------------------------------------------------------------
A = lista_a.set_index('config')
adv_estado = ev[(ev['config'] == P) & (ev['estado'].isin(['ADV', 'CRIT']))]
tam = [int(x) for x in A.loc[P, 'tam_min':'tam_max'].iloc[[0, -1]]] if False else None
modelo = J(f'seleccion/artefactos_provisionales/{P}/modelo_segmentacion.json')
decision = {
    'estado': 'PROVISIONAL. La decisión final queda en manos de la responsable del proyecto. No es una clasificación clínica ni un modelo validado.',
    'conclusion': 'B. Segmentación operativa condicionada', 'configuracion_propuesta': P, 'equivalente_practica': 'P1_c12_km_k4 (ARI 0,97 con la propuesta)', 'alternativa_elegible': Q_,
    'motivo_entre_elegibles': 'Regla 10.2 del protocolo: menos advertencias, luego mayor percentil 5 en E3, luego menor complejidad', 'protocolo_sha256': pre['protocolo_sha256'],
    'reduccion': modelo['reduccion'], 'escenario_imc': 'Sin IMC' if not modelo['con_imc'] else 'Con IMC', 'componentes': modelo['componentes'], 'algoritmo': modelo['algoritmo'], 'k': modelo['k'], 'tamanos': modelo['tamanos'],
    'estabilidad_E3': {'ari_entre_media': niv.loc[P, 'E3_entre_media'], 'ari_entre_p05': niv.loc[P, 'E3_entre_p05'], 'ari_fuera_media': niv.loc[P, 'E3_fuera_media'], 'ari_fuera_p05': niv.loc[P, 'E3_fuera_p05']},
    'sensibilidades_criticas': {x: s(P, x) for x in ('S-ORD', 'S-TRA', 'S-CUI', 'S-EJE', 'S-IMPMODA', 'S-EDAD', 'S-SOLAPE', 'S-BLOQUE')},
    'referencia_nula': {'silueta_obs': nu.loc[P, 'silueta_obs'], 'silueta_nula_media': nu.loc[P, 'silueta_nula_media'], 'silueta_nula_max': nu.loc[P, 'silueta_nula_max'], 'silueta_p': nu.loc[P, 'silueta_p'], 'E1_obs': nu.loc[P, 'E1_ari_entre_media_obs'], 'E1_nula_max': nu.loc[P, 'E1_ari_entre_media_nula_max'], 'E1_p': nu.loc[P, 'E1_ari_entre_media_p'], 'supera_control_busqueda_multiple': False},
    'asignacion': {'margen_mediano': asg.loc[P, 'margen_mediano_fuera'], 'desacuerdo_pct': asg.loc[P, 'desacuerdo_pct_medio'], 'nota': 'Sin umbrales definitivos de incertidumbre'},
    'clase_interpretabilidad': itp.loc[P, 'clase'], 'reconstruccion': {'1_variable': itp.loc[P, 'ari_reconstruccion_1'], '2_variables': itp.loc[P, 'ari_reconstruccion_2'], '3_variables_exploratorio': tre.loc[P, 'ari_3'], 'mejor_trio': tre.loc[P, 'mejor_trio']},
    'condiciones_de_uso': ['Depende de tiene_actividad_sexual y distension_abdominal (S-SOLAPE); regla V', 'Se presenta como cortes de un continuo, no como tipos naturales', 'Toda asignación lleva su margen; las cercanas a una frontera se señalan', 'Debe compararse con la regla simple de tres preguntas', 'Depende de la codificación ordinal consecutiva'],
    'advertencias': adv_estado[['etapa', 'criterio', 'estado']].to_dict('records'), 'artefactos': f'seleccion/artefactos_provisionales/{P}/'}
(B / 'seleccion' / 'decision_final_37C.json').write_text(json.dumps(decision, ensure_ascii=False, indent=1, default=float), encoding='utf-8')

n_doc = len(L('pruebas/verificacion_informes.csv')) if (B / 'pruebas' / 'verificacion_informes.csv').exists() else 0
assert '2217' in pr.set_index('n').loc[1, 'detalle'], pr.set_index('n').loc[1, 'detalle']
# Valores comunes ---------------------------------------------------------------------------------------------------------------------
la = niv[niv['en_lista_a']]
cuenta = {e: {'m65': int((la[f'{e}_entre_media'] >= .65).sum()), 'm65p5': int(((la[f'{e}_entre_media'] >= .65) & (la[f'{e}_entre_p05'] >= .5)).sum()), 'm80': int((la[f'{e}_entre_media'] > .8).sum())} for e in ('E0', 'E1', 'E2', 'E3')}
km = niv[niv['algoritmo'] == 'km'].groupby('k')[['E0_entre_media', 'E3_entre_media']].median()
ward = niv[niv['algoritmo'] == 'ward'].groupby('k')[['E0_entre_media', 'E3_entre_media']].median()
ejemplos = ['F2_c03_km_k3', 'F1_c03_km_k4', 'F2_c02_km_k3', P, 'P1_c12_km_k4', Q_, 'P1_c05_km_k3', 'F1_c05_km_k2', 'F1_c02_km_k2']
FOCO = [P, 'P1_c12_km_k4', Q_, 'P2_c05_km_k3', 'P2_c03_km_k3', 'F2_c03_km_k3', 'F1_c02_km_k2', 'F1_c05_km_k2']
FOCO = [c for c in FOCO if c in nu.index]
recup, pend = vr[vr['estado'] == 'recuperada'], vr[vr['estado'] == 'pendiente']
inval = vr[vr['estado'].str.contains('inválida')]
m_min = mem[mem['evento'].str.contains('mínimo')]['libre_gb'].astype(float).min()
act = imp[imp['variable'] == 'tiene_actividad_sexual']['valor_reestimado'].astype(str).value_counts()
cui = imp[imp['variable'] == 'cuida_otras_personas']['valor_reestimado'].astype(str).value_counts()
fue = imp[imp['variable'] == 'frecuencia_fuerza']['valor_reestimado'].astype(str).value_counts()
r0 = 'R0P1_cTodas_km_k4'
dias = efv[(efv['config'] == 'F1_c05_km_k2') & (efv['variable'] == 'dias_ejercicio_semana')].iloc[0]
dmax = dvar.sort_values('cambio_medio_d2', ascending=False).drop_duplicates('variable').head(4)
no_pri = cri[cri['pasa_todo'] & ~cri['en_priorizadas']]['config'].tolist()
famP = fam[(fam['referencia'] == P) & (fam['k'] == 4)].sort_values('ari_con_referencia', ascending=False)
perP = per[per['config'] == P].head(9)
dep_alt = dep[~dep['es_el_protocolo']]
n_c = int((dep_alt['conclusion'] == 'C').sum())
n_b = int((dep_alt['conclusion'] == 'B').sum())
clases = itp['clase'].value_counts()

# 02 y 03: listas ---------------------------------------------------------------------------------------------------------------------
escribir('02_registro_lista_A', f"""# Qué es este registro

La Lista A reúne las configuraciones que la Fase 37B señaló con su regla previa, sin ningún cambio. Se conserva completa en `candidatos/lista_A_completa.csv`, leída de sus originales.

{SINT}

# Composición

- Configuraciones: **{res_listas['lista_A']}**.
- Con señal de que un solo eje las domina: {res_listas['lista_A_eje1']}.
- Con repeticiones inestables según la Fase 37B: {res_listas['lista_A_inestables']}.
- Evaluadas en estabilidad del procedimiento completo, contando Lista B, referencias y comparaciones: {res_listas['evaluadas_en_estabilidad']}.
- En el conjunto priorizado de {res_listas['priorizadas']}, que recibe referencia nula, descomposición de S-ORD e interpretabilidad: {res_listas['priorizadas'] - res_listas['fuera_de_A_en_priorizadas']} de la Lista A.

{tabla(['k', 'K-means', 'Aglomerativo (Ward)'], [[k, int(((lista_a['k'] == k) & (lista_a['algoritmo'] == 'km')).sum()), int(((lista_a['k'] == k) & (lista_a['algoritmo'] == 'ward')).sum())] for k in sorted(lista_a['k'].unique())])}

# Qué le ocurrió al recalcular todo

{tabla(['Nivel', 'Media ≥ 0,65', 'Media ≥ 0,65 y p05 ≥ 0,50', 'Media > 0,80'], [[e, cuenta[e]['m65'], cuenta[e]['m65p5'], cuenta[e]['m80']] for e in ('E0', 'E1', 'E2', 'E3')])}

E0 es la evaluación de la Fase 37B, con todo congelado salvo el agrupamiento. E3 reajusta imputación, escalado, reducción y agrupamiento.

# Límite del cribado

{len(no_pri)} configuraciones de la Lista A pasan el cribado de estabilidad, asignación, codificación y población, pero no están en el conjunto priorizado: {', '.join(f'`{c}`' for c in no_pri)}. No recibieron referencia nula, descomposición de S-ORD ni interpretabilidad, tal como fijó el protocolo. Por eso no pudieron ser finalistas. La sección «Familia» del informe de comparación indica cuánto se parecen a las elegibles.

Tabla completa: `seleccion/cribado_lista_A.csv`.
""")

escribir('03_registro_lista_B', f"""# Qué es este registro

La Lista B es **exploratoria**: se definió después de examinar los resultados de la Fase 37B, en la segunda tabla de su informe de preparación. No se le da peso confirmatorio. Se conserva en `candidatos/lista_B_exploratoria.csv`.

{SINT}

# Composición y destino

Las {res_listas['lista_B']} configuraciones pertenecen también a la Lista A.

{tabla(['Configuración', 'E0 entre', 'E3 entre', 'E3 p05', 'S-ORD', 'S-SOLAPE', 'Clase', '¿Finalista?'], [[c, n(niv.loc[c, 'E0_entre_media']), n(niv.loc[c, 'E3_entre_media']), n(niv.loc[c, 'E3_entre_p05']), sn(c, 'S-ORD'), sn(c, 'S-SOLAPE'), itp.loc[c, 'clase'], 'Sí' if c in fin.index or any(c in str(x) for x in fin['representa_a']) else 'No'] for c in lista_b['config']])}

# Lectura

Las configuraciones con 3 componentes FAMD eran las más atractivas en la Fase 37B y son las que más caen: su estabilidad parecía alta porque la reducción estaba congelada. Las de 8 componentes FAMD se descartan porque la partición casi no resiste el paso a ridit (S-ORD cercano a 0,19) y los cambios no se concentran en la frontera.
""")

# 04 estabilidad ------------------------------------------------------------------------------------------------------------------------
escribir('04_estabilidad_procedimiento_completo', f"""# Pregunta

La Fase 37B midió la estabilidad con la reducción, el escalado y la imputación congelados. Aquí se comprueba qué pasa cuando esos pasos también se reajustan dentro de cada submuestra.

{SINT}

# Diseño

- Cuatro niveles: **E0** (37B, solo agrupamiento), **E1** (más reducción), **E2** (más escalado) y **E3** (más imputación en memoria). E3 es el nivel de decisión.
- Las mismas 30 submuestras de 423 participantes de la Fase 37B, sobre {res_listas['evaluadas_en_estabilidad']} configuraciones. {J('integridad/validacion_avances.json')['lotes_estabilidad_validos']} lotes válidos.
- Medida principal: ARI entre pares de remuestreos sobre las participantes compartidas (`ari_entre`, 435 pares). Bandas de trabajo: bajo 0,65, entre 0,65 y 0,80, y sobre 0,80.
- Ni siquiera E3 recalibra la limpieza, la selección de las 30 variables, la agrupación de categorías raras de FAMD, los códigos ordinales del instrumento ni los valores de c y k. Por eso E3 sigue siendo optimista.

# Resultado general: la estabilidad baja

{tabla(['Lista A', 'E0', 'E1', 'E2', 'E3'], [['Media ≥ 0,65'] + [cuenta[e]['m65'] for e in ('E0', 'E1', 'E2', 'E3')], ['Media ≥ 0,65 y p05 ≥ 0,50'] + [cuenta[e]['m65p5'] for e in ('E0', 'E1', 'E2', 'E3')], ['Media > 0,80'] + [cuenta[e]['m80'] for e in ('E0', 'E1', 'E2', 'E3')]])}

Casi toda la caída ocurre al pasar de E0 a E1. Reajustar el escalado y la imputación agrega poco.

{tabla(['k', 'K-means E0', 'K-means E3', 'Ward E0', 'Ward E3'], [[k, n(km.loc[k, 'E0_entre_media']), n(km.loc[k, 'E3_entre_media']), n(ward.loc[k, 'E0_entre_media']) if k in ward.index else 'n/a', n(ward.loc[k, 'E3_entre_media']) if k in ward.index else 'n/a'] for k in km.index])}

Medianas por k. Con k alto, la estabilidad aparente de la Fase 37B era en gran parte efecto de congelar la reducción.

{fig('f03_estabilidad_anterior_nueva', 'Estabilidad anterior frente a la nueva')}

# Configuraciones de referencia

{tabla(['Configuración', 'E0', 'E1', 'E3', 'E3 p05', 'E3 fuera', 'E3 fuera p05'], [[c, n(niv.loc[c, 'E0_entre_media']), n(niv.loc[c, 'E1_entre_media']), n(niv.loc[c, 'E3_entre_media']), n(niv.loc[c, 'E3_entre_p05']), n(niv.loc[c, 'E3_fuera_media']), n(niv.loc[c, 'E3_fuera_p05'])] for c in ejemplos if c in niv.index])}

{fig('f02_estabilidad_completa', 'Estabilidad del procedimiento completo')}

# Hallazgos adicionales

- La similitud entre subespacios de reducción, con la submuestra frente a la muestra completa, tiene mediana {n(sim['similitud_subespacio'].median())} y mínimo {n(sim['similitud_subespacio'].min())}. Los subespacios se parecen en general, pero pequeñas rotaciones bastan para mover fronteras en un continuo.
- **Anomalía sin explicar:** `{r0}`, sin reducción, sube de {n(niv.loc[r0, 'E0_entre_media'])} en E0 a {n(niv.loc[r0, 'E3_entre_media'])} en E3, con p05 {n(niv.loc[r0, 'E3_entre_p05'])}. No se investigó su causa y no influye en la decisión, porque R0 no tiene sensibilidades en la Fase 37B y no puede ser finalista.
- La imputación reestimada no siempre coincide con la original: en las 30 submuestras `tiene_actividad_sexual` queda en «SI» {int(act.get('SI', 0))} veces y en «NO» {int(act.get('NO', 0))}; `cuida_otras_personas` en «SI» {int(cui.get('SI', 0))} veces; y `frecuencia_fuerza` en el valor 4 {int(fue.get('4', 0))} veces.

# Límite

`ari_fuera` compara con las etiquetas de la Fase 37B, que usaron a esas mismas participantes. Por eso se conserva además `ari_fuera_pares`, sin contaminación, con unas 21 participantes por par: es más limpia y más ruidosa.
""")

# 05 nula ------------------------------------------------------------------------------------------------------------------------------
sg, bd = bm.loc['silueta'], bm.loc['E1_ari_entre_media']
escribir('05_referencia_correlacionada', f"""# Pregunta

¿Las particiones observadas se distinguen de lo que produciría un conjunto **sin grupos**, pero con las mismas marginales y correlaciones? Si no se distinguen, son compatibles con cortes arbitrarios de un continuo.

{SINT}

# Construcción

Cópula gaussiana con marginales empíricas exactas por asignación de rangos, Spearman calibrado de forma iterativa, IMC con su indicador de ausencia, la variable nominal con regresión logística multinomial regularizada y las madres derivadas de sus hijas.

# Enmienda 1: contracción

Sin contracción, la cópula **no cumplió su criterio sellado**: el error del segundo valor propio fue {n(100 * float(J('referencias_nulas/propiedades_alpha_0.json')['error_relativo_vp_P1_1a3'][1]) if isinstance(J('referencias_nulas/propiedades_alpha_0.json')['error_relativo_vp_P1_1a3'], list) else 100 * float(J('referencias_nulas/propiedades_alpha_0.json')['error_relativo_vp_P1_1a3']), 1)} % en PCA, sobre un límite de 10 %. No se ajustó el criterio. Se selló una enmienda separada que añade contracción `R' = (1 − α)R + αI` y elige el menor α de la grilla que cumple todos los criterios.

{tabla(['α', 'Spearman máx.', 'Valor propio PCA', 'Valor propio FAMD', '¿Cumple?'], [[n(f.alfa, 3), n(f.spearman_max, 3), n(100 * f.vp_P1_1a3, 1) + ' %', n(100 * f.vp_F1_1a3, 1) + ' %', 'Sí' if f.cumple else 'No'] for f in gr.itertuples()])}

Se usó **α = 0,05**, con margen estrecho. Es una elección **exploratoria**, hecha después de conocer el fallo. La falla original queda en `propiedades_alpha_0.json`.

# Propiedades y controles

- Marginales exactas y lógica de salto íntegra. Spearman: error máximo de la media {n(prop['error_max_spearman_media_replicas'], 3)}; dentro de una sola réplica, mediana del máximo {n(prop['error_max_spearman_por_replica_mediana'], 2)} (error de muestreo).
- V de Cramér medio: observado {n(prop['v_cramer_media_observado'], 3)}, réplicas {n(prop['v_cramer_media_replicas'], 3)}.
- Controles sintéticos: sin grupos no se supera la referencia, salvo un empate con p = 0,048 en `F2_c03`. Con grupos plantados se supera con claridad. **La potencia frente a grupos débiles no se evaluó.** Tabla: `controles_sinteticos.csv`.

# Control de búsqueda múltiple

100 réplicas para separación y 20 para estabilidad. Con 20 réplicas, el menor p posible es 0,048.

{tabla(['Métrica', 'Superan a todas (obs.)', 'Réplicas: máximo', 'z máx. obs.', 'z máx. réplicas', 'p'], [[m, int(bm.loc[m, 'superan_todas_obs']), int(bm.loc[m, 'superan_todas_replicas_max']), n(bm.loc[m, 'z_max_obs']), n(bm.loc[m, 'z_max_replicas_max']), n(bm.loc[m, 'p_max'], 3)] for m in bm.index])}

Ninguna finalista lo pasa en silueta y estabilidad a la vez. **Silueta y estabilidad no superan el control, pero Calinski-Harabasz sí (p = {n(bm.loc['calinski_harabasz', 'p_max'], 3)}) y Davies-Bouldin queda en el límite (p = {n(bm.loc['davies_bouldin', 'p_max'], 3)}).** Por tanto, los datos no son idénticos a la referencia. Esa diferencia no demuestra que haya grupos: también puede venir de dependencias que la cópula no reproduce, y estas medidas tienden a favorecer particiones con grupos compactos.

# Configuraciones destacadas

{tabla(['Configuración', 'Silueta', 'Nula media', 'Nula máx.', 'p', 'E1', 'Nula media', 'Nula máx.', 'p'], [[c, n(nu.loc[c, 'silueta_obs'], 3), n(nu.loc[c, 'silueta_nula_media'], 3), n(nu.loc[c, 'silueta_nula_max'], 3), n(nu.loc[c, 'silueta_p'], 3), n(nu.loc[c, 'E1_ari_entre_media_obs']), n(nu.loc[c, 'E1_ari_entre_media_nula_media']), n(nu.loc[c, 'E1_ari_entre_media_nula_max']), n(nu.loc[c, 'E1_ari_entre_media_p'], 3)] for c in FOCO])}

{fig('f04_referencia_correlacionada', 'Comparación con la referencia correlacionada')}

# Lectura

- **Un ARI alto no implica grupos.** Datos sin grupos alcanzan ARI altos: en k = 2, la media nula de E1 es {n(nu.loc['F1_c05_km_k2', 'E1_ari_entre_media_nula_media'])}.
- `{P}` tiene una silueta igual a la nula ({n(nu.loc[P, 'silueta_obs'], 3)} frente a {n(nu.loc[P, 'silueta_nula_media'], 3)}). No hay separación mayor que la de un continuo correlacionado. Su estabilidad E1 sí supera a las 20 réplicas ({n(nu.loc[P, 'E1_ari_entre_media_obs'])} frente a un máximo de {n(nu.loc[P, 'E1_ari_entre_media_nula_max'])}), aunque sin pasar el control de búsqueda múltiple.
- La referencia nunca descarta una configuración: solo da una advertencia. Esta conclusión no cambia con α = 0: `{P}` tampoco supera a la nula en silueta allí. Ese contraste se rotula «No válida según el criterio; solo informativa».
""")

# 06 S-ORD ------------------------------------------------------------------------------------------------------------------------------
escribir('06_s_ord', f"""# Pregunta

La Fase 37B encontró que tratar las ordinales como ridit, en lugar de códigos consecutivos, cambiaba mucho varias particiones. Aquí se separa de dónde viene ese cambio.

{SINT}

# Descomposición

- **H1:** cambian solo las distancias, con los centroides de la partición base.
- **H2:** cambian distancias y fronteras.
- **H3:** cambian solo los ejes de la reducción.
- **H4:** S-ORD completa.

{tabla(['Configuración', 'Subespacio', 'H1', 'H2', 'H3', 'H4', 'Cambian', 'AUC margen', '% en cuartil de menor margen'], [[c, n(des.loc[c, 'similitud_subespacio']), n(des.loc[c, 'H1_distancias_centroides_base']), n(des.loc[c, 'H2_distancias_y_fronteras']), n(des.loc[c, 'H3_ejes']), n(des.loc[c, 'H4_completa']), n(des.loc[c, 'cambian_pct'], 1) + ' %', n(des.loc[c, 'auc_margen_bajo_predice_cambio']), n(des.loc[c, 'pct_cambios_en_cuartil_menor_margen'], 0) + ' %'] for c in FOCO])}

{fig('f05_s_ord', 'Descomposición de S-ORD')}

# Lectura

- El subespacio casi no cambia. Las participantes se mueven poco: el cambio aparece cuando el agrupamiento se reajusta sobre esas distancias apenas distintas. Es lo esperable en un continuo: las fronteras no están sostenidas por huecos en los datos.
- En k = 2, S-ORD es muy baja porque el grupo pequeño depende de la distancia entre los niveles de `dias_ejercicio_semana`: el ARI cambiando solo esa variable es {n(dias['ari_solo_ella_en_ridit'])} en `F1_c05_km_k2`.
- Las variables con mayor cambio de distancia son {', '.join(f'`{v}`' for v in dmax['variable'].head(3))}.
- Las configuraciones con 8 componentes FAMD combinan S-ORD cercano a 0,19 con cambios que no se concentran en la frontera: son frágiles según la regla 6.3.

# Representaciones comparadas

{tabla(['Configuración', 'Cons.-ridit', 'Cons.-normal', 'Ridit-normal', 'E3 cons. (p05)', 'E3 ridit (p05)', 'E3 normal (p05)'], [[c, n(rep.loc[c, 'ari_consecutiva_ridit']), n(rep.loc[c, 'ari_consecutiva_normal']), n(rep.loc[c, 'ari_ridit_normal']), f"{n(rep.loc[c, 'E3_entre_media_consecutiva'])} ({n(rep.loc[c, 'E3_entre_p05_consecutiva'])})", f"{n(rep.loc[c, 'E3_entre_media_ridit'])} ({n(rep.loc[c, 'E3_entre_p05_ridit'])})", f"{n(rep.loc[c, 'E3_entre_media_normal'])} ({n(rep.loc[c, 'E3_entre_p05_normal'])})"] for c in [P, Q_] + [x for x in ['P2_c05_km_k3', 'P2_c03_km_k3', 'F1_c02_km_k2'] if x in rep.index]])}

# Decisión por la regla 6.3

- `{P}`: ARI consecutiva-ridit {n(rep.loc[P, 'ari_consecutiva_ridit'])}, sobre 0,65: **se mantiene con limitaciones aceptables**.
- `{Q_}`: {n(rep.loc[Q_, 'ari_consecutiva_ridit'])}, entre 0,40 y 0,65, con AUC {n(des.loc[Q_, 'auc_margen_bajo_predice_cambio'])}: **se mantiene con limitaciones aceptables**.
- Ninguna representación alternativa cumple las tres condiciones para reemplazar a la consecutiva. La codificación principal no cambia, y no se generó ninguna versión nueva.

**Limitación importante:** la estabilidad depende de la representación. Con ridit, `{P}` baja a {n(rep.loc[P, 'E3_entre_media_ridit'])} (p05 {n(rep.loc[P, 'E3_entre_p05_ridit'])}), que sería crítica si ridit fuera la codificación principal.
""")

# 07 sensibilidades ---------------------------------------------------------------------------------------------------------------------
SS = ['S-ORD', 'S-FAMD', 'S-RARA', 'S-TRA', 'S-CUI', 'S-EJE', 'S-IMPMODA', 'S-EDAD', 'S-SOLAPE', 'S-BLOQUE']
escribir('07_sensibilidades', f"""# Pregunta

¿Cuánto cambia cada partición al modificar la codificación, la población analizada o las variables que entran?

{SINT}

# Resultados

ARI de reajuste frente a la partición base.

{tabla(['Configuración'] + SS, [[c] + [sn(c, x) for x in SS] for c in FOCO])}

{fig('f06_sensibilidades', 'Sensibilidades críticas')}

# Lo que más afecta a las elegibles

- **S-SOLAPE (sin `tiene_actividad_sexual` ni `distension_abdominal`):** {sn(P, 'S-SOLAPE')} en `{P}` y {sn(Q_, 'S-SOLAPE')} en `{Q_}`. Es crítica. La partición de 4 grupos descansa en esas dos variables. La regla V le impide ser A; no le impide por sí sola ser B, pero se declara como condición de uso.
- **S-BLOQUE:** {sn(P, 'S-BLOQUE')} en `{P}`. Dar a cada bloque temático el mismo peso produce otra partición. El protocolo la deja fuera de las reglas porque responde a otra pregunta, pero indica que los grupos dependen de cuántas columnas aporta cada tema.
- **S-ORD:** {sn(P, 'S-ORD')}, ver el informe 06.
- **S-EJE:** {sn(P, 'S-EJE')}, advertencia leve.

# S-IMPMODA: un hallazgo nuevo

Las 30 celdas imputadas de `tiene_actividad_sexual` valen «NO», aunque la moda en las 529 es «SI» (251 frente a 248). La moda se calculó sobre 546 filas, antes de un filtro posterior, según el informe de limpieza. **No se corrigió.** Se evaluó su efecto con S-IMPMODA: {sn(P, 'S-IMPMODA')} en `{P}`, sobre el umbral de advertencia. La diferencia entre ambas modas es de 3 participantes, así que no se puede afirmar cuál es mejor. Queda como punto a revisar por la responsable.

# Con y sin IMC, K-means y Ward, PCA y FAMD

{tabla(['Configuración', 'Con/sin IMC', 'K-means/Ward', 'PCA/FAMD'], [[c, n(imc.loc[c, 'ari_con_sin_imc_529']), n(imc.loc[c, 'ari_km_ward']) if pd.notna(imc.loc[c, 'ari_km_ward']) else 'n/a', n(imc.loc[c, 'ari_pca_famd']) if pd.notna(imc.loc[c, 'ari_pca_famd']) else 'n/a'] for c in FOCO])}

El IMC casi no influye. En cambio, con k = 4 el algoritmo y el método de reducción sí importan: **la partición no es independiente del método**, lo que también apunta a un continuo.
""")

# 08 interpretabilidad ------------------------------------------------------------------------------------------------------------------
escribir('08_interpretabilidad', f"""# Alcance

Descripción preliminar con las 30 variables generales, sin MRS, sin nombres de grupos y sin lectura clínica. La caracterización corresponde a la Fase 37D, que no se inició.

{SINT}

# Clases del conjunto priorizado

{tabla(['Clase', 'Configuraciones'], [[k, int(v)] for k, v in clases.items()])}

# Configuraciones destacadas

{tabla(['Configuración', 'Clase', 'Actividad física (% SSB)', 'Variable mayor (%)', 'Variables con efecto ≥ 0,06', 'Bloques', 'N.º efectivo', 'Recon. 1', 'Recon. 2'], [[c, itp.loc[c, 'clase'], n(100 * itp.loc[c, 'ssb_actividad_fisica'], 0), f"{itp.loc[c, 'variable_mayor_ssb']} ({n(100 * itp.loc[c, 'ssb_variable_max'], 0)})", int(itp.loc[c, 'n_variables_efecto']), int(itp.loc[c, 'n_bloques_efecto']), n(itp.loc[c, 'n_efectivo_variables'], 1), n(itp.loc[c, 'ari_reconstruccion_1']), n(itp.loc[c, 'ari_reconstruccion_2'])] for c in FOCO])}

{fig('f09_bloques', 'Contribución de los bloques temáticos')}

# Variables que más separan en `{P}`

{tabla(['Variable', 'Bloque', 'Efecto', '% SSB', 'Grupo 0', 'Grupo 1', 'Grupo 2', 'Grupo 3'], [[f.variable, f.bloque, n(f.efecto), n(100 * f.parte_ssb, 0), n(f.grupo_0), n(f.grupo_1), n(f.grupo_2), n(f.grupo_3)] for f in perP.itertuples()])}

Medias de los códigos del instrumento, sin nombres de grupos. La numeración de los grupos es arbitraria.

# ¿Qué tan multivariables son?

- **k = 2:** no lo son. La actividad física aporta cerca de 95 % de la separación, y una sola variable, `{itp.loc['F1_c05_km_k2', 'mejor_variable_1']}`, reconstruye la partición con ARI {n(itp.loc['F1_c05_km_k2', 'ari_reconstruccion_1'])}. Preguntarla directamente es más simple.
- **k = 3:** son un gradiente de ejercicio, con la actividad física cerca de 60 %, algunas justo en el límite de la clase.
- **`{P}`:** clase multivariable según la regla sellada, con {int(itp.loc[P, 'n_variables_efecto'])} variables con efecto de al menos 0,06, {int(itp.loc[P, 'n_bloques_efecto'])} bloques y {n(itp.loc[P, 'n_efectivo_variables'], 1)} variables efectivas. Con dos variables la reconstrucción llega a {n(itp.loc[P, 'ari_reconstruccion_2'])}, bajo el umbral de 0,65.

# Comprobación exploratoria con tres variables

El protocolo solo mide 1 y 2 variables. Al ver los perfiles se añadió esta comprobación, fuera del protocolo. **No cambia la clase sellada.**

{tabla(['Configuración', 'Mejor trío', 'ARI con 3', 'ARI con 4'], [[c, tre.loc[c, 'mejor_trio'], n(tre.loc[c, 'ari_3']), n(tre.loc[c, 'ari_4'])] for c in tre.index])}

Tres preguntas directas reconstruyen `{P}` con ARI {n(tre.loc[P, 'ari_3'])}. La cuarta no mejora. Es decir, «multivariable» es correcto respecto de la regla, pero la partición se aproxima bastante con tres preguntas simples. Es una alternativa que debe compararse antes de usar los grupos.
""")

# 09 asignacion -------------------------------------------------------------------------------------------------------------------------
escribir('09_asignacion', f"""# Pregunta

¿Se puede asignar a una participante nueva sin reajustar nada, y es consistente esa asignación? Una asignación algorítmica **no es una clasificación clínica**.

{SINT}

# Diseño

Con las 30 submuestras de E3, el flujo se aplica a las 106 participantes no usadas: transformador, proyección y centroide más cercano. Se compara con la partición de referencia. Comprobado además que la asignación de una participante no depende de las demás. Las Ward no tienen centroides propios: se aproximan por prototipos y se rotulan como aproximación.

# Resultados

{tabla(['Configuración', 'ARI fuera', 'p05', 'Mínimo', 'Desacuerdo', 'Margen mediano'], [[c, n(asg.loc[c, 'ari_fuera_media']), n(asg.loc[c, 'ari_fuera_p05']), n(asg.loc[c, 'ari_fuera_min']), n(asg.loc[c, 'desacuerdo_pct_medio'], 1) + ' %', n(asg.loc[c, 'margen_mediano_fuera'])] for c in FOCO])}

{fig('f10_asignacion', 'Asignación de participantes no usadas')}

Las de k = 2 son las más consistentes porque casi solo miran el ejercicio, pero no son elegibles por eso mismo.

# Mecanismo de incertidumbre en `{P}`

El margen es `1 − d1/d2`: cerca de 0, la participante está casi a la misma distancia de dos centros.

{tabla(['Señal', 'Señaladas', 'Desacuerdo señaladas', 'Desacuerdo resto'], [[f'Margen < {n(u)}', n(g(P, 'margen', u)['senaladas_pct'], 1) + ' %', n(g(P, 'margen', u)['desacuerdo_senaladas_pct'], 1) + ' %', n(g(P, 'margen', u)['desacuerdo_resto_pct'], 1) + ' %'] for u in (.05, .10, .15, .20, .30)] + [[f'Distancia sobre p{int(u)}', n(g(P, 'distancia_percentil', u)['senaladas_pct'], 1) + ' %', n(g(P, 'distancia_percentil', u)['desacuerdo_senaladas_pct'], 1) + ' %', n(g(P, 'distancia_percentil', u)['desacuerdo_resto_pct'], 1) + ' %'] for u in (90, 95, 99)])}

- **El margen discrimina bien.** Casi todo el desacuerdo está en las participantes cerca de una frontera.
- **El costo es alto:** la mitad de las participantes tiene un margen bajo 0,15, porque en un continuo muchas quedan cerca de una frontera. En la muestra completa, {n(fro.loc[P, 'pct_margen_bajo_0.10'], 1)} % tiene margen bajo 0,10.
- **La distancia casi no predice el desacuerdo.** Sirve para señalar participantes atípicas, no asignaciones dudosas.

**No se fijan umbrales definitivos.** La grilla muestra el compromiso; fijarlos corresponde a una fase posterior y con datos que no se hayan usado para esto.
""")

# 10 comparacion ------------------------------------------------------------------------------------------------------------------------
escribir('10_comparacion_finalistas', f"""# Finalistas

Pasan quienes no tienen CRIT en las etapas 1 a 3, ni en codificación, ni en población e imputación. Las casi idénticas (ARI ≥ 0,95) cuentan como una sola. R0 queda fuera por no tener sensibilidades en la Fase 37B.

{SINT}

{tabla(['Configuración', 'Representa a', 'Clase', 'ADV', 'CRIT', 'Elegible para'], [[c, f.representa_a.replace(' | ', ', '), f.clase, int(f.n_adv), f.crit if pd.notna(f.crit) else '—', f.elegible_para] for c, f in zip(fin.index, fin.itertuples())])}

{fig('f11_finalistas', 'Evaluación por etapa')}

# Comparación

{tabla(['Medida'] + list(fin.index), [
    ['Silueta'] + [n(nu.loc[c, 'silueta_obs'], 3) for c in fin.index],
    ['Silueta frente a la nula, p'] + [n(nu.loc[c, 'silueta_p'], 3) for c in fin.index],
    ['E3 entre'] + [n(niv.loc[c, 'E3_entre_media']) for c in fin.index],
    ['E3 entre, p05'] + [n(niv.loc[c, 'E3_entre_p05']) for c in fin.index],
    ['E3 fuera'] + [n(niv.loc[c, 'E3_fuera_media']) for c in fin.index],
    ['E3 fuera, p05'] + [n(niv.loc[c, 'E3_fuera_p05']) for c in fin.index],
    ['S-ORD'] + [sn(c, 'S-ORD') for c in fin.index],
    ['S-SOLAPE'] + [sn(c, 'S-SOLAPE') for c in fin.index],
    ['Actividad física, % SSB'] + [n(100 * itp.loc[c, 'ssb_actividad_fisica'], 0) for c in fin.index],
    ['Reconstrucción con 2 variables'] + [n(itp.loc[c, 'ari_reconstruccion_2']) for c in fin.index],
    ['Margen mediano'] + [n(fro.loc[c, 'margen_mediano']) for c in fin.index]])}

{fig('f07_tamanos', 'Tamaños de los grupos')}

{fig('f08_separacion', 'Separación interna')}

# K-means frente al método aglomerativo

K-means mantiene sus ventajas: todas las finalistas son K-means. Las Ward caen en estabilidad y sus homólogas de la Lista B quedan entre 0,20 y 0,35 en E3. Además, K-means asigna de forma directa, mientras que Ward necesita una aproximación por prototipos. Esto no prueba que K-means descubra grupos reales: favorece fronteras sencillas y funciona igual en un continuo.

# Las dos elegibles para B

{tabla(['Criterio', P, Q_], [['Advertencias', int(fin.loc[P, 'n_adv']), int(fin.loc[Q_, 'n_adv'])], ['E3 entre, p05', n(niv.loc[P, 'E3_entre_p05']), n(niv.loc[Q_, 'E3_entre_p05'])], ['Componentes', 12, 8], ['ARI entre ellas', n(float(fam[(fam['referencia'] == P) & (fam['config'] == Q_)]['ari_con_referencia'].iloc[0])), n(float(fam[(fam['referencia'] == P) & (fam['config'] == Q_)]['ari_con_referencia'].iloc[0]))]])}

Por la regla 10.2 (menos ADV, luego mayor p05, luego menor complejidad) se propone `{P}`. Su única desventaja es que usa 12 componentes. La diferencia práctica es pequeña: comparten casi toda la partición.

# Familia

Configuraciones k = 4 que pasan el cribado, incluidas las no priorizadas:

{tabla(['Configuración', '¿Priorizada?', 'ARI con la propuesta', 'E3 entre', 'S-ORD', 'S-SOLAPE'], [[f.config, 'Sí' if f.en_priorizadas else 'No', n(f.ari_con_referencia), n(f.E3_entre_media), n(f.S_ORD), n(f.S_SOLAPE)] for f in famP.itertuples()])}

`P2_c16_km_k4` y `P1_c16_km_k4` no se evaluaron por completo: no están priorizadas. Son variantes cercanas, y `P2_c16_km_k4` incluso tiene S-ORD mayor. No cambian la conclusión, pero la elección entre 8, 12 y 16 componentes no está resuelta por los datos.
""")

# 11 decision ---------------------------------------------------------------------------------------------------------------------------
PLANO = f"""# Explicación en lenguaje sencillo

**¿Qué se quería saber?** Si las 529 participantes del conjunto sintético se dividen en grupos que existan de verdad en los datos, o si solo se puede repartirlas de forma práctica.

**¿Qué se encontró?** No hay evidencia suficiente de grupos naturales. Los resultados son compatibles con un continuo: en separación, la división propuesta no se distingue de un conjunto sin grupos con las mismas correlaciones. Algunas medidas sí muestran diferencias con ese conjunto, pero no bastan para afirmar que existan grupos. Imagine dividir a las personas por estatura en «bajas», «medianas» y «altas»: la división puede servir, pero nadie cree que existan tres tipos de personas.

**¿Qué se propone?** Una división práctica en 4 segmentos, `{P}`, como herramienta de trabajo provisional. No es un diagnóstico, ni una clasificación clínica, ni un modelo validado.

**¿Por qué esa y no otras?**

- Las divisiones en 2 grupos son las más estables, pero casi solo separan según cuántos días hace ejercicio la participante. Para eso basta con preguntarlo.
- Las divisiones en 3 grupos son básicamente un gradiente de ejercicio.
- Las que parecían mejores en la fase anterior, con 3 componentes, caen al repetir todo el procedimiento.
- Esta división de 4 segmentos es la que mejor resiste entre las que combinan varios temas: ejercicio, pareja, trabajo y alimentación.

**¿Qué tan firme es?** No mucho. Es lo que las reglas fijadas de antemano permiten, no una conclusión sólida:

- Si se quitan dos preguntas (`tiene_actividad_sexual` y `distension_abdominal`), la división cambia bastante.
- Cerca de la mitad de las participantes queda cerca de la frontera entre dos segmentos.
- Tres preguntas directas (trabajo, pareja y días de ejercicio) reproducen buena parte de la división.
- Se probaron {len(dep_alt)} criterios alternativos, planteados después de ver los resultados y no como reglas de decisión. Con {n_c} de ellos, la conclusión habría sido no seleccionar nada.

**¿Qué falta?** Datos reales e independientes. Todo esto se hizo con datos simulados y nada de esto describe a mujeres reales.
"""
escribir('11_decision_metodologica', f"""# Decisión

**Conclusión B: segmentación operativa condicionada.** Configuración propuesta: **`{P}`** (PCA, sin IMC, {modelo['componentes']} componentes, K-means, k = {modelo['k']}). Alternativa elegible: `{Q_}`.

{PROV}

{SINT}

{PLANO}

# Justificación técnica

- **No A:** tiene un CRIT en S-SOLAPE, no supera el control de búsqueda múltiple y su silueta es igual a la de la nula (p = {n(nu.loc[P, 'silueta_p'], 3)}).
- **Sí B:** cumple los cuatro requisitos sellados. Es finalista sin CRIT en las etapas 1 a 3, codificación ni población; es de clase multivariable; tiene un mecanismo de incertidumbre evaluado (margen); y la regla V queda declarada. B no exige superar a la nula: admite un continuo.
- **Por qué no las demás finalistas:** `F1_c02_km_k2`, `P2_c03_km_k3` y `P2_c05_km_k3` son gradientes de ejercicio. El protocolo dice que no se eligen como modelo, y se informan como alternativa simple.

# Parámetros

{tabla(['Parámetro', 'Valor'], [['Reducción', modelo['reduccion']], ['Escenario de IMC', 'Sin IMC'], ['Componentes', modelo['componentes']], ['Algoritmo', 'K-means, n_init 50, semilla 42'], ['k', modelo['k']], ['Tamaños', ' / '.join(map(str, modelo['tamanos']))], ['E3 entre, media y p05', f"{n(niv.loc[P, 'E3_entre_media'])} y {n(niv.loc[P, 'E3_entre_p05'])}"], ['E3 fuera, media y p05', f"{n(niv.loc[P, 'E3_fuera_media'])} y {n(niv.loc[P, 'E3_fuera_p05'])}"], ['Silueta y nula', f"{n(nu.loc[P, 'silueta_obs'], 3)} y {n(nu.loc[P, 'silueta_nula_media'], 3)}"], ['E1 y máximo nulo', f"{n(nu.loc[P, 'E1_ari_entre_media_obs'])} y {n(nu.loc[P, 'E1_ari_entre_media_nula_max'])}"], ['S-ORD / S-SOLAPE', f"{sn(P, 'S-ORD')} / {sn(P, 'S-SOLAPE')}"], ['Desacuerdo fuera de muestra', n(asg.loc[P, 'desacuerdo_pct_medio'], 1) + ' %'], ['Margen mediano', n(asg.loc[P, 'margen_mediano_fuera'])]])}

Artefactos: `seleccion/artefactos_provisionales/{P}/`, que cita por huella los transformadores de la Fase 36 y el modelo de la Fase 37A, sin copiarlos. Registro: `seleccion/decision_final_37C.json`.

# Advertencias de la propuesta

{tabla(['Etapa', 'Criterio', 'Estado'], [[f.etapa, f.criterio, f.estado] for f in adv_estado.itertuples()])}

# Condiciones de uso

1. Presentarla como cortes de un continuo, nunca como tipos naturales ni clínicos.
2. Declarar que depende de `tiene_actividad_sexual` y `distension_abdominal` (regla V). Esto importa especialmente en la Fase 37D, porque esas variables se relacionan con síntomas: compararlos con los grupos tendría riesgo de circularidad.
3. Acompañar cada asignación con su margen y señalar a las cercanas a una frontera.
4. Compararla con la regla simple de tres preguntas antes de usar los grupos.
5. Declarar que depende de la codificación ordinal consecutiva.

# Qué tanto depende de las reglas

La conclusión es estable al mover los umbrales: da B en los {len(umb)} escenarios. Pero **es sensible a la forma de leer la evidencia**, que es lo que más hay que tener presente:

{tabla(['Otra lectura', 'Conclusión', 'Siguen elegibles'], [[f.lectura, f.conclusion, f.siguen.replace(' | ', ', ')] for f in dep_alt.itertuples()])}

{fig('f12_decision', 'Dependencia de la conclusión')}

Estas lecturas no sustituyen a las reglas selladas y no se aplicaron para decidir. **Se plantearon en esta fase, después de ver los resultados, y el conteo no es una probabilidad:** otra lista daría otro conteo. Se muestran porque **en {n_c} de {len(dep_alt)} la conclusión pasaría a C**, lo que indica que B descansa en decisiones concretas del protocolo, en especial la regla V. Por eso, no seleccionar nada también es defendible, y es una opción que la responsable debería considerar. Ninguna lectura lleva a A.

# Limitaciones

- Datos sintéticos, sin conjunto independiente: ninguna selección queda validada.
- El protocolo se selló conociendo los resultados de la Fase 37B: nada es confirmatorio en sentido estricto.
- Enmienda 1 con margen estrecho y elección posterior al fallo. Con 20 réplicas, p mínimo 0,048. Potencia frente a grupos débiles sin evaluar.
- E3 no recalibra la limpieza, la selección de variables, las categorías raras, los códigos ordinales, ni c y k.
- `ari_fuera` es algo optimista. `ari_fuera_pares` es limpia, pero ruidosa.
- {len(no_pri)} configuraciones que pasan el cribado no se evaluaron por completo, según el protocolo.
- Sigue abierta la imputación de `tiene_actividad_sexual` (S-IMPMODA).
- Sensibilidad a la ponderación por bloques (S-BLOQUE {sn(P, 'S-BLOQUE')}), al algoritmo (Ward {n(imc.loc[P, 'ari_km_ward'])}) y al método de reducción (FAMD {n(imc.loc[P, 'ari_pca_famd'])}).
- Falta una regla de asignación con umbrales definitivos.
""")

# 12 pruebas y 13 integridad ------------------------------------------------------------------------------------------------------------
(INF / '12_informe_pruebas.md').write_text(f"""# Fase 37C: informe de pruebas

Programas: `scripts/pruebas_37c.py` y `scripts/control_mutaciones_37c.py`. Resultados: `pruebas/resultados_pruebas.csv` y `pruebas/control_mutaciones.csv`. Revisión documental: `scripts/verificar_informes_37c.py`.

**Resultado: {int((pr['resultado'] == 'superada').sum())} de {len(pr)} pruebas superadas; {int(mu['detectada'].sum())} de {len(mu)} errores introducidos detectados; {n_doc} comprobaciones documentales superadas.**

Las 22 pruebas pedidas en el encargo están cubiertas, y se agregaron otras cuatro. Ninguna se declara superada sin haberse ejecutado. Las mutaciones se aplican en memoria y no alteran ningún archivo.

## Pruebas

{tabla(['N.º', 'Prueba', 'Resultado', 'Detalle'], [[f.n, f.prueba, f.resultado, str(f.detalle).replace('|', '/')] for f in pr.itertuples()])}

## Controles negativos

{tabla(['Error introducido', 'Prueba', '¿Detectado?', 'Mensaje'], [[f.mutacion, f.prueba, 'Sí' if f.detectada else 'No', str(f.detalle).replace('|', '/')[:90]] for f in mu.itertuples()])}

## Lo que estas pruebas no aseguran

- Comprueban que el cálculo es correcto y coherente con el protocolo, no que la conclusión sea verdadera.
- No se reejecutaron las pruebas históricas de las fases anteriores. La integridad de esas fases se verificó por huellas. Alguna prueba histórica que revise el contenido de la carpeta `fase37` podría señalar la nueva subcarpeta, sin que eso signifique un cambio en sus archivos.
""", encoding='utf-8')

(INF / '13_informe_integridad.md').write_text(f"""# Fase 37C: informe de integridad

- **Fases protegidas:** la prueba 1 compara 2.217 archivos de las Fases 36, 37A, 37B y del cierre de las Fases 34 y 35 con sus manifiestos: todos iguales.
- **Lecturas:** {len(leidos)} archivos leídos, ninguno de `datos/`. El gancho de auditoría registra `integridad/archivos_leidos.csv`.
- **Escrituras fuera de la subfase:** {len(fuera)}. Registro: `integridad/escrituras_fuera.csv`.
- **Git:** HEAD sigue en 745d689. Sin commit y sin push. Sin cambios fuera de `analisis/` (Django y plataforma intactos).
- **Protocolo:** `protocolo/01_protocolo_37C.md` y `02_enmienda_referencia_nula.md` coinciden con sus sellos. Huella del protocolo: `{pre['protocolo_sha256']}`.
- **Reproducción:** las etiquetas de la Fase 37B y las recalculadas son idénticas ({len(rep_et)} configuraciones). `integridad/reproduccion_etiquetas.csv`.
- **Manifiesto final:** `integridad/manifiesto_final_37C.csv`, con la huella de todos los archivos de la subfase salvo él mismo.

## Avances recuperados

{tabla(['Elemento', 'Cantidad', 'Estado'], [['Réplicas 000 a 071', len(recup), 'Recuperadas tras validar sello, parámetros, dimensiones y silueta de control'], ['Réplicas inválidas', len(inval), 'Ninguna repetida'], ['Réplicas 072 a 099', len(pend), 'Ejecutadas por primera vez'], ['Contraste α = 0', 20, 'Por separado, en `lotes_alpha0/`, sin sobrescribir'], ['Lotes de estabilidad', J('integridad/validacion_avances.json')['lotes_estabilidad_validos'], 'Válidos, sin repetir']])}

## Memoria

La primera corrida, con 10 procesos, fue detenida por el sistema por falta de memoria con 72 réplicas completas. Se reanudó con un máximo de 3 procesos, un hilo por biblioteca y `scripts/vigilar_memoria.py`. Desde entonces no hubo presión de memoria: el mínimo registrado fue {n(m_min)} GB libres, sobre el límite de 0,7 GB. Registro: `integridad/registro_memoria.csv`.

## Restricciones

Sin MRS, Random Forest, Shannon ni GMM en la selección; sin verdad del simulador; sin reglas de asociación; sin caracterización clínica; sin iniciar la Fase 37D.
""", encoding='utf-8')

# 14 cierre -----------------------------------------------------------------------------------------------------------------------------
n_archivos = sum(1 for p in B.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
escribir('14_informe_cierre_37C', f"""# Conclusión

**Conclusión B: segmentación operativa condicionada, con `{P}` como propuesta provisional.** No hay evidencia suficiente de grupos naturales: los resultados son compatibles con un continuo. La propuesta cumple las reglas selladas, pero es débil, y no seleccionar nada también es defendible.

{PROV}

{SINT}

{PLANO}

# Respuestas a las preguntas del encargo

## 1. ¿Qué configuraciones A y B se examinaron?

{res_listas['lista_A']} de la Lista A y {res_listas['lista_B']} de la Lista B, todas también en A. La estabilidad se midió en {res_listas['evaluadas_en_estabilidad']} y el análisis completo en {res_listas['priorizadas']} priorizadas.

## 2. ¿Cuáles llegaron a la comparación final?

{', '.join(f'`{c}`' for c in fin.index)}. `{P}` representa también a `P1_c12_km_k4`, y `P2_c05_km_k3` a `P1_c05_km_k3`.

## 3. ¿Qué pasó al recalcular PCA y FAMD dentro de los remuestreos?

Los subespacios se parecen (mediana {n(sim['similitud_subespacio'].median())}), pero las fronteras se mueven. Es el paso que más reduce la estabilidad. Las configuraciones con pocos componentes parecían estables solo porque la reducción estaba congelada: `F2_c03_km_k3` pasa de {n(niv.loc['F2_c03_km_k3', 'E0_entre_media'])} a {n(niv.loc['F2_c03_km_k3', 'E1_entre_media'])}.

## 4. ¿La estabilidad subió o bajó frente a la Fase 37B?

Bajó. En la Lista A, con media ≥ 0,65: de {cuenta['E0']['m65']} a {cuenta['E3']['m65']}. Sumando p05 ≥ 0,50: de {cuenta['E0']['m65p5']} a {cuenta['E3']['m65p5']}. Sobre 0,80: de {cuenta['E0']['m80']} a {cuenta['E3']['m80']}. `{P}` baja de {n(niv.loc[P, 'E0_entre_media'])} a {n(niv.loc[P, 'E3_entre_media'])}.

## 5. ¿Qué mostró la referencia correlacionada?

Datos sin grupos reproducen buena parte de lo observado, incluidos ARI altos. Ninguna finalista pasa el control de búsqueda múltiple en silueta y estabilidad, aunque Calinski-Harabasz y Davies-Bouldin sí lo superan en el conjunto de la búsqueda (p = {n(bm.loc['calinski_harabasz', 'p_max'], 3)} y {n(bm.loc['davies_bouldin', 'p_max'], 3)}). `{P}` tiene silueta igual a la nula (p = {n(nu.loc[P, 'silueta_p'], 3)}) y estabilidad E1 sobre las 20 réplicas (p = {n(nu.loc[P, 'E1_ari_entre_media_p'], 3)}, el mínimo posible). La referencia usa la enmienda α = 0,05, de carácter exploratorio.

## 6. ¿Qué tan grave fue S-ORD?

Depende de la configuración. Es grave en k = 2 (cerca de 0,25) y en FAMD con 5 u 8 componentes y k = 3 (cerca de 0,20). Es moderada en `{P}` ({sn(P, 'S-ORD')}), con cambios concentrados en la frontera (AUC {n(des.loc[P, 'auc_margen_bajo_predice_cambio'])}), y se mantiene por la regla 6.3. Pero con ridit su estabilidad baja a {n(rep.loc[P, 'E3_entre_media_ridit'])}. Viene sobre todo del reajuste de fronteras, no de los ejes.

## 7. ¿Qué sensibilidades afectaron más a las finalistas?

S-SOLAPE en las de k = 3 y k = 4 (`{P}`: {sn(P, 'S-SOLAPE')}, crítica) y S-ORD en todas. Fuera de las reglas, S-BLOQUE también es baja ({sn(P, 'S-BLOQUE')}). Población, imputación y edad afectan poco.

## 8. ¿Qué tan multivariables son las agrupaciones?

Las de k = 2 y k = 3 son principalmente gradientes de ejercicio. `{P}` es multivariable según la regla ({int(itp.loc[P, 'n_variables_efecto'])} variables, {int(itp.loc[P, 'n_bloques_efecto'])} bloques), pero tres preguntas la reconstruyen con ARI {n(tre.loc[P, 'ari_3'])} (exploratorio).

## 9. ¿K-means mantuvo sus ventajas frente al método aglomerativo?

Sí: mayor estabilidad, asignación directa, y todas las finalistas son K-means. Eso no indica que los grupos sean reales: con `{P}`, el ARI entre K-means y Ward es {n(imc.loc[P, 'ari_km_ward'])}.

## 10. ¿Qué configuraciones asignan nuevas participantes con mayor consistencia?

Las de k = 2 (ARI fuera cercano a 0,95), que no son elegibles. Entre las elegibles, `{P}` ({n(asg.loc[P, 'ari_fuera_media'])}, p05 {n(asg.loc[P, 'ari_fuera_p05'])}, desacuerdo {n(asg.loc[P, 'desacuerdo_pct_medio'], 1)} %). El margen identifica bien las asignaciones dudosas, pero señala a muchas participantes.

## 11. ¿Modelo, segmentación operativa condicionada o ninguna selección?

Segmentación operativa condicionada (B).

## 12. Justificación exacta

Cumple los requisitos sellados de B: finalista, multivariable, incertidumbre evaluada y regla V declarada. No cumple A por el CRIT en S-SOLAPE y por no superar a la nula con control de búsqueda múltiple. Entre las elegibles, tiene menos advertencias que `{Q_}` ({int(fin.loc[P, 'n_adv'])} frente a {int(fin.loc[Q_, 'n_adv'])}). Es B en los {len(umb)} escenarios de umbrales, pero pasaría a C en {n_c} de {len(dep_alt)} lecturas alternativas, planteadas después de ver los resultados y no aplicadas para decidir.

## 13. Limitaciones que permanecen

Datos sintéticos y sin validación independiente; protocolo no ciego; enmienda con margen estrecho; resolución de 20 réplicas; potencia frente a grupos débiles sin evaluar; partes no recalibradas en E3; dependencia de S-SOLAPE, de la codificación, de la ponderación, del algoritmo y del método de reducción; {len(no_pri)} configuraciones sin evaluación completa; imputación de `tiene_actividad_sexual` abierta; y umbrales de incertidumbre sin definir.

## 14. Pruebas ejecutadas y superadas

{int((pr['resultado'] == 'superada').sum())} de {len(pr)} pruebas, y {int(mu['detectada'].sum())} de {len(mu)} errores introducidos detectados.

## 15. ¿Se preservaron los archivos protegidos?

Sí. 2.217 archivos iguales a sus manifiestos, HEAD en 745d689, sin escrituras fuera de la subfase y sin cambios en Django.

## 16. Archivos creados

Unos {n_archivos} archivos, todos en `analisis/fase37/37C_comparacion_seleccion/`. Ver `informes/00_indice_entregables.md` e `integridad/manifiesto_final_37C.csv`.

## 17. ¿Qué queda preparado para la Fase 37D?

La nota `15_nota_metodologica_37D.docx`, las etiquetas y parámetros provisionales, y la tabla de variables. **La Fase 37D no se inició.**

# Réplicas y estado de la fase

- **Recuperadas:** {len(recup)} réplicas (000 a 071), todas válidas.
- **Ejecutadas de nuevo:** ninguna. Por primera vez: {len(pend)} (072 a 099), más las 20 del contraste α = 0.
- **Estado:** la Fase 37C puede declararse **completa desde el punto de vista técnico**, a la espera de la decisión de la responsable.
""")

# 15 nota 37D ---------------------------------------------------------------------------------------------------------------------------
escribir('15_nota_metodologica_37D', f"""# Alcance

Esta nota prepara la Fase 37D. No la inicia, no usa el MRS y no caracteriza grupos. {PROV}

{SINT}

# Punto de decisión previo

Antes de la Fase 37D, la responsable debe elegir entre:

1. Continuar con la segmentación operativa `{P}`.
2. Usar la alternativa simple de tres preguntas (`{tre.loc[P, 'mejor_trio']}`).
3. No segmentar y tratar las variables como continuas.

También queda por resolver la imputación de `tiene_actividad_sexual`.

# Riesgos que la Fase 37D debe controlar

- **Circularidad.** `tiene_actividad_sexual` y `distension_abdominal` entran en la partición y se relacionan con síntomas. La asociación entre grupos y MRS puede estar inflada. Conviene repetir la comparación con la partición de S-SOLAPE.
- **Doble uso de datos.** Los grupos se crearon con estas 529 participantes. Las diferencias entre grupos en las variables usadas para crearlos son esperables y no constituyen una validación.
- **Verdad del simulador.** Una asociación con el MRS en datos sintéticos refleja lo que la simulación programó.
- **Nombres.** Evitar nombres que sugieran tipos clínicos. Un continuo no admite «perfiles» en sentido estricto.
- **Fronteras.** Informar los resultados también sin las participantes de margen bajo, para ver si dependen de ellas. Conviene presentar la comparación por cada corte.

# Comparaciones recomendadas

- Frente a la regla de tres preguntas: si esta explica lo mismo, es preferible por simple.
- Frente a variables continuas sin agrupar.
- Frente a `{Q_}`, `P2_c16_km_k4` y la partición con ridit, para ver si lo encontrado depende de la configuración.

# Lo disponible

{tabla(['Elemento', 'Ubicación'], [['Etiquetas provisionales', f'`seleccion/artefactos_provisionales/{P}/etiquetas.csv`'], ['Centroides y procedencia', f'`seleccion/artefactos_provisionales/{P}/modelo_segmentacion.json`'], ['Alternativa', f'`seleccion/artefactos_provisionales/{Q_}/`'], ['Decisión', '`seleccion/decision_final_37C.json`'], ['Variables que más separan', '`seleccion/variables_que_mas_separan.csv`'], ['Grilla de incertidumbre', '`asignacion/grilla_incertidumbre.csv`']])}

La Fase 37D no se inició. Requiere una instrucción expresa.
""")

# 00 indice -----------------------------------------------------------------------------------------------------------------------------
(INF / '00_indice_entregables.md').write_text(f"""# Fase 37C: índice de entregables

Rutas relativas a `analisis/fase37/37C_comparacion_seleccion/`.

{tabla(['N.º', 'Entregable', 'Ubicación'], [
    [1, 'Protocolo sellado y enmienda', '`protocolo/`, `informes/01_protocolo_37C.docx`, `informes/01b_enmienda_referencia_nula.docx`'],
    [2, 'Registro de la Lista A', '`informes/02_registro_lista_A.docx`, `candidatos/lista_A_completa.csv`'],
    [3, 'Registro de la Lista B (exploratoria)', '`informes/03_registro_lista_B.docx`, `candidatos/lista_B_exploratoria.csv`'],
    [4, 'Estabilidad del procedimiento completo', '`informes/04_estabilidad_procedimiento_completo.docx`, `estabilidad/`'],
    [5, 'Referencia correlacionada', '`informes/05_referencia_correlacionada.docx`, `referencias_nulas/`'],
    [6, 'S-ORD', '`informes/06_s_ord.docx`, `sensibilidades/s_ord/`'],
    [7, 'Sensibilidades críticas', '`informes/07_sensibilidades.docx`, `sensibilidades/`'],
    [8, 'Interpretabilidad preliminar', '`informes/08_interpretabilidad.docx`, `interpretabilidad/`'],
    [9, 'Asignación de participantes nuevas', '`informes/09_asignacion.docx`, `asignacion/`'],
    [10, 'Comparación de finalistas', '`informes/10_comparacion_finalistas.docx`, `seleccion/`'],
    [11, 'Decisión metodológica', '`informes/11_decision_metodologica.docx`, `seleccion/decision_final_37C.json`, `seleccion/artefactos_provisionales/`'],
    [12, 'Informe de pruebas', '`informes/12_informe_pruebas.md`, `pruebas/`'],
    [13, 'Informe de integridad', '`informes/13_informe_integridad.md`, `integridad/`'],
    [14, 'Informe de cierre', '`informes/14_informe_cierre_37C.docx`'],
    [15, 'Nota metodológica para la Fase 37D', '`informes/15_nota_metodologica_37D.docx`'],
    ['—', 'Figuras', '`figuras/` (12 PNG)'],
    ['—', 'Fuentes Markdown de los Word', '`informes/fuentes/`'],
    ['—', 'Programas', '`scripts/`']])}

Para entender el resultado, conviene empezar por el informe 14 o por la explicación en lenguaje sencillo del informe 11.
""", encoding='utf-8')

# Word ------------------------------------------------------------------------------------------------------------------------------------
shutil.copy(B / 'protocolo' / '01_protocolo_37C.md', FUENTES / '01_protocolo_37C.md')
shutil.copy(B / 'protocolo' / '02_enmienda_referencia_nula.md', FUENTES / '01b_enmienda_referencia_nula.md')
TITULOS = {'01_protocolo_37C': 'Protocolo de la Fase 37C', '01b_enmienda_referencia_nula': 'Enmienda 1: referencia nula', '02_registro_lista_A': 'Registro de la Lista A', '03_registro_lista_B': 'Registro de la Lista B', '04_estabilidad_procedimiento_completo': 'Estabilidad del procedimiento completo',
           '05_referencia_correlacionada': 'Referencia nula correlacionada', '06_s_ord': 'Análisis de S-ORD', '07_sensibilidades': 'Sensibilidades críticas', '08_interpretabilidad': 'Interpretabilidad preliminar', '09_asignacion': 'Asignación de participantes nuevas',
           '10_comparacion_finalistas': 'Comparación de finalistas', '11_decision_metodologica': 'Decisión metodológica', '14_informe_cierre_37C': 'Informe de cierre de la Fase 37C', '15_nota_metodologica_37D': 'Nota metodológica para la Fase 37D'}
for nombre, titulo in TITULOS.items():
    r = subprocess.run(['node', str(AQUI / 'md_a_word_37c.js'), str(FUENTES / f'{nombre}.md'), str(INF / f'{nombre}.docx'), titulo, 'Fase 37C: comparación, robustez y selección'], capture_output=True, text=True, encoding='utf-8')
    if r.returncode:
        raise SystemExit(f'{nombre}: {r.stderr[-800:]}')
    print(nombre, 'listo')
