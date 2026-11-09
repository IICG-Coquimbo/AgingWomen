// Cierre de las Fases 34 y 35: genera los cuatro documentos Word en informes/.
// Las tablas leen tablas/*.json; no calcula nada y no lee ni escribe fuera de esta carpeta.
// Uso, desde la raíz: NODE_PATH=<carpeta con node_modules de docx> node analisis/cierre_fases_34_35/scripts/generar_informes_cierre.js
const fs = require('fs');
const path = require('path');
const { Document, Packer } = require('docx');
const { ANCHO, P, H1, H2, LI, TIT, NOTA, tabla, estilos, numeracion, pie, PAG, portada, c } = require('./word_comun');

const CIERRE = path.resolve(__dirname, '..');
const J = (n) => JSON.parse(fs.readFileSync(path.join(CIERRE, 'tablas', n), 'utf8'));
const D = J('datos_fase35.json'), I = J('integridad.json'), T = J('tablas_cierre.json'), PR = J('pruebas.json');
const nueve = fs.readFileSync(path.join(CIERRE, 'tablas', 'h11_nueve_variables.csv'), 'utf8').replace(/^﻿/, '').trim().split(/\r?\n/).slice(1).map((l) => l.split(','));
const SEIS = D.shannon.primeras.slice(0, 6);
const CARP = 'analisis/cierre_fases_34_35';
const ejecutadas = PR.filter((x) => x.tipo !== 'No ejecutada');
const noEjecutadas = PR.filter((x) => x.tipo === 'No ejecutada');
const unitarias = ejecutadas.filter((x) => x.tipo === 'Prueba unitaria');
const totalUnit = unitarias.reduce((a, x) => a + x.casos, 0);
const todoOk = ejecutadas.every((x) => x.estado === 'Correcta');
const okInt = I.filas.filter((x) => x.resultado === 'OK').length;

const ETIQ = Object.fromEntries(D.rf.lista33.map((x) => [x.variable, x.etiqueta]));
const CONTRADICCIONES = [
  ['El cierre anterior da A1 por «Corregido» y H14 por «Corregido en texto».', 'Podría leerse que la asimetría y la curtosis de horas sentada, o la figura de 34E, se volvieron a calcular. No fue así.', 'El informe anterior se conserva; este cierre los registra como limitaciones abiertas.'],
  ['35A §3 elimina la sobrecarga; hoy es una de las 33 elegibles.', 'Leído solo, 35A contradice la lista vigente.', 'Decisión posterior del 03-11; nota en la versión revisada, tabla intacta.'],
  ['35A §5 conserva la diabetes como excepción y §9 lista 35 predictoras; hoy está excluida y hay 33.', 'Usar §9 como entrada de la Fase 36 incluiría variables fuera de la lista.', 'Notas en la versión revisada. Vale la lista de 33.'],
  ['dataset_fase35_33_variables.csv trae prevision y doble_carga, y no trae sobrecarga.', 'Por su nombre parece la entrada directa de la Fase 36, pero no coincide con las 33.', 'No se modifica. La Fase 36 debe seleccionar columnas y tomar la sobrecarga del conjunto limpio.'],
  ['Documentos previos remiten a la validación de la profesora.', 'Podría parecer que hay una validación pendiente que bloquea el avance.', 'La revisión metodológica corresponde a la responsable del proyecto. Los textos históricos no se cambian.'],
  ['La nota de la Fase 36 presenta como alternativas puntos que ya están acordados.', 'Podría reabrir decisiones ya tomadas (módulos laboral y de cuidados).', 'La nota se conserva; el protocolo nuevo prevalece sobre ella.'],
  ['El registro de Random Forest muestra huellas distintas del script y del protocolo entre el cálculo y el resumen.', 'Podría interpretarse como una ejecución con código distinto.', 'El protocolo registra el ajuste de funciones de figuras después de entrenar. Los 10 archivos crudos coinciden con la huella tomada antes de ese ajuste.'],
];
const tablaContradicciones = () => tabla(['Contradicción', 'Consecuencia', 'Tratamiento'], CONTRADICCIONES, [3500, 2930, 2930], { tam: 16 });
const tablaIntegridad = () => tabla(['Punto', 'Comprobación', 'Resultado', 'Detalle'], I.filas.map((x) => [x.punto, x.comprobacion, x.resultado, x.detalle]), [620, 3560, 900, 4280], { tam: 15 });
const tablaPruebas = () => tabla(['Prueba', 'Casos', 'Estado', 'Detalle'], ejecutadas.map((x) => [x.prueba, x.casos, x.estado, x.detalle]), [4560, 700, 1000, 3100], { tam: 16 });
const tablaNoEjecutadas = () => tabla(['No ejecutada', 'Motivo'], noEjecutadas.map((x) => [x.prueba, x.detalle]), [4300, 5060], { tam: 16 });

function fase34() {
  const lims = T.limitaciones.filter((l) => /Fase 34|Fases 34|Random Forest|Shannon$|Fase 35$/.test(l.fase) || ['H14', 'H17', 'A1'].includes(l.origen));
  const hijos = [
    ...portada('Informe de cierre de la Fase 34', 'Versión 2: resolución de H11 y H13 y estado definitivo de los hallazgos'),
    NOTA('Esta versión complementa y no reemplaza a la versión anterior, que se conserva en analisis/revision_correctiva_fase34/informe/informe_cierre_correccion_fase34.docx. Donde ambas difieren en el estado de un hallazgo, vale esta.'),
    H1('1. Resumen'),
    P(`El cierre resolvió los dos pendientes de reproducibilidad de la corrección controlada. **H11 quedó resuelto en el código**: el recuento de imputaciones ahora corresponde a las 529 participantes analíticas. **H13 quedó resuelto en rótulos y metadatos**: al volver a ejecutar el script, la etapa menopáusica saldrá como descriptiva. Ninguno de los dos cambios altera un resultado estadístico: no se ejecutó el flujo completo y ${I.protegidos_sin_cambio} de ${I.n_antes} archivos siguen idénticos; los dos restantes son los scripts corregidos.`),
    P(`**La Fase 34 ${todoOk && I.cumple ? 'puede declararse cerrada' : 'aún no puede declararse cerrada'} con limitaciones documentadas.** H14, H17, A1 y la sensibilidad de Shannon sin imputaciones laborales siguen abiertos: no se resuelven sin nuevos cálculos, que quedan fuera de esta tarea.`),
    H1('2. Cambios de este cierre y cambios anteriores'),
    tabla(['Origen', 'Archivos', 'Naturaleza'], [
      ['Corrección controlada anterior', '8 scripts: eda/univariado.py, eda_univariado.py, eda/informe_multivariado.py, eda/multivariado.py, eda/informe_usuaria.py, eda_usuaria.py, eda/variables.py, limpieza/informe.py', 'Textos, rótulos y comentarios, incluidas las funciones auxiliares que los construyen.'],
      ['Este cierre', 'eda/univariado.py y eda_usuaria.py (ya estaban entre los 8)', 'H11: lógica del recuento. H13: rótulo de salida y título de sección.'],
    ], [2300, 4360, 2700]),
    H1('3. H11: recuento de imputaciones'),
    P('**Causa.** En describir(), cuando una variable no tenía marca _imputado, el recuento tomaba los faltantes del diccionario, contados sobre 546 participantes. La auditoría de la corrección ya había calculado el valor exacto en 529 para las 65 variables con figura.'),
    P('**Corrección.** La nueva función recuento_imputados() usa, en orden, la marca de la fila, la tabla de origen de las respuestas si su n válido coincide con el de la figura y, solo si faltan ambas, la cota del diccionario. Las pruebas confirman que solo cambian estas nueve variables:'),
    tabla(['Variable', 'Cota histórica', 'Valor exacto (529)', 'Dominancia sin imputadas, antes', 'Ahora', 'Dominancia (%)'],
      nueve.map((f) => [f[0], f[1], f[2], c(f[3], 2), c(f[4], 2), c(f[5], 2)]), [3060, 1000, 1200, 1500, 1100, 1500], { tam: 16 }),
    NOTA('La dominancia sin imputadas sigue siendo una cota inferior: supone que todas las imputadas cayeron en la categoría dominante. Ninguna variable cambia de tramo y ningún comentario automático cambia.'),
    P('**Lo que no cambia.** Frecuencias, n válidos, porcentajes, entropía y medidas de forma. El CSV histórico eda_univariado_resumen.csv conserva la cota en esas nueve filas, porque no se sobrescribe; los valores exactos están en tablas/h11_nueve_variables.csv.'),
    H1('4. H13: etapa menopáusica'),
    P('**Referencias revisadas.** La etapa aparece en V.CONTROL_USUARIA y GRUPOS_ASOCIACION, de donde salía el rol «control», y en BLOQUES["control"], de donde salía el título de la sección 3.1. Son rótulos y agrupaciones sin efecto en los filtros de este flujo: el rol solo se escribe en la tabla de salida.'),
    P('**Corrección.** rotular_roles() cambia el rol a «descriptiva» después de la corrección FDR, y TITULOS_INFORME alinea la sección 3.1 con el informe histórico. La figura 89 conserva «Variables de control» porque no incluye la etapa.'),
    P('**Lo que no se hizo.** La etapa sigue agrupada internamente en V.CONTROL_USUARIA. Sacarla de ahí alteraría el recorrido del cálculo, de modo que se mantuvo: la familia FDR, el orden de las pruebas, el efecto (ε² = 0,006), p y q siguen iguales. La etapa continúa fuera de las variables elegibles.'),
    H1('5. Estado definitivo de los hallazgos'),
    tabla(['ID', 'Clase', 'Estado en el cierre anterior', 'Estado definitivo'], T.hallazgos.map((h) => [h.id, h.clase, h.antes, h.definitivo]), [620, 2040, 3350, 3350], { tam: 15, resaltar: (f) => T.hallazgos.find((h) => h.id === f[0]).cambia === 'Sí' }),
    NOTA('Filas resaltadas: el estado cambia o se precisa en este cierre. Las descripciones completas están en tablas/hallazgos_estado_definitivo.csv.'),
    H1('6. Hallazgos y limitaciones que permanecen'),
    P('Estos puntos no se presentan como corregidos. En A1 se corrigieron el título y el texto, pero la asimetría y la curtosis siguen sin recalcular. En H14 se aclaró el texto, pero la figura sigue diciendo «38 predictoras».'),
    tabla(['ID', 'Origen', 'Limitación', 'Efecto o tratamiento', 'Estado'], lims.map((l) => [l.id, l.origen, l.limitacion, l.efecto_o_tratamiento, l.estado]), [560, 900, 3500, 2900, 1500], { tam: 15 }),
    H1('7. Pruebas localizadas'),
    P(`Se ejecutaron ${totalUnit} casos de prueba unitaria y dos verificadores. El flujo de eda_univariado.py y eda_usuaria.py no se ejecutó: H11 y H13 se probaron llamando en memoria a las funciones afectadas.`),
    tablaPruebas(),
    TIT('Pruebas no ejecutadas'),
    tablaNoEjecutadas(),
    H1('8. Archivos modificados y comparación de integridad'),
    P(`Respecto del manifiesto inicial de este cierre (${I.n_antes} archivos) cambiaron solo eda/univariado.py y eda_usuaria.py. Respecto de la línea base de la corrección (${I.n_base} archivos), ${I.base_sin_cambio} siguen idénticos y ${I.previo_modificados.length} difieren: los 8 scripts autorizados. La lista completa está en tablas/archivos_creados_y_modificados.csv.`),
    tablaIntegridad(),
    H1('9. Conclusiones estadísticas históricas'),
    P('Las conclusiones estadísticas históricas de 34A a 34E no cambiaron. No se recalcularon asociaciones, valores p o q ni modelos. Los cálculos en memoria de las pruebas reproducen los valores históricos, salvo imputados_34B y su cota en las nueve variables declaradas.'),
    H1('10. Contradicciones documentales identificadas'),
    tablaContradicciones(),
    H1('11. Trazabilidad'),
    LI('Versión anterior: analisis/revision_correctiva_fase34/informe/informe_cierre_correccion_fase34.docx'),
    LI(`Tablas de este cierre: ${CARP}/tablas/ · Manifiestos: ${CARP}/integridad/`),
    LI('HEAD 745d689, rama datos-simulados. Sin commit ni push. Fecha del cierre: 4 de noviembre de 2026.'),
  ];
  return new Document({ styles: estilos, numbering: numeracion, sections: [{ properties: { page: PAG }, footers: { default: pie('Cierre de la Fase 34, versión 2') }, children: hijos }] });
}

function fase35() {
  const r = D.rf.rendimiento;
  const rm = Object.fromEntries(r.map((x) => [x.modelo, x]));
  const cons = (t) => D.rf.consistencia.filter((x) => x.consistencia === t).map((x) => ETIQ[x.variable] || x.variable);
  const lim = (ids) => T.limitaciones.filter((l) => ids.includes(l.id)).map((l) => [l.origen, l.limitacion, l.efecto_o_tratamiento]);
  const generales = D.rf.lista33.filter((x) => x.poblacion === 'general').map((x) => x.etiqueta);
  const hijos = [
    ...portada('Informe de cierre de la Fase 35 — Preparación analítica, Shannon, FCBF y Random Forest', 'Cierre formal de las Fases 35A y 35B'),
    H1('1. Resumen ejecutivo'),
    P('La Fase 35 preparó el conjunto analítico y evaluó qué variables comparten información con la severidad de los síntomas (MRS total ≥ 16). Este informe no agrega análisis: cada cifra se contrastó con los archivos guardados, sin repetir permutaciones, FCBF ni entrenamientos.'),
    LI('**Datos:** 529 participantes con MRS completo y 33 variables elegibles (30 generales, 2 laborales y 1 de sobrecarga).'),
    LI('**Shannon:** seis variables con q < 0,10, un criterio exploratorio. Con el protocolo oficial anterior (5.000 permutaciones y q < 0,05) no hubo seleccionadas.'),
    LI('**FCBF:** el adaptado conserva fuerza, IMC, lugar de trabajo y situación laboral; el estándar conserva fuerza y lugar de trabajo.'),
    LI(`**Random Forest:** capacidad modesta (ROC-AUC de evaluación entre ${c(rm.A.roc_auc_evaluacion)} y ${c(rm.C1.roc_auc_evaluacion)}) y sobreajuste marcado. El aporte adicional de las variables laborales y de sobrecarga no quedó demostrado con claridad.`),
    P(`**La Fase 35 ${todoOk && I.cumple ? 'puede declararse cerrada' : 'aún no puede declararse cerrada'} con las limitaciones de la sección 9.** Las ${D.n_comprobaciones} comprobaciones de cifras coinciden con los archivos.`),
    TIT('Tipo de información en este informe'),
    tabla(['Categoría', 'Contenido'], [
      ['Resultados históricos verificados', 'Fase 35A; Shannon y FCBF de la revisión de 33 variables; métricas de Random Forest.'],
      ['Análisis complementarios', 'Criterio q < 0,10, sensibilidades de IMC y sobrecarga, FCBF adaptado y Random Forest. Apoyan la interpretación, pero no son el criterio oficial previo.'],
      ['Decisiones propuestas para fases futuras', 'Protocolo de la Fase 36 y siguientes (sección 8). Aún no se han ejecutado.'],
    ], [3200, 6160]),
    H1('2. Alcance y datos utilizados'),
    P('Los datos son sintéticos: se generaron con relaciones programadas para probar el procedimiento. Las poblaciones se confirmaron en los archivos finales:'),
    tabla(['Población', 'n', 'Uso'], [
      ['Participantes con MRS completo', '529', 'Las 30 variables generales'],
      ['Situación laboral respondida o deducida', '287', 'Lugar de trabajo comprensivo y estrés del entorno laboral'],
      ['Clasificadas como trabajadoras', '309', '287 más 22 imputadas; no se usa como población de los análisis laborales'],
      ['Cuidadoras con sobrecarga observada', '239', 'Sobrecarga: análisis principal'],
      ['Cuidadoras, con 12 sobrecargas imputadas', '251', 'Sobrecarga: sensibilidad'],
    ], [4200, 700, 4460]),
    P(`**Variables generales (30):** ${generales.join(', ')}.`),
    P('**Excluidas:** usa_medicamentos_diabetes (dominancia de 87,5 %), doble_carga y prevision (fuera del modelado por decisión vigente), y etapa_menopausica con las tres preguntas menstruales (regla propia sin validar e información indirecta de la etapa).'),
    H1('3. Fase 35A'),
    P(`**Objetivo.** severo_mrs vale 1 si el MRS total es 16 o más: 281 severas (53,1 %) y 248 no severas. **Filtros.** Baja variabilidad (dominancia > 85 %) y redundancia (|asociación| > 0,80), que eliminó las variables realiza_* en favor de sus frecuencias.`),
    P('**Faltantes.** El IMC se imputó por la media (29,23 kg/m²) en 262 de 529 (49,5 %), lo que reduce rho con el MRS de 0,250 a 0,192. Quienes no trabajan llevan el código 0 en las variables laborales, y las frecuencias de ejercicio usan 0 para «no lo realiza».'),
    P(`**Población laboral.** De las 529, ${D['35A'].trabajadoras} quedan clasificadas como trabajadoras: ${D['35A'].con_respuesta} con situación respondida o deducida y ${D['35A'].imputadas} mediante imputación. El valor imputado no es una respuesta observada. Esas ${D['35A'].imputadas} participantes tienen valor 3 en lugar de trabajo y estrés en los conjuntos de la Fase 35, y ese 3 no es una opinión neutral real. No entraron en los análisis laborales. Dentro de las 287 también hay 16 valores de lugar y 10 de estrés imputados en 34B; 263 participantes tienen ambas respuestas observadas.`),
    P('El informe histórico de 35A se conserva. Su versión documental revisada corrige esta descripción sin cambiar ninguna tabla.'),
    H1('4. Fase 35B: Shannon'),
    P('**Procedimiento.** Para cada variable se calculó la incertidumbre simétrica, SU = 2·I(X;Y) / (H(X) + H(Y)), con la severidad binaria. La significancia se estimó por permutaciones, p = (k + 1) / (B + 1), y se corrigió con Benjamini-Hochberg sobre las 33 variables. Se verificó la aritmética de p, q y SU en los archivos guardados.'),
    P('**Criterios.** El protocolo oficial anterior usaba 5.000 permutaciones y q < 0,05, y no seleccionó variables. La revisión del 03-11 usa 10.000 y 50.000 permutaciones con q < 0,10 como criterio exploratorio.'),
    TIT('Variables con q < 0,10 (50.000 permutaciones; q con 10.000 como contraste)'),
    tabla(['Variable', 'n', 'SU', 'k', 'p', 'q', 'Monte Carlo de q', 'q (10.000)'],
      SEIS.map((f) => [ETIQ[f.variable], f.n, c(f.su, 4), f.k, c(f.p, 5), c(f.q, 4), `${c(f.mc_inf, 3)} a ${c(f.mc_sup, 3)}`, c(f.q_10000, 4)]),
      [3060, 520, 780, 620, 900, 800, 1600, 1080], { tam: 16 }),
    P('**Lectura.** Los valores de SU son bajos: entre 0,008 y 0,021, de modo que cada variable comparte poca información con la severidad. Las seis se repiten con 10.000 y 50.000 permutaciones. Con 10.000 ninguna llega a q < 0,05. Con 50.000 llegan días de ejercicio y bajo impacto, pero el intervalo Monte Carlo de ambas cruza 0,05, por lo que esa diferencia no debe sobreinterpretarse.'),
    P('**Sensibilidades.** IMC solo con observados: n = 267, SU = 0,0284, q al reemplazar = 0,0673. Sobrecarga con 251 cuidadoras: SU = 0,0213, q al reemplazar = 0,1419; sigue sin llegar a q < 0,10.'),
    P('**Interpretación.** SU no indica dirección y no demuestra una relación causal. La dirección (por ejemplo, negativa en días de ejercicio y positiva en IMC) se calculó por separado y solo describe la asociación. Es un análisis univariado: cada variable se evalúa sola.'),
    H1('5. Selección FCBF'),
    tabla(['Variable', 'FCBF adaptado', 'FCBF estándar'], [
      ['Frecuencia de ejercicio de fuerza', 'Seleccionada', 'Seleccionada'],
      ['Lugar de trabajo comprensivo', 'Seleccionada', 'Seleccionada'],
      ['IMC', 'Seleccionada', `Redundante con fuerza (q del par = ${c(D.fcbf.q_par_estandar.imc, 2)})`],
      ['Trabaja actualmente', 'Seleccionada', `Redundante con fuerza (q del par = ${c(D.fcbf.q_par_estandar.trabaja_actualmente, 4)})`],
      ['Días de ejercicio a la semana', 'Redundante con fuerza', 'Redundante con fuerza'],
      ['Frecuencia de ejercicio de bajo impacto', 'Redundante con fuerza', 'Redundante con fuerza'],
    ], [3800, 2360, 3200]),
    P('La selección es igual con 10.000 y 50.000 permutaciones. **La diferencia entre variantes** es que el estándar elimina por la regla SU, aunque la asociación del par no tenga respaldo, y el adaptado exige ese respaldo. Por eso IMC y situación laboral solo salen en el estándar.'),
    P('**Interpretación.** FCBF ordena según SU con la severidad, por lo que fuerza representa al bloque de ejercicio, pero 84,7 % de las participantes no realiza ese ejercicio y su dirección es mixta. «Redundante» significa que aporta información solapada, no que la variable carezca de interés.'),
    H1('6. Random Forest complementario'),
    P('**Propósito.** Evaluar si las variables, en conjunto, ayudan a predecir la severidad. Complementa a Shannon y no lo reemplaza. Se usó validación cruzada 5×3 (15 particiones), 500 árboles, hoja mínima de 5 y pesos balanceados; las diferencias se evalúan con corrección de Nadeau-Bengio.'),
    tabla(['Modelo', 'n', 'Variables', 'ROC-AUC evaluación', 'DE', 'ROC-AUC entrenamiento', 'Diferencia', 'Exactitud balanceada', 'p azar'],
      r.map((x) => [x.modelo, x.n, x.n_variables, c(x.roc_auc_evaluacion), c(x.roc_auc_de), c(x.roc_auc_entrenamiento), c(x.roc_auc_diferencia_ent_eval), c(x.balanced_accuracy_evaluacion), c(D.rf.azar_p[x.modelo], 3)]),
      [800, 600, 900, 1200, 700, 1460, 1100, 1200, 1400], { tam: 16 }),
    NOTA('p azar: 200 permutaciones, por lo que el mínimo posible es 0,005. A: edad, IMC y situación laboral. B: 30 generales. C0 y C1: trabajadoras (29 generales; C1 suma las 2 laborales). D0 y D1: cuidadoras (30 generales; D1 suma sobrecarga).'),
    TIT('Comparaciones de ROC-AUC'),
    tabla(['Comparación', 'Diferencia', 'IC 95 %', 'Lectura'], D.rf.comparar.map((x) => [`${x.modelo} frente a ${x.referencia}`, c(x.diferencia), `${c(x.ic_inf)} a ${c(x.ic_sup)}`, x.lectura]), [2800, 1400, 2360, 2800]),
    LI('**Capacidad modesta.** Los modelos superan al azar, salvo A, pero quedan lejos de una clasificación útil por sí sola.'),
    LI('**Sobreajuste.** Entre entrenamiento y evaluación hay diferencias de 0,257 a 0,359.'),
    LI('**Laborales y sobrecarga.** Los intervalos de C1 frente a C0 y de D1 frente a D0 incluyen el cero: su aporte adicional no quedó demostrado con claridad.'),
    LI('**Importancia.** La importancia predictiva no equivale a causalidad, y el conjunto sintético contiene relaciones programadas.'),
    LI('**H17.** La identificación de imputadas en la sensibilidad sigue incompleta en 10 variables. Se documenta sin nueva ejecución, de modo que su efecto no está medido.'),
    H1('7. Comparación entre Shannon y Random Forest'),
    P('Los métodos responden preguntas distintas: Shannon mide cuánta información comparte cada variable por separado; Random Forest, cuánto aporta cada una dentro de un modelo conjunto.'),
    tabla(['Clasificación', 'Variables', 'n'], [
      ['Coinciden ambos', cons('Coinciden ambos métodos').join(', '), '5'],
      ['Solo Shannon', cons('Solo Shannon').join(', '), '1'],
      ['Solo Random Forest', cons('Solo Random Forest').join(', '), '6'],
      ['Sin respaldo en ninguno', 'Las restantes', '21'],
    ], [2400, 6260, 700]),
    P('**Limitaciones de la comparación.** Las categorías dependen del umbral q < 0,10 y de los criterios de aporte definidos en el protocolo. Las variables correlacionadas reparten su importancia en Random Forest, y fuerza presenta un aporte inestable. Que una variable aparezca solo en un método no invalida el otro.'),
    H1('8. Decisiones metodológicas definitivas'),
    P('**Se conserva como entrada para la Fase 36:** la lista de 33 variables, con la estructura de capa general (529, 30 variables), módulo laboral (287, 2 variables) y módulo de cuidados (239 como análisis principal, 251 como sensibilidad). FCBF y Random Forest no recortan esta lista: informan la interpretación.'),
    P('**Decisiones propuestas para fases futuras.** El MRS queda fuera de la formación de clústeres; los valores laborales de las 22 no se tratan como observados; se compararán perfiles con y sin IMC; la codificación ordinal se definirá antes de PCA o FAMD. El detalle está en el protocolo de la Fase 36. Nada de esto se ha ejecutado.'),
    P('**Condición práctica.** dataset_fase35_33_variables.csv no es la entrada directa: trae prevision y doble_carga, y no trae sobrecarga.'),
    H1('9. Limitaciones'),
    tabla(['Tema', 'Limitación', 'Efecto o tratamiento'], lim(['L12', 'L06', 'L05', 'L07', 'L13', 'L14', 'L11', 'L15', 'L02', 'L04', 'L17', 'L18']), [1400, 4160, 3800], { tam: 16 }),
    H1('10. Verificación de integridad'),
    P(`**Cifras.** ${D.n_ok} de ${D.n_comprobaciones} comprobaciones coinciden con los archivos (tablas/verificacion_fase35.csv). **Archivos.** ${okInt} de ${I.filas.length} controles correctos al comparar manifiestos SHA-256.`),
    tablaIntegridad(),
    TIT('Contradicciones documentales identificadas'),
    tablaContradicciones(),
    H1('11. Conclusiones'),
    P('La Fase 35 dejó una lista definida de 33 variables, con poblaciones claras y resultados reproducibles desde los archivos guardados. Los resultados muestran asociaciones débiles y capacidad predictiva modesta, coherentes con un análisis exploratorio. Cinco variables reciben apoyo de ambos métodos: IMC, situación laboral, días de ejercicio, bajo impacto y lugar de trabajo.'),
    P('Queda preparada la entrada conceptual de la Fase 36, cuyo inicio queda sujeto a la decisión de la responsable del proyecto. No se inició ningún análisis posterior.'),
    H1('12. Trazabilidad'),
    tabla(['Elemento', 'Ruta o valor'], [
      ['Conjuntos', 'datos/analitico/dataset_fase35.csv; datos/analitico/dataset_fase35_33_variables.csv; datos/limpio_usuaria/dataset_usuaria_limpio.csv'],
      ['Shannon y FCBF', 'analisis/reunion_2026-11-03/revision_33_variables/ (permutaciones_10000, permutaciones_50000, informe)'],
      ['Random Forest', 'analisis/random_forest_revision_35b_33_variables/ (resultados, registro_ejecucion.txt)'],
      ['Informe histórico de 35A', 'analisis/informe_preprocesamiento_fase35.md'],
      ['35A revisada', `${CARP}/informes/informe_preprocesamiento_fase35_revisado.md`],
      ['Informes previos', 'reunion_2026-11-03/revision_33_variables/informe/informe_fase35b_33_variables.docx; random_forest_revision_35b_33_variables/informe/informe_random_forest_33_variables.docx; revision_correctiva_fase34/informes_revisados/informe_random_forest_33_variables_revisado.docx'],
      ['Versiones', 'Python 3.12.5, numpy 2.2.4, pandas 2.2.3, scikit-learn 1.6.1'],
      ['Ejecuciones', 'Shannon y FCBF: registro del 2026-11-03 19:33. Random Forest: registro del 2026-11-04 01:11. HEAD 745d689.'],
      ['Huellas de Random Forest', 'Script y protocolo cambiaron tras el cálculo para ajustar figuras; el protocolo lo registra y los archivos crudos no cambiaron.'],
      ['Fecha del cierre', '4 de noviembre de 2026. Sin commit ni push.'],
    ], [2400, 6960], { tam: 16 }),
  ];
  return new Document({ styles: estilos, numbering: numeracion, sections: [{ properties: { page: PAG }, footers: { default: pie('Informe de cierre de la Fase 35') }, children: hijos }] });
}

function protocolo() {
  const hijos = [
    ...portada('Protocolo de trabajo para la Fase 36', 'Decisiones acordadas y detalles técnicos por definir'),
    NOTA('Este documento registra decisiones y no implementa nada: no se generaron matrices ni se entrenaron modelos. Prevalece sobre las alternativas de analisis/revision_correctiva_fase34/informe/nota_metodologica_fase36.docx, que se conserva.'),
    H1('1. Acordado'),
    tabla(['Tema', 'Decisión'], [
      ['Capa general', '529 participantes y 30 variables generales. Incluye a las 22 participantes con situación laboral imputada. El MRS queda fuera de la formación de clústeres.'],
      ['Módulo laboral', '287 participantes con situación laboral respondida o deducida y dos variables: lugar de trabajo comprensivo y estrés del entorno laboral. Los valores laborales de las 22 no se incluyen como respuestas observadas.'],
      ['Módulo de cuidados', '239 cuidadoras con sobrecarga observada como análisis principal; 251 como análisis de sensibilidad.'],
      ['IMC', 'Se planifica comparar perfiles con y sin IMC, por su imputación de 49,5 %.'],
      ['Variables ordinales', 'Su codificación se define explícitamente antes de ejecutar PCA o FAMD.'],
      ['Fase 37', 'Evaluar PCA y FAMD. Aplicar K-means y jerárquico aglomerativo. Comparar con silueta, Davies-Bouldin, Calinski-Harabasz y estabilidad. Caracterizar los perfiles con las variables originales y la severidad MRS.'],
      ['Fases 38 y 39', 'Construir y evaluar reglas de asociación específicas por clúster.'],
      ['Fase 40', 'Integrar la asignación de perfiles y las recomendaciones en AgingWomen. Desarrollar pruebas funcionales y de integración.'],
      ['Exclusiones', 'No se incorporan modelos de mezclas gaussianas (GMM). usa_medicamentos_diabetes, doble_carga, prevision y etapa_menopausica siguen fuera de las variables de modelado.'],
    ], [2200, 7160]),
    H1('2. Por definir'),
    P('Estos detalles técnicos no están acordados. Se listan para decidirlos antes de implementar la fase; ninguna de las opciones mencionadas es una recomendación ya aprobada.'),
    tabla(['Detalle', 'Qué debe resolverse'], [
      ['Codificación ordinal', 'Numérica o nominal en cada método, y cómo tratar el 0 de «no lo realiza» en las frecuencias.'],
      ['Escalado', 'Método para cada tipo de variable y su coherencia con PCA y FAMD.'],
      ['Integración de módulos', 'Si los módulos forman clústeres propios o describen los perfiles de la capa general. Las poblaciones distintas impiden tratarlos como columnas comunes.'],
      ['Las 22 en la capa general', 'Cómo señalar en los resultados que su situación laboral está imputada. Si se medirá la sensibilidad sin ellas.'],
      ['Cuidado en la capa general', 'Cómo interpretar cantidad_personas_cuida, con 21 respuestas de cuidado imputadas como «No» que fijan cantidad = 0.'],
      ['Comparación con y sin IMC', 'Criterios para decidir qué versión se retiene: métricas, tamaños de los grupos e interpretabilidad.'],
      ['Edad', '35A anunció comparar la segmentación con y sin edad en la Fase 37. Falta confirmar si sigue vigente y con qué criterios.'],
      ['Selección de configuraciones', 'Rango de número de clústeres, reglas de desempate entre métricas y tamaño mínimo de grupo.'],
      ['Estabilidad', 'Método de remuestreo, número de repeticiones, medida de acuerdo y semillas.'],
      ['Reglas de asociación', 'Discretización, soporte, confianza, lift y control de pruebas múltiples.'],
    ], [2800, 6560]),
    H1('3. Condiciones de entrada'),
    LI('La lista de variables sale de relevancia_33.csv, no de todas las columnas de dataset_fase35_33_variables.csv, que trae prevision y doble_carga.'),
    LI('La sobrecarga se toma del conjunto limpio, porque no está en ese archivo.'),
    LI('En los análisis laborales se usan las 287 y se excluyen los valores 3 de las 22. Dentro de las 287 hay 16 valores de lugar y 10 de estrés imputados en 34B; 263 tienen ambas respuestas observadas.'),
    LI('Los datasets y resultados históricos no se sobrescriben; las salidas nuevas van en una carpeta propia.'),
    LI('No se ejecutan eda_univariado.py ni eda_usuaria.py completos sobre las carpetas históricas.'),
    H1('4. Variables de entrada'),
    tabla(['Población', 'n', 'Variables'], [
      ['General', '529', D.rf.lista33.filter((x) => x.poblacion === 'general').map((x) => x.etiqueta).join(', ')],
      ['Laboral', '287', D.rf.lista33.filter((x) => x.poblacion === 'laboral').map((x) => x.etiqueta).join(', ')],
      ['Cuidados', '239 (251 en sensibilidad)', D.rf.lista33.filter((x) => x.poblacion === 'cuidadoras').map((x) => x.etiqueta).join(', ')],
    ], [1400, 1300, 6660], { tam: 16 }),
  ];
  return new Document({ styles: estilos, numbering: numeracion, sections: [{ properties: { page: PAG }, footers: { default: pie('Protocolo de trabajo para la Fase 36') }, children: hijos }] });
}

function resumen() {
  const estadoCierre = todoOk && I.cumple ? 'Puede declararse cerrada, con limitaciones documentadas' : 'No puede declararse cerrada: hay pruebas o controles sin cumplir';
  const hijos = [
    ...portada('Resumen ejecutivo del cierre', 'Fases 34 y 35'),
    H1('Estado'),
    tabla(['Elemento', 'Estado'], [
      ['H11', 'Resuelto en el código. El CSV histórico conserva la cota; los valores exactos están en una tabla aparte.'],
      ['H13', 'Resuelto en rótulos y metadatos. La etapa sigue agrupada internamente con las de control para no alterar el cálculo.'],
      ['Informe de 35A', 'Corregido en una versión documental revisada; la histórica no cambió.'],
      ['Fase 34', estadoCierre],
      ['Fase 35', estadoCierre],
      ['Resultados estadísticos', 'Sin cambios. No se repitió ningún análisis.'],
      ['Archivos protegidos', `${I.protegidos_sin_cambio} de ${I.n_antes} sin cambios; los 2 restantes son los scripts de H11 y H13.`],
      ['Pruebas', `${totalUnit} casos unitarios y 2 verificadores: ${todoOk ? 'todos correctos' : 'hay fallos'}. ${noEjecutadas.length} grupos no se ejecutaron y están registrados.`],
    ], [2400, 6960]),
    H1('Resultados que se llevan a la Fase 36'),
    LI('**33 variables elegibles:** 30 generales (529), 2 laborales (287) y 1 de sobrecarga (239; 251 en sensibilidad).'),
    LI('**Shannon:** seis variables con q < 0,10, criterio exploratorio: días de ejercicio, bajo impacto, IMC, fuerza, lugar de trabajo y situación laboral.'),
    LI('**FCBF:** adaptado con fuerza, IMC, lugar de trabajo y situación laboral; estándar con fuerza y lugar de trabajo.'),
    LI(`**Random Forest:** ROC-AUC de evaluación entre ${c(D.rf.rendimiento[0].roc_auc_evaluacion)} y ${c(D.rf.rendimiento[3].roc_auc_evaluacion)}, con sobreajuste. Aporte adicional laboral y de sobrecarga no demostrado con claridad.`),
    H1('Limitaciones abiertas'),
    P('H14, H17, A1 y la sensibilidad de Shannon sin imputaciones laborales no se corrigieron, porque exigirían nuevos cálculos. Las 18 limitaciones están en tablas/registro_limitaciones.csv.'),
    H1('Contradicciones documentales'),
    tablaContradicciones(),
    H1('Bloqueos para la Fase 36'),
    P('No hay un bloqueo técnico ni de datos. Antes de implementar deben resolverse los detalles técnicos del protocolo, como la codificación ordinal, el escalado y la integración de módulos, y el inicio queda sujeto a la decisión de la responsable del proyecto.'),
    H1('Entregables'),
    tabla(['Documento', 'Ruta'], [
      ['Cierre de la Fase 34, versión 2', `${CARP}/informes/informe_cierre_fase34_v2.docx`],
      ['Cierre de la Fase 35', `${CARP}/informes/informe_cierre_fase35.docx`],
      ['35A revisada', `${CARP}/informes/informe_preprocesamiento_fase35_revisado.md`],
      ['Protocolo de la Fase 36', `${CARP}/informes/protocolo_trabajo_fase36.docx`],
      ['Estado de H11 y H13', `${CARP}/tablas/estado_h11_h13.csv`],
      ['Limitaciones', `${CARP}/tablas/registro_limitaciones.csv`],
      ['Archivos creados y modificados', `${CARP}/tablas/archivos_creados_y_modificados.csv`],
      ['Integridad posterior', `${CARP}/tablas/verificacion_integridad_posterior.csv`],
      ['Registro de pruebas', `${CARP}/tablas/registro_pruebas.csv`],
    ], [3000, 6360], { tam: 16 }),
  ];
  return new Document({ styles: estilos, numbering: numeracion, sections: [{ properties: { page: PAG }, footers: { default: pie('Resumen ejecutivo del cierre') }, children: hijos }] });
}

(async () => {
  const dir = path.join(CIERRE, 'informes');
  fs.mkdirSync(dir, { recursive: true });
  for (const [n, d] of [['informe_cierre_fase34_v2.docx', fase34()], ['informe_cierre_fase35.docx', fase35()], ['protocolo_trabajo_fase36.docx', protocolo()], ['resumen_ejecutivo_cierre.docx', resumen()]]) {
    fs.writeFileSync(path.join(dir, n), await Packer.toBuffer(d));
    console.log(n);
  }
})();
